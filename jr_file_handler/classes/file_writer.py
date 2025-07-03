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

from typing import Iterator, List, Sequence, Union, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from functools import partial

# Local imports
from jr_file_handler.utils.module_enums import LogWriteMode

# Utilities
from jr_file_handler.utils.utilities import batcher, batcher_with_gcmanager

# Exceptions
from jr_file_handler.exceptions.exceptions_file_writer import (
    FileWriterConstructionError,
    FileWriterSettingsError,
    FileWriterSyncPoolInitError,
    FileWriterSyncPoolCleanupError,
    FileWriterWriteError,
    FileWriterAsyncWriteError,
    FileWriterRotateError,
    FileWriterConfigError,
    FileWriterBufferError,
    FileWriterFlushError,
    FileWriterShutdownError,
    FileWriterResumeError,
    FileWriterResetError,
)


# ----------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------

LIST_OF_NECESSARY_KEYS: List[str] = [
    "file_paths",
    "write_mode",
    "retry_limit",
    "retry_delay",
    "backoff_factor",
    "max_file_size",
    "max_rotation",
    "max_buffer_size",
    "use_write_flush",
    "logger",
]


class FileWriter:

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
        if not hasattr(self, "_file_paths"):
            self._file_paths = []
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
        Returns the logger instance associated with the FileWriter.
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
            if paths is None:
                self._file_paths = []
                return

            if not isinstance(paths, list):
                raise ValueError(
                    f"File paths must be a list of Path objects, got {type(paths).__name__}"
                )

            if not paths:
                self._file_paths = []

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
            raise FileWriterSettingsError(
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
            raise FileWriterSettingsError(
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
            raise FileWriterSettingsError(
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
            raise FileWriterSettingsError(
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
            raise FileWriterSettingsError(
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
            raise FileWriterSettingsError(
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
            raise FileWriterSettingsError(
                f"Invalid maximum rotation: {e.__class__.__name__} -> {e}"
            ) from e

    @logger.setter
    def logger(self, logger: logging.Logger) -> None:
        """
        Sets the logger instance associated with the FileWriter.

        Arguments:
            logger (logging.Logger): The logger instance to set.
        """
        try:
            if not isinstance(logger, logging.Logger):
                raise ValueError("Logger must be an instance of logging.Logger")

            self._logger = logger
        except Exception as e:
            raise FileWriterSettingsError(
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
            raise FileWriterSettingsError(
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
            raise FileWriterSettingsError(
                f"Invalid use_write_flush setting: {e.__class__.__name__} -> {e}"
            ) from e

    # --------------
    # Constructor

    def __init__(
        self,
        file_paths: Union[List[Union[Path, str]], None] = None,
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
        Initialize the FileWriter with file paths, log level, and log format.

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
            # Ensure file_paths is a list of Path objects
            out_list = []
            if file_paths is None:
                out_list = []
            else:
                if not isinstance(file_paths, list):
                    raise TypeError(
                        f"File paths must be a list of Path or str objects, got {type(file_paths).__name__}"
                    )
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
                f"Error initializing FileWriter: {e.__class__.__name__} -> {e}"
            )
            raise FileWriterConstructionError(
                f"Error initializing FileWriter: {e.__class__.__name__} -> {e}"
            ) from e

    # --------------
    # Magic Methods

    def __str__(self) -> str:
        """
        Returns a string representation of the FileWriter.

        Returns:
            str: A string representation of the FileWriter.
        """
        return (
            f"FileWriter(file_paths={self.file_paths}, "
            f"write_mode={self.write_mode})"
            f"retry_limit={self.retry_limit}, "
            f"retry_delay={self.retry_delay})"
        )

    def __eq__(self, other: object) -> bool:
        """
        Checks if two FileWriter instances are equal.

        Arguments:
            other (object): The other instance to compare.

        Returns:
            bool: True if both instances are equal, False otherwise.
        """
        if not isinstance(other, FileWriter):
            return False
        return (
            self.file_paths == other.file_paths
            and self.write_mode == other.write_mode
            and self.retry_limit == other.retry_limit
            and self.retry_delay == other.retry_delay
        )

    def __ne__(self, other: object) -> bool:
        """
        Checks if two FileWriter instances are not equal.

        Arguments:
            other (FileWriter): The other FileWriter instance to compare.

        Returns:
            bool: True if both instances are not equal, False otherwise.
        """
        return not self.__eq__(other)

    def __len__(self) -> int:
        """
        Returns the number of file paths in the FileWriter.

        Returns:
            int: The number of file paths.
        """
        return len(self.file_paths)

    def __iter__(self) -> Iterator[Path]:
        """
        Returns an iterator over the file paths in the FileWriter.

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
        Checks if a file path is in the FileWriter.

        Arguments:
            item (Path): The file path to check.

        Returns:
            bool: True if the file path is in the FileWriter, False otherwise.
        """
        if not isinstance(item, Path):
            raise ValueError(f"Item must be a Path object, got {type(item).__name__}")
        return item in self.file_paths

    def __enter__(self):
        """
        Context manager enter method for FileWriter.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit method for FileWriter.
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
        Asynchronous context manager enter method for FileWriter.
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
            raise FileWriterSyncPoolInitError(
                f"Error initializing sync pool: {e.__class__.__name__} -> {e}"
            ) from e

    def clear_sync_pool(self) -> None:
        """
        Clear the temporary pool for synchronous file operations.
        This method closes all files in the temporary pool and clears it.
        """
        try:
            # Check if the pool exists
            if not hasattr(self, "_temp_sync_pool"):
                return

            # Check if the sync pool is empty
            if not self._temp_sync_pool:
                return

            for path in self._temp_sync_pool.keys():
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
            raise FileWriterSyncPoolCleanupError(
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
            raise FileWriterRotateError(
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
        Clear all resources used by the FileWriter.
        This method will:
        -   Force flush the buffer if it exists and has content.
        -   Clear the synchronous pool.
        -   Clean the file paths on exit.
        -   Clean the thread pool executor if it exists.
        -   This method is useful for cleaning up resources when the FileWriter is no longer needed.
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

    def write(self, message: str) -> None:
        """
        Write the message to the file(s).

        Arguments:
            message (str): The log message to write.
        """
        try:
            if not isinstance(message, str):
                raise ValueError("Message must be a string")

            if not message.strip():
                raise ValueError("Message cannot be empty or whitespace")

            if not self.file_paths:
                return

            if self.write_mode not in (
                LogWriteMode.APPEND,
                LogWriteMode.OVERWRITE,
                LogWriteMode.READ_WRITE,
            ):
                raise ValueError(
                    f"FileWriter is not configured for writing. Use LogWriteMode.APPEND, LogWriteMode.OVERWRITE, or LogWriteMode.READ_WRITE."
                    f"\n\tCurrent mode: {self.write_mode.value}\n"
                )

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
            raise FileWriterWriteError(
                f"Error writing log message: {e.__class__.__name__} -> {e}"
            ) from e

    async def async_write(self, message: str) -> None:
        """
        Asynchronously write the message to the file(s).

        Arguments:
            message (str): The log message to write.
        """
        try:
            if not isinstance(message, str):
                raise ValueError("Message must be a string")

            if not message.strip():
                raise ValueError("Message cannot be empty or whitespace")

            if not self.file_paths:
                return

            if self.write_mode not in (
                LogWriteMode.APPEND,
                LogWriteMode.OVERWRITE,
                LogWriteMode.READ_WRITE,
            ):
                raise ValueError(
                    f"FileWriter is not configured for writing. Use LogWriteMode.APPEND, LogWriteMode.OVERWRITE, or LogWriteMode.READ_WRITE."
                    f"\n\tCurrent mode: {self.write_mode.value}\n"
                )

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
            raise FileWriterAsyncWriteError(
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
            raise FileWriterBufferError(
                f"Error forcing buffer flush: {e.__class__.__name__} -> {e}"
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
            raise FileWriterFlushError(
                f"Error forcing flush: {e.__class__.__name__} -> {e}"
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
                raise FileWriterShutdownError(
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
            raise FileWriterResumeError(
                f"Error resuming thread pool executor: {e.__class__.__name__} -> {e}"
            ) from e

    def is_pool_shutdown(self) -> bool:
        """
        Check if the thread pool executor is shutdown.

        Returns:
            bool: True if the thread pool executor is shutdown, False otherwise.
        """
        return self._threadpool._shutdown if hasattr(self, "_threadpool") else True

    def is_pool_active(self) -> bool:
        """
        Check if the thread pool executor is active.

        Returns:
            bool: True if the thread pool executor is active, False otherwise.
        """
        return not self._threadpool._shutdown if hasattr(self, "_threadpool") else False

    # Class Methods

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "FileWriter":
        """
        Create a FileWriter instance from a configuration dictionary.

        Arguments:
            config_dict (Dict[str, Any]): The configuration dictionary containing file paths and other settings.

        Returns:
            out (FileWriter): An instance of FileWriter configured with the provided settings.
        """
        try:

            if not isinstance(config_dict, dict):
                raise TypeError("Configuration must be a dictionary.")

            if len(config_dict) == 0:
                raise ValueError("Configuration dictionary is empty.")

            for key in config_dict:
                if key not in LIST_OF_NECESSARY_KEYS:
                    raise KeyError(
                        f"Invalid key '{key}' in configuration. "
                        f"Allowed keys are: {', '.join(LIST_OF_NECESSARY_KEYS)}"
                    )

            # Extract configuration parameters from the dictionary
            file_paths: Sequence[Path | str] = config_dict.get("file_paths", [])
            write_mode: LogWriteMode = config_dict.get(
                "write_mode", LogWriteMode.APPEND
            )
            max_file_size: int = config_dict.get(
                "max_file_size", 10 * 1024 * 1024
            )  # Default 10 MB
            max_rotation: int = config_dict.get(
                "max_rotation", 5
            )  # Default 5 rotations
            max_buffer_size: int = config_dict.get(
                "max_buffer_size", 0
            )  # Default no buffer
            retry_limit: int = config_dict.get("retry_limit", 3)  # Default retry limit
            retry_delay: float = config_dict.get(
                "retry_delay", 1.0
            )  # Default retry delay in seconds
            backoff_factor: float = config_dict.get(
                "backoff_factor", 0.2
            )  # Default backoff factor for retries
            logger: logging.Logger = config_dict.get(
                "logger", logging.getLogger(__name__)
            )

            return cls(
                file_paths=[Path(p) for p in file_paths] if file_paths else [],
                write_mode=write_mode,
                max_file_size=max_file_size,
                max_rotation=max_rotation,
                max_buffer_size=max_buffer_size,
                retry_limit=retry_limit,
                retry_delay=retry_delay,
                backoff_factor=backoff_factor,
                logger=logger,
            )

        except Exception as e:
            raise FileWriterConfigError(
                f"Error creating FileWriter from config: {e.__class__.__name__} -> {e}"
            ) from e

    @classmethod
    def from_json(
        cls, json_file: Union[str, bytes], custom_decoder: str = "utf-8"
    ) -> "FileWriter":
        """
        Create a FileWriter instance from a JSON file.

        Arguments:
            json_file (Union[str, bytes]): The path to the JSON file or the JSON content as a string.
            custom_decoder (str): The encoding to use for decoding the JSON file content.
                - Default is 'utf-8'.

        Returns:
            out (FileWriter): An instance of FileWriter configured with the provided settings.
        """

        try:

            if not isinstance(json_file, (str, bytes)):
                raise TypeError("json_file must be a string or bytes.")

            if not isinstance(custom_decoder, str):
                raise TypeError(
                    "custom_decoder must be a string representing the encoding."
                )

            if custom_decoder not in ["utf-8", "utf-16", "latin-1"]:
                raise ValueError(
                    "custom_decoder must be one of 'utf-8', 'utf-16', or 'latin-1'."
                )

            json_str: str = (
                json_file
                if isinstance(json_file, str)
                else json_file.decode(custom_decoder)
            )

            if not json_str:
                raise ValueError("JSON file content is empty.")

            json_dict: Dict[str, Any] = json.loads(json_str)

            return cls.from_dict(json_dict)

        except Exception as e:
            raise FileWriterConfigError(
                f"Error creating FileWriter from JSON: {e.__class__.__name__} -> {e}"
            ) from e

    @classmethod
    def from_yaml(
        cls, yaml_file: Union[str, bytes], custom_decoder: str = "utf-8"
    ) -> "FileWriter":
        """
        Create a FileWriter instance from a YAML file.

        Arguments:
            yaml_file (Union[str, bytes]): The path to the YAML file or the YAML content as a string.
            custom_decoder (str): The encoding to use for decoding the YAML file content.
                - Default is 'utf-8'.

        Returns:
            out (FileWriter): An instance of FileWriter configured with the provided settings.
        """
        try:

            if not isinstance(yaml_file, (str, bytes)):
                raise TypeError("yaml_file must be a string or bytes.")

            if not isinstance(custom_decoder, str):
                raise TypeError(
                    "custom_decoder must be a string representing the encoding."
                )

            if custom_decoder not in ["utf-8", "utf-16", "latin-1"]:
                raise ValueError(
                    "custom_decoder must be one of 'utf-8', 'utf-16', or 'latin-1'."
                )

            yaml_str: str = (
                yaml_file
                if isinstance(yaml_file, str)
                else yaml_file.decode(custom_decoder)
            )

            if not yaml_str:
                raise ValueError("YAML file content is empty.")

            yaml_dict: Dict[str, Any] = yaml.safe_load(yaml_str)

            return cls.from_dict(yaml_dict)

        except Exception as e:
            raise FileWriterConfigError(
                f"Error creating FileWriter from YAML: {e.__class__.__name__} -> {e}"
            ) from e

    # Configuration

    def config(
        self,
        file_paths: Union[List[Path], None] = None,
        write_mode: LogWriteMode = LogWriteMode.APPEND,
        max_file_size: int = 10 * 1024 * 1024,  # Default 10 MB
        max_rotation: int = 5,  # Default 5 rotations
        max_buffer_size: int = 0,  # Default no buffer
        retry_limit: int = 3,  # Default retry limit
        retry_delay: float = 1.0,  # Default retry delay in seconds
        backoff_factor: float = 0.2,  # Default backoff factor for retries
    ) -> None:
        """
        Configure the FileWriter with the specified parameters.

        Arguments:
            file_paths (List[Path]): List of file paths to write to.
                - Default is `None`, which means no file paths are set.
            write_mode (LogWriteMode): The mode in which to write to the files.
                - Default is `LogWriteMode.APPEND`.
            max_file_size (int): Maximum size of each log file in bytes.
                - Default is `10 * 1024 * 1024` (10 MB).
            max_rotation (int): Maximum number of rotated files to keep.
                - Default is `5`.
            max_buffer_size (int): Maximum size of the buffer in bytes.
                - Default is `0`, which means no buffer is used.
            retry_limit (int): Number of retries for writing to files.
                - Default is `3`.
            retry_delay (float): Delay between retries in seconds.
                - Default is `1.0`.
            backoff_factor (float): Factor by which the delay increases on each retry.
                - Default is `0.2 `.
        Raises:
            FileWriterConfigError: If there is an error in configuring the FileWriter.
        """
        try:

            # Force flush the buffer before reconfiguring
            self.buffer_force_flush()

            # Wait for pool to shutdown if it exists
            if self.is_pool_active():
                self.force_shutdown(wait=True)

            self.file_paths = file_paths if file_paths is not None else []
            self.write_mode = write_mode
            self.max_file_size = max_file_size
            self.max_rotation = max_rotation
            self.max_buffer_size = max_buffer_size
            self.retry_limit = retry_limit
            self.retry_delay = retry_delay
            self.backoff_factor = backoff_factor
            self._buffer = StringIO()

            # Initialize the synchronous pool
            self._init_sync_pool()

            # Initialize the thread pool executor
            if hasattr(self, "_threadpool") and self._threadpool:
                self.resume_pool()

            # If the thread pool executor does not exist, create it
            else:
                max_workers: int = (
                    min(len(self.file_paths), 4) if len(self.file_paths) > 1 else 1
                )
                if os.name == "nt":
                    max_workers: int = min(max_workers, 4)  # Windows file handle limits
                else:
                    max_workers: int = min(max_workers, os.cpu_count() or 4)
                self._threadpool = ThreadPoolExecutor(
                    max_workers=max_workers,
                )
        except Exception as e:
            self.logger.error(
                f"Error configuring FileWriter: {e.__class__.__name__} -> {e}"
            )
            raise FileWriterConfigError(
                f"Error configuring FileWriter: {e.__class__.__name__} -> {e}"
            ) from e

    def config_from_dict(
        self,
        config: Dict[str, Any],
    ) -> None:
        """
        Configure the FileWriter using a dictionary of parameters.

        Arguments:
            config (Dict[str, Any]): Dictionary containing configuration parameters.

        Defaults:
        ----------
        **file_paths (List[Path]):**
            - List of file paths to write to.
            - Default is `None`, which means no file paths are set.
        **write_mode (LogWriteMode):**
            - The mode in which to write to the files.
            - Default is `LogWriteMode.APPEND`.
        **max_file_size (int):**
            - Maximum size of each log file in bytes.
            - Default is `10 * 1024 * 1024` (10 MB).
        **max_rotation (int):**
            - Maximum number of rotated files to keep.
            - Default is `5`.
        **max_buffer_size (int):**
            - Maximum size of the buffer in bytes.
            - Default is `0`, which means no buffer is used.
        **retry_limit (int):**
            - Number of retries for writing to files.
            - Default is `3`.
        **retry_delay (float):**
            - Delay between retries in seconds.
            - Default is `1.0`.
        **backoff_factor (float):**
            - Factor by which the delay increases on each retry.
            - Default is `0.2`.

        Raises:
            FileWriterConfigError: If there is an error in configuring the FileWriter.
        """
        try:

            if not isinstance(config, dict):
                raise ValueError("Configuration must be a dictionary")
            if not config:
                raise ValueError("Configuration dictionary cannot be empty")

            for key in config:
                if key not in LIST_OF_NECESSARY_KEYS:
                    raise ValueError(
                        f"Invalid configuration key: {key}. "
                        f"Allowed keys are: {', '.join(LIST_OF_NECESSARY_KEYS)}"
                    )

            # Extract configuration parameters from the dictionary
            file_paths: Union[List[Path], None] = config.get("file_paths", None)
            write_mode: LogWriteMode = config.get("write_mode", LogWriteMode.APPEND)
            max_file_size: int = config.get(
                "max_file_size", 10 * 1024 * 1024
            )  # Default 10 MB
            max_rotation: int = config.get("max_rotation", 5)  # Default 5 rotations
            max_buffer_size: int = config.get("max_buffer_size", 0)  # Default no buffer
            retry_limit: int = config.get("retry_limit", 3)  # Default retry limit
            retry_delay: float = config.get(
                "retry_delay", 1.0
            )  # Default retry delay in seconds
            backoff_factor: float = config.get(
                "backoff_factor", 0.2
            )  # Default backoff factor for retries

            # Call the config method with the extracted parameters
            self.config(
                file_paths=file_paths,
                write_mode=write_mode,
                max_file_size=max_file_size,
                max_rotation=max_rotation,
                max_buffer_size=max_buffer_size,
                retry_limit=retry_limit,
                retry_delay=retry_delay,
                backoff_factor=backoff_factor,
            )
        except Exception as e:
            self.logger.error(f"Error configuring FileWriter from dict: {e}")
            raise FileWriterConfigError(
                f"Error configuring FileWriter from dict: {e}"
            ) from e

    def config_from_json(
        self, json_file: Union[str, bytes], custom_decoder: str = "utf-8"
    ) -> None:
        """
        Configure the FileWriter using a JSON file.

        Arguments:
            json_file (Union[str, bytes]): The path to the JSON file or the JSON content as a string.
            custom_decoder (str): The encoding to use for decoding the JSON file content.
                - Default is 'utf-8'.
        """
        try:
            if not isinstance(json_file, (str, bytes)):
                raise TypeError("json_file must be a string or bytes.")

            if not isinstance(custom_decoder, str):
                raise TypeError(
                    "custom_decoder must be a string representing the encoding."
                )

            if custom_decoder not in ["utf-8", "utf-16", "latin-1"]:
                raise ValueError(
                    "custom_decoder must be one of 'utf-8', 'utf-16', or 'latin-1'."
                )

            json_str: str = (
                json_file
                if isinstance(json_file, str)
                else json_file.decode(custom_decoder)
            )

            if not json_str:
                raise ValueError("JSON file content is empty.")

            config_dict: Dict[str, Any] = json.loads(json_str)
            self.config_from_dict(config_dict)
        except Exception as e:
            raise FileWriterConfigError(
                f"Error updating FileReader configuration from JSON: {e.__class__.__name__} -> {e}"
            ) from e

    def config_from_yaml(
        self, yaml_file: Union[str, bytes], custom_decoder: str = "utf-8"
    ) -> None:
        """
        Configure the FileWriter using a YAML file.

        Arguments:
            yaml_file (Union[str, bytes]): The path to the YAML file or the YAML content as a string.
            custom_decoder (str): The encoding to use for decoding the YAML file content.
                - Default is 'utf-8'.
        """
        try:
            if not isinstance(yaml_file, (str, bytes)):
                raise TypeError("yaml_file must be a string or bytes.")

            if not isinstance(custom_decoder, str):
                raise TypeError(
                    "custom_decoder must be a string representing the encoding."
                )

            if custom_decoder not in ["utf-8", "utf-16", "latin-1"]:
                raise ValueError(
                    "custom_decoder must be one of 'utf-8', 'utf-16', or 'latin-1'."
                )

            yaml_str: str = (
                yaml_file
                if isinstance(yaml_file, str)
                else yaml_file.decode(custom_decoder)
            )

            if not yaml_str:
                raise ValueError("YAML file content is empty.")

            config_dict: Dict[str, Any] = yaml.safe_load(yaml_str)
            self.config_from_dict(config_dict)
        except Exception as e:
            raise FileWriterConfigError(
                f"Error updating FileReader configuration from YAML: {e.__class__.__name__} -> {e}"
            ) from e

    # Reset

    def reset_to_defaults(self) -> None:
        """
        Reset the FileWriter to its default configuration.
        This method will reset all parameters to their default values.
        """
        try:
            self.clear_all()  # Clear all resources before resetting

            self.config(
                file_paths=None,
                write_mode=LogWriteMode.APPEND,
                max_file_size=10 * 1024 * 1024,  # Default 10 MB
                max_rotation=5,  # Default 5 rotations
                max_buffer_size=0,  # Default no buffer
                retry_limit=3,  # Default retry limit
                retry_delay=1.0,  # Default retry delay in seconds
                backoff_factor=0.2,  # Default backoff factor for retries
            )
        except Exception as e:
            self.logger.error(
                f"Error resetting FileWriter to defaults: {e.__class__.__name__} -> {e}"
            )
            raise FileWriterResetError(
                f"Error resetting FileWriter to defaults: {e.__class__.__name__} -> {e}"
            ) from e
