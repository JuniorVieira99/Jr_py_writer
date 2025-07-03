# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
import gzip
import zlib
from pathlib import Path
from typing import Any, List, Final, Dict

# Third-party imports
import pytest

# Local imports
from jr_file_handler.classes.plugins.exporter_adapter import ExporterAdapter


# Exceptions Reader
from jr_file_handler.classes.plugins.exporter_adapter import (
    MakeGzipError,
    MakeZlibError,
    MakeJsonError,
    MakeYamlError,
    ExportToFileError
)

# ----------------------------------------------------------------------------------------------
# Fixture
# ----------------------------------------------------------------------------------------------


def make_data(num: int) -> Dict[Path, str | Exception]:
    """Create a dictionary with num entries, where each entry is a Path and a string."""
    return {Path(f"file_{i}.txt"): f"Content of file {i}" for i in range(num)}


def make_data_with_exceptions(num: int) -> Dict[Path, str | Exception]:
    """Create a dictionary with num entries, where some entries are exceptions."""
    data = {}
    for i in range(num):
        if i % 2 == 0:
            data[Path(f"file_{i}.txt")] = f"Content of file {i}"
        else:
            data[Path(f"file_{i}.txt")] = Exception(f"Error in file {i}")
    return data


# ----------------------------------------------------------------------------------------------
# Test Cases
# ----------------------------------------------------------------------------------------------

EDGE_DATA: Final[List[Any]] = [
    "",
    5,
    None,
    {},
    [],
    5.5,
    False
]


# ----------------------------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------------------------


# Edge cases for ExporterAdapter methods

class TestExporterAdapterEdgeCases:
    """
    Test cases for ExporterAdapter methods with edge cases.
    This class tests the methods of ExporterAdapter with various edge cases
    to ensure they handle unexpected inputs gracefully.

    Tests:
    -------
    - exporter cases 
    - exporter adapter edge cases
    - make_data_json with edge cases
    - make_data_yaml with edge cases
    - make_data_gzip with edge cases
    - make_data_zlib with edge cases
    - export_to_file with edge cases
    """

    @pytest.mark.parametrize("data", EDGE_DATA)
    def test_exporter_adapter_edge_cases(self, data: Any):
        """Test ExporterAdapter methods with edge cases."""
        # Test make_data_json with edge cases
        with pytest.raises(MakeJsonError):
                ExporterAdapter.make_data_json(data)

        # Test make_data_yaml with edge cases
        with pytest.raises(MakeYamlError):
                ExporterAdapter.make_data_yaml(data)
        
        # Test make_data_gzip with edge cases
        with pytest.raises(MakeGzipError):
                ExporterAdapter.make_data_gzip(data)
            
        # Test make_data_zlib with edge cases
        with pytest.raises(MakeZlibError):
                ExporterAdapter.make_data_zlib(data)


    @pytest.mark.parametrize("data", EDGE_DATA)
    def test_exporter_adapter_export_to_file_edge_cases(self, data: Any, tmp_path: Path):
        """Test ExporterAdapter.export_to_file with edge cases."""
        # Define the file path
        file_path = tmp_path / "exported_data.json"

        # Test export_to_file with edge cases
        with pytest.raises(ExportToFileError):
            ExporterAdapter.export_to_file(
                data=data,
                file_path=file_path,
                file_format='json'
            )
        
        with pytest.raises(ExportToFileError):
            ExporterAdapter.export_to_file(
                data=make_data(2),
                file_path=data,
                file_format='yaml'
            )

        with pytest.raises(ExportToFileError):
            ExporterAdapter.export_to_file(
                data=make_data(2),
                file_path=file_path,
                file_format=data
            )


# Make_data_* Tests

