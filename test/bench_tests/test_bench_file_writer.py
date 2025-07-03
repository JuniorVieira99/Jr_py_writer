# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
import time
import os

from pathlib import Path
from typing import Generator, List, Final

# Third-party imports
import pytest
import psutil

# Local imports
from jr_file_handler.classes.file_writer import FileWriter


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


def temporary_file_writer(num: int, tmp_path) -> List[Path]:
    """Fixture for creating temporary files for testing."""
    file_paths = [tmp_path / f"test_{i}.log" for i in range(1, num + 1)]
    for file_path in file_paths:
        file_path.touch()
    return file_paths


# ----------------------------------------------------------------------------------------------
# Tests Cases
# ----------------------------------------------------------------------------------------------


BATCH_TEST_CASES: Final[List[int]] = [100, 300, 500, 1000, 2000]

ST_MESSAGE: Final[str] = "This is a test message for FileWriter performance testing."


# ----------------------------------------------------------------------------------------------
# Performance Tests
# ----------------------------------------------------------------------------------------------


class TestFileWriterSyncPerformance:
    """
    Performance tests for FileWriter class in synchronous mode.
    These tests measure the time taken to log messages in batches and using context managers.

    Tests:
    -------
    - **test_message_batches:**
        - Tests the write method of FileWriter with different batch sizes.
    - **test_cm_message_batches:**
        - Tests the context manager write method of FileWriter with different batch sizes.
    - **test_message_batches_no_flush:**
        - Tests the write method of FileWriter without auto-flush with different batch sizes.
    - **test_message_cm_batches_no_flush:**
        - Tests the context manager write method of FileWriter without auto-flush with different batch sizes    
    """

    # Sync Performance Tests

    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_message_batches(
        self, file_writer: FileWriter, tmp_path, batch_size: int
    ):
        """
        Test the write method of FileWriter.

        Performance:
        --------------
        ### Specs:
        - RAM: 16 GB
        - Disk: 500 GB SSD
        - CPU: Intel Core i7-4510u

        ### Some Results:
        - Time taken to write 100 messages: 0.06 seconds.
        - Time taken to write 300 messages: 0.18 seconds.
        - Time taken to write 500 messages: 0.35 seconds.
        - Time taken to write 1000 messages: 0.434 seconds.
        - Time taken to write 2000 messages: 0.804 seconds.
        """
        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)
        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        start_time: float = time.time()

        # Write the messages
        file_writer.write(ST_MESSAGE)

        # Force the file handler to flush the buffer
        file_writer.buffer_force_flush()

        end_time: float = time.time()
        elapsed_time: float = end_time - start_time

        # Debug print
        print(f"\nTime taken to write {batch_size} messages: {elapsed_time:.4f} seconds")

        # Check if the log message is written to the files
        for file_path in file_writer.file_paths:
            with open(file_path, "r") as f:
                content = f.read()
                assert ST_MESSAGE in content

        file_writer.clear_all()

        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"


    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_cm_message_batches(
        self, file_writer: FileWriter, tmp_path, batch_size: int
    ):
        """
        Test the context manager write method of FileWriter.

        Performance:
        --------------
        ### Specs:
        - RAM: 16 GB
        - Disk: 500 GB SSD
        - CPU: Intel Core i7-4510u

        ### Some Results:
        - Time taken to write 100 messages: 0.09 seconds.
        - Time taken to write 300 messages: 0.22 seconds.
        - Time taken to write 500 messages: 0.39 seconds.
        - Time taken to write 1000 messages: 0.76 seconds.
        - Time taken to write 2000 messages: 1.39 seconds.
        """
        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)
        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        start_time: float = time.time()

        # Use context manager to log batches
        with file_writer as fw:
            fw.write(ST_MESSAGE)

        end_time: float = time.time()
        elapsed_time: float = end_time - start_time
        print(
            f"\nTime taken to write {batch_size} messages in context manager: {elapsed_time:.4f} seconds"
        )

        # Check if the log message is written to the files
        for file_path in file_writer.file_paths:
            with open(file_path, "r") as f:
                content = f.read()
                assert ST_MESSAGE in content

        # Clear the file writer
        file_writer.clear_all()

        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after context manager exit"


    # Sync With no Flush Performance Tests


    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_message_batches_no_flush(
        self, file_writer: FileWriter, tmp_path, batch_size: int
    ):
        """
        Test the write method of FileWriter - WITHOUT auto-flush.

        Performance:
        --------------
        ### Specs:
        - RAM: 16 GB
        - Disk: 500 GB SSD
        - CPU: Intel Core i7-4510u

        ### Some Results:
        - Time taken to write 100 messages: 0.03 seconds.
        - Time taken to write 300 messages: 0.06 seconds.
        - Time taken to write 500 messages: 0.13 seconds.
        - Time taken to write 1000 messages: 0.19 seconds.
        - Time taken to write 2000 messages: 0.37 seconds.
        """

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)
        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        # Set flush to false
        file_writer.use_write_flush = False

        start_time: float = time.time()

        # Call the log_batches method
        file_writer.write(ST_MESSAGE)

        # Force the file handler to flush the buffer
        file_writer.buffer_force_flush()

        end_time: float = time.time()
        elapsed_time: float = end_time - start_time

        print(f"Time taken to write {batch_size} messages: {elapsed_time:.4f} seconds")

        # Check if the log message is written to the files
        for file_path in file_writer.file_paths:
            with open(file_path, "r") as f:
                content = f.read()
                assert ST_MESSAGE in content

        # Clear the file writer
        file_writer.clear_all()

        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"


    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_message_cm_batches_no_flush(
        self, file_writer: FileWriter, tmp_path, batch_size: int
    ):
        """
        Test the context manager write method of FileWriter - WITHOUT auto-flush.

        Performance:
        --------------
        ### Specs:
        - RAM: 16 GB
        - Disk: 500 GB SSD
        - CPU: Intel Core i7-4510u

        ### Some Results:
        - Time taken to write 100 messages: 0.08 seconds.
        - Time taken to write 300 messages: 0.27 seconds.
        - Time taken to write 500 messages: 0.51 seconds.
        - Time taken to write 1000 messages: 0.98 seconds.
        - Time taken to write 2000 messages: 1.62 seconds.
        """
        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)
        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        # Set flush to false
        file_writer.use_write_flush = False


        start_time: float = time.time()

        # Use context manager to log batches
        with file_writer as fw:
            fw.write(ST_MESSAGE)

        end_time: float = time.time()
        elapsed_time: float = end_time - start_time
        print(
            f"Time taken to write {batch_size} messages in context manager: {elapsed_time:.4f} seconds"
        )

        # Check if the log message is written to the files
        for file_path in file_writer.file_paths:
            with open(file_path, "r") as f:
                content = f.read()
                assert ST_MESSAGE in content

        # Clear the file writer
        file_writer.clear_all()

        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after context manager exit"


