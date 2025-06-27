# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
from io import TextIOWrapper, StringIO

import logging
import os
import asyncio
import time
import json
import yaml

from typing import Iterator, List, Union, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from functools import partial

# Local imports
from jr_py_writer.utils.module_enums import LogWriteMode

# Utilities
from jr_py_writer.utils.utilities import batcher, batcher_with_gcmanager

# Exceptions
from jr_py_writer.exceptions.exceptions_file_handler import (
    FileHandlerConstructionError,
    FileHandlerSettingsError,
    FileHandlerSyncPoolInitError,
    FileHandlerSyncPoolCleanupError,
    FileHandlerWriteError,
    FileHandlerAsyncWriteError,
    FileHandleRotateError,
    FileHandlerConfigError,
    FileHandlerBufferError,
    FileHandlerFlushError,
    FileHandlerShutdownError,
    FileHandlerResumeError,
    FileHandlerResetError,
    FileHandlerReadError,
    FileHandlerAsyncReadError
)


# ----------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------


class FileHandler:
    """
    A handler that writes log messages to one or more files.
    FileHandler manages writing log messages to specified file paths with
    configurable write modes and retry mechanisms for handling file operation failures.

    The class also supports reading from files.

    The handler supports both synchronous and asynchronous writing and reading operations,
    automatically creating parent directories for log files if they don't exist.
    It also provides thread-safe writing and reading with retry logic to handle temporary
    file system access issues.

    Attributes:
        file_paths (List[Path]): List of file paths where log messages will be written.
        write_mode (LogWriteMode): Mode for writing to files (append or overwrite).
        retry_limit (int): Number of times to retry failed file operations.
        retry_delay (float): Delay in seconds between retry attempts.
        backoff_factor (float): Factor to increase the retry delay exponentially.
        max_file_size (int): Maximum size of log files in bytes before rotation.
        max_rotation (int): Maximum number of rotated log files to keep.
        max_buffer_size (int): Maximum size of the buffer for log messages.
        use_write_flush (bool): Whether to flush the file after each write operation.
        logger (logging.Logger): Logger instance for logging errors and information.

    max_buffer_size
    -------------
    -   The maximum size of the buffer for writing log messages in bytes.
    -   If used, the buffer will hold log messages until it reaches the maximum size.
        -   When the buffer size exceeds the maximum, it will automatically flush the buffer
        -   If size is not reached, the buffer will be flushed when the context manager exits or when `buffer_force_flush()` is called.
        -   **ALWAYS FLUSH THE BUFFER IF NOT USING CONTEXT MANAGER, OTHERWISE DATA MAY BE LOST!**

    use_write_flush
    -------------
    -   If set to True, the handler will flush the file after each write operation.
    -   If set to False, the handler will not flush the file after each write operation.
        -   Will improve performance but may lead to data loss in case of a crash.
        -   Must manually flush using `writer_force_flush()` method, or automatically with context manager.

    Methods:
    --------
        - Log Writing:
            #### log(message: str) - None:
                Write a log message to the specified file paths synchronously.
            #### async_log(message: str) - None:
                Asynchronously write a log message to the specified file paths.
            #### buffer_force_flush() - None:
                Force flush the buffer to the file(s) immediately.
            #### writer_force_flush() - None:
                Force flush the file(s) immediately, ensuring all data is written to disk.
        - Log Reading:
            #### read_log() - Dict[Path, str]:
                Read the content of all files in the file paths synchronously.
            #### async_read_log() - Dict[Path, str]:
                Asynchronously read the content of all files in the file paths.
        - Pool Management:
            #### clear_sync_pool() - None:
                Clear the temporary pool for synchronous file operations.
            #### force_shutdown() - None:
                Force shutdown the file handler, closing all files and clearing the pool.
            #### resume() - None:
                Resume the file handler after a forced shutdown, reinitializing the pool.
        - Cleanup:
            #### __del__() - None:
                Cleanup resources when the FileHandler object is destroyed.
            #### clear_sync_pool() - None:
                Clear the temporary pool for synchronous file operations.
            #### clear_all() - None:
                Clear all resources, including file paths and the synchronous pool.
        - Configuration
            #### reset() - None:
                Reset the FileHandler to its initial state, clearing all settings and file paths.
            #### config(**kwargs) - None:
                Configure the FileHandler with various settings like file paths, write mode, retry limits, etc.
            #### config_dict(Dict[str, Any]) - None:
                Configure the FileHandler using a dictionary of settings.
            #### config_json(json_str: str) - None:
                Configure the FileHandler using a JSON string of settings.
            #### config_yaml(yaml_str: str) - None:
                Configure the FileHandler using a YAML string of settings.
        
    Example:
        ```python
        # Create a file handler that writes to multiple log files
        handler = FileHandler(
            file_paths=[Path("app.log"), Path("debug.log")],
            write_mode=LogWriteMode.APPEND,
            retry_limit=3,
            retry_delay=0.5
        # Write log message to all specified files
        handler.log("Application started")

        # Asynchronously write log message
        def async main():
            await handler.async_log("Asynchronous logging started")
        # Run asynchronous
        asyncio.run(main())
        ```

    """

    # --------------
    # Slots

    __slots__ = (
        "__weakref__",
        "_file_paths",
        "_write_mode",
        "_retry_limit",
        "_retry_delay",
        "_backoff_factor",
        "_max_file_size",
        "_max_rotation",
        "_temp_sync_pool",
        "_lock",
        "_threadpool",
        "_logger",
        "_max_buffer_size",
        "_buffer",
        "_use_write_flush",
    )

    # --------------
    # Attributes

    _file_paths: List[Path]
    _write_mode: LogWriteMode
    _retry_limit: int
    _retry_delay: float
    _backoff_factor: float
    _max_file_size: int
    _max_rotation: int
    _temp_sync_pool: Dict[Path, TextIOWrapper]
    _lock: Lock
    _threadpool: ThreadPoolExecutor
    _logger: logging.Logger
    _buffer: StringIO
    _max_buffer_size: int
    _use_write_flush: bool

    # --------------
    # Properties

    @property
    def file_paths(self) -> List[Path]:
        """
        Returns the list of file paths for logging.
        """
        return self._file_paths

    @property
    def write_mode(self) -> LogWriteMode:
        """
        Returns the write mode for file logging.
        """
        return self._write_mode

    @property
    def retry_limit(self) -> int:
        """
        Returns the retry limit for file operations.
        """
        return self._retry_limit

    @property
    def retry_delay(self) -> float:
        """
        Returns the retry delay for file operations.
        """
        return self._retry_delay

    @property
    def backoff_factor(self) -> float:
        """
        Returns the backoff factor for retry delays.
        """
        return self._backoff_factor

    @property
    def max_file_size(self) -> int:
        """
        Returns the maximum file size for log files in bytes.
        Default is set to 10 MB.
        """
        return self._max_file_size

    @property
    def max_rotation(self) -> int:
        """
        Returns the maximum number of rotated log files.
        Default is set to 5.
        """
        return self._max_rotation

    @property
    def logger(self) -> logging.Logger:
        """
        Returns the logger instance associated with the FileHandler.
        """
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(__name__)
        return self._logger

    @property
    def max_buffer_size(self) -> int:
        """
        Returns the maximum size of the buffer for log messages.
        Default is set to 1 MB.
        """
        return self._max_buffer_size

    @property
    def use_write_flush(self) -> bool:
        """
        Returns whether the handler uses flush after writing to the file.
        Default is set to True.
        """
        return self._use_write_flush

    @property
    def get_buffer_size(self) -> int:
        """
        Returns the current size of the buffer for log messages.
        """
        if not hasattr(self, "_buffer"):
            return 0
        return self._buffer.tell() if self._buffer else 0

    # --------------
    # Setters

    @file_paths.setter
    def file_paths(self, paths: List[Path]) -> None:
        """
        Sets the file paths for logging.

        Arguments:
            paths (List[Path]) : A list of file paths.
        """
        try:
            if not isinstance(paths, list):
                raise ValueError(
                    f"File paths must be a list of Path objects, got {type(paths).__name__}"
                )

            if not paths:
                raise ValueError("File paths list cannot be empty")

            for path in paths:
                if not isinstance(path, Path):
                    raise ValueError(f"Invalid file path: {path}")

                if path.exists() and path.is_dir():
                    raise ValueError(
                        f"File path points to a directory, not a file: {path}"
                    )

                if not path.parent:
                    raise ValueError(f"File path has no parent directory: {path}")

                if len(path.name) > 255:
                    raise ValueError(
                        f"File path name is too long, must be less than 255 characters: {path.name}"
                    )

            self._file_paths = paths
        except Exception as e:
            self.logger.error(f"Invalid file paths: {e.__class__.__name__} -> {e}")
            raise FileHandlerSettingsError(
                f"Invalid file paths: {e.__class__.__name__} -> {e}"
            ) from e

    @write_mode.setter
    def write_mode(self, mode: LogWriteMode) -> None:
        """
        Sets the write mode for file logging.

        Arguments:
            mode (LogWriteMode) : The write mode to set.
        """
        try:
            if not isinstance(mode, (LogWriteMode, str)):
                raise ValueError(
                    f"Expected LogWriteMode or str, got {type(mode).__name__}"
                )

            if mode not in LogWriteMode:
                raise ValueError(f"Write mode {mode} is not a valid LogWriteMode.")

            self._write_mode = (
                mode if isinstance(mode, LogWriteMode) else LogWriteMode(mode)
            )
        except Exception as e:
            self.logger.error(f"Invalid write mode: {e.__class__.__name__} -> {e}")
            raise FileHandlerSettingsError(
                f"Invalid write mode: {e.__class__.__name__} -> {e}"
            ) from e

    @retry_limit.setter
    def retry_limit(self, limit: int) -> None:
        """
        Sets the retry limit for file operations.

        Arguments:
            limit (int): The number of retries for file operations.
        """
        try:
            if not isinstance(limit, int) or limit < 0:
                raise ValueError("Retry limit must be a non-negative integer")

            self._retry_limit = limit
        except Exception as e:
            self.logger.error(f"Invalid retry limit: {e.__class__.__name__} -> {e}")
            raise FileHandlerSettingsError(
                f"Invalid retry limit: {e.__class__.__name__} -> {e}"
            ) from e

    @retry_delay.setter
    def retry_delay(self, delay: float) -> None:
        """
        Sets the retry delay for file operations.

        Arguments:
            delay (float): The delay in seconds between retries.
        """
        try:
            if not isinstance(delay, (int, float)) or delay < 0:
                raise ValueError("Retry delay must be a non-negative number")

            self._retry_delay = delay
        except Exception as e:
            self.logger.error(f"Invalid retry delay: {e.__class__.__name__} -> {e}")
            raise FileHandlerSettingsError(
                f"Invalid retry delay: {e.__class__.__name__} -> {e}"
            ) from e

    @backoff_factor.setter
    def backoff_factor(self, factor: float) -> None:
        """
        Sets the backoff factor for retry delays.

        Arguments:
            factor (float): The backoff factor for retry delays.
        """
        try:
            if not isinstance(factor, (int, float)) or factor < 0:
                raise ValueError("Backoff factor must be a non-negative number")

            self._backoff_factor = factor
        except Exception as e:
            self.logger.error(f"Invalid backoff factor: {e.__class__.__name__} -> {e}")
            raise FileHandlerSettingsError(
                f"Invalid backoff factor: {e.__class__.__name__} -> {e}"
            ) from e

    @max_file_size.setter
    def max_file_size(self, size: int) -> None:
        """
        Sets the maximum file size for log files.

        Arguments:
            size (int): The maximum file size in bytes.
        """
        try:
            if not isinstance(size, int) or size < 0:
                raise ValueError("Maximum file size must be a positive integer")

            self._max_file_size = size
        except Exception as e:
            self.logger.error(
                f"Invalid maximum file size: {e.__class__.__name__} -> {e}"
            )
            raise FileHandlerSettingsError(
                f"Invalid maximum file size: {e.__class__.__name__} -> {e}"
            ) from e

    @max_rotation.setter
    def max_rotation(self, rotation: int) -> None:
        """
        Sets the maximum number of rotated log files.

        Arguments:
            rotation (int): The maximum number of rotated log files.
        """
        try:
            if not isinstance(rotation, int) or rotation < 0:
                raise ValueError("Maximum rotation must be a positive integer")

            self._max_rotation = rotation
        except Exception as e:
            self.logger.error(
                f"Invalid maximum rotation: {e.__class__.__name__} -> {e}"
            )
            raise FileHandlerSettingsError(
                f"Invalid maximum rotation: {e.__class__.__name__} -> {e}"
            ) from e

    @logger.setter
    def logger(self, logger: logging.Logger) -> None:
        """
        Sets the logger instance associated with the FileHandler.

        Arguments:
            logger (logging.Logger): The logger instance to set.
        """
        try:
            if not isinstance(logger, logging.Logger):
                raise ValueError("Logger must be an instance of logging.Logger")

            self._logger = logger
        except Exception as e:
            raise FileHandlerSettingsError(
                f"Invalid logger: {e.__class__.__name__} -> {e}"
            ) from e

    @max_buffer_size.setter
    def max_buffer_size(self, size: int) -> None:
        """
        Sets the maximum size of the buffer for log messages.

        Arguments:
            size (int): The maximum size of the buffer in bytes.
        """
        try:
            if not isinstance(size, int) or size < 0:
                raise ValueError("Maximum buffer size must be a positive integer")

            self._max_buffer_size = size
        except Exception as e:
            self.logger.error(
                f"Invalid maximum buffer size: {e.__class__.__name__} -> {e}"
            )
            raise FileHandlerSettingsError(
                f"Invalid maximum buffer size: {e.__class__.__name__} -> {e}"
            ) from e

    @use_write_flush.setter
    def use_write_flush(self, use_flush: bool) -> None:
        """
        Sets whether the handler uses flush after writing to the file.

        Arguments:
            use_flush (bool): Whether to use flush after writing to the file.
        """
        try:
            if not isinstance(use_flush, bool):
                raise ValueError("use_write_flush must be a boolean value")

            self._use_write_flush = use_flush
        except Exception as e:
            self.logger.error(
                f"Invalid use_write_flush setting: {e.__class__.__name__} -> {e}"
            )
            raise FileHandlerSettingsError(
                f"Invalid use_write_flush setting: {e.__class__.__name__} -> {e}"
            ) from e

    # --------------
    # Constructor

    def __init__(
        self,
        file_paths: List[Union[Path, str]],
        write_mode: LogWriteMode = LogWriteMode.APPEND,
        retry_limit: int = 2,
        retry_delay: float = 0.1,
        backoff_factor: float = 0.2,
        max_file_size: int = 10 * 1024 * 1024,  # Default 10 MB
        max_rotation: int = 5,  # Default max number of rotated files
        max_buffer_size: int = 1024 * 1024,  # Default 1 MB buffer size
        use_write_flush: bool = True,  # Whether to use flush after write
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialize the FileHandler with file paths, log level, and log format.

        Arguments:
            file_paths (List[Union[Path, str]]):
                A list of file paths for logging.
            write_mode (LogWriteMode):
                The write mode for file logging.
                    - Default is LogWriteMode.APPEND.
            retry_limit (int):
                The number of retries for file operations.
                    - Default is 2.
            retry_delay (float):
                The delay in seconds between retries for file operations.
                    - Default is 0.1 seconds.
            backoff_factor (float):
                The backoff factor for retry delays.
                    - Default is 0.2 times the retry delay.
            max_file_size (int):
                The maximum file size for log files in bytes.
                    - Default is 10 MB (10 * 1024 * 1024 bytes).
            max_rotation (int):
                The maximum number of rotated log files.
                    - Default is 5.
            max_buffer_size (int):
                The maximum size of the buffer for log messages in bytes.
                    - Default is 1 MB (1024 * 1024 bytes).
            use_write_flush (bool):
                Whether to use flush after writing to the file.
                    - Default is True.
            logger (logging.Logger | None):
                An optional logger instance to use for logging.
                    - If None, a default logger will be created.

        max_buffer_size
        -------------
        -   The maximum size of the buffer for log messages in bytes.
        -   If used, the buffer will hold log messages until it reaches the maximum size.
            -   When the buffer size exceeds the maximum, it will automatically flush the buffer
            -   If size is not reached, the buffer will be flushed when the context manager exits or when `buffer_force_flush()` is called.
            -   **ALWAYS FLUSH THE BUFFER OUTSIDE THE CONTEXT MANAGER, OTHERWISE DATA MAY BE LOST!**

        use_write_flush
        -------------
        -   If set to True, the handler will flush the file after each write operation.
        -   If set to False, the handler will not flush the file after each write operation.
            -   Will improve performance but may lead to data loss in case of a crash.
            -   Must manually flush using `writer_force_flush()` method, or automatically with context manager.

        """
        try:
            out_list = []
            for path in file_paths:
                if isinstance(path, str):
                    path = Path(path)
                elif not isinstance(path, Path):
                    raise ValueError(
                        f"Invalid file path: {path}. Must be a Path or str."
                    )
                out_list.append(path)

            if logger is not None:
                self.logger = logger

            self.file_paths = out_list
            self.write_mode = write_mode
            self.retry_limit = retry_limit
            self.retry_delay = retry_delay
            self.backoff_factor = backoff_factor
            self.max_file_size = max_file_size
            self.max_rotation = max_rotation
            self.max_buffer_size = max_buffer_size
            self.use_write_flush = use_write_flush

            self._temp_sync_pool: Dict[Path, TextIOWrapper] = {}
            self._lock = Lock()

            # Init Threadpool
            max_workers: int = min(len(out_list), 4) if len(out_list) > 1 else 1
            if os.name == "nt":
                max_workers: int = min(max_workers, 4)  # Windows file handle limits
            else:
                max_workers: int = min(max_workers, os.cpu_count() or 4)

            self._threadpool: ThreadPoolExecutor = ThreadPoolExecutor(
                max_workers=max_workers
            )
            self._buffer: StringIO = StringIO()

        except Exception as e:
            self.logger.error(
                f"Error initializing FileHandler: {e.__class__.__name__} -> {e}"
            )
            raise FileHandlerConstructionError(
                f"Error initializing FileHandler: {e.__class__.__name__} -> {e}"
            ) from e

    # --------------
    # Magic Methods

    def __str__(self) -> str:
        """
        Returns a string representation of the FileHandler.

        Returns:
            str: A string representation of the FileHandler.
        """
        return (
            f"FileHandler(file_paths={self.file_paths}, "
            f"write_mode={self.write_mode})"
            f"retry_limit={self.retry_limit}, "
            f"retry_delay={self.retry_delay})"
        )

    def __eq__(self, other: object) -> bool:
        """
        Checks if two FileHandler instances are equal.

        Arguments:
            other (FileHandler): The other FileHandler instance to compare.

        Returns:
            bool: True if both instances are equal, False otherwise.
        """
        if not isinstance(other, FileHandler):
            return False
        return (
            self.file_paths == other.file_paths
            and self.write_mode == other.write_mode
            and self.retry_limit == other.retry_limit
            and self.retry_delay == other.retry_delay
        )

    def __ne__(self, other: object) -> bool:
        """
        Checks if two FileHandler instances are not equal.

        Arguments:
            other (FileHandler): The other FileHandler instance to compare.

        Returns:
            bool: True if both instances are not equal, False otherwise.
        """
        return not self.__eq__(other)

    def __len__(self) -> int:
        """
        Returns the number of file paths in the FileHandler.

        Returns:
            int: The number of file paths.
        """
        return len(self.file_paths)

    def __iter__(self) -> Iterator[Path]:
        """
        Returns an iterator over the file paths in the FileHandler.

        Returns:
            Iterator[Path]: An iterator over the file paths.
        """
        if self.file_paths is None:
            raise ValueError("File paths list is empty. Cannot iterate.")
        return iter(self.file_paths)

    def __del__(self):
        """Cleanup resources when object is destroyed."""
        try:
            # Force flush buffer before cleanup
            if hasattr(self, "_buffer") and self._buffer:
                self.buffer_force_flush()

            # Clear the temporary sync pool
            self.clear_sync_pool()

            # Clear file paths
            if hasattr(self, "_file_paths"):
                self._file_paths = []

            # Shutdown the thread pool executor if it exists
            if hasattr(self, "_threadpool") and self._threadpool:
                if not self._threadpool._shutdown:
                    self._threadpool.shutdown(wait=True)

        except Exception:
            pass

    def __contains__(self, item: Path) -> bool:
        """
        Checks if a file path is in the FileHandler.

        Arguments:
            item (Path): The file path to check.

        Returns:
            bool: True if the file path is in the FileHandler, False otherwise.
        """
        if not isinstance(item, Path):
            raise ValueError(f"Item must be a Path object, got {type(item).__name__}")
        return item in self.file_paths

    def __enter__(self):
        """
        Context manager enter method for FileHandler.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit method for FileHandler.
        """

        # Force flush buffer before cleanup
        if hasattr(self, "_buffer") and self._buffer:
            self.buffer_force_flush()

        # Clear file paths on exit
        if hasattr(self, "_file_paths"):
            self._file_paths = []

        # Clear the synchronous pool
        self.clear_sync_pool()

        # Shutdown the thread pool executor
        if hasattr(self, "_threadpool") and self._threadpool:
            if not self._threadpool._shutdown:
                self._threadpool.shutdown(wait=True)

        # Optionally, you can handle exceptions here if needed
        if exc_type is not None:
            return False

    async def __aenter__(self):
        """
        Asynchronous context manager enter method for FileHandler.
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Asynchronous context manager exit method.
        """
        # Force Buffer flush
        if hasattr(self, "_buffer") and self._buffer:
            self.buffer_force_flush()

        # Clean file paths on exit
        if hasattr(self, "_file_paths"):
            self._file_paths = []

        # Clean the threadpool
        if hasattr(self, "_threadpool") and self._threadpool:
            if not self._threadpool._shutdown:
                self._threadpool.shutdown(wait=True)

        # Optionally, you can handle exceptions here if needed
        if exc_type is not None:
            return False

    # --------------
    # Pool Handlers

    def _ensure_sync_pool(self) -> None:
        """Lazy initialization - only create pool if needed."""
        if not self._temp_sync_pool:
            self._init_sync_pool()

    def _init_sync_pool(self) -> None:
        """
        Initialize the temporary pool for synchronous file operations.
        This method opens the files specified in file_paths in the write mode
        and adds them to the temporary pool for later use.
        """
        try:
            # Check if file_paths is empty
            if not self.file_paths:
                return

            # Ensure all file paths are Path objects
            for path in self.file_paths:
                if not isinstance(path, Path):
                    raise ValueError(
                        f"Invalid file path: {path}. Must be a Path object."
                    )

                if path in self._temp_sync_pool:
                    # If the file is already in the pool, skip it
                    continue

                # Ensure the parent directory exists
                self._ensure_parent_dirs(path)

                # Create the file if it does not exist
                self._create_file(path)

                # Open the file in the specified write mode
                file: TextIOWrapper = open(
                    path, self.write_mode.value, encoding="utf-8"
                )
                if not file.writable():
                    raise IOError(f"File {path} is not writable")

                with self._lock:  # Ensure thread-safe access to the sync pool
                    self._temp_sync_pool[path] = file

        except Exception as e:
            self.logger.error(
                f"Error initializing sync pool: {e.__class__.__name__} -> {e}"
            )
            raise FileHandlerSyncPoolInitError(
                f"Error initializing sync pool: {e.__class__.__name__} -> {e}"
            ) from e

    def clear_sync_pool(self) -> None:
        """
        Clear the temporary pool for synchronous file operations.
        This method closes all files in the temporary pool and clears it.
        """
        try:
            # Check if the sync pool is empty
            if not self._temp_sync_pool:
                return

            for path in list(self._temp_sync_pool.keys()):
                file = self._temp_sync_pool[path]
                try:
                    if isinstance(file, TextIOWrapper) and not file.closed:
                        file.flush()
                        file.close()
                except Exception as e:
                    # Log the error but continue closing other files
                    self.logger.warning(f"Warning: Failed to close file {path}: {e}")
                finally:
                    # Always remove from pool even if close failed
                    self._temp_sync_pool.pop(path, None)

            # Final clear as safety measure
            with self._lock:
                self._temp_sync_pool.clear()
        except Exception as e:
            self.logger.error(
                f"Error clearing sync pool: {e.__class__.__name__} -> {e}"
            )
            raise FileHandlerSyncPoolCleanupError(
                f"Error clearing sync pool: {e.__class__.__name__} -> {e}"
            ) from e

    # --------------
    # Helpers