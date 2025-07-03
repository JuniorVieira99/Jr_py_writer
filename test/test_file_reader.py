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
from jr_file_handler.classes.file_writer import FileWriter
from jr_file_handler.classes.file_reader import FileReader


# Exceptions Reader
from jr_file_handler.exceptions.exceptions_file_reader import (
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
    (),
    set(),
    None,
    b"byte",
]

EDGE_FLOAT = [-1.0, "1.0", [], {}, (), set(), None, b"byte"]

EDGE_PATHS = [
    (),
    {},
    set(),
    b"byte",
    55,
    1.0,
    -1.0,
    "1.0",
]

EDGE_LOG = [55, 1.0, -1.0, [], {}, (), set(), None]

BATCH_TEST_CASES: Final[List[int]] = [100, 300, 500, 1000, 2000]

ST_MESSAGE: Final[str] = "This is a test message for the file reader and writer."

# ----------------------------------------------------------------------------------------------
# EDGE Tests
# ----------------------------------------------------------------------------------------------


class TestFileReaderEdgeCases:
    """
    Test edge cases for FileReader.

    Tests:
    -------
    - **test_file_reader_edge_constructor_paths:**
        - Test edge cases for FileReader constructor with invalid file_paths.
    - **test_file_reader_edge_constructor_int:**
        - Test edge cases for FileReader constructor with invalid retry_limit.
    - **test_file_reader_edge_constructor_float:**
        - Test edge cases for FileReader constructor with invalid retry_delay and backoff_factor.
    - **test_file_reader_edge_setters:**
        - Test edge cases for FileReader setters with invalid values.
    """

    @pytest.mark.parametrize("edge_value", EDGE_PATHS)
    def test_file_reader_edge_constructor_paths(self, edge_value):
        """Test edge cases for FileReader constructor."""
        # Test with invalid file_paths
        with pytest.raises(FileReaderConstructionError):
            FileReader(
                file_paths=edge_value,
                retry_limit=0,
                retry_delay=0.0,
                backoff_factor=0.0,
            )

    @pytest.mark.parametrize("edge_value", EDGE_INT)
    def test_file_reader_edge_constructor_int(self, tmp_path, edge_value):
        """Test edge cases for FileReader constructor."""
        temp_files = [tmp_path / "test_1.log", tmp_path / "test_2.log"]
        # Test with invalid retry_limit
        with pytest.raises(FileReaderConstructionError):
            FileReader(temp_files, retry_limit=edge_value)

    @pytest.mark.parametrize("edge_value", EDGE_FLOAT)
    def test_file_reader_edge_constructor_float(self, tmp_path, edge_value):
        """Test edge cases for FileReader constructor."""
        temp_files = [tmp_path / "test_1.log", tmp_path / "test_2.log"]

        # Test with invalid retry_delay
        with pytest.raises(FileReaderConstructionError):
            FileReader(temp_files, retry_delay=edge_value)

        # Test with invalid backoff_factor
        with pytest.raises(FileReaderConstructionError):
            FileReader(temp_files, backoff_factor=edge_value)

    def test_file_reader_edge_setters(self, file_reader: FileReader):
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


class TestFileReaderInitialization:
    """
    Test the initialization of FileReader.

    Tests:
    -------
    - **test_file_reader_init:**
        - Test the initialization of FileReader with default parameters.
    """

    def test_file_reader_init(self, file_reader: FileReader):
        """Test the initialization of FileWriter."""
        assert len(file_reader.file_paths) == 2
        assert file_reader.write_mode == "r"
        assert file_reader.retry_limit == 0
        assert file_reader.retry_delay == pytest.approx(0.0)
        assert file_reader.backoff_factor == pytest.approx(0.0)