class TestFileWriterAsyncPerformance:
    """
    Performance tests for FileWriter class in asynchronous mode.
    These tests measure the time taken to write messages in batches.

    Tests:
    -------
    - **test_bench_file_writer:**
        - Benchmark test for writing messages to files.
    """

    # Async Performance Tests

    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_file_writer_log_async_batches(
        self, file_writer: FileWriter, tmp_path, batch_size
    ):
        """
        Test the async_write method of FileWriter.

        Performance:
        --------------
        ### Specs:
        - RAM: 16 GB
        - Disk: 500 GB SSD
        - CPU: Intel Core i7-4510u

        ### Some Results:
        - Time taken to write 100 messages: 0.03 seconds.
        - Time taken to write 300 messages: 0.08 seconds.
        - Time taken to write 500 messages: 0.11 seconds.
        - Time taken to write 1000 messages: 0.20 seconds.
        - Time taken to write 2000 messages: 0.39 seconds.
        """
        # Close the sync pool before starting async operations
        file_writer.clear_sync_pool()

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)
        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        start_time: float = time.time()

        # Call the async log_batches method
        await file_writer.async_write(ST_MESSAGE)

        # Force the file handler to flush the buffer
        file_writer.buffer_force_flush()

        end_time: float = time.time()
        elapsed_time: float = end_time - start_time
        # Debug print
        print(f"\nAsync time taken to write {batch_size} messages: {elapsed_time:.4f} seconds")

        # Check if the log message is written to the files
        for file_path in file_writer.file_paths:
            with open(file_path, "r") as f:
                content = f.read()
                assert ST_MESSAGE in content

        # After flushing, the buffer should be empty
        file_writer.clear_all()
        assert (
            file_writer.get_buffer_size == 0
        ), "Buffer should be empty after flush"


    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_file_writer_cm_log_async_batches(
        self, file_writer: FileWriter, tmp_path, batch_size
    ):
        """
        Test the async context manager async_write method of FileWriter.

        Performance:
        --------------
        ### Specs:
        - RAM: 16 GB
        - Disk: 500 GB SSD
        - CPU: Intel Core i7-4510u

        ### Some Results:
        - Time taken to write 100 messages: 0.11 seconds.
        - Time taken to write 300 messages: 0.28 seconds.
        - Time taken to write 500 messages: 0.48 seconds.
        - Time taken to write 1000 messages: 0.83 seconds.
        - Time taken to write 2000 messages: 1.66 seconds.
        """
        # Close the sync pool before starting async operations
        file_writer.clear_sync_pool()

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)
        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        start_time: float = time.time()

        # Use async context manager to log batches
        async with file_writer as fw:
            await fw.async_write(ST_MESSAGE)

        end_time: float = time.time()
        elapsed_time: float = end_time - start_time
        print(
            f"\nAsync time taken to write {batch_size} messages in context manager: {elapsed_time:.4f} seconds"
        )

        # Check if the log message is written to the files
        for file_path in file_writer.file_paths:
            with open(file_path, "r") as f:
                content = f.read()
                assert ST_MESSAGE in content

        # After exiting the context, file_paths should be cleared
        file_writer.clear_all()
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after context manager exit"


    # Async With no Flush Performance Tests


    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_file_writer_log_async_batches_no_flush(
        self, file_writer: FileWriter, tmp_path, batch_size
    ):
        """
        Test the async_write method of FileWriter - WITHOUT auto-flush.

        Performance:
        --------------
        ### Specs:
        - RAM: 16 GB
        - Disk: 500 GB SSD
        - CPU: Intel Core i7-4510u

        ### Some Results:
        - Time taken to write 100 messages: 0.02 seconds.
        - Time taken to write 300 messages: 0.06 seconds.
        - Time taken to write 500 messages: 0.11 seconds.
        - Time taken to write 1000 messages: 0.24 seconds.
        - Time taken to write 2000 messages: 0.40 seconds.
        """
        # Close the sync pool before starting async operations
        file_writer.clear_sync_pool()

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)
        file_writer.file_paths = temp_files

        # Set flush to false
        file_writer.use_write_flush = False

        start_time: float = time.time()

        # Call the async log_batches method
        await file_writer.async_write(ST_MESSAGE)

        # Force the file handler to flush the buffer
        file_writer.buffer_force_flush()

        end_time: float = time.time()
        elapsed_time: float = end_time - start_time
        print(f"\nAsync time taken to write {batch_size} messages: {elapsed_time:.4f} seconds")

        # Check if the log message is written to the files
        for file_path in file_writer.file_paths:
            with open(file_path, "r") as f:
                content = f.read()
                assert ST_MESSAGE in content

        file_writer.clear_all()
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after async_write"



    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_file_writer_cm_log_async_batches_no_flush(
        self, file_writer: FileWriter, tmp_path, batch_size
    ):
        """
        Test the async context manager async_write method of FileWriter - WITHOUT auto-flush.

        Performance:
        --------------
        ### Specs:
        - RAM: 16 GB
        - Disk: 500 GB SSD
        - CPU: Intel Core i7-4510u

        ### Some Results:
        - Time taken to write 100 messages: 0.09 seconds.
        - Time taken to write 300 messages: 0.33 seconds.
        - Time taken to write 500 messages: 0.46 seconds.
        - Time taken to write 1000 messages: 0.89 seconds.
        - Time taken to write 2000 messages: 1.45 seconds.
        """
        # Close the sync pool before starting async operations
        file_writer.clear_sync_pool()

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)
        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        # Set flush to false
        file_writer.use_write_flush = False

        start_time: float = time.time()

        # Use async context manager to log batches
        async with file_writer as fw:
            await fw.async_write(ST_MESSAGE)

        end_time: float = time.time()
        elapsed_time: float = end_time - start_time
        print(
            f"\nAsync time taken to write {batch_size} messages in context manager: {elapsed_time:.4f} seconds"
        )

        # Check if the log message is written to the files
        for file_path in file_writer.file_paths:
            with open(file_path, "r") as f:
                content = f.read()
                assert ST_MESSAGE in content

        # After exiting the context, file_paths should be cleared
        file_writer.clear_all()

        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after context manager exit"


