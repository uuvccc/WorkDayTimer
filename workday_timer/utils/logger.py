import logging
import os

from workday_timer.config import config


def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        filename=config.log_file,  # Log file name in the application directory
        level=logging.DEBUG,  # Only record logs at DEBUG level and above
        format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
    )
