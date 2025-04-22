import logging


LOG_FILE_PATH = "output.log"


class Logger:
    def __init__(
        self,
        log_file_path: str = LOG_FILE_PATH,
        prefix: str = "",
        debug: bool = False,
        log_to_console: bool = True,
    ):
        # Create a unique logger name if needed, here we just use the file path
        level = logging.INFO
        if debug:
            level = logging.DEBUG

        self.logger = logging.getLogger(log_file_path)
        self.logger.propagate = False
        self.logger.setLevel(level)
        self.prefix = prefix

        # Clear any existing handlers to avoid duplicate logs
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        formatter = logging.Formatter(
            "[%(levelname)s],%(asctime)s,%(message)s", datefmt="%Y/%m/%d %H:%M:%S"
        )

        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        if log_to_console:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(level)
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

    def debug(self, msg):
        self.logger.debug(f"{self.prefix},{msg}")

    def info(self, msg):
        self.logger.info(f"{self.prefix},{msg}")

    def warning(self, msg):
        self.logger.warning(f"{self.prefix},{msg}")

    def error(self, msg):
        self.logger.error(f"{self.prefix},{msg}")
