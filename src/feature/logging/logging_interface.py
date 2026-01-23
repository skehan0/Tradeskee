from abc import ABC, abstractmethod


class LoggingService(ABC):
    """Abstract base class for logging services"""
    
    @abstractmethod
    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message with the given level"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Clean up resources"""
        pass
