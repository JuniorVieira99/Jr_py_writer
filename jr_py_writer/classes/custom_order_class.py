# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
import json
import re
import logging

from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict
from pathlib import Path

# Third-party imports
import yaml


# ----------------------------------------------------------------------------------------------
# Exceptions
# ----------------------------------------------------------------------------------------------

class CustomOrderError(Exception):
    """Base class for exceptions in the CustomOrder module."""

    pass

class ConstructError(CustomOrderError):
    """Exception raised for errors in the construction of a CustomOrder."""
    
    pass

class AddError(CustomOrderError):
    """Exception raised for errors in adding paths to a CustomOrder."""
    
    pass

class AddBatchError(CustomOrderError):
    """Exception raised for errors in adding multiple paths to a CustomOrder."""
    
    pass

class RemoveError(CustomOrderError):
    """Exception raised for errors in removing paths from a CustomOrder."""
    
    pass

class RemoveBatchError(CustomOrderError):
    """Exception raised for errors in removing multiple paths from a CustomOrder."""
    
    pass

class ClearError(CustomOrderError):
    """Exception raised for errors in clearing paths from a CustomOrder."""
    
    pass

class FromToError(CustomOrderError):
    """Exception raised for errors in converting from or to a CustomOrder."""
    
    pass

class ToFromError(CustomOrderError):
    """Exception raised for errors in converting to or from a CustomOrder."""
    
    pass


# ----------------------------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------------------------

def _writer_validation(
    dict_paths: Dict[Path, List[str]],
    security_path_filter: Optional[str] = None,
    security_message_filter: Optional[str] = None
) -> Dict[Path, List[str]]:
    """
    Validate and secure the paths and messages in the provided dictionary.
    Arguments:
        dict_paths (Dict[Path, List[str]]) : A dictionary where keys are paths and values are lists of messages.
        security_path_filter (Optional[str]) : A regex pattern to filter paths for security.
        security_message_filter (Optional[str]) : A regex pattern to filter messages for security.
    Returns:
       out (Dict[Path, List[str]]) : A dictionary with secured paths and messages.
    """
    
    secured_dict_paths: Dict[Path, List[str]] = {}

     # Ensure all paths are of type Path and secure them
    for path, list_mes in dict_paths.items():

        # Path validation
        if isinstance(path, str):
            new_path: Path = Path(path).resolve()
        elif isinstance(path, Path):
            if security_path_filter:
                if not re.match(security_path_filter, str(path)):
                    raise ValueError(f"Path in write_paths: '{path}' does not match the security filter.")
            new_path: Path = path.resolve()
        else:
            raise TypeError("write_paths key must be strings or Path objects.")
        
        # List Messages validation
        if not isinstance(list_mes, list):
            raise TypeError("write_paths values must be lists.")
        for mes in list_mes:
            if not isinstance(mes, str):
                raise TypeError("write_paths list items must be strings.")
            if not mes:
                raise ValueError("write_paths list items cannot be empty strings.")
            if security_message_filter:
                if not re.match(security_message_filter, mes):
                    raise ValueError(f"Message '{mes}' in write_paths does not match the security message filter.")
        
        # Update secured write paths
        secured_dict_paths[new_path] = list_mes

    return secured_dict_paths


def _reader_validation(
    list_paths: List[Path],
    security_path_filter: Optional[str] = None,
) -> List[Path]:
    """
    Validate and secure the paths in the provided list.
    Arguments:
        list_paths (List[Path]) : A list of paths to read from.
        security_path_filter (Optional[str]) : A regex pattern to filter paths for security.
    Returns:
       out (List[Path]) : A list with secured paths.
    """
    
    secured_list_paths: List[Path] = []

    # Ensure all paths are of type Path and secure them
    for path in list_paths:
        if isinstance(path, str):
            new_path: Path = Path(path).resolve()
        elif isinstance(path, Path):
            if security_path_filter:
                if not re.match(security_path_filter, str(path)):
                    raise ValueError(f"Path in read_paths: '{path}' does not match the security filter.")
            new_path: Path = path.resolve()
        else:
            raise TypeError("read_paths items must be strings or Path objects.")
        
        secured_list_paths.append(new_path)

    return secured_list_paths


