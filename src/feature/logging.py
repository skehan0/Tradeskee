import logging


class StdoutLoggingService:
    """Placeholder logging handler for tests and local runs."""
    def __init__(self):
        pass


def build_app_logger(name: str = "tradeskee", handlers=None):
    logger = logging.getLogger(name)
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)
    logger.setLevel(logging.INFO)
    return logger