# ----------------------------------------------------------------------------------------------
# Benchmark Tests
# ----------------------------------------------------------------------------------------------


class TestFileWriterSyncBenchmarks:
    """
    Benchmark sync tests for FileWriter class.
    These tests measure the time taken to write messages in batches and using context managers.

    Tests:
    -------
    - **test_bench_file_writer:**
        - Benchmark test for writing messages to files.
    - **test_bench_file_writer_no_flush:**
        - Benchmark test for writing messages to files without auto-flush.
    - **test_bench_file_writer_cm_no_flush:**
        - Benchmark test for writing messages to files using context manager without auto-flush.
    - **test_bench_file_writer_cm:**
        - Benchmark test for writing messages to files using context manager.
    """
    @pytest.mark.benchmark(group="FileWriterSync")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_bench_file_writer(self, benchmark, file_writer: FileWriter, batch_size: int, tmp_path) -> None:
        """Benchmark test for writing messages to files."""

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)  

        # Set the file paths in the file writer
        file_writer.file_paths = temp_files     

        # Benchmark the write operation
        def write_messages():
            file_writer.write(ST_MESSAGE)

        benchmark(write_messages)

        # Assert that all messages were written
        assert len(file_writer.file_paths) == batch_size, f"Expected {batch_size} messages, got {len(file_writer.file_paths)}"

        file_writer.clear_all()

        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"


    @pytest.mark.benchmark(group="FileWriterSync")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_bench_file_writer_no_flush(
        self, benchmark, file_writer: FileWriter, batch_size: int, tmp_path
    ) -> None:
        """Benchmark test for writing messages to files without auto-flush."""

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)

        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        # Set flush to false
        file_writer.use_write_flush = False

        # Benchmark the write operation
        def write_messages_no_flush():
            file_writer.write(ST_MESSAGE)

        benchmark(write_messages_no_flush)

        # Assert that all messages were written
        assert len(file_writer.file_paths) == batch_size, f"Expected {batch_size} messages, got {len(file_writer.file_paths)}"

        file_writer.clear_all()

        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"


    @pytest.mark.benchmark(group="FileWriterSync")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_bench_file_writer_cm_no_flush(
        self, benchmark, file_writer: FileWriter, batch_size: int, tmp_path
    ) -> None:
        """Benchmark test for writing messages to files using context manager without auto-flush."""

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)

        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        # Set flush to false
        file_writer.use_write_flush = False

        # Benchmark the write operation using context manager
        def write_messages_cm_no_flush():
            with file_writer as fw:
                fw.write(ST_MESSAGE)

        benchmark(write_messages_cm_no_flush)

        file_writer.clear_all()

        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"


    @pytest.mark.benchmark(group="FileWriterSync")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_bench_file_writer_cm(
        self, benchmark, file_writer: FileWriter, batch_size: int, tmp_path
    ) -> None:
        """Benchmark test for writing messages to files using context manager."""

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)

        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        # Benchmark the write operation using context manager
        def write_messages_cm():
            with file_writer as fw:
                fw.write(ST_MESSAGE)

        benchmark(write_messages_cm)

        file_writer.clear_all()

        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"
    

