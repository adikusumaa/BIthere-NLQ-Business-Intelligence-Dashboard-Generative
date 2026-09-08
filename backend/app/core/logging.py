"""
Standardized logging configuration for BIthere.
Format: [PROCESS NAME] detail process...
"""

import logging
import sys


PROCESS_LEVEL = 25
SUCCESS_LEVEL = 35

logging.addLevelName(PROCESS_LEVEL, "PROCESS")
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


def _process(self, message, *args, **kwargs):
    if self.isEnabledFor(PROCESS_LEVEL):
        self._log(PROCESS_LEVEL, message, args, **kwargs)


def _success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)


logging.Logger.process = _process
logging.Logger.success = _success


class BIthereFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in professional format.
    """

    COLORS = {
        "PROCESS": "\033[36m",
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        log_level = record.levelname
        color = self.COLORS.get(log_level, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        return f"{color}[{log_level}]{reset} {record.getMessage()}"


def get_logger(name: str = "bithere") -> logging.Logger:
    """
    Returns a configured logger instance.
    Prevents duplicate handlers on repeated calls.
    """

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(BIthereFormatter())
    logger.addHandler(console_handler)

    return logger


logger = get_logger()