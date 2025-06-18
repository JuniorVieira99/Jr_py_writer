# jr_py_writer API Documentation

This documentation provides an overview of the `jr_py_writer` library, including its features, usage examples, and class details.

## Index

- [File Handler Overview](#file-handler-overview)
  - [Attributes](#attributes)
  - [Constructor](#constructor)
  - [Default Values](#default-values)
  - [file_paths](#file_paths)
  - [retry_limit](#retry_limit)
  - [retry_delay](#retry_delay)
  - [backoff_factor](#backoff_factor)
  - [max_rotation](#max_rotation)
  - [max_file_size](#max_file_size)
  - [write_mode](#write_mode)
  - [max_buffer_size](#max_buffer_size)
  - [use_write_flush](#use_write_flush)
  - [logger](#logger)
- [Methods Overview](#methods-overview)
  - [Magic Methods](#magic-methods)
  - [Private Methods](#private-methods)
  - [Public Methods](#public-methods)
- [Signature and Description of Public Methods](#signature-and-description-of-public-methods)
  - [log](#log)
  - [async_log](#async_log)
  - [buffer_force_flush](#buffer_force_flush)
  - [writer_force_flush](#writer_force_flush)
  - [clear_all](#clear_all)
  - [force_shutdown](#force_shutdown)
  - [resume_pool](#resume_pool)
  - [reset](#reset)
  - [config](#config)
  - [config_dict](#config_dict)
  - [config_json](#config_json)
  - [config_yaml](#config_yaml)

## File Handler Overview

The `jr_py_writer` library provides a `FileHandler` class that allows for efficient file writing with features such as buffering, file rotation, and retry mechanisms. It supports both synchronous and asynchronous operations.

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

### Default Values

| Attribute         | Default Value          |
|-------------------|------------------------|
| `write_mode`      | `LogWriteMode.APPEND`  |
| `retry_limit`     | `2`                    |
| `retry_delay`     | `0.1`                  |
| `backoff_factor`  | `0.2`                  |
| `max_file_size`   | `10 * 1024 * 1024`     |
| `max_rotation`    | `5`                    |
| `max_buffer_size` | `1024 * 1024`          |
| `use_write_flush` | `True`                 |

### file_paths

The `file_paths` attribute is a list of file paths where log messages will be written. It can accept both `Path` objects and strings representing file paths. Strings will be converted to `Path` objects internally.

- **Type**: `List[Path | str]`
- **Description**: This attribute holds the paths to the files where log messages will be written. It can contain multiple paths, allowing for logging to multiple files simultaneously.
- **Example**:

  ```python
  file_paths: List[Path] = [Path("log1.txt"), Path("log2.txt")]
  ```

### retry_limit

The `retry_limit` attribute specifies the maximum number of times the file handler will attempt to retry a failed file operation before giving up. This is useful for handling transient errors, such as temporary file access issues.

- **Type**: `int`
- **Description**: The number of retry attempts for failed file operations. If a file operation fails, the handler will wait for a specified delay and then retry the operation up to this limit.
- **Note**: If set to `0`, no retries will be attempted, and the operation will fail immediately on the first error.
- **Default Value**: `2`
- **Example**:

  ```python
  retry_limit: int = 3  # Retry up to 3 times
  ```

### retry_delay

The `retry_delay` attribute defines the initial delay in seconds before retrying a failed file operation. This delay can help mitigate issues caused by temporary file access problems.

- **Type**: `float`
- **Description**: The delay in seconds before the first retry attempt after a failed file operation. This delay can be adjusted to suit the application's needs.
- **Note**: If the `retry_delay` is set to `0`, the handler will not wait before retrying.
- **Default Value**: `0.1`
- **Example**:

  ```python
  retry_delay: float = 0.2  # Wait for 0.2 seconds before retrying
  ```

### backoff_factor

The `backoff_factor` attribute is used to increase the retry delay exponentially after each failed attempt. This helps to avoid overwhelming the system with retries in case of persistent issues.

- **Type**: `float`
- **Description**: The factor by which the retry delay is multiplied after each failed attempt. For example, if the initial delay is `0.1` seconds and the backoff factor is `0.2`, the delays for subsequent retries will be `0.1`, `0.12`, `0.14`, etc.
- **Note**: If set to `0`, the retry delay will not increase after each attempt, and the delay will remain constant.
- **Default Value**: `0.2`

- **Example**:

  ```python
  backoff_factor: float = 0.3  # Increase delay by 0.3 seconds after each retry
  ```

### max_rotation

The `max_rotation` attribute specifies the maximum number of rotated log files to keep. When the number of rotated files exceeds this limit, the oldest files will be deleted to make room for new ones.

- **Type**: `int`
- **Description**: This attribute controls how many rotated log files are retained. If the limit is reached, the oldest files will be removed to ensure that the total number of log files does not exceed this limit.
- **Note**: If set to `0`, no rotation will occur, and all log files will be kept indefinitely.
- **Default Value**: `5`
- **Example**:

  ```python
  max_rotation: int = 10  # Keep a maximum of 10 rotated log files
  ```

### max_file_size

The `max_file_size` attribute specifies the maximum size of a log file in bytes before it is rotated. When the file exceeds this size, it will be renamed and a new file will be created for further logging.

- **Type**: `int`
- **Description**: This attribute defines the maximum size of a log file. When the file size exceeds this limit, the file will be rotated, meaning it will be renamed and a new file will be created for further logging.
- **Note**: If set to `0`, file size checks will be disabled, and files will not be rotated based on size.
- **Default Value**: `10 * 1024 * 1024` (10 MB)
- **Example**:

    ```python
    max_file_size: int = 5 * 1024 * 1024  # Set maximum file size to 5 MB
    ```

### write_mode

The `write_mode` attribute determines how log messages are written to the files. It can be set to either append or overwrite mode.
The enum is strEnum, so it can be set to either a string or the enum itself.

- **Append Mode (`LogWriteMode.APPEND` | `a`)**: Log messages are added to the end of the file. If the file does not exist, it will be created.
- **Overwrite Mode (`LogWriteMode.OVERWRITE` | `w`)**: The file is truncated to
    zero length before writing new log messages. This means that previous log messages will be lost.
- **Read Mode (`LogWriteMode.READ` | `r`)**: The file is opened for reading. This mode is not typically used for logging but can be useful for reading existing log files.
- **Read and Write Mode (`LogWriteMode.READ_WRITE` | `r+`)**: The file is opened for both reading and writing. This allows you to read existing log messages while also appending new ones.

- **Default Value**: `LogWriteMode.APPEND`
- **Example**:

  ```python
  write_mode: LogWriteMode = LogWriteMode.OVERWRITE  # Use overwrite mode for logging
  ```

### max_buffer_size

The `max_buffer_size` attribute is used to define the maximum size of the buffer that holds log messages before they are automatically written to the file. This helps in optimizing performance by reducing the number of write operations, especially when logging high-frequency messages.

- When the buffer size exceeds the maximum, it will automatically flush the buffer
- If the value is set to `0`, the handler will not use a buffer, and every log message will be written immediately to the file. This will impact performance negatively, but ensures that no data is lost in case of unexpected shutdowns or crashes.
- To manually flush the buffer, you can use the `buffer_force_flush()` method.
- If size is not reached, the buffer will be flushed when the context manager exits or when `buffer_force_flush()` is called.
- **ALWAYS FLUSH THE BUFFER IF NOT USING CONTEXT MANAGER, OTHERWISE DATA MAY BE LOST!**

- **Type**: `int`
- **Description**: The maximum size of the buffer in bytes. When the buffer reaches this size, it will automatically flush the contents to the file.
- **Default Value**: `1024 * 1024` (1 MB)
- **Example**:

  ```python
  max_buffer_size: int = 512 * 1024  # Set maximum buffer size to 512 KB
  ```

### use_write_flush

The `use_write_flush` attribute determines whether the file should be flushed after each write operation. This can be useful for ensuring that log messages are immediately written to disk, especially in critical applications where data loss is unacceptable.

- Can be set to `True` or `False`.
- If set to `True`, the file will be flushed after each write operation, ensuring that all data is written to disk immediately.
- If set to `False`, the file will not be flushed after each write, which can improve performance but may risk losing data in case of a crash or unexpected shutdown.
- To manually flush all files use `writer_force_flush()` method.

- **Type**: `bool`
- **Description**: Whether to flush the file after each write operation.
- **Default Value**: `True`
- **Example**:

  ```python
  use_write_flush: bool = False  # Do not flush after each write operation
  ```

### logger

The `logger` attribute is an instance of Python's built-in `logging.Logger` class. It is used to log messages related to the file handler's operations, such as errors, warnings, and informational messages.

- If not provided, a default logger will be created.
- It is recommended to pass a logger instance to capture logs in your application.

- **Type**: `logging.Logger | None`
- **Description**: The logger instance used for logging messages related to file operations. If not provided, a default logger will be created.
- **Example**:

    ```python
    import logging
    
    logger = logging.getLogger("my_file_handler")
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler("file_handler.log")
    logger.addHandler(file_handler)
    
    # Pass the logger to the FileHandler
    file_paths: List[Path] = [Path("log.txt")]
    handler = FileHandler(file_paths, logger=logger)
    ```

---

## Methods Overview

### Magic Methods

The `jr_py_writer` library includes several magic methods that enhance the functionality of the `FileHandler` class. These methods allow for better integration with Python's built-in features, such as context management and string representation.

| Method Name          | Description                                                                 |
|----------------------|-----------------------------------------------------------------------------|
| `__enter__`          | Initializes the file handler and prepares it for use in a context manager.  |
| `__exit__`           | Cleans up resources and closes files when exiting the context manager.     |
| `__aenter__`         | Asynchronously initializes the file handler for use in an async context manager. |
| `__aexit__`          | Asynchronously cleans up resources and closes files when exiting the async context manager. |
| `__str__`            | Returns a string representation of the file handler, including its configuration. |
| `__iter__`          | Allows iteration over the file paths managed by the file handler.         |
| `__len__`            | Returns the number of file paths managed by the file handler.             |
| `__contains__`       | Checks if a specific file path is managed by the file handler.            |
| `__eq__`            | Compares two file handlers for equality based on their configuration.     |
| `__ne__`            | Compares two file handlers for inequality based on their configuration.  |
| `__del__`           | Deletes the file handler and cleans up resources.                          |

### Private Methods

The `jr_py_writer` library includes several private methods that are used internally by the `FileHandler` class. These methods are not intended for direct use by users of the library, but they play a crucial role in the functionality of the file handler.

| Method Name          | Description                                                                 |
|----------------------|-----------------------------------------------------------------------------|
| `_ensure_sync_pool`  | Lazy initialization of the temporary sync pool for file operations.         |
| `_init_sync_pool`    | Initializes the temporary pool for synchronous file operations.             |
| `clear_sync_pool`    | Clears the temporary pool and closes all files in it.                      |
| `_check_file_size`   | Checks if the file size exceeds the maximum allowed size.                  |
| `_rotate_file`       | Rotates the log file if it exceeds the maximum size.                       |
| `_ensure_parent_dirs`| Ensures parent directories exist for the given path.                       |
| `_create_file`       | Creates a new file at the specified path if it does not exist.             |
| `_get_buffer_message`| Retrieves and clears the buffer content for writing.                       |
| `_write_to_buffer`   | Writes the log message to the buffer and checks for size limits.           |
| `_write_to_file`     | Writes the log message to a single file with retry logic.                  |
| `_writer`            | Writes the log message to all specified file paths using threading.        |
| `_log_batch`         | Writes log messages to a batch of file paths for optimized performance.    |
| `_async_log_batch`   | Asynchronously writes log messages to a batch of file paths.               |
| `_writer_handler`    | Handles writing log messages to file paths in batches.                     |
| `_async_writer`      | Asynchronously writes log messages to all specified file paths.            |
| `_async_writer_handler` | Handles asynchronous writing of log messages in batches.                |

### Public Methods

The `jr_py_writer` library provides several public methods in the `FileHandler` class that allow users to interact with the file handler for logging purposes. These methods are designed to be user-friendly and provide various functionalities for writing logs, managing buffers, and configuring the file handler.

| Method Name          | Description                                                                 |
|----------------------|-----------------------------------------------------------------------------|
| `log`                | Writes a log message to the specified file paths synchronously.            |
| `async_log`          | Asynchronously writes a log message to the specified file paths.           |
| `buffer_force_flush` | Forces the buffer to flush its content to the file(s).                     |
| `writer_force_flush` | Forces all file writers to flush their content to disk.                    |
| `clear_all`          | Clears all resources used by the FileHandler.                              |
| `force_shutdown`     | Forces shutdown of the thread pool executor.                               |
| `resume_pool`        | Resumes the thread pool executor after shutdown.                           |
| `reset`              | Resets the FileHandler to its default configuration.                       |
| `config`             | Configures the FileHandler with new settings.                              |
| `config_dict`        | Configures the FileHandler using a dictionary.                             |
| `config_json`        | Configures the FileHandler using a JSON string or dictionary.              |
| `config_yaml`        | Configures the FileHandler using a YAML string or dictionary.              |

---

## Signature and Description of Public Methods

### log

The `log` method is used to write a log message to the specified file paths synchronously. It handles buffering, file rotation, and retry logic.

**Signature:**

```python
def log(self, message: str) ->
    None:
```

**Parameters:**

- `message` (`str`): The log message to be written to the file(s).

**Returns:**

- `None`: This method does not return any value.

**Example:**

```python
my_handler.log("This is a log message.")
```

---

### async_log

The `async_log` method is used to asynchronously write a log message to the specified file paths. It handles buffering, file rotation, and retry logic.

**Signature:**

```python
async def async_log(self, message: str) -> None:
```

**Parameters:**

- `message` (`str`): The log message to be written to the file(s).

**Returns:**

- `None`: This method does not return any value.

**Example:**

```python
await my_handler.async_log("This is an asynchronous log message.")
```

---

### buffer_force_flush

The `buffer_force_flush` method forces the buffer to flush its content to the file(s). This ensures that all buffered log messages are written to disk.

**Signature:**

```python
def buffer_force_flush(self) -> None:
```

**Parameters:**

- None.

**Returns:**

- `None`: This method does not return any value.

**Example:**

```python
my_handler.buffer_force_flush()
```

---

### writer_force_flush

The `writer_force_flush` method forces all file writers to flush their content to disk. This ensures that all pending writes are completed.

**Signature:**

```python
def writer_force_flush(self) -> None:
```

**Parameters:**

- None.

**Returns:**

- `None`: This method does not return any value.

**Example:**

```python
my_handler.writer_force_flush()
```

---

### clear_all

The `clear_all` method clears all resources used by the `FileHandler`. This includes flushing buffers, clearing the sync pool, and shutting down the thread pool.

**Signature:**

```python
def clear_all(self) -> None:
```

**Parameters:**

- None.

**Returns:**

- `None`: This method does not return any value.

**Example:**

```python
my_handler.clear_all()
```

---

### force_shutdown

The `force_shutdown` method forces the shutdown of the thread pool executor. This is useful for cleaning up resources when the `FileHandler` is no longer needed.

**Signature:**

```python
def force_shutdown(self, wait: bool = True) -> None:
```

**Parameters:**

- `wait` (`bool`): Whether to wait for all tasks to complete before shutting down. Default is `True`.

**Returns:**

- `None`: This method does not return any value.

**Example:**

```python
my_handler.force_shutdown(wait=True)
```

---

### resume_pool

The `resume_pool` method resumes the thread pool executor after it has been shut down. This is useful for reinitializing the thread pool.

**Signature:**

```python
def resume_pool(self) -> None:
```

**Parameters:**

- None.

**Returns:**

- `None`: This method does not return any value.

**Example:**

```python
my_handler.resume_pool()
```

---

### reset

The `reset` method resets the `FileHandler` to its default configuration. This includes resetting all attributes to their default values.

**Signature:**

```python
def reset(self, file_paths: List[Union[Path, str]]) -> None:
```

**Parameters:**

- `file_paths` (`List[Union[Path, str]]`): A list of file paths for logging.

**Returns:**

- `None`: This method does not return any value.

**Example:**

```python
my_handler.reset(file_paths=[Path("log1.txt"), Path("log2.txt")])
```

---

### config

The `config` method configures the `FileHandler` with new settings. This includes updating attributes such as `file_paths`, `write_mode`, and `retry_limit`.

**Signature:**

```python
def config(
    self,
    file_paths: List[Union[Path, str]],
    write_mode: LogWriteMode = LogWriteMode.APPEND,
    retry_limit: int = 3,
    retry_delay: float = 0.5,
    backoff_factor: float = 0.2,
    max_file_size: int = 10 * 1024 * 1024,
    max_rotation: int = 5,
    max_buffer_size: int = 1024 * 1024,
    use_write_flush: bool = True,
    logger: logging.Logger | None = None
) -> None:
```

**Parameters:**

- `file_paths` (`List[Union[Path, str]]`): A list of file paths for logging.
- `write_mode` (`LogWriteMode`): Write mode for file logging. Default is `LogWriteMode.APPEND`.
- `retry_limit` (`int`): Number of retries for file operations. Default is `3`.
- `retry_delay` (`float`): Delay in seconds between retries. Default is `0.5`.
- `backoff_factor` (`float`): Backoff factor for retry delays. Default is `0.2`.
- `max_file_size` (`int`): Maximum file size in bytes. Default is `10 MB`.
- `max_rotation` (`int`): Maximum number of rotated log files. Default is `5`.
- `max_buffer_size` (`int`): Maximum buffer size in bytes. Default is `1 MB`.
- `use_write_flush` (`bool`): Whether to flush the file after each write. Default is `True`.
- `logger` (`logging.Logger | None`): An optional logger instance to use for logging.

**Returns:**

- `None`: This method does not return any value.

**Example:**

```python
my_handler.config(
    file_paths=[Path("log1.txt"), Path("log2.txt")],
    write_mode=LogWriteMode.OVERWRITE,
    retry_limit=5,
    retry_delay=0.2
)
```

---

### config_dict

The `config_dict` method configures the `FileHandler` using a dictionary of settings.

**Signature:**

```python
def config_dict(self, config_dict: Dict[str, Any]) -> None:
```

**Parameters:**

- `config_dict` (`Dict[str, Any]`): A dictionary containing configuration options.

**Returns:**

- `None`: This method does not return any value.

**Example:**

```python
config = {
    "file_paths": [Path("log1.txt"), Path("log2.txt")],
    "write_mode": LogWriteMode.APPEND,
    "retry_limit": 3
}
my_handler.config_dict(config)
```

---

### config_json

The `config_json` method configures the `FileHandler` using a JSON string or dictionary.

**Signature:**

```python
def config_json(self, config_json: str | bytes) -> None:
```

**Parameters:**

- `config_json` (`str | bytes`): A JSON string or dictionary containing configuration options.

**Returns:**

- `None`: This method does not return any value.

**Example:**

```python
json_config = '{"file_paths": ["log1.txt", "log2.txt"], "write_mode": "APPEND"}'
my_handler.config_json(json_config)
```

---

### config_yaml

The `config_yaml` method configures the `FileHandler` using a YAML string or dictionary.

**Signature:**

```python
def config_yaml(self, config_yaml: str | bytes) -> None:
```

**Parameters:**

- `config_yaml` (`str | bytes`): A YAML string or dictionary containing configuration options.

**Returns:**

- `None`: This method does not return any value.

**Example:**

```python
yaml_config = """
file_paths:
  - log1.txt
  - log2.txt
write_mode: APPEND
"""
my_handler.config_yaml(yaml_config)
```
