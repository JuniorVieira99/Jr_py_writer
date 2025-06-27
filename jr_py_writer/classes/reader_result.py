# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
from abc import ABC, abstractmethod

import json
import traceback as tb

from dataclasses import dataclass, field
from typing import Any, Generator, Optional, Union, Dict
from pathlib import Path
from itertools import chain

# Third-party imports
import yaml

# ----------------------------------------------------------------------------------------------
# Exceptions
# ----------------------------------------------------------------------------------------------

class ReaderResultError(Exception):
    """
    Custom exception for errors related to ReaderResult operations.
    This exception is raised when there are issues with the content, file path, or exception
    attributes of the ReaderResult class.
    """
    
    pass


class ConstructionError(ReaderResultError):
    """
    Exception raised when there is an error during the construction of a ReaderResult object.
    This can occur if the content is not a string or bytes, the file path is not a Path object,
    or the exception is not an Exception object.
    """
    
    pass


class SetterError(ReaderResultError):
    """
    Exception raised when there is an error setting attributes of a ReaderResult object.
    This can occur if the content, file path, or exception attributes are not in the expected format.
    """
    
    pass


class MagicMethodError(ReaderResultError):
    """
    Exception raised when there is an error in the magic methods of a ReaderResult object.
    This can occur if the content, file path, or exception attributes are not in the expected format
    or if the comparison operations fail.
    """
    
    pass


class AddContentError(ReaderResultError):
    """
    Exception raised when there is an error adding content to a ReaderResult object.
    This can occur if the content is not a string or bytes, or if the content cannot be added
    to the existing content of the ReaderResult object.
    """
    
    pass


class ToDictError(ReaderResultError):
    """
    Exception raised when there is an error converting a ReaderResult object to a dictionary.
    This can occur if the content, file path, or exception attributes are not in the expected format.
    """
    
    pass


class ToJsonError(ReaderResultError):
    """
    Exception raised when there is an error converting a ReaderResult object to JSON.
    This can occur if the content, file path, or exception attributes cannot be serialized to JSON.
    """
    
    pass


class ToYamlError(ReaderResultError):
    """
    Exception raised when there is an error converting a ReaderResult object to YAML.
    This can occur if the content, file path, or exception attributes cannot be serialized to YAML.
    """
    
    pass


# ----------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------

def _validator(
    file_path: Optional[Path] = None,
    exception: Optional[Exception] = None
) -> bool:
    """
    Validates the file_path and exception attributes of a ReaderResult object.
    
    Args:
        file_path (Optional[Path]): The file path to validate. Defaults to None.
        exception (Optional[Exception]): The exception to validate. Defaults to None.
    
    Returns:
        bool: True if both file_path and exception are valid, False otherwise.
    
    Raises:
        TypeError: If file_path is not a Path object or exception is not an Exception object.
    """
    if file_path is not None and not isinstance(file_path, Path):
        raise TypeError(f"File path must be a Path object, got {type(file_path)}")
    
    if exception is not None and not isinstance(exception, Exception):
        raise TypeError(f"Exception must be an Exception object, got {type(exception)}")
    
    return True


