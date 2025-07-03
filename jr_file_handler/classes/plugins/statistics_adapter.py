# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
from functools import lru_cache

from typing import FrozenSet, List, Union, Dict, Any, Tuple
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


class ReportGenerationError(StatisticsAdapterError):
    """
    Exception raised when there is an error in the report generation methods of StatisticsAdapter.
    This exception is raised when the data provided to the report generation methods is not a dictionary or is
    empty.
    """

    pass


class GetError(StatisticsAdapterError):
    """
    Exception raised when there is an error in the get methods of StatisticsAdapter.
    This exception is raised when the data provided to the get methods is not a dictionary or is
    empty.
    """

    pass


class MakeHashableError(StatisticsAdapterError):
    """
    Exception raised when there is an error in the make_hashable function.
    This exception is raised when the input object cannot be converted to a hashable type.
    """

    pass


class DictOfHashableError(StatisticsAdapterError):
    """
    Exception raised when there is an error in the make_dict_of_hashable function.
    This exception is raised when the input data cannot be converted to a dictionary with hashable keys.
    """

    pass


# ----------------------------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------------------------


def make_hashable(obj: Any) -> Any:
    """
    Converts an object to a hashable type.

    Arguments:
        obj (Any): The object to be converted.

    Returns:
        out (Any) : A hashable version of the input object.
    """
    try:
        if isinstance(obj, (list, set)):
            return tuple(make_hashable(item) for item in obj)
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, dict):
            return frozenset((make_hashable(k), make_hashable(v)) for k, v in obj.items())
        elif isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, Exception):
            return (obj.__class__.__name__, str(obj))
        else:
            return str(obj)  # Convert other types to string
    except Exception as e:
        raise MakeHashableError(f"Error converting object to hashable type: {e}") from e


def make_dict_of_hashable(
    data: Tuple[FrozenSet]
) -> Dict[Path, Union[str, Exception]]:
    """
    Converts a frozen set of data to a dictionary with hashable keys.

    Arguments:
        data (FrozenSet): The frozen set of data to be converted.

    Returns:
        out (Dict[Path, Union[str, Exception]]) : A dictionary with hashable keys.
    """
    try:
        out = {Path(str(key)): value for key, value in data}

        if not out:
            raise InvalidDataError("Data dictionary is empty. Cannot convert to dictionary of hashable keys.")

        for key, value in out.items():
            if not isinstance(key, Path):
                raise TypeError(f"Key {key} is not a Path object.")
            if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str):
                # Dynamically create the exception using the class name and message
                exception_class = globals().get(value[0], Exception)
                if issubclass(exception_class, Exception):
                    out[key] = exception_class(value[1])
                else:
                    out[key] = Exception(f"{value[1]}: Invalid exception class: {value[0]}")
            elif not isinstance(value, (str, Exception)):
                raise TypeError(f"Value {value} is not a str or Exception, it is {type(value).__name__}.")
                
        return out
    except Exception as e:
        raise DictOfHashableError(f"Error converting data to dictionary of hashable keys: {e}") from e


