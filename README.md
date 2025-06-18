# jr_py_writer

`jr_py_writer` is a Python library designed for efficient and configurable file handling and logging. It supports both synchronous and asynchronous operations, file rotation, buffering, and retry mechanisms for robust file operations.

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![PyPI](https://img.shields.io/pypi/v/jr-py-writer)
![Tests](https://img.shields.io/github/workflow/status/jr-py-writer/tests/main?label=tests)
![Code Coverage](https://img.shields.io/codecov/c/github/jr-py-writer/main?label=coverage)
![Black](https://img.shields.io/badge/code%20style-black-000000.svg)

---

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Requirements](#requirements)
4. [Usage](#usage)
    - [Basic Example](#basic-example)
    - [Asynchronous Example](#asynchronous-example)
    - [File Rotation Example](#file-rotation-example)
    - [Context Manager Example](#context-manager-example)
5. [File Handler Class](#file-handler-class)
    - [Attributes](#attributes)
    - [Constructor](#constructor)
    - [write_mode](#write_mode)
    - [max_buffer_size](#max_buffer_size)
    - [use_write_flush](#use_write_flush)
    - [logger](#logger)
6. [Configuration Options](#configuration-options)
    - [Dictionary Configuration](#dictionary-configuration)
    - [JSON Configuration](#json-configuration)
    - [YAML Configuration](#yaml-configuration)
7. [Testing](#testing)
8. [Documentation](#documentation)
9. [License](#license)
10. [Contributing](#contributing)

## Features

- **Synchronous and Asynchronous Logging** ⚡: Write log messages to multiple files with support for async operations.
- **Performance Optimization** 🚀: Can write to 2000 multiple files with minimal performance impact. Check docs for benchmarks.
- **File Rotation** 🔄: Automatically rotate log files when they exceed a specified size.
- **Buffering** 📦: Configurable buffer size for improved performance.
- **Retry Mechanisms** 🔁: Handle temporary file system access issues with retry logic.
- **Thread-Safe Operations** 🔒: Ensure safe concurrent writes to files.
- **Context Manager Support** 🎯: Automatically manage resources using Python's context managers.
- **Customizable Configuration** ⚙️: Configure file paths, write modes, retry limits, buffer sizes, and more.
- **Memory Management** 💾: Efficient memory usage with garbage collection support.
- **Flexible Configuration** 🔧: Load configurations from dictionaries, JSON, or YAML files.
- **Extensive Testing** ✅: Includes unit tests and performance benchmarks to ensure reliability and efficiency.

---

## Installation

```bash
pip install jr_py_writer
```

## Requirements

```plaintext
- Python 3.12 or higher
- PYAML
- pytest (for testing)
```

---

## Usage

### Basic Example

```python
from pathlib import Path
from jr_py_writer import FileHandler
from jr_py_writer import LogWriteMode

# Create a FileHandler instance
handler = FileHandler(
    file_paths=[Path("app.log"), Path("debug.log")],
    write_mode=LogWriteMode.APPEND,
    retry_limit=3,
    retry_delay=0.5
)

# Write log messages
handler.log("This is a test log message.")

# Force flush the buffer
handler.buffer_force_flush()

# Cleanup resources
handler.clear_all()
```

## Asynchronous Example

```python
import asyncio
from pathlib import Path
from jr_py_writer import FileHandler

async def main():
    handler = FileHandler(
        file_paths=[Path("async_app.log")],
        write_mode="a",
        retry_limit=3,
        retry_delay=0.5
    )
    await handler.async_log("This is an async log message.")
    handler.buffer_force_flush()
    handler.clear_all()

asyncio.run(main())
```

## File Rotation Example

```python
from pathlib import Path
from jr_py_writer import FileHandler

handler = FileHandler(
    file_paths=[Path("rotating.log")],
    max_file_size=1024,  # 1 KB
    max_rotation=3
)

for i in range(100):
    handler.log(f"Log message {i}")

handler.buffer_force_flush()
handler.clear_all()
```

## Context Manager Example

```python
from pathlib import Path
from jr_py_writer import FileHandler

# Directly using the FileHandler within a context manager
with FileHandler(
    file_paths=[Path("context.log")],
    write_mode="a",
    retry_limit=3,
    retry_delay=0.5
) as handler:
    handler.log("This log message is written within a context manager.")
    handler.buffer_force_flush()

# Or, creating a new handler and then using it with a context manager
handler = FileHandler(
    file_paths=[Path("outside_context.log")],
    write_mode="a",
    retry_limit=3,
    retry_delay=0.5
)

with handler:
    handler.log("This log message is written outside the context manager.")
    handler.buffer_force_flush()

# The context manager automatically handles resource cleanup.
```

---

## File Handler Class

The `FileHandler` class provides a robust interface for managing file operations, including logging, file rotation, and asynchronous writes. It supports multiple file paths and can be configured to handle various write modes and retry strategies.

### Attributes

Here is the markdown table based on the provided information:

| Attribute         | Type               | Description                                                                 |
|-------------------|--------------------|-----------------------------------------------------------------------------|
| `file_paths`      | `List[Path]`       | List of file paths where log messages will be written.                      |
| `write_mode`      | `LogWriteMode`     | Mode for writing to files (append or overwrite).                            |
| `retry_limit`     | `int`              | Number of times to retry failed file operations.                            |
| `retry_delay`     | `float`            | Delay in seconds between retry attempts.                                    |
| `backoff_factor`  | `float`            | Factor to increase the retry delay exponentially.                           |
| `max_file_size`   | `int`              | Maximum size of log files in bytes before rotation.                         |
| `max_rotation`    | `int`              | Maximum number of rotated log files to keep.                                |
| `max_buffer_size` | `int`              | Maximum size of the buffer for log messages.                                |
| `use_write_flush` | `bool`             | Whether to flush the file after each write operation.                       |
| `logger`          | `logging.Logger`   | Logger instance for logging errors and information.                         |

### Constructor

```python
def __init__(
    self, 
    file_paths: List[Union[Path, str]], 
    write_mode: LogWriteMode = LogWriteMode.APPEND,
    retry_limit: int = 2,
    retry_delay: float = 0.1,
    backoff_factor: float = 0.2,
    max_file_size: int = 10 * 1024 * 1024,  # Default 10 MB
    max_rotation: int = 5,  # Default max number of rotated files
    max_buffer_size:int = 1024 * 1024,  # Default 1 MB buffer size
    use_write_flush: bool = True, # Whether to use flush after write
    logger: logging.Logger | None = None
) -> None:
```

### write_mode

The `write_mode` attribute determines how log messages are written to the files. It can be set to either append or overwrite mode.
The enum is strEnum, so it can be set to either a string or the enum itself.

- **Append Mode (`LogWriteMode.APPEND` | `a`)**: Log messages are added to the end of the file. If the file does not exist, it will be created.
- **Overwrite Mode (`LogWriteMode.OVERWRITE` | `w`)**: The file is truncated to
    zero length before writing new log messages. This means that previous log messages will be lost.
- **Read Mode (`LogWriteMode.READ` | `r`)**: The file is opened for reading. This mode is not typically used for logging but can be useful for reading existing log files.
- **Read and Write Mode (`LogWriteMode.READ_WRITE` | `r+`)**: The file is opened for both reading and writing. This allows you to read existing log messages while also appending new ones.

### max_buffer_size

The `max_buffer_size` attribute is used to define the maximum size of the buffer that holds log messages before they are automatically written to the file. This helps in optimizing performance by reducing the number of write operations, especially when logging high-frequency messages.

- When the buffer size exceeds the maximum, it will automatically flush the buffer
- If the value is set to `0`, the handler will not use a buffer, and every log message will be written immediately to the file. This will impact performance negatively, but ensures that no data is lost in case of unexpected shutdowns or crashes.
- To manually flush the buffer, you can use the `buffer_force_flush()` method.
- If size is not reached, the buffer will be flushed when the context manager exits or when `buffer_force_flush()` is called.
- **ALWAYS FLUSH THE BUFFER IF NOT USING CONTEXT MANAGER, OTHERWISE DATA MAY BE LOST!**

### use_write_flush

The `use_write_flush` attribute determines whether the file should be flushed after each write operation. This can be useful for ensuring that log messages are immediately written to disk, especially in critical applications where data loss is unacceptable.

- Can be set to `True` or `False`.
- If set to `True`, the file will be flushed after each write operation, ensuring that all data is written to disk immediately.
- If set to `False`, the file will not be flushed after each write, which can improve performance but may risk losing data in case of a crash or unexpected shutdown.
- To manually flush all files use `writer_force_flush()` method.

### logger

The `logger` attribute is an instance of Python's built-in `logging.Logger` class. It is used to log messages related to the file handler's operations, such as errors, warnings, and informational messages.

- If not provided, a default logger will be created.

---

## Configuration Options

You can configure the FileHandler using dictionaries, JSON, or YAML files.

### Dictionary Configuration

```python
config = {
    "file_paths": ["config_test.log"],
    "write_mode": "a",
    "retry_limit": 3,
    "retry_delay": 0.5,
    "max_file_size": 5 * 1024 * 1024,  # 5 MB
    "max_rotation": 2
}

handler.config_dict(config)
```

### JSON Configuration

```python
import json

config_json = json.dumps({
    "file_paths": ["config_test.log"],
    "write_mode": "a",
    "retry_limit": 3,
    "retry_delay": 0.5,
    "max_file_size": 5 * 1024 * 1024,  # 5 MB
    "max_rotation": 2
})

handler.config_json(config_json)
```

### YAML Configuration

```python
import yaml

config_yaml = """
file_paths:
  - config_test.log
write_mode: a
retry_limit: 3
retry_delay: 0.5
max_file_size: 5242880  # 5 MB
max_rotation: 2
"""

handler.config_yaml(config_yaml)
```
---

## Testing

The library includes comprehensive unit tests and benchmarks. To run the tests, use:

- For all tests:

```bash
pytest test/
```

- For overall functionality:

```bash
pytest test/test_overall.py
```

- For sync performance tests:

```bash
pytest test/test_sync_performance.py
```

- For async performance tests:

```bash
pytest test/test_async_performance.py
```

Also, check the workflow files in the `.github/workflows` directory for CI/CD configurations.

---

## Documentation

For detailed documentation, please refer to the [docs](docs/) directory. It includes examples, API references, and configuration guides.

- Api reference: [API Reference](docs/api_reference.md)
- Examples: [Examples](docs/examples.md)
- Performance benchmarks: [Performance Benchmarks](docs/performance.md)

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions are welcome! Please submit issues or pull requests to improve the library.
