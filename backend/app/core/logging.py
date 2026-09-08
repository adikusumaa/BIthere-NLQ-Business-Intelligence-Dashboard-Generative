"""
Standardized logging configuration for BIthere.
Format: [PROCESS NAME] detail process...
"""

import logging
import sys


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