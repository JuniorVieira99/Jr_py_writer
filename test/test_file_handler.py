# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
from pathlib import Path
from typing import Generator, List, Final
import time
import threading
import json
import yaml
import os

# Third-party imports
import pytest
import psutil

# Local imports
from jr_py_writer.handler_file import FileHandler
from jr_py_writer.utils.module_enums import LogWriteMode
# Exceptions
from jr_py_writer.exceptions.exceptions_file_handler import(
    FileHandlerConstructionError,
    FileHandlerSettingsError,
    FileHandlerWriteError,
    FileHandlerAsyncWriteError,
)


# ----------------------------------------------------------------------------------------------
# Fixture
# ----------------------------------------------------------------------------------------------

@pytest.fixture
def fixture_file_handler(tmp_path) -> Generator[FileHandler, None, None]:
    """Fixture for FileHandler with temporary files."""
    temp_files = [tmp_path / "test_1.log", tmp_path / "test_2.log"]
    handler = FileHandler(
        file_paths=temp_files,  # Use temp files
        retry_limit=0,
        retry_delay=0.0,
        backoff_factor=0.0
    )
    
    yield handler
    
    # Cleanup
    handler.clear_sync_pool()
    handler.force_shutdown(wait=True)


def temporary_file_handler(num: int , tmp_path) -> List[Path]:
    """Fixture for creating temporary files for testing."""
    file_paths = [tmp_path / f"test_{i}.log" for i in range(1, num + 1)]
    for file_path in file_paths:
        file_path.touch()
    return file_paths


# ----------------------------------------------------------------------------------------------
# Tests Cases
# ----------------------------------------------------------------------------------------------

EDGE_INT = [
    0.0, "1.0", [], {}, tuple() , set(), None, b"byte",
]

EDGE_FLOAT = [
    -1.0, "1.0", [], {}, tuple(), set(), None, b"byte"
]

EDGE_PATHS = [
    tuple(), [], {}, set(), None, b"byte", 55, 1.0, -1.0, "1.0",
]

EDGE_LOG = [
    55, 1.0, -1.0, [], {}, tuple(), set(), None
]

BATCH_TEST_CASES: Final[List[int]] = [100, 300, 500, 1000, 2000]

# ----------------------------------------------------------------------------------------------
# EDGE Tests
# ----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("edge_value", EDGE_PATHS)
def test_file_handler_edge_constructor_paths(edge_value):
    """Test edge cases for FileHandler constructor."""
    # Test with invalid file_paths
    with pytest.raises(FileHandlerConstructionError):
        FileHandler(
            file_paths=edge_value,
            retry_limit=0,
            retry_delay=0.0,
            backoff_factor=0.0
        )


@pytest.mark.parametrize("edge_value", EDGE_INT)
def test_file_handler_edge_constructor_int(tmp_path, edge_value):
    """Test edge cases for FileHandler constructor."""
    temp_files = [tmp_path / "test_1.log", tmp_path / "test_2.log"]
    # Test with invalid retry_limit
    with pytest.raises(FileHandlerConstructionError):
        FileHandler(
            temp_files,
            retry_limit=edge_value
        )

    # Test with invalid max_file_size
    with pytest.raises(FileHandlerConstructionError):
        FileHandler(
            temp_files,
            max_file_size=edge_value
        )

    # Test with invalid max_rotation
    with pytest.raises(FileHandlerConstructionError):
        FileHandler(
            temp_files,
            max_rotation=edge_value
    )


@pytest.mark.parametrize("edge_value", EDGE_FLOAT)
def test_file_handler_edge_constructor_float(tmp_path, edge_value):
    """Test edge cases for FileHandler constructor."""
    temp_files = [tmp_path / "test_1.log", tmp_path / "test_2.log"]
    
    # Test with invalid retry_delay
    with pytest.raises(FileHandlerConstructionError):
        FileHandler(
            temp_files,
            retry_delay=edge_value
        )

    # Test with invalid backoff_factor
    with pytest.raises(FileHandlerConstructionError):
        FileHandler(
            temp_files,
            backoff_factor=edge_value
        )


def test_file_handler_edge_setters(fixture_file_handler: FileHandler):
    """Test edge cases for FileHandler."""

    # Test with empty file_paths
    with pytest.raises(FileHandlerSettingsError):
        fixture_file_handler.file_paths = []

    # Test with invalid retry_limit
    with pytest.raises(FileHandlerSettingsError):
        fixture_file_handler.retry_limit = -1

    # Test with invalid retry_delay
    with pytest.raises(FileHandlerSettingsError):
        fixture_file_handler.retry_delay = -1.0

    # Test with invalid backoff_factor
    with pytest.raises(FileHandlerSettingsError):
        fixture_file_handler.backoff_factor = -1.0

    # Test with invalid max_file_size
    with pytest.raises(FileHandlerSettingsError):
        fixture_file_handler.max_file_size = -1

    # Test with invalid max_rotation
    with pytest.raises(FileHandlerSettingsError):
        fixture_file_handler.max_rotation = -1


