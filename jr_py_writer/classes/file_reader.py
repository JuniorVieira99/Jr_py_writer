# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
from io import TextIOWrapper

import logging
import os
import asyncio
import time
import json

from typing import Generator, Iterator, List, Union, Dict, Final, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from functools import partial

# Third-party imports
import yaml

# Utilities
from jr_py_writer.utils.utilities import batcher, batcher_with_gcmanager
from jr_py_writer.utils.module_enums import LogWriteMode
from jr_py_writer.classes.reader_result import ReaderResultGenerator, ReaderResultStr
from jr_py_writer.classes.reader_result_pack import ReaderResultPack

# Exceptions
from jr_py_writer.exceptions.exceptions_file_reader import (
    FileReaderConstructionError,
    FileReaderSettingsError,
    FileReaderReadError,
    FileReaderAsyncReadError,
    FileReaderSyncPoolInitError,
    FileReaderSyncPoolCleanupError,
    FileReaderShutdownError,
    FileReaderResumeError,
    FileReaderConfigError
)


# ----------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------

LIST_NECESSARY_KEYS: Final[List[str]] = [
    "file_paths",
    "retry_limit",
    "retry_delay",
    "backoff_factor",
    "logger"
]

class FileReader:
    """
    FileReader Class
    ================
    The `FileReader` class is designed to handle file reading operations with support for synchronous, asynchronous, and generator-based approaches.
    It provides robust error handling, retry mechanisms, and thread-safe operations for reading files. 
    This class is particularly useful for managing multiple file paths and reading their contents efficiently.

    Attention:
    ---------
    It is recommended to use the `with` statement when working with this class to ensure proper resource management and cleanup.
    Otherwise, you must call `clear_all()` to release resources and close files properly.
    Example usage:
    ```python
    with FileReader(file_paths=["file1.txt", "file2.txt"]) as reader:
        content = reader.read_log()
    ```
    or
    ```python
    reader = FileReader(file_paths=["file1.txt", "file2.txt"])
    content = reader.read_log()
    reader.clear_all()
    ```

    Notes:
    ------
    - Will automatically handle error of path not found, file not readable, etc.
        - Error will be presented in the dictionary as the value for the path.
    - Supports both synchronous and asynchronous reading of files.
    - Provides a generator-based approach for reading files line by line.

    Attributes:
        file_paths (List[Path]):
            A list of file paths to be read.
        write_mode (LogWriteMode):
            The mode in which files are opened for reading.
        retry_limit (int):
            The number of retries for file read operations in case of failure.
        retry_delay (float):
            The delay in seconds between retries for file read operations.
        backoff_factor (float):
            The factor by which the retry delay increases after each retry.
        logger (logging.Logger):
            The logger instance used for logging errors and warnings.
    
    Example:
        ```python
        # Initialize FileReader with file paths
        file_paths = [Path("file1.txt"), Path("file2.txt")]
        reader = FileReader(file_paths=file_paths, write_mode=LogWriteMode.READ)
        
        # Read files synchronously
        with reader:
            content: Dict[Path, str] = reader.read_log() 

        # Manual iteration over generators
        for path, gen in generator_content.items():
            print(f"Content of {path} (line by line):")
            for line in gen:
                print(line)

        # You can also use the `unpacker` utility to unpack the generator content
        result: Dict[Path, str] = reader.unpack_generator(generator_content)

        # Read files asynchronously
        async def read_files_async():
            async with reader:
                async_content: Dict[Path, str] = await reader.async_read_log()
        asyncio.run(read_files_async())
        
        # Shutdown thread pool
        reader.force_shutdown()

        # Clear all resources
        reader.clear_all()
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
        "_temp_sync_pool",
        "_lock",
        "_threadpool",
        "_logger",
    )


    # --------------
    # Attributes

    _file_paths: List[Path]
    _write_mode: LogWriteMode
    _retry_limit: int
    _retry_delay: float
    _backoff_factor: float
    _temp_sync_pool: Dict[Path, TextIOWrapper]
    _lock: Lock
    _threadpool: ThreadPoolExecutor
    _logger: logging.Logger


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
    def logger(self) -> logging.Logger:
        """
        Returns the logger instance associated with the FileReader.
        """
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(__name__)
        return self._logger


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
            raise FileReaderSettingsError(
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
            raise FileReaderSettingsError(
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
            raise FileReaderSettingsError(
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
            raise FileReaderSettingsError(
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
            raise FileReaderSettingsError(
                f"Invalid backoff factor: {e.__class__.__name__} -> {e}"
            ) from e

    @logger.setter
    def logger(self, logger: logging.Logger) -> None:
        """
        Sets the logger instance associated with the FileReader.

        Arguments:
            logger (logging.Logger): The logger instance to set.
        """
        try:
            if not isinstance(logger, logging.Logger):
                raise ValueError("Logger must be an instance of logging.Logger")

            self._logger = logger
        except Exception as e:
            raise FileReaderSettingsError(
                f"Invalid logger: {e.__class__.__name__} -> {e}"
            ) from e


    # --------------
    # Constructor

    def __init__(
        self,
        file_paths: List[Union[Path, str]],
        write_mode: LogWriteMode = LogWriteMode.READ,
        retry_limit: int = 2,
        retry_delay: float = 0.1,
        backoff_factor: float = 0.2,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialize the FileReader with file paths, log level, and log format.

        Arguments:
            file_paths (List[Union[Path, str]]):
                A list of file paths for logging.
            write_mode (LogWriteMode):
                The write mode for file logging.
                    - Default is LogWriteMode.READ.
            retry_limit (int):
                The number of retries for file operations.
                    - Default is 2.
            retry_delay (float):
                The delay in seconds between retries for file operations.
                    - Default is 0.1 seconds.
            backoff_factor (float):
                The backoff factor for retry delays.
                    - Default is 0.2 times the retry delay.
            logger (logging.Logger | None):
                An optional logger instance to use for logging.
                    - If None, a default logger will be created.
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

        except Exception as e:
            self.logger.error(
                f"Error initializing FileReader: {e.__class__.__name__} -> {e}"
            )
            raise FileReaderConstructionError(
                f"Error initializing FileReader: {e.__class__.__name__} -> {e}"
            ) from e


    # --------------
    # Magic Methods

    def __str__(self) -> str:
        """
        Returns a string representation of the FileReader.

        Returns:
            str: A string representation of the FileReader.
        """
        return (
            f"FileReader(file_paths={self.file_paths}, "
            f"write_mode={self.write_mode})"
            f"retry_limit={self.retry_limit}, "
            f"retry_delay={self.retry_delay})"
        )

    def __eq__(self, other: object) -> bool:
        """
        Checks if two FileReader instances are equal.

        Arguments:
            other (object): The other instance to compare.

        Returns:
            bool: True if both instances are equal, False otherwise.
        """
        if not isinstance(other, FileReader):
            return False
        return (
            self.file_paths == other.file_paths
            and self.write_mode == other.write_mode
            and self.retry_limit == other.retry_limit
            and self.retry_delay == other.retry_delay
        )

    def __ne__(self, other: object) -> bool:
        """
        Checks if two FileReader instances are not equal.

        Arguments:
            other (FileReader): The other FileReader instance to compare.

        Returns:
            bool: True if both instances are not equal, False otherwise.
        """
        return not self.__eq__(other)

    def __len__(self) -> int:
        """
        Returns the number of file paths in the FileReader.

        Returns:
            int: The number of file paths.
        """
        return len(self.file_paths)

    def __iter__(self) -> Iterator[Path]:
        """
        Returns an iterator over the file paths in the FileReader.

        Returns:
            Iterator[Path]: An iterator over the file paths.
        """
        if self.file_paths is None:
            raise ValueError("File paths list is empty. Cannot iterate.")
        return iter(self.file_paths)

    def __del__(self):
        """Cleanup resources when object is destroyed."""
        try:
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
        Checks if a file path is in the FileReader.

        Arguments:
            item (Path): The file path to check.

        Returns:
            bool: True if the file path is in the FileReader, False otherwise.
        """
        if not isinstance(item, Path):
            raise ValueError(f"Item must be a Path object, got {type(item).__name__}")
        return item in self.file_paths

    def __enter__(self):
        """
        Context manager enter method for FileReader.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit method for FileReader.
        """

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
        Asynchronous context manager enter method for FileReader.
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Asynchronous context manager exit method.
        """

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
            raise FileReaderSyncPoolCleanupError(
                f"Error clearing sync pool: {e.__class__.__name__} -> {e}"
            ) from e
        

    # --------------
    # ResultPack Handler

    def _result_pack_handler(
        self,
        result_pack: ReaderResultPack,
        content: str,
        path,
        exception: Exception | None = None
    ) -> ReaderResultPack:
        """
        Handle the result pack by adding a ReaderResult to it.

        Arguments:
            result_pack (ReaderResultPack): The result pack to add the result to.
            content (str): The content of the file.
            path (Path): The file path for logging.
            exception (Exception | None): An optional exception that occurred during reading.

        Returns:
            out (ReaderResultPack) : The updated result pack with the new ReaderResult.
        """
        if len(content) == 0 and exception is None:
            self.logger.warning(f"File {path} is empty.")
            result_pack.add_result(
                ReaderResult(
                    file_path=path,
                    content="",
                    exception=FileReaderReadError(f"File {path} is empty.")
                )
            )
        else:
            result_pack.add_result(
                ReaderResult(
                    file_path=path,
                    content=content,
                    exception=exception
                )
            )
       
        return result_pack


    # --------------
    # File Reading Methods


    # Sync

    def _read_file(self, file: TextIOWrapper, path: Path) -> str:
        """
        Read the content of a file.

        Arguments:
            file (TextIOWrapper): The file object to read from.
            path (Path): The file path for logging.

        Returns:
            out (str) : The content of the file.
        """
        with self._lock:  # Ensure thread-safe access to the file
            file_str: str = file.read()
            if not file_str:
                self.logger.warning(f"File {path} is a empty file.")
            return file_str


    def _read_file_retries(self, file: TextIOWrapper, path: Path) -> str:
        """
        Read the content of a file with retry logic.

        Arguments:
            file (TextIOWrapper): The file object to read from.
            path (Path): The file path for logging.

        Returns:
            out (str) : The content of the file.
        """
        if self.retry_limit <= 0:
            return self._read_file(file, path)

        counter: int = 0
        while counter < self.retry_limit:
            try:
                return self._read_file(file, path)
            except Exception as e:
                counter += 1
                if counter >= self.retry_limit:
                    raise RuntimeError(
                        f"Failed to read from {file} after {self.retry_limit} attempts: {e.__class__.__name__} -> {e}"
                    ) from e

                # Wait before retrying
                if self.retry_delay > 0:
                    if self.backoff_factor:
                        # Exponential backoff
                        exp_time: float = self.retry_delay * (
                            self.backoff_factor ** (counter - 1)
                        )
                        self.logger.warning(
                            f"Retrying to read from {file} in {exp_time:.2f} seconds (attempt {counter}/{self.retry_limit})"
                        )
                        time.sleep(exp_time)
                    else:
                        # Linear backoff
                        self.logger.warning(
                            f"Retrying to read from {file} in {self.retry_delay:.2f} seconds (attempt {counter}/{self.retry_limit})"
                        )
                        time.sleep(self.retry_delay)
        return ""


    def _read_batch(self, path_batch: List[Path]) -> ReaderResultPack:
        """
        Read the content of a batch of files.

        Arguments:
            path_batch (List[Path]): The list of file paths to read from.

        Returns:
            out (ReaderResultPack) : A pack of ReaderResult objects containing file paths and their content or exceptions.
        """
        result_pack: ReaderResultPack = ReaderResultPack()
        for path in path_batch:
            try:
                out_str: str = self._read_file_prep(path)
                # Update the results dictionary with the ReaderResult
                result_pack = self._result_pack_handler(
                    result_pack=result_pack,
                    content=out_str,
                    path=path
                )
                
            except Exception as e:
                self.logger.error(f"Error reading file {path}: {e}")
                # If an exception occurs, log it and set the exception in results
                result_pack = self._result_pack_handler(
                    result_pack=result_pack,
                    content="",
                    path=path,
                    exception=FileReaderReadError(
                        f"Error reading file {path}: {e.__class__.__name__} -> {e}"
                    )
                )
        return result_pack


    def _read_file_prep(self, path: Path) -> str:
        """
        Read the content of a file using the synchronous pool.

        Arguments:
            path (Path): The file path to read from.

        Returns:
            out (str) : The content of the file.
        """
        try:

            if not path.exists():
                self.logger.error(f"File {path} does not exist.")
                raise FileExistsError(f"File {path} does not exist.")

            file: TextIOWrapper | None = self._temp_sync_pool.get(path, None)
            
            # If file not in pool, then lazy initialize it
            if not file:
                self.logger.warning(
                    f"File {path} is not in the temporary sync pool."
                )
                self.logger.debug(f"Opening file {path} for reading...")
                file = open(path, self.write_mode.value, encoding="utf-8")
            
                with self._lock:
                    self._temp_sync_pool[path] = file

            # Check if the file is closed or not readable
            # Unlike to happen, but just in case
            if file.closed:
                self.logger.warning(f"File {path} is closed. Reopening it...")
                # Reopen the file if it is closed
                file = open(path, "r", encoding="utf-8")

            if not file.readable():
                self.logger.error(f"File {path} is not readable.")
                raise IOError(f"File {path} is not readable.")
            
            return self._read_file_retries(file, path)

        except Exception as e:
            self.logger.error(f"Error reading file {path}: {e}")
            raise


    def _reader(
        self
    ) -> ReaderResultPack:
        """
        Read the content of all files in the file paths.

        Returns:
            out (ReaderResultPack) : A pack of ReaderResult objects containing file paths and their content or exceptions.
        """
        # Send to ThreadPool
        futures = {
            self._threadpool.submit(partial(self._read_file_prep, path)): path for path in self.file_paths
        }

        # Initialize Dict
        result_pack: ReaderResultPack = ReaderResultPack()
        
        # Handle Results from the futures
        for future in as_completed(futures):
            path = futures[future]
            # Get the result from the future
            try:
                # Get the output string from the future
                out_str: str = future.result()
                # Update the results dictionary with the ReaderResult
                result_pack = self._result_pack_handler(
                    result_pack=result_pack,
                    content=out_str,
                    path=path
                )
                
            # If an exception occurs, log it and set the exception in results
            except Exception as e:
                self.logger.error(f"Error reading files : {e.__class__.__name__} -> {e}")
                # Update the result pack with the exception
                result_pack = self._result_pack_handler(
                    result_pack=result_pack,
                    content="",
                    path=path,
                    exception=FileReaderReadError(
                        f"Error reading file: {e.__class__.__name__} -> {e}"
                    )
                )
        return result_pack


    def _reader_handler(self) -> ReaderResultPack:
        """
        Read the content of all files in the file paths in batches.

        Returns:
            out (ReaderResultPack) : A pack of ReaderResult objects containing file paths and their content or exceptions.
        """
        # If the number of file paths is less than 50, use the _reader method.
        if len(self.file_paths) < 50:
            result_pack: ReaderResultPack = self._reader()
            self.logger.debug(
                f"Read {len(result_pack)} files successfully."
            )
            return result_pack
        
        # Initialize batches of paths
        batches_of_paths: List[List[Path]] = []

        # If the number of file paths is greater than 50, use the batcher function.
        if len(self.file_paths) > 50 and len(self.file_paths) <= 1000:
            batches_of_paths: List[List[Path]] = list(batcher(self.file_paths))
        
        # If the number of file paths is greater than 1000, use the batcher_with_gcmanager function.
        elif len(self.file_paths) > 1000:
            batches_of_paths: List[List[Path]] = list(
                batcher_with_gcmanager(self.file_paths)
            )

        # Send to Pool
        futures = {
            self._threadpool.submit(partial(self._read_batch, path_batch)): path_batch
            for path_batch in batches_of_paths
        }

        # Initialize ReaderResultPack
        result_pack: ReaderResultPack = ReaderResultPack()

        # Handle the results from the futures
        for future in as_completed(futures):
            paths: List[Path] = futures[future]
            for path in paths:
                try:
                    # Get the result from the future
                    out_result: ReaderResultPack = future.result()
                    # Update the result pack with the ReaderResultPack
                    # Magic method add allows this
                    result_pack += out_result

                # Safely measure only, this is unlikely to happen since we handle exceptions in the level 
                # of creation of the ReaderResultPack
                except Exception as e:
                    self.logger.error(f"Error reading files in batch: {e}")
                    # If an exception occurs, log it and set the exception in results
                    if path is not None:  # Ensure path is valid before using it
                        result_pack = self._result_pack_handler(
                            result_pack=result_pack,
                            content="",
                            path=path,
                            exception=FileReaderReadError(
                                f"Error reading file {path}: {e.__class__.__name__} -> {e}"
                            )
                        )
                    else:
                        raise FileReaderReadError(
                            f"Error reading files in batch: {e.__class__.__name__} -> {e}"
                        ) from e
                    
        # Ensure all paths in results are valid
        self.logger.debug(f"Read {len(result_pack)} files successfully.")
        return result_pack


    # Generator Sync

    def _read_generator(
        self,
        file: TextIOWrapper,
        path: Path
    ) -> Generator[str, None, None]:
        """
        Generator to read the content of a file line by line.

        Arguments:
            file (TextIOWrapper): The file object to read from.
            path (Path): The file path for logging.

        Yields:
            out (str) : The content of the file line by line.
        """
        try:
            with self._lock:  # Ensure thread-safe access to the file
                for line in file:
                    yield line.strip()
        except Exception as e:
            self.logger.error(f"Error reading file {path}: {e}")
            raise FileReaderReadError(f"Error reading file {path}: {e}") from e


    def _read_generator_retries(
        self,
        file: TextIOWrapper,
        path: Path
    ) -> Generator[str, None, None]:
        """
        Generator to read the content of a file line by line with retry logic.

        Arguments:
            file (TextIOWrapper): The file object to read from.
            path (Path): The file path for logging.
        
        Yields:
            out (str) : The content of the file line by line.
        """
        if self.retry_limit <= 0:
            yield from self._read_generator(file, path)
            return

        counter: int = 0
        while counter < self.retry_limit:
            try:
                yield from self._read_generator(file, path)
                return
            except Exception as e:
                counter += 1
                if counter >= self.retry_limit:
                    self.logger.error(
                        f"Failed to read from {file} after {self.retry_limit} attempts: {e}"
                    )
                    raise RuntimeError(
                        f"Failed to read from {file} after {self.retry_limit} attempts: {e}"
                    ) from e

                # Wait before retrying
                if self.retry_delay > 0:
                    if self.backoff_factor:
                        # Exponential backoff
                        exp_time: float = self.retry_delay * (
                            self.backoff_factor ** (counter - 1)
                        )
                        self.logger.warning(
                            f"Retrying to read from {file} in {exp_time:.2f} seconds (attempt {counter}/{self.retry_limit})"
                        )
                        time.sleep(exp_time)
                    else:
                        # Linear backoff
                        self.logger.warning(
                            f"Retrying to read from {file} in {self.retry_delay:.2f} seconds (attempt {counter}/{self.retry_limit})"
                        )
                        time.sleep(self.retry_delay)


    def _read_generator_prep(
        self,
        path: Path
    ) -> Generator[str, None, None]:
        """
        Prepare the generator for reading the content of a file.

        Arguments:
            path (Path): The file path to read from.
        
        Returns:
            out (Generator[str, None, None]) : A generator yielding the content of the file            

        """

        try:
            # Check if the path exists
            if not path.exists():
                self.logger.error(f"File {path} does not exist.")
                yield "File not found."
                return

            # Get the file from the temporary sync pool
            file: TextIOWrapper | None = self._temp_sync_pool.get(path)
            
            # If file not in pool, then lazy initialize it
            if not file:
                    self.logger.warning(
                        f"File {path} is not in the temporary sync pool."
                    )
                    self.logger.info(f"Opening file {path} for reading...")
                    file = open(path, self.write_mode.value, encoding="utf-8")

                    # Send to sync pool
                    with self._lock:
                        self._temp_sync_pool[path] = file

            # Check if the file is closed or not readable
            # Unlike to happen, but just in case
            if file.closed:
                self.logger.warning(f"File {path} is closed. Reopening it...")
                # Reopen the file if it is closed
                file = open(path, "r", encoding="utf-8")

            if not file.readable():
                self.logger.error(f"File {path} is not readable.")
                yield "File is not readable."
                return
            
            for line in self._read_generator_retries(file, path):
                yield line
            return

        except Exception as e:
            self.logger.error(f"Error reading file {path}: {e}")
            raise FileReaderReadError(f"Error reading file {path}: {e}") from e


    def _reader_generator(
        self,
    ) -> Dict[Path, Generator[str, None, None]]:
        """
        Read the content of all files in the file paths as generators.

        Returns:
            out (Dict[Path, Generator[str, None, None]]) : A dictionary mapping file paths to their content as generators.
        """
        if not self.file_paths:
            raise ValueError("File paths list is empty. Cannot read files.")

        futures = {
            self._threadpool.submit(partial(self._read_generator_prep, path)): path for path in self.file_paths
        }

        results: Dict[Path, Generator[str, None, None]] = {}
        for future in as_completed(futures):
            path = futures[future]
            # Get the result from the future
            try:
                out_gen: Generator[str, None, None] = future.result()
                if out_gen is not None:
                    results[path] = out_gen
            except Exception as e:
                self.logger.error(f"Error reading files : {e}")
                raise FileReaderReadError(f"Error reading files: {e}") from e
        return results


    def _reader_batch_generator(
        self,
        path_batch: List[Path]
    ) -> Dict[Path, Generator[str, None, None]]:
        """
        Read the content of a batch of files as generators.

        Arguments:
            path_batch (List[Path]): The list of file paths to read from.

        Returns:
            out (Dict[Path, Generator[str, None, None]]) : A dictionary mapping file paths to their content as generators.
        """
        results: Dict[Path, Generator[str, None, None]] = {}
        for path in path_batch:
            try:
                out_gen: Generator[str, None, None] = self._read_generator_prep(path)
                if out_gen is not None:
                    results[path] = out_gen
            except Exception as e:
                self.logger.error(f"Error reading file {path}: {e}")
                results[path] = (line for line in [f"Error reading file : {e}"])
        return results


    def _reader_generator_handler(self) -> Dict[Path, Generator[str, None, None]]:
        """
        Read the content of all files in the file paths in batches as generators.

        Returns:
            out (Dict[Path, Generator[str, None, None]]) : A dictionary mapping file paths to their content as generators.
        """

        # If the number of file paths is less than 50, use the _reader_generator method.
        if len(self.file_paths) < 50:
            return self._reader_generator()

        # Initialize batches of paths
        batches_of_paths: List[List[Path]] = []

        # If the number of file paths is greater than 50, use the batcher function.
        if len(self.file_paths) > 50 and len(self.file_paths) <= 1000:
            batches_of_paths: List[List[Path]] = list(batcher(self.file_paths))
        # If the number of file paths is greater than 1000, use the batcher_with_gcmanager function.
        elif len(self.file_paths) > 1000:
            batches_of_paths: List[List[Path]] = list(
                batcher_with_gcmanager(self.file_paths)
            )

        # Initialize results dictionary
        results: Dict[Path, Generator[str, None, None]] = {}

        # Send to Pool
        futures = {
            self._threadpool.submit(partial(self._reader_batch_generator, path_batch)): path_batch
            for path_batch in batches_of_paths
        }
        # Handle the results from the futures
        for future in as_completed(futures):
            try:
                results.update(future.result())
            except Exception as e:
                self.logger.error(f"Error reading files in batch: {e}")
                raise FileReaderReadError(
                    f"Error reading files in batch: {e.__class__.__name__} -> {e}"
                ) from e
            
        # Return the results dictionary containing file paths and their content
        self.logger.debug(f"Read {len(results)} files successfully.")
        return results


    # Async

    async def _async_read(self) -> ReaderResultPack:
        """
        Asynchronously read the content of all files in the file paths.

        Returns:
            out (ReaderResultPack) : A pack of ReaderResult objects containing file paths and their content or exceptions.
        """
        if not self.file_paths:
            raise ValueError("File paths list is empty. Cannot read files.")

        def read_all_files():
            result_pack: ReaderResultPack = ReaderResultPack()
            for path in self.file_paths:
                try:
                    out_str = self._read_file_prep(path)
                    # Update the result pack with the ReaderResult
                    result_pack = self._result_pack_handler(
                        result_pack, out_str, path
                    )

                except Exception as e:
                    self.logger.error(f"Error reading file {path}: {e}")
                    # Update the result pack with the exception
                    result_pack = self._result_pack_handler(
                        result_pack, "", path, FileReaderReadError(
                            f"Error reading file {path}: {e.__class__.__name__} -> {e}"
                        )
                    )
            
            return result_pack

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._threadpool, read_all_files)


    async def _async_read_batch(
        self, path_batch: List[Path]
    ) -> ReaderResultPack:
        """
        Asynchronously read the content of a batch of files.

        Arguments:
            path_batch (List[Path]): The list of file paths to read from.

        Returns:
            out (ReaderResultPack) : A pack of ReaderResult objects containing file paths and their content or exceptions.
        """
        # Use asyncio to send file read tasks concurrently
        return await asyncio.get_event_loop().run_in_executor(
            self._threadpool, partial(self._read_batch, path_batch)
        )


    async def _async_reader_handler(self) -> ReaderResultPack:
        """
        Asynchronously read the content of all files in the file paths in batches.

        Returns:
            out (ReaderResultPack) : A pack of ReaderResult objects containing file paths and their content or exceptions.
        """
        # If the number of file paths is less than 50, use the _async_read method.
        if len(self.file_paths) < 50:
            result_pack: ReaderResultPack = await self._async_read()
            self.logger.debug(f"Read {len(result_pack)} files successfully.")
            return result_pack
        
        # Initialize batches of paths
        batches_of_paths: List[List[Path]] = []

        # If the number of file paths is greater than 50, use the batcher function.
        if len(self.file_paths) > 50 and len(self.file_paths) <= 1000:
            batches_of_paths: List[List[Path]] = list(batcher(self.file_paths))

        # If the number of file paths is greater than 1000, use the batcher_with_gcmanager function.
        elif len(self.file_paths) > 1000:
            batches_of_paths: List[List[Path]] = list(
                batcher_with_gcmanager(self.file_paths)
            )

        # Init ReaderResultPack
        result_pack: ReaderResultPack = ReaderResultPack()

        # Send to Pool
        for path_batch in batches_of_paths:
            try:
                batch_results: ReaderResultPack = await self._async_read_batch(path_batch)
                result_pack += batch_results
            except Exception as e:
                self.logger.error(f"Error reading files in batch: {e}")
                raise FileReaderReadError(
                    f"Error reading files in batch: {e.__class__.__name__} -> {e}"
                ) from e
            
        # Return the result pack containing file paths and their content
        self.logger.debug(f"Read {len(result_pack)} files successfully.")
        return result_pack


    # Async Generator

    async def _async_reader_generator(
        self,
    ) -> Dict[Path, Generator[str, None, None]]:

        """
        Asynchronously read the content of all files in the file paths as generators.

        Returns:
            out (Dict[Path, Generator[str, None, None]]) : A dictionary mapping file paths to their content as generators.
        """
        if not self.file_paths:
            raise ValueError("File paths list is empty. Cannot read files.")

        def read_all_files():
            results = {}
            for path in self.file_paths:
                try:
                    out_gen = self._read_generator_prep(path)
                    if out_gen is not None:
                        results[path] = out_gen
                except Exception as e:
                    self.logger.error(f"Error reading file {path}: {e}")
                    results[path] = (line for line in [f"Error reading file: {e}"])
            return results

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._threadpool, read_all_files)


    async def _async_read_batch_generator(
        self, 
        path_batch: List[Path]
    ) -> Dict[Path, Generator[str, None, None]]:
        """
        Asynchronously read the content of a batch of files as generators.

        Arguments:
            path_batch (List[Path]): The list of file paths to read from.

        Returns:
            out (Dict[Path, Generator[str, None, None]]) : A dictionary mapping file paths to their content as generators.
        """
        # Use asyncio to send file read tasks concurrently
        return await asyncio.get_event_loop().run_in_executor(
            self._threadpool, partial(self._reader_batch_generator, path_batch)
        )
    

    async def _async_reader_generator_handler(
        self
    ) -> Dict[Path, Generator[str, None, None]]:
        """
        Asynchronously read the content of all files in the file paths in batches as generators.

        Returns:
            out (Dict[Path, Generator[str, None, None]]) : A dictionary mapping file paths to their content as generators.
        """

        # If the number of file paths is less than 50, use the _async_reader_generator method.
        if len(self.file_paths) < 50:
            return await self._async_reader_generator()
        
        # Initialize batches of paths
        batches_of_paths: List[List[Path]] = []

        # If the number of file paths is greater than 50, use the batcher function.
        if len(self.file_paths) > 50 and len(self.file_paths) <= 1000:
            batches_of_paths: List[List[Path]] = list(batcher(self.file_paths))
        # If the number of file paths is greater than 1000, use the batcher_with_gcmanager function.
        elif len(self.file_paths) > 1000:
            batches_of_paths: List[List[Path]] = list(
                batcher_with_gcmanager(self.file_paths)
            )

        # Handle the results from the batches
        results: Dict[Path, Generator[str, None, None]] = {}
        for path_batch in batches_of_paths:
            try:
                batch_results: Dict[Path, Generator[str, None, None]] = await self._async_read_batch_generator(path_batch)
                results.update(batch_results)
            except Exception as e:
                self.logger.error(f"Error reading files in batch: {e}")
                raise FileReaderReadError(
                    f"Error reading files in batch: {e.__class__.__name__} -> {e}"
                ) from e
            
        # Return the results dictionary containing file paths and their content
        self.logger.debug(f"Read {len(results)} files successfully.")
        return results


    # --------------
    # Methods

    # Clear

    def clear_all(self) -> None:
        """
        Clear all file paths and the temporary sync pool.
        This method is useful for resetting the FileReader state.
        """
        # Clear file paths
        if hasattr(self, "_file_paths"):
            self._file_paths = []

        # Clear the synchronous pool
        self.clear_sync_pool()

        # Shutdown the thread pool executor
        if hasattr(self, "_threadpool") and self._threadpool:
            if not self._threadpool._shutdown:
                self._threadpool.shutdown(wait=True)


    # Reader

    def read(self) -> ReaderResultPack:
        """
        Read the content of all files in the file paths.

        Returns:
            out (ReaderResultPack) : A pack of ReaderResult objects containing file paths and their content or exceptions.
        
        Example:
        ```python
        my_file_reader = FileReader(
            file_paths=["/path/to/file1.txt", "/path/to/file2.txt"],
        )
        results: ReaderResultPack = my_file_reader.read()
        # Print summary of results
        print(results.get_summary)
        # Or, get all successful results
        successful_results: List[ReaderResult] = results.get_successful_results()
        # Or, get all failed results
        failed_results: List[ReaderResult] = results.get_failed_results()
        # Or, get all results
        all_results: List[ReaderResult] = results.get_all_results()
        ```
        """
        try:
            if not self.file_paths:
                raise ValueError("File paths list is empty. Cannot read files.")
            
            if self.write_mode not in (LogWriteMode.READ, LogWriteMode.READ_WRITE):
                raise ValueError(
                    f"FileReader is not configured for reading. Use LogWriteMode.READ or LogWriteMode.READ_WRITE."
                    f"\n\tCurrent mode: {self.write_mode.value}\n"
                )
            
            return self._reader_handler()
        except Exception as e:
            self.logger.error(f"Error reading files: {e.__class__.__name__} -> {e}")
            raise FileReaderReadError(f"Error reading files: {e.__class__.__name__} -> {e}") from e
    

    async def async_read(self) -> ReaderResultPack:
        """
        Asynchronously read the content of all files in the file paths.

        Returns:
            out (ReaderResultPack) : A pack of ReaderResult objects containing file paths and their content or exceptions.
        """
        try:
            if not self.file_paths:
                raise ValueError("File paths list is empty. Cannot read files.")
            
            if self.write_mode not in (LogWriteMode.READ, LogWriteMode.READ_WRITE):
                raise ValueError(
                    f"FileReader is not configured for reading. Use LogWriteMode.READ or LogWriteMode.READ_WRITE."
                    f"\n\tCurrent mode: {self.write_mode.value}\n"
                )

            return await self._async_reader_handler()
        except Exception as e:
            self.logger.error(f"Error reading files asynchronously: {e.__class__.__name__} -> {e}")
            raise FileReaderAsyncReadError(f"Error reading files asynchronously: {e.__class__.__name__} -> {e}") from e


    # Generator Reader

    def read_generator(self) -> Dict[Path, Generator[str, None, None]]:
        """ 
        Read the content of all files in the file paths as generators.

        Returns:
            Dict[Path, Generator[str, None, None]]: A dictionary mapping file paths to their content as generators.
        """

        try:
            if not self.file_paths:
                raise ValueError("File paths list is empty. Cannot read files.")
            
            if self.write_mode not in (LogWriteMode.READ, LogWriteMode.READ_WRITE):
                raise ValueError(
                    f"FileReader is not configured for reading. Use LogWriteMode.READ or LogWriteMode.READ_WRITE."
                    f"\n\tCurrent mode: {self.write_mode.value}\n"
                )

            return self._reader_generator_handler()
        except Exception as e:
            self.logger.error(f"Error reading files as generators: {e.__class__.__name__} -> {e}")
            raise FileReaderReadError(f"Error reading files as generators: {e.__class__.__name__} -> {e}") from e


    async def async_read_generator(self) -> Dict[Path, Generator[str, None, None]]:
        """
        Asynchronously read the content of all files in the file paths as generators.

        Returns:
            Dict[Path, AsyncGenerator[str, None, None]]: A dictionary mapping file paths to their content as generators.
        """
        try:
            if not self.file_paths:
                raise ValueError("File paths list is empty. Cannot read files.")
            
            if self.write_mode not in (LogWriteMode.READ, LogWriteMode.READ_WRITE):
                raise ValueError(
                    f"FileReader is not configured for reading. Use LogWriteMode.READ or LogWriteMode.READ_WRITE."
                    f"\n\tCurrent mode: {self.write_mode.value}\n"
                )

            return await self._async_reader_generator_handler()
        except Exception as e:
            self.logger.error(f"Error reading files asynchronously as generators: {e.__class__.__name__} -> {e}")
            raise FileReaderAsyncReadError(f"Error reading files asynchronously as generators: {e.__class__.__name__} -> {e}") from e


    # Generator Unpacker

    def unpacker(
        self,
        dict_gen: Dict[Path, Generator[str, None, None]],
        chunk: int | None = None
    ) -> Dict[Path, str]:
        
        """
        Unpack the content of generators in a dictionary.

        Arguments:
            dict_gen (Dict[Path, Generator[str, None, None]]): A dictionary mapping file paths to their content as generators.
            chunk (int | None): Optional chunk size to limit the number of lines read from each generator.

        Returns:
            out (Dict[Path, str]) : A dictionary mapping file paths to their unpacked content.
        """
        results: Dict[Path, str] = {}
        for path, gen in dict_gen.items():
            try:
                if chunk is not None:
                    # If chunk is specified, limit the number of lines read
                    results[path] = "".join(
                        line for _, line in zip(range(chunk), gen)
                    )
                else:
                    # Otherwise, read all lines from the generator
                    results[path] = "".join(line for line in gen)
            except Exception as e:
                self.logger.error(f"Error unpacking generator for file {path}: {e}")
                results[path] = f"Error unpacking generator: {e}"
        return results
        

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
                raise FileReaderShutdownError(
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
            raise FileReaderResumeError(
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
    def from_dict(
        cls,
        config_dict: Dict[str, Any]
    ) -> 'FileReader':

        """
        Create a FileReader instance from a configuration dictionary.

        Arguments:
            config_dict (Dict[str, Any]): The configuration dictionary containing file paths and other settings.

        Returns:
            out (FileReader): An instance of FileReader configured with the provided settings.
        """
        try:

            if not isinstance(config_dict, dict):
                raise TypeError("Configuration must be a dictionary.")
            
            if len(config_dict) == 0:
                raise ValueError("Configuration dictionary is empty.")
            
            file_paths: List[Path | str] = config_dict.get("file_paths", [])

            if not file_paths:
                raise TypeError("No file paths provided in the configuration.")
            
            write_mode: LogWriteMode = LogWriteMode(config_dict.get("write_mode", "READ"))

            retry_limit: int = config_dict.get("retry_limit", 3)
            retry_delay: float = config_dict.get("retry_delay", 1.0)
            backoff_factor: float = config_dict.get("backoff_factor", 1.0)
            logger: logging.Logger | None = config_dict.get("logger", None)

            return cls(
                file_paths=file_paths,
                write_mode=write_mode,
                retry_limit=retry_limit,
                retry_delay=retry_delay,
                backoff_factor=backoff_factor,
                logger=logger
            )              
            
        except Exception as e:
            raise FileReaderConfigError(f"Error creating FileReader from config: {e.__class__.__name__} -> {e}") from e
        

    @classmethod
    def from_json(
        cls,
        json_file: Union[str, bytes],
        custom_decoder: str = 'utf-8'
    ) -> 'FileReader':
        """
        Create a FileReader instance from a JSON file.

        Arguments:
            json_file (Union[str, bytes]): The path to the JSON file or the JSON content as a string.
            custom_decoder (str): The encoding to use for decoding the JSON file content.
                - Default is 'utf-8'.
        
        Returns:
            out (FileReader): An instance of FileReader configured with the provided settings.
        """

        try:

            if not isinstance(json_file, (str, bytes)):
                raise TypeError("json_file must be a string or bytes.")

            if not isinstance(custom_decoder, str):
                raise TypeError("custom_decoder must be a string representing the encoding.")
            
            if custom_decoder not in ['utf-8', 'utf-16', 'latin-1']:
                raise ValueError("custom_decoder must be one of 'utf-8', 'utf-16', or 'latin-1'.")

            json_str: str = json_file if isinstance(json_file, str) else json_file.decode(custom_decoder)
            
            if not json_str:
                raise ValueError("JSON file content is empty.")
            
            json_dict: Dict[str, Any] = json.loads(json_str)

            return cls.from_dict(json_dict)
        
        except Exception as e:
            raise FileReaderConfigError(f"Error creating FileReader from JSON: {e.__class__.__name__} -> {e}") from e


    @classmethod
    def from_yaml(
        cls,
        yaml_file: Union[str, bytes],
        custom_decoder: str = 'utf-8'
    ) -> 'FileReader':
        """
        Create a FileReader instance from a YAML file.

        Arguments:
            yaml_file (Union[str, bytes]): The path to the YAML file or the YAML content as a string.
            custom_decoder (str): The encoding to use for decoding the YAML file content.
                - Default is 'utf-8'.

        Returns:
            out (FileReader): An instance of FileReader configured with the provided settings.
        """

        try:

            if not isinstance(yaml_file, (str, bytes)):
                raise TypeError("yaml_file must be a string or bytes.")
            
            if not isinstance(custom_decoder, str):
                raise TypeError("custom_decoder must be a string representing the encoding.")
            
            if custom_decoder not in ['utf-8', 'utf-16', 'latin-1']:
                raise ValueError("custom_decoder must be one of 'utf-8', 'utf-16', or 'latin-1'.")

            yaml_str: str = yaml_file if isinstance(yaml_file, str) else yaml_file.decode(custom_decoder)
            
            if not yaml_str:
                raise ValueError("YAML file content is empty.")
            
            yaml_dict: Dict[str, Any] = yaml.safe_load(yaml_str)

            return cls.from_dict(yaml_dict)
        
        except Exception as e:
            raise FileReaderConfigError(f"Error creating FileReader from YAML: {e.__class__.__name__} -> {e}") from e


    # Config

    def config_from_dict(
        self,
        config: Dict[str, Any],
    ) -> None:

        """
        Update the FileReader configuration from a dictionary.

        Arguments:
            config (Dict[str, Any]): The configuration dictionary containing file paths and other settings.
        """
        try:
            if not isinstance(config, dict):
                raise TypeError("Configuration must be a dictionary.")
            
            if len(config) == 0:
                raise ValueError("Configuration dictionary is empty.")
            
            for key in config.keys():
                if key not in LIST_NECESSARY_KEYS:
                    raise KeyError(
                        f"Invalid key '{key}' in configuration. "
                        f"Allowed keys are: {', '.join(LIST_NECESSARY_KEYS)}"
                    )
            
            self.file_paths = config.get("file_paths", self.file_paths)
            self.write_mode = LogWriteMode(config.get("write_mode", self.write_mode.value))
            self.retry_limit = config.get("retry_limit", self.retry_limit)
            self.retry_delay = config.get("retry_delay", self.retry_delay)
            self.backoff_factor = config.get("backoff_factor", self.backoff_factor)

        except Exception as e:
            raise FileReaderConfigError(f"Error updating FileReader configuration: {e.__class__.__name__} -> {e}") from e
        
    
    def config_from_json(
        self,
        json_file: Union[str, bytes],
        custom_decoder: str = 'utf-8'
    ) -> None:
        """
        Update the FileReader configuration from a JSON file.

        Arguments:
            json_file (Union[str, bytes]): The path to the JSON file or the JSON content as a string.
            custom_decoder (str): The encoding to use for decoding the JSON file content.
                - Default is 'utf-8'.
        """
        try:
            if not isinstance(json_file, (str, bytes)):
                raise TypeError("json_file must be a string or bytes.")
            
            if not isinstance(custom_decoder, str):
                raise TypeError("custom_decoder must be a string representing the encoding.")
            
            if custom_decoder not in ['utf-8', 'utf-16', 'latin-1']:
                raise ValueError("custom_decoder must be one of 'utf-8', 'utf-16', or 'latin-1'.")

            json_str: str = json_file if isinstance(json_file, str) else json_file.decode(custom_decoder)

            if not json_str:
                raise ValueError("JSON file content is empty.")

            config_dict: Dict[str, Any] = json.loads(json_str)
            self.config_from_dict(config_dict)
        except Exception as e:
            raise FileReaderConfigError(f"Error updating FileReader configuration from JSON: {e.__class__.__name__} -> {e}") from e


    def config_from_yaml(
        self,
        yaml_file: Union[str, bytes],
        custom_decoder: str = 'utf-8'
    ) -> None:
        """
        Update the FileReader configuration from a YAML file.

        Arguments:
            yaml_file (Union[str, bytes]): The path to the YAML file or the YAML content as a string.
            custom_decoder (str): The encoding to use for decoding the YAML file content.
                - Default is 'utf-8'.
        """
        try:
            if not isinstance(yaml_file, (str, bytes)):
                raise TypeError("yaml_file must be a string or bytes.")
            
            if not isinstance(custom_decoder, str):
                raise TypeError("custom_decoder must be a string representing the encoding.")
            
            if custom_decoder not in ['utf-8', 'utf-16', 'latin-1']:
                raise ValueError("custom_decoder must be one of 'utf-8', 'utf-16', or 'latin-1'.")

            yaml_str: str = yaml_file if isinstance(yaml_file, str) else yaml_file.decode(custom_decoder)

            if not yaml_str:
                raise ValueError("YAML file content is empty.")

            config_dict: Dict[str, Any] = yaml.safe_load(yaml_str)
            self.config_from_dict(config_dict)
        except Exception as e:
            raise FileReaderConfigError(f"Error updating FileReader configuration from YAML: {e.__class__.__name__} -> {e}") from e
        
    