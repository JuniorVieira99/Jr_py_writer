# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
from pathlib import Path
from typing import Any, List, Final, Dict

# Third-party imports
import pytest

# Local imports
from jr_py_writer.classes.plugins.statistics_adapter import StatisticsAdapter

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

# Get Report

def test_get_report():
    """Test StatisticsAdapter.get_report."""

    # Add some data
    data = make_data(5)

    # Get the report
    report = StatisticsAdapter.get_report(data)

    # Check if the report is a dictionary
    assert isinstance(report, dict)

    # Check if the report contains the expected keys
    assert 'total_files' in report
    assert 'successful_reads' in report
    assert 'failed_reads' in report
    assert 'success_rate' in report
    assert 'failed_rate' in report
    assert 'successful_files' in report
    assert 'failed_files' in report
    assert 'total_size' in report

    # Check if the values are of the expected types
    assert isinstance(report['total_files'], int)
    assert isinstance(report['successful_reads'], int)
    assert isinstance(report['failed_reads'], int)
    assert isinstance(report['success_rate'], float)
    assert isinstance(report['failed_rate'], float)
    assert isinstance(report['successful_files'], list)
    assert isinstance(report['failed_files'], list)
    assert isinstance(report['total_size'], int)

    # Check Values
    assert report['total_files'] == 5
    assert report['successful_reads'] == 5
    assert report['failed_reads'] == 0
    assert report['success_rate'] == pytest.approx(100.0)
    assert report['failed_rate'] == pytest.approx(0.0)
    assert report['successful_files'] == list(data.keys())
    assert report['failed_files'] == []

    # Getters

    total_files = StatisticsAdapter.get_count_total_files(data)
    successful_reads = StatisticsAdapter.get_success_count(data)
    failed_reads = StatisticsAdapter.get_failure_count(data)
    success_rate = StatisticsAdapter.get_success_rate(data)
    failed_rate = StatisticsAdapter.get_failure_rate(data)
    successful_files = StatisticsAdapter.get_successful_files(data)
    failed_files = StatisticsAdapter.get_failed_files(data)
    total_size = StatisticsAdapter.get_total_size(data)

    # Check if the getters return the expected values
    assert total_files == 5
    assert successful_reads == 5
    assert failed_reads == 0
    assert success_rate == pytest.approx(100.0)
    assert failed_rate == pytest.approx(0.0)
    assert successful_files == list(data.keys())
    assert failed_files == []
    assert total_size == sum(len(content) for content in data.values() if isinstance(content, str))