class TestExporterAdapterMakeData:
    """
    Test cases for ExporterAdapter.make_data methods.
    This class tests the make_data methods of ExporterAdapter to ensure they handle various data formats correctly.
    
    Tests:
    -------
    - make_data_json
    - make_data_yaml
    - make_data_gzip
    - make_data_zlib
    """
    def test_make_data_json(self):
        """Test making JSON data."""
        # Create a sample data dictionary
        data = make_data(5)
        assert isinstance(data, dict)
        assert len(data) == 5

        # Convert the data to JSON format
        json_str = ExporterAdapter.make_data_json(data)

        # Validate the JSON string
        assert isinstance(json_str, str), f"JSON data should be a string got {type(json_str)}"
        assert len(json_str) > 0, f"JSON data should not be empty, got {json_str}"
        assert json_str.startswith("{") and json_str.endswith("}"), f"JSON data should start with '{{' and end with '}}', got {json_str}"

        # Debug output
        print("\nJSON Data:\n", json_str)


    def test_make_data_yaml(self):
        """Test making YAML data."""
        # Create a sample data dictionary
        data = make_data(5)
        assert isinstance(data, dict)
        assert len(data) == 5

        # Convert the data to YAML format
        yaml_str = ExporterAdapter.make_data_yaml(data)

        # Validate the YAML string
        assert isinstance(yaml_str, str), f"YAML data should be a string got {type(yaml_str)}"
        assert len(yaml_str) > 0, f"YAML data should not be empty, got {yaml_str}"

        # Debug output
        print("\nYAML Data:\n", yaml_str)


    def test_make_data_gzip(self):
        """Test making GZIP data."""
        # Create a sample data dictionary
        data = make_data(5)
        assert isinstance(data, dict)
        assert len(data) == 5

        # Convert the data to GZIP format
        gzip_data = ExporterAdapter.make_data_gzip(data)

        # Validate the GZIP data
        assert isinstance(gzip_data, bytes), f"GZIP data should be bytes got {type(gzip_data)}"
        assert len(gzip_data) > 0, f"GZIP data should not be empty, got {gzip_data}"

        # Decompress the GZIP data to verify correctness
        decompressed_data = gzip.decompress(gzip_data).decode('utf-8')
        # Validate the decompressed data
        assert decompressed_data.startswith("{") and decompressed_data.endswith("}"), \
            f"Decompressed GZIP data should start with '{{' and end with '}}', got {decompressed_data}"

        # Debug output
        print("\nGZIP Data Length:", len(decompressed_data))
        print("\nDecompressed GZIP Data:\n", decompressed_data)


    def test_make_data_zlib(self):
        """Test making ZLIB data."""
        # Create a sample data dictionary
        data = make_data(5)
        assert isinstance(data, dict)
        assert len(data) == 5

        # Convert the data to ZLIB format
        zlib_data = ExporterAdapter.make_data_zlib(data)

        # Validate the ZLIB data
        assert isinstance(zlib_data, bytes), f"ZLIB data should be bytes got {type(zlib_data)}"
        assert len(zlib_data) > 0, f"ZLIB data should not be empty, got {zlib_data}"

        # Decompress the ZLIB data to verify correctness
        decompressed_data = zlib.decompress(zlib_data).decode('utf-8')
        # Validate the decompressed data
        assert decompressed_data.startswith("{") and decompressed_data.endswith("}"), \
            f"Decompressed ZLIB data should start with '{{' and end with '}}', got {decompressed_data}"

        # Debug output
        print("\nZLIB Data Length:", len(zlib_data))
        print("\nDecompressed ZLIB Data:\n", decompressed_data)
        


# Make_string_* Tests

class TestExporterAdapterMakeString:
    """
    Test cases for ExporterAdapter.make_string methods.
    This class tests the make_string methods of ExporterAdapter to ensure they handle various string formats correctly.
    
    Tests:
    -------
    - make_string_gzip
    - make_string_zlib
    """
    def test_make_string_gzip(self):
        """Test making GZIP string."""
        # Create a sample data dictionary
        string: str = "This is a test string for GZIP compression."

        # Convert the data to GZIP string
        gzip_str: bytes = ExporterAdapter.make_string_gzip(string)

        # Validate the GZIP string
        assert isinstance(gzip_str, bytes), f"GZIP string should be bytes got {type(gzip_str)}"

        # Decompress the GZIP string to verify correctness
        decompressed_str = gzip.decompress(gzip_str).decode('utf-8')
        # Validate the decompressed string
        assert decompressed_str == string, f"Decompressed string should match original, got {decompressed_str}"

        # Debug output
        print("\nGZIP String Length:", len(gzip_str))
        print("\nDecompressed GZIP String:\n", decompressed_str)


    def test_make_string_zlib(self):
        """Test making ZLIB string."""
        # Create a sample data dictionary
        string: str = "This is a test string for ZLIB compression."

        # Convert the data to ZLIB string
        zlib_str: bytes = ExporterAdapter.make_string_zlib(string)

        # Validate the ZLIB string
        assert isinstance(zlib_str, bytes), f"ZLIB string should be bytes got {type(zlib_str)}"

        # Decompress the ZLIB string to verify correctness
        decompressed_str = zlib.decompress(zlib_str).decode('utf-8')
        # Validate the decompressed string
        assert decompressed_str == string, f"Decompressed string should match original, got {decompressed_str}"

        # Debug output
        print("\nZLIB String Length:", len(zlib_str))
        print("\nDecompressed ZLIB String:\n", decompressed_str)


    # Export to file tests


