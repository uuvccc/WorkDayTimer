import logging
from PyQt5.QtWidgets import QMessageBox


def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler"""
    # Log the exception
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Show error message to user
    error_message = f"An unexpected error occurred: {str(exc_value)}"
    QMessageBox.critical(None, "Error", error_message)


def safe_execute(func, *args, **kwargs):
    """Execute a function with exception handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logging.error(f"Error executing {func.__name__}: {str(e)}")
        return None
