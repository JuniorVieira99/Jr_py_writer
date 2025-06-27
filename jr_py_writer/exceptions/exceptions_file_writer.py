class FileWriterException(Exception):
    """Base exception for file writer errors."""

    pass


class FileWriterConstructionError(FileWriterException):
    """Raised when there is an error during the construction of the file writer."""

    pass


class FileWriterSettingsError(FileWriterException):
    """Raised when there is an error with the settings of the file writer."""

    pass


class FileWriterSyncPoolInitError(FileWriterException):
    """Raised when there is an error initializing the file writer pool."""

    pass


class FileWriterSyncPoolCleanupError(FileWriterException):
    """Raised when there is an error cleaning up the file writer pool."""

    pass


class FileWriterAsyncPoolInitError(FileWriterException):
    """Raised when there is an error initializing the asynchronous file writer pool."""

    pass


class FileWriterAsyncPoolCleanupError(FileWriterException):
    """Raised when there is an error cleaning up the asynchronous file writer pool."""

    pass


class FileWriterWriteError(FileWriterException):
    """Raised when there is an error writing to the file writer."""

    pass


class FileWriterAsyncWriteError(FileWriterException):
    """Raised when there is an error writing asynchronously to the file writer."""

    pass


class FileWriterRotateError(FileWriterException):
    """Raised when there is an error rotating the file writer."""

    pass


class FileWriterConfigError(FileWriterException):
    """Raised when there is an error with the file writer configuration."""

    pass


class FileWriterBufferError(FileWriterException):
    """Raised when there is an error with the file writer buffer."""

    pass


class FileWriterFlushError(FileWriterException):
    """Raised when there is an error flushing the file writer."""

    pass


class FileWriterShutdownError(FileWriterException):
    """Raised when there is an error shutting down the file writer."""

    pass


class FileWriterResumeError(FileWriterException):
    """Raised when there is an error resuming the file writer."""

    pass


class FileWriterResetError(FileWriterException):
    """Raised when there is an error resetting the file writer."""

    pass
