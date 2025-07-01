# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
import gc
import time
import threading
import json
import yaml
import os

from pathlib import Path
from typing import Any, Generator, List, Final, Dict

# Third-party imports
import pytest
import psutil

# Local imports
from jr_py_writer.classes.file_writer import FileWriter
from jr_py_writer.classes.file_reader import FileReader, ReaderResultPack


# Exceptions Reader
from jr_py_writer.exceptions.exceptions_file_reader import (
    FileReaderConstructionError,
    FileReaderSettingsError,
)

# ----------------------------------------------------------------------------------------------
# Fixture
# ----------------------------------------------------------------------------------------------


@pytest.fixture
def file_writer(tmp_path) -> Generator[FileWriter, None, None]:
    """Fixture for creating a FileReader instance."""
    temp_files = [tmp_path / "test_1.log", tmp_path / "test_2.log"]
    
    file_writer = FileWriter(
        file_paths=temp_files,  # Use temp files
        retry_limit=0,
        retry_delay=0.0,
        backoff_factor=0.0,
    )

    yield file_writer
    file_writer.clear_all()


@pytest.fixture
def file_reader(tmp_path) -> Generator[FileReader, None, None]:
    """Fixture for creating a FileReader instance."""

    temp_files = [tmp_path / "test_1.log", tmp_path / "test_2.log"]

    # Create a FileReader instance
    file_reader = FileReader(
        file_paths=temp_files,
        retry_limit=0,
        retry_delay=0.0,
        backoff_factor=0.0,
    )

    yield file_reader
    file_reader.clear_all()


def temporary_file_handler(num: int, tmp_path) -> List[Path]:
    """Fixture for creating temporary files for testing."""
    file_paths = [tmp_path / f"test_{i}.log" for i in range(1, num + 1)]
    for file_path in file_paths:
        file_path.touch()
    return file_paths


# ----------------------------------------------------------------------------------------------
# Tests Cases
# ----------------------------------------------------------------------------------------------

EDGE_INT = [
    0.0,
    "1.0",
    [],
    {},
    tuple(),
    set(),
    None,
    b"byte",
]

EDGE_FLOAT = [-1.0, "1.0", [], {}, tuple(), set(), None, b"byte"]

EDGE_PATHS = [
    tuple(),
    [],
    {},
    set(),
    None,
    b"byte",
    55,
    1.0,
    -1.0,
    "1.0",
]

EDGE_LOG = [55, 1.0, -1.0, [], {}, tuple(), set(), None]

BATCH_TEST_CASES: Final[List[int]] = [100, 300, 500, 1000, 2000]

ST_MESSAGE: Final[str] = "This is a test message for the file reader and writer."

# ----------------------------------------------------------------------------------------------
# EDGE Tests
# ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("edge_value", EDGE_PATHS)
def test_file_reader_edge_constructor_paths(edge_value):
    """Test edge cases for FileReader constructor."""
    # Test with invalid file_paths
    with pytest.raises(FileReaderConstructionError):
        FileReader(
            file_paths=edge_value, retry_limit=0, retry_delay=0.0, backoff_factor=0.0
        )


@pytest.mark.parametrize("edge_value", EDGE_INT)
def test_file_reader_edge_constructor_int(tmp_path, edge_value):
    """Test edge cases for FileReader constructor."""
    temp_files = [tmp_path / "test_1.log", tmp_path / "test_2.log"]
    # Test with invalid retry_limit
    with pytest.raises(FileReaderConstructionError):
        FileReader(temp_files, retry_limit=edge_value)


@pytest.mark.parametrize("edge_value", EDGE_FLOAT)
def test_file_reader_edge_constructor_float(tmp_path, edge_value):
    """Test edge cases for FileReader constructor."""
    temp_files = [tmp_path / "test_1.log", tmp_path / "test_2.log"]

    # Test with invalid retry_delay
    with pytest.raises(FileReaderConstructionError):
        FileReader(temp_files, retry_delay=edge_value)

    # Test with invalid backoff_factor
    with pytest.raises(FileReaderConstructionError):
        FileReader(temp_files, backoff_factor=edge_value)


def test_file_reader_edge_setters(file_reader: FileReader):
    """Test edge cases for FileReader."""

    # Test with empty file_paths
    with pytest.raises(FileReaderSettingsError):
        file_reader.file_paths = []

    # Test with invalid retry_limit
    with pytest.raises(FileReaderSettingsError):
        file_reader.retry_limit = -1

    # Test with invalid retry_delay
    with pytest.raises(FileReaderSettingsError):
        file_reader.retry_delay = -1.0

    # Test with invalid backoff_factor
    with pytest.raises(FileReaderSettingsError):
        file_reader.backoff_factor = -1.0


# ----------------------------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------------------------


def test_file_reader_init(file_reader: FileReader):
    """Test the initialization of FileWriter."""
    assert len(file_reader.file_paths) == 2
    assert file_reader.write_mode == "r"
    assert file_reader.retry_limit == 0
    assert file_reader.retry_delay == pytest.approx(0.0)
    assert file_reader.backoff_factor == pytest.approx(0.0)


# Sync

def test_file_reader_read(file_reader: FileReader, file_writer: FileWriter, tmp_path):
    """Test reading from files."""
    # Create temporary files
    temp_paths: List[Path] = temporary_file_handler(5, tmp_path)
    # Set File Writer paths
    file_writer.file_paths = temp_paths
    # Set File Reader paths
    file_reader.file_paths = temp_paths

    # Write some data to the files
    file_writer.write(message=ST_MESSAGE)

    # Force Buffer Flush
    file_writer.buffer_force_flush()

    # Assert data is written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, mode="r") as f:
            content = f.read()
            assert ST_MESSAGE in content

    # Read the data back
    read_data: ReaderResultPack = file_reader.read()

    len_paths: int = len(temp_paths)

    # Assert data is read
    assert read_data.total_path_count == len_paths, f"Expected {len_paths} paths, got {read_data.total_path_count}"
    assert read_data.total_results_count == len_paths, f"Expected {len_paths} results, got {read_data.total_results_count}"
    assert read_data.success_count == len_paths, f"Expected {len_paths} successes, got {read_data.success_count}"
    assert read_data.failure_count == 0, f"Expected 0 failures, got {read_data.failure_count}"

    # Assert data is read correctly
    for res in read_data.get_all_str_results:
        assert ST_MESSAGE in res.content, f"Expected '{ST_MESSAGE}' in content, got {res.content}"
        
    # Clean up temporary files
    file_writer.clear_all()
    file_reader.clear_all()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0
    assert len(file_writer.file_paths) == 0


