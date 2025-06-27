# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

# Standard library imports
from pathlib import Path
from typing import Generator, List, Final, Tuple, Any
import time
import json
import yaml

# Third-party imports
import pytest
import psutil

# Local imports
from jr_py_writer.classes.reader_result import (
    ReaderResultGenerator, ReaderResultStr,
    ConstructionError,
    AddContentError,
    SetterError,
    MagicMethodError,
    ToDictError,
    ToJsonError,
    ToYamlError,
)

# ----------------------------------------------------------------------------------------------
# Fixture Cases
# ----------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def reader_result_str_fixture() -> Generator[ReaderResultStr, None, None]:
    """Fixture to provide a ReaderResultStr instance for testing."""
    result = ReaderResultStr(content="Test content", file_path=Path("test.txt"))
    yield result
    # Cleanup if necessary
    del result


@pytest.fixture(scope="module")
def reader_result_generator_fixture() -> Generator[ReaderResultGenerator, None, None]:
    """Fixture to provide a ReaderResultGenerator instance for testing."""
    generator = (f"Line {i}" for i in range(3))
    result = ReaderResultGenerator(content_generator=generator, file_path=Path("test.txt"))
    yield result
    # Cleanup if necessary
    del result


@pytest.fixture(scope="module")
def generator_fixture() -> Generator[str, None, None]:
    """Fixture to provide a generator for testing."""
    for line in (f"Line {i}" for i in range(10)):
        yield line


def make_generator(num:int) -> Generator[str, None, None]:
    """Helper function to create a generator that yields a specified number of lines."""
    for i in range(num):
        yield f"Line {i}"


# ----------------------------------------------------------------------------------------------
# Tests Cases
# ----------------------------------------------------------------------------------------------


EDGE_RESULT_CONTENT: Final[List[Tuple[Any,...]]] = [
    # Content Errors
    (5, Path("test.txt"), None),
    (5.5, Path("test.txt"), None),
    (True, Path("test.txt"), None),
    ([], Path("test.txt"), None),
    ({}, Path("test.txt"), None),
    (set(), Path("test.txt"), None)
]


EDGE_RESULT_FILE_PATH: Final[List[Tuple[Any,...]]] = [
    # File Path Errors
    ("Test content", 5, None),
    ("Test content", 5.5, None),
    ("Test content", True, None),
    ("Test content", [], None),
    ("Test content", {}, None),
    ("Test content", set(), None)
]


EDGE_RESULT_GEN_FILE_PATH: Final[List[Tuple[Any,...]]] = [
    # Generator File Path Errors
    (make_generator(2), 5, None),
    (make_generator(2), 5.5, None),
    (make_generator(2), True, None),
    (make_generator(2), [], None),
    (make_generator(2), {}, None),
    (make_generator(2), set(), None)
]


EDGE_RESULT_EXCEPTION: Final[List[Tuple[Any,...]]] = [
    # Exception Errors
    ("Test content", Path("test.txt"), 5),
    ("Test content", Path("test.txt"), 5.5),
    ("Test content", Path("test.txt"), True),
    ("Test content", Path("test.txt"), []),
    ("Test content", Path("test.txt"), {}),
    ("Test content", Path("test.txt"), set())
]


EDGE_RESULT_GEN_EXCEPTION: Final[List[Tuple[Any,...]]] = [
    # Generator Exception Errors
    (make_generator(2), Path("test.txt"), 5),
    (make_generator(2), Path("test.txt"), 5.5),
    (make_generator(2), Path("test.txt"), True),
    (make_generator(2), Path("test.txt"), []),
    (make_generator(2), Path("test.txt"), {}),
    (make_generator(2), Path("test.txt"), set())
]


EDGE_RESULT_MAGIC_METHOD: Final[List[Any]] = [
    # Magic Method Errors
    5, 5.5, True, [], {}, set(), "", Path("test.txt")
]


# ----------------------------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------------------------

