# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
import asyncio

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
    handler.clear_all()


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

# Asynchronous FileHandler Tests


@pytest.mark.benchmark(group="FileHandler_ASYNC")
@pytest.mark.asyncio
@pytest.mark.parametrize("num_files", BATCH_TEST_CASES)
async def test_benchmark_async_file_handler_write(benchmark, num_files, tmp_path):
    """Benchmark test for writing to multiple files."""
    file_paths: List[Path] = temporary_file_handler(num_files, tmp_path)

    log_message = "This is a test log message."

    handler = FileHandler(
        file_paths=list(file_paths), retry_limit=0, retry_delay=0.0, backoff_factor=0.0
    )

    async def write_logs_async():
        # Write a log message to each file
        await handler.async_log(log_message)
        # Force flush the buffer to ensure logs are written
        handler.buffer_force_flush()

    await benchmark(write_logs_async)

    # Cleanup
    handler.clear_all()
    assert len(handler.file_paths) == 0


@pytest.mark.benchmark(group="FileHandler_ASYNC")
@pytest.mark.asyncio
@pytest.mark.parametrize("num_files", BATCH_TEST_CASES)
async def test_benchmark_async_file_handler_write_no_flush(
    benchmark, num_files, tmp_path
):
    """Benchmark test for writing to multiple files."""
    file_paths: List[Path] = temporary_file_handler(num_files, tmp_path)

    log_message = "This is a test log message."

    handler = FileHandler(
        file_paths=list(file_paths), retry_limit=0, retry_delay=0.0, backoff_factor=0.0
    )

    # Disable auto-flush for this test
    handler.use_write_flush = False

    async def write_logs_async():
        # Write a log message to each file
        await handler.async_log(log_message)
        # Force flush the buffer to ensure logs are written
        handler.buffer_force_flush()

    await benchmark(write_logs_async)

    # Cleanup
    handler.clear_all()
    assert len(handler.file_paths) == 0


@pytest.mark.benchmark(group="FileHandler_ASYNC")
@pytest.mark.asyncio
@pytest.mark.parametrize("num_files", BATCH_TEST_CASES)
async def test_benchmark_async_cm_file_handler_write(benchmark, num_files, tmp_path):
    """Benchmark test for writing to multiple files."""
    file_paths: List[Path] = temporary_file_handler(num_files, tmp_path)

    log_message = "This is a test log message."

    handler = FileHandler(
        file_paths=list(file_paths), retry_limit=0, retry_delay=0.0, backoff_factor=0.0
    )

    async def write_logs_async():
        async with handler as h:
            # Write a log message to each file
            await h.async_log(log_message)
            # Force flush the buffer to ensure logs are written
            h.buffer_force_flush()

    await benchmark(write_logs_async)

    # Cleanup
    handler.clear_all()
    assert len(handler.file_paths) == 0


@pytest.mark.benchmark(group="FileHandler_ASYNC")
@pytest.mark.asyncio
@pytest.mark.parametrize("num_files", BATCH_TEST_CASES)
async def test_benchmark_async_cm_file_handler_write_no_flush(
    benchmark, num_files, tmp_path
):
    """Benchmark test for writing to multiple files."""
    file_paths: List[Path] = temporary_file_handler(num_files, tmp_path)

    log_message = "This is a test log message."

    handler = FileHandler(
        file_paths=list(file_paths), retry_limit=0, retry_delay=0.0, backoff_factor=0.0
    )

    # Disable auto-flush for this test
    handler.use_write_flush = False

    async def write_logs_async():
        async with handler as h:
            # Write a log message to each file
            await h.async_log(log_message)
            # Force flush the buffer to ensure logs are written
            h.buffer_force_flush()

    await benchmark(write_logs_async)

    # Cleanup
    handler.clear_all()
    assert len(handler.file_paths) == 0