class TestFileWriterAsyncBenchmarks:
    """
    Benchmark async tests for FileWriter class.
    These tests measure the time taken to write messages in batches and using context managers.
    
    Tests:
    -------
    - **test_bench_file_writer_async:**
        - Benchmark test for writing messages to files asynchronously.
    - **test_bench_file_writer_async_no_flush:**
        - Benchmark test for writing messages to files asynchronously without auto-flush.
    - **test_bench_file_writer_cm_async:**
        - Benchmark test for writing messages to files asynchronously using context manager.
    - **test_bench_file_writer_cm_async_no_flush:**
        - Benchmark test for writing messages to files asynchronously using context manager without auto-flush.
    """
    @pytest.mark.benchmark(group="FileWriterAsync")
    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_bench_file_writer_async(
        self, benchmark, file_writer: FileWriter, batch_size: int, tmp_path
    ) -> None:
        """Benchmark test for writing messages to files asynchronously."""

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)

        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        # Benchmark the async write operation
        async def write_messages_async():
            await file_writer.async_write(ST_MESSAGE)

        benchmark(write_messages_async)

        # Assert that all messages were written
        assert len(file_writer.file_paths) == batch_size, f"Expected {batch_size} messages, got {len(file_writer.file_paths)}"

        file_writer.clear_all()

        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"

    
    @pytest.mark.benchmark(group="FileWriterAsync")
    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_bench_file_writer_async_no_flush(
        self, benchmark, file_writer: FileWriter, batch_size: int, tmp_path
    ) -> None:
        """Benchmark test for writing messages to files asynchronously without auto-flush."""

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)

        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        # Set flush to false
        file_writer.use_write_flush = False

        # Benchmark the async write operation without auto-flush
        async def write_messages_async_no_flush():
            await file_writer.async_write(ST_MESSAGE)

        await benchmark(write_messages_async_no_flush)

        # Assert that all messages were written
        assert len(file_writer.file_paths) == batch_size, f"Expected {batch_size} messages, got {len(file_writer.file_paths)}"

        file_writer.clear_all()

        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"


    @pytest.mark.benchmark(group="FileWriterAsync")
    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_bench_file_writer_cm_async(
        self, benchmark, file_writer: FileWriter, batch_size: int, tmp_path
    ) -> None:
        """Benchmark test for writing messages to files asynchronously using context manager."""

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)

        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        # Benchmark the async write operation using context manager
        async def write_messages_cm_async():
            async with file_writer as fw:
                await fw.async_write(ST_MESSAGE)

        await benchmark(write_messages_cm_async)

        file_writer.clear_all()

        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"


    @pytest.mark.benchmark(group="FileWriterAsync")
    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_bench_file_writer_cm_async_no_flush(
        self, benchmark, file_writer: FileWriter, batch_size: int, tmp_path
    ) -> None:
        """Benchmark test for writing messages to files asynchronously using context manager without auto-flush."""

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)

        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        # Set flush to false
        file_writer.use_write_flush = False

        # Benchmark the async write operation using context manager without auto-flush
        async def write_messages_cm_async_no_flush():
            async with file_writer as fw:
                await fw.async_write(ST_MESSAGE)

        await benchmark(write_messages_cm_async_no_flush)

        file_writer.clear_all()

        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"


