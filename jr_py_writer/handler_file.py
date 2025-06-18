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
)


# ----------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------


class FileHandler:
    """
    A handler that writes log messages to one or more files.
    FileHandler manages writing log messages to specified file paths with
    configurable write modes and retry mechanisms for handling file operation failures.

    The handler supports both synchronous and asynchronous writing operations,
    automatically creating parent directories for log files if they don't exist.
    It also provides thread-safe writing with retry logic to handle temporary
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
    -   The maximum size of the buffer for log messages in bytes.
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
        #### log(message: str) - None:
            Write a log message to the specified file paths synchronously.
        #### async_log(message: str) - None:
            Asynchronously write a log message to the specified file paths.
        #### buffer_force_flush() - None:
            Force flush the buffer to the file(s) immediately.
        #### writer_force_flush() - None:
            Force flush the file(s) immediately, ensuring all data is written to disk.
        #### clear_sync_pool() - None:
            Clear the temporary pool for synchronous file operations, closing all files.

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

    def _check_file_size(self, message: str, path: Path) -> bool:
        """
        Check if the file size exceeds the maximum allowed size.

        Arguments:
            message (str): The log message to be written.
            path (Path): The file path to check.

        Returns:
            bool: True if the file size exceeds the maximum allowed size, False otherwise.
        """
        try:
            if (
                path.exists()
                and path.stat().st_size + len(message.encode("utf-8"))
                > self.max_file_size
            ):
                self.logger.debug(
                    f"File:\n{path}\nOf size {path.stat().st_size} exceeds maximum size of {self.max_file_size} bytes."
                )
                return True

            self.logger.debug(
                f"File:\n{path}\nOf size {path.stat().st_size} is within the size limit of {self.max_file_size} bytes."
            )
            return False

        except Exception as e:
            self.logger.error(f"Error checking file size for {path}: {e}")
            return False

    def _rotate_file(self, message: str, path: Path) -> None:
        """
        Rotate the log file if it exceeds the maximum size.

        Arguments:
            message (str): The log message to be written.
            path (Path): The file path to rotate.
        """
        try:
            if not self._check_file_size(message, path):
                return

            with self._lock:  # Ensure thread-safe access to rotate file operations
                # Close and remove from pool before rotation
                if path in self._temp_sync_pool:
                    file = self._temp_sync_pool[path]
                    if not file.closed:
                        file.close()
                    del self._temp_sync_pool[path]

                # Handle max_rotation = 0 (no rotation, just truncate)
                if self.max_rotation == 0:
                    path.write_text("", encoding="utf-8")
                    return

                # Rotate existing files (move them up in number)
                for i in range(self.max_rotation - 1, 0, -1):
                    rotated_file: Path = path.with_name(f"{path.stem}_{i}{path.suffix}")
                    next_rotated_file: Path = path.with_name(
                        f"{path.stem}_{i + 1}{path.suffix}"
                    )

                    if rotated_file.exists():
                        # Remove the target file if it exists (oldest log)
                        if next_rotated_file.exists():
                            next_rotated_file.unlink()
                        rotated_file.rename(next_rotated_file)

                # Move the current file to the first rotated position
                first_rotated_file = path.with_name(f"{path.stem}_1{path.suffix}")

                # Remove the first rotated file if it exists
                if first_rotated_file.exists():
                    first_rotated_file.unlink()

                # Rename the current file to the first rotated file
                path.rename(first_rotated_file)

                # Log the rotation
                self.logger.debug(f"Rotated file {path} to {first_rotated_file}")

                # Create a new empty file
                path.touch()

        except Exception as e:
            self.logger.error(
                f"Error rotating file {path}: {e.__class__.__name__} -> {e}"
            )
            raise FileHandleRotateError(
                f"Error rotating file {path}: {e.__class__.__name__} -> {e}"
            ) from e

    def _ensure_parent_dirs(self, path: Path) -> None:
        """Ensure parent directories exist for the given path."""
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

    def _create_file(self, path: Path) -> None:
        """
        Create a new file at the specified path if it does not exist.

        Arguments:
            path (Path): The file path to create.
        """
        if not path.exists():
            self.logger.debug(f"Creating file {path} ...")
            self._ensure_parent_dirs(path)
            with open(path, "w", encoding="utf-8") as file:
                if not file.writable():
                    raise IOError(f"Error in _create_file: File {path} is not writable")
            self.logger.debug(f"File {path} created successfully.")

    # --------------
    # Buffer

    def _get_buffer_message(self) -> str:
        """
        Return the message if available.
        This method retrieves the message from the buffer, clears the buffer,
        and returns the message if it is not empty.

        Returns:
            out (str | None): The message from the buffer or None if the buffer is empty.
        """
        # Get the message from the buffer
        self._buffer.flush()
        message: str = self._buffer.getvalue().strip()

        # Log
        self.logger.debug("Buffer flushed")

        # Clear the buffer
        self._buffer.truncate(0)
        self._buffer.seek(0)

        # Return the message to be written
        return message

    def _write_to_buffer(self, message: str) -> str | None:
        """
        Write the log message to the buffer.

        Arguments:
            message (str): The log message to write.
        """
        if not hasattr(self, "_buffer") or self._buffer is None:
            if self.max_buffer_size > 0:
                self._buffer = StringIO()
            else:
                return None

        # Check if the buffer size exceeds the maximum allowed size
        if self._buffer.tell() + len(message.encode("utf-8")) > self.max_buffer_size:
            # Log message and clear the buffer if it exceeds the max size
            return self._get_buffer_message()

        self._buffer.write(message + "\n")
        return None

    # --------------
    # File Writing Methods

    def _write_to_file(self, path: Path, message: str) -> None:
        """
        Write the log message to a single file.

        Arguments:
            path (Path): The file path to write to.
            message (str): The log message to write.
        """

        # Check and rotate before writing
        if self._check_file_size(message, path):
            self._rotate_file(message, path)
            # Reinitialize pool after rotation
            with self._lock:
                # If the file is in the temporary sync pool, close it and remove it
                if path in self._temp_sync_pool:
                    self._temp_sync_pool[path].close()
                    del self._temp_sync_pool[path]

        # Get the file from the temporary pool
        file: TextIOWrapper | None = self._temp_sync_pool.get(path)

        if not file:
            # If the file is not in the temporary pool, open it
            self._ensure_parent_dirs(path)
            self._create_file(path)
            with self._lock:  # Ensure thread-safe access to the sync pool
                file = open(path, self.write_mode.value, encoding="utf-8")
                if not file.writable():
                    raise IOError(f"File {path} is not writable")
                self._temp_sync_pool[path] = file

        # Write with retry logic
        if self.retry_limit > 0:
            counter: int = 0
            for _ in range(self.retry_limit):
                try:
                    with self._lock:  # Ensure thread-safe access to the file
                        if not file:
                            raise RuntimeError(f"File {path} is not open for writing.")
                        file.write(message + "\n")
                        # Check for flush after write
                        if self.use_write_flush:
                            file.flush()
                    return  # Exit if write is successful

                except Exception as e:
                    counter += 1
                    if counter >= self.retry_limit:
                        raise RuntimeError(
                            f"Failed to write to {file} after {self.retry_limit} attempts: {e}"
                        ) from e

                    # Wait before retrying
                    if self.retry_delay > 0:
                        if self.backoff_factor:
                            # Exponential backoff
                            exp_time: float = self.retry_delay * (
                                self.backoff_factor ** (counter - 1)
                            )

                            # Log the retry attempt
                            self.logger.warning(
                                f"Retrying to write to {file} in {exp_time:.2f} seconds (attempt {counter}/{self.retry_limit})"
                            )
                            # Sleep for the calculated backoff time

                            time.sleep(
                                self.retry_delay
                                * (self.backoff_factor ** (counter - 1))
                            )
                        else:

                            # Linear backoff
                            self.logger.warning(
                                f"Retrying to write to {file} in {self.retry_delay:.2f} seconds (attempt {counter}/{self.retry_limit})"
                            )
                            time.sleep(self.retry_delay)

        # If no retry is needed, write directly
        else:
            with self._lock:  # Ensure thread-safe access to the file
                if not file:
                    raise RuntimeError(f"File {path} is not open for writing.")
                if file.closed:
                    raise RuntimeError(
                        f"File {path} is closed and cannot be written to."
                    )

                file.write(message + "\n")
                # Check for flush after write
                if self.use_write_flush:
                    file.flush()

    def _writer(self, message: str) -> None:
        """
        Write the log message to the specified file paths.

        Arguments:
            message (str): The log message to write.
        """
        if not self.file_paths:
            raise ValueError("File paths list is empty. Cannot write log message.")

        futures = {
            self._threadpool.submit(partial(self._write_to_file, path, message)): path
            for path in self.file_paths
        }
        for future in as_completed(futures):
            path = futures[future]
            try:
                future.result()
            except Exception as e:
                raise RuntimeError(f"Error writing to {path}: {e}") from e

    def _log_batch(self, message: str, path_batch: List[Path]) -> None:
        """
        Optimized batch logging.

        Arguments:
            message (str): The log message to write.
            path_batch (List[Path]): The file paths to write to.
        """
        # Write all message in a single operation per file
        for path in path_batch:
            self._write_to_file(path, message)

    async def _async_log_batch(self, message: str, path_batch: List[Path]) -> None:
        """
        Asynchronously write the log message to a batch of file paths.

        Arguments:
            message (str): The log message to write.
            path_batch (List[Path]): The file paths to write to.
        """
        # Use asyncio to send file write tasks concurrently
        await asyncio.get_event_loop().run_in_executor(
            self._threadpool, partial(self._log_batch, message, path_batch)
        )

    def _writer_handler(self, message: str) -> None:
        """
        Write the log message to the specified file paths in batches.

        Arguments:
            message (str): The log message to write.

        Notes:
        ------
        - If the number of file paths is greater than 50, use the batcher function.
        - If the number of file paths is greater than 1000, use the batcher_with_gcmanager function.
        - Otherwise, use the list of file paths.
        """
        # If the number of file paths is greater than 50, use the batcher function.
        if len(self.file_paths) > 50:
            batches_of_paths: List[List[Path]] = list(batcher(self.file_paths))
        # If the number of file paths is greater than 1000, use the batcher_with_gcmanager function.
        elif len(self.file_paths) > 1000:
            batches_of_paths: List[List[Path]] = list(
                batcher_with_gcmanager(self.file_paths)
            )
        # Otherwise, use the list of file paths.
        else:
            for path in self.file_paths:
                self._write_to_file(path, message)
            return

        # Use ThreadPoolExecutor to write in parallel
        futures = {
            self._threadpool.submit(
                partial(self._log_batch, message, path_batch)
            ): path_batch
            for path_batch in batches_of_paths
        }
        for future in as_completed(futures):
            path_batch = futures[future]
            try:
                future.result()
            except Exception as e:
                raise RuntimeError(f"Error writing to {path_batch}: {e}") from e

    async def _async_writer(self, message: str) -> None:
        """
        Asynchronously write the log message to the specified file paths.

        Arguments:
            message (str): The log message to write.
        """
        if not isinstance(message, str):
            raise ValueError("Log message must be a string")

        # Use asyncio to send file write tasks concurrently
        # Will not use asyncio directly, the ThreadPoolExecutor will handle the file writes
        # The ThreadPoolExecutor have better performance for I/O-bound tasks

        def write_all_files():
            for path in self.file_paths:
                self._write_to_file(path, message)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._threadpool, write_all_files)

    async def _async_writer_handler(self, message: str) -> None:
        """
        Write asynchronously the log message to the specified file paths in batches.

        Arguments:
            message (str): The log message to write.

        Notes:
        ------
        - If the number of file paths is greater than 50, use the batcher function.
        - If the number of file paths is greater than 1000, use the batcher_with_gcmanager function.
        - Otherwise, use the list of file paths.
        """
        # Get the length of the file paths list
        len_of_file_paths: int = len(self.file_paths)

        # If the number of file paths is greater than 50, use the batcher function.
        if len_of_file_paths > 50:
            batches_of_paths: List[List[Path]] = list(batcher(self.file_paths))
        # If the number of file paths is greater than 1000, use the batcher_with_gcmanager function.
        elif len_of_file_paths > 1000:
            batches_of_paths: List[List[Path]] = list(
                batcher_with_gcmanager(self.file_paths)
            )
        # Otherwise, use the list of file paths.
        else:
            await self._async_writer(message)
            return

        for path_batch in batches_of_paths:
            await self._async_log_batch(message, path_batch)

    # --------------
    # Methods

    def clear_all(self) -> None:
        """
        Clear all resources used by the FileHandler.
        This method will:
        -   Force flush the buffer if it exists and has content.
        -   Clear the synchronous pool.
        -   Clean the file paths on exit.
        -   Clean the thread pool executor if it exists.
        -   This method is useful for cleaning up resources when the FileHandler is no longer needed.
        """

        # Force flush the buffer if it exists and has content
        if hasattr(self, "_buffer") and self._buffer:
            self.buffer_force_flush()

        # Clean the synchronous pool
        self.clear_sync_pool()

        # Clean file paths on exit
        if hasattr(self, "_file_paths"):
            self._file_paths = []

        # Clean the threadpool
        if hasattr(self, "_threadpool") and self._threadpool:
            if not self._threadpool._shutdown:
                self._threadpool.shutdown(wait=True)

    # Logging

    def log(self, message: str) -> None:
        """
        Write the log message to the file(s).

        Arguments:
            message (str): The log message to write.
        """
        try:
            if not isinstance(message, str):
                raise ValueError("Log message must be a string")

            if not message.strip():
                raise ValueError("Log message cannot be empty or whitespace")

            if not self.file_paths:
                return

            # Initialize the synchronous pool
            # Will skip paths that are already initialized
            self._ensure_sync_pool()

            # If the max_buffer_size is set, write to buffer first
            if self.max_buffer_size > 0:
                # Write to buffer and check if it exceeds the max size
                buffer_message: str | None = self._write_to_buffer(message)
                # If the buffer message is not None, it means the buffer exceeded the max size
                # and we need to write it to the file(s)
                if buffer_message:
                    self._writer_handler(buffer_message)
                    return
                # If the buffer is used, but size is not exceeded, we can continue
                # writing to the file(s) without flushing the buffer
                else:
                    return

            # If the buffer is not used, write directly to the file(s)
            self._writer_handler(message)
        except Exception as e:
            self.logger.error(
                f"Error writing log message: {e.__class__.__name__} -> {e}"
            )
            raise FileHandlerWriteError(
                f"Error writing log message: {e.__class__.__name__} -> {e}"
            ) from e

    async def async_log(self, message: str) -> None:
        """
        Asynchronously write the log message to the file(s).

        Arguments:
            message (str): The log message to write.
        """
        try:
            if not isinstance(message, str):
                raise ValueError("Log message must be a string")

            if not message.strip():
                raise ValueError("Log message cannot be empty or whitespace")

            if not self.file_paths:
                return

            # Initialize the asynchronous pool
            # Will skip paths that are already initialized
            self._init_sync_pool()

            # If the max_buffer_size is set, write to buffer first
            if self.max_buffer_size > 0:
                # Write to buffer and check if it exceeds the max size
                buffer_message: str | None = self._write_to_buffer(message)
                # If the buffer message is not None, it means the buffer exceeded the max size
                # and we need to write it to the file(s)
                if buffer_message:
                    await self._async_writer_handler(buffer_message)
                    return
                # If the buffer is used, but size is not exceeded, we can continue
                # writing to the file(s) without flushing the buffer
                else:
                    return

            # Use the asynchronous writer to write the message
            await self._async_writer_handler(message)
        except Exception as e:
            self.logger.error(
                f"Error writing log message asynchronously: {e.__class__.__name__} -> {e}"
            )
            raise FileHandlerAsyncWriteError(
                f"Error writing log message asynchronously: {e.__class__.__name__} -> {e}"
            ) from e

    # Buffer Management

    def buffer_force_flush(self) -> None:
        """
        Force flush the buffer to the file(s).
        -   This method will check if the buffer is not None and if it has any content.
        -   If the buffer is not empty, it will write the content to the file(s) using the writer handler.
        -   Will flush the file(s) after writing the buffer content.
        """
        try:
            if self._buffer is None:
                return

            if len(self._buffer.getvalue()) > 0:
                # If the buffer is not empty, write the buffer to the file(s)
                buffer_message: str | None = self._get_buffer_message()
                if buffer_message:
                    self._writer_handler(buffer_message)

            self.writer_force_flush()  # Ensure all files are flushed

        except Exception as e:
            self.logger.error(
                f"Error forcing buffer flush: {e.__class__.__name__} -> {e}"
            )
            raise FileHandlerBufferError(
                f"Error forcing buffer flush: {e.__class__.__name__} -> {e}"
            ) from e

    # Thread Pool Management

    def force_shutdown(self, wait: bool = True) -> None:
        """
        Force shutdown the thread pool executor.
        This method will shut down the thread pool executor.

        Arguments:
            wait (bool): Whether to wait for all tasks to complete before shutting down.
                - Default is True, which waits for all tasks to finish.
        """
        if not self._threadpool._shutdown:
            try:
                self._threadpool.shutdown(wait=wait)
                self.logger.debug("Thread pool executor shutdown successfully.")
            except Exception as e:
                self.logger.error(
                    f"Error shutting down thread pool executor: {e.__class__.__name__} -> {e}"
                )
                raise FileHandlerShutdownError(
                    f"Error shutting down thread pool executor: {e.__class__.__name__} -> {e}"
                ) from e

    def resume_pool(self) -> None:
        """
        Resume the thread pool executor.
        This method will reinitialize the thread pool executor.
        """
        try:
            if self._threadpool is not None and self._threadpool._shutdown:
                self._threadpool.shutdown(wait=True)

            # Init Threadpool
            max_workers: int = (
                min(len(self.file_paths), 4) if len(self.file_paths) > 1 else 1
            )
            if os.name == "nt":
                max_workers: int = min(max_workers, 4)  # Windows file handle limits
            else:
                max_workers: int = min(max_workers, os.cpu_count() or 4)

            # Reinitialize the thread pool executor
            self._threadpool = ThreadPoolExecutor(
                max_workers=max_workers,
            )
        except Exception as e:
            self.logger.error(
                f"Error resuming thread pool executor: {e.__class__.__name__} -> {e}"
            )
            raise FileHandlerResumeError(
                f"Error resuming thread pool executor: {e.__class__.__name__} -> {e}"
            ) from e

    # Writer Performance

    def writer_force_flush(self) -> None:
        """
        Force flush the file writer.
        This method will ensure that all pending writes are flushed to the file(s).
        """
        try:
            if not self._temp_sync_pool:
                return None

            with self._lock:  # Ensure thread-safe access to the sync pool
                # Flush all files in the temporary sync pool
                for path, file in self._temp_sync_pool.items():
                    try:
                        if not file.closed:
                            file.flush()
                    except Exception as e:
                        raise RuntimeError(
                            f"Error flushing file {path}: {e.__class__.__name__} -> {e}"
                        ) from e

        except Exception as e:
            self.logger.error(
                f"Error {e.__class__.__name__} in writer_force_flush: {e}"
            )
            raise FileHandlerFlushError(
                f"Error forcing flush: {e.__class__.__name__} -> {e}"
            ) from e

    # --------------
    # Config

    def reset(self, file_paths: List[Union[Path, str]]) -> None:
        """
        Reset the FileHandler to its default configuration.
        This method will reset all configuration parameters to their default values.

        Arguments:
            file_paths (List[Union[Path, str]]):
                A list of file paths for logging. If a string is provided, it will be converted to a Path object.
        """
        try:
            out_list: List[Path] = [
                Path(path) if isinstance(path, str) else path for path in file_paths
            ]

            self.file_paths = out_list
            self.write_mode = LogWriteMode.APPEND
            self.retry_limit = 3
            self.retry_delay = 0.5
            self.backoff_factor = 0.2
            self.max_file_size = 10 * 1024 * 1024
            self.max_rotation = 2
            self.max_buffer_size = 1024 * 1024  # Default no buffer size limit
            self.use_write_flush = True  # Default no write flush

        except Exception as e:
            self.logger.error(
                f"Error resetting FileHandler: {e.__class__.__name__} -> {e}"
            )
            raise FileHandlerResetError(
                f"Error resetting FileHandler: {e.__class__.__name__} -> {e}"
            ) from e

    def config(
        self,
        file_paths: List[Union[Path, str]],
        write_mode: LogWriteMode = LogWriteMode.APPEND,
        retry_limit: int = 3,
        retry_delay: float = 0.5,
        backoff_factor: float = 0.2,
        max_file_size: int = 10 * 1024 * 1024,  # Default 10 MB
        max_rotation: int = 5,  # Default max number of rotated files
        max_buffer_size: int = 1024 * 1024,  # Default no buffer size limit
        use_write_flush: bool = True,  # Default no write flush
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Configure the FileHandler with new settings.

        Arguments:
            file_paths (List[Union[Path, str]]):
                A list of file paths for logging.
            write_mode (LogWriteMode):
                Write mode for file logging (default is LogWriteMode.APPEND).
            retry_limit (int):
                Number of retries for file operations (default is 3).
            retry_delay (float):
                Delay in seconds between retries (default is 0.5).
            backoff_factor (float):
                Backoff factor for retry delays (default is 0.2).
            max_file_size (int):
                Maximum file size in bytes (default is 10 MB).
            max_rotation (int):
                Maximum number of rotated log files (default is 5).
            max_buffer_size (int):
                Maximum buffer size in bytes (default is 0, meaning no limit).
            use_write_flush (bool):
                Whether to flush the file after each write (default is True).
            logger (logging.Logger | None):
                An optional logger instance to use for logging.
        """

        try:

            if file_paths is not None:
                out_paths: List[Path] = [
                    Path(path) if isinstance(path, str) else path for path in file_paths
                ]
                self.file_paths = out_paths

            if write_mode is not None:
                self.write_mode = write_mode

            if retry_limit is not None:
                self.retry_limit = retry_limit

            if retry_delay is not None:
                self.retry_delay = retry_delay

            if backoff_factor is not None:
                self.backoff_factor = backoff_factor

            if max_file_size is not None:
                self.max_file_size = max_file_size

            if max_rotation is not None:
                self.max_rotation = max_rotation

            if max_buffer_size is not None:
                self.max_buffer_size = max_buffer_size

            if use_write_flush is not None:
                self.use_write_flush = use_write_flush

            if logger is not None:
                self.logger = logger

        except Exception as e:
            self.logger.error(
                f"Error configuring FileHandler: {e.__class__.__name__} -> {e}"
            )
            raise FileHandlerConfigError(
                f"Error configuring FileHandler: {e.__class__.__name__} -> {e}"
            ) from e

    def config_dict(self, config_dict: Dict[str, Any]) -> None:
        """
        Configure the FileHandler using a dictionary.

        Arguments:
            configDict (Dict[str, Any]): A dictionary containing configuration options.

        Options:
        ---------
            file_paths (List[Union[Path, str]]): List of file paths for logging.
            write_mode (LogWriteMode): Write mode for file logging (default is LogWriteMode.APPEND).
            retry_limit (int): Number of retries for file operations (default is 3).
            retry_delay (float): Delay in seconds between retries (default is 0.5).
            backoff_factor (float): Backoff factor for retry delays (default is 0.2).
            max_file_size (int): Maximum file size in bytes (default is 10 MB).
            max_rotation (int): Maximum number of rotated log files (default is 5).
            max_buffer_size (int): Maximum buffer size in bytes (default is 0, meaning no limit).
            use_write_flush (bool): Whether to flush the file after each write (default is True).
            logger (logging.Logger | None): An optional logger instance to use for logging.
        """
        if not isinstance(config_dict, dict):
            raise ValueError("Configuration must be a dictionary")

        self.config(**config_dict)

    def config_json(self, config_json: str | bytes) -> None:
        """
        Configure the FileHandler using a JSON string or dictionary.

        Arguments:
            config_json (Union[str, Dict[str, Any]]): A JSON string or dictionary containing configuration options.
        """
        if isinstance(config_json, str):
            try:
                config_dict: Dict[str, Any] = json.loads(config_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {e}") from e

        elif isinstance(config_json, bytes):
            try:
                config_dict: Dict[str, Any] = json.loads(config_json.decode("utf-8"))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {e}") from e
        else:
            raise ValueError("Configuration must be a JSON string or bytes")

        self.config_dict(config_dict)

    def config_yaml(self, config_yaml: str | bytes) -> None:
        """
        Configure the FileHandler using a YAML string or dictionary.

        Arguments:
            config_yaml (Union[str, Dict[str, Any]]): A YAML string or dictionary containing configuration options.
        """
        if isinstance(config_yaml, str):
            try:
                config_dict: Dict[str, Any] = yaml.safe_load(config_yaml)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML format: {e}") from e

        elif isinstance(config_yaml, bytes):
            try:
                config_dict: Dict[str, Any] = yaml.safe_load(
                    config_yaml.decode("utf-8")
                )
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML format: {e}") from e
        else:
            raise ValueError("Configuration must be a YAML string or bytes")

        self.config_dict(config_dict)
