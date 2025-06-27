# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
from dataclasses import dataclass, field

from typing import Any, Generator, Dict, List
from pathlib import Path
from threading import Lock

# Local application imports
from jr_py_writer.classes.reader_result import ReaderResult, ReaderResultStr, ReaderResultGenerator

# ----------------------------------------------------------------------------------------------
# Exceptions
# ----------------------------------------------------------------------------------------------

class ReaderResultPackError(Exception):
    """
    Custom exception for ReaderResultPack errors.
    
    This exception is raised when there are issues with the ReaderResultPack, such as invalid operations or data.
    """

    pass


class ConstructError(ReaderResultPackError):
    """
    Custom exception for construction errors in ReaderResultPack.
    
    This exception is raised when there are issues during the construction of the ReaderResultPack, such as invalid data types or missing attributes.
    """

    pass


class GetterError(ReaderResultPackError):
    """
    Custom exception for getter errors in ReaderResultPack.
    
    This exception is raised when there are issues during the retrieval of attributes from the ReaderResultPack, such as invalid data types or missing attributes.
    """

    pass


class SetterError(ReaderResultPackError):
    """
    Custom exception for setter errors in ReaderResultPack.
    
    This exception is raised when there are issues during the setting of attributes in the ReaderResultPack, such as invalid data types or values.
    """

    pass


class MagicMethodError(ReaderResultPackError):
    """
    Custom exception for magic method errors in ReaderResultPack.
    
    This exception is raised when there are issues with the implementation of magic methods in the ReaderResultPack, such as incorrect comparisons or hashing.
    """

    pass


class UnpackError(ReaderResultPackError):
    """
    Custom exception for unpacking errors in ReaderResultPack.
    
    This exception is raised when there are issues during the unpacking of the ReaderResultPack, such as invalid data types or missing attributes.
    """

    pass


class AddError(ReaderResultPackError):
    """
    Custom exception for adding errors in ReaderResultPack.
    
    This exception is raised when there are issues during the addition of results to the ReaderResultPack, such as invalid data types or values.
    """

    pass


class RemoveError(ReaderResultPackError):
    """
    Custom exception for removing errors in ReaderResultPack.
    
    This exception is raised when there are issues during the removal of results from the ReaderResultPack, such as invalid data types or values.
    """

    pass


class ClearError(ReaderResultPackError):
    """
    Custom exception for clearing errors in ReaderResultPack.
    
    This exception is raised when there are issues during the clearing of results in the ReaderResultPack, such as invalid data types or values.
    """

    pass


# ----------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------
    
