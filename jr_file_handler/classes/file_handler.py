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

from typing import Generator, Iterator, List, Union, Dict, Final, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from functools import partial

# Third-party imports
import yaml

# Utilities
from jr_file_handler.utils.utilities import batcher, batcher_with_gcmanager
from jr_file_handler.utils.module_enums import LogWriteMode
from jr_file_handler.classes.file_reader import FileReader
from jr_file_handler.classes.file_writer import FileWriter

# Exceptions


# ----------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------


class FileHandler:

    # ----------
    # Slots

    __slots__ = (
        "_file_reader",
        "_file_writer",
    )

    # ----------
    # Attributes

    _file_reader: FileReader
    _file_writer: FileWriter
    _handler_mode: LogWriteMode

    # ----------
    # Properties

    @property
    def file_reader(self) -> FileReader:
        """
        Returns the FileReader instance.
        """
        if not hasattr(self, "_file_reader"):
            self._file_reader = FileReader()
        return self._file_reader

    @property
    def file_writer(self) -> FileWriter:
        """
        Returns the FileWriter instance.
        """
        if not hasattr(self, "_file_writer"):
            self._file_writer = FileWriter()
        return self._file_writer

    # ----------
    # Constructor

    def __init__(
        self,
        handler_mode: LogWriteMode = LogWriteMode.READ_WRITE,
        logger: Union[logging.Logger, None] = None,
    ) -> None:
        """
        Initializes the FileHandler with instances of FileReader and FileWriter.
        """
        try:
            self._file_reader = FileReader(write_mode=handler_mode, logger=logger)
            self._file_writer = FileWriter(write_mode=handler_mode, logger=logger)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize FileHandler: {e}") from e

    # ----------
    # Configuration Methods

    def config_writer(
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
        self._file_writer.config(
            file_paths=file_paths,
            write_mode=write_mode,
            max_file_size=max_file_size,
            max_rotation=max_rotation,
            max_buffer_size=max_buffer_size,
            retry_limit=retry_limit,
            retry_delay=retry_delay,
            backoff_factor=backoff_factor,
        )

    def config_dict_writer(self, config: Dict[str, Any]) -> None:
        """
        Configure the FileWriter using a dictionary of parameters.

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
        self._file_writer.config_dict(config)