def test_file_reader_cm_read(file_reader: FileReader, file_writer: FileWriter, tmp_path):
    """Test reading from files with context manager."""
    # Create temporary files
    temp_paths: List[Path] = temporary_file_handler(5, tmp_path)
    # Set File Writer paths
    file_writer.file_paths = temp_paths
    # Set File Reader paths
    file_reader.file_paths = temp_paths

    with file_writer as fw:
        # Write some data to the files
        fw.write(message=ST_MESSAGE)
    
    # Assert data is written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, "r") as f:
            content = f.read()
            assert ST_MESSAGE in content
    
    # Read the data back using context manager
    with file_reader as fr:
        read_data: ReaderResultPack = fr.read()

    # Assert data is read
    len_paths: int = len(temp_paths)
    assert read_data.total_path_count == len_paths, f"Expected {len_paths} paths, got {read_data.total_path_count}"
    assert read_data.total_results_count == len_paths, f"Expected {len_paths} results, got {read_data.total_results_count}"
    assert read_data.success_count == len_paths, f"Expected {len_paths} successes, got {read_data.success_count}"
    assert read_data.failure_count == 0, f"Expected 0 failures, got {read_data.failure_count}"
    
    # Assert data is read correctly
    for res in read_data.get_all_str_results:
        assert ST_MESSAGE in res.content, f"Expected '{ST_MESSAGE}' in content, got {res.content}"

    # Clean up temporary files
    file_writer.clear_all()
    file_reader.clear_all()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0
    assert len(file_writer.file_paths) == 0


# Sync Generator 

def test_file_reader_read_generator(file_reader: FileReader, file_writer: FileWriter, tmp_path):
    """Test reading from files using generator."""
    # Create temporary files
    temp_paths: List[Path] = temporary_file_handler(5, tmp_path)
    # Set File Writer paths
    file_writer.file_paths = temp_paths
    # Set File Reader paths
    file_reader.file_paths = temp_paths

    # Write some data to the files
    file_writer.write(message=ST_MESSAGE)

    # Force Buffer Flush
    file_writer.buffer_force_flush()

    # Assert data is written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, "r") as f:
            content = f.read()
            assert ST_MESSAGE in content

    # Read the data back using generator
    read_data: ReaderResultPack = file_reader.read_generator()

    # Assert data is read
    len_paths: int = len(temp_paths)
    assert read_data.total_path_count == len_paths, f"Expected {len_paths} paths, got {read_data.total_path_count}"
    assert read_data.total_results_count == len_paths, f"Expected {len_paths} results, got {read_data.total_results_count}"
    assert read_data.success_count == len_paths, f"Expected {len_paths} successes, got {read_data.success_count}"
    assert read_data.failure_count == 0, f"Expected 0 failures, got {read_data.failure_count}"
    
    # Assert data is read correctly
    for res in read_data.get_all_generator_results:
        if res.content is not None:
            assert ST_MESSAGE in "".join(list(res.content)), f"Expected '{ST_MESSAGE}' in content, got {''.join(list(res.content))}"

    # Clean up temporary files
    file_writer.clear_all()
    file_reader.clear_all()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0
    assert len(file_writer.file_paths) == 0


def test_file_reader_cm_read_generator(file_reader: FileReader, file_writer: FileWriter, tmp_path):
    """Test reading from files using generator with context manager."""
    # Create temporary files
    temp_paths: List[Path] = temporary_file_handler(5, tmp_path)
    # Set File Writer paths
    file_writer.file_paths = temp_paths
    # Set File Reader paths
    file_reader.file_paths = temp_paths

    with file_writer as fw:
        # Write some data to the files
        fw.write(message=ST_MESSAGE)

    # Assert data is written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, "r") as f:
            content = f.read()
            assert ST_MESSAGE in content

    # Read the data back using context manager and generator
    with file_reader as fr:
        read_data: ReaderResultPack = fr.read_generator()

    # Assert data is read
    len_paths: int = len(temp_paths)
    assert read_data.total_path_count == len_paths, f"Expected {len_paths} paths, got {read_data.total_path_count}"
    assert read_data.total_results_count == len_paths, f"Expected {len_paths} results, got {read_data.total_results_count}"
    assert read_data.success_count == len_paths, f"Expected {len_paths} successes, got {read_data.success_count}"
    assert read_data.failure_count == 0, f"Expected 0 failures, got {read_data.failure_count}"

    # Assert data is read correctly
    for res in read_data.get_all_generator_results:
        if res.content is not None:
            assert ST_MESSAGE in "".join(list(res.content)), f"Expected '{ST_MESSAGE}' in content, got {''.join(list(res.content))}" 

    # Clean up temporary files
    file_writer.clear_all()
    file_reader.clear_all()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0
    assert len(file_writer.file_paths) == 0


# Async