@dataclass
class ReaderResult(ABC):
    """
    ReaderResult Class
    ==================
    The ReaderResult class is designed to encapsulate the result of reading a file or other content source.
    It provides attributes to store the content, the file path, and any exception that occurred during the
    reading process. The class includes methods for converting its data to various formats, such as dictionaries,
    JSON, and YAML, as well as magic methods for comparison, hashing, and string representation.
    """

    # --------------
    # Attributes

    _file_path: Optional[Path] = field(default=None, init=False)
    _exception: Optional[Exception] = field(default=None, init=False)

    # --------------
    # Properties

    @property
    def file_path(self) -> Optional[Path]:
        """
        Returns the file path of the ReaderResult object.
        
        Returns:
            Optional[Path]: The file path if it is set, otherwise None.
        """
        return self._file_path
    

    @property
    def exception(self) -> Optional[Exception]:
        """
        Returns the exception of the ReaderResult object.
        
        Returns:
            Optional[Exception]: The exception if it is set, otherwise None.
        """
        return self._exception
    

    # --------------
    # Setters

    @file_path.setter
    def file_path(self, file_path: Optional[Path]) -> None:
        """
        Sets the file path for the ReaderResult object.
        
        Args:
            file_path (Optional[Path]): The file path to be set. Must be a Path object or None.
        
        Raises:
            TypeError: If the file_path is not a Path object or None.
        """
        try:
            if file_path is not None and not isinstance(file_path, Path):
                raise TypeError(f"File path must be a Path object or None, got {type(file_path)}")
            
            if len(str(file_path)) == 0:
                raise ValueError("File path cannot be empty")
            
            if len(str(file_path)) > 255:
                raise ValueError("File path cannot exceed 255 characters")
            
            self._file_path = file_path
        except Exception as e:
            raise SetterError(f"Error setting 'file_path': {e}") from e


    @exception.setter
    def exception(self, exception: Optional[Exception]) -> None:
        """
        Sets the exception for the ReaderResult object.
        
        Args:
            exception (Optional[Exception]): The exception to be set. Must be an Exception object or None.
        
        Raises:
            TypeError: If the exception is not an Exception object or None.
        """
        try:
            if exception is not None and not isinstance(exception, Exception):
                raise TypeError(f"Exception must be an Exception object or None, got {type(exception)}")
            
            self._exception = exception
        except Exception as e:
            raise SetterError(f"Error setting 'exception': {e}") from e

    # --------------
    # Abstract Methods


    @abstractmethod
    def to_dict(self) -> Dict: ...


    # --------------
    # Methods

    def to_json(self) -> str:
        """
        Converts the ReaderResult object to a JSON string representation.
        
        Returns:
            str: A JSON string containing the content, file_path, and exception attributes of
            the ReaderResult object.
        """
        try:
            return json.dumps(self.to_dict(), ensure_ascii=False)
        except Exception as e:
            raise ToJsonError(f"Error converting ReaderResult to JSON: {e}") from e
    

    def to_yaml(self) -> str:
        """
        Converts the ReaderResult object to a YAML string representation.
        
        Returns:
            str: A YAML string containing the content, file_path, and exception attributes of
            the ReaderResult object.
        """
        try:
            return yaml.dump(self.to_dict(), allow_unicode=True, default_flow_style=False)
        except Exception as e:
            raise ToYamlError(f"Error converting ReaderResult to YAML: {e}") from e
            

    def print(self) -> None:
        """
        Prints the string representation of the ReaderResult object to the console.
        
        This method is a convenience method for printing the ReaderResult object directly.
        """
        print(self.__str__())


