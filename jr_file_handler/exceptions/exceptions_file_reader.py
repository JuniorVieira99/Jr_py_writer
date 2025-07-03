class FileReaderException(Exception):
    """Base exception for file reader errors."""

    pass


class FileReaderConstructionError(FileReaderException):
    """Raised when there is an error during the construction of the file reader."""

    pass


class FileReaderSettingsError(FileReaderException):
    """Raised when there is an error with the settings of the file reader."""

    pass


class FileReaderSyncPoolInitError(FileReaderException):
    """Raised when there is an error initializing the file reader pool."""

    pass


class FileReaderSyncPoolCleanupError(FileReaderException):
    """Raised when there is an error cleaning up the file reader pool."""

    pass


class FileReaderAsyncPoolInitError(FileReaderException):
    """Raised when there is an error initializing the asynchronous file reader pool."""

    pass


class FileReaderAsyncPoolCleanupError(FileReaderException):
    """Raised when there is an error cleaning up the asynchronous file reader pool."""

    pass


class FileReaderReadError(FileReaderException):
    """Raised when there is an error reading to the file reader."""

    pass


class FileReaderAsyncReadError(FileReaderException):
    """Raised when there is an error reading asynchronously to the file reader."""

    pass


class FileReaderConfigError(FileReaderException):
    """Raised when there is an error with the file reader configuration."""

    pass


class FileReaderShutdownError(FileReaderException):
    """Raised when there is an error shutting down the file reader."""

    pass


class FileReaderResumeError(FileReaderException):
    """Raised when there is an error resuming the file reader."""

    pass


class FileReaderResetError(FileReaderException):
    """Raised when there is an error resetting the file reader."""

    pass