@pytest.mark.asyncio
async def test_file_reader_async_read(file_reader: FileReader, file_writer: FileWriter, tmp_path):
    """Test reading from files asynchronously."""
    # Create temporary files
    temp_paths: List[Path] = temporary_file_handler(5, tmp_path)
    # Set File Writer paths
    file_writer.file_paths = temp_paths
    # Set File Reader paths
    file_reader.file_paths = temp_paths

    # Write some data to the files
    await file_writer.async_write(message=ST_MESSAGE)

    # Force Buffer Flush
    file_writer.buffer_force_flush()

    # Assert data is written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, "r") as f:
            content = f.read()
            assert ST_MESSAGE in content

    # Read the data back asynchronously
    read_data: ReaderResultPack = await file_reader.async_read()

    # Assert data is read
    len_paths: int = len(temp_paths)
    assert read_data.total_path_count == len_paths, f"Expected {len_paths} paths, got {read_data.total_path_count}"
    assert read_data.total_results_count == len_paths, f"Expected {len_paths} results, got {read_data.total_results_count}"
    assert read_data.success_count == len_paths, f"Expected {len_paths} successes, got {read_data.success_count}"
    assert read_data.failure_count == 0

    # Assert data is read correctly
    for res in read_data.get_all_str_results:
        assert ST_MESSAGE in res.content, f"Expected '{ST_MESSAGE}' in content, got {res.content}"

    # Clean up temporary files
    file_writer.clear_all()
    file_reader.clear_all()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0
    assert len(file_writer.file_paths) == 0


@pytest.mark.asyncio
async def test_file_reader_cm_async_read(file_reader: FileReader, file_writer: FileWriter, tmp_path):
    """Test reading from files asynchronously with context manager."""
    # Create temporary files
    temp_paths: List[Path] = temporary_file_handler(5, tmp_path)
    # Set File Writer paths
    file_writer.file_paths = temp_paths
    # Set File Reader paths
    file_reader.file_paths = temp_paths

    async with file_writer as fw:
        # Write some data to the files
        await fw.async_write(message=ST_MESSAGE)

    # Assert data is written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, "r") as f:
            content = f.read()
            assert ST_MESSAGE in content

    # Read the data back asynchronously using context manager
    async with file_reader as fr:
        read_data: ReaderResultPack = await fr.async_read()

    # Assert data is read
    len_paths: int = len(temp_paths)
    assert read_data.total_path_count == len_paths, f"Expected {len_paths} paths, got {read_data.total_path_count}"
    assert read_data.total_results_count == len_paths, f"Expected {len_paths} results, got {read_data.total_results_count}"
    assert read_data.success_count == len_paths, f"Expected {len_paths} successes, got {read_data.success_count}"
    assert read_data.failure_count == 0, f"Expected 0 failures, got {read_data.failure_count}"

    # Assert data is read correctly
    for res in read_data.get_all_str_results:
        assert ST_MESSAGE in res.content, f"Expected '{ST_MESSAGE}' in content, got {res.content}"

    # Clean up temporary files
    file_writer.clear_all()
    file_reader.clear_all()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0
    assert len(file_writer.file_paths) == 0


# Async Generator

@pytest.mark.asyncio
async def test_file_reader_async_read_generator(file_reader: FileReader, file_writer: FileWriter, tmp_path):
    """Test reading from files asynchronously using generator."""
    # Create temporary files
    temp_paths: List[Path] = temporary_file_handler(5, tmp_path)
    # Set File Writer paths
    file_writer.file_paths = temp_paths
    # Set File Reader paths
    file_reader.file_paths = temp_paths

    # Write some data to the files
    await file_writer.async_write(message=ST_MESSAGE)

    # Force Buffer Flush
    file_writer.buffer_force_flush()

    # Assert data is written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, "r") as f:
            content = f.read()
            assert ST_MESSAGE in content

    # Read the data back asynchronously using generator
    read_data: ReaderResultPack = await file_reader.async_read_generator()

    # Assert data is read
    len_paths: int = len(temp_paths)
    assert read_data.total_path_count == len_paths, f"Expected {len_paths} paths, got {read_data.total_path_count}"
    assert read_data.total_results_count == len_paths, f"Expected {len_paths} results, got {read_data.total_results_count}"
    assert read_data.success_count == len_paths, f"Expected {len_paths} successes, got {read_data.success_count}"
    assert read_data.failure_count == 0, f"Expected 0 failures, got {read_data.failure_count}"

    # Assert data is read correctly
    for res in read_data.get_all_generator_results:
        if res.content is not None:
            assert ST_MESSAGE in "".join(list(res.content)), f"Expected '{ST_MESSAGE}' in content, got {''.join(list(res.content))}"

    # Clean up temporary files
    file_writer.clear_all()
    file_reader.clear_all()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0
    assert len(file_writer.file_paths) == 0


@pytest.mark.asyncio
async def test_file_reader_cm_async_read_generator(file_reader: FileReader, file_writer: FileWriter, tmp_path):
    """Test reading from files asynchronously using generator with context manager."""
    # Create temporary files
    temp_paths: List[Path] = temporary_file_handler(5, tmp_path)
    # Set File Writer paths
    file_writer.file_paths = temp_paths
    # Set File Reader paths
    file_reader.file_paths = temp_paths

    async with file_writer as fw:
        # Write some data to the files
        await fw.async_write(message=ST_MESSAGE)

    # Assert data is written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, "r") as f:
            content = f.read()
            assert ST_MESSAGE in content

    # Read the data back asynchronously using context manager and generator
    async with file_reader as fr:
        read_data: ReaderResultPack = await fr.async_read_generator()

    # Assert data is read
    len_paths: int = len(temp_paths)
    assert read_data.total_path_count == len_paths, f"Expected {len_paths} paths, got {read_data.total_path_count}"
    assert read_data.total_results_count == len_paths, f"Expected {len_paths} results, got {read_data.total_results_count}"
    assert read_data.success_count == len_paths, f"Expected {len_paths} successes, got {read_data.success_count}"
    assert read_data.failure_count == 0, f"Expected 0 failures, got {read_data.failure_count}"

    # Assert data is read correctly
    for res in read_data.get_all_generator_results:
        if res.content is not None:
            assert ST_MESSAGE in "".join(list(res.content)), f"Expected '{ST_MESSAGE}' in content, got {''.join(list(res.content))}"

    # Clean up temporary files
    file_writer.clear_all()
    file_reader.clear_all()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0
    assert len(file_writer.file_paths) == 0


# ----------------------------------------------------------------------------------------------
# Functionality Tests
# ----------------------------------------------------------------------------------------------