# Sync
class TestFileReaderSync:
    """
    Test synchronous FileReader functionality.

    Tests:
    -------
    - **test_file_reader_read:**
        - Test reading from files.
    - **test_file_reader_cm_read:**
        - Test reading from files using context manager.
    - **test_file_reader_read_generator:**
        - Test reading from files using generator.
    - **test_file_reader_cm_read_generator:**
        - Test reading from files using generator with context manager.
    """

    def test_file_reader_read(
        self, file_reader: FileReader, file_writer: FileWriter, tmp_path
    ):
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
        read_data: Dict[Path, str | Exception] = file_reader.read()

        len_paths: int = len(temp_paths)

        # Assert data is read
        assert (
            len(read_data) == len_paths
        ), f"Expected {len_paths} paths, got {len(read_data)}"
        for file_path, content in read_data.items():
            if isinstance(content, Exception):
                pytest.fail(f"Error reading file {file_path}: {content}")
            assert (
                ST_MESSAGE in content
            ), f"Expected '{ST_MESSAGE}' in content, got {content}"

        # Clean up temporary files
        file_writer.clear_all()
        file_reader.clear_all()

        # Assert that the file paths are cleared
        assert len(file_reader.file_paths) == 0
        assert len(file_writer.file_paths) == 0

    def test_file_reader_cm_read(
        self, file_reader: FileReader, file_writer: FileWriter, tmp_path
    ):
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
            read_data: Dict[Path, str | Exception] = fr.read()

        # Assert data is read
        len_paths: int = len(temp_paths)
        assert (
            len(read_data) == len_paths
        ), f"Expected {len_paths} paths, got {len(read_data)}"
        for file_path, content in read_data.items():
            if isinstance(content, Exception):
                pytest.fail(f"Error reading file {file_path}: {content}")
            assert (
                ST_MESSAGE in content
            ), f"Expected '{ST_MESSAGE}' in content, got {content}"

        # Clean up temporary files
        file_writer.clear_all()
        file_reader.clear_all()

        # Assert that the file paths are cleared
        assert len(file_reader.file_paths) == 0
        assert len(file_writer.file_paths) == 0

    # Sync Generator

    def test_file_reader_read_generator(
        self, file_reader: FileReader, file_writer: FileWriter, tmp_path
    ):
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
        read_data: Dict[Path, Generator[str, None, None] | Exception] = (
            file_reader.read_generator()
        )

        # Assert data is successful
        for data in read_data.values():
            if isinstance(data, Exception):
                pytest.fail(f"Error reading file: {data}")

        # Unpack the generator results
        len_paths: int = len(temp_paths)
        unpacked_data: Dict[Path, str | Exception] = file_reader.unpacker(read_data)

        # Assert data is read
        assert (
            len(unpacked_data) == len_paths
        ), f"Expected {len_paths} paths, got {len(unpacked_data)}"
        for file_path, content in unpacked_data.items():
            if not isinstance(file_path, Path):
                pytest.fail(f"Expected Path, got {type(file_path)}")
            if isinstance(content, Exception):
                pytest.fail(f"Error reading file {file_path}: {content}")
            assert (
                ST_MESSAGE in content
            ), f"Expected '{ST_MESSAGE}' in content, got {content}"

        # Clean up temporary files
        file_writer.clear_all()
        file_reader.clear_all()

        # Assert that the file paths are cleared
        assert len(file_reader.file_paths) == 0
        assert len(file_writer.file_paths) == 0

    def test_file_reader_cm_read_generator(
        self, file_reader: FileReader, file_writer: FileWriter, tmp_path
    ):
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
            read_data: Dict[Path, Generator[str, None, None] | Exception] = (
                fr.read_generator()
            )

        # Assert data is successful
        for data in read_data.values():
            if isinstance(data, Exception):
                pytest.fail(f"Error reading file: {data}")

        # Unpack the generator results
        unpacked_data: Dict[Path, str | Exception] = file_reader.unpacker(read_data)

        # Assert data is read
        len_paths: int = len(temp_paths)
        assert (
            len(unpacked_data) == len_paths
        ), f"Expected {len_paths} paths, got {len(unpacked_data)}"
        for file_path, content in unpacked_data.items():
            if not isinstance(file_path, Path):
                pytest.fail(f"Expected Path, got {type(file_path)}")
            if isinstance(content, Exception):
                pytest.fail(f"Error reading file {file_path}: {content}")
            assert (
                ST_MESSAGE in content
            ), f"Expected '{ST_MESSAGE}' in content, got {content}"

        # Clean up temporary files
        file_writer.clear_all()
        file_reader.clear_all()

        # Assert that the file paths are cleared
        assert len(file_reader.file_paths) == 0
        assert len(file_writer.file_paths) == 0


