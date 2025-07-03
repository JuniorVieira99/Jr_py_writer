# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
from mimetypes import suffix_map
import os
import json
import yaml
import gzip
import zlib

from typing import Callable, List, Literal, Union, Dict
from pathlib import Path

# ----------------------------------------------------------------------------------------------
# Exceptions
# ----------------------------------------------------------------------------------------------


class ExporterError(Exception):
    """
    Custom exception for exporter errors.
    """

    pass


class MakeJsonError(ExporterError):
    """
    Exception raised when there is an error in making JSON.
    """

    pass


class MakeYamlError(ExporterError):
    """
    Exception raised when there is an error in making YAML.
    """

    pass


class MakeGzipError(ExporterError):
    """
    Exception raised when there is an error in making Gzip.
    """

    pass


class MakeZlibError(ExporterError):
    """
    Exception raised when there is an error in making Zlib.
    """

    pass


class ExportToFileError(ExporterError):
    """
    Exception raised when there is an error exporting to a file.
    """

    pass


# ----------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------


def _clean_dict(data: Dict[Path, str | Exception]) -> Dict[str, str]:
    """
    _clean_dict
    ===========
    Clean the dictionary by converting Path keys to strings and values to strings.

    Arguments:
        data (Dict[Path, str | Exception]): Dictionary to be cleaned.

    Returns:
        Dict[str, str]: Cleaned dictionary with string keys and values.
    """
    return {str(k): str(v) if isinstance(v, Exception) else v for k, v in data.items()}


def _validate_dict(data: Dict[Path, str | Exception]) -> bool:
    """
    _validate_dict
    ==============
    Validate the dictionary to ensure it has valid keys and values.

    Arguments:
        data (Dict[Path, str | Exception]): Dictionary to be validated.

    Returns:
        bool: True if the dictionary is valid, False otherwise.
    """
    if not isinstance(data, dict):
        raise TypeError("Data must be a dictionary.")
    if not data:
        raise ValueError("Data cannot be empty.")
    for k, v in data.items():
        if not isinstance(k, Path) or not isinstance(v, (str, Exception)):
            raise TypeError(
                f"Invalid key-value pair: {k} -> {v}. Keys must be Path objects and values must be str or Exception."
            )
    # If all checks pass, return True
    return True


def _get_suffix(file_format: Literal["json", "yaml", "gzip", "zlib"]) -> str:
    """
    _get_suffix
    ===========
    Get the file suffix based on the specified file format.

    Arguments:
        file_format (Literal['json', 'yaml', 'gzip', 'zlib']): Format of the output file.

    Returns:
        str: The appropriate file suffix for the specified format.

    Raises:
        ValueError: If the file format is not supported.
    """
    if file_format == "json":
        return ".json"
    elif file_format == "yaml":
        return ".yaml"
    elif file_format == "gzip":
        return ".gz"
    elif file_format == "zlib":
        return ".zlib"
    else:
        raise ValueError(f"Unsupported file format: {file_format}")