def test_thread_safety(file_reader: FileReader, file_writer: FileWriter, tmp_path):
    """Test thread safety with concurrent writes and reads."""
    # Create temporary files
    temp_file =[tmp_path / "thread_test_1.log", tmp_path / "thread_test_2.log"]

    try:
        # Set File Writer paths
        file_writer.file_paths = temp_file
        # Set File Reader paths
        file_reader.file_paths = temp_file

        def write_messages():
            for i in range(100):
                file_writer.write(ST_MESSAGE + f" Thread message {i}")

        # Create multiple threads - 5
        threads = [threading.Thread(target=write_messages) for _ in range(5)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Force the file handler to flush the buffer
        file_writer.buffer_force_flush()

        # Verify all messages were written
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                write_result = f.read()
                for _ in range(100):
                    assert ST_MESSAGE in write_result
        
        # Read the data back
        def read_messages(pack: ReaderResultPack):
            read_data: ReaderResultPack = file_reader.read()
            pack += read_data
            return pack

        # Create a shared list to store results from threads
        pack: ReaderResultPack = ReaderResultPack()

        # Create multiple threads for reading - 5
        read_threads = [
            threading.Thread(target=read_messages, args=(pack,))
            for _ in range(5)
        ]

        # Start all read threads
        for thread in read_threads:
            thread.start()

        # Wait for all read threads to complete
        for thread in read_threads:
            thread.join()

        # Assert results
        assert pack.has_failed_results == False, "There should be no failed results"
        assert pack.has_successful_results == True, "There should be successful results"

        # Assert that all messages were read correctly
        assert any(ST_MESSAGE in res.content for res in pack.get_all_str_results), "All messages should be present in the read results"

        pack.clear_results()

    finally:
        # Ensure that the file paths are cleared in case of any exceptions
        file_reader.clear_all()
        file_writer.clear_all()
        assert len(file_reader.file_paths) == 0, "File paths should be cleared after operations"
        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"

        for path in temp_file:
            if path.exists():
                path.unlink()


@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
def test_memory_usage(file_reader: FileReader, file_writer: FileWriter, tmp_path, batch_size: int):
    """
    Test memory usage during file operations.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u
    """

    # Create a FileHandler instance
    temp_file = [tmp_path / "memory_test_1.log", tmp_path / "memory_test_2.log"]
    # Set File Writer paths
    file_writer.file_paths = temp_file
    # Set File Reader paths
    file_reader.file_paths = temp_file

    # Write some logs
    for i in range(batch_size):
        file_writer.write(f"Memory test message {i}")

    # Force the file handler to flush the buffer
    file_writer.buffer_force_flush()

    # Assert hat message was written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, "r") as f:
            read = f.read()
            assert len(read) > 0, "File should not be empty after writing logs"
            assert "Memory test message" in read, "Messages should be present in the file"

    # Cleanup
    file_writer.clear_all()

        # Assert that the file paths are cleared
    assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"

    del file_writer

    gc.collect()  # Force garbage collection

    print("Testing memory usage of for batch size:", batch_size)

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss  # Resident Set Size
    initial_memory_mb = round(initial_memory / (1024 * 1024), 2)  # Convert to MB
    initial_memory_kb = round(initial_memory / 1024, 2)  # Convert to KB

    print(
        f"Initial memory usage: {initial_memory} bytes ({initial_memory_kb} KB, {initial_memory_mb} MB)"
    )

    # Read the data back
    read_data: ReaderResultPack = file_reader.read()

    after_memory = process.memory_info().rss  # Resident Set Size after logging
    after_memory_mb = round(after_memory / (1024 * 1024), 2)  # Convert to MB
    after_memory_kb = round(after_memory / 1024, 2)  # Convert to KB
    print(
        f"After memory usage: {after_memory} bytes ({after_memory_kb} KB, {after_memory_mb} MB)"
    )

    leak_memory_kb = round((after_memory - initial_memory) / 1024, 2)  # Convert to KB
    leak_memory_mb = round(
        (after_memory - initial_memory) / (1024 * 1024), 2
    )  # Convert to MB
    print(
        f"Memory difference for {batch_size} messages: {leak_memory_kb} KB ({leak_memory_mb} MB)"
    )

    # Assert Reading is done
    assert read_data.total_path_count == 2, f"Expected 2 paths, got {read_data.total_path_count}"
    assert read_data.total_results_count == 2, f"Expected 2 results, got {read_data.total_results_count}"
    assert read_data.success_count == 2, f"Expected 2 successes, got {read_data.success_count}"
    assert read_data.failure_count == 0, f"Expected 0 failures, got {read_data.failure_count}"

    # Assert data is read correctly
    for path in temp_file:
        str_content: List[str] = read_data.get_content(path)
        assert len(str_content) > 0, f"file {path} should not be empty after reading"
        assert any("Memory test message" in line for line in str_content), f"Messages should be present in the file {path}"

    # Cleanup
    file_reader.clear_all()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0, "File paths should be cleared after operations"

    del file_reader
    gc.collect()  # Force garbage collection


@pytest.mark.asyncio
@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
async def test_memory_usage_async(file_reader: FileReader, file_writer: FileWriter, tmp_path, batch_size: int):
    """
    Test memory usage during asynchronous file operations.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u
    """

    # Create a FileHandler instance
    temp_file = temporary_file_handler(batch_size, tmp_path)
    # Set File Writer paths
    file_writer.file_paths = temp_file
    # Set File Reader paths
    file_reader.file_paths = temp_file

    # Write some logs asynchronously
    await file_writer.async_write(ST_MESSAGE)

    # Force the file handler to flush the buffer
    file_writer.buffer_force_flush()

    # Assert that message was written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, "r") as f:
            read = f.read()
            assert len(read) > 0, "File should not be empty after writing logs"
            assert ST_MESSAGE in read, "Messages should be present in the file"

    # Cleanup
    file_writer.clear_all()

        # Assert that the file paths are cleared
    assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"

    del file_writer

    gc.collect()  # Force garbage collection
    print("Testing memory usage of for batch size:", batch_size)

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss  # Resident Set Size
    initial_memory_mb = round(initial_memory / (1024 * 1024), 2)
    initial_memory_kb = round(initial_memory / 1024, 2)
    print(
        f"Initial memory usage: {initial_memory} bytes ({initial_memory_kb} KB, {initial_memory_mb} MB)"
    )

    # Read the data back asynchronously
    read_data: ReaderResultPack = await file_reader.async_read()

    after_memory = process.memory_info().rss  # Resident Set Size after logging
    after_memory_mb = round(after_memory / (1024 * 1024), 2)
    after_memory_kb = round(after_memory / 1024, 2)
    print(
        f"After memory usage: {after_memory} bytes ({after_memory_kb} KB, {after_memory_mb} MB)"
    )

    leak_memory_kb = round((after_memory - initial_memory) / 1024, 2)
    leak_memory_mb = round(
        (after_memory - initial_memory) / (1024 * 1024), 2
    )

    print(
        f"Memory difference for {batch_size} messages: {leak_memory_kb} KB ({leak_memory_mb} MB)"
    )

    # Assert Reading is done
    assert read_data.total_path_count == batch_size, f"Expected {batch_size} paths, got {read_data.total_path_count}"
    assert read_data.total_results_count == batch_size, f"Expected {batch_size} results, got {read_data.total_results_count}"
    assert read_data.success_count == batch_size, f"Expected {batch_size} successes, got {read_data.success_count}"
    assert read_data.failure_count == 0, f"Expected 0 failures, got {read_data.failure_count}"

    # Assert data is read correctly
    for path in temp_file:
        str_content: List[str] = read_data.get_content(path)
        assert len(str_content) > 0, f"file {path} should not be empty after reading"
        assert any(ST_MESSAGE in line for line in str_content), f"Messages should be present in the file {path}"

    # Cleanup
    file_reader.clear_all()
    read_data.clear_results()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0, "File paths should be cleared after operations"

    del file_reader
    del read_data

    gc.collect()  # Force garbage collection
    print("Memory usage test completed for batch size:", batch_size)


# ----------------------------------------------------------------------------------------------
# Performance Tests
# ----------------------------------------------------------------------------------------------

# Sync

@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
def test_file_reader_performance(file_reader: FileReader, file_writer: FileWriter, tmp_path, batch_size: int):
    """
    Test performance of file reading and writing operations.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u
    """

    # Create a FileHandler instance
    temp_file = temporary_file_handler(batch_size, tmp_path)
    # Set File Writer paths
    file_writer.file_paths = temp_file
    # Set File Reader paths
    file_reader.file_paths = temp_file

    start_time = time.time()

    # Write some logs
    with file_writer as fw:
        fw.write(ST_MESSAGE)

    # Force the file handler to flush the buffer
    file_writer.buffer_force_flush()

    end_time = time.time()
    
    elapsed_time = end_time - start_time
    print(f"\nTime taken to write {batch_size} logs: {elapsed_time:.4f} seconds")

    # Assert that message was written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, "r") as f:
            read = f.read()
            assert len(read) > 0, "Messages file should not be empty after writing logs"
            assert ST_MESSAGE in read, "Messages should be present in the file"

    # Cleanup
    file_writer.clear_all()

    # Assert that the file paths are cleared
    assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"

    # Delete the file_writer to force garbage collection
    del file_writer

    gc.collect()  # Force garbage collection

    # Read the data back
    start_time = time.time()

    with file_reader as fr:
        read_data: ReaderResultPack = fr.read()

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"Time taken to read {batch_size} messages: {elapsed_time:.4f} seconds")
    print(f"Read Data: {read_data}")

    # Assert Reading is done
    assert read_data.has_failed_results == False, "There should be no failed results"
    assert read_data.has_successful_results == True, "There should be successful results"
    assert read_data.total_path_count == batch_size, f"Expected {batch_size} paths, got {read_data.total_path_count}"
    assert read_data.total_results_count == batch_size, f"Expected {batch_size} results got {read_data.total_results_count}"
    assert read_data.success_count == batch_size, f"Expected {batch_size} successes, got {read_data.success_count}"

    # Cleanup
    file_reader.clear_all()
    read_data.clear_results()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0, "File paths should be cleared after operations"


