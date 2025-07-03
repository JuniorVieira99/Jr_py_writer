# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
import time
import os

from pathlib import Path
from typing import Any, Generator, List, Final, Dict, Union

# Third-party imports
import pytest
import psutil

# Local imports
from jr_file_handler.classes.file_writer import FileWriter
from jr_file_handler.classes.file_reader import FileReader


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


def make_file_reader(
    file_paths: List[Union[Path, str]],
    retry_limit: int = 0,
    retry_delay: float = 0.0,
    backoff_factor: float = 0.0,
) -> FileReader:
    """
    Create a FileReader instance with specified parameters.

    Arguments:
        file_paths (List[Path | str]): List of file paths to read.
        retry_limit (int): Number of retries for reading files.
        retry_delay (float): Delay between retries in seconds.
        backoff_factor (float): Backoff factor for retries.

    Returns:
        FileReader: An instance of FileReader.
    """
    return FileReader(
        file_paths=file_paths,
        retry_limit=retry_limit,
        retry_delay=retry_delay,
        backoff_factor=backoff_factor,
    )


def temporary_file_handler(num: int, tmp_path) -> List[Path]:
    """Fixture for creating temporary files for testing."""
    file_paths = [tmp_path / f"test_{i}.log" for i in range(1, num + 1)]
    for file_path in file_paths:
        file_path.touch()
    return file_paths


def write_files(file_writer: FileWriter, message: str, path_list: List[Path]) -> None:
    """
    Write a specified number of messages to the file using the FileWriter.

    Arguments:
        file_writer (FileWriter): The FileWriter instance.
        num (int): The number of times to write the message.
        path_list (List[Path]): List of file paths to write to.
    """
    file_writer.file_paths = path_list
    with file_writer as fw:
        fw.write(message)


# ----------------------------------------------------------------------------------------------
# Tests Cases
# ----------------------------------------------------------------------------------------------


ST_MESSAGE: Final[str] = "This is a test message for the file reader and writer."


BATCH_TEST_CASES: Final[List[int]] = [100, 300, 500, 1000, 2000]


# ----------------------------------------------------------------------------------------------
# Performance Tests
# ----------------------------------------------------------------------------------------------