# ----------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------

@dataclass
class CustomOrder:
    """
    A class to represent a custom order for writing and reading paths with security filters.
    This class allows you to define an order with specific paths for writing and reading,
    along with optional security filters for both paths and messages.
    It provides methods to add, remove, and clear paths, as well as to convert the order
    to various formats (dictionary, JSON, YAML).

    Attributes:
        order_id (str): Unique identifier for the order.
        security_path_filter (Optional[str]): A regex pattern to filter paths for security.
        security_message_filter (Optional[str]): A regex pattern to filter messages for security.
        write_paths (Dict[Path, List[str]]): A dictionary where keys are paths and values are lists of messages to write.
        read_paths (List[Path]): A list of paths to read from.
        use_logger (bool): Flag to indicate if logging is enabled.
        logger (Optional[logging.Logger]): Placeholder for a logger, if needed.

    Example:
    ```python

    write_paths = {
        Path("/secure/data1.txt"): ["message1", "message2"],
        Path("/secure/data2.txt"): ["message3"],
        Path("/public/data.txt"): ["public_message"],
        Path("/another/path.txt"): ["another_message"]
    }

    read_paths = [Path("/secure/data3.txt"), Path("/secure/data4.txt")]
    
    security_path_filter = r"^/secure/.*"
    security_message_filter = r"^[a-zA-Z0-9_]+$"
    
    # Create a CustomOrder instance
    custom_order = CustomOrder(
        order_id="order123",
        security_path_filter=security_path_filter,
        security_message_filter=security_message_filter,
        write_paths=write_paths,
        read_paths=read_paths
    )

    # add a write path
    custom_order.add_write_path(Path("/secure/data5.txt"), ["message4", "message5"])
    # add a read path
    custom_order.add_read_path(Path("/secure/data6.txt"))
    # remove a write path
    custom_order.remove_write_path(Path("/secure/data1.txt"))
    # remove a read path
    custom_order.remove_read_path(Path("/secure/data3.txt"))
    
    # Convert to dictionary
    order_dict = custom_order.to_dict()
    # Convert to JSON
    order_json = custom_order.to_json()
    # Convert to YAML
    order_yaml = custom_order.to_yaml()

    # Create a CustomOrder instance from a dictionary
    custom_order_from_dict = CustomOrder.from_dict(order_dict)
    # Create a CustomOrder instance from a JSON string
    custom_order_from_json = CustomOrder.from_json(order_json)
    # Create a CustomOrder instance from a YAML string
    ```
    """


    # -------------
    # Attributes

    order_id: str
    security_path_filter: Optional[str] = None
    security_message_filter: Optional[str] = None
    write_paths: Dict[Path, List[str]] = field(default_factory=dict)
    read_paths: List[Path] = field(default_factory=list)
    use_logger: bool = True  # Flag to indicate if logging is enabled
    logger: Optional[logging.Logger] = None  # Placeholder for a logger, if needed


    # -------------
    # Post-initialization

    def __post_init__(self):
        """Post-initialization method to validate and secure the CustomOrder instance."""
        try:
            # Initialize logger if not provided
            if self.logger is None:
                self.logger = logging.getLogger(__name__)
                self.logger.setLevel(logging.DEBUG)
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
            else:
                if not isinstance(self.logger, logging.Logger):
                    raise TypeError("Logger must be an instance of logging.Logger.")
                
            # if use_logger is not set, default to True
            if not hasattr(self, 'use_logger'):
                self.use_logger = True

            # Validate the order_id and paths
            if not isinstance(self.order_id, str):
                raise TypeError("Order ID must be a string.")
            elif len(self.order_id) == 0:
                raise ValueError("Order ID cannot be an empty string.")
            elif len(self.order_id) > 255:
                raise ValueError("Order ID cannot exceed 255 characters.")
            
            if not isinstance(self.write_paths, dict):
                raise TypeError("Write paths must be a dict.")
            if not isinstance(self.read_paths, list):
                raise TypeError("Read paths must be a list.")
            
            # Security filter validation
            if self.security_path_filter is not None:
                if not isinstance(self.security_path_filter, str):
                    raise TypeError("Security filter must be a string or None.")
                elif len(self.security_path_filter) == 0:
                    raise ValueError("Security path filter cannot be an empty string.")
                
            if self.security_message_filter is not None:
                if not isinstance(self.security_message_filter, str):
                    raise TypeError("Security message filter must be a string or None.")
                elif len(self.security_message_filter) == 0:
                    raise ValueError("Security message filter cannot be an empty string.")
            
            # Validate and secure the write_paths
            security_write_paths: Dict[Path, List[str]] = _writer_validation(
                dict_paths=self.write_paths,
                security_path_filter=self.security_path_filter,
                security_message_filter=self.security_message_filter
            )

            # Validate and secure the read_paths
            security_read_paths: List[Path] = _reader_validation(
                list_paths=self.read_paths,
                security_path_filter=self.security_path_filter,
            )

            # Assign secured paths
            self.write_paths = security_write_paths
            self.read_paths = security_read_paths
       
        except Exception as e:
            # Log the error and raise a ConstructError
            if isinstance(self.logger, logging.Logger) and self.use_logger:
                self.logger.error(f"Error constructing CustomOrder: {e}")
            raise ConstructError(f"Error {e.__class__.__name__} constructing CustomOrder: {e}") from e


    # -------------
    # Magic Methods

    def __str__(self):
        """Return a string representation of the CustomOrder instance."""
        string: str = "\nCustomOrder:\n"
        string += f"\tOrder ID: {self.order_id}\n"
        string += f"\tSecurity Path Filter: {self.security_path_filter}\n"
        string += f"\tSecurity Message Filter: {self.security_message_filter}\n"
        string += "\tWrite Paths:\n"
        for path, messages in self.write_paths.items():
            string += f"\t\t{path}:\n"
            for message in messages:
                string += f"\t\t\t{message}\n"
        string += "  Read Paths:\n"
        for path in self.read_paths:
            string += f"\t\t{path}:\n"
        return string
    
    def __eq__(self, other: object) -> bool:
        """Check equality with another CustomOrder instance."""
        if not isinstance(other, CustomOrder):
            return False
        return (self.order_id == other.order_id and
                self.security_path_filter == other.security_path_filter and
                self.security_message_filter == other.security_message_filter and
                self.write_paths == other.write_paths and
                self.read_paths == other.read_paths
                )

    def __ne__(self, other: object) -> bool:
        """Check inequality with another CustomOrder instance."""
        if not isinstance(other, CustomOrder):
            return True
        return not self.__eq__(other)

    def __lt__(self, other: object) -> bool:
        """Check if this CustomOrder is less than another."""
        if not isinstance(other, CustomOrder):
            return False
        return len(self.write_paths) + len(self.read_paths) < len(other.write_paths) + len(other.read_paths)
    
    def __gt__(self, other: object) -> bool:
        """Check if this CustomOrder is greater than another."""
        if not isinstance(other, CustomOrder):
            return False
        return len(self.write_paths) + len(self.read_paths) > len(other.write_paths) + len(other.read_paths)
    
    def __ge__(self, other: object) -> bool:
        """Check if this CustomOrder is greater than or equal to another."""
        if not isinstance(other, CustomOrder):
            return False
        return len(self.write_paths) + len(self.read_paths) >= len(other.write_paths) + len(other.read_paths)

    def __len__(self) -> int:
        """Return the total number of paths in the order."""
        return len(self.write_paths) + len(self.read_paths)

    def __hash__(self) -> int:
        """Return a hash of the CustomOrder instance."""
        tuple_write_paths = tuple((str(path), tuple(messages)) for path, messages in self.write_paths.items())
        tuple_read_paths = tuple((str(path) for path in self.read_paths))
        # Use a tuple of the order_id, security_filter, write_paths, and read_paths for hashing
        return hash((self.order_id, self.security_path_filter, self.security_message_filter, tuple_write_paths, tuple_read_paths))
    
    def __contains__(self, item: Union[Path, str]) -> bool:
        """Check if a path is in the write or read paths."""
        if isinstance(item, str):
            item = Path(item)
        return item in self.write_paths or item in self.read_paths
    
    def __bool__(self) -> bool:
        """Return True if the CustomOrder has any paths."""
        return bool(self.write_paths or self.read_paths)
    

    # -------------
    # Methods


    # to_*

    def to_dict(self) -> Dict[str, Union[str, List[Path], Dict[Path, List[str]], None]]:
        """Return a dictionary representation of the CustomOrder instance."""
        try:
            return {
                'order_id': self.order_id,
                'security_path_filter': self.security_path_filter,
                'security_message_filter': self.security_message_filter,
                'write_paths': self.write_paths,
                'read_paths': self.read_paths
            }
        except Exception as e:
            if self.logger and self.use_logger:
                # Log the error if logging is enabled
                self.logger.error(f"Error converting CustomOrder to dict: {e}")
            raise ToFromError(f"Error {e.__class__.__name__} converting CustomOrder to dict: {e}") from e
        

    def to_json(self) -> str:
        """Return a JSON string representation of the CustomOrder instance."""
        try:
            return json.dumps(self.to_dict(), default=str, indent=4)
        except Exception as e:
            if self.logger and self.use_logger:
                # Log the error if logging is enabled
                self.logger.error(f"Error converting CustomOrder to JSON: {e}")
            raise ToFromError(f"Error {e.__class__.__name__} converting CustomOrder to JSON: {e}") from e
    

    def to_yaml(self) -> str:
        """Return a YAML string representation of the CustomOrder instance."""
        try:
            return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)
        except Exception as e:
            if self.logger and self.use_logger:
                # Log the error if logging is enabled
                self.logger.error(f"Error converting CustomOrder to YAML: {e}")
            raise ToFromError(f"Error {e.__class__.__name__} converting CustomOrder to YAML: {e}") from e
    

    # from_*

    @classmethod
    def from_dict(cls, data: Dict[str, Union[str, List[Path], None]]) -> 'CustomOrder':
        """Create a CustomOrder instance from a dictionary."""
        try:
            if not isinstance(data, dict):
                raise TypeError("Data must be a dictionary.")
            
            order_id = data.get('order_id', None)
            if not order_id:
                raise ValueError("Order ID cannot be empty.")
            if not isinstance(order_id, str):
                raise TypeError("Order ID must be a string.")

            security_path_filter = data.get('security_path_filter', None)
            if security_path_filter is not None and not isinstance(security_path_filter, str):
                raise TypeError("Security path filter must be a string or None.")
            
            security_message_filter = data.get('security_message_filter', None)
            if security_message_filter is not None and not isinstance(security_message_filter, str):
                raise TypeError("Security message filter must be a string or None.")
            
            write_paths = data.get('write_paths', {})
            read_paths = data.get('read_paths', [])
            
            return cls(
                order_id=order_id, 
                security_path_filter=security_path_filter,
                security_message_filter=security_message_filter, 
                write_paths=dict(write_paths) if isinstance(write_paths, dict) else {},
                read_paths=list(read_paths) if isinstance(read_paths, list) else []
            )
        except Exception as e:
            raise FromToError(f"Error {e.__class__.__name__} constructing CustomOrder from dict: {e}") from e


    @classmethod
    def from_json(cls, json_str: str) -> 'CustomOrder':
        """Create a CustomOrder instance from a JSON string."""
        try:
            try:
                data: Dict[str, Union[str, List[Path], None]] = json.loads(json_str)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
            return cls.from_dict(data)
        except Exception as e:
            raise FromToError(f"Error {e.__class__.__name__} constructing CustomOrder from JSON: {e}") from e


    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'CustomOrder':
        """Create a CustomOrder instance from a YAML string."""
        try:
            try:
                data: Dict[str, Union[str, List[Path], None]] = yaml.safe_load(yaml_str)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML: {e}")
            return cls.from_dict(data)
        except Exception as e:
            raise FromToError(f"Error {e.__class__.__name__} constructing CustomOrder from YAML: {e}") from e
        

    # adds

    def add_write_path(self, path: Path, messages: List[str]) -> None:
        """
        Add a write path with associated messages to the CustomOrder.

        Arguments:
            path (Path): The path to write to.
            messages (List[str]): A list of messages to write to the path.
        """
        try:
            if not isinstance(path, Path):
                raise TypeError("Path must be a Path object.")
            if not isinstance(messages, list):
                raise TypeError("Messages must be a list.")
            for message in messages:
                if not isinstance(message, str):
                    raise TypeError("Messages must be strings.")
                if not message:
                    raise ValueError("Messages cannot be empty strings.")
            
            # Validate and secure the path and messages
            secured_path = _writer_validation({path: messages}, self.security_path_filter, self.security_message_filter)

            if not secured_path:
                raise ValueError("No valid write paths or messages after security validation.")
            
            if path in self.write_paths:
                # If the path already exists, append the messages
                for mes in secured_path[path]:
                    if mes not in self.write_paths[path]:
                        self.write_paths[path].append(mes)
            else:
                # If the path does not exist, add it with the messages
                self.write_paths.update(secured_path)

        except Exception as e:
            if self.logger and self.use_logger:
                # Log the error if logging is enabled
                self.logger.error(f"Error adding write path: {e}")
            raise AddError(f"Error {e.__class__.__name__} adding write path: {e}") from e


    def add_read_path(self, path: Path) -> None:
        """
        Add a read path to the CustomOrder.

        Arguments:
            path (Path): The path to read from.
        """
        try:
            if not isinstance(path, Path):
                raise TypeError("Path must be a Path object.")
            
            if path in self.read_paths:
                raise ValueError(f"Read path '{path}' already exists in CustomOrder.")
            
            # Validate and secure the path
            secured_path = _reader_validation([path], self.security_path_filter)
            self.read_paths.extend(secured_path)

        except Exception as e:
            if self.logger and self.use_logger:
                # Log the error if logging is enabled
                self.logger.error(f"Error adding read path: {e}")
            raise AddError(f"Error {e.__class__.__name__} adding read path: {e}") from e


    def add_batch_write_paths(
        self, 
        dict_paths: Dict[Path, List[str]]
    ) -> None:
        """
        Add multiple write paths with associated messages to the CustomOrder.

        Arguments:
            dict_paths (Dict[Path, List[str]]): A dictionary where keys are paths and values are lists of messages to write.
        """
        try:
            if not isinstance(dict_paths, dict):
                raise TypeError("Write paths must be a dictionary.")
            
            secured_paths = _writer_validation(
                dict_paths=dict_paths,
                security_path_filter=self.security_path_filter,
                security_message_filter=self.security_message_filter
            )

            for path, messages in secured_paths.items():
                if path in self.write_paths:
                    # If the path already exists, append the messages
                    for mes in messages:
                        if mes not in self.write_paths[path]:
                            self.write_paths[path].append(mes)
                else:
                    # If the path does not exist, add it with the messages
                    self.write_paths[path] = messages
            
        except Exception as e:
            if self.logger and self.use_logger:
                # Log the error if logging is enabled
                self.logger.error(f"Error adding batch write paths: {e}")
            raise AddBatchError(f"Error {e.__class__.__name__} adding batch write paths: {e}") from e


    def add_batch_read_paths(self, list_paths: List[Path]) -> None:
        """
        Add multiple read paths to the CustomOrder.

        Arguments:
            list_paths (List[Path]): A list of paths to read from.
        """
        try:
            if not isinstance(list_paths, list):
                raise TypeError("Read paths must be a list.")
            
            secured_paths = _reader_validation(
                list_paths=list_paths,
                security_path_filter=self.security_path_filter
            )

            for path in secured_paths:
                if path in self.read_paths:
                    raise ValueError(f"Read path '{path}' already exists in CustomOrder.")
            
            self.read_paths.extend(secured_paths)
        except Exception as e:
            if self.logger and self.use_logger:
                # Log the error if logging is enabled
                self.logger.error(f"Error adding batch read paths: {e}")
            raise AddBatchError(f"Error {e.__class__.__name__} adding batch read paths: {e}") from e


    # removes

    def remove_write_path(self, path: Path) -> None:
        """
        Remove a write path from the CustomOrder.

        Arguments:
            path (Path): The path to remove.
        """
        try:
            if not isinstance(path, Path):
                raise TypeError("Path must be a Path object.")
            
            path = path.resolve()  # Ensure the path is resolved
            
            if path in self.write_paths:
                del self.write_paths[path]
            else:
                raise KeyError(f"Write path '{path}' not found in CustomOrder. {self.write_paths}")
            
        except Exception as e:
            if self.logger and self.use_logger:
                # Log the error if logging is enabled
                self.logger.error(f"Error removing write path: {e}")
            raise RemoveError(f"Error {e.__class__.__name__} removing write path: {e}") from e


    def remove_read_path(self, path: Path) -> None:
        """
        Remove a read path from the CustomOrder.

        Arguments:
            path (Path): The path to remove.
        """
        try:
            if not isinstance(path, Path):
                raise TypeError("Path must be a Path object.")
            
            path = path.resolve()  # Ensure the path is resolved
            
            if path in self.read_paths:
                self.read_paths.remove(path)
            else:
                raise KeyError(f"Read path '{path}' not found in CustomOrder.")
        except Exception as e:
            if self.logger and self.use_logger:
                # Log the error if logging is enabled
                self.logger.error(f"Error removing read path: {e}")
            raise RemoveError(f"Error {e.__class__.__name__} removing read path: {e}") from e


    def remove_batch_write_paths(self, list_paths: List[Path]) -> None:
        """
        Remove multiple write paths from the CustomOrder.

        Arguments:
            list_paths (List[Path]): A list of paths to remove.
        """
        try:
            if not isinstance(list_paths, list):
                raise TypeError("Write paths must be a list.")
            if len(list_paths) == 0:
                raise ValueError("Write paths list cannot be empty.")
            
            for path in list_paths:
                if not isinstance(path, Path):
                    raise TypeError("Each path must be a Path object.")
                self.remove_write_path(path)
        except Exception as e:
            if self.logger and self.use_logger:
                # Log the error if logging is enabled
                self.logger.error(f"Error removing batch write paths: {e}")
            raise RemoveBatchError(f"Error {e.__class__.__name__} removing batch write paths: {e}") from e


    def remove_batch_read_paths(self, list_paths: List[Path]) -> None:
        """
        Remove multiple read paths from the CustomOrder.

        Arguments:
            list_paths (List[Path]): A list of paths to remove.
        """
        try:
            if not isinstance(list_paths, list):
                raise TypeError("Read paths must be a list.")
            
            for path in list_paths:
                if not isinstance(path, Path):
                    raise TypeError("Each path must be a Path object.")
                self.remove_read_path(path)
        except Exception as e:
            if self.logger and self.use_logger:
                # Log the error if logging is enabled
                self.logger.error(f"Error removing batch read paths: {e}")
            raise RemoveBatchError(f"Error {e.__class__.__name__} removing batch read paths: {e}") from e


    def remove_all_write_paths(self) -> None:
        """
        Remove all write paths from the CustomOrder.
        """
        if hasattr(self, 'write_paths') and isinstance(self.write_paths, dict):
            self.write_paths.clear()


    def remove_all_read_paths(self) -> None:
        """
        Remove all read paths from the CustomOrder.
        """
        if hasattr(self, 'read_paths') and isinstance(self.read_paths, list):
            self.read_paths.clear()


    # clears

    def clear(self) -> None:
        """
        Clear all write and read paths from the CustomOrder.
        """
        try:
            self.remove_all_write_paths()
            self.remove_all_read_paths()
        except Exception as e:
            if self.logger and self.use_logger:
                # Log the error if logging is enabled
                self.logger.error(f"Error clearing CustomOrder: {e}")
            raise ClearError(f"Error {e.__class__.__name__} clearing CustomOrder: {e}") from e


