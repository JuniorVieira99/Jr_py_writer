# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
import gc
import logging

from pathlib import Path
from typing import Generator, List, Final, Dict

# Third-party imports
import pytest

# Local imports
from jr_py_writer.classes.custom_order_class import (
    CustomOrder,
    ConstructError,
    AddError,
    RemoveError,
    AddBatchError,
    RemoveBatchError,
)


# ----------------------------------------------------------------------------------------------
# Fixture
# ----------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def custom_order() -> Generator[CustomOrder, None, None]:
    """Fixture to create a CustomOrder instance."""
    # Create a CustomOrder instance
    order = CustomOrder(
        order_id = "test_order"
    )

    order.clear()  # Clear paths to ensure a clean state

    # Yield the instance for use in tests
    yield order

    order.clear()  # Clear paths after tests

    # Cleanup
    del order
    gc.collect()


def get_writer_paths(num:int) -> Dict[Path, List[str]]:
    """
    Generate a dictionary of writer paths with dummy data.
    
    Args:
        num (int): Number of writer paths to generate.
        tmp_path: Temporary path for the test.

    Returns:
        Dict[Path, List[str]]: Dictionary with writer paths and dummy data.
    """
    return {
        Path(f"writer_{i}.txt"): [f"data_{i}_{j}" for j in range(5)]
        for i in range(num)
    }


def get_read_paths(num: int) -> List[Path]:
    """
    Generate a list of read paths with dummy data.
    
    Args:
        num (int): Number of read paths to generate.

    Returns:
        List[Path]: List of read paths.
    """
    return [Path(f"read_path_{i}.txt") for i in range(num)]


# ----------------------------------------------------------------------------------------------
# Edge Cases
# ----------------------------------------------------------------------------------------------

EDGE_ORDER_ID: Final[List] = [
    5,
    5.5,
    "",
    {},
    [],
    None,
]

EDGE_SECURITY: Final[List] = [
    5,
    5.5,
    "",
    {},
    [],
    tuple()
]

EDGE_WRITER_PATHS: Final[List] = [
    5,
    5.5,
    "",
    [],
    tuple(),
    None,
]

EDGE_READ_PATHS: Final[List] = [
    5,
    5.5,
    "",
    {},
    tuple(),
    None,
]


# ----------------------------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------------------------

def test_custom_order_initialization(custom_order: CustomOrder) -> None:
    """Test the initialization of CustomOrder."""
    assert custom_order.order_id == "test_order"
    assert custom_order.write_paths == {}
    assert custom_order.read_paths == []
    assert custom_order.use_logger is True
    assert isinstance(custom_order.logger, logging.Logger)


@pytest.mark.parametrize("order_id", EDGE_ORDER_ID)
def test_custom_order_invalid_order_id(order_id) -> None:
    """Test CustomOrder initialization with invalid order_id."""
    with pytest.raises(ConstructError):
        CustomOrder(order_id=order_id)


@pytest.mark.parametrize("security", EDGE_SECURITY)
def test_custom_order_invalid_security(security) -> None:
    """Test CustomOrder initialization with invalid security."""
    with pytest.raises(ConstructError):
        CustomOrder(order_id="test_order", security_path_filter=security)
    with pytest.raises(ConstructError):
        CustomOrder(order_id="test_order", security_message_filter=security)


@pytest.mark.parametrize("writer_paths", EDGE_WRITER_PATHS)
def test_custom_order_invalid_writer_paths(writer_paths) -> None:
    """Test CustomOrder initialization with invalid writer_paths."""
    with pytest.raises(ConstructError):
        CustomOrder(order_id="test_order", write_paths=writer_paths)


@pytest.mark.parametrize("read_paths", EDGE_READ_PATHS)
def test_custom_order_invalid_read_paths(read_paths) -> None:
    """Test CustomOrder initialization with invalid read_paths."""
    with pytest.raises(ConstructError):
        CustomOrder(order_id="test_order", read_paths=read_paths)


@pytest.mark.parametrize("security", EDGE_SECURITY)
def test_custom_order_invalid_logger(security) -> None:
    """Test CustomOrder initialization with invalid logger."""
    with pytest.raises(ConstructError):
        CustomOrder(order_id="test_order", logger=security)


# ----------------------------------------------------------------------------------------------
# Functionality Tests
# ----------------------------------------------------------------------------------------------


# Add

@pytest.mark.parametrize("path, messages", [
    (Path("/valid/path.txt"), ["message1", "message2"]),
    (Path("/another/valid/path.txt"), ["message3"]),
    (Path("/empty/messages/path.txt"), ["message4"]),
])
def test_add_write_path_valid(custom_order: CustomOrder, path, messages) -> None:
    """Test adding valid write paths to CustomOrder."""
    custom_order.add_write_path(path, messages)
    for path, list_msg in custom_order.write_paths.items():
        assert isinstance(path, Path)
        assert isinstance(list_msg, list)
        assert all(isinstance(msg, str) for msg in list_msg)
        for message in messages:
            assert message in list_msg
    custom_order.clear()  # Clear after test to avoid side effects