@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
def test_file_reader_cm_performance(file_reader: FileReader, file_writer: FileWriter, tmp_path, batch_size: int):
    """
    Test performance of file reading and writing operations using context manager.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u
    """

    # Create a FileHandler instance
    temp_file = temporary_file_handler(batch_size, tmp_path)
    # Set File Writer paths
    file_writer.file_paths = temp_file
    # Set File Reader paths
    file_reader.file_paths = temp_file

    start_time = time.time()

    with file_writer as fw:
        # Write some logs
        fw.write(ST_MESSAGE)

        # Force the file handler to flush the buffer
        fw.buffer_force_flush()

    end_time = time.time()
    
    elapsed_time = end_time - start_time
    print(f"\nTime taken to write {batch_size} logs using context manager: {elapsed_time:.4f} seconds")

    # Assert that message was written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, "r") as f:
            read = f.read()
            assert len(read) > 0, "Log file should not be empty after writing logs"
            assert ST_MESSAGE in read, "Log messages should be present in the file"

    # Cleanup
    file_writer.clear_all()

        # Assert that the file paths are cleared
    assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"

    # Delete the file_writer to force garbage collection
    del file_writer

    gc.collect() # Force garbage collection

    # Read the data back using context manager
    start_time = time.time()
    
    with file_reader as fr:
       read_data: ReaderResultPack = fr.read()

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"Time taken to read {batch_size} logs using context manager: {elapsed_time:.4f} seconds")

    # Assert Reading is done
    assert read_data.has_failed_results == False, "There should be no failed results"
    assert read_data.has_successful_results == True, "There should be successful results"
    assert read_data.success_count == batch_size, f"Expected {batch_size} successes, got {read_data.success_count}"

    # Cleanup
    file_reader.clear_all()
    read_data.clear_results()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0, "File paths should be cleared after operations"


# Generator Sync

