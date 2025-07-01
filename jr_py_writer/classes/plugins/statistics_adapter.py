# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
import os

from sqlite3 import DataError
from typing import List, Union, Dict
from pathlib import Path

# ----------------------------------------------------------------------------------------------
# Exceptions
# ----------------------------------------------------------------------------------------------

class StatisticsAdapterError(Exception):
    """
    Custom exception for StatisticsAdapter errors.
    This exception is raised when there is an error in the StatisticsAdapter class.
    """

    pass


class InvalidDataError(StatisticsAdapterError):
    """
    Exception raised when the provided data is not a dictionary or is empty.
    This exception is raised by methods in the StatisticsAdapter class when the input data is invalid.
    """

    pass


class GetError(StatisticsAdapterError):
    """
    Exception raised when there is an error in the get methods of StatisticsAdapter.
    This exception is raised when the data provided to the get methods is not a dictionary or is
    empty.
    """

    pass


# ----------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------

class StatisticsAdapter:
    """
    StatisticsAdapter
    ==========
    A utility class for generating statistical reports and analyzing data related to file processing. 
    This class provides methods to calculate success rates, failure rates, total file counts, 
    successful and failed file lists, and total file sizes.

    Methods:
    ---------
        #### get_report(data: Dict[Path, str | Exception]):
            Generate a comprehensive report from the provided data.
        #### print_report(data: Dict[Path, str | Exception]):
            Print the generated report to the console.
        #### get_success_count(data: Dict[Path, str | Exception]):
            Get the count of successful reads from the provided data.
        #### get_failure_count(data: Dict[Path, str | Exception]):
            Get the count of failed reads from the provided data.
        #### get_success_rate(data: Dict[Path, str | Exception]):
            Get the success rate from the provided data.
        #### get_failure_rate(data: Dict[Path, str | Exception]):
            Get the failure rate from the provided data.
        #### get_successful_files(data: Dict[Path, str | Exception]):
            Get the list of successful files from the provided data.
        #### get_failed_files(data: Dict[Path, str | Exception]):
            Get the list of failed files from the provided data.
        #### get_count_total_files(data: Dict[Path, str | Exception]):
            Get the total number of files in the provided data.
        #### get_total_size(data: Dict[Path, str | Exception]):
            Get the total size of the files in the provided data.

    Examples:
    ---------

    ```python
    # Example usage of StatisticsAdapter
    
    # Get report from data
    data = {
        Path("file1.txt"): "File content 1",
        Path("file2.txt"): "File content 2",
        Path("file3.txt"): Exception("File not found"),
    }

    report = StatisticsAdapter.get_report(data)
    print(report)

    # For pretty printing the report
    StatisticsAdapter.print_report(data)

    # Get success count
    success_count: int = StatisticsAdapter.get_success_count(data)

    # Get failure count
    failure_count: int = StatisticsAdapter.get_failure_count(data)
    ```
    ==========
    """

    @staticmethod
    def get_report(
        data: Dict[Path, str | Exception]
    ) -> Dict[str, Union[str, int, float, List[str]]]:
        """
        Generate a report from the provided data.

        Arguments:
            data (Dict[Path, str | Exception]): The data to generate the report from.

        Returns:
            out (Dict[str, Union[str, int, float, List[str]]]): A dictionary containing the report.
        
        Raises:
            ValueError: If the data is not a dictionary or is empty.
        """

        try:

            if not isinstance(data, dict):
                raise InvalidDataError("Data must be a dictionary for statistics analysis.")

            total_files = len(data)
            if total_files == 0:
                return {
                    "total_files": 0,
                    "successful_reads": 0,
                    "failed_reads": 0,
                    "success_rate": 0.0,
                    "successful_files": [],
                    "failed_files": [],
                    "total_size": 0,
                }

            # Prepare the report
            successful_reads = sum(1 for v in data.values() if isinstance(v, str))
            failed_reads = sum(1 for v in data.values() if isinstance(v, Exception))
            success_rate = (
                successful_reads / total_files if total_files > 0 else 0.0
            )
            failed_rates = sum(1 for v in data.values() if isinstance(v, Exception))
            successful_files = [
                str(path) for path, v in data.items() if isinstance(v, str)
            ]
            failed_files = [
                str(path) for path, v in data.items() if isinstance(v, Exception)
            ]
            total_size = sum(
                os.path.getsize(path) for path in data.keys() if isinstance(path, Path)
            )

            out = {
                "total_files": total_files,
                "successful_reads": successful_reads,
                "failed_reads": failed_reads,
                "success_rate": success_rate,
                "failed_rate": failed_rates,
                "successful_files": successful_files,
                "failed_files": failed_files,
                "total_size": total_size,
            }

            return out
        except Exception as e:
            raise GetError(f"Error generating report: {e}") from e
        

    @staticmethod
    def print_report(
        data: Dict[Path, str | Exception]
    ) -> None:
        """
        Print the report to the console or log it using the provided logger.

        Arguments:
            data (Dict[Path, str | Exception]): The data to generate the report from.
        """

        try:

            if not isinstance(data, dict) or not data:
                print("No data to generate report.")
                return

            report = StatisticsAdapter.get_report(data)

            list_of_successful_files = report.get('successful_files', [])
            list_of_failed_files = report.get('failed_files', [])

            string: str = "\n-- Statistics Report --\n"

            string += (
                f"Total Files: {report['total_files']}\n"
                f"Successful Reads: {report['successful_reads']}\n"
                f"Failed Reads: {report['failed_reads']}\n"
                f"Success Rate: {report['success_rate']:.2%}\n"
                f"Failed Rate: {report['failed_rate']:.2%}\n"
            )

            if list_of_successful_files and isinstance(list_of_successful_files, list):
                string += "Successful Files:\n"
                for file in list_of_successful_files:
                    string += f"  - {file}\n"
            else:
                string += "No successful files found.\n"
            
            if list_of_failed_files and isinstance(list_of_failed_files, list):
                string += "Failed Files:\n"
                for file in list_of_failed_files:
                    string += f"  - {file}\n"
            else:
                string += "No failed files found.\n"

            string += (
                f"Total Size of Files: {report['total_size']} bytes\n"
            )

            string += "-- End of Statistics Report --\n"

            # Print the report to the console
            print(string)
            
        except Exception as e:
            raise GetError(f"Error printing report: {e}") from e

    
    @staticmethod
    def get_success_count(
        data: Dict[Path, str | Exception]
    ) -> int:
        """
        Get the count of successful reads from the provided data.

        Arguments:
            data (Dict[Path, str | Exception]): The data to analyze.

        Returns:
            int: The count of successful reads.
        """

        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary for statistics analysis.")

        return sum(1 for v in data.values() if isinstance(v, str))


    @staticmethod
    def get_failure_count(
        data: Dict[Path, str | Exception]
    ) -> int:
        """
        Get the count of failed reads from the provided data.

        Arguments:
            data (Dict[Path, str | Exception]): The data to analyze.

        Returns:
            int: The count of failed reads.
        """

        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary for statistics analysis.")

        return sum(1 for v in data.values() if isinstance(v, Exception))
    

    @staticmethod
    def get_success_rate(
        data: Dict[Path, str | Exception]
    ) -> float:
        """
        Get the success rate from the provided data.

        Arguments:
            data (Dict[Path, str | Exception]): The data to analyze.

        Returns:
            float: The success rate.
        """

        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary for statistics analysis.")

        total_files = len(data)
        if total_files == 0:
            return 0.0

        successful_reads = StatisticsAdapter.get_success_count(data)
        return successful_reads / total_files


    @staticmethod
    def get_failure_rate(
        data: Dict[Path, str | Exception]
    ) -> float:
        """
        Get the failure rate from the provided data.

        Arguments:
            data (Dict[Path, str | Exception]): The data to analyze.

        Returns:
            float: The failure rate.
        """

        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary for statistics analysis.")

        total_files = len(data)
        if total_files == 0:
            return 0.0

        failed_reads = StatisticsAdapter.get_failure_count(data)
        return failed_reads / total_files
    

    @staticmethod
    def get_successful_files(
        data: Dict[Path, str | Exception]
    ) -> List[str]:
        """
        Get the list of successful files from the provided data.

        Arguments:
            data (Dict[Path, str | Exception]): The data to analyze.

        Returns:
            List[str]: A list of successful file paths.
        """

        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary for statistics analysis.")

        return [
            str(path) for path, v in data.items() if isinstance(v, str)
        ]


    @staticmethod
    def get_failed_files(
        data: Dict[Path, str | Exception]
    ) -> List[str]:
        """
        Get the list of failed files from the provided data.

        Arguments:
            data (Dict[Path, str | Exception]): The data to analyze.

        Returns:
            List[str]: A list of failed file paths.
        """

        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary for statistics analysis.")

        return [
            str(path) for path, v in data.items() if isinstance(v, Exception)
        ]
    

    @staticmethod
    def get_count_total_files(
        data: Dict[Path, str | Exception]
    ) -> int:
        """
        Get the total number of files in the provided data.

        Arguments:
            data (Dict[Path, str | Exception]): The data to analyze.

        Returns:
            int: The total number of files.
        """

        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary for statistics analysis.")

        return len(data)


    @staticmethod
    def get_total_size(
        data: Dict[Path, str | Exception]
    ) -> int:
        """
        Get the total size of the files in the provided data.

        Arguments:
            data (Dict[Path, str | Exception]): The data to analyze.

        Returns:
            int: The total size of the files.
        """

        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary for statistics analysis.")

        return sum(
            os.path.getsize(path) for path in data.keys() if isinstance(path, Path)
        )

