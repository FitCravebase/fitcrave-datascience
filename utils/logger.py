import os
import logging
from datetime import datetime

def setup_logger(name: str):
    """
    Sets up a logger. In production / Cloud Run, logs only to stdout so
    Cloud Logging can pick them up. In development, also writes to a
    date-stamped file when the logs/ directory is writable.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler — always present (stdout captured by Cloud Run / local terminal)
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    sh.setLevel(logging.INFO)
    logger.addHandler(sh)

    # Optional file handler — only when we can write to a logs/ directory
    try:
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
        )
        os.makedirs(log_dir, exist_ok=True)
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"app_{current_date_str}.log")
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(formatter)
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)
    except OSError:
        pass  # Read-only filesystem (Cloud Run) — stdout logging is enough

    return logger
