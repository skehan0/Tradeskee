import unittest
import sys
import json
from io import StringIO
from datetime import datetime
from src.feature.logging.logging_handlers import StdoutLoggingService


class TestStdoutLoggingService(unittest.TestCase):
    """Test StdoutLoggingService outputs correctly to stdout"""
    
    def setUp(self):
        """Redirect stdout for testing"""
        self.held_stdout = sys.stdout
        sys.stdout = StringIO()
    
    def tearDown(self):
        """Restore stdout"""
        sys.stdout = self.held_stdout
    
    def test_handle_logs_to_stdout(self):
        """Test that handle() writes JSON to stdout"""
        # Arrange
        service = StdoutLoggingService()
        
        # Act
        service.handle("INFO", "Test message", context={"user_id": 123})
        
        # Assert
        output = sys.stdout.getvalue()
        log_entry = json.loads(output.strip())
        
        self.assertEqual(log_entry["level"], "INFO")
        self.assertEqual(log_entry["message"], "Test message")
        self.assertEqual(log_entry["context"]["user_id"], 123)
        self.assertIn("timestamp", log_entry)
    
    def test_handle_with_no_context(self):
        """Test logging without context kwargs"""
        # Arrange
        service = StdoutLoggingService()
        
        # Act
        service.handle("ERROR", "Error occurred")
        
        # Assert
        output = sys.stdout.getvalue()
        log_entry = json.loads(output.strip())
        
        self.assertEqual(log_entry["level"], "ERROR")
        self.assertEqual(log_entry["message"], "Error occurred")
        self.assertEqual(log_entry["context"], {})
    
    def test_timestamp_format(self):
        """Test that timestamp is in ISO format with UTC timezone"""
        # Arrange
        service = StdoutLoggingService()
        
        # Act
        service.handle("DEBUG", "Debug message")
        
        # Assert
        output = sys.stdout.getvalue()
        log_entry = json.loads(output.strip())
        
        # Verify timestamp is parseable and has timezone info
        timestamp = datetime.fromisoformat(log_entry["timestamp"])
        self.assertIsNotNone(timestamp.tzinfo)
    
    def test_multiple_logs(self):
        """Test multiple log entries are written on separate lines"""
        # Arrange
        service = StdoutLoggingService()
        
        # Act
        service.handle("INFO", "First message")
        service.handle("WARNING", "Second message")
        
        # Assert
        output = sys.stdout.getvalue()
        lines = output.strip().split("\n")
        
        self.assertEqual(len(lines), 2)
        log1 = json.loads(lines[0])
        log2 = json.loads(lines[1])
        
        self.assertEqual(log1["message"], "First message")
        self.assertEqual(log2["message"], "Second message")


if __name__ == "__main__":
    unittest.main()