# ReaderResultStr

# ---------------------
# Edge Cases


@pytest.mark.parametrize("content", EDGE_RESULT_CONTENT)
def test_reader_result_str_content_errors(content):
    """Test that ReaderResultStr raises ConstructionError for invalid content types."""
    with pytest.raises(ConstructionError):
        ReaderResultStr(content=content[0], file_path=content[1], exception=content[2])


@pytest.mark.parametrize("file_path", EDGE_RESULT_FILE_PATH)
def test_reader_result_str_file_path_errors(file_path):
    """Test that ReaderResultStr raises ConstructionError for invalid file_path types."""
    with pytest.raises(ConstructionError):
        ReaderResultStr(content=file_path[0], file_path=file_path[1], exception=file_path[2])


@pytest.mark.parametrize("exception", EDGE_RESULT_EXCEPTION)
def test_reader_result_str_exception_errors(exception):
    """Test that ReaderResultStr raises ConstructionError for invalid exception types."""
    with pytest.raises(ConstructionError):
        ReaderResultStr(content=exception[0], file_path=exception[1], exception=exception[2])


# ---------------------
# Edge Cases for Setters

@pytest.mark.parametrize("content", EDGE_RESULT_CONTENT)
def test_reader_result_str_set_content_errors(reader_result_str_fixture, content):
    """Test that ReaderResultStr raises AddContentError for invalid content types."""
    with pytest.raises(SetterError):
        reader_result_str_fixture.content = content[0]


@pytest.mark.parametrize("file_path", EDGE_RESULT_FILE_PATH)
def test_reader_result_str_set_file_path_errors(reader_result_str_fixture, file_path):
    """Test that ReaderResultStr raises SetterError for invalid file_path types."""
    with pytest.raises(SetterError):
        reader_result_str_fixture.file_path = file_path[0]


@pytest.mark.parametrize("exception", EDGE_RESULT_EXCEPTION)
def test_reader_result_str_set_exception_errors(reader_result_str_fixture, exception):
    """Test that ReaderResultStr raises SetterError for invalid exception types."""
    with pytest.raises(SetterError):
        reader_result_str_fixture.exception = exception[0]


# ---------------------
# Edge Cases for Magic Methods

@pytest.mark.parametrize("magic_method", EDGE_RESULT_MAGIC_METHOD)
def test_reader_result_str_magic_methods_errors(reader_result_str_fixture, magic_method):
    """Test that ReaderResultStr raises MagicMethodError for invalid magic method calls."""
    with pytest.raises(MagicMethodError):
        _  = reader_result_str_fixture + magic_method
    with pytest.raises(MagicMethodError):
        _ = reader_result_str_fixture - magic_method
    with pytest.raises(MagicMethodError):
        reader_result_str_fixture += magic_method
    with pytest.raises(MagicMethodError):
        reader_result_str_fixture -= magic_method


@pytest.mark.parametrize("magic_method", EDGE_RESULT_MAGIC_METHOD)
def test_reader_result_str_magic_methods_comparison_errors(reader_result_str_fixture, magic_method):
    """Test that ReaderResultStr raises MagicMethodError for invalid comparison operations."""
    result = reader_result_str_fixture < magic_method
    assert result is False, f"Expected False for < comparison with {magic_method}"
    result = reader_result_str_fixture > magic_method
    assert result is False, f"Expected False for > comparison with {magic_method}"
    result = reader_result_str_fixture <= magic_method
    assert result is False, f"Expected False for <= comparison with {magic_method}"
    result = reader_result_str_fixture >= magic_method
    assert result is False, f"Expected False for >= comparison with {magic_method}"
    result = reader_result_str_fixture == magic_method
    assert result is False, f"Expected False for == comparison with {magic_method}"
    result = reader_result_str_fixture != magic_method
    assert result is True, f"Expected True for != comparison with {magic_method}"


# ---------------------
# Initialization and Setters

