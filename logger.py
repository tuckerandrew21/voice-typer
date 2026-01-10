"""
Logging configuration for MurmurTone.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(log_level=logging.INFO, log_to_file=True):
    """
    Configure logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Whether to also log to a file

    Returns:
        Logger instance for the app
    """
    # Create logger
    logger = logging.getLogger("murmurtone")
    logger.setLevel(log_level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Format with timestamp and level
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_to_file:
        try:
            app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
            log_dir = os.path.join(app_data, "MurmurTone")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "murmurtone.log")

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=1024 * 1024,  # 1 MB
                backupCount=3
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass  # File logging is optional

    return logger


# Create default logger
log = setup_logging()
