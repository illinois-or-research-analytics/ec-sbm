import logging
from pathlib import Path


def setup_logging(log_filepath: Path):
    """
    Universal logging function.
    Forces output exclusively to the provided log_filepath with timestamps.
    Prevents any standard error/console leakage.
    """
    log_filepath.parent.mkdir(parents=True, exist_ok=True)

    # 1. Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 2. Strip out ALL existing handlers (this prevents the stderr leakage)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 3. Create a dedicated FileHandler
    file_handler = logging.FileHandler(log_filepath, mode="w")
    file_handler.setLevel(logging.INFO)

    # 4. Enforce the timestamp format
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # 5. Attach our strict file handler to the root logger
    logger.addHandler(file_handler)