# test_export_to_file_* Tests
class TestExporterAdapterExportToFile:
    """
    Test cases for ExporterAdapter.export_to_file methods.
    This class tests the export_to_file methods of ExporterAdapter to ensure they handle various file formats correctly.
    
    Tests:
    -------
    - test_export_to_file_json
    - test_export_to_file_yaml
    - test_export_to_file_gzip
    - test_export_to_file_zlib
    """

    def test_export_to_file_json(self, tmp_path: Path):
        """Test exporting data to a file."""
        # Create a sample data dictionary
        data = make_data(5)
        assert isinstance(data, dict)
        assert len(data) == 5

        # Define the file path
        file_path = tmp_path / "exported_data.json"

        # Export the data to a file
        ExporterAdapter.export_to_file(
            data=data,
            file_path=file_path,
            file_format='json'
        )

        # Validate the exported file
        assert file_path.exists(), f"Exported file should exist at {file_path}"
        assert file_path.is_file(), f"Exported path should be a file, got {file_path}"

        # Read the content of the exported file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Validate the content of the exported file
        assert isinstance(content, str), f"Content of exported file should be a string, got {type(content)}"
        assert len(content) > 0, f"Content of exported file should not be empty, got {content}"
        assert content.startswith("{") and content.endswith("}"), f"JSON content should start with '{{' and end with '}}', got {content}"
        assert "Content of file" in content, "Content should contain 'content of file'"

        # Debug output
        print("\nExported JSON Content Length:", len(content))
        print("\nExported JSON Content:\n", content)


    def test_export_to_file_yaml(self, tmp_path: Path):
        """Test exporting data to a YAML file."""
        # Create a sample data dictionary
        data = make_data(5)
        assert isinstance(data, dict)
        assert len(data) == 5

        # Define the file path
        file_path = tmp_path / "exported_data.yaml"

        # Export the data to a file
        ExporterAdapter.export_to_file(
            data=data,
            file_path=file_path,
            file_format='yaml'
        )

        # Validate the exported file
        assert file_path.exists(), f"Exported file should exist at {file_path}"
        assert file_path.is_file(), f"Exported path should be a file, got {file_path}"

        # Read the content of the exported file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Validate the content of the exported file
        assert isinstance(content, str), f"Content of exported file should be a string, got {type(content)}"
        assert len(content) > 0, f"Content of exported file should not be empty, got {content}"
        assert "Content of file" in content, "Content should contain 'content of file'"

        # Debug output
        print("\nExported YAML Content Length:", len(content))
        print("\nExported YAML Content:\n", content)


    def test_export_to_file_gzip(self, tmp_path: Path):
        """Test exporting data to a GZIP file."""
        # Create a sample data dictionary
        data = make_data(5)
        assert isinstance(data, dict)
        assert len(data) == 5

        # Define the file path
        file_path = tmp_path / "exported_data.gz"

        # Export the data to a file
        ExporterAdapter.export_to_file(
            data=data,
            file_path=file_path,
            file_format='gzip'
        )

        # Validate the exported file
        assert file_path.exists(), f"Exported file should exist at {file_path}"
        assert file_path.is_file(), f"Exported path should be a file, got {file_path}"

        # Read the content of the exported file
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Validate the content of the exported file
        assert isinstance(content, bytes), f"Content of exported file should be a string, got {type(content)}"
        assert len(content) > 0, f"Content of exported file should not be empty, got {content}"

        # Decompress the GZIP file to verify correctness
        decompress_content = gzip.decompress(content).decode('utf-8')
        # Validate the decompressed content
        assert "Content of file" in decompress_content, "Decompressed content should contain 'content of file'"

        # Debug output
        print("\nGZIP Content Length:", len(content))
        print("\nDecompressed GZIP Content:\n", decompress_content)


    def test_export_to_file_zlib(self, tmp_path: Path):
        """Test exporting data to a ZLIB file."""
        # Create a sample data dictionary
        data = make_data(5)
        assert isinstance(data, dict)
        assert len(data) == 5

        # Define the file path
        file_path = tmp_path / "exported_data.zlib"

        # Export the data to a file
        ExporterAdapter.export_to_file(
            data=data,
            file_path=file_path,
            file_format='zlib'
        )

        # Validate the exported file
        assert file_path.exists(), f"Exported file should exist at {file_path}"
        assert file_path.is_file(), f"Exported path should be a file, got {file_path}"

        # Read the content of the exported file
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Validate the content of the exported file
        assert isinstance(content, bytes), f"Content of exported file should be bytes, got {type(content)}"
        assert len(content) > 0, f"Content of exported file should not be empty, got {content}"

        # Decompress the ZLIB file to verify correctness
        decompress_content = zlib.decompress(content).decode('utf-8')

        # Validate the decompressed content
        assert "Content of file" in decompress_content, "Decompressed content should contain 'content of file'"

        # Debug output
        print("\nZLIB Content Length: ", len(content))
        print("\nDecompressed ZLIB Content:\n", decompress_content)


# ----------------------------------------------------------------------------------------------
# End of File