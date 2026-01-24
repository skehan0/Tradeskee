from abc import ABC, abstractmethod


class LoggingService(ABC):
    """Abstract base class for logging services"""
    
    @abstractmethod
    def handle(self, level: str, message: str, **kwargs) -> None:
        """Log a message with the given level"""
        pass
    
    def close(self) -> None:
        """Close the logging service and cleanup resources. Override if needed."""
        pass