@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
def test_file_reader_performance_generator(file_reader: FileReader, file_writer: FileWriter, tmp_path, batch_size: int):
    """
    Test performance of file reading and writing operations using generator.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u
    """

    # Create a FileHandler instance
    temp_file = temporary_file_handler(batch_size, tmp_path)
    # Set File Writer paths
    file_writer.file_paths = temp_file
    # Set File Reader paths
    file_reader.file_paths = temp_file

    start_time = time.time()

    # Write some logs
    file_writer.write(ST_MESSAGE)

    # Force the file handler to flush the buffer
    file_writer.buffer_force_flush()

    end_time = time.time()
    
    elapsed_time = end_time - start_time
    print(f"\nTime taken to write {batch_size} messages using generator: {elapsed_time:.4f} seconds")

    # Assert that message was written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, "r") as f:
            read = f.read()
            assert len(read) > 0, "File should not be empty after writing messages"
            assert ST_MESSAGE in read, "Messages should be present in the file"

    # Cleanup
    file_writer.clear_all()

        # Assert that the file paths are cleared
    assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"

    # Delete the file_writer to force garbage collection
    del file_writer

    gc.collect() # Force garbage collection

    # Read the data back using generator
    start_time = time.time()
    read_data: ReaderResultPack = file_reader.read_generator()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"-[No unpacking] - Time taken to read {batch_size} messages using generator: {elapsed_time:.4f} seconds")

    # Unpack the generator to read data
    start_time = time.time()
    read_data.in_unpack()

    end_time = time.time()
    elapsed_time_unpacking = end_time - start_time
    print(f"-[Unpacking] - Time taken to unpack {batch_size} messages using generator: {elapsed_time_unpacking:.4f} seconds")
    print(f"Total time taken to read and unpack {batch_size} messages using generator: {elapsed_time + elapsed_time_unpacking:.4f} seconds")

    # Assert Reading is done
    assert read_data.has_failed_results == False, "There should be no failed results"
    assert read_data.has_successful_results == True, "There should be successful results"
    assert read_data.success_count == batch_size, f"Expected {batch_size} successes, got {read_data.success_count}"

    # Cleanup
    file_reader.clear_all()
    read_data.clear_results()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0, "File paths should be cleared after operations"


@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
def test_file_reader_cm_performance_generator(file_reader: FileReader, file_writer: FileWriter, tmp_path, batch_size: int):
    """
    Test performance of file reading and writing operations using generator with context manager.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u
    """

    # Create a FileHandler instance
    temp_file = temporary_file_handler(batch_size, tmp_path)
    # Set File Writer paths
    file_writer.file_paths = temp_file
    # Set File Reader paths
    file_reader.file_paths = temp_file

    start_time = time.time()

    with file_writer as fw:
        # Write some logs
        fw.write(ST_MESSAGE)

        # Force the file handler to flush the buffer
        fw.buffer_force_flush()

    end_time = time.time()
    
    elapsed_time = end_time - start_time
    print(f"\nTime taken to write {batch_size} messages using context manager and generator: {elapsed_time:.4f} seconds")

    # Assert that message was written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, "r") as f:
            read = f.read()
            assert len(read) > 0, "File should not be empty after writing messages"
            assert ST_MESSAGE in read, "Messages should be present in the file"

    # Cleanup
    file_writer.clear_all()

        # Assert that the file paths are cleared
    assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"

    # Delete the file_writer to force garbage collection
    del file_writer

    gc.collect() # Force garbage collection

    # Read the data back using context manager and generator
    start_time = time.time()
    with file_reader as fr:
        read_data: ReaderResultPack = fr.read_generator()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"-[No unpacking] - Time taken to read {batch_size} messages using context manager and generator: {elapsed_time:.4f} seconds")

    # Unpack the generator to read data
    start_time = time.time()
    read_data.in_unpack()
    
    end_time = time.time()
    elapsed_time_unpacking = end_time - start_time
    print(f"-[Unpacking] - Time taken to unpack {batch_size} messages using context manager and generator: {elapsed_time_unpacking:.4f} seconds")
    print(f"Total time taken to read and unpack {batch_size} messages using context manager and generator: {elapsed_time + elapsed_time_unpacking:.4f} seconds")

    # Assert Reading is done
    assert read_data.has_failed_results == False, "There should be no failed results"
    assert read_data.has_successful_results == True, "There should be successful results"
    assert read_data.success_count == batch_size, f"Expected {batch_size} successes, got {read_data.success_count}"

    # Cleanup
    file_reader.clear_all()
    read_data.clear_results()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0, "File paths should be cleared after operations"


# Async

@pytest.mark.asyncio
@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
async def test_file_reader_performance_async(file_reader: FileReader, file_writer: FileWriter, tmp_path, batch_size: int):
    """
    Test performance of asynchronous file reading and writing operations.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u
    """

    # Create a FileHandler instance
    temp_file = temporary_file_handler(batch_size, tmp_path)
    # Set File Writer paths
    file_writer.file_paths = temp_file
    # Set File Reader paths
    file_reader.file_paths = temp_file

    start_time = time.time()

    # Write some logs asynchronously
    await file_writer.async_write(ST_MESSAGE)

    # Force the file handler to flush the buffer
    file_writer.buffer_force_flush()

    end_time = time.time()
    
    elapsed_time = end_time - start_time
    print(f"\nTime taken to write {batch_size} messages asynchronously: {elapsed_time:.4f} seconds")

    # Assert that message was written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, "r") as f:
            read = f.read()
            assert len(read) > 0, "File should not be empty after writing messages"
            assert ST_MESSAGE in read, "Messages should be present in the file"

    # Cleanup
    file_writer.clear_all()

        # Assert that the file paths are cleared
    assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"

    # Delete the file_writer to force garbage collection
    del file_writer

    gc.collect() # Force garbage collection

    # Read the data back asynchronously

    start_time = time.time()
    read_data: ReaderResultPack = await file_reader.async_read()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Time taken to read {batch_size} messages asynchronously: {elapsed_time:.4f} seconds")

    # Assert Reading is done
    for path in temp_file:
        content: List[str] = read_data.get_content(path)
        assert len(content) > 0, f"File {path} should not be empty"
        assert ST_MESSAGE in content, f"Messages should be present in the file {path}"

    # Cleanup
    file_reader.clear_all()
    read_data.clear_results()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0, "File paths should be cleared after operations"


