import logging
import sys

def configure_logging(name: str = None, level: int = logging.INFO) -> logging.Logger:
    formatter = logging.Formatter(
        fmt="[%(asctime)s: %(levelname)s/%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        logger.addHandler(handler)

    logger.propagate = False

    return logger