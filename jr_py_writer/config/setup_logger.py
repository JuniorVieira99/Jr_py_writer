# ------------------------------------------------------
# Imports
# ------------------------------------------------------

import logging.config
import logging
import yaml

from pathlib import Path

# ------------------------------------------------------
# Constants
# ------------------------------------------------------

YAML_FILE_PATH = Path(__file__).resolve().parent / "logging_settings.yaml"

# -------------------------------------------------------
# Exceptions
# -------------------------------------------------------


class LoggerSetupError(Exception):
    """Custom exception for logger setup errors."""

    pass


# ------------------------------------------------------
# Functions
# ------------------------------------------------------


def setup_logger(
    path: Path = YAML_FILE_PATH,
    name: str = "default_logger",
    level: int = logging.DEBUG,
) -> logging.Logger:
    """
    Setup a logger with the given name and level.
    The logger configuration is loaded from a YAML file.
    The YAML file should be located in the same directory as this script.

    Arguments
    -----------
        path (Path) : Path to the YAML file containing the logger configuration.
            - Default is the YAML_FILE_PATH constant.
        name (str) : Name of the logger to be created.
        level (int) : Logging level for the logger. Default is logging.INFO.

    Available Logger Names
    -----------
        - default_logger : Default logger for the application.
        - file_console_logger : Logger for file and console output.

    Available Levels
    -----------
        - logging.DEBUG : 10
        - logging.INFO : 20
        - logging.WARNING : 30
        - logging.ERROR : 40
        - logging.CRITICAL : 50

    Returns
    -----------
        out (logging.Logger) : The configured logger.

    Raises
    -----------
        raises (LoggerSetupError) : If there is an error setting up the logger.

    """

    try:
        if not isinstance(name, str):
            raise TypeError(f"Logger name {name} is not a string")

        if not isinstance(level, int):
            raise TypeError(f"Logger level {level} is not an integer")

        dir_path = path.parent
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory {dir_path} does not exist")

        if not path.exists():
            raise FileNotFoundError(f"File {path} does not exist")
        if not path.is_file():
            raise IsADirectoryError(f"{path} is not a file")
        if path.suffix != ".yaml":
            raise ValueError(f"File {path} is not a yaml file")

        # Create logs directory if it doesn't exist
        logs_dir = dir_path / "logs"
        if not logs_dir.exists():
            logs_dir.mkdir(parents=True, exist_ok=True)

        with open(path, "r") as file:

            if not file.readable():
                raise PermissionError(f"File {path} is not readable")

            config = yaml.safe_load(file.read())

        if not config:
            raise ValueError(f"File {path} is empty")

        if not isinstance(config, dict):
            raise TypeError(f"File {path} is not a valid yaml file")

        if "version" not in config:
            raise KeyError(f"File {path} does not contain a version key")

        # Config Logger
        logging.config.dictConfig(config)
        # Get Logger
        logger = logging.getLogger(name)

        if not logger:
            raise ValueError(f"Logger {name} not found in config file")

        # Set Level
        logger.setLevel(level)

        # Return Logger
        return logger
    except Exception as e:
        raise LoggerSetupError(
            f"Error setting up logger -> {e.__class__.__name__} : {e}"
        ) from e


# ------------------------------------------------------
# Simple Testing
# ------------------------------------------------------

if __name__ == "__main__":

    # Setup logger
    logger = setup_logger()

    # Test logger
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    logger.log(100, "This is a custom log message with level 100")

    # File logger
    file_logger = setup_logger(name="file_console_logger")
    file_logger.debug("This is a debug message from file_console_logger")
    file_logger.info("This is an info message from file_console_logger")
    file_logger.warning("This is a warning message from file_console_logger")
    file_logger.error("This is an error message from file_console_logger")
    file_logger.critical("This is a critical message from file_console_logger")
    file_logger.log(
        100, "This is a custom log message with level 100 from file_console_logger"
    )