@pytest.mark.asyncio
@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
async def test_file_reader_cm_performance_async(file_reader: FileReader, file_writer: FileWriter, tmp_path, batch_size: int):
    """
    Test performance of asynchronous file reading and writing operations using context manager.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u
    """

    # Create a FileHandler instance
    temp_file = temporary_file_handler(batch_size, tmp_path)
    # Set File Writer paths
    file_writer.file_paths = temp_file
    # Set File Reader paths
    file_reader.file_paths = temp_file

    start_time = time.time()

    async with file_writer as fw:
        # Write some logs asynchronously
        await fw.async_write(ST_MESSAGE)

        # Force the file handler to flush the buffer
        fw.buffer_force_flush()

    end_time = time.time()
    
    elapsed_time = end_time - start_time
    print(f"\nTime taken to write {batch_size} messages asynchronously using context manager: {elapsed_time:.4f} seconds")

    # Assert that message was written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, "r") as f:
            read = f.read()
            assert len(read) > 0, "File should not be empty after writing messages"
            assert ST_MESSAGE in read, "Messages should be present in the file"

    # Cleanup
    file_writer.clear_all()

        # Assert that the file paths are cleared
    assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"

    # Delete the file_writer to force garbage collection
    del file_writer

    gc.collect() # Force garbage collection

    # Read the data back asynchronously using context manager

    start_time = time.time()
    async with file_reader as fr:
        data_read: ReaderResultPack = await fr.async_read()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Time taken to read {batch_size} messages asynchronously using context manager: {elapsed_time:.4f} seconds")

    # Assert Reading is done
    for path in temp_file:
        content: List[str] = data_read.get_content(path)
        assert len(content) > 0, f"File {path} should not be empty"
        assert ST_MESSAGE in content, f"Messages should be present in the file {path}"

    # Cleanup
    file_reader.clear_all()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0, "File paths should be cleared after operations"


# Async Generator

@pytest.mark.asyncio
@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
async def test_file_reader_performance_async_generator(file_reader: FileReader, file_writer: FileWriter, tmp_path, batch_size: int):
    """
    Test performance of asynchronous file reading operations using generator.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u
    """

    # Create a FileHandler instance
    temp_file = temporary_file_handler(batch_size, tmp_path)
    # Set File Writer paths
    file_writer.file_paths = temp_file
    # Set File Reader paths
    file_reader.file_paths = temp_file

    start_time = time.time()

    # Write some logs asynchronously
    await file_writer.async_write(ST_MESSAGE)

    # Force the file handler to flush the buffer
    file_writer.buffer_force_flush()

    end_time = time.time()
    
    elapsed_time = end_time - start_time
    print(f"\nTime taken to write {batch_size} messages asynchronously using generator: {elapsed_time:.4f} seconds")

    # Assert that message was written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, "r") as f:
            read = f.read()
            assert len(read) > 0, "File should not be empty after writing messages"
            assert ST_MESSAGE in read, "Messages should be present in the file"

    # Cleanup
    file_writer.clear_all()

    # Assert that the file paths are cleared
    assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"

    # Delete the file_writer to force garbage collection
    del file_writer

    gc.collect() # Force garbage collection

    # Read the data back asynchronously using generator
    start_time = time.time()
    read_data: ReaderResultPack = await file_reader.async_read_generator()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"-[No unpacking] - Time taken to read {batch_size} messages asynchronously using generator: {elapsed_time:.4f} seconds")

    # Unpack the generator to read data
    start_time = time.time()
    read_data.in_unpack()

    end_time = time.time()
    elapsed_time_unpacking = end_time - start_time
    print(f"-[Unpacking] - Time taken to unpack {batch_size} messages asynchronously using generator: {elapsed_time_unpacking:.4f} seconds")
    print(f"Total time taken to read and unpack {batch_size} messages asynchronously using generator: {elapsed_time + elapsed_time_unpacking:.4f} seconds")

    # Assert Reading is done
    for path in temp_file:
        content: List[str] = read_data.get_content(path)
        assert len(content) > 0, f"File {path} should not be empty"
        assert ST_MESSAGE in content, f"Messages should be present in the file {path}"

    # Cleanup
    file_reader.clear_all()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0, "File paths should be cleared after operations"


@pytest.mark.asyncio
@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
async def test_file_reader_cm_performance_async_generator(file_reader: FileReader, file_writer: FileWriter, tmp_path, batch_size: int):
    """
    Test performance of asynchronous file reading operations using generator with context manager.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u
    """

    # Create a FileHandler instance
    temp_file = temporary_file_handler(batch_size, tmp_path)
    # Set File Writer paths
    file_writer.file_paths = temp_file
    # Set File Reader paths
    file_reader.file_paths = temp_file

    start_time = time.time()

    async with file_writer as fw:
        # Write some logs asynchronously
        await fw.async_write(ST_MESSAGE)

        # Force the file handler to flush the buffer
        fw.buffer_force_flush()

    end_time = time.time()
    
    elapsed_time = end_time - start_time
    print(f"\nTime taken to write {batch_size} messages asynchronously using context manager and generator: {elapsed_time:.4f} seconds")

    # Assert that message was written correctly
    for file_path in file_writer:
        assert file_path.exists()
        with open(file_path, "r") as f:
            read = f.read()
            assert len(read) > 0, "File should not be empty after writing messages"
            assert ST_MESSAGE in read, "Messages should be present in the file"

    # Cleanup
    file_writer.clear_all()

    # Assert that the file paths are cleared
    assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"

    # Delete the file_writer to force garbage collection
    del file_writer

    gc.collect() # Force garbage collection

    # Read the data back asynchronously using context manager and generator
    start_time = time.time()
    async with file_reader as fr:
        read_data: ReaderResultPack = await fr.async_read_generator()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"-[No unpacking] - Time taken to read {batch_size} messages asynchronously using context manager and generator: {elapsed_time:.4f} seconds")

    # Unpack the generator to read data
    start_time = time.time()
    read_data.in_unpack()
    
    end_time = time.time()
    elapsed_time_unpacking = end_time - start_time
    print(f"-[Unpacking] - Time taken to unpack {batch_size} messages asynchronously using context manager and generator: {elapsed_time_unpacking:.4f} seconds")
    print(f"Total time taken to read and unpack {batch_size} messages asynchronously using context manager and generator: {elapsed_time + elapsed_time_unpacking:.4f} seconds")

    # Assert Reading is done
    assert ST_MESSAGE in read_data.get_full_report

    # Cleanup
    file_reader.clear_all()
    read_data.clear_results()

    # Assert that the file paths are cleared
    assert len(file_reader.file_paths) == 0, "File paths should be cleared after operations"


