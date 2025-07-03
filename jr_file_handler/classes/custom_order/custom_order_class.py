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
