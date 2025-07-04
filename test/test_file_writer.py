# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
from pathlib import Path
from typing import Dict, Generator, List, Final, Any
import threading
import json
import yaml
import asyncio

# Third-party imports
import pytest

# Local imports
from jr_file_handler.classes.file_writer import FileWriter
from jr_file_handler.utils.module_enums import LogWriteMode

# Exceptions
from jr_file_handler.exceptions.exceptions_file_writer import (
    FileWriterConstructionError,
    FileWriterSettingsError,
    FileWriterWriteError,
    FileWriterAsyncWriteError,
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


def temporary_file_writer(num: int, tmp_path) -> List[Path]:
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


class TestFileWriterEdge:
    """
    Test edge cases for FileWriter.
    This class contains tests for the FileWriter class to ensure it handles edge cases correctly.
    It includes tests for constructor parameters, setters, and methods.

    Tests:
    -------
    - Edge cases for constructor parameters
    - Edge cases for setters
    - Edge cases for the write method
    - Edge cases for the async_write method
    - Edge cases for the context manager functionality
    """

    @pytest.mark.parametrize("edge_value", EDGE_PATHS)
    def test_file_writer_edge_constructor_paths(self, edge_value):
        """Test edge cases for FileWriter constructor."""
        # Test with invalid file_paths
        with pytest.raises(FileWriterConstructionError):
            FileWriter(
                file_paths=edge_value,
                retry_limit=0,
                retry_delay=0.0,
                backoff_factor=0.0,
            )

    @pytest.mark.parametrize("edge_value", EDGE_INT)
    def test_file_writer_edge_constructor_int(self, tmp_path, edge_value):
        """Test edge cases for FileWriter constructor."""
        temp_files = [tmp_path / "test_1.log", tmp_path / "test_2.log"]
        # Test with invalid retry_limit
        with pytest.raises(FileWriterConstructionError):
            FileWriter(temp_files, retry_limit=edge_value)

        # Test with invalid max_file_size
        with pytest.raises(FileWriterConstructionError):
            FileWriter(temp_files, max_file_size=edge_value)

        # Test with invalid max_rotation
        with pytest.raises(FileWriterConstructionError):
            FileWriter(temp_files, max_rotation=edge_value)

    @pytest.mark.parametrize("edge_value", EDGE_FLOAT)
    def test_file_writer_edge_constructor_float(self, tmp_path, edge_value):
        """Test edge cases for FileWriter constructor."""
        temp_files = [tmp_path / "test_1.log", tmp_path / "test_2.log"]

        # Test with invalid retry_delay
        with pytest.raises(FileWriterConstructionError):
            FileWriter(temp_files, retry_delay=edge_value)

        # Test with invalid backoff_factor
        with pytest.raises(FileWriterConstructionError):
            FileWriter(temp_files, backoff_factor=edge_value)

    def test_file_writer_edge_setters(self, file_writer: FileWriter):
        """Test edge cases for FileWriter."""

        # Test with invalid retry_limit
        with pytest.raises(FileWriterSettingsError):
            file_writer.retry_limit = -1

        # Test with invalid retry_delay
        with pytest.raises(FileWriterSettingsError):
            file_writer.retry_delay = -1.0

        # Test with invalid backoff_factor
        with pytest.raises(FileWriterSettingsError):
            file_writer.backoff_factor = -1.0

        # Test with invalid max_file_size
        with pytest.raises(FileWriterSettingsError):
            file_writer.max_file_size = -1

        # Test with invalid max_rotation
        with pytest.raises(FileWriterSettingsError):
            file_writer.max_rotation = -1

    @pytest.mark.parametrize("edge_value", EDGE_LOG)
    def test_file_writer_edge_message(self, file_writer: FileWriter, edge_value):
        """Test edge cases for FileWriter log method."""

        # Test with invalid log message type
        with pytest.raises(FileWriterWriteError):
            file_writer.write(edge_value)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("edge_value", EDGE_LOG)
    async def test_file_writer_edge_async_message(
        self, file_writer: FileWriter, edge_value
    ):
        """Test edge cases for FileWriter async log method."""
        # Test with invalid log message type
        with pytest.raises(FileWriterAsyncWriteError):
            await file_writer.async_write(edge_value)


# ----------------------------------------------------------------------------------------------
# Overall Tests
# ----------------------------------------------------------------------------------------------


class TestFileWriterOverall:
    """
    Test overall functionality of FileWriter.
    This class contains tests for the FileWriter class to ensure it works as expected.
    It includes tests for initialization, setters, methods, and context manager functionality.

    Tests:
    -------
    - Initialization of FileWriter
    - Setters for file_paths, write_mode, retry_limit, retry_delay, backoff_factor
    - Write method
    - Async write method
    - Context manager functionality
    """

    def test_file_writer_init(self, file_writer: FileWriter):
        """Test the initialization of FileWriter."""
        assert len(file_writer.file_paths) == 2
        assert file_writer.write_mode == "a"
        assert file_writer.retry_limit == 0
        assert file_writer.retry_delay == pytest.approx(0.0)
        assert file_writer.backoff_factor == pytest.approx(0.0)
        assert file_writer.max_file_size == 10 * 1024 * 1024  # 10 MB
        assert file_writer.max_rotation == 5

    def test_file_writer_setters(self, file_writer: FileWriter):
        """Test the setters of FileWriter."""
        # Test setting file_paths
        new_paths = [Path("new_test_1.log"), Path("new_test_2.log")]
        file_writer.file_paths = new_paths

        assert file_writer.file_paths == new_paths

        # Test setting write_mode
        file_writer.write_mode = LogWriteMode.WRITE_READ
        assert file_writer.write_mode == LogWriteMode.WRITE_READ

        # Test setting retry_limit
        file_writer.retry_limit = 5
        assert file_writer.retry_limit == 5

        # Test setting retry_delay
        file_writer.retry_delay = 1.0
        assert file_writer.retry_delay == pytest.approx(1.0)

        # Test setting backoff_factor
        file_writer.backoff_factor = 0.5
        assert file_writer.backoff_factor == pytest.approx(0.5)

    def test_file_writer_write(self, file_writer: FileWriter, tmp_path):
        """Test the log method of FileWriter."""
        log_message = "Test log message for FileWriter"

        # Set up temporary files for logging
        temp_file_1 = tmp_path / "test_1.log"
        temp_file_2 = tmp_path / "test_2.log"
        file_writer.file_paths = [temp_file_1, temp_file_2]

        # Call the log method
        file_writer.write(log_message)

        # Force the file handler to flush the buffer
        file_writer.buffer_force_flush()

        # Check if the log message is written to the file
        for file_path in file_writer.file_paths:
            with open(file_path, "r") as f:
                content = f.read()
                assert log_message in content

        file_writer.clear_sync_pool()

    def test_file_writer_context_manager(self, file_writer: FileWriter, tmp_path):
        """Test the context manager functionality of FileWriter."""
        log_message = "Context manager log message for FileWriter"
        temp_file = tmp_path / "context_test.log"

        with file_writer as handler:
            handler.file_paths = [temp_file]
            handler.write(log_message)

        # Check if the log message is written to the file
        with open(temp_file, "r") as f:
            content = f.read()
            assert log_message in content

        # After exiting the context, file_paths should be cleared
        assert len(handler.file_paths) == 0

    @pytest.mark.asyncio
    async def test_file_writer_async_write(self, file_writer: FileWriter, tmp_path):
        """Test the async log method of FileWriter."""
        log_message = "Async log message for FileWriter"

        # Set up temporary files for logging
        temp_file_1 = tmp_path / "test_1.log"
        temp_file_2 = tmp_path / "test_2.log"
        file_writer.file_paths = [temp_file_1, temp_file_2]

        # Call the async log method
        await file_writer.async_write(log_message)

        # Force the file handler to flush the buffer
        file_writer.buffer_force_flush()

        # Check if the log message is written to the file
        for file_path in file_writer.file_paths:
            with open(file_path, "r") as f:
                content = f.read()
                assert log_message in content

        file_writer.clear_sync_pool()

    @pytest.mark.asyncio
    async def test_file_writer_async_context_manager(
        self, file_writer: FileWriter, tmp_path
    ):
        """Test the async context manager functionality of FileWriter."""
        log_message = "Async context manager log message for FileWriter"
        temp_file = tmp_path / "async_context_test.log"

        async with file_writer as handler:
            handler.file_paths = [temp_file]
            await handler.async_write(log_message)

        # Check if the log message is written to the file
        with open(temp_file, "r") as f:
            content = f.read()
            assert log_message in content

        # After exiting the context, file_paths should be cleared
        assert len(handler.file_paths) == 0


# ----------------------------------------------------------------------------------------------
# Functionality Tests
# ----------------------------------------------------------------------------------------------


class TestFileWriterFunctionality:
    """
    Test the functionality of FileWriter.
    This class contains tests for the FileWriter class to ensure it works as expected.
    It includes tests for file rotation, thread safety, and memory cleanup.

    Tests:
    -------
    - File rotation when max size is exceeded
    - Thread safety with concurrent writes
    - Memory cleanup after usage
    """

    def test_file_rotation(self, file_writer: FileWriter, tmp_path):
        """Test file rotation when max size is exceeded."""

        # Set Logger
        file_writer.logger.setLevel("DEBUG")

        # Create a temporary log file
        log_file = tmp_path / "small.log"
        file_writer.file_paths = [log_file]
        file_writer.max_file_size = 5  # Very small for testing
        file_writer.max_rotation = 3  # Limit to 2 rotations

        # Write enough to trigger rotation
        for i in range(700):
            file_writer.write(f"Long message {i} " * 10)

        # Force the file handler to flush the buffer
        file_writer.buffer_force_flush()

        try:
            # Check if rotation files exist in the tmp_path directory
            rotation_file_1 = tmp_path / "small_1.log"
            rotation_file_2 = tmp_path / "small_2.log"
            assert (
                rotation_file_1.exists() or rotation_file_2.exists()
            ), "Rotation files should exist"

        finally:
            # Cleanup rotation files
            for i in range(3):
                rotation_file = tmp_path / f"small_{i}.log"
                if rotation_file.exists():
                    rotation_file.unlink()

    def test_thread_safety(self, file_writer: FileWriter, tmp_path):
        """Test thread safety with concurrent writes."""
        temp_file = tmp_path / "thread_test.log"
        file_writer.file_paths = [temp_file]

        def write_logs():
            for i in range(100):
                file_writer.write(f"Thread message {i}")

        # Create multiple threads
        threads = [threading.Thread(target=write_logs) for _ in range(5)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Force the file handler to flush the buffer
        file_writer.buffer_force_flush()

        # Clear the file writer
        file_writer.clear_all()

        # Verify all messages were written
        with open(temp_file, "r") as f:
            content = f.read()
            assert content.count("Thread message") == 500
            assert "Thread message" in content, "First thread message should be present"

    def test_thread_with_async_safety(self, file_writer: FileWriter, tmp_path):
        """Test thread safety with concurrent writes."""
        temp_file = tmp_path / "thread_test.log"
        file_writer.file_paths = [temp_file]

        async def write_logs():
            for i in range(100):
                await file_writer.async_write(f"Thread message {i}")

        # Create multiple threads
        threads = [threading.Thread(target=asyncio.run, args=(write_logs(),)) for _ in range(5)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Force the file handler to flush the buffer
        file_writer.buffer_force_flush()

        # Clear the file writer
        file_writer.clear_all()

        # Verify all messages were written
        with open(temp_file, "r") as f:
            content = f.read()
            assert content.count("Thread message") == 500
            assert "Thread message" in content, "First thread message should be present"

    @pytest.mark.asyncio
    async def test_async_thread_safety(self, file_writer: FileWriter, tmp_path):
        """Test async thread safety with concurrent writes."""
        temp_file = tmp_path / "async_thread_test.log"
        temp_file.touch()  # Ensure the file is created
        file_writer.file_paths = [temp_file]
        
        file_writer.max_buffer_size = 0  # Disable buffering for testing

        async def write_logs():
            for i in range(100):
                await file_writer.async_write(f"Async thread message {i}")

        # Create multiple threads
        threads = [write_logs() for _ in range(5)]
        
        # Use asyncio to run all threads concurrently
        await asyncio.gather(*threads)

        # Clear the file writer
        file_writer.clear_all()

        # Verify all messages were written
        with open(temp_file, "r") as f:
            content = f.read()
            assert content.count("Async thread message") == 500
            assert "Async thread message" in content, "First async thread message should be present"


    def test_memory_cleanup(self, tmp_path):
        """Test that file handles are properly cleaned up."""
        import gc
        import weakref

        temp_file = tmp_path / "cleanup_test.log"

        handler: FileWriter = FileWriter(file_paths=[temp_file])

        # Create weak reference to track cleanup
        weak_ref = weakref.ref(handler)

        # Write some logs
        handler.write("test message")

        # Force cleanup
        handler.buffer_force_flush()
        handler.clear_sync_pool()
        handler.force_shutdown()

        # Delete reference to handler to allow garbage collection
        del handler

        # Force garbage collection
        gc.collect()

        # Verify cleanup
        assert (
            weak_ref() is None
        ), "FileWriter should be cleaned up and weak reference should be None"


# ----------------------------------------------------------------------------------------------
# Magic Method Tests
# ----------------------------------------------------------------------------------------------


class TestFileWriterMagicMethods:
    """
    Test the magic methods of FileWriter.
    This class contains tests for the magic methods of the FileWriter class to ensure they work as expected.
    It includes tests for __str__, __repr__, __len__, __eq__, __iter__, __contains__, and __del__.

    Tests:
    -------
    - String representation (__str__)
    - Detailed representation (__repr__)
    - Length of file paths (__len__)
    - Equality comparison (__eq__)
    - Iteration over file paths (__iter__)
    - Membership check (__contains__)
    - Cleanup on deletion (__del__)
    """

    def test_file_writer_magic_methods(self, file_writer: FileWriter, tmp_path):
        """Test the magic methods of FileWriter."""

        # Test __str__
        str_repr = str(file_writer)
        assert (
            "FileWriter" in str_repr
        ), "__str__ method should return a string representation of FileWriter"

        # Test __repr__
        repr_repr = repr(file_writer)
        assert (
            "FileWriter" in repr_repr
        ), "__repr__ method should return a detailed representation of FileWriter"

        # Test __len__
        assert (
            len(file_writer) == 2
        ), "__len__ method should return the number of file paths (2 initially)"

        # Test __eq__
        temp_files = [tmp_path / "test_1.log", tmp_path / "test_2.log"]
        handler = FileWriter(
            file_paths=temp_files,  # Use temp files
            retry_limit=0,
            retry_delay=0.0,
            backoff_factor=0.0,
        )
        assert (
            file_writer == handler
        ), "__eq__ method should compare file paths and other attributes"

        # Test __iter__
        for file_path in file_writer:
            assert isinstance(
                file_path, Path
            ), "__iter__ method should yield Path objects"

        # Test __contains__
        assert (
            file_writer.file_paths[0] in file_writer
        ), "__contains__ method should check if a file path is in the handler"

        # Test __del__
        del file_writer  # This should not raise any exceptions
        del handler  # This should not raise any exceptions either


# ----------------------------------------------------------------------------------------------
# ClassMethods Tests
# ----------------------------------------------------------------------------------------------


class TestFileWriterClassMethods:
    """
    Test class methods of FileWriter.

    Tests:
    -------
    - **test_from_dict:**
        - Test creating FileWriter from a dictionary.
    - **test_from_json:**
        - Test creating FileWriter from a JSON string.
    - **test_from_yaml:**
        - Test creating FileWriter from a YAML string.
    """

    def test_from_dict(self, tmp_path):
        tmp_list: List[Path] = temporary_file_writer(2, tmp_path)

        config_dict: Dict[str, Any] = {
            "file_paths": [str(path) for path in tmp_list],
            "write_mode": "a",
            "max_file_size": 10 * 1024 * 1024,  # 10 MB
            "max_rotation": 5,
            "max_buffer_size": 0,
            "retry_limit": 10,
            "retry_delay": 0.5,
            "backoff_factor": 0.1,
        }

        my_file_reader: FileWriter = FileWriter.from_dict(config_dict)

        assert len(my_file_reader) == 2
        assert my_file_reader.file_paths == tmp_list
        assert my_file_reader.retry_limit == 10
        assert my_file_reader.retry_delay == pytest.approx(0.5)
        assert my_file_reader.backoff_factor == pytest.approx(0.1)
        assert my_file_reader.write_mode == "a"
        assert my_file_reader.max_file_size == 10 * 1024 * 1024
        assert my_file_reader.max_rotation == 5
        assert my_file_reader.max_buffer_size == 0

    def test_from_json(self, tmp_path):
        tmp_list: List[Path] = temporary_file_writer(2, tmp_path)

        config_dict: Dict[str, Any] = {
            "file_paths": [str(path) for path in tmp_list],
            "write_mode": "a",
            "max_file_size": 10 * 1024 * 1024,  # 10 MB
            "max_rotation": 5,
            "max_buffer_size": 0,
            "retry_limit": 10,
            "retry_delay": 0.5,
            "backoff_factor": 0.1,
            
        }

        json_str: str = json.dumps(config_dict)

        my_file_reader: FileWriter = FileWriter.from_json(json_str)

        assert len(my_file_reader) == 2
        assert my_file_reader.file_paths == tmp_list
        assert my_file_reader.retry_limit == 10
        assert my_file_reader.retry_delay == pytest.approx(0.5)
        assert my_file_reader.backoff_factor == pytest.approx(0.1)
        assert my_file_reader.write_mode == "a"
        assert my_file_reader.max_file_size == 10 * 1024 * 1024
        assert my_file_reader.max_rotation == 5
        assert my_file_reader.max_buffer_size == 0
        
    def test_from_yaml(self, tmp_path):
        tmp_list: List[Path] = temporary_file_writer(2, tmp_path)

        config_dict: Dict[str, Any] = {
            "file_paths": [str(path) for path in tmp_list],
            "write_mode": "a",
            "max_file_size": 10 * 1024 * 1024,  # 10 MB
            "max_rotation": 5,
            "max_buffer_size": 0,
            "retry_limit": 10,
            "retry_delay": 0.5,
            "backoff_factor": 0.1,
            
        }

        yaml_str: str = yaml.dump(config_dict)

        my_file_reader: FileWriter = FileWriter.from_yaml(yaml_str)

        assert len(my_file_reader) == 2
        assert my_file_reader.file_paths == tmp_list
        assert my_file_reader.retry_limit == 10
        assert my_file_reader.retry_delay == pytest.approx(0.5)
        assert my_file_reader.backoff_factor == pytest.approx(0.1)


# ----------------------------------------------------------------------------------------------
# Config Tests
# ----------------------------------------------------------------------------------------------


class TestFileWriterConfig:
    """
    Test configuration methods of FileWriter.

    Tests:
    -------
    - **test_config_from_dict:**
        - Test configuration of FileWriter using a dictionary.
    - **test_config_from_json:**
        - Test configuration of FileWriter using a JSON file.
    - **test_config_from_yaml:**
        - Test configuration of FileWriter using a YAML file.
    """

    def test_config_from_dict(self, file_writer: FileWriter, tmp_path):
        """Test configuration of FileReader using a dictionary."""
        tmp_list = [tmp_path / "test_1.log", tmp_path / "test_2.log"]
        config_dict: Dict[str, Any] = {
            "file_paths": [str(path) for path in tmp_list],
            "write_mode": "a",
            "max_file_size": 10 * 1024 * 1024,  # 10 MB
            "max_rotation": 5,
            "max_buffer_size": 0,
            "retry_limit": 3,
            "retry_delay": 0.5,
            "backoff_factor": 0.1,
            
        }

        file_writer.config_from_dict(config_dict)

        assert file_writer.file_paths == tmp_list
        assert file_writer.retry_limit == 3
        assert file_writer.retry_delay == pytest.approx(0.5)
        assert file_writer.backoff_factor == pytest.approx(0.1)
        assert file_writer.write_mode == "a"
        assert file_writer.max_file_size == 10 * 1024 * 1024
        assert file_writer.max_rotation == 5
        assert file_writer.max_buffer_size == 0

    def test_config_from_json(self, file_writer: FileWriter, tmp_path):
        """Test configuration of FileReader using a JSON file."""
        tmp_list = [tmp_path / "test_1.log", tmp_path / "test_2.log"]
        
        config_dict: Dict[str, Any] = {
            "file_paths": [str(path) for path in tmp_list],
            "write_mode": "a",
            "max_file_size": 10 * 1024 * 1024,  # 10 MB
            "max_rotation": 5,
            "max_buffer_size": 0,
            "retry_limit": 3,
            "retry_delay": 0.5,
            "backoff_factor": 0.1,
        }


        json_str: str = json.dumps(config_dict)

        file_writer.config_from_json(json_str)

        assert file_writer.file_paths == tmp_list
        assert file_writer.retry_limit == 3
        assert file_writer.retry_delay == pytest.approx(0.5)
        assert file_writer.backoff_factor == pytest.approx(0.1)
        assert file_writer.write_mode == "a"
        assert file_writer.max_file_size == 10 * 1024 * 1024
        assert file_writer.max_rotation == 5
        assert file_writer.max_buffer_size == 0

    def test_config_from_yaml(self, file_writer: FileWriter, tmp_path):
        """Test configuration of FileReader using a YAML file."""
        tmp_list = [tmp_path / "test_1.log", tmp_path / "test_2.log"]
        config_dict: Dict[str, Any] = {
            "file_paths": [str(path) for path in tmp_list],
            "write_mode": "a",
            "max_file_size": 10 * 1024 * 1024,  # 10 MB
            "max_rotation": 5,
            "max_buffer_size": 0,
            "retry_limit": 3,
            "retry_delay": 0.5,
            "backoff_factor": 0.1,
        }

        yaml_file: str = yaml.dump(config_dict)

        file_writer.config_from_yaml(yaml_file)

        assert file_writer.file_paths == tmp_list
        assert file_writer.retry_limit == 3
        assert file_writer.retry_delay == pytest.approx(0.5)
        assert file_writer.backoff_factor == pytest.approx(0.1)
        assert file_writer.write_mode == "a"
        assert file_writer.max_file_size == 10 * 1024 * 1024
        assert file_writer.max_rotation == 5
        assert file_writer.max_buffer_size == 0


# ----------------------------------------------------------------------------------------------
# End of File