@pytest.mark.parametrize("path, messages", [
    (5, ["message1", "message2"]),
    (Path("/valid/path.txt"), 5),
    (Path("/valid/path.txt"), None),
    (None, ["message1"]),
])
def test_add_write_path_invalid(custom_order: CustomOrder, path, messages) -> None:
    """Test adding invalid write paths to CustomOrder."""
    with pytest.raises(AddError):
        custom_order.add_write_path(path, messages)


def test_add_read_path_valid(custom_order: CustomOrder) -> None:
    """Test adding valid read paths to CustomOrder."""
    paths: List[Path] = get_read_paths(5)
    for path in paths:
        custom_order.add_read_path(path)
    
    assert len(custom_order.read_paths) == 5
    for path in custom_order.read_paths:
        assert isinstance(path, Path)

    custom_order.clear()  # Clear after test to avoid side effects


@pytest.mark.parametrize("path", [
    5,
    None,
    "",
    [],
])
def test_add_read_path_invalid(custom_order: CustomOrder, path) -> None:
    """Test adding invalid read paths to CustomOrder."""
    with pytest.raises(AddError):
        custom_order.add_read_path(path)


# Remove

def test_remove_write_path_valid(custom_order: CustomOrder) -> None:
    """Test removing valid write paths from CustomOrder."""
    custom_order.add_write_path(Path("/valid/path.txt"), ["message1"])
    custom_order.remove_write_path(Path("/valid/path.txt"))

    custom_order.clear()  # Clear after test to avoid side effects


@pytest.mark.parametrize("path", [
    Path("/nonexistent/path.txt"),
    5,
    None,
])
def test_remove_write_path_invalid(custom_order: CustomOrder, path) -> None:
    """Test removing invalid write paths from CustomOrder."""
    with pytest.raises(RemoveError):
        custom_order.remove_write_path(path)


@pytest.mark.parametrize("path", [
    Path("/valid/path.txt"),
    Path("/another/valid/path.txt"),
])
def test_remove_read_path_valid(custom_order: CustomOrder, path) -> None:
    """Test removing valid read paths from CustomOrder."""
    custom_order.add_read_path(path)
    custom_order.remove_read_path(path)
    assert path not in custom_order.read_paths


@pytest.mark.parametrize("path", [
    Path("/nonexistent/path.txt"),
    5,
    None,
])
def test_remove_read_path_invalid(custom_order: CustomOrder, path) -> None:
    """Test removing invalid read paths from CustomOrder."""
    with pytest.raises(RemoveError):
        custom_order.remove_read_path(path)


# Batch Add/Remove

def test_add_batch_write_paths_valid(custom_order: CustomOrder) -> None:
    """Test adding a batch of valid write paths to CustomOrder."""
    paths = get_writer_paths(5)
    custom_order.add_batch_write_paths(paths)

    assert len(custom_order.write_paths) == 5

    for path, messages in custom_order.write_paths.items():
        assert isinstance(path, Path)
        assert isinstance(messages, list)
        assert all(isinstance(msg, str) for msg in messages)
    
    for path in paths.keys():
        assert path.resolve() in custom_order.write_paths

    for messages in paths.values():
        assert messages in custom_order.write_paths.values()


@pytest.mark.parametrize("paths", EDGE_WRITER_PATHS)
def test_add_batch_write_paths_invalid(custom_order: CustomOrder, paths) -> None:
    """Test adding a batch of invalid write paths to CustomOrder."""
    with pytest.raises(AddBatchError):
        custom_order.add_batch_write_paths(paths)


def test_remove_batch_write_paths_valid(custom_order: CustomOrder) -> None:
    """Test removing a batch of valid write paths from CustomOrder."""
    paths = get_writer_paths(5)
    custom_order.add_batch_write_paths(paths)
    
    custom_order.remove_batch_write_paths(list(paths.keys()))

    assert len(custom_order.write_paths) == 0


@pytest.mark.parametrize("paths", EDGE_WRITER_PATHS)
def test_remove_batch_write_paths_invalid(custom_order: CustomOrder, paths) -> None:
    """Test removing a batch of invalid write paths from CustomOrder."""
    with pytest.raises(RemoveBatchError):
        custom_order.remove_batch_write_paths(paths)


# Clear

def test_clear_paths(custom_order: CustomOrder) -> None:
    """Test clearing all paths in CustomOrder."""
    custom_order.add_write_path(Path("/valid/path.txt"), ["message1"])
    custom_order.add_read_path(Path("/valid/read/path.txt"))
    custom_order.clear()
    assert custom_order.write_paths == {}
    assert custom_order.read_paths == []