@pytest.mark.parametrize("edge_value", EDGE_LOG)
def test_file_handler_edge_log(fixture_file_handler: FileHandler, edge_value):
    """Test edge cases for FileHandler log method."""

    # Test with invalid log message type
    with pytest.raises(FileHandlerWriteError):
        fixture_file_handler.log(edge_value)


@pytest.mark.asyncio
@pytest.mark.parametrize("edge_value", EDGE_LOG)
async def test_file_handler_edge_async_log(fixture_file_handler: FileHandler, edge_value):
    """Test edge cases for FileHandler async log method."""
    # Test with invalid log message type
    with pytest.raises(FileHandlerAsyncWriteError):
        await fixture_file_handler.async_log(edge_value)


# ----------------------------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------------------------

def test_file_handler_init(fixture_file_handler: FileHandler):
    """Test the initialization of FileHandler."""
    assert len(fixture_file_handler.file_paths) == 2
    assert fixture_file_handler.write_mode == "a"
    assert fixture_file_handler.retry_limit == 0
    assert fixture_file_handler.retry_delay == pytest.approx(0.0)
    assert fixture_file_handler.backoff_factor == pytest.approx(0.0)
    assert fixture_file_handler.max_file_size == 10 * 1024 * 1024  # 10 MB
    assert fixture_file_handler.max_rotation == 5


def test_file_handler_setters(fixture_file_handler: FileHandler):
    """Test the setters of FileHandler."""
    # Test setting file_paths
    new_paths = [Path("new_test_1.log"), Path("new_test_2.log")]
    fixture_file_handler.file_paths = new_paths

    assert fixture_file_handler.file_paths == new_paths

    # Test setting write_mode
    fixture_file_handler.write_mode = LogWriteMode.WRITE_READ
    assert fixture_file_handler.write_mode == LogWriteMode.WRITE_READ

    # Test setting retry_limit
    fixture_file_handler.retry_limit = 5
    assert fixture_file_handler.retry_limit == 5

    # Test setting retry_delay
    fixture_file_handler.retry_delay = 1.0
    assert fixture_file_handler.retry_delay == pytest.approx(1.0)

    # Test setting backoff_factor
    fixture_file_handler.backoff_factor = 0.5
    assert fixture_file_handler.backoff_factor == pytest.approx(0.5)


def test_file_handler_log(fixture_file_handler: FileHandler, tmp_path):
    """Test the log method of FileHandler."""
    log_message = "Test log message for FileHandler"

    # Set up temporary files for logging
    temp_file_1 = tmp_path / "test_1.log"
    temp_file_2 = tmp_path / "test_2.log"
    fixture_file_handler.file_paths = [temp_file_1, temp_file_2]

    # Call the log method
    fixture_file_handler.log(
        log_message
    )

    # Force the file handler to flush the buffer
    fixture_file_handler.buffer_force_flush()

    # Check if the log message is written to the file
    for file_path in fixture_file_handler.file_paths:
        with open(file_path, 'r') as f:
            content = f.read()
            assert log_message in content
    
    fixture_file_handler.clear_sync_pool()
    

def test_file_handler_context_manager(fixture_file_handler: FileHandler, tmp_path):
    """Test the context manager functionality of FileHandler."""
    log_message = "Context manager log message for FileHandler"
    temp_file = tmp_path / "context_test.log"
    
    with fixture_file_handler as handler:
        handler.file_paths = [temp_file]
        handler.log(log_message)
        
    # Check if the log message is written to the file
    with open(temp_file, 'r') as f:
        content = f.read()
        assert log_message in content

    # After exiting the context, file_paths should be cleared
    assert len(handler.file_paths) == 0


@pytest.mark.asyncio
async def test_file_handler_log_async(fixture_file_handler: FileHandler, tmp_path):
    """Test the async log method of FileHandler."""
    log_message = "Async log message for FileHandler"

    # Set up temporary files for logging
    temp_file_1 = tmp_path / "test_1.log"
    temp_file_2 = tmp_path / "test_2.log"
    fixture_file_handler.file_paths = [temp_file_1, temp_file_2]

    # Call the async log method
    await fixture_file_handler.async_log(
        log_message
    )

    # Force the file handler to flush the buffer
    fixture_file_handler.buffer_force_flush()
    
    # Check if the log message is written to the file
    for file_path in fixture_file_handler.file_paths:
        with open(file_path, 'r') as f:
            content = f.read()
            assert log_message in content

    fixture_file_handler.clear_sync_pool()


@pytest.mark.asyncio
async def test_file_handler_async_context_manager(fixture_file_handler: FileHandler, tmp_path):
    """Test the async context manager functionality of FileHandler."""
    log_message = "Async context manager log message for FileHandler"
    temp_file = tmp_path / "async_context_test.log"
    
    async with fixture_file_handler as handler:
        handler.file_paths = [temp_file]
        await handler.async_log(log_message)
        
    # Check if the log message is written to the file
    with open(temp_file, 'r') as f:
        content = f.read()
        assert log_message in content

    # After exiting the context, file_paths should be cleared
    assert len(handler.file_paths) == 0


# ----------------------------------------------------------------------------------------------
# Performance Tests
# ----------------------------------------------------------------------------------------------

