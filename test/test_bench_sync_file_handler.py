# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
import os
from pathlib import Path
from typing import Generator, List, Final

# Third-party imports
import pytest
import psutil

# Local imports
from jr_py_writer.handler_file import FileHandler

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
        backoff_factor=0.0,
    )

    yield handler

    # Cleanup
    handler.clear_sync_pool()
    handler.force_shutdown(wait=True)


def temporary_file_handler(num: int, tmp_path) -> List[Path]:
    """Fixture for creating temporary files for testing."""
    file_paths = [tmp_path / f"test_{i}.log" for i in range(1, num + 1)]
    for file_path in file_paths:
        file_path.touch()
    return file_paths


# ----------------------------------------------------------------------------------------------
# Tests Cases
# ----------------------------------------------------------------------------------------------

BATCH_TEST_CASES: Final[List[int]] = [100, 300, 500, 1000, 2000]

LOG_MESSAGE: Final[str] = "This is a test log message."


# ----------------------------------------------------------------------------------------------
# Benchmark Performance Tests
# ----------------------------------------------------------------------------------------------

# Synchronous FileHandler Tests


@pytest.mark.benchmark(group="FileHandler_SYNC")
@pytest.mark.parametrize("num_files", BATCH_TEST_CASES)
def test_benchmark_file_handler_write(benchmark, num_files, tmp_path):
    """Benchmark test for writing to multiple files."""

    file_paths: List[Path] = temporary_file_handler(num_files, tmp_path)

    handler = FileHandler(
        file_paths=list(file_paths), retry_limit=0, retry_delay=0.0, backoff_factor=0.0
    )

    def write_logs():
        # Write a log message to each file
        handler.log(LOG_MESSAGE)
        # Force flush the buffer to ensure logs are written
        handler.buffer_force_flush()

    benchmark(write_logs)

    for file_path in file_paths:
        # Check if the file exists and has content
        assert file_path.exists(), f"File {file_path} should exist after logging."
        with open(file_path, "r") as f:
            content = f.read()
            assert (
                LOG_MESSAGE in content
            ), f"Log message should be present in {file_path}."

    # Cleanup
    handler.clear_all()
    assert len(handler.file_paths) == 0


@pytest.mark.benchmark(group="FileHandler_SYNC")
@pytest.mark.parametrize("num_files", BATCH_TEST_CASES)
def test_benchmark_file_handler_write_no_flush(benchmark, num_files, tmp_path):
    """Benchmark test for writing to multiple files."""
    file_paths: List[Path] = temporary_file_handler(num_files, tmp_path)

    log_message = "This is a test log message."

    handler = FileHandler(
        file_paths=list(file_paths), retry_limit=0, retry_delay=0.0, backoff_factor=0.0
    )

    # Disable auto-flush for this test
    handler.use_write_flush = False

    def write_logs():
        # Write a log message to each file
        handler.log(log_message)
        # Force flush the buffer to ensure logs are written
        handler.buffer_force_flush()

    benchmark(write_logs)

    for file_path in file_paths:
        # Check if the file exists and has content
        assert file_path.exists(), f"File {file_path} should exist after logging."
        with open(file_path, "r") as f:
            content = f.read()
            assert (
                LOG_MESSAGE in content
            ), f"Log message should be present in {file_path}."

    # Cleanup
    handler.clear_all()
    assert len(handler.file_paths) == 0


@pytest.mark.benchmark(group="FileHandler_SYNC")
@pytest.mark.parametrize("num_files", BATCH_TEST_CASES)
def test_benchmark_file_handler_cm_write(benchmark, num_files, tmp_path):
    """Benchmark test for context manager writing to multiple files."""
    file_paths: List[Path] = temporary_file_handler(num_files, tmp_path)

    log_message = "This is a test log message."

    handler = FileHandler(
        file_paths=list(file_paths), retry_limit=0, retry_delay=0.0, backoff_factor=0.0
    )

    def write_logs():
        with handler as h:
            # Write a log message to each file
            h.log(log_message)
            # Force flush the buffer to ensure logs are written
            h.buffer_force_flush()

    benchmark(write_logs)

    for file_path in file_paths:
        # Check if the file exists and has content
        assert file_path.exists(), f"File {file_path} should exist after logging."
        with open(file_path, "r") as f:
            content = f.read()
            assert (
                LOG_MESSAGE in content
            ), f"Log message should be present in {file_path}."

    # Cleanup
    handler.clear_all()
    assert len(handler.file_paths) == 0


@pytest.mark.benchmark(group="FileHandler_SYNC")
@pytest.mark.parametrize("num_files", BATCH_TEST_CASES)
def test_benchmark_file_handler_cm_write_no_flush(benchmark, num_files, tmp_path):
    """Benchmark test for context manager writing to multiple files."""
    file_paths: List[Path] = temporary_file_handler(num_files, tmp_path)

    log_message = "This is a test log message."

    handler = FileHandler(
        file_paths=list(file_paths), retry_limit=0, retry_delay=0.0, backoff_factor=0.0
    )

    # Disable auto-flush for this test
    handler.use_write_flush = False

    def write_logs():
        with handler as h:
            # Write a log message to each file
            h.log(log_message)
            # Force flush the buffer to ensure logs are written
            h.buffer_force_flush()

    benchmark(write_logs)

    for file_path in file_paths:
        # Check if the file exists and has content
        assert file_path.exists(), f"File {file_path} should exist after logging."
        with open(file_path, "r") as f:
            content = f.read()
            assert (
                LOG_MESSAGE in content
            ), f"Log message should be present in {file_path}."

    # Cleanup
    handler.clear_all()
    assert len(handler.file_paths) == 0


# ----------------------------------------------------------------------------------------------
# Benchmark Memory Tests
# ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
def test_memory_usage(tmp_path, batch_size: int):
    """
    Test memory usage during file operations.
    """
    print("Testing memory usage for batch size:", batch_size)

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss  # Resident Set Size
    initial_memory_mb = round(initial_memory / (1024 * 1024), 2)  # Convert to MB
    initial_memory_kb = round(initial_memory / 1024, 2)  # Convert to KB

    print(
        f"Initial memory usage: {initial_memory} bytes ({initial_memory_kb} KB, {initial_memory_mb} MB)"
    )

    # Create a FileHandler instance
    temp_file = tmp_path / "memory_test.log"
    handler: FileHandler = FileHandler(file_paths=[temp_file])

    # Write some logs
    for i in range(batch_size):
        handler.log(f"Memory test message {i}")

    # Force the file handler to flush the buffer
    handler.buffer_force_flush()

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
        f"Memory difference for {batch_size} logs: {leak_memory_kb} KB ({leak_memory_mb} MB)"
    )

    # Cleanup
    handler.clear_all()

    assert len(handler.file_paths) == 0, "File paths should be cleared after operations"

    with open(temp_file, "r") as f:
        content = f.read()
        assert len(content) > 0, "Log file should not be empty after writing logs"
        for i in range(batch_size):
            assert (
                f"Memory test message {i}" in content
            ), f"Log message {i} should be present in the file"