@dataclass
class ReaderResultStr(ReaderResult):
    """
    ReaderResult Class
    ================
    The ReaderResult class is designed to encapsulate the result of reading a file or other content source.
    It provides attributes to store the content, the file path, and any exception that occurred during the
    reading process. The class includes methods for converting its data to various formats, such as dictionaries,
    JSON, and YAML, as well as magic methods for comparison, hashing, and string representation.

    Attributes:
        content (str): The content read from the file or source. Must be a string or bytes.
        file_path (Optional[Path]): The path to the file from which the content was read. Defaults to None.
        exception (Optional[Exception]): Any exception that occurred during the reading process. Defaults to None.

    Methods:
    -----------
        Magic Methods:
            __str__(): Returns a string representation of the ReaderResult object.
            __len__(): Returns the length of the content.
            __lt__(other): Checks if the content of this ReaderResult object is less than that of another ReaderResult object.
            __gt__(other): Checks if the content of this ReaderResult object is greater than that of another ReaderResult object.
            __le__(other): Checks if the content of this ReaderResult object is less than or equal to that of another ReaderResult object.
            __add__(other): Adds the content of another ReaderResultStr object to this one.
            __iadd__(other): In-place addition of the content of another ReaderResultStr object to this one.
            __sub__(other): Subtracts the content of another ReaderResultStr object from this one.
            __isub__(other): In-place subtraction of the content of another ReaderResultStr object from this one.
            __eq__(other): Checks if two ReaderResult objects are equal based on their attributes.
            __ne__(other): Checks if two ReaderResult objects are not equal.
            __hash__(): Returns a hash of the ReaderResult object based on its attributes.

        To Methods:
            #### to_dict():
                Converts the ReaderResult object to a dictionary representation.
            #### to_json():
                Converts the ReaderResult object to a JSON string representation.
            #### to_yaml():
                Converts the ReaderResult object to a YAML string representation.
            #### print():
                Prints the string representation of the ReaderResult object to the console.
        Setters:
            #### set_content(content: Union[str, bytes]):
                Sets the content for the ReaderResult object.
            #### set_file_path(file_path: Path):
                Sets the file path for the ReaderResult object.
            #### set_exception(exception: Exception):
                Sets the exception for the ReaderResult object.
        Add:
            #### add_content(content: str):
                Adds content to the ReaderResult object.

    Example:

    ```python

    my_result = ReaderResult(
        content="This is the content of the file.",
        file_path=Path("/path/to/file.txt"),
        exception=None
    )
    print(my_result)  # Outputs the string representation of the ReaderResult object
    print(my_result.to_dict())  # Outputs a dictionary representation of the ReaderResult object
    print(my_result.to_json())  # Outputs a JSON string representation of the ReaderResult object
    print(my_result.to_yaml())  # Outputs a YAML string representation of the ReaderResult object
    my_result.print()  # Prints the string representation of the ReaderResult object to the console
    ```
    """

    # --------------
    # Attributes

    _content: str = field(default="", init=True, repr=True)

    # --------------
    # Properties

    @property
    def content(self) -> str:
        """
        Returns the content of the ReaderResult object.
        
        Returns:
            str: The content of the ReaderResult object.
        """
        return self._content


    # --------------
    # Setters

    @content.setter
    def content(self, content: Union[str, bytes]) -> None:
        """
        Sets the content for the ReaderResult object.
        
        Args:
            content (Union[str, bytes]): The content to be set. Must be a string or bytes.
        
        Raises:
            TypeError: If the content is not a string or bytes.
        """
        try:
            if not isinstance(content, (str, bytes)):
                raise TypeError(f"Content must be a string or bytes, got {type(content)}")
            
            if isinstance(content, bytes):
                try:
                    content = content.decode('utf-8')
                except UnicodeDecodeError:
                    # If decoding fails, we can still set the content
                    content = content.decode('utf-8', errors='ignore')
            self._content = content
        except Exception as e:
            raise SetterError(f"Error setting 'content': {e}") from e

    # --------------
    # Constructors

    def __init__(self, content: Union[str, bytes] = "", file_path: Optional[Path] = None, exception: Optional[Exception] = None):
        """
        Initializes a ReaderResult object with the given content, file path, and exception.
        
        Arguments:
            content (Union[str, bytes]): The content read from the file or source. Must be a string or bytes.
            file_path (Optional[Path]): The path to the file from which the content was read. Defaults to None.
            exception (Optional[Exception]): Any exception that occurred during the reading process. Defaults to None.
        
        Raises:
            ConstructionError: If the content is not a string or bytes, the file_path is not a Path object,
                               or the exception is not an Exception object.
        """
        try:
            self.content = content
            self.file_path = file_path
            self.exception = exception
            self.__post_init__()
        except Exception as e:
            raise ConstructionError(f"Error during ReaderResult initialization: {e}") from e


    def __post_init__(self):
        """
        Post-Init
        ==========
        This method is called after the initialization of the ReaderResult object to perform additional
        validation and type checking on the attributes.

        Raises:
            ConstructionError: If the content is not a string or bytes, the file_path is not a Path object,
                               or the exception is not an Exception object.
        """
        try:

            if not isinstance(self.content, (str, bytes)):
                raise TypeError(f"Content must be a string or bytes, got {type(self.content)}")

            if isinstance(self.content, bytes):
                self.content = self.content.decode('utf-8')
            
            _validator(
                file_path=self.file_path,
                exception=self.exception
            )  
        except Exception as e:
            raise ConstructionError(f"Error during ReaderResult initialization: {e}") from e
        
    # --------------
    # Magic Methods

    def __str__(self) -> str:
        """
        Returns a string representation of the ReaderResult object.
        
        Returns:
            str: A string containing the content, file_path, and exception attributes of the
            ReaderResult object.
        """
        traceback = self.exception.__traceback__ if self.exception else None
        traceback_str = ''.join(tb.format_tb(traceback)) if traceback else None
        string: str = ""
        string += "ReaderResult Object:\n"

        if self.content:
            string += f"Content: {self.content}\n"
            string += f"Content Length: {len(self.content)}\n"
        else:
            string += "Content: None\n"

        if self.file_path:
            string += f"File Path: {self.file_path}\n"

        if self.exception:
            string += f"Exception: {type(self.exception).__name__}\n"
            string += f"Exception Message: {str(self.exception)}\n"
            string += f"Traceback: {traceback_str}\n"

        return string
    

    def __len__(self) -> int:
        """
        Returns the length of the content attribute.
        
        Returns:
            int: The length of the content string.
        """
        return len(self.content) if self.content else 0
    

    def __lt__(self, other: object) -> bool:
        """
        Checks if the content of this ReaderResult object is less than that of another ReaderResult object.
        
        Arguments:
            other (object): The object to compare with.
        
        Returns:
            bool: True if this object's content is less than the other's, False otherwise.
        """
        try:
            if not isinstance(other, ReaderResultStr):
                return False
            
            return len(self.content) < len(other.content)
        except Exception as e:
            raise MagicMethodError(f"Error in __lt__ comparison: {e}") from e


    def __gt__(self, other: object) -> bool:
        """
        Checks if the content of this ReaderResult object is greater than that of another ReaderResult object.
        
        Arguments:
            other (object): The object to compare with.
        
        Returns:
            bool: True if this object's content is greater than the other's, False otherwise.
        """
        try:
            if not isinstance(other, ReaderResultStr):
                return False
            
            return len(self.content) > len(other.content)
        except Exception as e:
            raise MagicMethodError(f"Error in __gt__ comparison: {e}") from e


    def __le__(self, other: object) -> bool:
        """
        Checks if the content of this ReaderResult object is less than or equal to that of another ReaderResult object.
        
        Arguments:
            other (object): The object to compare with.
        
        Returns:
            bool: True if this object's content is less than or equal to the other's, False otherwise.
        """
        try:
            if not isinstance(other, ReaderResultStr):
                return False
            
            return len(self.content) <= len(other.content)
        except Exception as e:
            raise MagicMethodError(f"Error in __le__ comparison: {e}") from e


    def __ge__(self, other: object) -> bool:
        """
        Checks if the content of this ReaderResult object is greater than or equal to that of another ReaderResult object.
        
        Arguments:
            other (object): The object to compare with.
        
        Returns:
            bool: True if this object's content is greater than or equal to the other's, False otherwise.
        """
        try:
            if not isinstance(other, ReaderResultStr):
                return False
            
            return len(self.content) >= len(other.content)
        except Exception as e:
            raise MagicMethodError(f"Error in __ge__ comparison: {e}") from e


    def __eq__(self, other: object) -> bool:
        """
        Checks if two ReaderResult objects are equal based on their content, file_path, and exception.
        
        Arguments:
            other (object): The object to compare with.
        
        Returns:
            bool: True if the objects are equal, False otherwise.
        """
        try:
            if not isinstance(other, ReaderResultStr):
                return False
            
            return (self.content == other.content and
                    self.file_path == other.file_path and
                    self.exception == other.exception)
        except Exception as e:
            raise MagicMethodError(f"Error in __eq__ comparison: {e}") from e
        

    def __ne__(self, other: object) -> bool:
        """
        Checks if two ReaderResult objects are not equal.
        
        Arguments:
            other (object): The object to compare with.
        
        Returns:
            bool: True if the objects are not equal, False otherwise.
        """
        try:
            return not self.__eq__(other)
        except Exception as e:
            raise MagicMethodError(f"Error in __ne__ comparison: {e}") from e


    def __hash__(self) -> int:
        """
        Returns a hash of the ReaderResult object based on its content, file_path, and exception.
        
        Returns:
            int: A hash value for the ReaderResult object.
        """
        return hash((self.content, self.file_path, self.exception))


    def __add__(self, other: object) -> 'ReaderResultStr':
        """
        Adds the content of another ReaderResultStr object to this one.
        
        Arguments:
            other (object): The ReaderResultStr object to add.
        
        Returns:
            ReaderResultStr: A new ReaderResultStr object with combined content.
        
        Raises:
            TypeError: If the other object is not a ReaderResultStr.
        """
        try:
            if not isinstance(other, ReaderResultStr):
                raise TypeError(f"Cannot add ReaderResultStr with {type(other)}")
            
            new_content = self.content + other.content
            return ReaderResultStr(content=new_content, file_path=self.file_path, exception=self.exception)
        except Exception as e:
            raise MagicMethodError(f"Error in __add__ operation: {e}") from e


    def __iadd__(self, other: object) -> 'ReaderResultStr':
        """
        In-place addition of the content of another ReaderResultStr object to this one.
        
        Arguments:
            other (object): The ReaderResultStr object to add.
        
        Returns:
            ReaderResultStr: The current ReaderResultStr object with updated content.
        
        Raises:
            TypeError: If the other object is not a ReaderResultStr.
        """
        try:
            if not isinstance(other, ReaderResultStr):
                raise TypeError(f"Cannot add ReaderResultStr with {type(other)}")
            
            self.content += other.content
            return self
        except Exception as e:
            raise MagicMethodError(f"Error in __iadd__ operation: {e}") from e


    def __sub__(self, other: object) -> 'ReaderResultStr':
        """
        Subtracts the content of another ReaderResultStr object from this one.
        
        Arguments:
            other (object): The ReaderResultStr object to subtract.
        
        Returns:
            ReaderResultStr: A new ReaderResultStr object with the content of this object minus the other.
        
        Raises:
            TypeError: If the other object is not a ReaderResultStr.
        """
        try:
            if not isinstance(other, ReaderResultStr):
                raise TypeError(f"Cannot subtract ReaderResultStr with {type(other)}")
            
            new_content = self.content.replace(other.content, "")
            return ReaderResultStr(content=new_content, file_path=self.file_path, exception=self.exception)
        except Exception as e:
            raise MagicMethodError(f"Error in __sub__ operation: {e}") from e


    def __isub__(self, other: object) -> 'ReaderResultStr':
        """
        In-place subtraction of the content of another ReaderResultStr object from this one.
        
        Arguments:
            other (object): The ReaderResultStr object to subtract.
        
        Returns:
            ReaderResultStr: The current ReaderResultStr object with updated content.
        
        Raises:
            TypeError: If the other object is not a ReaderResultStr.
        """
        try:
            if not isinstance(other, ReaderResultStr):
                raise TypeError(f"Cannot subtract ReaderResultStr with {type(other)}")
            
            self.content = self.content.replace(other.content, "")
            return self
        except Exception as e:
            raise MagicMethodError(f"Error in __isub__ operation: {e}") from e

  
    # --------------
    # Methods

    def add_content(self, content: str) -> None:
        """
        Adds content to the ReaderResult object.
        
        Args:
            content (str): The content to be added. Must be a string.
        
        Raises:
            TypeError: If the content is not a string.
        """
        try:
            if not isinstance(content, str):
                raise TypeError(f"Content must be a string, got {type(content)}")
            
            if not self.content:
                self.content = content
            else:
                self.content += content
        except Exception as e:
            raise AddContentError(f"Error adding content to ReaderResultStr: {e}") from e


    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the ReaderResult object to a dictionary representation.
        
        Returns:
            Dict[str, Any]: A dictionary containing the content, file_path,
            and exception attributes of the ReaderResult object.
        """
        try:
            traceback = self.exception.__traceback__ if self.exception else None
            traceback_str = ''.join(tb.format_tb(traceback)) if traceback else None

            return {
                'content': self.content,
                'file_path': str(self.file_path) if self.file_path else None,
                'exception': {
                    'type': type(self.exception).__name__,
                    'message': str(self.exception),
                    'traceback': traceback_str 
                } if self.exception else None
            }
        except Exception as e:
            raise ToDictError(f"Error converting ReaderResult to dict: {e}") from e
        

@dataclass
class ReaderResultGenerator(ReaderResult):
    """
    ReaderResultGenerator Class
    ===========================
    A subclass of ReaderResult that is designed to handle the generation of ReaderResult objects.
    It inherits all attributes and methods from the ReaderResult class and can be used to create
    ReaderResult objects with additional functionality.

    Attributes:
        content_generator (Generator[str, None, None]): A generator that yields strings as content.
        file_path (Optional[Path]): The path to the file from which the content was read. Defaults to None.
        exception (Optional[Exception]): Any exception that occurred during the reading process. Defaults to None.

    Methods:
    -----------
        To Methods:
            #### to_dict():
                Converts the ReaderResultGenerator object to a dictionary representation with packed content.
            #### to_json():
                Converts the ReaderResultGenerator object to a JSON string representation with packed content.
            #### to_yaml():
                Converts the ReaderResultGenerator object to a YAML string representation with packed content.
            #### to_dict_unpacked():
                Converts the ReaderResultGenerator object to a dictionary representation with unpacked content.
            #### to_json_unpacked():
                Converts the ReaderResultGenerator object to a JSON string representation with unpacked content.
            #### to_yaml_unpacked():
                Converts the ReaderResultGenerator object to a YAML string representation with unpacked content.
        Setters:
            #### set_content(content: Generator[str, None, None]):
                Sets the content for the ReaderResultGenerator object.
            #### set_file_path(file_path: Path):
                Sets the file path for the ReaderResultGenerator object.
            #### set_exception(exception: Exception):
                Sets the exception for the ReaderResultGenerator object.
        Add:
            #### add_content(content: Generator[str, None, None]):
                Adds content to the ReaderResultGenerator object.
        
    Example:
    ```python
    my_generator = (f"Line {i}" for i in range(5))  # A generator that yields strings
    my_result_gen = ReaderResultGenerator(
        content_generator=my_generator,
        file_path=Path("/path/to/file.txt"),
        exception=None
    )

    print(my_result_gen)  # Outputs the string representation of the ReaderResultGenerator object
    print(my_result_gen.to_dict_packed())  # Outputs a dictionary representation with packed content
        
    """
    # --------------
    # Attributes

    _content_generator: Generator[str, None, None] = field(default_factory=lambda: (yield))


    # --------------
    # Properties

    @property
    def content_generator(self) -> Generator[str, None, None]:
        """
        Returns the content generator of the ReaderResultGenerator object.
        
        Returns:
            out (Generator[str, None, None]) : The content generator of the ReaderResultGenerator object.
        """
        return self._content_generator
    

    @content_generator.setter
    def content_generator(self, content: Generator[str, None, None]) -> None:
        """
        Sets the content for the ReaderResultGenerator object.
        
        Arguments:
            content (Generator[str, None, None]): The content to be set. Must be a Generator that yields strings.
        
        Raises:
            TypeError: If the content is not a Generator object.
        """
        try:
            if not isinstance(content, Generator):
                raise TypeError(f"Content must be a Generator object, got {type(content)}")
            
            if not hasattr(self, '_content_generator') or self._content_generator is None:
                self._content_generator = ("" for _ in range(0))  # Default to an empty generator
                        
            self._content_generator = content
        except Exception as e:
            raise SetterError(f"Error setting 'content': {e}") from e
        

    # --------------
    # Constructors

    def __init__(
        self,
        content_generator: Generator[str, None, None],
        file_path: Optional[Path] = None,
        exception: Optional[Exception] = None
    ) -> None:
        """
        Initializes a ReaderResultGenerator object with the given content generator, file path, and exception.
        
        Arguments:
            content_generator (Generator[str, None, None]): A generator that yields strings as content.
            file_path (Optional[Path]): The path to the file from which the content was read. Defaults to None.
            exception (Optional[Exception]): Any exception that occurred during the reading process. Defaults to None.
        """
        try:
            self.content_generator = content_generator if content_generator else ("" for _ in range(0))  # Default to an empty generator
            self.file_path = file_path
            self.exception = exception
            self.__post_init__()
        except Exception as e:
            raise ConstructionError(f"Error during ReaderResultGenerator initialization: {e}") from e

    
    def __post_init__(self):
        """
        Post-Init
        ==========
        This method is called after the initialization of the ReaderResultGenerator object to perform additional
        validation and type checking on the content_generator attribute.
        
        Raises:
            TypeError: If the content_generator is not a Generator object.
        """
        if not isinstance(self.content_generator, Generator):
            raise TypeError(f"Content must be a Generator object, got {type(self.content_generator)}")
        # Validate the file_path and exception attributes
        _validator(
            file_path=self.file_path,
            exception=self.exception
        )


    # --------------
    # Magic Methods
    
    def __str__(self) -> str:
        """
        Returns a string representation of the ReaderResult object.
        
        Returns:
            str: A string containing the content, file_path, and exception attributes of the
            ReaderResult object.
        """
        traceback = self.exception.__traceback__ if self.exception else None
        traceback_str = ''.join(tb.format_tb(traceback)) if traceback else None
        string: str = ""
        string += "ReaderResult Object:\n"
        
        if self.content_generator:
            string += f"Content: {self.content_generator}\n"
        else:
            string += "Content: None\n"

        if self.file_path:
            string += f"File Path: {self.file_path}\n"

        if self.exception:
            string += f"Exception: {type(self.exception).__name__}\n"
            string += f"Exception Message: {str(self.exception)}\n"
            string += f"Traceback: {traceback_str}\n"

        return string
    

    # --------------
    # Methods

    def add_content(self, content: Generator[str, None, None]) -> None:
        """
        Add content to the ReaderResultGenerator object.
        
        Args:
            content (Generator[str, None, None]): The content to be added. Must be a Generator that yields strings.
        
        Raises:
            TypeError: If the content is not a Generator object.
        """
        try:
            if not isinstance(content, Generator):
                raise TypeError(f"Content must be a Generator object, got {type(content)}")
            
            # Consume the existing generator and add new content
            if not self.content_generator:
                self.content_generator = content
            else:
                try:
                    next(self.content_generator, None)  # Check if exhausted
                    new_content = chain(self.content_generator, content)
                    self.content_generator = (item for item in new_content)
                except StopIteration:
                    self.content_generator = content
        except Exception as e:
            raise AddContentError(f"Error adding content to ReaderResultGenerator: {e}") from e


    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the ReaderResultGenerator object to a dictionary representation with packed content.
        
        Returns:
            Dict[str, Any]: A dictionary containing the content as a generator, file_path, and exception attributes
            of the ReaderResultGenerator object.
        """
        try:
            traceback = self.exception.__traceback__ if self.exception else None
            traceback_str = ''.join(tb.format_tb(traceback)) if traceback else None

            return {
                'content': self.content_generator,
                'file_path': str(self.file_path) if self.file_path else None,
                'exception': {
                    'type': type(self.exception).__name__,
                    'message': str(self.exception),
                    'traceback': traceback_str
                } if self.exception else None
            }
        
        except Exception as e:
            raise ToDictError(f"Error converting ReaderResult to dict: {e}") from e


    def to_dict_unpacked(self, chunk: Optional[int] = None, separator: str = "\n") -> Dict[str, Any]:
        """
        Converts the ReaderResultGenerator object to a dictionary representation with unpacked content.
        This method collects all content from the generator and joins it into a single string.

        Arguments:
            chunk (Optional[int]): If provided, the content will be split into chunks of this size.
            separator (str): The string used to join the content from the generator. Defaults to newline character.

        Returns:
            Dict[str, Any]: A dictionary containing the content as a string, file_path, and exception attributes
            of the ReaderResultGenerator object.
        """
        try:
            content: str = separator.join(line for i, line in enumerate(self.content_generator) if chunk is None or i < chunk)

            traceback = None
            if self.exception:
                traceback = self.exception.__traceback__

            return {
                'content': content,
                'file_path': str(self.file_path) if self.file_path else None,
                'exception': {
                    'type': type(self.exception).__name__,
                    'message': str(self.exception),
                    'traceback': traceback 
                } if self.exception else None
            }
        except Exception as e:
            raise ToDictError(f"Error converting ReaderResultGenerator to dict: {e}") from e


    def to_json_unpacked(self) -> str:
        """
        Converts the ReaderResultGenerator object to a JSON string representation with unpacked content.
        
        Returns:
            str: A JSON string containing the content, file_path, and exception attributes of
            the ReaderResultGenerator object.
        """
        try:
            return json.dumps(self.to_dict_unpacked(), ensure_ascii=False)
        except Exception as e:
            raise ToJsonError(f"Error converting ReaderResultGenerator to JSON: {e}") from e


    def to_yaml_unpacked(self) -> str:
        """
        Converts the ReaderResultGenerator object to a YAML string representation with unpacked content.
        
        Returns:
            str: A YAML string containing the content, file_path, and exception attributes of
            the ReaderResultGenerator object.
        """
        try:
            return yaml.dump(self.to_dict_unpacked(), allow_unicode=True, default_flow_style=False)
        except Exception as e:
            raise ToYamlError(f"Error converting ReaderResultGenerator to YAML: {e}") from e

