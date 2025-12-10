import logging
from logging.handlers import RotatingFileHandler


def setup_logger():
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        "pipeline.log", maxBytes=2_000_000, backupCount=3)
    formatter = logging.Formatter(
        "%(asctime)s — %(levelname)s — %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger


logger = setup_logger()
