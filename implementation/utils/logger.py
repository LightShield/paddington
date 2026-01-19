"""
Thread-safe singleton logger with colored output.
Source: https://github.com/LightShield/logger_python
"""

import sys
import threading
import datetime
import inspect


class Logger:
    _instance = None
    _lock = threading.Lock()

    LEVELS = {
        "DEBUG": 10,
        "INFO": 20,
        "USER": 25,  # User-facing output (always shown)
        "WARNING": 30,
        "ERROR": 40,
    }

    COLORS = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[92m",  # Green
        "USER": "\033[96m",  # Cyan
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[1;91m",  # Bright red bold
        "RESET": "\033[0m",
    }

    def __new__(cls, level="INFO"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super(Logger, cls).__new__(cls)
                    cls._instance = instance
                    instance.level = cls.LEVELS.get(level.upper(), 20)
        return cls._instance

    @staticmethod
    def get():
        """Get singleton instance."""
        return Logger._instance or Logger()

    def set_level(self, level_name):
        """Set logging level."""
        level = self.LEVELS.get(level_name.upper())
        if level is not None:
            self.level = level
        else:
            self.warning(f"Unknown log level: {level_name}")

    def _get_caller_info(self):
        """Get caller filename and line number."""
        frame = inspect.currentframe()
        outer_frames = inspect.getouterframes(frame)
        
        # Skip frames until we're out of Logger class
        for frm in outer_frames:
            frame_globals = frm.frame.f_globals.get("__name__", "")
            # Skip if we're still in logger module
            if "logger" in frame_globals.lower():
                continue
            
            # Get filename without path
            filename = frm.filename.split("/")[-1].replace(".py", "")
            
            # Try to get class name if in a class method
            if 'self' in frm.frame.f_locals:
                class_name = frm.frame.f_locals['self'].__class__.__name__
                return f"{class_name}:{frm.lineno}", frm.lineno
            
            # Otherwise use filename
            return f"{filename}:{frm.lineno}", frm.lineno
        
        return "(unknown)", 0

    def _log(self, level_name, message):
        """Log message with timestamp, color, and source location."""
        level_num = self.LEVELS.get(level_name, 99)
        if level_num < self.level:
            return  # Skip logs lower than current level

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        location, lineno = self._get_caller_info()
        color = self.COLORS.get(level_name, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        output = f"{now} {color}[{level_name}] {location}{reset} {message}"
        print(output, file=sys.stderr if level_name == "ERROR" else sys.stdout)

    def debug(self, message):
        """Log debug message."""
        self._log("DEBUG", message)

    def info(self, message):
        """Log info message."""
        self._log("INFO", message)

    def warning(self, message):
        """Log warning message."""
        self._log("WARNING", message)

    def error(self, message):
        """Log error message."""
        self._log("ERROR", message)
    
    def user(self, message):
        """Log user-facing message (always shown)."""
        self._log("USER", message)