def _validate_dict(
    data: Dict[Path, Union[str, Exception]]
) -> None:
    """
    Validates that the provided dictionary has Path keys and values of type str or Exception.

    Arguments:
        data (Dict[Path, Union[str, Exception]]): The dictionary to validate.

    Raises:
        TypeError: If the keys are not Path objects or the values are not str or Exception.
    """
    if not isinstance(data, dict):
        raise InvalidDataError(f"Data must be a dictionary, got {type(data).__name__}.")
    if not data:
        raise InvalidDataError("Data dictionary is empty.")

    for key, value in data.items():
        if not isinstance(key, Path):
            raise TypeError(f"Key {key} in data is not a Path object, it is {type(key).__name__}.")
        if not isinstance(value, (str, Exception)):
            raise TypeError(f"Value {value} in data is not a str or Exception, it is {type(value).__name__}.")


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
        #### get_dict_with_exceptions(data: Dict[Path, str | Exception]):
            Get a dictionary with exceptions from the provided data.
        #### get_list_of_exceptions(data: Dict[Path, str | Exception]):
            Get a list of exceptions from the provided data.
    
    Size Methods:
    ------------
    - This will only work if the Path objects in the data dictionary point to actual files on disk.
        #### get_total_size_of_files(data: Dict[Path, str | Exception]):
            Get the total size of files in the provided data.
        #### get_largest_file_size(data: Dict[Path, str | Exception]):
            Get the largest file in the provided data.
        #### get_smallest_file_size(data: Dict[Path, str | Exception]):
            Get the smallest file in the provided data.
        #### get_average_file_size(data: Dict[Path, str | Exception]):
            Get the average file size in the provided data.

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
    @lru_cache(maxsize=128)
    def _c_get_report(
        data: Tuple[FrozenSet]
    ) -> Dict[str, Union[str, int, float, List[str]]]:
        """
        Generate a report from the provided data.

        Arguments:
            data (Tuple[FrozenSet]): The data to generate the report from, converted to a hashable format.

        Returns:
            out (Dict[str, Union[str, int, float, List[str]]]): A dictionary containing the report.
        """
        # Get Dictionary of hashable keys
        dict_data = make_dict_of_hashable(data)

        # If the dictionary is empty, return an empty report
        total_files = len(dict_data)
        if total_files == 0:
            return {
                "total_files": 0,
                "successful_reads": 0,
                "failed_reads": 0,
                "success_rate": 0.0,
                "failed_rate": 0.0,
                "successful_files": [],
                "failed_files": [],
            }

        # Get Stats

        successful_files = [
        str(path) for path, v in dict_data.items() if isinstance(v, str)
        ]

        failed_files = [
            str(path) for path, v in dict_data.items() if isinstance(v, Exception)
        ]

        successful_reads = len(successful_files)
        failed_reads = len(failed_files)

        success_rate = (successful_reads / total_files) * 100  if total_files > 0 else 0.0
        failed_rate = (failed_reads / total_files) * 100 if total_files > 0 else 0.0

        # Return the report
        return {
            "total_files": total_files,
            "successful_reads": successful_reads,
            "failed_reads": failed_reads,
            "success_rate": success_rate,
            "failed_rate": failed_rate,
            "successful_files": successful_files,
            "failed_files": failed_files
        }


    @staticmethod
    def get_report(data: Dict[Path, str | Exception]) -> Dict[str, Union[str, int, float, List[str]]]:
        """
        Generate a report from the provided data.

        Arguments:
            data (Dict[Path, str | Exception]): The original data to generate the report from.

        Returns:
            out (Dict[str, Union[str, int, float, List[str]]]) : The generated report.

        Note:
        ------
            This method is a wrapper around the _c_get_report method to ensure that the input data is a cached dictionary.
        """
        try:
            # Validate input data
            _validate_dict(data)
            
            # Convert the data to a hashable format
            # This is necessary for caching purposes
            hashable_data = make_hashable(data)

            # Call the cached report generation method
            # This will return a cached report if the same data has been processed before
            return StatisticsAdapter._c_get_report(hashable_data)
        except Exception as e:
            raise ReportGenerationError(f"Error generating report: {e}") from e
        

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
        try:
            # Validate input data
            _validate_dict(data)

            # get cached report
            result = StatisticsAdapter.get_report(data).get('successful_reads', 0)

            # Type assertion
            if isinstance(result, int):
                return result
            
            # Probably wont happen, but just in case         
            raise TypeError(f"Expected 'successful_reads' to be of type int, but got {type(result).__name__}")
        
        except Exception as e:
            raise GetError(f"Error getting success count: {e}") from e


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
        try:
            # Validate input data
            _validate_dict(data)

            # get cached report
            result = StatisticsAdapter.get_report(data).get('failed_reads', 0)

            # Type assertion
            if isinstance(result, int):
                return result
            
            # Probably wont happen, but just in case         
            raise TypeError(f"Expected 'failed_reads' to be of type int, but got {type(result).__name__}")

        except Exception as e:
            raise GetError(f"Error getting failure count: {e}") from e


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
        try:
            # Validate input data
            _validate_dict(data)

            # get cached report
            successful_reads = StatisticsAdapter.get_report(data).get('success_rate', 0)

            # Type assertion
            if isinstance(successful_reads, (float, int)):
                return successful_reads

            # Probably wont happen, but just in case         
            raise TypeError(f"Expected 'success_rate' to be of type float or int, but got {type(successful_reads).__name__}")

        except Exception as e:
            raise GetError(f"Error getting success rate: {e}") from e


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
        try:
            # Validate input data
            _validate_dict(data)

            # get cached report
            failed_reads = StatisticsAdapter.get_report(data).get('failed_rate', 0)

            # Type assertion
            if isinstance(failed_reads, (float, int)):
                return failed_reads
            
            # Probably wont happen, but just in case         
            raise TypeError(f"Expected 'failed_rate' to be of type float or int, but got {type(failed_reads).__name__}")
        except Exception as e:
            raise GetError(f"Error getting failure rate: {e}") from e
        

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
        try:
            # Validate input data
            _validate_dict(data)

            # get cached report
            successful_files = StatisticsAdapter.get_report(data).get('successful_files', [])

            # Type assertion
            if isinstance(successful_files, list):
                return successful_files
            
            # Probably wont happen, but just in case         
            raise TypeError(f"Expected 'successful_files' to be of type list, but got {type(successful_files).__name__}")

        except Exception as e:
            raise GetError(f"Error getting successful files: {e}") from e


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
        try:
            # Validate input data
            _validate_dict(data)

            # get cached report
            failed_files = StatisticsAdapter.get_report(data).get('failed_files', [])

            # Type assertion
            if isinstance(failed_files, list):
                return failed_files

            # Probably wont happen, but just in case         
            raise TypeError(f"Expected 'failed_files' to be of type list, but got {type(failed_files).__name__}")
        
        except Exception as e:
            raise GetError(f"Error getting failed files: {e}") from e
        

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
        try:
            # Validate input data
            _validate_dict(data)

            # get cached report
            total_files = StatisticsAdapter.get_report(data).get('total_files', 0)

            # Type assertion
            if isinstance(total_files, int):
                return total_files
            
            # Probably wont happen, but just in case         
            raise TypeError(f"Expected 'total_files' to be of type int, but got {type(total_files).__name__}")
        except Exception as e:
            raise GetError(f"Error getting total file count: {e}") from e


    @staticmethod
    def get_dict_with_exceptions(
        data: Dict[Path, str | Exception]
    ) -> Dict[Path, Exception]:
        """
        Get a dictionary with exceptions from the provided data.

        Arguments:
            data (Dict[Path, str | Exception]): The data to analyze.

        Returns:
            Dict[Path, Exception]: A dictionary with Path keys and Exception values.
        """
        try:
            # Validate input data
            _validate_dict(data)

            # Extract exceptions from the data
            out = {k: v for k, v in data.items() if isinstance(v, Exception)}

            return out

        except Exception as e:
            raise GetError(f"Error getting dictionary with exceptions: {e}") from e


    @staticmethod
    def get_list_of_exceptions(
        data: Dict[Path, str | Exception]
    ) -> List[Exception]:
        """
        Get a list of exceptions from the provided data.

        Arguments:
            data (Dict[Path, str | Exception]): The data to analyze.

        Returns:
            List[Exception]: A list of exceptions.
        """
        try:
            # Validate input data
            _validate_dict(data)

            # Extract exceptions from the data
            exceptions = [v for v in data.values() if isinstance(v, Exception)]

            return exceptions

        except Exception as e:
            raise GetError(f"Error getting list of exceptions: {e}") from e

    
    @staticmethod
    def get_total_size_of_files(
        data: Dict[Path, str | Exception]
    ) -> int:
        """
        Get the total size of files in the provided data.

        Arguments:
            data (Dict[Path, str | Exception]): The data to analyze.

        Returns:
            int: The total size of files in bytes.
        """
        try:
            # Validate input data
            _validate_dict(data)

            total_size = sum(path.stat().st_size for path in data if isinstance(path, Path) and path.exists())

            return total_size

        except Exception as e:
            raise GetError(f"Error getting total size of files: {e}") from e


    @staticmethod
    def get_largest_file_size(
        data: Dict[Path, str | Exception]
    ) -> Tuple[Path | None, int]:
        """
        Get the largest file in the provided data.

        Arguments:
            data (Dict[Path, str | Exception]): The data to analyze.

        Returns:
            Tuple[Path | None, int]: A tuple containing the Path of the largest file and its size in bytes.
        """
        try:
            # Validate input data
            _validate_dict(data)

            largest_file = max(
                (path for path in data if isinstance(path, Path) and path.exists()),
                key=lambda p: p.stat().st_size,
                default=None
            )

            if largest_file is None:
                return None, 0

            return largest_file, largest_file.stat().st_size

        except Exception as e:
            raise GetError(f"Error getting largest file: {e}") from e


    @staticmethod
    def get_smallest_file_size(
        data: Dict[Path, str | Exception]
    ) -> Tuple[Path | None, int]:
        """
        Get the smallest file in the provided data.

        Arguments:
            data (Dict[Path, str | Exception]): The data to analyze.

        Returns:
            Tuple[Path | None, int]: A tuple containing the Path of the smallest file and its size in bytes.
        """
        try:
            # Validate input data
            _validate_dict(data)

            smallest_file = min(
                (path for path in data if isinstance(path, Path) and path.exists()),
                key=lambda p: p.stat().st_size,
                default=None
            )

            if smallest_file is None:
                return None, 0

            return smallest_file, smallest_file.stat().st_size

        except Exception as e:
            raise GetError(f"Error getting smallest file: {e}") from e


    @staticmethod
    def get_average_file_size(
        data: Dict[Path, str | Exception]
    ) -> float:
        """
        Get the average file size in the provided data.

        Arguments:
            data (Dict[Path, str | Exception]): The data to analyze.

        Returns:
            float: The average file size in bytes.
        """
        try:
            # Validate input data
            _validate_dict(data)

            total_size = StatisticsAdapter.get_total_size_of_files(data)
            total_files = StatisticsAdapter.get_count_total_files(data)

            if total_files == 0:
                return 0.0

            return total_size / total_files

        except Exception as e:
            raise GetError(f"Error getting average file size: {e}") from e

