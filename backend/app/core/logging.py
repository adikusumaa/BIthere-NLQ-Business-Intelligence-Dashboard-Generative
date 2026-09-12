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


# ---------------------------------------------------------------------
# Convenience helpers
# Dipakai oleh agent (llm.py, planner.py, dll) supaya cukup:
#     from app.core.logging import log_info, log_error
# tanpa harus membuat logger sendiri.
# ---------------------------------------------------------------------

def log_debug(message: str, *args, **kwargs) -> None:
    """Log pesan di level DEBUG."""
    logger.debug(message, *args, **kwargs)


def log_info(message: str, *args, **kwargs) -> None:
    """Log pesan di level INFO."""
    logger.info(message, *args, **kwargs)


def log_process(message: str, *args, **kwargs) -> None:
    """Log pesan di level PROCESS (25) — untuk step-by-step proses agent."""
    logger.process(message, *args, **kwargs)


def log_success(message: str, *args, **kwargs) -> None:
    """Log pesan di level SUCCESS (35) — untuk operasi yang berhasil."""
    logger.success(message, *args, **kwargs)


def log_warning(message: str, *args, **kwargs) -> None:
    """Log pesan di level WARNING."""
    logger.warning(message, *args, **kwargs)


def log_error(message: str, *args, **kwargs) -> None:
    """Log pesan di level ERROR."""
    logger.error(message, *args, **kwargs)


def log_critical(message: str, *args, **kwargs) -> None:
    """Log pesan di level CRITICAL."""
    logger.critical(message, *args, **kwargs)