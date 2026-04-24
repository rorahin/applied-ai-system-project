import logging
import os


def setup_logger(name: str = "music_agent") -> logging.Logger:
    """
    Create and return a named logger that writes to both the console and logs/app.log.
    Safe to call multiple times — returns the existing logger if already configured.
    """
    logger = logging.getLogger(name)

    # Guard: only add handlers once per logger name
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler — INFO and above
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(console)

    # File handler — DEBUG and above (full trace)
    os.makedirs("logs", exist_ok=True)
    file_handler = logging.FileHandler("logs/app.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    logger.addHandler(file_handler)

    return logger
