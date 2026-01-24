import unittest
from src.feature.logging.logging_interface import LoggingService
from src.feature.logging.logging_config import build_app_logger


class FakeHandler(LoggingService):
    """Fake handler for testing dependency injection"""
    
    def __init__(self):
        self.logs = []
        self.closed = False
    
    def handle(self, level: str, message: str, **kwargs) -> None:
        self.logs.append({
            "level": level,
            "message": message,
            "kwargs": kwargs
        })
    
    def close(self) -> None:
        self.closed = True


class TestAppLogger(unittest.TestCase):
    """Test AppLogger with dependency injection"""
    
    def test_logger_calls_injected_handler(self):
        """Test that logger delegates to injected handler"""
        # Arrange: Create and inject fake handler
        fake_handler = FakeHandler()
        logger = build_app_logger(handlers=[fake_handler])
        
        # Act: Log a message
        logger.info("Test message", user_id=123)
        
        # Assert: Handler received the log call
        self.assertEqual(len(fake_handler.logs), 1)
        self.assertEqual(fake_handler.logs[0]["level"], "INFO")
        self.assertEqual(fake_handler.logs[0]["message"], "Test message")
        self.assertEqual(fake_handler.logs[0]["kwargs"]["user_id"], 123)


if __name__ == "__main__":
    unittest.main()
