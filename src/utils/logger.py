import logging
from logging.handlers import RotatingFileHandler
import os
from src.config import LOG_FILE

def setup_logger(name, log_file=LOG_FILE, level=logging.INFO):
    """
    Sets up a logger with a rotating file handler.

    Args:
        name (str): Name of the logger.
        log_file (str): Path to the log file.
        level (int): Logging level (e.g., logging.INFO, logging.DEBUG).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding multiple handlers to the same logger
    if not logger.hasHandlers():
        # Ensure the logs directory exists
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)

        # Create a rotating file handler
        handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=2)  # 5 MB per file
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(handler)

        # Add a stream handler for console output
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