# Async
class TestFileReaderAsync:
    """
    Test asynchronous FileReader functionality.

    Tests:
    -------
    - **test_file_reader_async_read:**
        - Test reading from files asynchronously.
    - **test_file_reader_cm_async_read:**
        - Test reading from files asynchronously with context manager.
    - **test_file_reader_async_read_generator:**
        - Test reading from files asynchronously using generator.
    - **test_file_reader_cm_async_read_generator:**
        - Test reading from files asynchronously using generator with context manager.
    """

    @pytest.mark.asyncio
    async def test_file_reader_async_read(
        self, file_reader: FileReader, file_writer: FileWriter, tmp_path
    ):
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
        read_data: Dict[Path, str | Exception] = await file_reader.async_read()

        # Assert data is read
        len_paths: int = len(temp_paths)
        assert (
            len(read_data) == len_paths
        ), f"Expected {len_paths} paths, got {len(read_data)}"
        for file_path, content in read_data.items():
            if isinstance(content, Exception):
                pytest.fail(f"Error reading file {file_path}: {content}")
            assert (
                ST_MESSAGE in content
            ), f"Expected '{ST_MESSAGE}' in content, got {content}"

        # Clean up temporary files
        file_writer.clear_all()
        file_reader.clear_all()

        # Assert that the file paths are cleared
        assert len(file_reader.file_paths) == 0
        assert len(file_writer.file_paths) == 0

    @pytest.mark.asyncio
    async def test_file_reader_cm_async_read(
        self, file_reader: FileReader, file_writer: FileWriter, tmp_path
    ):
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
            read_data: Dict[Path, str | Exception] = await fr.async_read()

        # Assert data is read
        len_paths: int = len(temp_paths)
        assert (
            len(read_data) == len_paths
        ), f"Expected {len_paths} paths, got {len(read_data)}"
        for file_path, content in read_data.items():
            if isinstance(content, Exception):
                pytest.fail(f"Error reading file {file_path}: {content}")
            assert (
                ST_MESSAGE in content
            ), f"Expected '{ST_MESSAGE}' in content, got {content}"

        # Clean up temporary files
        file_writer.clear_all()
        file_reader.clear_all()

        # Assert that the file paths are cleared
        assert len(file_reader.file_paths) == 0
        assert len(file_writer.file_paths) == 0

    # Async Generator

    @pytest.mark.asyncio
    async def test_file_reader_async_read_generator(
        self, file_reader: FileReader, file_writer: FileWriter, tmp_path
    ):
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
        read_data: Dict[Path, Generator[str, None, None] | Exception] = (
            await file_reader.async_read_generator()
        )

        # Assert data is read
        len_paths: int = len(temp_paths)
        assert (
            len(read_data) == len_paths
        ), f"Expected {len_paths} paths, got {len(read_data)}"

        # Assert data is successful
        for data in read_data.values():
            if isinstance(data, Exception):
                pytest.fail(f"Error reading file: {data}")

        # Unpack the generator results
        unpacked_data: Dict[Path, str | Exception] = file_reader.unpacker(read_data)

        # Assert data is read
        assert (
            len(unpacked_data) == len_paths
        ), f"Expected {len_paths} paths, got {len(unpacked_data)}"
        for file_path, content in unpacked_data.items():
            if not isinstance(file_path, Path):
                pytest.fail(f"Expected Path, got {type(file_path)}")
            if isinstance(content, Exception):
                pytest.fail(f"Error reading file {file_path}: {content}")
            assert (
                ST_MESSAGE in content
            ), f"Expected '{ST_MESSAGE}' in content, got {content}"

        # Clean up temporary files
        file_writer.clear_all()
        file_reader.clear_all()

        # Assert that the file paths are cleared
        assert len(file_reader.file_paths) == 0
        assert len(file_writer.file_paths) == 0

    @pytest.mark.asyncio
    async def test_file_reader_cm_async_read_generator(
        self, file_reader: FileReader, file_writer: FileWriter, tmp_path
    ):
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
            read_data: Dict[Path, Generator[str, None, None] | Exception] = (
                await fr.async_read_generator()
            )

        # Assert data is read
        len_paths: int = len(temp_paths)
        assert (
            len(read_data) == len_paths
        ), f"Expected {len_paths} paths, got {len(read_data)}"

        # Assert data is successful
        for data in read_data.values():
            if isinstance(data, Exception):
                pytest.fail(f"Error reading file: {data}")

        # Unpack the generator results
        unpacked_data: Dict[Path, str | Exception] = file_reader.unpacker(read_data)

        # Assert data is read
        assert (
            len(unpacked_data) == len_paths
        ), f"Expected {len_paths} paths, got {len(unpacked_data)}"
        for file_path, content in unpacked_data.items():
            if not isinstance(file_path, Path):
                pytest.fail(f"Expected Path, got {type(file_path)}")
            if isinstance(content, Exception):
                pytest.fail(f"Error reading file {file_path}: {content}")
            assert (
                ST_MESSAGE in content
            ), f"Expected '{ST_MESSAGE}' in content, got {content}"

        # Clean up temporary files
        file_writer.clear_all()
        file_reader.clear_all()

        # Assert that the file paths are cleared
        assert len(file_reader.file_paths) == 0
        assert len(file_writer.file_paths) == 0