# Sync Performance Tests

@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
def test_file_handler_log_batches(fixture_file_handler: FileHandler, tmp_path, batch_size: int):
    """
    Test the log_batches method of FileHandler.

    Performance: 
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u

    ### Some Results:
    - Time taken to log 100 messages: 0.06 seconds.
    - Time taken to log 300 messages: 0.18 seconds.
    - Time taken to log 500 messages: 0.35 seconds.
    - Time taken to log 1000 messages: 0.62 seconds.
    - Time taken to log 2000 messages: 1.08 seconds.
    """
    log_message: str = "Batch log message for FileHandler"

    # Make paths
    temp_files: List[Path] = temporary_file_handler(batch_size, tmp_path)
    fixture_file_handler.file_paths = temp_files

    # Set the write mode to append
    fixture_file_handler.write_mode = LogWriteMode.APPEND

    start_time: float = time.time()
    # Call the log_batches method
    fixture_file_handler.log(
        log_message
    )
    end_time: float = time.time()
    elapsed_time: float = end_time - start_time

    # Force the file handler to flush the buffer
    fixture_file_handler.buffer_force_flush()

    print(f"Time taken to log {batch_size} messages: {elapsed_time:.3f} seconds")

    # Check if the log message is written to the files
    for file_path in fixture_file_handler.file_paths:
        with open(file_path, 'r') as f:
            content = f.read()
            assert log_message in content

    fixture_file_handler.clear_sync_pool()


@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
def test_file_handler_cm_log_batches(fixture_file_handler: FileHandler, tmp_path, batch_size: int):
    """
    Test the context manager log_batches method of FileHandler.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u

    ### Some Results:
    - Time taken to log 100 messages: 0.09 seconds.
    - Time taken to log 300 messages: 0.22 seconds.
    - Time taken to log 500 messages: 0.39 seconds.
    - Time taken to log 1000 messages: 0.76 seconds.
    - Time taken to log 2000 messages: 1.39 seconds.
    """
    log_message: str = "Context Manager Batch log message for FileHandler"

    # Make paths
    temp_files: List[Path] = temporary_file_handler(batch_size, tmp_path)
    fixture_file_handler.file_paths = temp_files

    # Set the write mode to append
    fixture_file_handler.write_mode = LogWriteMode.APPEND

    start_time: float = time.time()

    # Use context manager to log batches
    with fixture_file_handler as handler:
        handler.log(
            log_message
        )

    end_time: float = time.time()
    elapsed_time: float = end_time - start_time
    print(f"Time taken to log {batch_size} messages in context manager: {elapsed_time:.2f} seconds")

    # Check if the log message is written to the files
    for file_path in fixture_file_handler.file_paths:
        with open(file_path, 'r') as f:
            content = f.read()
            assert log_message in content

    assert len(fixture_file_handler.file_paths) == 0, "File paths should be cleared after context manager exit"


# Sync With no Flush Performance Tests

@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
def test_file_handler_log_batches_no_flush(fixture_file_handler: FileHandler, tmp_path, batch_size: int):
    """
    Test the log_batches method of FileHandler - WITHOUT auto-flush.

    Performance: 
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u

    ### Some Results:
    - Time taken to log 100 messages: 0.03 seconds.
    - Time taken to log 300 messages: 0.06 seconds.
    - Time taken to log 500 messages: 0.13 seconds.
    - Time taken to log 1000 messages: 0.19 seconds.
    - Time taken to log 2000 messages: 0.37 seconds.
    """
    log_message: str = "Batch log message for FileHandler"

    # Make paths
    temp_files: List[Path] = temporary_file_handler(batch_size, tmp_path)
    fixture_file_handler.file_paths = temp_files

    # Set flush to false
    fixture_file_handler.use_write_flush = False

    # Set the write mode to append
    fixture_file_handler.write_mode = LogWriteMode.APPEND

    # Call the log_batches method
    fixture_file_handler.log(
        log_message
    )

    start_time: float = time.time()

    # Force the file handler to flush the buffer
    fixture_file_handler.buffer_force_flush()

    end_time: float = time.time()
    elapsed_time: float = end_time - start_time

    print(f"Time taken to log {batch_size} messages: {elapsed_time:.3f} seconds")

    # Check if the log message is written to the files
    for file_path in fixture_file_handler.file_paths:
        with open(file_path, 'r') as f:
            content = f.read()
            assert log_message in content

    fixture_file_handler.clear_sync_pool()


