# ----------------------------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------------------------

from enum import StrEnum

# ----------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------

class LogWriteMode(StrEnum):
    """
    String Enum for log write modes.

    Attributes:
        APPEND (str | a): Append mode, adds to the end of the file.
        OVERWRITE (str | w): Overwrite mode, replaces the file content.
        READ (str | r): Read mode, reads from the file.
        READ_WRITE (str | r+): Read and write mode, allows reading and writing.
        WRITE_READ (str | w+): Write and read mode, allows writing and reading.
        
    """
    APPEND = "a"
    OVERWRITE = "w"
    READ = "r"
    READ_WRITE = "r+"
    WRITE_READ = "w+"


    @staticmethod
    def print_modes():
        """
        Print all log write modes.
        """
        for mode in LogWriteMode:
            print(f"{mode.name}: {mode.value}")