# ----------------------------------------------------------------------------------------------
# Functionality Tests
# ----------------------------------------------------------------------------------------------


class TestFileReaderFunctionality:
    """
    Test FileReader functionality.

    Tests:
    -------
    - **test_thread_safety:**
        - Test thread safety with concurrent writes and reads.
    - **test_memory_usage:**
        - Test memory usage during file operations.
    - **test_file_reader_unpacker:**
        - Test unpacking results from read_generator.
    """

    def test_thread_safety(
        self, file_reader: FileReader, file_writer: FileWriter, tmp_path
    ):
        """Test thread safety with concurrent writes and reads."""
        # Create temporary files
        temp_file = [tmp_path / "thread_test_1.log", tmp_path / "thread_test_2.log"]

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
                if thread.is_alive():
                    thread.join()

            # Wait for all threads to complete and then force the file handler to flush the buffer
            for thread in threads:
                thread.join()

            file_writer.buffer_force_flush()

            # Verify all messages were written
            for file_path in file_writer:
                assert file_path.exists()
                with open(file_path, "r") as f:
                    write_result = f.read()
                    for _ in range(100):
                        assert ST_MESSAGE in write_result

            # Read the data back
            def read_messages(pack: Dict[Path, str | Exception], lock: threading.Lock):
                with file_reader as fr:
                    read_data: Dict[Path, str | Exception] = fr.read()
                    for file_path, content in read_data.items():
                        with lock:
                            pack[file_path] = content

            # Create a shared list to store results from threads
            pack: Dict[Path, str | Exception] = {}
            lock = threading.Lock()  # Thread-safe lock

            # Create multiple threads for reading - 5
            read_threads = [
                threading.Thread(target=read_messages, args=(pack, lock))
                for _ in range(5)
            ]

            # Start all read threads
            for thread in read_threads:
                thread.start()

            # Wait for all read threads to complete
            for thread in read_threads:
                if thread.is_alive():
                    thread.join()

            # Assert results
            for file_path, content in pack.items():
                if isinstance(content, Exception):
                    pytest.fail(f"Error reading file {file_path}: {content}")
                assert (
                    ST_MESSAGE in content
                ), f"Expected '{ST_MESSAGE}' in content, got {content}"

        finally:
            # Ensure that the file paths are cleared in case of any exceptions
            file_reader.clear_all()
            file_writer.clear_all()
            assert (
                len(file_reader.file_paths) == 0
            ), "File paths should be cleared after operations"
            assert (
                len(file_writer.file_paths) == 0
            ), "File paths should be cleared after operations"

            for path in temp_file:
                if path.exists():
                    path.unlink()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_memory_usage_async(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
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
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"

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
        read_data: Dict[Path, str | Exception] = await file_reader.async_read()

        after_memory = process.memory_info().rss  # Resident Set Size after logging
        after_memory_mb = round(after_memory / (1024 * 1024), 2)
        after_memory_kb = round(after_memory / 1024, 2)
        print(
            f"After memory usage: {after_memory} bytes ({after_memory_kb} KB, {after_memory_mb} MB)"
        )

        leak_memory_kb = round((after_memory - initial_memory) / 1024, 2)
        leak_memory_mb = round((after_memory - initial_memory) / (1024 * 1024), 2)

        print(
            f"Memory difference for {batch_size} messages: {leak_memory_kb} KB ({leak_memory_mb} MB)"
        )

        # Assert Reading is done
        assert (
            len(read_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(read_data)}"
        for file_path, content in read_data.items():
            if isinstance(content, Exception):
                pytest.fail(f"Error reading file {file_path}: {content}")
            assert (
                len(content) > 0
            ), f"File {file_path} should not be empty after reading"
            assert (
                ST_MESSAGE in content
            ), f"Messages should be present in the file {file_path}"

        # Cleanup
        file_reader.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"

        del file_reader
        del read_data

        gc.collect()  # Force garbage collection
        print("Memory usage test completed for batch size:", batch_size)


# ----------------------------------------------------------------------------------------------
# ClassMethods Tests
# ----------------------------------------------------------------------------------------------


class TestFileReaderClassMethods:
    """
    Test class methods of FileReader.

    Tests:
    -------
    - **test_from_dict:**
        - Test creating FileReader from a dictionary.
    - **test_from_json:**
        - Test creating FileReader from a JSON string.
    - **test_from_yaml:**
        - Test creating FileReader from a YAML string.
    """

    def test_from_dict(self, tmp_path):
        tmp_list: List[Path] = temporary_file_handler(2, tmp_path)

        config_dict: Dict[str, Any] = {
            "file_paths": tmp_list,
            "retry_limit": 10,
            "retry_delay": 0.5,
            "backoff_factor": 0.5,
        }

        my_file_reader: FileReader = FileReader.from_dict(config_dict)

        assert len(my_file_reader) == 2
        assert my_file_reader.file_paths == tmp_list
        assert my_file_reader.retry_limit == 10
        assert my_file_reader.retry_delay == pytest.approx(0.5)
        assert my_file_reader.backoff_factor == pytest.approx(0.5)

    def test_from_json(self, tmp_path):
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

    def test_from_yaml(self, tmp_path):
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


class TestFileReaderConfig:
    """
    Test configuration methods of FileReader.

    Tests:
    -------
    - **test_file_reader_config_from_dict:**
        - Test configuration of FileReader using a dictionary.
    - **test_file_reader_config_from_json:**
        - Test configuration of FileReader using a JSON file.
    - **test_file_reader_config_from_yaml:**
        - Test configuration of FileReader using a YAML file.
    """

    def test_file_reader_config_from_dict(self, file_reader: FileReader, tmp_path):
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

    def test_file_reader_config_from_json(self, file_reader: FileReader, tmp_path):
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

    def test_file_reader_config_from_yaml(self, file_reader: FileReader, tmp_path):
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


class TestFileReaderPoolMethods:
    """
    Test thread pool methods of FileReader.

    Tests:
    -------
    - **test_file_reader_is_pool_active:**
        - Test if the thread pool is active.
    - **test_file_reader_is_pool_shutdown:**
        - Test if the thread pool is shutdown.
    - **test_file_reader_force_shutdown:**
        - Test force shutdown of the thread pool.
    - **test_file_reader_resume_pool:**
        - Test resuming the thread pool.
    """

    def test_file_reader_is_pool_active(self, file_reader: FileReader):
        """Test if the thread pool is active."""
        assert file_reader.is_pool_active(), "Thread pool should be active"

    def test_file_reader_is_pool_shutdown(self, file_reader: FileReader):
        """Test if the thread pool is shutdown."""
        assert not file_reader.is_pool_shutdown(), "Thread pool should not be shutdown"

    def test_file_reader_force_shutdown(self, file_reader: FileReader):
        """Test force shutdown of the thread pool."""
        assert file_reader.is_pool_active()
        file_reader.force_shutdown()
        assert file_reader.is_pool_shutdown()

    def test_file_reader_resume_pool(self, file_reader: FileReader):
        """Test resuming the thread pool."""
        file_reader.force_shutdown()
        assert file_reader.is_pool_shutdown()
        file_reader.resume_pool()
        assert file_reader.is_pool_active()