# ----------------------------------------------------------------------------------------------
# Memory Tests
# ----------------------------------------------------------------------------------------------


class TestFileWriterMemoryUsage:
    """
    Memory usage tests for FileWriter class in synchronous mode.
    These tests measure the memory usage during file operations.

    Tests:
    -------
    - **test_memory_usage:**
        - Tests memory usage during file operations.
    - **test_memory_usage_async:**
        - Tests memory usage during async file operations.
    """     
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_memory_usage(self, tmp_path, batch_size: int):
        """
        Test memory usage during file operations.

        Performance:
        --------------
        ### Specs:
        - RAM: 16 GB
        - Disk: 500 GB SSD
        - CPU: Intel Core i7-4510u

        ### Some Results:
        - **100 messages:**
            -   Initial memory usage: 45273088 bytes (44212.0 KB, 43.18 MB)
            -   After memory usage: 45305856 bytes (44244.0 KB, 43.21 MB)
            -   Memory difference for 100 logs: 32.0 KB (0.03 MB)
        - **300 messages:**
            -   Initial memory usage: 45301760 bytes (44240.0 KB, 43.2 MB)
            -   After memory usage: 45322240 bytes (44260.0 KB, 43.22 MB)
            -   Memory difference for 300 logs: 20.0 KB (0.02 MB)
        - **500 messages:**
            -   Initial memory usage: 45301760 bytes (44240.0 KB, 43.2 MB)
            -   After memory usage: 45363200 bytes (44300.0 KB, 43.26 MB)
            -   Memory difference for 500 logs: 60.0 KB (0.06 MB)
        - **1000 messages:**
            -   Initial memory usage: 45342720 bytes (44280.0 KB, 43.24 MB)
            -   After memory usage: 45363200 bytes (44300.0 KB, 43.26 MB)
            -   Memory difference for 1000 logs: 20.0 KB (0.02 MB)
        - **2000 messages:**
            -   Initial memory usage: 45342720 bytes (44280.0 KB, 43.24 MB)
            -   After memory usage: 45363200 bytes (44300.0 KB, 43.26 MB)
            -   Memory difference for 2000 logs: 20.0 KB (0.02 MB)
        """
        print("Testing memory usage for batch size:", batch_size)

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss  # Resident Set Size
        initial_memory_mb = round(initial_memory / (1024 * 1024), 2)  # Convert to MB
        initial_memory_kb = round(initial_memory / 1024, 2)  # Convert to KB

        print(
            f"Initial memory usage: {initial_memory} bytes ({initial_memory_kb} KB, {initial_memory_mb} MB)"
        )

        # Create a FileWriter instance
        temp_file = tmp_path / "memory_messages.log"
        handler: FileWriter = FileWriter(file_paths=[temp_file])

        # Write some messages
        for i in range(batch_size):
            handler.write(f"Memory test message {i}")

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
            f"Memory difference for {batch_size} messages: {leak_memory_kb} KB ({leak_memory_mb} MB)"
        )

        # Cleanup
        handler.clear_all()

        assert len(handler.file_paths) == 0, "File paths should be cleared after operations"

        with open(temp_file, "r") as f:
            content = f.read()
            assert len(content) > 0, "Log file should not be empty after writing messages"
            for i in range(batch_size):
                assert (
                    f"Memory test message {i}" in content
                ), f"Log message {i} should be present in the file"


    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_memory_usage_async(self, tmp_path, batch_size: int):
        """
        Test memory usage during async file operations.

        Performance:
        --------------
        ### Specs:
        - RAM: 16 GB
        - Disk: 500 GB SSD
        - CPU: Intel Core i7-4510u

        ### Some Results:
        - **100 messages:**
            -   Initial memory usage: 43151360 bytes (42140.0 KB, 41.15 MB)
            -   After memory usage: 43200512 bytes (42188.0 KB, 41.2 MB)
            -   Memory difference for 100 messages: 48.0 KB (0.05 MB)
        - **300 messages:**
            -   Initial memory usage: 43200512 bytes (42188.0 KB, 41.2 MB)
            -   After memory usage: 43266048 bytes (42252.0 KB, 41.26 MB)
            -   Memory difference for 300 messages: 64.0 KB (0.06 MB)
        - **500 messages:**
            -   Initial memory usage: 43249664 bytes (42236.0 KB, 41.25 MB)
            -   After memory usage: 43327488 bytes (42312.0 KB, 41.32 MB)
            -   Memory difference for 500 messages: 76.0 KB (0.07 MB)
        - **1000 messages:**
            -   Initial memory usage: 43315200 bytes (42300.0 KB, 41.31 MB)
            -   After memory usage: 43433984 bytes (42416.0 KB, 41.42 MB)
            -   Memory difference for 1000 messages: 116.0 KB (0.11 MB)
        - **2000 messages:**
            -   Initial memory usage: 43413504 bytes (42396.0 KB, 41.4 MB)
            -   After memory usage: 43692032 bytes (42668.0 KB, 41.67 MB)
            -   Memory difference for 2000 messages: 272.0 KB (0.27 MB)
        """
        print("Testing async memory usage for batch size:", batch_size)

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        initial_memory_mb = round(initial_memory / (1024 * 1024), 2)  # Convert to MB
        initial_memory_kb = round(initial_memory / 1024, 2)  # Convert to KB

        print(
            f"Initial memory usage: {initial_memory} bytes ({initial_memory_kb} KB, {initial_memory_mb} MB)"
        )
        # Create a FileWriter instance
        temp_file = tmp_path / "async_memory_test.log"
        handler: FileWriter = FileWriter(file_paths=[temp_file])
        # Write some logs asynchronously
        for i in range(batch_size):
            await handler.async_write(f"Async Memory test message {i}")
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
            f"Memory difference for {batch_size} messages: {leak_memory_kb} KB ({leak_memory_mb} MB)"
        )

        # Cleanup
        handler.clear_all()

        assert len(handler.file_paths) == 0, "File paths should be cleared after operations"

        with open(temp_file, "r") as f:
            content = f.read()
            assert len(content) > 0, "Log file should not be empty after writing logs"
            for i in range(batch_size):
                assert (
                    f"Async Memory test message {i}" in content
                ), f"Log message {i} should be present in the file"