@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
def test_file_handler_cm_log_batches_no_flush(fixture_file_handler: FileHandler, tmp_path, batch_size: int):
    """
    Test the context manager log_batches method of FileHandler - WITHOUT auto-flush.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u

    ### Some Results:
    - Time taken to log 100 messages: 0.08 seconds.
    - Time taken to log 300 messages: 0.27 seconds.
    - Time taken to log 500 messages: 0.51 seconds.
    - Time taken to log 1000 messages: 0.98 seconds.
    - Time taken to log 2000 messages: 1.62 seconds.
    """
    log_message: str = "Context Manager Batch log message for FileHandler"

    # Make paths
    temp_files: List[Path] = temporary_file_handler(batch_size, tmp_path)
    fixture_file_handler.file_paths = temp_files

    # Set flush to false
    fixture_file_handler.use_write_flush = False

    # Set the write mode to append
    fixture_file_handler.write_mode = LogWriteMode.APPEND

    start_time: float = time.time()

    # Use context manager to log batches
    with fixture_file_handler as handler:
        handler.log(
            log_message
        )

    end_time: float = time.time()
    elapsed_time: float = end_time - start_time
    print(f"Time taken to log {batch_size} messages in context manager: {elapsed_time:.3f} seconds")

    # Check if the log message is written to the files
    for file_path in fixture_file_handler.file_paths:
        with open(file_path, 'r') as f:
            content = f.read()
            assert log_message in content

    assert len(fixture_file_handler.file_paths) == 0, "File paths should be cleared after context manager exit"


# Async Performance Tests

@pytest.mark.asyncio
@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
async def test_file_handler_log_async_batches(fixture_file_handler: FileHandler, tmp_path, batch_size):
    """
    Test the async log_batches method of FileHandler.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u

    ### Some Results:
    - Time taken to log 100 messages: 0.03 seconds.
    - Time taken to log 300 messages: 0.08 seconds.
    - Time taken to log 500 messages: 0.11 seconds.
    - Time taken to log 1000 messages: 0.20 seconds.
    - Time taken to log 2000 messages: 0.39 seconds.
    """
    log_message: str = "Async Batch log message for FileHandler"

    # Close the sync pool before starting async operations
    fixture_file_handler.clear_sync_pool()

    # Make paths
    temp_files: List[Path] = temporary_file_handler(batch_size, tmp_path)
    fixture_file_handler.file_paths = temp_files

    # Set the write mode to append
    fixture_file_handler.write_mode = LogWriteMode.APPEND


    # Call the async log_batches method
    await fixture_file_handler.async_log(
        log_message
    )

    print(f"buffer size: {fixture_file_handler.get_buffer_size}")

    start_time: float = time.time()

    # Force the file handler to flush the buffer
    fixture_file_handler.buffer_force_flush()

    end_time: float = time.time()
    elapsed_time: float = end_time - start_time
    print(f"Async time taken to log {batch_size} messages: {elapsed_time:.2f} seconds")

    # Check if the log message is written to the files
    for file_path in fixture_file_handler.file_paths:
        with open(file_path, 'r') as f:
            content = f.read()
            assert log_message in content
    
    # After flushing, the buffer should be empty
    fixture_file_handler.clear_all()
    assert fixture_file_handler.get_buffer_size == 0, "Buffer should be empty after flush"

    print(f"Async log completed for {batch_size}")


@pytest.mark.asyncio
@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
async def test_file_handler_cm_log_async_batches(fixture_file_handler: FileHandler, tmp_path, batch_size):
    """
    Test the async context manager log_batches method of FileHandler.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u

    ### Some Results:
    - Time taken to log 100 messages: 0.11 seconds.
    - Time taken to log 300 messages: 0.28 seconds.
    - Time taken to log 500 messages: 0.48 seconds.
    - Time taken to log 1000 messages: 1.12 seconds.
    - Time taken to log 2000 messages: 1.66 seconds.
    """
    log_message: str = "Async Context Manager Batch log message for FileHandler"

    # Close the sync pool before starting async operations
    fixture_file_handler.clear_sync_pool()

    # Make paths
    temp_files: List[Path] = temporary_file_handler(batch_size, tmp_path)
    fixture_file_handler.file_paths = temp_files

    # Set the write mode to append
    fixture_file_handler.write_mode = LogWriteMode.APPEND

    start_time: float = time.time()

    # Use async context manager to log batches
    async with fixture_file_handler as handler:
        await handler.async_log(
            log_message
        )

    end_time: float = time.time()
    elapsed_time: float = end_time - start_time
    print(f"Async time taken to log {batch_size} messages in context manager: {elapsed_time:.2f} seconds")

    # Check if the log message is written to the files
    for file_path in fixture_file_handler.file_paths:
        with open(file_path, 'r') as f:
            content = f.read()
            assert log_message in content

    # After exiting the context, file_paths should be cleared
    fixture_file_handler.clear_all()
    assert len(fixture_file_handler.file_paths) == 0, "File paths should be cleared after context manager exit"


# Async With no Flush Performance Tests

