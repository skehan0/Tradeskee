from datetime import datetime, timezone, timezone
import json
import sys

from src.feature.logging.logging_interface import LoggingService


class StdoutLoggingService(LoggingService):
    """Logging service that outputs to stdout"""

    def handle(self, level: str, message: str, **kwargs) -> None:
        """Log a message to stdout"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "context": kwargs.get("context", {})
        }
        
        json.dump(log_entry, sys.stdout)
        sys.stdout.write("\n")
        sys.stdout.flush()
    
    def close(self) -> None:
        """No cleanup needed for stdout"""
        pass