"""
Standardized logging configuration for BIthere.
Format: [LEVEL] message
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
    Return a configured logger instance.
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


# ---------------------------------------------------------------------
# Convenience helpers
# Used by agents (llm.py, planner.py, etc.) so they can simply call:
#     from app.core.logging import log_info, log_error
# without creating their own logger instance.
# ---------------------------------------------------------------------

def log_debug(message: str, *args, **kwargs) -> None:
    """Log message at DEBUG level."""
    logger.debug(message, *args, **kwargs)


def log_info(message: str, *args, **kwargs) -> None:
    """Log message at INFO level."""
    logger.info(message, *args, **kwargs)


def log_process(message: str, *args, **kwargs) -> None:
    """Log message at PROCESS level (25) for step-by-step agent pipeline."""
    logger.process(message, *args, **kwargs)


def log_success(message: str, *args, **kwargs) -> None:
    """Log message at SUCCESS level (35) for successful operations."""
    logger.success(message, *args, **kwargs)


def log_warning(message: str, *args, **kwargs) -> None:
    """Log message at WARNING level."""
    logger.warning(message, *args, **kwargs)


def log_error(message: str, *args, **kwargs) -> None:
    """Log message at ERROR level."""
    logger.error(message, *args, **kwargs)


def log_critical(message: str, *args, **kwargs) -> None:
    """Log message at CRITICAL level."""
    logger.critical(message, *args, **kwargs)