@pytest.mark.asyncio
@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
async def test_file_handler_log_async_batches_no_flush(fixture_file_handler: FileHandler, tmp_path, batch_size):
    """
    Test the async log_batches method of FileHandler - WITHOUT auto-flush.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u

    ### Some Results:
    - Time taken to log 100 messages: 0.02 seconds.
    - Time taken to log 300 messages: 0.06 seconds.
    - Time taken to log 500 messages: 0.11 seconds.
    - Time taken to log 1000 messages: 0.24 seconds.
    - Time taken to log 2000 messages: 0.40 seconds.
    """
    log_message: str = "Async Batch log message for FileHandler"

    # Close the sync pool before starting async operations
    fixture_file_handler.clear_sync_pool()

    # Make paths
    temp_files: List[Path] = temporary_file_handler(batch_size, tmp_path)
    fixture_file_handler.file_paths = temp_files

    # Set flush to false
    fixture_file_handler.use_write_flush = False

    # Set the write mode to append
    fixture_file_handler.write_mode = LogWriteMode.APPEND

    # Call the async log_batches method
    await fixture_file_handler.async_log(
        log_message
    )

    start_time: float = time.time()

    # Force the file handler to flush the buffer
    fixture_file_handler.buffer_force_flush()

    end_time: float = time.time()
    elapsed_time: float = end_time - start_time
    print(f"Async time taken to log {batch_size} messages: {elapsed_time:.2f} seconds")

    # Check if the log message is written to the files
    for file_path in fixture_file_handler.file_paths:
        with open(file_path, 'r') as f:
            content = f.read()
            assert log_message in content
    
    fixture_file_handler.clear_all()
    assert fixture_file_handler.get_buffer_size == 0, "Buffer should be empty after flush"
    assert len(fixture_file_handler.file_paths) == 0, "File paths should be cleared after async log"

    print(f"Async log completed for {batch_size}")


@pytest.mark.asyncio
@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
async def test_file_handler_cm_log_async_batches_no_flush(fixture_file_handler: FileHandler, tmp_path, batch_size):
    """
    Test the async context manager log_batches method of FileHandler - WITHOUT auto-flush.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u

    ### Some Results:
    - Time taken to log 100 messages: 0.11 seconds.
    - Time taken to log 300 messages: 0.33 seconds.
    - Time taken to log 500 messages: 0.46 seconds.
    - Time taken to log 1000 messages: 0.97 seconds.
    - Time taken to log 2000 messages: 1.45 seconds.
    """
    log_message: str = "Async Context Manager Batch log message for FileHandler"

    # Close the sync pool before starting async operations
    fixture_file_handler.clear_sync_pool()

    # Make paths
    temp_files: List[Path] = temporary_file_handler(batch_size, tmp_path)
    fixture_file_handler.file_paths = temp_files

    # Set flush to false
    fixture_file_handler.use_write_flush = False

    # Set the write mode to append
    fixture_file_handler.write_mode = LogWriteMode.APPEND

    start_time: float = time.time()

    # Use async context manager to log batches
    async with fixture_file_handler as handler:
        await handler.async_log(
            log_message
        )

    end_time: float = time.time()
    elapsed_time: float = end_time - start_time
    print(f"Async time taken to log {batch_size} messages in context manager: {elapsed_time:.2f} seconds")

    # Check if the log message is written to the files
    for file_path in fixture_file_handler.file_paths:
        with open(file_path, 'r') as f:
            content = f.read()
            assert log_message in content

    assert len(fixture_file_handler.file_paths) == 0, "File paths should be cleared after context manager exit"
    assert fixture_file_handler.get_buffer_size == 0, "Buffer should be empty after async log"

# ----------------------------------------------------------------------------------------------
# Functionality Tests
# ----------------------------------------------------------------------------------------------

def test_file_rotation(fixture_file_handler, tmp_path):
    """Test file rotation when max size is exceeded."""

    # Set Logger
    fixture_file_handler.logger.setLevel("DEBUG")

    # Create a temporary log file
    log_file = tmp_path / "small.log"
    fixture_file_handler.file_paths = [log_file]
    fixture_file_handler.max_file_size = 5  # Very small for testing
    fixture_file_handler.max_rotation = 3 # Limit to 2 rotations
    
    # Write enough to trigger rotation
    for i in range(700):
        fixture_file_handler.log(f"Long message {i} " * 10)
    
    # Force the file handler to flush the buffer
    fixture_file_handler.buffer_force_flush()

    try:
        # Check if rotation files exist in the tmp_path directory
        rotation_file_1 = tmp_path / "small_1.log"
        rotation_file_2 = tmp_path / "small_2.log"
        assert (rotation_file_1.exists() or rotation_file_2.exists()), "Rotation files should exist"

    finally:
        # Cleanup rotation files
        for i in range(3):
            rotation_file = tmp_path / f"small_{i}.log"
            if rotation_file.exists():
                rotation_file.unlink()

        
def test_thread_safety(fixture_file_handler, tmp_path):
    """Test thread safety with concurrent writes."""
    temp_file = tmp_path / "thread_test.log"
    fixture_file_handler.file_paths = [temp_file]
    
    def write_logs():
        for i in range(100):
            fixture_file_handler.log(f"Thread message {i}")
    
    # Create multiple threads
    threads = [threading.Thread(target=write_logs) for _ in range(5)]
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Force the file handler to flush the buffer
    fixture_file_handler.buffer_force_flush()
    
    # Verify all messages were written
    with open(temp_file, 'r') as f:
        content = f.read()
        assert content.count("Thread message") == 500