def test_reader_result_str_initialization():
    """Test the initialization of ReaderResultStr."""
    result = ReaderResultStr(content="Test content", file_path=Path("test.txt"))
    assert result.content == "Test content"
    assert result.file_path == Path("test.txt")
    assert result.exception is None


def test_reader_result_str_setters():
    """Test the setters of ReaderResultStr."""
    result = ReaderResultStr(content="Initial content")
    result.content = "Updated content"
    result.file_path = Path("updated.txt")
    result.exception = ValueError("Test exception")
    assert result.content == "Updated content"
    assert result.file_path == Path("updated.txt")
    assert isinstance(result.exception, ValueError)


def test_reader_result_str_to_dict():
    """Test the to_dict method of ReaderResultStr."""
    result = ReaderResultStr(content="Test content", file_path=Path("test.txt"))
    result_dict = result.to_dict()
    assert result_dict["content"] == "Test content"
    assert result_dict["file_path"] == "test.txt"
    assert result_dict["exception"] is None


def test_reader_result_str_to_dict_with_exception():
    """Test the to_dict method of ReaderResultStr with an exception."""
    result = ReaderResultStr(content="Test content", file_path=Path("test.txt"), exception=ValueError("Test exception"))
    result_dict = result.to_dict()
    assert result_dict["content"] == "Test content"
    assert result_dict["file_path"] == "test.txt"
    assert isinstance(result_dict["exception"], dict)
    assert result_dict["exception"]["type"] == "ValueError"
    assert result_dict["exception"]["message"] == "Test exception"


def test_reader_result_str_to_dict_with_traceback():
    """Test the to_dict method of ReaderResultStr with an exception and traceback."""
    try:
        raise ValueError("Test exception")
    except ValueError as e:
        result = ReaderResultStr(content="Test content", file_path=Path("test.txt"), exception=e)
    
    result_dict = result.to_dict()
    assert result_dict["content"] == "Test content"
    assert result_dict["file_path"] == "test.txt"
    assert isinstance(result_dict["exception"], dict)
    assert result_dict["exception"]["type"] == "ValueError"
    assert result_dict["exception"]["message"] == "Test exception"
    assert "traceback" in result_dict["exception"]

    print("Result Dictionary with Traceback:\n", result_dict)


def test_reader_result_str_to_json():
    """Test the to_json method of ReaderResultStr."""
    result = ReaderResultStr(content="Test content", file_path=Path("test.txt"))
    result_json = result.to_json()
    json_dict = json.loads(result_json)
    assert json_dict["content"] == "Test content"
    assert json_dict["file_path"] == "test.txt"
    assert json_dict["exception"] is None


def test_reader_result_str_to_yaml():
    """Test the to_yaml method of ReaderResultStr."""
    result = ReaderResultStr(content="Test content", file_path=Path("test.txt"))
    result_yaml = result.to_yaml()
    assert "Test content" in result_yaml
    assert "test.txt" in result_yaml
    assert "exception: null" in result_yaml
    dict_yaml = yaml.safe_load(result_yaml)
    assert dict_yaml["content"] == "Test content"
    assert dict_yaml["file_path"] == "test.txt"
    assert dict_yaml["exception"] is None


# ---------------------
# Magic Methods

def test_reader_result_str_magic_methods():
    """Test the magic methods of ReaderResultStr."""
    result1 = ReaderResultStr(content="Test content", file_path=Path("test1.txt"))
    result2 = ReaderResultStr(content="Another larger content", file_path=Path("test2.txt"))
    result3 = ReaderResultStr(content="Test content", file_path=Path("test1.txt"))

    # Equality and inequality
    assert result1 == result3
    assert result1 != result2

    # Less than and greater than
    assert result1 < result2 or result1.content < result2.content
    assert result2 > result1 or result2.content > result1.content

    # Less than or equal to and greater than or equal to
    assert result1 <= result3
    assert result2 >= result1

    # Addition and subtraction
    result_add = result1 + result2
    assert isinstance(result_add, ReaderResultStr)
    assert result_add.content == "Test contentAnother larger content"
    assert len(result_add.content) == len(result1.content) + len(result2.content)

    result_sub = result2 - result1
    assert isinstance(result_sub, ReaderResultStr)
    assert result_sub.content == "Another larger content", f"Expected content to be 'Another larger content', got {result_sub.content}"

    # In-place addition and subtraction
    result1 += result2
    assert result1.content == "Test contentAnother larger content"
    result2 -= result1
    assert result2.content == "Another larger content", f"Expected content to be 'Another larger content', got {result2.content}"