@dataclass
class ReaderResultPack:
    """
    ReaderResultPack
    =================
    A class designed to manage and manipulate a collection of `ReaderResult` objects. It provides functionality for 
    adding, removing, and retrieving results, as well as calculating statistics such as success and failure rates.

    Attributes
    ----------
    results : Dict[Path, List[ReaderResult]]
        -   A dictionary where keys are file paths (Path objects) and values are lists of `ReaderResult` objects.
        -   This allows for efficient storage and retrieval of results associated with specific file paths.
    lock : Lock
        A threading lock used to ensure thread-safe operations on the `results` list.

    Notes
    -------
    -   This class is thread-safe.
    -   Magic Methods for comparison, hashing, and string representation are implemented to allow for easy manipulation and display of the `ReaderResultPack` object.
        Along with adding `ReaderResultPack` objects, it also supports iteration over the results.
    -   The class provides methods to calculate statistics such as total path count, total results count, success count, failure count, success rate, and failure rate.
    -   It also provides methods to retrieve all results, successful results, failed results, generator results, and string results.

    Properties
    -------
    - **results (Dict[Path, List[ReaderResult]])**: A dictionary where keys are file paths (Path objects) and values are lists of `ReaderResult` objects.
    - **cached_dict (Dict[str, Any])**: A cached dictionary containing statistics about the pack, such as total path count, total results count, success count, failure count, success rate, and failure rate.
    - **Statistics:**
        -   **total_path_count (int)**: The total number of unique file paths in the pack.
        -   **total_results_count (int)**: The total number of `ReaderResult` objects in the pack.
        -   **success_count (int)**: The number of successful `ReaderResult` objects in the pack.
        -   **failure_count (int)**: The number of failed `ReaderResult` objects in the pack.
        -   **success_rate (float)**: The success rate of `ReaderResult` objects in the pack, calculated as a percentage.
        -   **failure_rate (float)**: The failure rate of `ReaderResult` objects in the pack, calculated as a percentage.
    - **Retrieval:**
        -   **success_results (List[ReaderResult])**: A list of successful `ReaderResult` objects.
        -   **failure_results (List[ReaderResult])**: A list of failed `ReaderResult` objects.
        -   **success_paths (List[Path])**: A list of file paths for successful `ReaderResult` objects.
        -   **failure_paths (List[Path])**: A list of file paths for failed `ReaderResult` objects.
        -   **get_all_results (List[ReaderResult])**: A list of all `ReaderResult` objects in the pack.
        -   **get_all_paths (List[Path])**: A list of all file paths in the pack.
        -   **get_all_generator_results (List[ReaderResultGenerator])**: A list of all `ReaderResultGenerator` objects in the pack.
        -   **get_all_str_results (List[ReaderResultStr])**: A list of all `ReaderResultStr` objects in the pack.
    - **Summary:**
        -   **get_summary()**: Returns a summary string of the pack, including total paths, total results, success count, failure count, success rate, and failure rate.
        -   **get_full_report()**: Returns a full report of the pack as a dictionary, including all results and their attributes.
        -   **print_full_report()**: Prints a full report of the pack, including all results and their attributes.
        -   **print_summary()**: Prints a summary of the pack to the console.
    
    Methods
    -------
    - **Add and Remove methods:**
        add_result(result: ReaderResult) -> None
        add_results(results: list[ReaderResult]) -> None
        remove_result(path: Path) -> None
        remove_results(paths: list[Path]) -> None
        clear_results() -> None
    - **Unpacking methods:**
        in_unpack() -> None
        unpack() -> 'ReaderResultPack'
    
    Example
    -------
    ```python

    # Create ReaderResult objects
    result1 = ReaderResultStr(content="File content 1", file_path=Path("/path/to/file1.txt"))
    result2 = ReaderResultStr(content="File content 2", file_path=Path("/path/to/file2.txt"), exception=ValueError("Invalid content"))
    result3 = ReaderResultGenerator(content_generator=(f"Line {i}" for i in range(5)), file_path=Path("/path/to/file3.txt"))

    # Create a ReaderResultPack and add results
    pack = ReaderResultPack()
    pack.add_result(result1)
    pack.add_result(result2)
    pack.add_result(result3)

    # Print summary
    pack.print_summary()

    # Get all successful results
    success_results = pack.success_results
    print("Successful Results:")
    for res in success_results:
        print(res)

    # Get all failed results
    failure_results = pack.failure_results
    print("Failed Results:")
    for res in failure_results:
        print(res)

    # Unpack the pack (convert generators to strings)
    unpacked_pack = pack.unpack()
    print("Unpacked Results:")
    for res in unpacked_pack.get_all_results:
        print(res)

    # Unpack the pack in-place
    pack.in_unpack()

    # Print full report
    pack.print_full_report()
    ``` 

    """
    
    # --------------
    # Attributes

    _results: Dict[Path, List[ReaderResult]] = field(default_factory=dict, repr=False)
    lock: Lock = field(default_factory=Lock, init=False, repr=False)
    _total_path_count: int = field(init=False, default=0, repr=False)
    _total_results_count: int = field(init=False, default=0, repr=False)
    _success_count: int = field(init=False, default=0, repr=False)
    _failure_count: int = field(init=False, default=0, repr=False)
    _success_rate: float = field(init=False, default=0.0, repr=False)
    _failure_rate: float = field(init=False, default=0.0, repr=False)
    _cached_dict: Dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    # --------------
    # Constructors
    
    def __post_init__(self):
        """
        Post-Init
        ==========
        This method is called after the initialization of the ReaderResultPack object to perform additional
        validation and type checking on the results attribute.
        """
        try:
            if not isinstance(self.results, dict):
                raise TypeError(f"Results must be a dict, got {type(self.results)}")
            
            if len(self.results) != 0:
                for path, list_res in self.results.items():
                    if not isinstance(path, Path):
                        raise TypeError(f"Path must be a Path object, got {type(path)}")
                    if not isinstance(list_res, list):
                        raise TypeError(f"Results must be a list, got {type(list_res)}")
                    for res in list_res:
                        if not isinstance(res, ReaderResult):
                            raise TypeError(f"Each result must be a ReaderResultStr or ReaderResultGenerator object, got {type(res)}")
                    
                        # Update Statistics
                        self._total_results_count += 1
                        self._success_count += 1 if res.exception is None else 0
                        self._failure_count += 1 if res.exception is not None else 0

            # Update success and failure rates
            self._total_path_count = len(self.results)
            self._success_rate = self._get_success_rate()
            self._failure_rate = self._get_failure_rate()

            # Cache Dict Update
            self._cached_dict = {
                'total_results_count': self._total_results_count,
                'total_path_count': self._total_path_count,
                'success_count': self._success_count,
                'failure_count': self._failure_count,
                'success_rate': self._success_rate,
                'failure_rate': self._failure_rate,
            }

            # Initialize the lock if it does not exist
            if not hasattr(self, 'lock'):
                self.lock = Lock()
        except Exception as e:
            raise ConstructError(f"Error during ReaderResultPack construction: {e}") from e


    # --------------
    # Properties

    @property
    def results(self) -> Dict[Path, List[ReaderResult]]:
        """
        Returns the results dictionary containing ReaderResult objects.
        
        This is a read-only property that returns the results dictionary.
        
        Returns:
            Dict[Path, List[ReaderResult]]: The results dictionary.
        """
        return self._results


    @property
    def total_path_count(self) -> int:
        """
        Returns the total path count of ReaderResult objects in the pack.
        
        This is a read-only property that returns the number of unique file paths in the results.
        
        Returns:
            int: The total number of unique file paths in the pack.
        """
        return self._total_path_count
    

    @property
    def total_results_count(self) -> int:
        """
        Returns the total count of ReaderResult objects in the pack.
        
        This is a read-only property that returns the total number of ReaderResult objects, regardless of whether they are successful or failed.
        
        Returns:
            int: The total number of ReaderResult objects in the pack.
        """
        return self._total_results_count


    @property
    def success_count(self) -> int:
        """
        Returns the count of successful ReaderResult objects in the pack.
        
        A ReaderResult is considered successful if it does not have an exception.
        
        Returns:
            int: The number of successful ReaderResult objects in the pack.
        """
        return self._success_count


    @property
    def failure_count(self) -> int:
        """
        Returns the count of failed ReaderResult objects in the pack.
        
        A ReaderResult is considered failed if it has an exception.
        
        Returns:
            int: The number of failed ReaderResult objects in the pack.
        """
        return self._failure_count    


    @property
    def success_rate(self) -> float:
        """
        Returns the success rate of ReaderResult objects in the pack.
        
        The success rate is calculated as the number of successful results divided by the total number of results.
        
        Returns:
            float: The success rate as a percentage (0.0 to 100.0).
        """
        return self._success_rate
    

    @property
    def failure_rate(self) -> float:
        """
        Returns the failure rate of ReaderResult objects in the pack.
        
        The failure rate is calculated as the number of failed results divided by the total number of results.
        
        Returns:
            float: The failure rate as a percentage (0.0 to 100.0).
        """
        return self._failure_rate
    

    @property
    def success_paths(self) -> List[Path | None]:
        """
        Returns a list of file paths that have successful ReaderResult objects.
        
        A ReaderResult is considered successful if it does not have an exception.
        
        Returns:
            List[Path | None]: A list of file paths with successful ReaderResult objects.
        """
        try:
            return self._get_success_paths()
        except Exception as e:
            raise GetterError(f"Error retrieving success paths: {e}") from e
    

    @property
    def success_results(self) -> List[ReaderResult]:
        """
        Returns a list of all successful ReaderResult objects in the pack.
        
        A ReaderResult is considered successful if it does not have an exception.
        
        Returns:
            List[ReaderResult]: A list of all successful ReaderResult objects in the pack.
        """
        try:
            return self._get_all_successful_results()
        except Exception as e:
            raise GetterError(f"Error retrieving successful results: {e}") from e


    @property
    def failure_paths(self) -> List[Path | None]:
        """
        Returns a list of file paths that have failed ReaderResult objects.
        
        A ReaderResult is considered failed if it has an exception.
        
        Returns:
            List[Path | None]: A list of file paths with failed ReaderResult objects.
        """
        try:
            return self._get_failure_paths()
        except Exception as e:
            raise GetterError(f"Error retrieving failure paths: {e}") from e
    

    @property
    def failure_results(self) -> List[ReaderResult]:
        """
        Returns a list of all failed ReaderResult objects in the pack.
        
        A ReaderResult is considered failed if it has an exception.
        
        Returns:
            List[ReaderResult]: A list of all failed ReaderResult objects in the pack.
        """
        try:
            return self._get_all_failure_results()
        except Exception as e:
            raise GetterError(f"Error retrieving failed results: {e}") from e


    @property
    def get_all_results(self) -> List[ReaderResult]:
        """
        Returns a list of all ReaderResult objects in the pack.
        
        This includes both successful and failed ReaderResult objects.
        
        Returns:
            List[ReaderResult]: A list of all ReaderResult objects in the pack.
        """
        try:
            return self._get_all_results()
        except Exception as e:
            raise GetterError(f"Error retrieving all results: {e}") from e


    @property
    def get_all_paths(self) -> List[Path | None]:
        """
        Returns a list of all file paths in the pack.
        
        This includes both successful and failed ReaderResult objects.
        
        Returns:
            List[Path | None]: A list of all file paths in the pack.
        """
        try:
            return self._get_all_paths()
        except Exception as e:
            raise GetterError(f"Error retrieving all paths: {e}") from e


    @property
    def get_all_generator_results(self) -> List[ReaderResultGenerator]:
        """
        Returns a list of all ReaderResultGenerator objects in the pack.
        
        This includes only ReaderResult objects that are instances of ReaderResultGenerator.
        
        Returns:
            List[ReaderResultGenerator]: A list of all ReaderResultGenerator objects in the pack.
        """
        try:
            return self._get_all_generator_results()
        except Exception as e:
            raise GetterError(f"Error retrieving all generator results: {e}") from e
        

    @property
    def get_all_str_results(self) -> List[ReaderResultStr]:
        """
        Returns a list of all ReaderResultStr objects in the pack.
        
        This includes only ReaderResult objects that are instances of ReaderResultStr.
        
        Returns:
            List[ReaderResultStr]: A list of all ReaderResultStr objects in the pack.
        """
        try:
            return self._get_all_str_results()
        except Exception as e:
            raise GetterError(f"Error retrieving all string results: {e}") from e
        

    @property
    def get_summary(self) -> str:
        """
        Returns a summary of the ReaderResultPack.
        
        The summary includes the total path count, total results count, success count, failure count,
        success rate, and failure rate.
        
        Returns:
            str: A summary string of the ReaderResultPack.
        """
        try:
            summary = (
                f"Total Results: {self.total_results_count}\n"
                f"Successful Results: {self.success_count} ({self.success_rate:.2f}%)\n"
                f"Failed Results: {self.failure_count} ({self.failure_rate:.2f}%)\n"
            )
            return summary
        except Exception as e:
            raise GetterError(f"Error generating summary: {e}") from e
        

    @property
    def cached_dict(self) -> Dict[str, Any]:
        """
        Returns the cached dictionary containing statistics of the ReaderResultPack.
        
        This dictionary includes total results count, total path count, success count, failure count,
        success rate, and failure rate.
        
        Returns:
            Dict[str, Any]: The cached dictionary with statistics.
        """
        return self._cached_dict


    @property
    def get_full_report(self) -> str:
        """
        Returns a full report of the ReaderResultPack.
        
        The report includes detailed information about each ReaderResult object, including content,
        file path, and exception (if any).
        
        Returns:
            str: A full report string of the ReaderResultPack.
        """
        try:
            string: str = ""
            string += self.__str__()
            string += self.get_summary
            for path, result in self.results.items():
                string += f"\nResults for {path}:\n"
                for res in result:
                    string += "\t" + res.__str__() + "\n"

            return string
        except Exception as e:
            raise GetterError(f"Error generating full report: {e}") from e


    # --------------
    # Setters

    @results.setter
    def results(self, value: Dict[Path, List[ReaderResult]]) -> None:
        """
        Sets the results dictionary containing ReaderResult objects.
        
        This is a setter method that allows you to manually set the results dictionary.
        
        Args:
            value (Dict[Path, List[ReaderResult]]): The new results dictionary to be set.
        
        Raises:
            TypeError: If the value is not a dictionary or if the keys are not Path objects.
            ValueError: If the value is empty.
        """
        try:
            if not isinstance(value, dict):
                raise TypeError(f"Results must be a dict, got {type(value)}")
            
            if len(value) == 0:
                raise ValueError("Results cannot be empty")

            for path, list_res in value.items():
                if not isinstance(path, Path):
                    raise TypeError(f"Path must be a Path object, got {type(path)}")
                if not isinstance(list_res, list):
                    raise TypeError(f"Results must be a list, got {type(list_res)}")
                for res in list_res:
                    if not isinstance(res, ReaderResult):
                        raise TypeError(f"Each result must be a ReaderResultStr or ReaderResultGenerator object, got {type(res)}")

            # Cache update
            self._update_cache()
            self._results = value

        except Exception as e:
            raise SetterError(f"Error setting results: {e}") from e

    
    # --------------
    # Helpers

    def _update_cache(self):
        """
        Updates the cached dictionary with the current statistics of the ReaderResultPack.
        """
        self._total_path_count = self._get_total_path_count()
        self._total_results_count = self._get_total_results_count()
        self._success_count = self._get_success_count()
        self._failure_count = self._get_failure_count()
        self._success_rate = self._get_success_rate()
        self._failure_rate = self._get_failure_rate()
        self._cached_dict.update({
            'total_path_count': self._total_path_count,
            'total_results_count': self._total_results_count,
            'success_count': self._success_count,
            'failure_count': self._failure_count,
            'success_rate': self._success_rate,
            'failure_rate': self._failure_rate
        })
    

    def _get_total_result_count(self) -> int:
        """
        Returns the total count of ReaderResult objects in the pack.
        
        This includes all ReaderResult objects, regardless of whether they are successful or failed.
        
        Returns:
            int: The total number of ReaderResult objects in the pack.
        """
        return sum(len(list_results) for list_results in self.results.values())


    def _get_success_count(self) -> int:
        """
        Returns the count of successful ReaderResult objects in the pack.
        
        A ReaderResult is considered successful if it does not have an exception.
        
        Returns:
            int: The number of successful ReaderResult objects in the pack.
        """
        return sum(1 for _, list_results in self.results.items() for res in list_results if res.exception is None)


    def _get_failure_count(self) -> int:
        """
        Returns the count of failed ReaderResult objects in the pack.
        
        A ReaderResult is considered failed if it has an exception.
        
        Returns:
            int: The number of failed ReaderResult objects in the pack.
        """
        return sum(1 for _, list_results in self.results.items() for res in list_results if res.exception is not None)


    def _get_total_path_count(self) -> int:
        """
        Returns the total path count of ReaderResult objects in the pack.
        
        Returns:
            int: The total number of ReaderResult objects in the pack.
        """
        return len(self.results)
    

    def _get_total_results_count(self) -> int:
        """
        Returns the total count of ReaderResult objects in the pack.
        
        This includes all ReaderResult objects, regardless of whether they are successful or failed.
        
        Returns:
            int: The total number of ReaderResult objects in the pack.
        """
        return sum(len(list_results) for list_results in self.results.values())
    

    def _get_success_rate(self) -> float:
        """
        Returns the success rate of ReaderResult objects in the pack.
        
        The success rate is calculated as the number of successful results divided by the total number of results.
        
        Returns:
            float: The success rate as a percentage (0.0 to 100.0).
        """
        total_count = self._get_total_results_count()
        if total_count == 0:
            return 0.0
        
        success_count = self._get_success_count()
        return (success_count / total_count) * 100.0


    def _get_failure_rate(self) -> float:
        """
        Returns the failure rate of ReaderResult objects in the pack.
        
        The failure rate is calculated as the number of failed results divided by the total number of results.
        
        Returns:
            float: The failure rate as a percentage (0.0 to 100.0).
        """
        total_count = self._get_total_results_count()
        if total_count == 0:
            return 0.0
        
        failure_count = self._get_failure_count()
        return (failure_count / total_count) * 100.0


    def _get_failure_paths(self) -> List[Path | None]:
        """
        Returns a list of file paths for ReaderResult objects that have failed (i.e., have an exception).
        
        Returns:
            List[Path | None]: A list of file paths for failed ReaderResult objects.
        """
        return [result.file_path for _, list_results in self.results.items() for result in list_results if result.exception is not None]
    

    def _get_all_failure_results(self) -> List[ReaderResult]:
        """
        Returns a list of ReaderResult objects that have failed (i.e., have an exception).
        
        Returns:
            List[ReaderResult]: A list of failed ReaderResult objects.
        """
        return [result for _, list_results in self.results.items() for result in list_results if result.exception is not None]


    def _get_success_paths(self) -> List[Path | None]:
        """
        Returns a list of file paths for ReaderResult objects that have succeeded (i.e., do not have an exception).
        
        Returns:
            List[Path | None]: A list of file paths for successful ReaderResult objects.
        """
        return [result.file_path for _, list_results in self.results.items() for result in list_results if result.exception is None]


    def _get_all_successful_results(self) -> List[ReaderResult]:
        """
        Returns a list of all successful ReaderResult objects in the pack.
        
        A ReaderResult is considered successful if it does not have an exception.
        
        Returns:
            List[ReaderResult]: A list of all successful ReaderResult objects in the pack.
        """
        return [result for _, list_results in self.results.items() for result in list_results if result.exception is None]


    def _get_all_results(self) -> List[ReaderResult]:
        """
        Returns a list of all ReaderResult objects in the pack.
        
        Returns:
            List[ReaderResult]: A list of all ReaderResult objects in the pack.
        """
        return [result for _, list_results in self.results.items() for result in list_results]


    def _get_all_paths(self) -> List[Path | None]:
        """
        Returns a list of all file paths for ReaderResult objects in the pack.
        
        Returns:
            List[Path | None]: A list of all file paths for ReaderResult objects.
        """
        return [path for path, _ in self.results.items()]

    
    def _get_all_generator_results(self) -> List[ReaderResultGenerator]:
        """
        Retrieves all ReaderResultGenerator objects from the results list.
        
        Returns:
            list[ReaderResultGenerator]: A list of ReaderResultGenerator objects in the results list.
        """
        return [result for result in self.results if isinstance(result, ReaderResultGenerator)]
    

    def _get_all_str_results(self) -> List[ReaderResultStr]:
        """
        Retrieves all ReaderResultStr objects from the results list.
        
        Returns:
            list[ReaderResultStr]: A list of ReaderResultStr objects in the results list.
        """
        return [result for result in self.results if isinstance(result, ReaderResultStr)]


    # --------------
    # Magic Methods

    def __str__(self) -> str:
        """
        Returns a string representation of the ReaderResultPack object.
        
        Returns:
            str: A string containing the number of ReaderResult objects in the pack.
        """
        try:
            string: str = ""
            string += "ReaderResultPack Object:\n"
            string += f"Number of results: {len(self.results)}\n"
            string += f"Success Count: {self.success_count}\n"
            string += f"Success Rate: {self.success_rate:.3f}%\n"
            string += f"Failure Count: {self.failure_count}\n"
            string += f"Failure Rate: {self.failure_rate:.3f}%\n"
            return string
        except Exception as e:
            raise MagicMethodError(f"Error in __str__ method: {e}") from e


    def __len__(self) -> int:
        """
        Returns the numbers of paths in the results list.
        """
        try:
            return self.total_path_count
        except Exception as e:
            raise MagicMethodError(f"Error in __len__ method: {e}") from e


    def __eq__(self, other: object) -> bool:
        """
        Checks if two ReaderResultPack objects are equal based on their results.
        
        Args:
            other (object): The object to compare with.
        
        Returns:
            bool: True if the objects are equal, False otherwise.
        """
        try:
            if not isinstance(other, ReaderResultPack):
                return False
            
            return  self.results == other.results and \
                    self.total_path_count == other.total_path_count and \
                    self.total_results_count == other.total_results_count and \
                    self.success_count == other.success_count and \
                    self.failure_count == other.failure_count and \
                    self.success_rate == other.success_rate and \
                    self.failure_rate == other.failure_rate
        except Exception as e:
            raise MagicMethodError(f"Error in __eq__ method: {e}") from e


    def __ne__(self, other: object) -> bool:
        """
        Checks if two ReaderResultPack objects are not equal.
        
        Args:
            other (object): The object to compare with.
        
        Returns:
            bool: True if the objects are not equal, False otherwise.
        """
        try:
            return not self.__eq__(other)
        except Exception as e:
            raise MagicMethodError(f"Error in __ne__ method: {e}") from e


    def __hash__(self) -> int:
        """
        Returns a hash of the ReaderResultPack object based on its results.
        
        Returns:
            int: A hash value for the ReaderResultPack object.
        """
        try:
            return hash(tuple(sorted(self.results.items())))
        except Exception as e:
            raise MagicMethodError(f"Error in __hash__ method: {e}") from e


    def __contains__(self, item: Path) -> bool:
        """
        Checks if a Path object is in the results list.
        
        Args:
            item (Path): The file path to check for in the results list.
        
        Returns:
            bool: True if the item is in the results list, False otherwise.
        """
        try:
            if not isinstance(item, Path):
                raise TypeError(f"Item must be a Path object, got {type(item)}")
            
            return item in self.results
        except Exception as e:
            raise MagicMethodError(f"Error in __contains__ method: {e}") from e


    def __iter__(self) -> Generator[ReaderResult, None, None]:
        """
        Returns an iterator for the results list.
        
        This allows iteration over the results.
        
        Returns:
            Iterator[ReaderResult]: An iterator for the results list.
        """
        try:
            with self.lock:
                results = [(path, list_res) for path, list_res in self.results.items()]
            for path, list_res in results:
                for res in list_res:
                    yield res
        except Exception as e:
            raise MagicMethodError(f"Error in __iter__ method: {e}") from e


    def __next__(self):
        """
        Returns the next ReaderResult object from the results list.
        
        This method is used to iterate over the ReaderResult objects in the pack.
        
        Returns:
            ReaderResult: The next ReaderResult object in the results list.
        
        Raises:
            StopIteration: If there are no more ReaderResult objects to return.
        """
        try:
            return next(self.__iter__())
        except Exception as e:
            raise MagicMethodError(f"Error in __next__ method: {e}") from e


    def __add__(self, other: 'ReaderResultPack') -> 'ReaderResultPack':
        """
        Adds another ReaderResultPack to the current one.
        
        Arguments:
            other (ReaderResultPack): The ReaderResultPack to be added.
        
        Returns:
            ReaderResultPack: A new ReaderResultPack containing the combined results of both packs.
        """
        try:
            if not isinstance(other, ReaderResultPack):
                raise TypeError(f"Other must be a ReaderResultPack object, got {type(other)}")
            
            with self.lock:
                new_pack = ReaderResultPack()
                new_pack.results = {**self.results, **other.results}
            return new_pack
        except Exception as e:
            raise MagicMethodError(f"Error in __add__ method: {e}") from e


    def __iadd__(self, other: 'ReaderResultPack') -> None:
        """
        In-place addition of another ReaderResultPack to the current one.
        This method modifies the current ReaderResultPack by adding the results from another ReaderResultPack.
        
        Arguments:
            other (ReaderResultPack): The ReaderResultPack to be added.
        """
        try:
            if not isinstance(other, ReaderResultPack):
                raise TypeError(f"Other must be a ReaderResultPack object, got {type(other)}")
            
            with self.lock:
                for path, list_res in other.results.items():
                    if path in self.results:
                        self.results[path].extend(list_res)
                    else:
                        self.results[path] = list_res
                
                # Update statistics
                self._update_cache()
        except Exception as e:
            raise MagicMethodError(f"Error in __iadd__ method: {e}") from e


    def __sub__(self, other: 'ReaderResultPack') -> 'ReaderResultPack':
        """
        Subtracts another ReaderResultPack from the current one.
        
        Arguments:
            other (ReaderResultPack): The ReaderResultPack to be subtracted.
        
        Returns:
            ReaderResultPack: A new ReaderResultPack containing the results of the current pack minus the other pack.
        """
        try:
            if not isinstance(other, ReaderResultPack):
                raise TypeError(f"Other must be a ReaderResultPack object, got {type(other)}")
            
            with self.lock:
                new_pack = ReaderResultPack()
                for path, list_res in self.results.items():
                    if path not in other.results:
                        new_pack.add_results(list_res)
                    else:
                        new_pack.add_results([res for res in list_res if res not in other.results[path]])
            
            return new_pack
        except Exception as e:
            raise MagicMethodError(f"Error in __sub__ method: {e}") from e


    def __isub__(self, other: 'ReaderResultPack') -> None:
        """
        In-place subtraction of another ReaderResultPack from the current one.
        
        This method modifies the current ReaderResultPack by removing results that are present in another ReaderResultPack.
        
        Arguments:
            other (ReaderResultPack): The ReaderResultPack to be subtracted.
        """
        try:
            if not isinstance(other, ReaderResultPack):
                raise TypeError(f"Other must be a ReaderResultPack object, got {type(other)}")
            
            with self.lock:
                for path, list_res in other.results.items():
                    if path in self.results:
                        for res in list_res:
                            if res in self.results[path]:
                                self.results[path].remove(res)
                
                # Update statistics
                self._update_cache()
        except Exception as e:
            raise MagicMethodError(f"Error in __isub__ method: {e}") from e


    def __del__(self):
        """
        Destructor for the ReaderResultPack class.
        
        This method is called when the ReaderResultPack object is about to be destroyed.
        It clears the results and cached dictionary to free up memory.
        """
        try:
            with self.lock:
                self.results.clear()
                self.cached_dict.clear()
        except Exception as e:
            raise MagicMethodError(f"Error in __del__ method: {e}") from e

    # --------------
    # Methods

    def add_result(self, result: ReaderResult) -> None:
        """
        Adds a ReaderResult object to the results list.
        
        Args:
            result (ReaderResult): The ReaderResult object to be added.
        
        Raises:
            TypeError: If the result is not a ReaderResult object.
        """
        try:
            if not isinstance(result, ReaderResult):
                raise TypeError(f"Result must be a ReaderResult object, got {type(result)}")
            
            with self.lock:
                path: Path = result.file_path if result.file_path else Path("unknown_path")
                
                if result.file_path in self.results:
                    self.results[path].append(result)
                else:
                    self.results[path] = [result]
            
                # Update Statistics
                self._update_cache()
        except Exception as e:
            raise AddError(f"Error adding result: {e}") from e
            

    def add_results(self, results: list[ReaderResult]) -> None:
        """
        Adds multiple ReaderResult objects to the results list.
        
        Args:
            results (list[ReaderResult]): A list of ReaderResult objects to be added.
        
        Raises:
            TypeError: If any item in the results list is not a ReaderResult object.
        """
        try:
            if not isinstance(results, list):
                raise TypeError(f"Results must be a list, got {type(results)}")
            
            for result in results:
                if not isinstance(result, ReaderResult):
                    raise TypeError(f"Each result must be a ReaderResult object, got {type(result)}")
            
            with self.lock:
                for result in results:
                    path: Path = result.file_path if result.file_path else Path("unknown_path")
                    
                    if result.file_path in self.results:
                        self.results[path].append(result)
                    else:
                        self.results[path] = [result]
            
                # Update Statistics
                self._update_cache()
        except Exception as e:
            raise AddError(f"Error adding results: {e}") from e


    def remove_result(self, path: Path) -> None:
        """
        Removes a ReaderResult object from the results list based on its file path.
        
        Args:
            path (Path): The file path of the ReaderResult object to be removed.
        
        Raises:
            ValueError: If no ReaderResult object with the specified file path is found.
        """
        try:
            if not isinstance(path, Path):
                raise TypeError(f"Path must be a Path object, got {type(path)}")

            with self.lock:
                if path in self.results:
                    del self.results[path]
                    # Update Statistics
                    self._update_cache()
                else:
                    raise ValueError(f"No ReaderResult found with file path: {path}")
        except Exception as e:
            raise RemoveError(f"Error removing result for path {path}: {e}") from e
            

    def remove_results(self, paths: list[Path]) -> None:
        """
        Removes multiple ReaderResult objects from the results list based on their file paths.
        
        Args:
            paths (list[Path]): A list of file paths of the ReaderResult objects to be removed.
        
        Raises:
            TypeError: If any item in the paths list is not a Path object.
            ValueError: If no ReaderResult object with the specified file path is found.
        """
        try:
            if not isinstance(paths, list):
                raise TypeError(f"Paths must be a list, got {type(paths)}")
            
            for path in paths:
                if not isinstance(path, Path):
                    raise TypeError(f"Each path must be a Path object, got {type(path)}")
            
            with self.lock:
                for path in paths:
                    if path in self.results:
                        del self.results[path]
                    else:
                        raise ValueError(f"No ReaderResult found with file path: {path}")
                # Update Statistics
                self._update_cache()
        except Exception as e:
            raise RemoveError(f"Error removing results for paths {paths}: {e}") from e

    
    def clear_results(self) -> None:
        """
        Clears all ReaderResult objects from the results list.
        
        This method removes all ReaderResult objects from the results list, effectively resetting it.
        """
        try:
            with self.lock:
                self.results.clear()
                # Update Statistics
                self._update_cache()
        except Exception as e:
            raise ClearError(f"Error clearing results: {e}") from e


    # Getters

    def get_result(self, path: Path) -> Dict[Path, List[ReaderResult]]:
        """
        Retrieves a ReaderResult object from the results list based on its file path.
        
        Arguments:
            path (Path): The file path of the ReaderResult object to be retrieved.
        
        Returns:
            Dict[Path, List[ReaderResult]]: A dictionary containing the file path and the corresponding ReaderResult objects.
        """
        try:
            if not isinstance(path, Path):
                raise TypeError(f"Path must be a Path object, got {type(path)}")
            
            out: Dict[Path, List[ReaderResult]] = {}
            if path in self.results:
                out[path] = self.results[path]
            else:
                raise ValueError(f"No ReaderResult found with file path: {path}")
            return out
        except Exception as e:
            raise GetterError(f"Error retrieving result for path {path}: {e}") from e
    

    def get_results(self, paths: List[Path]) -> Dict[Path, List[ReaderResult]]:
        """
        Retrieves multiple ReaderResult objects from the results list based on their file paths.
        
        Args:
            paths (List[Path]): A list of file paths of the ReaderResult objects to be retrieved.
        
        Returns:
            Dict[Path, List[ReaderResult]]: A dictionary containing the file paths and the corresponding ReaderResult objects.
        """
        try:
            if not isinstance(paths, list):
                raise TypeError(f"Paths must be a list, got {type(paths)}")
            
            for path in paths:
                if not isinstance(path, Path):
                    raise TypeError(f"Each path must be a Path object, got {type(path)}")
            
            out: Dict[Path, List[ReaderResult]] = {}

            for path in paths:
                if path in self.results:
                    out[path] = self.results[path]
                else:
                    raise ValueError(f"No ReaderResult found with file path: {path}")
            return out
        except Exception as e:
            raise GetterError(f"Error retrieving results for paths {paths}: {e}") from e
    

    def get_report_from_path(self, path: Path) -> str:
        """
        Retrieves a report of ReaderResult objects from the results list based on their file path.
        
        Arguments:
            path (Path): The file path of the ReaderResult object to be retrieved.
        
        Returns:
            str: A string containing the report of the ReaderResult objects for the specified file path.
        """
        try:
            if not isinstance(path, Path):
                raise TypeError(f"Path must be a Path object, got {type(path)}")
            
            if path not in self.results:
                raise ValueError(f"No ReaderResult found with file path: {path}")
            
            report = f"Results for {path}:\n"
            for result in self.results[path]:
                report += "\t" + result.__str__() + "\n"
            return report
        except Exception as e:
            raise GetterError(f"Error retrieving report for path {path}: {e}") from e


    # Utils

    def print_summary(self) -> None:
        """
        Prints a summary of the ReaderResultPack.
        
        This method prints the total path count, total results count, success count, failure count,
        success rate, and failure rate to the console.
        """
        print(self.get_summary)

    
    def print_full_report(self) -> None:
        """
        Prints a full report of the ReaderResultPack.
        
        This method prints detailed information about each ReaderResult object, including content,
        file path, and exception (if any) to the console.
        """
        print(self.get_full_report)


    def print_report_from_path(self, path: Path) -> None:
        """
        Prints a report of ReaderResult objects from the results list based on their file path.
        
        Arguments:
            path (Path): The file path of the ReaderResult object to be retrieved.
        
        Raises:
            TypeError: If the path is not a Path object.
            ValueError: If no ReaderResult object with the specified file path is found.
        """
        if not isinstance(path, Path):
            raise TypeError(f"Path must be a Path object, got {type(path)}")
        
        print(self.get_report_from_path(path))

    # --------------
    # Unpacker

    def in_unpack(self, line_separator: str = '\n') -> None:
        """
        Inplace unpacks the ReaderResultPack object by converting all ReaderResultGenerator objects
        in the results list to ReaderResultStr objects.

        This method iterates through the results list and replaces any ReaderResultGenerator
        objects with ReaderResultStr objects, which contain the content as a string instead of a generator.

        Arguments:
            line_separator (str): The string to use as a separator for joining the content of ReaderResultGenerator objects.
        """
        try:
            if not isinstance(line_separator, str):
                raise TypeError(f"line_separator must be a string, got {type(line_separator)}")
            if len(line_separator) == 0:
                raise ValueError("line_separator cannot be an empty string")
            
            with self.lock:
                for path, list_results in self.results.items():
                    for i, result in enumerate(list_results):
                        if isinstance(result, ReaderResultGenerator):
                            content: str = line_separator.join(result.content_generator)
                            list_results[i] = ReaderResultStr(
                                content=content,
                                file_path=result.file_path,
                                exception=result.exception
                            )
                        elif not isinstance(result, ReaderResultStr):
                            raise TypeError(f"Invalid type in results list: {type(result)})")
        except Exception as e:
            raise UnpackError(f"Error unpacking ReaderResultPack: {e}") from e
                    
    
    def unpack(self, line_separator: str = '\n') -> 'ReaderResultPack':
        """
        Unpacks the ReaderResultPack object by converting all ReaderResultGenerator objects
        in the results list to ReaderResultStr objects.

        This method creates a new ReaderResultPack object with the unpacked results, where each
        ReaderResultGenerator is replaced with a ReaderResultStr containing the content as a string.

        Arguments:
            line_separator (str): The string to use as a separator for joining the content of Reader
        
        Returns:
            out (ReaderResultPack) : A new ReaderResultPack object with unpacked results.
        """
        try:
            unpacked_pack = ReaderResultPack()
            for path, list_results in self.results.items():
                for result in list_results:
                    if isinstance(result, ReaderResultGenerator):
                        content = line_separator.join(result.content_generator)
                        unpacked_pack.add_result(ReaderResultStr(content=content, file_path=result.file_path, exception=result.exception))
                    elif isinstance(result, ReaderResult):
                        unpacked_pack.add_result(result)
                    else:
                        raise TypeError(f"Invalid type in results list: {type(result)}")
            return unpacked_pack
        except Exception as e:
            raise UnpackError(f"Error unpacking ReaderResultPack: {e}") from e
