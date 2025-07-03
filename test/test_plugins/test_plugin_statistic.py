# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
from pathlib import Path
from typing import Any, List, Final, Dict

import time

# Third-party imports
import pytest

# Local imports
from jr_file_handler.classes.plugins.statistics_adapter import StatisticsAdapter

# Exceptions
from jr_file_handler.classes.plugins.statistics_adapter import (
    ReportGenerationError,
    GetError,
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
            data[Path(f"file_{i}.txt")] = ValueError(f"Error in file {i}")
    return data


# ----------------------------------------------------------------------------------------------
# Test Cases
# ----------------------------------------------------------------------------------------------

EDGE_DATA: Final[List[Any]] = ["", 5, None, {}, [], 5.5, False]

CACHE_TEST: Final[List[int]] = [100, 1000, 5000, 10000, 50000, 100000]

# ----------------------------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------------------------


# Edge Cases


class TestStatisticsAdapterEdgeCases:
    """
    Test StatisticsAdapter with edge cases.

    Test:
    ------
    - Test StatisticsAdapter with edge cases.
    - Test StatisticsAdapter with edge cases for getters.
    - Test StatisticsAdapter with edge cases for exceptions.
    - Test StatisticsAdapter with edge cases for size methods.
    """

    @pytest.mark.parametrize("data", EDGE_DATA)
    def test_init_statistics_adapter_edge_cases(self, data):
        """Test StatisticsAdapter with edge cases."""
        with pytest.raises(ReportGenerationError):
            StatisticsAdapter.get_report(data)
        with pytest.raises(GetError):
            StatisticsAdapter.get_count_total_files(data)
        with pytest.raises(GetError):
            StatisticsAdapter.get_success_count(data)
        with pytest.raises(GetError):
            StatisticsAdapter.get_failure_count(data)
        with pytest.raises(GetError):
            StatisticsAdapter.get_success_rate(data)
        with pytest.raises(GetError):
            StatisticsAdapter.get_failure_rate(data)
        with pytest.raises(GetError):
            StatisticsAdapter.get_successful_files(data)
        with pytest.raises(GetError):
            StatisticsAdapter.get_failed_files(data)
        with pytest.raises(GetError):
            StatisticsAdapter.get_dict_with_exceptions(data)
        with pytest.raises(GetError):
            StatisticsAdapter.get_list_of_exceptions(data)
        with pytest.raises(GetError):
            StatisticsAdapter.get_total_size_of_files(data)
        with pytest.raises(GetError):
            StatisticsAdapter.get_largest_file_size(data)
        with pytest.raises(GetError):
            StatisticsAdapter.get_smallest_file_size(data)


# Get Report


class TestStatisticsAdapterGetReport:
    """
    Test StatisticsAdapter.get_report and its getters.

    Test:
    ------
    - Test StatisticsAdapter.get_report with valid data.
    - Test StatisticsAdapter.get_report with exceptions in the data.
    """

    def test_init_get_report(self):
        """Test StatisticsAdapter.get_report."""

        # Add some data
        data = make_data(5)

        # data str path list for assertions
        data_str_list = [str(path) for path in data.keys()]

        # Get the report
        report = StatisticsAdapter.get_report(data)

        # Check if the report is a dictionary
        assert isinstance(report, dict)

        # Check if the report contains the expected keys
        assert "total_files" in report
        assert "successful_reads" in report
        assert "failed_reads" in report
        assert "success_rate" in report
        assert "failed_rate" in report
        assert "successful_files" in report
        assert "failed_files" in report

        # Check if the values are of the expected types
        assert isinstance(report["total_files"], int)
        assert isinstance(report["successful_reads"], int)
        assert isinstance(report["failed_reads"], int)
        assert isinstance(report["success_rate"], float)
        assert isinstance(report["failed_rate"], float)
        assert isinstance(report["successful_files"], list)
        assert isinstance(report["failed_files"], list)

        # Check Values
        assert (
            report["total_files"] == 5
        ), f"Total files should be 5, got {report['total_files']}"
        assert (
            report["successful_reads"] == 5
        ), f"Successful reads should be 5, got {report['successful_reads']}"
        assert (
            report["failed_reads"] == 0
        ), f"Failed reads should be 0, got {report['failed_reads']}"
        assert report["success_rate"] == pytest.approx(
            100.0
        ), f"Success rate should be 100.0, got {report['success_rate']}"
        assert report["failed_rate"] == pytest.approx(
            0.0
        ), f"Failed rate should be 0.0, got {report['failed_rate']}"
        assert (
            report["failed_files"] == []
        ), f"Failed files should be empty, got {report['failed_files']}"

        for file in report["successful_files"]:
            assert isinstance(
                file, str
            ), f"Successful file {file} should be a string, got {type(file).__name__}"
            assert (
                file in data_str_list
            ), f"Successful file {file} should be in the original data, got {data_str_list}"

        # Getters
        total_files = StatisticsAdapter.get_count_total_files(data)
        successful_reads = StatisticsAdapter.get_success_count(data)
        failed_reads = StatisticsAdapter.get_failure_count(data)
        success_rate = StatisticsAdapter.get_success_rate(data)
        failed_rate = StatisticsAdapter.get_failure_rate(data)
        successful_files = StatisticsAdapter.get_successful_files(data)
        failed_files = StatisticsAdapter.get_failed_files(data)

        # Check if the getters return the expected values
        assert total_files == 5, f"Total files should be 5, got {total_files}"
        assert (
            successful_reads == 5
        ), f"Successful reads should be 5, got {successful_reads}"
        assert failed_reads == 0, f"Failed reads should be 0, got {failed_reads}"
        assert success_rate == pytest.approx(
            100.0
        ), f"Success rate should be 100.0, got {success_rate}"
        assert failed_rate == pytest.approx(
            0.0
        ), f"Failed rate should be 0.0, got {failed_rate}"
        assert failed_files == [], f"Failed files should be empty, got {failed_files}"

        for file in successful_files:
            assert isinstance(
                file, str
            ), f"Successful file {file} should be a string, got {type(file).__name__}"
            assert (
                file in data_str_list
            ), f"Successful file {file} should be in the original data, got {data_str_list}"

    def test_init_get_report_with_exceptions(self):
        """Test StatisticsAdapter.get_report with exceptions in the data."""

        # Add some data with exceptions
        data = make_data_with_exceptions(5)

        # data str path list for assertions
        data_str_list = [str(path) for path in data.keys()]

        # Get the report
        report = StatisticsAdapter.get_report(data)

        # Check if the report is a dictionary
        assert isinstance(report, dict)

        # Check if the report contains the expected keys
        assert "total_files" in report
        assert "successful_reads" in report
        assert "failed_reads" in report
        assert "success_rate" in report
        assert "failed_rate" in report
        assert "successful_files" in report
        assert "failed_files" in report

        # Check if the values are of the expected types
        assert isinstance(report["total_files"], int)
        assert isinstance(report["successful_reads"], int)
        assert isinstance(report["failed_reads"], int)
        assert isinstance(report["success_rate"], float)
        assert isinstance(report["failed_rate"], float)
        assert isinstance(report["successful_files"], list)
        assert isinstance(report["failed_files"], list)

        # Check Values
        total_files = 5
        successful_reads = 3  # 3 successful reads (even indices)
        failed_reads = 2  # 2 failed reads (odd indices)

        success_rate = (
            (successful_reads / total_files) * 100 if total_files > 0 else 0.0
        )
        failed_rate = (failed_reads / total_files) * 100 if total_files > 0 else 0.0

        assert (
            report["total_files"] == total_files
        ), f"Total files should be {total_files}, got {report['total_files']}"
        assert (
            report["successful_reads"] == successful_reads
        ), f"Successful reads should be {successful_reads}, got {report['successful_reads']}"
        assert (
            report["failed_reads"] == failed_reads
        ), f"Failed reads should be {failed_reads}, got {report['failed_reads']}"
        assert report["success_rate"] == pytest.approx(
            success_rate
        ), f"Success rate should be {success_rate}, got {report['success_rate']}"
        assert report["failed_rate"] == pytest.approx(
            failed_rate
        ), f"Failed rate should be {failed_rate}, got {report['failed_rate']}"
        assert (
            len(report["failed_files"]) == failed_reads
        ), f"Failed files should have {failed_reads} entries, got {len(report['failed_files'])}"
        assert (
            len(report["successful_files"]) == successful_reads
        ), f"Successful files should have {successful_reads} entries, got {len(report['successful_files'])}"

        for file in report["successful_files"]:
            assert isinstance(
                file, str
            ), f"Successful file {file} should be a string, got {type(file).__name__}"
            assert (
                file in data_str_list
            ), f"Successful file {file} should be in the original data, got {data_str_list}"

        for file in report["failed_files"]:
            assert isinstance(
                file, str
            ), f"Failed file {file} should be a string, got {type(file).__name__}"
            assert (
                file in data_str_list
            ), f"Failed file {file} should be in the original data, got {data_str_list}"

        # Getters
        get_total_files = StatisticsAdapter.get_count_total_files(data)
        get_successful_reads = StatisticsAdapter.get_success_count(data)
        get_failed_reads = StatisticsAdapter.get_failure_count(data)
        get_success_rate = StatisticsAdapter.get_success_rate(data)
        get_failed_rate = StatisticsAdapter.get_failure_rate(data)
        get_successful_files = StatisticsAdapter.get_successful_files(data)
        get_failed_files = StatisticsAdapter.get_failed_files(data)

        # Check if the getters return the expected values
        assert (
            get_total_files == total_files
        ), f"Total files should be {total_files}, got {get_total_files}"
        assert (
            get_successful_reads == successful_reads
        ), f"Successful reads should be {successful_reads}, got {get_successful_reads}"
        assert (
            get_failed_reads == failed_reads
        ), f"Failed reads should be {failed_reads}, got {get_failed_reads}"
        assert get_success_rate == pytest.approx(
            success_rate
        ), f"Success rate should be {success_rate}, got {get_success_rate}"
        assert get_failed_rate == pytest.approx(
            failed_rate
        ), f"Failed rate should be {failed_rate}, got {get_failed_rate}"
        assert (
            len(get_failed_files) == failed_reads
        ), f"Failed files should have {failed_reads} entries, got {len(get_failed_files)}"
        assert (
            len(get_successful_files) == successful_reads
        ), f"Successful files should have {successful_reads} entries, got {len(get_successful_files)}"

        for file in get_successful_files:
            assert isinstance(
                file, str
            ), f"Successful file {file} should be a string, got {type(file).__name__}"
            assert (
                file in data_str_list
            ), f"Successful file {file} should be in the original data, got {data_str_list}"

        for file in get_failed_files:
            assert isinstance(
                file, str
            ), f"Failed file {file} should be a string, got {type(file).__name__}"
            assert (
                file in data_str_list
            ), f"Failed file {file} should be in the original data, got {data_str_list}"


# Get Exceptions


class TestStatisticsAdapterGetExceptions:
    """
    Test StatisticsAdapter.get_report with exceptions in the data.

    Test:
    ------
    - Test StatisticsAdapter.get_report with exceptions in the data.
    """

    def test_init_get_exceptions(self):
        """Test StatisticsAdapter.get_report with exceptions in the data."""
        # Add some data with exceptions
        data = make_data_with_exceptions(5)

        # Get Dict of exceptions
        exception_dict: Dict = StatisticsAdapter.get_dict_with_exceptions(data)

        # Check if the exception_dict is a dictionary
        assert isinstance(
            exception_dict, dict
        ), f"Exception dict should be a dictionary, got {type(exception_dict).__name__}"
        assert (
            len(exception_dict) == 2
        ), f"Exception dict should have 2 entries, got {len(exception_dict)}"
        for key, value in exception_dict.items():
            assert isinstance(
                key, Path
            ), f"Exception dict key should be a Path, got {type(key).__name__}"
            assert isinstance(
                value, Exception
            ), f"Exception dict value should be an Exception, got {type(value).__name__}"
            assert isinstance(
                value, ValueError
            ), f"Exception dict value should be a ValueError, got {type(value).__name__}"

        # Debug print
        print(f"\nException dict:\n{exception_dict}")

        # Get List of exceptions
        exception_list: List[Exception] = StatisticsAdapter.get_list_of_exceptions(data)

        # Check if the exception_list is a list
        assert isinstance(
            exception_list, list
        ), f"Exception list should be a list, got {type(exception_list).__name__}"
        assert (
            len(exception_list) == 2
        ), f"Exception list should have 2 entries, got {len(exception_list)}"
        for exception in exception_list:
            assert isinstance(
                exception, Exception
            ), f"Exception list item should be an Exception, got {type(exception).__name__}"
            assert isinstance(
                exception, ValueError
            ), f"Exception list item should be a ValueError, got {type(exception).__name__}"

        # Debug print
        print(f"\nException list:\n{exception_list}")


# Test Size Methods


class TestStatisticsAdapterSizeMethods:
    """
    Test StatisticsAdapter size methods.

    Test:
    ------
    - Test StatisticsAdapter.get_total_size_of_files.
    """

    def test_get_total_size(self, tmp_path):
        """Test StatisticsAdapter.get_total_size."""
        # Create some files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file3 = tmp_path / "file3.txt"

        string_max: str = "Python is great! " * 100
        string_medium: str = "Python is great! " * 10
        string_min: str = "Python is great!"

        file1.write_text(string_max)
        file2.write_text(string_min)
        file3.write_text(string_medium)

        # Create data dictionary
        data: Dict[Path, str | Exception] = {
            file1: "Content of file 1",
            file2: "Content of file 2",
            file3: "Content of file 3",
        }

        # Get the total size
        total_size = StatisticsAdapter.get_total_size_of_files(data)
        # Get largest file size
        largest_file_size = StatisticsAdapter.get_largest_file_size(data)
        # Get smallest file size
        smallest_file_size = StatisticsAdapter.get_smallest_file_size(data)
        # Get average file size
        average_file_size = StatisticsAdapter.get_average_file_size(data)

        # Assertions
        assert isinstance(
            total_size, int
        ), f"Total size should be an integer, got {type(total_size).__name__}"
        assert total_size > 0, f"Total size should be greater than 0, got {total_size}"
        assert total_size == (
            len(string_max) + len(string_min) + len(string_medium)
        ), f"Total size should be {len(string_max) + len(string_min) + len(string_medium)}, got {total_size}"

        assert isinstance(
            largest_file_size, tuple
        ), f"Largest file size should be a tuple, got {type(largest_file_size).__name__}"
        assert (
            len(largest_file_size) == 2
        ), f"Largest file size tuple should have 2 elements, got {len(largest_file_size)}"
        assert isinstance(
            largest_file_size[0], Path
        ), f"Largest file size first element should be a Path, got {type(largest_file_size[0]).__name__}"
        assert isinstance(
            largest_file_size[1], int
        ), f"Largest file size second element should be an integer, got {type(largest_file_size[1]).__name__}"
        assert largest_file_size[1] == len(
            string_max
        ), f"Largest file size should be {len(string_max)}, got {largest_file_size[1]}"
        assert (
            largest_file_size[0] == file1
        ), f"Largest file should be {file1}, got {largest_file_size[0]}"

        assert isinstance(
            smallest_file_size, tuple
        ), f"Smallest file size should be a tuple, got {type(smallest_file_size).__name__}"
        assert (
            len(smallest_file_size) == 2
        ), f"Smallest file size tuple should have 2 elements, got {len(smallest_file_size)}"
        assert isinstance(
            smallest_file_size[0], Path
        ), f"Smallest file size first element should be a Path, got {type(smallest_file_size[0]).__name__}"
        assert isinstance(
            smallest_file_size[1], int
        ), f"Smallest file size second element should be an integer, got {type(smallest_file_size[1]).__name__}"
        assert smallest_file_size[1] == len(
            string_min
        ), f"Smallest file size should be {len(string_min)}, got {smallest_file_size[1]}"
        assert (
            smallest_file_size[0] == file2
        ), f"Smallest file should be {file2}, got {smallest_file_size[0]}"

        assert isinstance(
            average_file_size, float
        ), f"Average file size should be a float, got {type(average_file_size).__name__}"
        assert (
            average_file_size > 0
        ), f"Average file size should be greater than 0, got {average_file_size}"
        expected_average = total_size / len(data)
        assert average_file_size == pytest.approx(
            expected_average
        ), f"Average file size should be {expected_average}, got {average_file_size}"


# Test Cache


class TestStatisticsAdapterCache:
    """
    Test StatisticsAdapter cache functionality.

    Test:
    ------
    - Test StatisticsAdapter cache functionality.
    - Test StatisticsAdapter getters cache functionality.
    """

    @pytest.mark.parametrize("num_files", CACHE_TEST)
    def test_cache(self, num_files: int):
        """
        Test StatisticsAdapter cache functionality.

        Result Sample:
        --------------------
        - 100 entries:
            -   Time taken to report 100 entries without cache: 0.0048 seconds
            -   Time taken to report 100 entries with cache: 0.0000 seconds
        - 1000 entries:
            -   Time taken to report 1000 entries without cache: 0.0102 seconds
            -   Time taken to report 1000 entries with cache: 0.0132 seconds
        - 5000 entries:
            -   Time taken to report 5000 entries without cache: 0.1426 seconds
            -   Time taken to report 5000 entries with cache:  0.0254 seconds
        - 10000 entries:
            -   Time taken to report 10000 entries without cache:0.4935 seconds
            -   Time taken to report 10000 entries with cache: 0.0902 seconds
        - 50000 entries:
            -   Time taken to report 50000 entries without cache: 1.1983 seconds
            -   Time taken to report 50000 entries with cache: 0.2161 seconds
        - 100000 entries:
            -   Time taken to report 100000 entries without cache: 2.4905 seconds
            -   Time taken to report 100000 entries with cache: 0.3193 seconds
        """
        # Create some data
        data = make_data(num_files)

        # Start time for the report generation
        start_time: float = time.time()

        # Get the report without cache
        report_no_cache = StatisticsAdapter.get_report(data)

        end_time: float = time.time()
        no_cache_time: float = end_time - start_time
        # Debug print
        print(
            f"\nTime taken to report {num_files} entries without cache: {no_cache_time:.4f} seconds\n"
        )

        # Start time for the report generation with cache
        start_time = time.time()

        # Get the report with cache
        report_with_cache = StatisticsAdapter.get_report(data)

        end_time = time.time()
        with_cache_time: float = end_time - start_time
        # Debug print
        print(
            f"\nTime taken to report {num_files} entries with cache: {with_cache_time:.4f} seconds\n"
        )

        # Assert reports
        # Check if the report contains the expected keys
        assert "total_files" in report_with_cache
        assert "successful_reads" in report_with_cache
        assert "failed_reads" in report_with_cache
        assert "success_rate" in report_with_cache
        assert "failed_rate" in report_with_cache
        assert "successful_files" in report_with_cache
        assert "failed_files" in report_with_cache

        # Check if the values are of the expected types
        assert isinstance(report_with_cache["total_files"], int)
        assert isinstance(report_with_cache["successful_reads"], int)
        assert isinstance(report_with_cache["failed_reads"], int)
        assert isinstance(report_with_cache["success_rate"], float)
        assert isinstance(report_with_cache["failed_rate"], float)
        assert isinstance(report_with_cache["successful_files"], list)
        assert isinstance(report_with_cache["failed_files"], list)

        # Data list
        data_str_list = [str(path) for path in data.keys()]

        # Getters
        total_files = StatisticsAdapter.get_count_total_files(data)
        successful_reads = StatisticsAdapter.get_success_count(data)
        failed_reads = StatisticsAdapter.get_failure_count(data)
        success_rate = StatisticsAdapter.get_success_rate(data)
        failed_rate = StatisticsAdapter.get_failure_rate(data)
        successful_files = StatisticsAdapter.get_successful_files(data)
        failed_files = StatisticsAdapter.get_failed_files(data)

        # Check if the getters return the expected values
        assert (
            total_files == num_files
        ), f"Total files should be {num_files}, got {total_files}"
        assert (
            successful_reads == num_files
        ), f"Successful reads should be {num_files}, got {successful_reads}"
        assert failed_reads == 0, f"Failed reads should be 0, got {failed_reads}"
        assert success_rate == pytest.approx(
            100.0
        ), f"Success rate should be 100.0, got {success_rate}"
        assert failed_rate == pytest.approx(
            0.0
        ), f"Failed rate should be 0.0, got {failed_rate}"
        assert failed_files == [], f"Failed files should be empty, got {failed_files}"

    @pytest.mark.parametrize("num_files", CACHE_TEST)
    def test_getters_cache(self, num_files: int):
        """
        Test StatisticsAdapter getters cache functionality.

        Result Sample:
        --------------------
        - 100 entries:
            -   Time taken to get total files without cache for 100 entries: 0.0067 seconds
            -   Time taken to get total files with cache for 100 entries: 0.0000 seconds
        - 1000 entries:
            -   Time taken to get total files without cache for 1000 entries: 0.0244 seconds
            -   Time taken to get total files with cache for 1000 entries: 0.0000 seconds
        - 5000 entries:
            -   Time taken to get total files without cache for 5000 entries: 0.1861 seconds
            -   Time taken to get total files with cache for 5000 entries: 0.0291 seconds
        - 10000 entries:
            -   Time taken to get total files without cache for 10000 entries: 0.2363 seconds
            -   Time taken to get total files with cache for 10000 entries: 0.0785 seconds
        - 50000 entries:
            -   Time taken to get total files without cache for 50000 entries: 1.1492 seconds
            -   Time taken to get total files with cache for 50000 entries: 0.2219 seconds
        - 100000 entries:
            -   Time taken to get total files without cache for 100000 entries: 2.4031 seconds
            -   Time taken to get total files with cache for 100000 entries: 0.3351 seconds
        """
        # Create some data
        data = make_data(num_files)

        # Start time for the getters without cache
        start_time = time.time()

        # Get the count of total files without cache
        count_total_files_no_cache = StatisticsAdapter.get_count_total_files(data)

        end_time = time.time()
        no_cache_time = end_time - start_time
        # Debug print
        print(
            f"\nTime taken to get total files without cache for {num_files} entries: {no_cache_time:.4f} seconds\n"
        )

        # Start time for the getters with cache
        start_time = time.time()

        # Get the count of total files with cache
        count_total_files_with_cache = StatisticsAdapter.get_count_total_files(data)

        end_time = time.time()
        with_cache_time = end_time - start_time
        # Debug print
        print(
            f"\nTime taken to get total files with cache for {num_files} entries: {with_cache_time:.4f} seconds\n"
        )
