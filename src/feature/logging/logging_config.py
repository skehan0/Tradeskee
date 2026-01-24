from typing import List
from src.feature.logging.applog import AppLogger
from src.feature.logging.logging_interface import LoggingService
from src.feature.logging.logging_handlers import StdoutLoggingService


def build_app_logger(handlers: List[LoggingService]) -> AppLogger:
    """Dependency injection composition root"""
    return AppLogger(handlers=handlers)