class ExporterAdapter:
    """
    ExporterAdapter
    ===============
    A utility class for converting and exporting data in various formats such as JSON, YAML, Gzip, and Zlib.

    Methods:
    --------
        #### make_data_json(data: Dict[Path, str | Exception]) -> str:
            Convert data to JSON format.
        #### make_data_yaml(data: Dict[Path, str | Exception]) -> str:
            Convert data to YAML format.
        #### make_data_gzip(data: Dict[Path, str | Exception]) -> bytes:
            Compress data using Gzip.
        #### make_data_zlib(data: Dict[Path, str | Exception]) -> bytes:
            Compress data using Zlib.
        #### make_string_gzip(data: str) -> bytes:
            Compress string data using Gzip.
        #### make_string_zlib(data: str) -> bytes:
            Compress string data using Zlib.
        #### make_data_map() -> Dict[str, Callable[[Dict[Path, str | Exception]], str | bytes]]:
            Create a mapping of data formats to their respective conversion methods.
        #### export_to_file(...) -> None:
            Export data to a file in the specified format.

    Example:
    ```python
    from jr_py_writer import ExporterAdapter

    # Example usage of ExporterAdapter
    data = {
        Path('file1.txt'): 'Content of file 1',
        Path('file2.txt'): 'Content of file 2',
        Path('file3.txt'): Exception("Error reading file 3")
    }

    # Convert data to JSON
    json_data: str = ExporterAdapter.make_data_json(data)

    # Convert data to YAML
    yaml_data: str = ExporterAdapter.make_data_yaml(data)

    # Compress data using Gzip
    gzip_data: bytes = ExporterAdapter.make_data_gzip(data)

    # Compress data using Zlib
    zlib_data: bytes = ExporterAdapter.make_data_zlib(data)

    # Export data to a JSON file
    ExporterAdapter.export_to_file(data, 'output.json', file_format='json')

    # Export data to a YAML file
    ExporterAdapter.export_to_file(data, 'output.yaml', file_format='yaml')

    # Export data to a Gzip file
    ExporterAdapter.export_to_file(data, 'output.gz', file_format='gzip')

    # Export data to a Zlib file
    ExporterAdapter.export_to_file(data, 'output.zlib', file_format='zlib
    """

    @staticmethod
    def make_data_json(data: Dict[Path, str | Exception]) -> str:
        """
        make_json
        ==========
        Convert data to JSON format.

        Arguments:
            data (Dict[Path, str | Exception]): Data to be converted to JSON.

        Returns:
            str: JSON formatted string.

        Raises:
            MakeJsonError: If there is an error in making JSON.

        Example:
            ```python
            # Example usage of make_json method
            data = {
                Path('file1.txt'): 'Content of file 1',
                Path('file2.txt'): 'Content of file 2'
            }
            # Convert data to JSON
            json_data: str = ExporterAdapter.make_data_json(data)
            ```
        """
        try:
            # Validate the input dictionary
            _validate_dict(data)

            # Clean the dictionary by converting Path keys to strings and values to strings
            json_data = json.dumps(_clean_dict(data), indent=4, ensure_ascii=False)
            return json_data
        except Exception as e:
            raise MakeJsonError(f"Error making JSON: {e}") from e

    @staticmethod
    def make_data_yaml(data: Dict[Path, str | Exception]) -> str:
        """
        make_yaml
        =========
        Convert data to YAML format.

        Arguments:
            data (Dict[Path, str | Exception]): Data to be converted to YAML.

        Returns:
            str: YAML formatted string.

        Raises:
            MakeYamlError: If there is an error in making YAML.

        Example:
            ```python
            # Example usage of make_yaml method
            data = {
                Path('file1.txt'): 'Content of file 1',
                Path('file2.txt'): 'Content of file 2'
            }
            # Convert data to YAML
            yaml_data: str = ExporterAdapter.make_data_yaml(data)
            ```
        """
        try:
            # Validate the input dictionary
            _validate_dict(data)

            # Clean the dictionary by converting Path keys to strings and values to strings
            yaml_data = yaml.dump(
                _clean_dict(data),
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
            return yaml_data
        except Exception as e:
            raise MakeYamlError(f"Error making YAML: {e}") from e

    @staticmethod
    def make_data_gzip(data: Dict[Path, str | Exception]) -> bytes:
        """
        make_data_gzip
        ==============
        Compress data using Gzip.

        Arguments:
            data (Dict[Path, str | Exception]): Data to be compressed.

        Returns:
            bytes: Compressed data in Gzip format.

        Raises:
            MakeGzipError: If there is an error in making Gzip.

        Example:
            ```python
            # Example usage of make_data_gzip method
            data = {
                Path('file1.txt'): 'Content of file 1',
                Path('file2.txt'): 'Content of file 2'
            }
            # Compress data using Gzip
            gzip_data: bytes = ExporterAdapter.make_data_gzip(data)
            ```
        """
        try:
            # Validate the input dictionary
            _validate_dict(data)

            # Clean the dictionary by converting Path keys to strings and values to strings
            json_data = ExporterAdapter.make_data_json(data)
            gzip_data = gzip.compress(json_data.encode("utf-8"))
            return gzip_data
        except Exception as e:
            raise MakeGzipError(f"Error making Gzip: {e}") from e

    @staticmethod
    def make_data_zlib(data: Dict[Path, str | Exception]) -> bytes:
        """
        make_data_zlib
        ==============
        Compress data using Zlib.

        Arguments:
            data (Dict[Path, str | Exception]): Data to be compressed.

        Returns:
            bytes: Compressed data in Zlib format.

        Raises:
            MakeZlibError: If there is an error in making Zlib.

        Example:
            ```python
            # Example usage of make_data_zlib method
            data = {
                Path('file1.txt'): 'Content of file 1',
                Path('file2.txt'): 'Content of file 2'
            }
            # Compress data using Zlib
            zlib_data: bytes = ExporterAdapter.make_data_zlib(data)
            ```
        """
        try:
            # Validate the input dictionary
            _validate_dict(data)

            # Clean the dictionary by converting Path keys to strings and values to strings
            json_data = ExporterAdapter.make_data_json(data)
            zlib_data = zlib.compress(json_data.encode("utf-8"))
            return zlib_data
        except Exception as e:
            raise MakeZlibError(f"Error making Zlib: {e}") from e

    @staticmethod
    def make_string_gzip(data: str) -> bytes:
        """
        make_string_gzip
        =========
        Compress string data using Gzip.

        Arguments:
            data (str): Data to be compressed.

        Returns:
            bytes: Compressed data in Gzip format.

        Raises:
            MakeGzipError: If there is an error in making Gzip.

        Example:
            ```python
            # Example usage of make_gzip method
            data = 'This is some text data to be compressed.'
            # Compress data using Gzip
            gzip_data: bytes = ExporterAdapter.make_gzip(data)
            ```
        """
        try:
            if not isinstance(data, str):
                raise TypeError("Data must be a string.")
            if not data:
                raise ValueError("Data cannot be empty.")
            gzip_data = gzip.compress(data.encode("utf-8"))
            return gzip_data
        except Exception as e:
            raise MakeGzipError(f"Error making Gzip: {e}") from e

    @staticmethod
    def make_string_zlib(data: str) -> bytes:
        """
        make_string_zlib
        ================
        Compress string data using Zlib.

        Arguments:
            data (str): Data to be compressed.

        Returns:
            bytes: Compressed data in Zlib format.

        Raises:
            MakeZlibError: If there is an error in making Zlib.

        Example:
            ```python
            # Example usage of make_zlib method
            data = 'This is some text data to be compressed.'
            # Compress data using Zlib
            zlib_data: bytes = ExporterAdapter.make_zlib(data)
            ```
        """
        try:
            if not isinstance(data, str):
                raise TypeError("Data must be a string.")
            if not data:
                raise ValueError("Data cannot be empty.")
            zlib_data = zlib.compress(data.encode("utf-8"))
            return zlib_data
        except Exception as e:
            raise MakeZlibError(f"Error making Zlib: {e}") from e

    @staticmethod
    def make_data_map() -> (
        Dict[str, Callable[[Dict[Path, str | Exception]], str | bytes]]
    ):
        """
        make_data_map
        =============
        Create a mapping of data formats to their respective conversion methods.

        Returns:
            Dict[str, Callable[[Dict[Path, str | Exception]], str | bytes]]: Mapping of format names to methods.

        Example:
            ```python
            # Example usage of make_data_map method
            data_map = ExporterAdapter.make_data_map()

            # Access the JSON conversion method
            json_method = data_map['json']
            # Convert data to JSON
            json_str = json_method(data)

            # Access the YAML conversion method
            yaml_method = data_map['yaml']
            # Convert data to YAML
            yaml_str = yaml_method(data)
            ...
            ```
        """
        return {
            "json": ExporterAdapter.make_data_json,
            "yaml": ExporterAdapter.make_data_yaml,
            "gzip": ExporterAdapter.make_data_gzip,
            "zlib": ExporterAdapter.make_data_zlib,
        }

    @staticmethod
    def export_to_file(
        data: Dict[Path, str | Exception],
        file_path: Union[str, Path],
        decode: bool = True,
        create_file: bool = True,
        file_format: Literal["json", "yaml", "gzip", "zlib"] = "json",
    ) -> None:
        """
        export_to_file
        ==============
        Export data to a file in the specified format.

        Arguments:
            data (Dict[Path, str | Exception]): Data to be exported.
            file_path (Union[str, Path]): Path to the output file.
            create_file (bool): Whether to create the file if it does not exist. Defaults to True.
            decode (bool): Whether to decode the data before exporting. Defaults to True.
            file_format (str): Format of the output file ('json', 'yaml', 'gzip', 'zlib').

        Raises:
            ExportToFileError: If there is an error exporting to a file.

        Example:
            ```python
            # Example usage of export_to_file method
            data = {
                Path('file1.txt'): 'Content of file 1',
                Path('file2.txt'): 'Content of file 2'
            }
            # Export data to a JSON file
            ExporterAdapter.export_to_file(data, 'output.json', 'json')
            ```
        """
        try:
            # Validate inputs

            if not isinstance(file_path, (str, Path)):
                raise TypeError("File path must be a string or Path object.")

            if isinstance(file_path, str):
                file_path = Path(file_path)

            if not file_path:
                raise ValueError("File path cannot be empty.")

            _validate_dict(data)

            if file_format not in ExporterAdapter.make_data_map():
                raise ValueError(f"Unsupported file format: {file_format}")

            if not isinstance(decode, bool):
                raise TypeError("Decode must be a boolean value.")
            if not isinstance(create_file, bool):
                raise TypeError("create_file must be a boolean value.")

            # Ensure the file path has the correct suffix
            if file_path.suffix and file_path.suffix[1:] != file_format:
                suffix: str = _get_suffix(file_format)
                file_path = file_path.with_suffix(suffix)

            # Ensure the directory exists if create_file is True
            if not file_path.parent.exists():
                if create_file:
                    try:
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        raise ExportToFileError(
                            f"Error creating directory {file_path.parent}: {e}"
                        ) from e
                else:
                    raise ExportToFileError(
                        f"Directory {file_path.parent} does not exist and create_file is False."
                    )

            # Get MAP of data methods based on file format
            data_method: Callable = ExporterAdapter.make_data_map()[file_format]

            # Get the content based on the specified format
            content: Union[str, bytes] = data_method(data)

            if (
                decode
                and isinstance(content, bytes)
                and file_format in ["gzip", "zlib"]
            ):
                # Skip decoding for binary formats
                decode = False

            with open(file_path, "wb" if file_format in ["gzip", "zlib"] else "w") as f:
                if not f.writable():
                    raise IOError(f"File {file_path} is not writable.")
                f.write(content)

            # Check if the file was written successfully

            with open(file_path, "rb" if file_format in ["gzip", "zlib"] else "r") as f:
                if not f.readable():
                    raise IOError(f"File {file_path} is not readable.")
                content = f.read()
                if not content:
                    raise IOError(f"File {file_path} is empty after writing.")

        except Exception as e:
            raise ExportToFileError(f"Error exporting to file {file_path}: {e}") from e