def test_memory_cleanup(tmp_path):
    """Test that file handles are properly cleaned up."""
    import gc
    import weakref
    
    temp_file = tmp_path / "cleanup_test.log"
    
    handler: FileHandler = FileHandler(
        file_paths=[temp_file]
    )
    
    # Create weak reference to track cleanup
    weak_ref = weakref.ref(handler)
    
    # Write some logs
    handler.log("test message")
    
    # Force cleanup
    handler.buffer_force_flush()
    handler.clear_sync_pool()
    handler.force_shutdown()
    
    # Delete reference to handler to allow garbage collection
    del handler
    
    # Force garbage collection
    gc.collect()
    
    # Verify cleanup
    assert weak_ref() is None, "FileHandler should be cleaned up and weak reference should be None"


@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
def test_memory_usage(tmp_path, batch_size: int):
    """
    Test memory usage during file operations.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u

    ### Some Results:
    - **100 logs:**
        -   Initial memory usage: 45273088 bytes (44212.0 KB, 43.18 MB)
        -   After memory usage: 45305856 bytes (44244.0 KB, 43.21 MB)
        -   Memory difference for 100 logs: 32.0 KB (0.03 MB)
    - **300 logs:**
        -   Initial memory usage: 45301760 bytes (44240.0 KB, 43.2 MB)
        -   After memory usage: 45322240 bytes (44260.0 KB, 43.22 MB)
        -   Memory difference for 300 logs: 20.0 KB (0.02 MB)
    - **500 logs:**
        -   Initial memory usage: 45301760 bytes (44240.0 KB, 43.2 MB)
        -   After memory usage: 45363200 bytes (44300.0 KB, 43.26 MB)
        -   Memory difference for 500 logs: 60.0 KB (0.06 MB)
    - **1000 logs:**
        -   Initial memory usage: 45342720 bytes (44280.0 KB, 43.24 MB)
        -   After memory usage: 45363200 bytes (44300.0 KB, 43.26 MB)
        -   Memory difference for 1000 logs: 20.0 KB (0.02 MB)
    - **2000 logs:**
        -   Initial memory usage: 45342720 bytes (44280.0 KB, 43.24 MB)
        -   After memory usage: 45363200 bytes (44300.0 KB, 43.26 MB)
        -   Memory difference for 2000 logs: 20.0 KB (0.02 MB)
    """
    print("Testing memory usage for batch size:", batch_size)
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss  # Resident Set Size
    initial_memory_mb = round(initial_memory / (1024 * 1024), 2)  # Convert to MB
    initial_memory_kb = round(initial_memory / 1024, 2)  # Convert to KB

    print(f"Initial memory usage: {initial_memory} bytes ({initial_memory_kb} KB, {initial_memory_mb} MB)")
    
    # Create a FileHandler instance
    temp_file = tmp_path / "memory_test.log"
    handler: FileHandler = FileHandler(
        file_paths=[temp_file]
    )
    
    # Write some logs
    for i in range(batch_size):
        handler.log(f"Memory test message {i}")
    
    # Force the file handler to flush the buffer
    handler.buffer_force_flush()
    
    after_memory = process.memory_info().rss  # Resident Set Size after logging
    after_memory_mb = round(after_memory / (1024 * 1024), 2)  # Convert to MB
    after_memory_kb = round(after_memory / 1024, 2)  # Convert to KB
    print(f"After memory usage: {after_memory} bytes ({after_memory_kb} KB, {after_memory_mb} MB)")


    leak_memory_kb = round((after_memory - initial_memory) / 1024, 2)  # Convert to KB
    leak_memory_mb = round((after_memory - initial_memory) / (1024 * 1024), 2)  # Convert to MB    
    print(f"Memory difference for {batch_size} logs: {leak_memory_kb} KB ({leak_memory_mb} MB)")

    # Cleanup
    handler.clear_all()

    assert len(handler.file_paths) == 0, "File paths should be cleared after operations"
    
    with open(temp_file, 'r') as f:
        content = f.read()
        assert len(content) > 0, "Log file should not be empty after writing logs"
        for i in range(batch_size):
            assert f"Memory test message {i}" in content, f"Log message {i} should be present in the file"


