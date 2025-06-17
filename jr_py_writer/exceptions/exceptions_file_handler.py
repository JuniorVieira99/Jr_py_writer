class FileHandlerException(Exception):
    """Base exception for file handler errors."""
    pass

class FileHandlerConstructionError(FileHandlerException):
    """Raised when there is an error during the construction of the file handler."""
    pass

class FileHandlerSettingsError(FileHandlerException):
    """Raised when there is an error with the settings of the file handler."""
    pass

class FileHandlerSyncPoolInitError(FileHandlerException):
    """Raised when there is an error initializing the file handler pool."""
    pass

class FileHandlerSyncPoolCleanupError(FileHandlerException):
    """Raised when there is an error cleaning up the file handler pool."""
    pass

class FileHandlerAsyncPoolInitError(FileHandlerException):
    """Raised when there is an error initializing the asynchronous file handler pool."""
    pass

class FileHandlerAsyncPoolCleanupError(FileHandlerException):
    """Raised when there is an error cleaning up the asynchronous file handler pool."""
    pass

class FileHandlerWriteError(FileHandlerException):
    """Raised when there is an error writing to the file handler."""
    pass

class FileHandlerAsyncWriteError(FileHandlerException):
    """Raised when there is an error writing asynchronously to the file handler."""
    pass

class FileHandleRotateError(FileHandlerException):
    """Raised when there is an error rotating the file handler."""
    pass

class FileHandlerConfigError(FileHandlerException):
    """Raised when there is an error with the file handler configuration."""
    pass

class FileHandlerBufferError(FileHandlerException):
    """Raised when there is an error with the file handler buffer."""
    pass

class FileHandlerFlushError(FileHandlerException):
    """Raised when there is an error flushing the file handler."""
    pass

class FileHandlerShutdownError(FileHandlerException):
    """Raised when there is an error shutting down the file handler."""
    pass

class FileHandlerResumeError(FileHandlerException):
    """Raised when there is an error resuming the file handler."""
    pass

class FileHandlerResetError(FileHandlerException):
    """Raised when there is an error resetting the file handler."""
    pass