# Sync
class TestFileReaderPerformance:
    """
    Test performance of FileReader and FileWriter.

    Tests:
    -------
    - **test_file_reader_performance:**
        - Test performance of file reading and writing operations.
    - **test_file_reader_cm_performance:**
        - Test performance of file reading and writing operations using context manager.
    """

    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_file_reader_performance(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
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
        temp_files = temporary_file_handler(batch_size, tmp_path)

        # Write files
        write_files(file_writer, ST_MESSAGE, temp_files)

        # Assert that message was written correctly
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                read = f.read()
                assert (
                    len(read) > 0
                ), "Messages file should not be empty after writing logs"
                assert ST_MESSAGE in read, "Messages should be present in the file"

        # Set File Writer paths
        file_reader.file_paths = temp_files

        # Read the data back
        start_time = time.time()

        read_data: Dict[Path, str | Exception] = file_reader.read()

        end_time = time.time()
        elapsed_time = end_time - start_time

        # Debug print
        print(f"Time taken to read {batch_size} messages: {elapsed_time:.4f} seconds")

        # Assert should be correct if all other tests passed
        assert (
            len(read_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(read_data)}"
        # Assert that all read data contains the expected message
        for path, content in read_data.items():
            if isinstance(content, Exception):
                pytest.fail(f"Error reading file {path}: {content}")
            if isinstance(content, str):
                assert ST_MESSAGE in content, f"Message not found in file {path}"

        # Cleanup
        file_reader.clear_all()
        file_writer.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"

    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_file_reader_cm_performance(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
        """
        Test performance of file reading and writing operations using context manager.

        Performance:
        --------------
        ### Specs:
        - RAM: 16 GB
        - Disk: 500 GB SSD
        - CPU: Intel Core i7-4510u
        """
        # Make temporary files
        temp_files = temporary_file_handler(batch_size, tmp_path)

        # Write some messages
        write_files(file_writer, ST_MESSAGE, temp_files)

        # Assert that message was written correctly
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                read = f.read()
                assert len(read) > 0, "Log file should not be empty after writing logs"
                assert ST_MESSAGE in read, "Log messages should be present in the file"

        # Set File Writer paths
        file_reader.file_paths = temp_files

        # Read the data back using context manager
        start_time = time.time()

        with file_reader as fr:
            read_data: Dict[Path, str | Exception] = fr.read()

        end_time = time.time()
        elapsed_time = end_time - start_time

        # Debug print
        print(
            f"Time taken to read {batch_size} logs using context manager: {elapsed_time:.4f} seconds"
        )

        # Assert should be correct if all other tests passed
        assert (
            len(read_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(read_data)}"

        # Cleanup
        file_reader.clear_all()
        file_writer.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"

    # Generator Sync
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_file_reader_performance_generator(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
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
        temp_files = temporary_file_handler(batch_size, tmp_path)

        # Write some messages
        write_files(file_writer, ST_MESSAGE, temp_files)

        # Assert that message was written correctly
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                read = f.read()
                assert len(read) > 0, "File should not be empty after writing messages"
                assert ST_MESSAGE in read, "Messages should be present in the file"

        # Set File Writer paths
        file_reader.file_paths = temp_files

        # Read the data back using generator
        start_time = time.time()
        read_data: Dict[Path, Generator[str, None, None] | Exception] = (
            file_reader.read_generator()
        )

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(
            f"-[No unpacking] - Time taken to read {batch_size} messages using generator: {elapsed_time:.4f} seconds"
        )

        # Unpack the generator to read data
        start_time = time.time()
        unpacked_data: Dict[Path, str | Exception] = file_reader.unpacker(read_data)

        end_time = time.time()
        elapsed_time_unpacking = end_time - start_time
        print(
            f"-[Unpacking] - Time taken to unpack {batch_size} messages using generator: {elapsed_time_unpacking:.4f} seconds"
        )
        print(
            f"Total time taken to read and unpack {batch_size} messages using generator: {elapsed_time + elapsed_time_unpacking:.4f} seconds"
        )

        # Assert should be correct if all other tests passed
        assert (
            len(unpacked_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(unpacked_data)}"

        # Cleanup
        file_reader.clear_all()
        file_writer.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"

    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_file_reader_cm_performance_generator(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
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

        # Write some messages
        write_files(file_writer, ST_MESSAGE, temp_file)

        # Assert that message was written correctly
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                read = f.read()
                assert len(read) > 0, "File should not be empty after writing messages"
                assert ST_MESSAGE in read, "Messages should be present in the file"

        # Set File Writer paths
        file_reader.file_paths = temp_file

        # Read the data back using context manager and generator
        start_time = time.time()
        with file_reader as fr:
            read_data: Dict[Path, Generator[str, None, None] | Exception] = (
                fr.read_generator()
            )

        end_time = time.time()
        elapsed_time = end_time - start_time
        # Debug print
        print(
            f"\n-[No unpacking] - Time taken to read {batch_size} messages using context manager and generator: {elapsed_time:.4f} seconds"
        )

        # Unpack the generator to read data
        start_time = time.time()
        unpacked_data: Dict[Path, str | Exception] = file_reader.unpacker(read_data)

        end_time = time.time()
        elapsed_time_unpacking = end_time - start_time
        # Debug print
        print(
            f"\n-[Unpacking] - Time taken to unpack {batch_size} messages using context manager and generator: {elapsed_time_unpacking:.4f} seconds"
        )
        print(
            f"\nTotal time taken to read and unpack {batch_size} messages using context manager and generator: {elapsed_time + elapsed_time_unpacking:.4f} seconds"
        )

        # Assert should be correct if all other tests passed
        assert (
            len(unpacked_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(unpacked_data)}"

        # Cleanup
        file_reader.clear_all()
        file_writer.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"


# Async
class TestFileReaderPerformanceAsync:
    """
    Test performance of FileReader and FileWriter asynchronously.

    Tests:
    -------
    - **test_file_reader_performance_async:**
        - Test performance of asynchronous file reading and writing operations.
    - **test_file_reader_cm_performance_async:**
        - Test performance of asynchronous file reading and writing operations using context manager.
    - **test_file_reader_performance_generator_async:**
        - Test performance of asynchronous file reading and writing operations using generator.
    - **test_file_reader_cm_performance_generator_async:**
        - Test performance of asynchronous file reading and writing operations using generator with context manager.
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_file_reader_performance_async(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
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

        # Write some messages
        write_files(file_writer, ST_MESSAGE, temp_file)

        # Assert that message was written correctly
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                read = f.read()
                assert len(read) > 0, "File should not be empty after writing messages"
                assert ST_MESSAGE in read, "Messages should be present in the file"

        # Read the data back asynchronously

        # Set File Reader paths
        file_reader.file_paths = temp_file

        start_time = time.time()
        read_data: Dict[Path, str | Exception] = await file_reader.async_read()

        end_time = time.time()
        elapsed_time = end_time - start_time
        # Debug print
        print(
            f"\nTime taken to read {batch_size} messages asynchronously: {elapsed_time:.4f} seconds"
        )

        # Assert should be correct if all other tests passed
        assert (
            len(read_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(read_data)}"

        # Cleanup
        file_reader.clear_all()
        file_writer.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_file_reader_cm_performance_async(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
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

        # Write some messages
        write_files(file_writer, ST_MESSAGE, temp_file)

        # Assert that message was written correctly
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                read = f.read()
                assert len(read) > 0, "File should not be empty after writing messages"
                assert ST_MESSAGE in read, "Messages should be present in the file"

        # Read the data back asynchronously using context manager

        # Set File Reader paths
        file_reader.file_paths = temp_file

        start_time = time.time()
        async with file_reader as fr:
            data_read: Dict[Path, str | Exception] = await fr.async_read()

        end_time = time.time()
        elapsed_time = end_time - start_time
        # Debug print
        print(
            f"\nTime taken to read {batch_size} messages asynchronously using context manager: {elapsed_time:.4f} seconds"
        )

        # Assert should be correct if all other tests passed
        assert (
            len(data_read) == batch_size
        ), f"Expected {batch_size} paths, got {len(data_read)}"

        # Cleanup
        file_reader.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"

    # Async Generator

    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_file_reader_performance_async_generator(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
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

        # Write some messages
        write_files(file_writer, ST_MESSAGE, temp_file)

        # Assert that message was written correctly
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                read = f.read()
                assert len(read) > 0, "File should not be empty after writing messages"
                assert ST_MESSAGE in read, "Messages should be present in the file"

        # Read the data back asynchronously using generator

        # Set File Reader paths
        file_reader.file_paths = temp_file

        start_time = time.time()
        read_data: Dict[Path, Generator[str, None, None] | Exception] = (
            await file_reader.async_read_generator()
        )

        end_time = time.time()
        elapsed_time = end_time - start_time
        # Debug print
        print(
            f"\n-[No unpacking] - Time taken to read {batch_size} messages asynchronously using generator: {elapsed_time:.4f} seconds"
        )

        # Unpack the generator to read data
        start_time = time.time()
        unpacked_data: Dict[Path, str | Exception] = file_reader.unpacker(read_data)

        end_time = time.time()
        elapsed_time_unpacking = end_time - start_time
        # Debug print
        print(
            f"\n-[Unpacking] - Time taken to unpack {batch_size} messages asynchronously using generator: {elapsed_time_unpacking:.4f} seconds"
        )
        print(
            f"\nTotal time taken to read and unpack {batch_size} messages asynchronously using generator: {elapsed_time + elapsed_time_unpacking:.4f} seconds"
        )

        # Assert should be correct if all other tests passed
        assert (
            len(unpacked_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(unpacked_data)}"

        # Cleanup
        file_reader.clear_all()
        file_writer.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_file_reader_cm_performance_async_generator(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
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

        # Write some messages
        write_files(file_writer, ST_MESSAGE, temp_file)

        # Assert that message was written correctly
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                read = f.read()
                assert len(read) > 0, "File should not be empty after writing messages"
                assert ST_MESSAGE in read, "Messages should be present in the file"

        # Read the data back asynchronously using context manager and generator

        # Set File Reader paths
        file_reader.file_paths = temp_file

        start_time = time.time()
        async with file_reader as fr:
            read_data: Dict[Path, Generator[str, None, None] | Exception] = (
                await fr.async_read_generator()
            )

        end_time = time.time()
        elapsed_time = end_time - start_time
        # Debug print
        print(
            f"\n-[No unpacking] - Time taken to read {batch_size} messages asynchronously using context manager and generator: {elapsed_time:.4f} seconds"
        )

        # Unpack the generator to read data
        start_time = time.time()
        unpacked_data: Dict[Path, str | Exception] = file_reader.unpacker(read_data)

        end_time = time.time()
        elapsed_time_unpacking = end_time - start_time
        # Debug print
        print(
            f"\n-[Unpacking] - Time taken to unpack {batch_size} messages asynchronously using context manager and generator: {elapsed_time_unpacking:.4f} seconds"
        )
        print(
            f"\nTotal time taken to read and unpack {batch_size} messages asynchronously using context manager and generator: {elapsed_time + elapsed_time_unpacking:.4f} seconds"
        )

        # Assert should be correct if all other tests passed
        assert (
            len(unpacked_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(unpacked_data)}"

        # Cleanup
        file_reader.clear_all()
        file_writer.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"


# ----------------------------------------------------------------------------------------------
# Benchmark Tests
# ----------------------------------------------------------------------------------------------


class TestFileReaderSyncBenchmark:
    """
    Test benchmark performance of FileReader and FileWriter.

    Tests:
    -------
    - **test_bench_sync:**
        - Benchmark test for synchronous file reading and writing operations.
    - **test_bench_sync_cm:**
        - Benchmark test for synchronous file reading and writing operations using context manager.
    - **test_bench_sync_generator:**
        - Benchmark test for synchronous file reading and writing operations using generator.
    - **test_bench_sync_generator_cm:**
        - Benchmark test for synchronous file reading and writing operations using generator with context manager.
    """

    @pytest.mark.benchmark(group="FileReaderSync")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_bench_sync(
        self,
        benchmark,
        file_writer: FileWriter,
        file_reader: FileReader,
        batch_size: int,
        tmp_path,
    ):
        """
        Benchmark test for synchronous file reading and writing operations.

        Performance:
        --------------
        ### Specs:
        - RAM: 16 GB
        - Disk: 500 GB SSD
        - CPU: Intel Core i7-4510u
        """

        # Create a FileHandler instance
        temp_files = temporary_file_handler(batch_size, tmp_path)

        # Write files
        write_files(file_writer, ST_MESSAGE, temp_files)

        # Assert that message was written correctly
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                read = f.read()
                assert (
                    len(read) > 0
                ), "Messages file should not be empty after writing logs"
                assert ST_MESSAGE in read, "Messages should be present in the file"

        # Set File Writer paths
        file_reader.file_paths = temp_files

        # Benchmark the read operation
        def read_files():
            return file_reader.read()

        # Benchmark the read operation
        read_data: Dict[Path, str | Exception] = benchmark(read_files)

        # Assert should be correct if all other tests passed
        assert (
            len(read_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(read_data)}"

        # Cleanup
        file_reader.clear_all()
        file_writer.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"

    @pytest.mark.benchmark(group="FileReaderSync")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_bench_sync_generator(
        self, benchmark, file_writer, file_reader, batch_size: int, tmp_path
    ):
        """
        Benchmark test for synchronous file reading and writing operations using generator.

        Performance:
        --------------
        ### Specs:
        - RAM: 16 GB
        - Disk: 500 GB SSD
        - CPU: Intel Core i7-4510u
        """

        # Make temp files
        temp_file = temporary_file_handler(batch_size, tmp_path)

        # Write files
        write_files(file_writer, ST_MESSAGE, temp_file)

        # Read files
        file_reader.file_paths = temp_file

        def read_files():
            read_data: Dict[Path, Generator[str, None, None] | Exception] = (
                file_reader.read_generator()
            )
            unpacked_data = file_reader.unpacker(read_data)
            return unpacked_data

        # Benchmark the read operation
        read_data = benchmark(read_files)

        # Assert should be correct if all other tests passed
        assert (
            len(read_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(read_data)}"

        # Cleanup
        file_writer.clear_all()
        file_reader.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"


class TestFileReaderAsyncBenchmark:
    """
    Test benchmark performance of FileReader and FileWriter asynchronously.

    Tests:
    -------
    - **test_bench_async:**
        - Benchmark test for asynchronous file reading and writing operations.
    - **test_bench_async_cm:**
        - Benchmark test for asynchronous file reading and writing operations using context manager.
    - **test_bench_async_generator:**
        - Benchmark test for asynchronous file reading and writing operations using generator.
    - **test_bench_async_generator_cm:**
        - Benchmark test for asynchronous file reading and writing operations using generator with context manager.
    """

    @pytest.mark.asyncio
    @pytest.mark.benchmark(group="FileReaderAsync")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_bench_async(
        self, benchmark, file_writer, file_reader, batch_size: int, tmp_path
    ):
        """
        Benchmark test for asynchronous file reading and writing operations.
        """
        temp_file = temporary_file_handler(batch_size, tmp_path)
        write_files(file_writer, ST_MESSAGE, temp_file)
        file_reader.file_paths = temp_file

        async def read_files():
            read_data: Dict[Path, str | Exception] = await file_reader.async_read()
            return read_data

        read_data = await benchmark(read_files)
        assert (
            len(read_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(read_data)}"

        for path, content in read_data.items():
            if isinstance(content, Exception):
                pytest.fail(f"Error reading file {path}: {content}")
            assert ST_MESSAGE in content, f"Message not found in file {path}"

        file_writer.clear_all()
        file_reader.clear_all()
        assert len(file_writer.file_paths) == 0
        assert len(file_reader.file_paths) == 0

    @pytest.mark.asyncio
    @pytest.mark.benchmark(group="FileReaderAsync")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_bench_async_cm(
        self, benchmark, file_writer, file_reader, batch_size: int, tmp_path
    ):
        """
        Benchmark test for asynchronous file reading and writing operations using context manager.
        """
        temp_file = temporary_file_handler(batch_size, tmp_path)
        write_files(file_writer, ST_MESSAGE, temp_file)
        file_reader.file_paths = temp_file

        async def read_files():
            async with file_reader as fr:
                read_data: Dict[Path, str | Exception] = await fr.async_read()
            return read_data

        read_data = await benchmark(read_files)
        assert (
            len(read_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(read_data)}"
        for path, content in read_data.items():
            if isinstance(content, Exception):
                pytest.fail(f"Error reading file {path}: {content}")
            assert ST_MESSAGE in content, f"Message not found in file {path}"

        file_writer.clear_all()
        file_reader.clear_all()
        assert len(file_writer.file_paths) == 0
        assert len(file_reader.file_paths) == 0

    @pytest.mark.asyncio
    @pytest.mark.benchmark(group="FileReaderAsync")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_bench_async_generator(
        self, benchmark, file_writer, file_reader, batch_size: int, tmp_path
    ):
        """
        Benchmark test for asynchronous file reading operations using generator.
        """
        temp_file = temporary_file_handler(batch_size, tmp_path)
        write_files(file_writer, ST_MESSAGE, temp_file)
        file_reader.file_paths = temp_file

        async def read_files():
            read_data: Dict[Path, Generator[str, None, None] | Exception] = (
                await file_reader.async_read_generator()
            )
            unpacked_data = file_reader.unpacker(read_data)
            return unpacked_data

        read_data = await benchmark(read_files)
        assert (
            len(read_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(read_data)}"
        for path, content in read_data.items():
            if isinstance(content, Exception):
                pytest.fail(f"Error reading file {path}: {content}")
            assert ST_MESSAGE in content, f"Message not found in file {path}"

        file_writer.clear_all()
        file_reader.clear_all()
        assert len(file_writer.file_paths) == 0
        assert len(file_reader.file_paths) == 0

    @pytest.mark.asyncio
    @pytest.mark.benchmark(group="FileReaderAsync")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_bench_async_cm_generator(
        self, benchmark, file_writer, file_reader, batch_size: int, tmp_path
    ):
        """
        Benchmark test for asynchronous file reading operations using generator with context manager.
        """
        temp_file = temporary_file_handler(batch_size, tmp_path)
        write_files(file_writer, ST_MESSAGE, temp_file)
        file_reader.file_paths = temp_file

        async def read_files():
            async with file_reader as fr:
                read_data: Dict[Path, Generator[str, None, None] | Exception] = (
                    await fr.async_read_generator()
                )
                unpacked_data = file_reader.unpacker(read_data)
            return unpacked_data

        read_data = await benchmark(read_files)
        assert (
            len(read_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(read_data)}"
        for path, content in read_data.items():
            if isinstance(content, Exception):
                pytest.fail(f"Error reading file {path}: {content}")
            assert ST_MESSAGE in content, f"Message not found in file {path}"

        file_writer.clear_all()
        file_reader.clear_all()
        assert len(file_writer.file_paths) == 0
        assert len(file_reader.file_paths) == 0


# ----------------------------------------------------------------------------------------------
# Memory Tests
# ----------------------------------------------------------------------------------------------


class TestFileReaderMemory:
    """
    Test memory usage of FileReader and FileWriter.

    Tests:
    -------
    - **test_memory_usage:**
        - Test memory usage during file operations.
    """

    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_memory_usage(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
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
                assert (
                    "Memory test message" in read
                ), "Messages should be present in the file"

        # Cleanup
        file_writer.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"

        print("Testing memory usage of for batch size:", batch_size)

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss  # Resident Set Size
        initial_memory_mb = round(initial_memory / (1024 * 1024), 2)  # Convert to MB
        initial_memory_kb = round(initial_memory / 1024, 2)  # Convert to KB

        print(
            f"Initial memory usage: {initial_memory} bytes ({initial_memory_kb} KB, {initial_memory_mb} MB)"
        )

        # Read the data back
        read_data: Dict[Path, str | Exception] = file_reader.read()

        after_memory = process.memory_info().rss  # Resident Set Size after logging
        after_memory_mb = round(after_memory / (1024 * 1024), 2)  # Convert to MB
        after_memory_kb = round(after_memory / 1024, 2)  # Convert to KB
        print(
            f"After memory usage: {after_memory} bytes ({after_memory_kb} KB, {after_memory_mb} MB)"
        )

        leak_memory_kb = round(
            (after_memory - initial_memory) / 1024, 2
        )  # Convert to KB
        leak_memory_mb = round(
            (after_memory - initial_memory) / (1024 * 1024), 2
        )  # Convert to MB
        print(
            f"Memory difference for {batch_size} messages: {leak_memory_kb} KB ({leak_memory_mb} MB)"
        )

        # Assert Reading is done
        assert len(read_data) == 2, f"Expected {2} paths, got {len(read_data)}"

        # Cleanup
        file_reader.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"

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

        print("Memory usage test completed for batch size:", batch_size)


# ----------------------------------------------------------------------------------------------
# Stress Tests
# ----------------------------------------------------------------------------------------------


class TestFileReaderSyncStress:
    """
    Test stress performance of FileReader and FileWriter.

    Tests:
    -------
    - **test_file_reader_stress:**
        - Stress test for file reading and writing operations.
    - **test_file_reader_cm_stress:**
        - Stress test for file reading and writing operations using context manager.
    - **test_file_reader_generator_stress:**
        - Stress test for file reading and writing operations using generator.
    - **test_file_reader_cm_generator_stress:**
        - Stress test for file reading and writing operations using generator with context manager.
    """

    @pytest.mark.benchmark(group="FileReaderSyncStress")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_file_reader_stress(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
        """
        Stress test for file reading and writing operations.

        Performance:
        --------------
        ### Specs:
        - RAM: 16 GB
        - Disk: 500 GB SSD
        - CPU: Intel Core i7-4510u
        """

        long_message: str = ST_MESSAGE * 100  # Create a long message for stress testing

        # Create a FileHandler instance
        temp_files = temporary_file_handler(batch_size, tmp_path)

        # Write some messages
        write_files(file_writer, long_message, temp_files)

        # Assert that message was written correctly
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                read = f.read()
                assert (
                    len(read) > 0
                ), "Message file should not be empty after writing messages"
                assert any(
                    long_message in line for line in read.splitlines()
                ), "Long messages should be present in the file"

        # Set File Writer paths
        file_reader.file_paths = temp_files

        start_time = time.time()

        # Read the data back
        read_data: Dict[Path, str | Exception] = file_reader.read()

        end_time = time.time()
        elapsed_time = end_time - start_time
        # Debug print
        print(
            f"\nTime taken to read {batch_size} files of length {len(long_message)}: {elapsed_time:.4f} seconds"
        )

        # Assert should be correct if all other tests passed
        assert (
            len(read_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(read_data)}"
        # Assert that all read data contains the expected message
        for path, content in read_data.items():
            if isinstance(content, Exception):
                pytest.fail(f"Error reading file {path}: {content}")
            if isinstance(content, str):
                assert any(
                    long_message in line for line in content.splitlines()
                ), f"Long message not found in file {path}"

        # Cleanup
        file_reader.clear_all()
        file_writer.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"

    @pytest.mark.benchmark(group="FileReaderSyncStress")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_file_reader_cm_stress(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
        """
        Stress test for file reading and writing operations using context manager.
        """
        long_message: str = ST_MESSAGE * 100  # Create a long message for stress testing

        # Create a FileHandler instance
        temp_files = temporary_file_handler(batch_size, tmp_path)

        # Write some messages
        write_files(file_writer, long_message, temp_files)

        # Assert that message was written correctly
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                read = f.read()
                assert (
                    len(read) > 0
                ), "Message file should not be empty after writing message"
                assert any(
                    long_message in line for line in read.splitlines()
                ), "Long messages should be present in the file"

        # Set File Writer paths
        file_reader.file_paths = temp_files

        start_time: float = time.time()

        # Read the data back using context manager
        with file_reader as fr:
            read_data: Dict[Path, str | Exception] = fr.read()

        end_time: float = time.time()
        elapsed_time: float = end_time - start_time
        # Debug print
        print(
            f"\nTime taken to read {batch_size} files of length {len(long_message)}: {elapsed_time:.4f} seconds"
        )

        # Assert should be correct if all other tests passed
        assert (
            len(read_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(read_data)}"

        # Cleanup
        file_reader.clear_all()
        file_writer.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"

    @pytest.mark.benchmark(group="FileReaderSyncStress")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_file_reader_generator_stress(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
        """
        Stress test for file reading and writing operations using generator.
        """
        long_message: str = ST_MESSAGE * 100  # Create a long message for stress testing

        # Create a FileHandler instance
        temp_files = temporary_file_handler(batch_size, tmp_path)

        # Write some messages
        write_files(file_writer, long_message, temp_files)

        # Assert that message was written correctly
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                read = f.read()
                assert (
                    len(read) > 0
                ), "Messsage file should not be empty after writing messages"
                assert any(
                    long_message in line for line in read.splitlines()
                ), "Long messages should be present in the file"

        # Set File Writer paths
        file_reader.file_paths = temp_files

        start_time: float = time.time()

        # Read the data back using generator
        read_data: Dict[Path, Generator[str, None, None] | Exception] = (
            file_reader.read_generator()
        )
        unpacked_data: Dict[Path, str | Exception] = file_reader.unpacker(read_data)

        end_time: float = time.time()
        elapsed_time: float = end_time - start_time
        # Debug print
        print(
            f"\nTime taken to read {batch_size} files of length {len(long_message)}: {elapsed_time:.4f} seconds"
        )

        # Assert should be correct if all other tests passed
        assert (
            len(unpacked_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(unpacked_data)}"

        # Cleanup
        file_reader.clear_all()
        file_writer.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"

    @pytest.mark.benchmark(group="FileReaderSyncStress")
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    def test_file_reader_cm_generator_stress(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
        """
        Stress test for file reading and writing operations using generator with context manager.
        """
        long_message: str = ST_MESSAGE * 100  # Create a long message for stress testing

        # Create a FileHandler instance
        temp_files = temporary_file_handler(batch_size, tmp_path)

        # Write some messages
        write_files(file_writer, long_message, temp_files)

        # Assert that message was written correctly
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                read = f.read()
                assert (
                    len(read) > 0
                ), "Message file should not be empty after writing message"
                assert any(
                    long_message in line for line in read.splitlines()
                ), "Long messages should be present in the file"

        # Set File Writer paths
        file_reader.file_paths = temp_files

        start_time: float = time.time()

        # Read the data back using context manager and generator
        with file_reader as fr:
            read_data: Dict[Path, Generator[str, None, None] | Exception] = (
                fr.read_generator()
            )
            unpacked_data: Dict[Path, str | Exception] = file_reader.unpacker(read_data)

        end_time: float = time.time()
        elapsed_time: float = end_time - start_time
        # Debug print
        print(
            f"\nTime taken to read {batch_size} files of length {len(long_message)}: {elapsed_time:.4f} seconds"
        )

        # Assert should be correct if all other tests passed
        assert (
            len(unpacked_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(unpacked_data)}"

        # Cleanup
        file_reader.clear_all()
        file_writer.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"

        class TestFileReaderAsyncStress:
            """
            Test stress performance of FileReader and FileWriter asynchronously.

            Tests:
            -------
            - **test_file_reader_stress_async:**
                - Stress test for asynchronous file reading and writing operations.
            - **test_file_reader_cm_stress_async:**
                - Stress test for asynchronous file reading and writing operations using context manager.
            - **test_file_reader_generator_stress_async:**
                - Stress test for asynchronous file reading and writing operations using generator.
            - **test_file_reader_cm_generator_stress_async:**
                - Stress test for asynchronous file reading and writing operations using generator with context manager.
            """

            @pytest.mark.asyncio
            @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
            async def test_file_reader_stress_async(
                self,
                file_reader: FileReader,
                file_writer: FileWriter,
                tmp_path,
                batch_size: int,
            ):
                """
                Stress test for asynchronous file reading and writing operations.
                """
                long_message: str = (
                    ST_MESSAGE * 1000
                )  # Create a long message for stress testing

                # Create a FileHandler instance
                temp_files = temporary_file_handler(batch_size, tmp_path)

                # Write some messages
                write_files(file_writer, long_message, temp_files)

                # Assert that message was written correctly
                for file_path in file_writer:
                    assert file_path.exists()
                    with open(file_path, "r") as f:
                        read = f.read()
                        assert (
                            len(read) > 0
                        ), "Log file should not be empty after writing logs"
                        assert any(
                            long_message in line for line in read.splitlines()
                        ), "Long messages should be present in the file"

                # Set File Writer paths
                file_reader.file_paths = temp_files

                # Read the data back asynchronously
                read_data: Dict[Path, str | Exception] = await file_reader.async_read()

                # Assert should be correct if all other tests passed
                assert (
                    len(read_data) == batch_size
                ), f"Expected {batch_size} paths, got {len(read_data)}"

                # Cleanup
                file_reader.clear_all()
                file_writer.clear_all()

                # Assert that the file paths are cleared
                assert (
                    len(file_reader.file_paths) == 0
                ), "File paths should be cleared after operations"
                assert (
                    len(file_writer.file_paths) == 0
                ), "File paths should be cleared after operations"

            @pytest.mark.asyncio
            @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
            async def test_file_reader_cm_stress_async(
                self,
                file_reader: FileReader,
                file_writer: FileWriter,
                tmp_path,
                batch_size: int,
            ):
                """
                Stress test for asynchronous file reading and writing operations using context manager.
                """
                long_message: str = (
                    ST_MESSAGE * 1000
                )  # Create a long message for stress testing

                # Create a FileHandler instance
                temp_files = temporary_file_handler(batch_size, tmp_path)

                # Write some messages
                write_files(file_writer, long_message, temp_files)

                # Assert that message was written correctly
                for file_path in file_writer:
                    assert file_path.exists()
                    with open(file_path, "r") as f:
                        read = f.read()
                        assert (
                            len(read) > 0
                        ), "Log file should not be empty after writing logs"
                        assert any(
                            long_message in line for line in read.splitlines()
                        ), "Long messages should be present in the file"

                # Set File Writer paths
                file_reader.file_paths = temp_files

                # Read the data back asynchronously using context manager
                async with file_reader as fr:
                    read_data: Dict[Path, str | Exception] = await fr.async_read()

                # Assert should be correct if all other tests passed
                assert (
                    len(read_data) == batch_size
                ), f"Expected {batch_size} paths, got {len(read_data)}"

                # Cleanup
                file_reader.clear_all()
                file_writer.clear_all()

                # Assert that the file paths are cleared
                assert (
                    len(file_reader.file_paths) == 0
                ), "File paths should be cleared after operations"
                assert (
                    len(file_writer.file_paths) == 0
                ), "File paths should be cleared after operations"

            @pytest.mark.asyncio
            @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
            async def test_file_reader_generator_stress_async(
                self,
                file_reader: FileReader,
                file_writer: FileWriter,
                tmp_path,
                batch_size: int,
            ):
                """
                Stress test for asynchronous file reading and writing operations using generator.
                """
                long_message: str = (
                    ST_MESSAGE * 1000
                )  # Create a long message for stress testing

                # Create a FileHandler instance
                temp_files = temporary_file_handler(batch_size, tmp_path)

                # Write some messages
                write_files(file_writer, long_message, temp_files)

                # Assert that message was written correctly
                for file_path in file_writer:
                    assert file_path.exists()
                    with open(file_path, "r") as f:
                        read = f.read()
                        assert (
                            len(read) > 0
                        ), "Log file should not be empty after writing logs"
                        assert any(
                            long_message in line for line in read.splitlines()
                        ), "Long messages should be present in the file"

                # Set File Writer paths
                file_reader.file_paths = temp_files

                # Read the data back asynchronously using generator
                read_data: Dict[Path, Generator[str, None, None] | Exception] = (
                    await file_reader.async_read_generator()
                )
                unpacked_data: Dict[Path, str | Exception] = file_reader.unpacker(
                    read_data
                )

                # Assert should be correct if all other tests passed
                assert (
                    len(unpacked_data) == batch_size
                ), f"Expected {batch_size} paths, got {len(unpacked_data)}"

                # Cleanup
                file_reader.clear_all()
                file_writer.clear_all()

                # Assert that the file paths are cleared
                assert (
                    len(file_reader.file_paths) == 0
                ), "File paths should be cleared after operations"
                assert (
                    len(file_writer.file_paths) == 0
                ), "File paths should be cleared after operations"

            @pytest.mark.asyncio
            @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
            async def test_file_reader_cm_generator_stress_async(
                self,
                file_reader: FileReader,
                file_writer: FileWriter,
                tmp_path,
                batch_size: int,
            ):
                """
                Stress test for asynchronous file reading and writing operations using generator with context manager.
                """
                long_message: str = (
                    ST_MESSAGE * 1000
                )  # Create a long message for stress testing

                # Create a FileHandler instance
                temp_files = temporary_file_handler(batch_size, tmp_path)

                # Write some messages
                write_files(file_writer, long_message, temp_files)

                # Assert that message was written correctly
                for file_path in file_writer:
                    assert file_path.exists()
                    with open(file_path, "r") as f:
                        read = f.read()
                        assert (
                            len(read) > 0
                        ), "Log file should not be empty after writing logs"
                        assert any(
                            long_message in line for line in read.splitlines()
                        ), "Long messages should be present in the file"

                # Set File Writer paths
                file_reader.file_paths = temp_files

                # Read the data back asynchronously using context manager and generator
                async with file_reader as fr:
                    read_data: Dict[Path, Generator[str, None, None] | Exception] = (
                        await fr.async_read_generator()
                    )
                    unpacked_data: Dict[Path, str | Exception] = file_reader.unpacker(
                        read_data
                    )

                # Assert should be correct if all other tests passed
                assert (
                    len(unpacked_data) == batch_size
                ), f"Expected {batch_size} paths, got {len(unpacked_data)}"

                # Cleanup
                file_reader.clear_all()
                file_writer.clear_all()

                # Assert that the file paths are cleared
                assert (
                    len(file_reader.file_paths) == 0
                ), "File paths should be cleared after operations"
                assert (
                    len(file_writer.file_paths) == 0
                ), "File paths should be cleared after operations"


class TestFileReaderAsyncStress:
    """
    Test stress performance of FileReader and FileWriter asynchronously.

    Tests:
    -------
    - **test_file_reader_stress_async:**
        - Stress test for asynchronous file reading and writing operations.
    - **test_file_reader_cm_stress_async:**
        - Stress test for asynchronous file reading and writing operations using context manager.
    - **test_file_reader_generator_stress_async:**
        - Stress test for asynchronous file reading and writing operations using generator.
    - **test_file_reader_cm_generator_stress_async:**
        - Stress test for asynchronous file reading and writing operations using generator with context manager.
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_file_reader_stress_async(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
        """
        Stress test for asynchronous file reading and writing operations.
        """
        long_message: str = ST_MESSAGE * 100  # Create a long message for stress testing

        # Create a FileHandler instance
        temp_files = temporary_file_handler(batch_size, tmp_path)

        # Write some messages
        write_files(file_writer, long_message, temp_files)

        # Assert that message was written correctly
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                read = f.read()
                assert (
                    len(read) > 0
                ), "Message file should not be empty after writing messages"
                assert any(
                    long_message in line for line in read.splitlines()
                ), "Long messages should be present in the file"

        # Set File Writer paths
        file_reader.file_paths = temp_files

        start_time: float = time.time()

        # Read the data back asynchronously
        read_data: Dict[Path, str | Exception] = await file_reader.async_read()

        # Assert should be correct if all other tests passed
        assert (
            len(read_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(read_data)}"

        end_time: float = time.time()
        elapsed_time: float = end_time - start_time
        # Debug print
        print(
            f"\nTime taken to read {batch_size} files of length {len(long_message)}: {elapsed_time:.4f} seconds"
        )

        # Cleanup
        file_reader.clear_all()
        file_writer.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_file_reader_cm_stress_async(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
        """
        Stress test for asynchronous file reading and writing operations using context manager.
        """
        long_message: str = ST_MESSAGE * 100  # Create a long message for stress testing

        # Create a FileHandler instance
        temp_files = temporary_file_handler(batch_size, tmp_path)

        # Write some messages
        write_files(file_writer, long_message, temp_files)

        # Assert that message was written correctly
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                read = f.read()
                assert (
                    len(read) > 0
                ), "Message file should not be empty after writing messages"
                assert any(
                    long_message in line for line in read.splitlines()
                ), "Long messages should be present in the file"

        # Set File Writer paths
        file_reader.file_paths = temp_files

        start_time: float = time.time()

        # Read the data back asynchronously using context manager
        async with file_reader as fr:
            read_data: Dict[Path, str | Exception] = await fr.async_read()

        end_time: float = time.time()
        elapsed_time: float = end_time - start_time
        # Debug print
        print(
            f"\nTime taken to read {batch_size} files of length {len(long_message)}: {elapsed_time:.4f} seconds"
        )

        # Assert should be correct if all other tests passed
        assert (
            len(read_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(read_data)}"

        # Cleanup
        file_reader.clear_all()
        file_writer.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_file_reader_generator_stress_async(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
        """
        Stress test for asynchronous file reading and writing operations using generator.
        """
        long_message: str = ST_MESSAGE * 100  # Create a long message for stress testing

        # Create a FileHandler instance
        temp_files = temporary_file_handler(batch_size, tmp_path)

        # Write some messages
        write_files(file_writer, long_message, temp_files)

        # Assert that message was written correctly
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                read = f.read()
                assert (
                    len(read) > 0
                ), "Message file should not be empty after writing messages"
                assert any(
                    long_message in line for line in read.splitlines()
                ), "Long messages should be present in the file"

        # Set File Writer paths
        file_reader.file_paths = temp_files

        start_time: float = time.time()

        # Read the data back asynchronously using generator
        read_data: Dict[Path, Generator[str, None, None] | Exception] = (
            await file_reader.async_read_generator()
        )
        unpacked_data: Dict[Path, str | Exception] = file_reader.unpacker(read_data)

        end_time: float = time.time()
        elapsed_time: float = end_time - start_time
        # Debug print
        print(
            f"\nTime taken to read {batch_size} files of length {len(long_message)}: {elapsed_time:.4f} seconds"
        )

        # Assert should be correct if all other tests passed
        assert (
            len(unpacked_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(unpacked_data)}"

        # Cleanup
        file_reader.clear_all()
        file_writer.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("batch_size", BATCH_TEST_CASES)
    async def test_file_reader_cm_generator_stress_async(
        self,
        file_reader: FileReader,
        file_writer: FileWriter,
        tmp_path,
        batch_size: int,
    ):
        """
        Stress test for asynchronous file reading and writing operations using generator with context manager.
        """
        long_message: str = ST_MESSAGE * 100  # Create a long message for stress testing

        # Create a FileHandler instance
        temp_files = temporary_file_handler(batch_size, tmp_path)

        # Write some messages
        write_files(file_writer, long_message, temp_files)

        # Assert that message was written correctly
        for file_path in file_writer:
            assert file_path.exists()
            with open(file_path, "r") as f:
                read = f.read()
                assert (
                    len(read) > 0
                ), "Message file should not be empty after writing messages"
                assert any(
                    long_message in line for line in read.splitlines()
                ), "Long messages should be present in the file"

        # Set File Writer paths
        file_reader.file_paths = temp_files

        start_time: float = time.time()

        # Read the data back asynchronously using context manager and generator
        async with file_reader as fr:
            read_data: Dict[Path, Generator[str, None, None] | Exception] = (
                await fr.async_read_generator()
            )
            unpacked_data: Dict[Path, str | Exception] = file_reader.unpacker(read_data)

        end_time: float = time.time()
        elapsed_time: float = end_time - start_time
        # Debug print
        print(
            f"\nTime taken to read {batch_size} files of length {len(long_message)}: {elapsed_time:.4f} seconds"
        )

        # Assert should be correct if all other tests passed
        assert (
            len(unpacked_data) == batch_size
        ), f"Expected {batch_size} paths, got {len(unpacked_data)}"

        # Cleanup
        file_reader.clear_all()
        file_writer.clear_all()

        # Assert that the file paths are cleared
        assert (
            len(file_reader.file_paths) == 0
        ), "File paths should be cleared after operations"
        assert (
            len(file_writer.file_paths) == 0
        ), "File paths should be cleared after operations"


# ----------------------------------------------------------------------------------------------
# End of File
