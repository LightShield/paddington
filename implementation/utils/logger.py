"""Logging utilities."""

import sys
from datetime import datetime


class Logger:
    """Simple logger with verbosity levels."""
    
    LEVELS = {
        'ERROR': 0,
        'WARNING': 1,
        'INFO': 2,
        'DEBUG': 3,
        'TRACE': 4
    }
    
    def __init__(self, level='INFO'):
        self.level = self.LEVELS.get(level, 2)
    
    def set_level(self, level):
        """Set logging level."""
        if isinstance(level, str):
            self.level = self.LEVELS.get(level, 2)
        else:
            self.level = level
    
    def error(self, msg):
        """Log error message."""
        if self.level >= 0:
            print(f"[ERROR] {msg}", file=sys.stderr)
    
    def warning(self, msg):
        """Log warning message."""
        if self.level >= 1:
            print(f"[WARNING] {msg}")
    
    def info(self, msg):
        """Log info message."""
        if self.level >= 2:
            print(f"[INFO] {msg}")
    
    def debug(self, msg):
        """Log debug message."""
        if self.level >= 3:
            print(f"[DEBUG] {msg}")
    
    def trace(self, msg):
        """Log trace message."""
        if self.level >= 4:
            print(f"[TRACE] {msg}")