# ReaderResultGenerator

# ---------------------
# Edge Cases


@pytest.mark.parametrize("content_generator", EDGE_RESULT_CONTENT)
def test_reader_result_generator_content_generator_errors(content_generator):
    """Test that ReaderResultGenerator raises ConstructionError for invalid content_generator types."""
    with pytest.raises(ConstructionError):
        ReaderResultGenerator(content_generator=content_generator[0], file_path=content_generator[1], exception=content_generator[2])


@pytest.mark.parametrize("file_path", EDGE_RESULT_GEN_FILE_PATH)
def test_reader_result_generator_file_path_errors(file_path):
    """Test that ReaderResultGenerator raises ConstructionError for invalid file_path types."""
    with pytest.raises(ConstructionError):
        ReaderResultGenerator(content_generator=file_path[0], file_path=file_path[1], exception=file_path[2])


@pytest.mark.parametrize("exception", EDGE_RESULT_GEN_EXCEPTION)
def test_reader_result_generator_exception_errors(exception):
    """Test that ReaderResultGenerator raises ConstructionError for invalid exception types."""
    with pytest.raises(ConstructionError):
        ReaderResultGenerator(content_generator=exception[0], file_path=exception[1], exception=exception[2])


# ---------------------
# Edge Cases for Setters


@pytest.mark.parametrize("content_generator", EDGE_RESULT_CONTENT)
def test_reader_result_generator_set_content_generator_errors(reader_result_generator_fixture, content_generator):
    """Test that ReaderResultGenerator raises AddContentError for invalid content_generator types."""
    with pytest.raises(AddContentError):
        reader_result_generator_fixture.content_generator = content_generator[0]


@pytest.mark.parametrize("file_path", EDGE_RESULT_FILE_PATH)
def test_reader_result_generator_set_file_path_errors(reader_result_generator_fixture, file_path):
    """Test that ReaderResultGenerator raises SetterError for invalid file_path types."""
    with pytest.raises(SetterError):
        reader_result_generator_fixture.file_path = file_path[1]


@pytest.mark.parametrize("exception", EDGE_RESULT_EXCEPTION)
def test_reader_result_generator_set_exception_errors(reader_result_generator_fixture, exception):
    """Test that ReaderResultGenerator raises SetterError for invalid exception types."""
    with pytest.raises(SetterError):
        reader_result_generator_fixture.exception = exception[2]


# ---------------------
# Initialization

def test_reader_result_generator_initialization():
    generator = (f"Line {i}" for i in range(3))
    result = ReaderResultGenerator(content_generator=generator, file_path=Path("test.txt"))
    assert result.file_path == Path("test.txt")
    assert result.exception is None
    assert list(result.content_generator) == ["Line 0", "Line 1", "Line 2"]


@pytest.mark.parametrize("num_lines", [0, 1, 5, 10])
def test_reader_result_generator_content(num_lines):
    """Test the content of ReaderResultGenerator."""
    generator = make_generator(num_lines)
    result = ReaderResultGenerator(content_generator=generator, file_path=Path("test.txt"))
    assert all(isinstance(line, str) for line in result.content_generator)
    for i, line in enumerate(result.content_generator):
        assert isinstance(line, str), f"Expected line to be a string, got {type(line)}"
        assert line == f"Line {i}", f"Expected line to be 'Line {i}', got '{line}'"
        assert generator.__next__() == f"Line {i}", f"Expected next line to be 'Line {i}', got '{generator.__next__()}'"

    
