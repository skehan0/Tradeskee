from typing import List

from src.alphaVantage import services
from src.feature.logging.logging_interface import LoggingService


class AppLogger:
    """Application logger with dependency injection"""
    
    def __init__(self, handlers: List[LoggingService]):
        """
        Initialize the logger with a name and logging services.
        
        Args:
            name: Logger name (typically module or class name)
            handlers: List of logging services (injected dependency)
        """
        self.handlers = handlers
    
    def _log(self, level: str, message: str, **kwargs) -> None:
        """Internal method to log to all services"""
        for handler in self.handlers:
            try:
                handler.handle(level, message, **kwargs)
            except Exception:
                # Fail silently to avoid breaking the application
                pass
    
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message"""
        self._log("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log an info message"""
        self._log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message"""
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log an error message"""
        self._log("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message"""
        self._log("CRITICAL", message, **kwargs)
    
    def add_handler(self, handler: LoggingService) -> None:
        """Add a new logging service"""
        self.handlers.append(handler)
    
    def remove_handler(self, handler: LoggingService) -> None:
        """Remove a logging service"""
        if handler in self.handlers:
            self.handlers.remove(handler)
    
    def close(self) -> None:
        """Close all logging services"""
        for handler in self.handlers:
            try:
                handler.close()
            except Exception:
                # Fail silently
                pass
