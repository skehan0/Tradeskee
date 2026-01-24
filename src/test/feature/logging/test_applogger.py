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


class FailingHandler(LoggingService):
    """Handler that raises exceptions for testing error handling"""
    
    def handle(self, level: str, message: str, **kwargs) -> None:
        raise RuntimeError("Handler failed")
    
    def close(self) -> None:
        raise RuntimeError("Close failed")


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
    
    def test_all_log_levels(self):
        """Test all log levels are properly delegated"""
        # Arrange
        fake_handler = FakeHandler()
        logger = build_app_logger(handlers=[fake_handler])
        
        # Act
        logger.debug("Debug msg")
        logger.info("Info msg")
        logger.warning("Warning msg")
        logger.error("Error msg")
        logger.critical("Critical msg")
        
        # Assert
        self.assertEqual(len(fake_handler.logs), 5)
        self.assertEqual(fake_handler.logs[0]["level"], "DEBUG")
        self.assertEqual(fake_handler.logs[1]["level"], "INFO")
        self.assertEqual(fake_handler.logs[2]["level"], "WARNING")
        self.assertEqual(fake_handler.logs[3]["level"], "ERROR")
        self.assertEqual(fake_handler.logs[4]["level"], "CRITICAL")
    
    def test_multiple_handlers(self):
        """Test logger sends messages to multiple handlers"""
        # Arrange
        handler1 = FakeHandler()
        handler2 = FakeHandler()
        logger = build_app_logger(handlers=[handler1, handler2])
        
        # Act
        logger.info("Test message")
        
        # Assert
        self.assertEqual(len(handler1.logs), 1)
        self.assertEqual(len(handler2.logs), 1)
        self.assertEqual(handler1.logs[0]["message"], "Test message")
        self.assertEqual(handler2.logs[0]["message"], "Test message")
    
    def test_handler_failure_does_not_break_logging(self):
        """Test that if one handler fails, logging continues"""
        # Arrange
        failing = FailingHandler()
        working = FakeHandler()
        logger = build_app_logger(handlers=[failing, working])
        
        # Act - should not raise exception
        logger.info("Test message")
        
        # Assert - working handler still received the log
        self.assertEqual(len(working.logs), 1)
    
    def test_add_handler(self):
        """Test adding a handler dynamically"""
        # Arrange
        handler1 = FakeHandler()
        logger = build_app_logger(handlers=[handler1])
        handler2 = FakeHandler()
        
        # Act
        logger.add_handler(handler2)
        logger.info("Test message")
        
        # Assert
        self.assertEqual(len(handler1.logs), 1)
        self.assertEqual(len(handler2.logs), 1)
    
    def test_remove_handler(self):
        """Test removing a handler"""
        # Arrange
        handler1 = FakeHandler()
        handler2 = FakeHandler()
        logger = build_app_logger(handlers=[handler1, handler2])
        
        # Act
        logger.remove_handler(handler1)
        logger.info("Test message")
        
        # Assert
        self.assertEqual(len(handler1.logs), 0)
        self.assertEqual(len(handler2.logs), 1)
    
    def test_close_calls_all_handlers(self):
        """Test close() calls close on all handlers"""
        # Arrange
        handler1 = FakeHandler()
        handler2 = FakeHandler()
        logger = build_app_logger(handlers=[handler1, handler2])
        
        # Act
        logger.close()
        
        # Assert
        self.assertTrue(handler1.closed)
        self.assertTrue(handler2.closed)
    
    def test_close_handles_failing_handlers(self):
        """Test close() doesn't raise even if handler close fails"""
        # Arrange
        failing = FailingHandler()
        working = FakeHandler()
        logger = build_app_logger(handlers=[failing, working])
        
        # Act - should not raise exception
        logger.close()
        
        # Assert - working handler still closed
        self.assertTrue(working.closed)


if __name__ == "__main__":
    unittest.main()
