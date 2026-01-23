from typing import List
from src.feature.logging.applog import AppLogger
from src.feature.logging.logging_interface import LoggingService
from src.feature.logging.logging_handlers import StdoutLoggingService


def build_app_logger(name: str, handlers: List[LoggingService]) -> AppLogger:
    """
    Dependency Injection composition root.
    
    Wires pre-configured handlers into AppLogger.
    Handlers are created externally and passed in.
    
    Example:
        handlers = [StdoutLoggingService()]
        logger = build_app_logger("my_module", handlers)
    """
    return AppLogger(name=name, services=handlers)


def get_default_logger(name: str) -> AppLogger:
    """Convenience function: creates logger with default stdout handler"""
    return build_app_logger(name, handlers=[StdoutLoggingService()])