"""
Custom Logger Module

Provides a Logger class wrapping Python's logging library to output
formatted logs to a file and optionally to the console with an optional prefix.
"""

import logging

# Default path for the log file
LOG_FILE_PATH = "output.log"


class Logger:
    """
    Logger wrapper to handle file and console logging with a custom format and prefix.

    :param log_file_path: Path to the log file where messages will be written
    :param prefix: Optional string to prepend to each log message
    :param debug: If True, set logging level to DEBUG; otherwise INFO
    :param log_to_console: If True, also output logs to the console
    """

    def __init__(
        self,
        log_file_path: str = LOG_FILE_PATH,
        prefix: str = "",
        debug: bool = False,
        log_to_console: bool = True,
    ):
        # Determine log level based on debug flag
        level = logging.DEBUG if debug else logging.INFO

        # Create or retrieve a logger using the file path as its name
        self.logger = logging.getLogger(log_file_path)
        # Prevent logs from being passed to ancestor loggers
        self.logger.propagate = False
        # Set the logger's threshold level
        self.logger.setLevel(level)
        self.prefix = prefix

        # Remove existing handlers to avoid duplicate output
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Define a standard formatter for file and console
        formatter = logging.Formatter(
            "[%(levelname)s],%(asctime)s,%(message)s", datefmt="%Y/%m/%d %H:%M:%S"
        )

        # Configure file handler
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Optionally configure console (stream) handler
        if log_to_console:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(level)
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

    def debug(self, msg: str):
        """
        Log a debug-level message, prefixed if specified.

        :param msg: The message to log
        """
        self.logger.debug(f"{self.prefix},{msg}")

    def info(self, msg: str):
        """
        Log an info-level message, prefixed if specified.

        :param msg: The message to log
        """
        self.logger.info(f"{self.prefix},{msg}")

    def warning(self, msg: str):
        """
        Log a warning-level message, prefixed if specified.

        :param msg: The message to log
        """
        self.logger.warning(f"{self.prefix},{msg}")

    def error(self, msg: str):
        """
        Log an error-level message, prefixed if specified.

        :param msg: The message to log
        """
        self.logger.error(f"{self.prefix},{msg}")