# ----------------------------------------------------------------------------------------------
# Stress Tests
# ----------------------------------------------------------------------------------------------


class TestFileWriterSyncStress:

    @pytest.mark.benchmark(group="FileWriterSyncStress")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_bench_stress(self, benchmark, file_writer: FileWriter, batch_size: int, tmp_path) -> None:
        """
        Benchmark test for writing a large number of messages to files.
        """

        long_message: str = ST_MESSAGE * 1000  # Create a long message by repeating the string

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)  

        # Set the file paths in the file writer
        file_writer.file_paths = temp_files     

        # Benchmark the write operation
        def write_messages():
            file_writer.write(long_message)

        benchmark(write_messages)

        # Assert that all messages were written
        assert len(file_writer.file_paths) == batch_size, f"Expected {batch_size} messages, got {len(file_writer.file_paths)}"

        file_writer.clear_all()

        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"


    @pytest.mark.benchmark(group="FileWriterSyncStress")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_bench_stress_no_flush(
        self, benchmark, file_writer: FileWriter, batch_size: int, tmp_path
    ) -> None:
        """
        Benchmark test for writing a large number of messages to files without auto-flush.
        """

        long_message: str = ST_MESSAGE * 1000  # Create a long message by repeating the string

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)

        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        # Set flush to false
        file_writer.use_write_flush = False

        # Benchmark the write operation
        def write_messages_no_flush():
            file_writer.write(long_message)

        benchmark(write_messages_no_flush)

        # Assert that all messages were written
        assert len(file_writer.file_paths) == batch_size, f"Expected {batch_size} messages, got {len(file_writer.file_paths)}"

        file_writer.clear_all()

        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"


    @pytest.mark.benchmark(group="FileWriterSyncStress")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_bench_stress_cm(
        self, benchmark, file_writer: FileWriter, batch_size: int, tmp_path
    ) -> None:
        """
        Benchmark test for writing a large number of messages to files using context manager.
        """

        long_message: str = ST_MESSAGE * 1000  # Create a long message by repeating the string

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)

        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        # Benchmark the write operation using context manager
        def write_messages_cm():
            with file_writer as fw:
                fw.write(long_message)

        benchmark(write_messages_cm)

        file_writer.clear_all()

        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"


    @pytest.mark.benchmark(group="FileWriterSyncStress")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_bench_stress_cm_no_flush(
        self, benchmark, file_writer: FileWriter, batch_size: int, tmp_path
    ) -> None:
        """
        Benchmark test for writing a large number of messages to files using context manager without auto-flush.
        """

        long_message: str = ST_MESSAGE * 1000  # Create a long message by repeating the string

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)

        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        # Set flush to false
        file_writer.use_write_flush = False

        # Benchmark the write operation using context manager
        def write_messages_cm_no_flush():
            with file_writer as fw:
                fw.write(long_message)

        benchmark(write_messages_cm_no_flush)

        file_writer.clear_all()

        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"