@pytest.mark.asyncio
@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
async def test_memory_usage_async(tmp_path, batch_size: int):
    """
    Test memory usage during async file operations.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u

    ### Some Results:
    - **100 logs:**
        -   Initial memory usage: 43151360 bytes (42140.0 KB, 41.15 MB)
        -   After memory usage: 43200512 bytes (42188.0 KB, 41.2 MB)
        -   Memory difference for 100 logs: 48.0 KB (0.05 MB)
    - **300 logs:**
        -   Initial memory usage: 43200512 bytes (42188.0 KB, 41.2 MB)
        -   After memory usage: 43266048 bytes (42252.0 KB, 41.26 MB)
        -   Memory difference for 300 logs: 64.0 KB (0.06 MB)
    - **500 logs:**
        -   Initial memory usage: 43249664 bytes (42236.0 KB, 41.25 MB)
        -   After memory usage: 43327488 bytes (42312.0 KB, 41.32 MB)
        -   Memory difference for 500 logs: 76.0 KB (0.07 MB)
    - **1000 logs:**
        -   Initial memory usage: 43315200 bytes (42300.0 KB, 41.31 MB)
        -   After memory usage: 43433984 bytes (42416.0 KB, 41.42 MB)
        -   Memory difference for 1000 logs: 116.0 KB (0.11 MB)
    - **2000 logs:**
        -   Initial memory usage: 43413504 bytes (42396.0 KB, 41.4 MB)
        -   After memory usage: 43692032 bytes (42668.0 KB, 41.67 MB)
        -   Memory difference for 2000 logs: 272.0 KB (0.27 MB)
    """
    print("Testing async memory usage for batch size:", batch_size)

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    initial_memory_mb = round(initial_memory / (1024 * 1024), 2)  # Convert to MB
    initial_memory_kb = round(initial_memory / 1024, 2)  # Convert to KB

    print(f"Initial memory usage: {initial_memory} bytes ({initial_memory_kb} KB, {initial_memory_mb} MB)")
    # Create a FileHandler instance
    temp_file = tmp_path / "async_memory_test.log"
    handler: FileHandler = FileHandler(
        file_paths=[temp_file]
    )
    # Write some logs asynchronously
    for i in range(batch_size):
        await handler.async_log(f"Async Memory test message {i}")
    # Force the file handler to flush the buffer
    handler.buffer_force_flush()

    after_memory = process.memory_info().rss  # Resident Set Size after logging
    after_memory_mb = round(after_memory / (1024 * 1024), 2)  # Convert to MB
    after_memory_kb = round(after_memory / 1024, 2)  # Convert to KB
    print(f"After memory usage: {after_memory} bytes ({after_memory_kb} KB, {after_memory_mb} MB)")

    leak_memory_kb = round((after_memory - initial_memory) / 1024, 2)  # Convert to KB
    leak_memory_mb = round((after_memory - initial_memory) / (1024 * 1024), 2)  # Convert to MB
    print(f"Memory difference for {batch_size} logs: {leak_memory_kb} KB ({leak_memory_mb} MB)")

    # Cleanup
    handler.clear_all()

    assert len(handler.file_paths) == 0, "File paths should be cleared after operations"

    with open(temp_file, 'r') as f:
        content = f.read()
        assert len(content) > 0, "Log file should not be empty after writing logs"
        for i in range(batch_size):
            assert f"Async Memory test message {i}" in content, f"Log message {i} should be present in the file"


# ----------------------------------------------------------------------------------------------
# Config Tests
# ----------------------------------------------------------------------------------------------

def test_file_handler_config(fixture_file_handler: FileHandler):
    """Test the configuration of FileHandler."""
    
    fixture_file_handler.config(
        file_paths=[Path("config_test.log")],
        write_mode=LogWriteMode.WRITE_READ,
        retry_limit=3,
        retry_delay=0.5,
        backoff_factor=1.0,
        max_file_size=5 * 1024 * 1024,  # 5 MB
        max_rotation=2
    )

    assert fixture_file_handler.file_paths == [Path("config_test.log")]
    assert fixture_file_handler.write_mode == LogWriteMode.WRITE_READ
    assert fixture_file_handler.retry_limit == 3
    assert fixture_file_handler.retry_delay == pytest.approx(0.5)
    assert fixture_file_handler.backoff_factor == pytest.approx(1.0)
    assert fixture_file_handler.max_file_size == 5 * 1024 * 1024  # 5 MB
    assert fixture_file_handler.max_rotation == 2


def test_file_handler_config_dict(fixture_file_handler: FileHandler):
    """Test the configuration of FileHandler with a dictionary."""
    
    config_dict = {
        "file_paths": [Path("config_dict_test.log")],
        "write_mode": LogWriteMode.WRITE_READ,
        "retry_limit": 3,
        "retry_delay": 0.5,
        "backoff_factor": 1.0,
        "max_file_size": 5 * 1024 * 1024,  # 5 MB
        "max_rotation": 2
    }
    
    fixture_file_handler.config_dict(config_dict)

    assert fixture_file_handler.file_paths == [Path("config_dict_test.log")]
    assert fixture_file_handler.write_mode == LogWriteMode.WRITE_READ
    assert fixture_file_handler.retry_limit == 3
    assert fixture_file_handler.retry_delay == pytest.approx(0.5)
    assert fixture_file_handler.backoff_factor == pytest.approx(1.0)
    assert fixture_file_handler.max_file_size == 5 * 1024 * 1024  # 5 MB
    assert fixture_file_handler.max_rotation == 2


def test_file_handler_config_json(fixture_file_handler: FileHandler):
    """Test the configuration of FileHandler with a JSON file."""
    
    config_json = {
        "file_paths": ["config_json_test.log"],
        "write_mode": LogWriteMode.APPEND,
        "retry_limit": 3,
        "retry_delay": 0.5,
        "backoff_factor": 1.0,
        "max_file_size": 5 * 1024 * 1024,  # 5 MB
        "max_rotation": 2
    }

    json_str = json.dumps(config_json)
    
    fixture_file_handler.config_json(json_str)

    assert fixture_file_handler.file_paths == [Path("config_json_test.log")]
    assert fixture_file_handler.write_mode == LogWriteMode.APPEND
    assert fixture_file_handler.retry_limit == 3
    assert fixture_file_handler.retry_delay == pytest.approx(0.5)
    assert fixture_file_handler.backoff_factor == pytest.approx(1.0)
    assert fixture_file_handler.max_file_size == 5 * 1024 * 1024  # 5 MB
    assert fixture_file_handler.max_rotation == 2
    

