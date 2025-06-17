# ---------------------------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------------------------


# Standard library imports
import sys
import logging
import asyncio
import time
import gc
import os

from functools import wraps
from itertools import islice
from typing import Callable, Generator, Iterable, Set, List, Any, Optional, Tuple, Union
from threading import Thread
from contextlib import contextmanager

# Third-party imports
import psutil

# ---------------------------------------------------------------------------------------------
# Classes Definitions
# ---------------------------------------------------------------------------------------------

class GCManager:
    """
    GCManager
    ==========
    A class to manage garbage collection and memory monitoring in Python.
    - It provides functionality to enable or disable garbage collection,
    - Monitors memory usage in a separate thread.
    - Supports Sync and Async Context Manager protocol.

    Attributes:
        monitoring (bool): Whether the garbage collection manager is monitoring memory usage.
        wait_time (float): The wait time for the garbage collection manager.
        thread (Optional[Thread]): The thread associated with the garbage collection manager.
        memory_threshold (float): The memory threshold for garbage collection, between 0.0 and 1.0.

    Example:
    ```python
    # Using the GCManager as a synchronous context manager
    with GCManager(wait_time=0.1, memory_threshold=0.80) as gc_manager:
        # Your code here
        pass

    # Or for asynchronous context manager
    async with GCManager(wait_time=0.1, memory_threshold=0.80) as gc_manager:
        # Your async code here
        pass
    ```
    """

    # ------------
    # Slots

    __slots__ = ('_monitoring','_wait_time', '_sync_thread', '_async_thread' ,'_memory_threshold')

    # ------------
    # Attributes

    _monitoring: bool
    _sync_thread: Optional[Thread]
    _async_thread: Optional[asyncio.Task]
    _memory_threshold: float
    _wait_time: float

    # ------------
    # Properties

    @property
    def monitoring(self) -> bool:
        """Returns whether the garbage collection manager is monitoring memory usage."""
        return self._monitoring

    @property
    def wait_time(self) -> float:
        """Returns the wait time for the garbage collection manager."""
        return self._wait_time
    
    @property
    def sync_thread(self) -> Optional[Thread]:
        """Returns the thread associated with the garbage collection manager."""
        return self._sync_thread

    @property
    def async_thread(self) -> Optional[asyncio.Task]:
        """Returns the async task associated with the garbage collection manager."""
        return self._async_thread

    @property
    def memory_threshold(self) -> float:
        """Returns the memory threshold for garbage collection."""
        return self._memory_threshold

    # ------------
    # Setters

    @monitoring.setter
    def monitoring(self, value: bool):
        """Sets whether the garbage collection manager is monitoring memory usage."""
        if not isinstance(value, bool):
            raise ValueError("Monitoring must be a boolean value.")
        self._monitoring = value

    @wait_time.setter
    def wait_time(self, value: float):
        """Sets the wait time for the garbage collection manager."""
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("Wait time must be a non-negative integer or float.")
        self._wait_time = value

    @sync_thread.setter
    def sync_thread(self, value: Optional[Thread]):
        """Sets the thread for garbage collection manager."""
        if value is not None and not isinstance(value, Thread):
            raise TypeError("Thread must be an instance of Thread.")
        self._sync_thread = value

    @async_thread.setter
    def async_thread(self, value: Optional[asyncio.Task]):
        """Sets the async task for garbage collection manager."""
        if value is not None and not isinstance(value, asyncio.Task):
            raise TypeError("Async thread must be an instance of asyncio.Task.")
        self._async_thread = value

    @memory_threshold.setter
    def memory_threshold(self, value: float):
        """Sets the memory threshold for garbage collection."""
        if not isinstance(value, (int, float)):
            raise ValueError("Memory threshold must be a number.")
        if not (0.0 <= value <= 1.0):
            raise ValueError("Memory threshold must be between 0.0 and 1.0 (inclusive).")
        self._memory_threshold = float(value)

    # ------------
    # Constructor

    def __init__(
        self, 
        wait_time: float = 0.1,  # Default wait time of 100ms    
        memory_threshold: float = 0.80  # Default to 80% memory usage threshold
    ) -> None:
        
        self._monitoring = True
        self.wait_time = wait_time
        self.memory_threshold = memory_threshold
        self.sync_thread = None
        self.async_thread = None

    # ------------
    # Magic Methods

    def __str__(self):
        return f"GCManager(monitoring={self.monitoring}, wait_time={self.wait_time}, memory_threshold={self.memory_threshold})"
    
    
    def __enter__(self):
        """
        Enter the context manager, disabling garbage collection and starting memory monitoring.
        This method is called when entering the context manager using the `with` statement.
        """
        # Safe check
        mem = psutil.virtual_memory()
        if mem.percent > self.memory_threshold:
            gc.collect()

        # Disable garbage collection if it is enabled
        if gc.isenabled():
            gc.disable()

        # Start monitoring if it is enabled
        if self.monitoring:
            if self.sync_thread is None:
                # Create a new thread for memory observation
                self.sync_thread = Thread(target=self.memory_observer, daemon=True)
            # Check if the thread is alive and start it if not
            if self.sync_thread is not None and not self.sync_thread.is_alive():
                self.sync_thread.start()

        return self


    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the context manager, stopping memory monitoring and enabling garbage collection.
        This method is called when exiting the context manager using the `with` statement.
        """
        # Stop monitoring
        self.monitoring = False

        # Join the thread if it is running
        if self.sync_thread is not None and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=1.0)
            self.sync_thread = None

        # Enable garbage collection if it was disabled
        if not gc.isenabled():
            gc.enable()

        # Final garbage collection
        gc.collect()

        return False


    def __aenter__(self):
        """
        Enter the asynchronous context manager, disabling garbage collection and starting memory monitoring.
        This method is called when entering the context manager using the `async with` statement.
        """
        # Safe check
        mem = psutil.virtual_memory()
        if mem.percent > self.memory_threshold:
            gc.collect()        

        # Disable garbage collection if it is enabled
        if gc.isenabled():
            gc.disable()

        # Start monitoring if it is enabled
        if self.monitoring:
            if self.async_thread is None:
                # Create a new async task for memory observation
                self.async_thread = asyncio.create_task(self.async_memory_observer())
            # Check if the async task is running and start it if not
            if self.async_thread is not None and not self.async_thread.done():
                self.async_thread = asyncio.get_event_loop().create_task(self.async_memory_observer())
        # Return the context manager
        return self
    
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        """
        Exit the asynchronous context manager, stopping memory monitoring and enabling garbage collection.
        This method is called when exiting the context manager using the `async with` statement.
        """
        # Stop monitoring
        self.monitoring = False
        
        # Get the result of the async task
        result = self.async_thread.result() if self.async_thread is not None else None
        if result is not None:
            raise result
        
        # Cancel the async task if it is running
        if self.async_thread is not None and not self.async_thread.done():
            self.async_thread.cancel()

        # Enable garbage collection if it was disabled
        if not gc.isenabled():
            gc.enable()
        
        return False


    # ------------
    # Methods

    def memory_observer(self) -> None:
        """
        Monitors memory usage and prints it to the console.
        
        This method runs in a separate thread and continuously prints the current memory usage.
        """
        try:
            while self._monitoring:
                mem = psutil.virtual_memory()
                if mem.percent > self._memory_threshold * 100:
                    gc.collect()
                if not self._monitoring:
                    break
                time.sleep(self.wait_time)  # Sleep for a while to avoid busy waiting
        except Exception as e:
            raise RuntimeError(f"Error in memory observer thread: {e}") from e
        
        
    async def async_memory_observer(self) -> None:
        """
        Monitors asynchronously memory usage and prints it to the console.
        
        This method runs in a separate thread and continuously prints the current memory usage.
        """
        try:
            while self._monitoring:
                mem = psutil.virtual_memory()
                if mem.percent > self._memory_threshold * 100:
                    gc.collect()
                if not self._monitoring:
                    break
                await asyncio.sleep(self.wait_time)  # Sleep for a while to avoid busy waiting
        except Exception as e:
            raise RuntimeError(f"Error in memory observer thread: {e}") from e


    def force_gc(self) -> None:
        """
        Forces garbage collection.
        
        This method can be called to manually trigger garbage collection.
        """
        gc.collect()


# ---------------------------------------------------------------------------------------------
# Function Definitions
# ---------------------------------------------------------------------------------------------

def _calculate_batch_size(data: Union[List, Tuple, Set], batch_size: int) -> int:
    """
    _calculate_batch_size
    ======================
    Calculates an optimal batch size based on data length and available CPU cores.

    Arguments:
        data (Union[List, Tuple, Set]): The input data to be batched.
        batch_size (int): The initial batch size (if ≤ 0, uses CPU count).

    Returns:
        int: The calculated batch size.
    
    Notes:
        - For small datasets (< 1000), batch size is small but at least 1
        - For larger datasets, batch size scales proportionally to data length
        - The scaling is designed to balance memory usage and processing efficiency
    """
    data_len = len(data)
    
    # Use CPU count as default if batch_size is not positive
    if batch_size <= 0:
        batch_size = max(os.cpu_count() or 1, 1)
    
    # Return data length if batch size exceeds it
    if batch_size >= data_len:
        return data_len
    
    # Scaling factors based on data size
    if data_len < 1000:
        return max(batch_size, 1)
    
    scaling_table = [
        (10_000, 2, 4),      # (max_size, multiplier, divisor)
        (100_000, 4, 8),
        (1_000_000, 8, 16),
        (10_000_000, 16, 32),
    ]
    
    for max_size, multiplier, divisor in scaling_table:
        if data_len <= max_size:
            return max(batch_size * multiplier, data_len // divisor)
    
    # For very large datasets (> 10M elements)
    return max(batch_size * 32, data_len // 64)


def universal_wrapper(
    exception_class: type[Exception], 
    logger: Optional[logging.Logger] = None,
    use_sys_std: bool = False
) -> Callable:
    """
    A decorator to wrap a function and catch exceptions of a specific class.

    Arguments:
        exception_class (Exception) : The class of the exception to catch.
        logger (Optional[logging.Logger]) : An optional logger to log the error message.
        use_sys_std (bool) : If True, uses sys.stderr for logging instead of the provided logger.

    Returns:
        Callable: A decorator that wraps the function and catches exceptions.

    Example:
    ```python
    @universal_wrapper(ValueError, logger=logging.getLogger(__name__))
    def my_function():
        # Function implementation that may raise ValueError
        pass
    ```
    """
    def decorator(func):
        # Check if the function is a coroutine function
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if logger:
                        logger.error(
                            f"An error occurred in {func.__name__}: {e}", exc_info=True
                        )
                    elif use_sys_std:
                        print(
                            f"An error occurred in {func.__name__}\n"
                            f"Exception type: {e.__class__.__name__}\n"
                            f"Exception message: {e}",
                            file=sys.stderr
                        )
                    raise exception_class(f"An error {e.__class__.__name__} occurred in {func.__name__}:\n\t{e}") from e
            return async_wrapper
        # If the function is not a coroutine, use a regular wrapper
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if logger:
                        logger.error(
                            f"An error occurred in {func.__name__}: {e}", exc_info=True
                        )
                    elif use_sys_std:
                        print(
                            f"An error occurred in {func.__name__}\n"
                            f"Exception type: {e.__class__.__name__}\n"
                            f"Exception message: {e}",
                            file=sys.stderr
                        )
                    raise exception_class(f"An error {e.__class__.__name__} occurred in {func.__name__}:\n\t{e}") from e
            return wrapper
    return decorator


@contextmanager
def performance_monitor(operation: str):
    """
    A context manager to measure the performance of a block of code.

    Arguments:
        operation (str): The operation to measure the performance of.

    Returns:
        None
    """
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f"{operation}: {elapsed:.3f}s")


# ---------------------------------------------------------------------------------------------
# Synchronous Batcher
# ---------------------------------------------------------------------------------------------

def batcher_with_gcmanager(
    data: Iterable,
    batch_size: int = -1, # Default to -1 which will calculate batch size based on CPU cores
    max_memory_usage: float = 0.80,  # Default to 80% memory usage threshold
    wait_time: float = 0.1 # Default wait time of 100ms
) -> Generator[List[Any], None, None]:
    """
    batcher_with_gcmanager
    ============
    A generator function that batches input data into smaller lists while managing memory usage

    Arguments:
        data (Iterable): The input data to be batched.
        batch_size (int): The size of each batch.
            - Default is -1, which will calculate the batch size based on the number of CPU cores.
        max_memory_usage (float): The maximum memory usage threshold for garbage collection (default is 0.80).
        wait_time (float): The time to wait between memory checks (default is 0.1 seconds).

    Notes:
    -------
    - If `batch_size` is less than or equal to 0, it defaults to the number of CPU cores.
    - If `data` is not a list, a TypeError is raised.
    - If `batch_size` is greater than or equal to the length of `data`, the entire data is returned as a single batch.

    Yields:
        list: A list containing a batch of items from the input data.
    """

    if not isinstance(max_memory_usage, (int, float)) or not (0.0 <= max_memory_usage <= 1.0):
        raise ValueError("max_memory_usage must be a number between 0.0 and 1.0 (inclusive).")
    
    if not isinstance(wait_time, (int, float)) or wait_time < 0:
        raise ValueError("wait_time must be a non-negative integer or float.")
    
    if not isinstance(batch_size, int):
        raise TypeError("Batch size must be an integer.")
    
    if not isinstance(data, (list, tuple, set)):
        raise TypeError("Data must be an iterable (list, tuple, or set).")
    
    if len(data) == 0:
        raise ValueError("Data cannot be empty.")

    if batch_size <= 0:
        batch_size = _calculate_batch_size(data, batch_size)
    
    if batch_size >= len(data):
        yield list(data)
        return
    
    if wait_time <= 0:
        wait_time = 0.1
    
    iter_data = iter(data)

    with GCManager(memory_threshold=max_memory_usage, wait_time=wait_time):
        while True:
            batch = list(islice(iter_data, batch_size))
            if not batch:
                break
            yield batch


def batcher(
    data: Iterable,
    batch_size: int = -1
) -> Generator[List[Any], None, None]:
    """
    batcher
    =======
    A generator function that batches input data into smaller lists.

    Arguments:
        data (Iterable): The input data to be batched.
        batch_size (int): The size of each batch.

    Notes:
    -------
    - If `batch_size` is less than or equal to 0, it defaults to the number of CPU cores.
    - If `data` is not a list, a TypeError is raised.
    - If `batch_size` is greater than or equal to the length of `data`, the entire data is returned as a single batch.

    Yields:
        list: A list containing a batch of items from the input data.
    """

    if not isinstance(batch_size, int):
        raise TypeError("Batch size must be an integer.")
    
    if not isinstance(data, (list, tuple, set)):
        raise TypeError("Data must be an list,tuple or set.")

    if len(data) == 0:
        raise ValueError("Data cannot be empty.")

    if batch_size <= 0:
        batch_size = _calculate_batch_size(data, batch_size)
    
    if batch_size >= len(data):
        yield list(data)
        return
    
    iter_data = iter(data)

    while True:
        batch = list(islice(iter_data, batch_size))
        if not batch:
            break
        yield batch