def test_reader_result_generator_to_dict_unpacked():
    generator = (f"Line {i}" for i in range(3))
    result = ReaderResultGenerator(content_generator=generator, file_path=Path("test.txt"))
    result_dict = result.to_dict_unpacked()
    assert isinstance(result_dict, dict)
    assert result_dict["content"] == "Line 0\nLine 1\nLine 2"


def test_reader_result_generator_to_json_unpacked():
    generator = (f"Line {i}" for i in range(3))
    result = ReaderResultGenerator(content_generator=generator, file_path=Path("test.txt"))
    result_json = result.to_json_unpacked()
    assert "Line 0" in result_json
    assert "Line 1" in result_json
    assert "Line 2" in result_json


def test_reader_result_generator_to_yaml_unpacked():
    generator = (f"Line {i}" for i in range(3))
    result = ReaderResultGenerator(content_generator=generator, file_path=Path("test.txt"))
    result_yaml = result.to_yaml_unpacked()
    assert "Line 0" in result_yaml
    assert "Line 1" in result_yaml
    assert "Line 2" in result_yaml


# ----------------------------------------------------------------------------------------------
# Memory
# ----------------------------------------------------------------------------------------------


def test_memory_reader_result_str():
    """Test the memory usage of ReaderResultStr."""

    # Measure memory before and after accessing content
    process = psutil.Process()
    initial_memory = process.memory_info().rss

    result = ReaderResultStr(content="Test content", file_path=Path("test.txt"), exception=ValueError("Test exception"))

    string = result.content  # Access content to trigger memory allocation
    assert isinstance(string, str), "Expected content to be a string"
    assert string == "Test content", f"Expected content to be 'Test content', got '{string}'"

    # Measure memory after accessing content
    final_memory = process.memory_info().rss
    memory_usage = final_memory - initial_memory
    print(f"\nMemory usage for ReaderResultStr: {memory_usage / 1024:.4f} KB")

    # Check if memory usage is within a reasonable limit
    assert memory_usage < 1024 * 1024  # Less than 1 MB


def test_memory_reader_result_generator():
    """Test the memory usage of ReaderResultGenerator."""
    generator = (f"Line {i}" for i in range(1000))  # Large generator

    # Measure memory before and after accessing content
    process = psutil.Process()
    initial_memory = process.memory_info().rss

    result = ReaderResultGenerator(content_generator=generator, file_path=Path("test.txt"))

    gen_list = list(result.content_generator)  # Access content to trigger memory allocation
    
    # Measure memory after accessing content
    final_memory = process.memory_info().rss
    memory_usage = final_memory - initial_memory
    print(f"\nMemory usage for ReaderResultGenerator: {memory_usage / 1024:.4f} KB")

    assert len(gen_list) == 1000, "Expected 1000 lines in the generator"

    # Check if memory usage is within a reasonable limit
    assert memory_usage < 10 * 1024 * 1024  # Less than 10 MB
    
   
def test_memory_reader_result_generator_large():
    """Test the memory usage of ReaderResultGenerator with a large generator."""

    generator = make_generator(10000)  # Large generator

    # Measure memory before and after accessing content
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    result = ReaderResultGenerator(content_generator=generator, file_path=Path("test.txt"))

    gen_list = list(result.content_generator)  # Access content to trigger memory allocation
    
    # Measure memory after accessing content
    final_memory = process.memory_info().rss
    memory_usage = final_memory - initial_memory
    print(f"\nMemory usage for large ReaderResultGenerator: {memory_usage / 1024:.4f} KB")

    assert len(gen_list) == 10000, "Expected 10000 lines in the generator"

    # Check if memory usage is within a reasonable limit
    assert memory_usage < 50 * 1024 * 1024  # Less than 50 MB