# ----------------------------------------------------------------------------------------------
# ClassMethods Tests
# ----------------------------------------------------------------------------------------------

def test_from_dict(tmp_path):
    tmp_list: List[Path] = temporary_file_handler(2, tmp_path)

    config_dict: Dict[str, Any] = {
        "file_paths" : tmp_list,
        "retry_limit" : 10,
        "retry_delay" : 0.5,
        "backoff_factor" : 0.5
    }

    my_file_reader: FileReader = FileReader.from_dict(config_dict)

    assert len(my_file_reader) == 2
    assert my_file_reader.file_paths == tmp_list
    assert my_file_reader.retry_limit == 10
    assert my_file_reader.retry_delay == pytest.approx(0.5)
    assert my_file_reader.backoff_factor == pytest.approx(0.5)


def test_from_json(tmp_path):
    tmp_list: List[Path] = temporary_file_handler(2, tmp_path)

    config_dict: Dict[str, Any] = {
        "file_paths": [str(path) for path in tmp_list],
        "retry_limit": 10,
        "retry_delay": 0.5,
        "backoff_factor": 0.5,
    }

    json_str: str = json.dumps(config_dict)

    my_file_reader: FileReader = FileReader.from_json(json_str)

    assert len(my_file_reader) == 2
    assert my_file_reader.file_paths == tmp_list
    assert my_file_reader.retry_limit == 10
    assert my_file_reader.retry_delay == pytest.approx(0.5)
    assert my_file_reader.backoff_factor == pytest.approx(0.5)


def test_from_yaml(tmp_path):
    tmp_list: List[Path] = temporary_file_handler(2, tmp_path)

    config_dict: Dict[str, Any] = {
        "file_paths": [str(path) for path in tmp_list],
        "retry_limit": 10,
        "retry_delay": 0.5,
        "backoff_factor": 0.5,
    }

    yaml_str: str = yaml.dump(config_dict)

    my_file_reader: FileReader = FileReader.from_yaml(yaml_str)

    assert len(my_file_reader) == 2
    assert my_file_reader.file_paths == tmp_list
    assert my_file_reader.retry_limit == 10
    assert my_file_reader.retry_delay == pytest.approx(0.5)
    assert my_file_reader.backoff_factor == pytest.approx(0.5)


# ----------------------------------------------------------------------------------------------
# Config Tests
# ----------------------------------------------------------------------------------------------

def test_file_reader_config_from_dict(file_reader: FileReader, tmp_path):
    """Test configuration of FileReader using a dictionary."""
    temp_files = [tmp_path / "test_1.log", tmp_path / "test_2.log"]
    config = {
        "file_paths": temp_files,
        "retry_limit": 3,
        "retry_delay": 0.5,
        "backoff_factor": 0.1,
    }

    file_reader.config_from_dict(config)

    assert file_reader.file_paths == temp_files
    assert file_reader.retry_limit == 3
    assert file_reader.retry_delay == pytest.approx(0.5)
    assert file_reader.backoff_factor == pytest.approx(0.1)


def test_file_reader_config_from_json(file_reader: FileReader, tmp_path):
    """Test configuration of FileReader using a JSON file."""
    temp_files = [tmp_path / "test_1.log", tmp_path / "test_2.log"]
    config = {
        "file_paths": [str(path) for path in temp_files],
        "retry_limit": 3,
        "retry_delay": 0.5,
        "backoff_factor": 0.1,
    }

    json_str: str = json.dumps(config)

    file_reader.config_from_json(json_str)

    assert file_reader.file_paths == temp_files
    assert file_reader.retry_limit == 3
    assert file_reader.retry_delay == pytest.approx(0.5)
    assert file_reader.backoff_factor == pytest.approx(0.1)


def test_file_reader_config_from_yaml(file_reader: FileReader, tmp_path):
    """Test configuration of FileReader using a YAML file."""
    temp_files = [tmp_path / "test_1.log", tmp_path / "test_2.log"]
    config = {
        "file_paths": [str(path) for path in temp_files],
        "retry_limit": 3,
        "retry_delay": 0.5,
        "backoff_factor": 0.1,
    }
    yaml_file: str = yaml.dump(config)

    file_reader.config_from_yaml(yaml_file)

    assert file_reader.file_paths == temp_files
    assert file_reader.retry_limit == 3
    assert file_reader.retry_delay == pytest.approx(0.5)
    assert file_reader.backoff_factor == pytest.approx(0.1)


# ----------------------------------------------------------------------------------------------
# Pool Methods
# ---------------------------------------------------------------------------------------------- 

def test_file_reader_force_shutdown(file_reader: FileReader):
    """Test force shutdown of the thread pool."""
    assert file_reader.is_pool_active()
    file_reader.force_shutdown()
    assert file_reader.is_pool_shutdown()


def test_file_reader_resume_pool(file_reader: FileReader):
    """Test resuming the thread pool."""
    file_reader.force_shutdown()
    assert file_reader.is_pool_shutdown()
    file_reader.resume_pool()
    assert file_reader.is_pool_active()


