import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

# Define the log directory based on absolute path
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")

# Ensure the logs directory exists
os.makedirs(log_dir, exist_ok=True)

def setup_logger(name: str):
    """
    Sets up a logger that logs to the console and to a date-wise rotating file.
    The file will overwrite the day's logs but keep history separated by dates.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if setup_logger is called multiple times for the same module
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Log Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console Handler
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        sh.setLevel(logging.INFO)
        logger.addHandler(sh)
        
        # Rotating File Handler - creates new file at midnight, keeps backup count if needed
        # Overwrites the current date's file dynamically (appends throughout the day)
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"app_{current_date_str}.log")
        
        # Using specific FileHandler that appends for the day
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(formatter)
        fh.setLevel(logging.DEBUG)  # File gets more detailed logs (DEBUG level)
        logger.addHandler(fh)
        
    return logger