def test_file_handler_config_yaml(fixture_file_handler: FileHandler):
    """Test the configuration of FileHandler with a YAML file."""
    
    config_yaml = {
        "file_paths": ["config_yaml_test.log"],
        "write_mode": LogWriteMode.WRITE_READ.value,
        "retry_limit": 3,
        "retry_delay": 0.5,
        "backoff_factor": 1.0,
        "max_file_size": 5 * 1024 * 1024,  # 5 MB
        "max_rotation": 2
    }

    yaml_str = yaml.dump(config_yaml)
    
    fixture_file_handler.config_yaml(yaml_str)

    assert fixture_file_handler.file_paths == [Path("config_yaml_test.log")]
    assert fixture_file_handler.write_mode == LogWriteMode.WRITE_READ.value
    assert fixture_file_handler.retry_limit == 3
    assert fixture_file_handler.retry_delay == pytest.approx(0.5)
    assert fixture_file_handler.backoff_factor == pytest.approx(1.0)
    assert fixture_file_handler.max_file_size == 5 * 1024 * 1024  # 5 MB
    assert fixture_file_handler.max_rotation == 2


# ----------------------------------------------------------------------------------------------
# Stress Tests
# ----------------------------------------------------------------------------------------------


def test_file_handler_long_message(fixture_file_handler: FileHandler):
    """
    Test FileHandler with a very long message.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u

    ### Some Results:
    - Time taken to log a long message: 0.013 seconds.

    """
    long_message = "A" * 1000000  # 1 million characters

    # Set up a temporary file for logging
    temp_file = Path("long_message_test.log")
    fixture_file_handler.file_paths = [temp_file]

    # Log the long message
    fixture_file_handler.log(long_message)

    start_time: float = time.time()

    # Force the file handler to flush the buffer
    fixture_file_handler.buffer_force_flush()

    end_time: float = time.time()
    elapsed_time: float = end_time - start_time
    print(f"Time taken to log long message: {elapsed_time:.3f} seconds")

    # Check if the long message is written to the file
    with open(temp_file, 'r') as f:
        content = f.read()
        assert long_message in content


@pytest.mark.asyncio
async def test_file_handler_async_long_message(fixture_file_handler: FileHandler, tmp_path):
    """
    Test FileHandler with a very long message in async mode.

    Performance:
    --------------
    ### Specs:
    - RAM: 16 GB
    - Disk: 500 GB SSD
    - CPU: Intel Core i7-4510u

    ### Some Results:
    - Time taken to log a long message: 0.011 seconds.

    """

    # Create a very long message
    long_message = "A" * 1000000

    # Set up a temporary file for logging
    temp_file = tmp_path / "async_long_message_test.log"
    fixture_file_handler.file_paths = [temp_file]

    # Log the long message
    await fixture_file_handler.async_log(long_message)

    start_time: float = time.time()

    # Force the file handler to flush the buffer
    fixture_file_handler.buffer_force_flush()

    end_time: float = time.time()
    elapsed_time: float = end_time - start_time
    print(f"Async time taken to log long message: {elapsed_time:.3f} seconds")

    # Check if the long message is written to the file
    with open(temp_file, 'r') as f:
        content = f.read()
        assert long_message in content

    fixture_file_handler.clear_all()
    assert len(fixture_file_handler.file_paths) == 0, "File paths should be cleared after async log"


# ----------------------------------------------------------------------------------------------
# Magic Method Tests
# ----------------------------------------------------------------------------------------------

def test_file_handler_magic_methods(fixture_file_handler: FileHandler, tmp_path):
    """Test the magic methods of FileHandler."""
    
    # Test __str__
    str_repr = str(fixture_file_handler)
    assert "FileHandler" in str_repr, "__str__ method should return a string representation of FileHandler"

    # Test __repr__
    repr_repr = repr(fixture_file_handler)
    assert "FileHandler" in repr_repr, "__repr__ method should return a detailed representation of FileHandler"

    # Test __len__
    assert len(fixture_file_handler) == 2, "__len__ method should return the number of file paths (2 initially)"

    # Test __eq__
    temp_files = [tmp_path / "test_1.log", tmp_path / "test_2.log"]
    handler = FileHandler(
        file_paths=temp_files,  # Use temp files
        retry_limit=0,
        retry_delay=0.0,
        backoff_factor=0.0
    )
    assert fixture_file_handler == handler, "__eq__ method should compare file paths and other attributes"
    
    # Test __iter__
    for file_path in fixture_file_handler:
        assert isinstance(file_path, Path), "__iter__ method should yield Path objects"
    
    # Test __contains__
    assert fixture_file_handler.file_paths[0] in fixture_file_handler, "__contains__ method should check if a file path is in the handler"

    # Test __del__
    del fixture_file_handler  # This should not raise any exceptions
    del handler  # This should not raise any exceptions either
    