class TestFileWriterAsyncStress:

    @pytest.mark.benchmark(group="FileWriterAsyncStress")
    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_bench_stress_async(
        self, benchmark, file_writer: FileWriter, batch_size: int, tmp_path
    ) -> None:
        """
        Benchmark test for writing a large number of messages to files asynchronously.
        """

        long_message: str = ST_MESSAGE * 1000  # Create a long message by repeating the string

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)

        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        # Benchmark the async write operation
        async def write_messages_async():
            await file_writer.async_write(long_message)

        await benchmark(write_messages_async)

        # Assert that all messages were written
        assert len(file_writer.file_paths) == batch_size, f"Expected {batch_size} messages, got {len(file_writer.file_paths)}"

        file_writer.clear_all()

        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"


    @pytest.mark.benchmark(group="FileWriterAsyncStress")
    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_bench_stress_async_no_flush(
        self, benchmark, file_writer: FileWriter, batch_size: int, tmp_path
    ) -> None:
        """
        Benchmark test for writing a large number of messages to files asynchronously without auto-flush.
        """

        long_message: str = ST_MESSAGE * 1000  # Create a long message by repeating the string

        # Make temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)

        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        # Set flush to false
        file_writer.use_write_flush = False

        # Benchmark the async write operation without auto-flush
        async def write_messages_async_no_flush():
            await file_writer.async_write(long_message)

        await benchmark(write_messages_async_no_flush)

        # Assert that all messages were written
        assert len(file_writer.file_paths) == batch_size, f"Expected {batch_size} messages, got {len(file_writer.file_paths)}"

        file_writer.clear_all()
        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"


    @pytest.mark.benchmark(group="FileWriterAsyncStress")
    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_bench_stress_cm_async(
        self, benchmark, file_writer: FileWriter, batch_size: int, tmp_path
    ) -> None:
        """
        Benchmark test for writing a large number of messages to files asynchronously using context manager.
        """

        long_message: str = ST_MESSAGE * 1000

        # Create temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)

        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        # Benchmark the async write operation using context manager
        async def write_messages_cm_async():
            async with file_writer as fw:
                await fw.async_write(long_message)
        
        await benchmark(write_messages_cm_async)

        file_writer.clear_all()

        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"


    @pytest.mark.benchmark(group="FileWriterAsyncStress")
    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_bench_stress_cm_async_no_flush(
        self, benchmark, file_writer: FileWriter, batch_size: int, tmp_path
    ) -> None:
        """ 
        Benchmark test for writing a large number of messages to files asynchronously using context manager without auto-flush.
        """

        long_message: str = ST_MESSAGE * 1000

        # Create temporary paths
        temp_files: List[Path] = temporary_file_writer(batch_size, tmp_path)

        # Set the file paths in the file writer
        file_writer.file_paths = temp_files

        # Set flush to false
        file_writer.use_write_flush = False

        # Benchmark the async write operation using context manager
        async def write_messages_cm_async():
            async with file_writer as fw:
                await fw.async_write(long_message)
        
        await benchmark(write_messages_cm_async)

        file_writer.clear_all()

        assert len(file_writer.file_paths) == 0, "File paths should be cleared after operations"



# ----------------------------------------------------------------------------------------------
# End of file