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
        "WARNING": 30,
        "ERROR": 40,
    }

    COLORS = {
        "DEBUG": "\033[94m",        # Blue
        "INFO": "\033[92m",         # Green
        "WARNING": "\033[93m",      # Yellow
        "ERROR": "\033[1;91m",      # Bright red bold
        "RESET": "\033[0m"
    }

    def __new__(cls, level="DEBUG"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super(Logger, cls).__new__(cls)
                    cls._instance = instance
                    instance.level = cls.LEVELS.get(level.upper(), 10)
        return cls._instance

    @staticmethod
    def get():
        # Return existing instance (created via __new__)
        return Logger._instance or Logger()

    def set_level(self, level_name):
        level = self.LEVELS.get(level_name.upper())
        if level is not None:
            self.level = level
        else:
            self.warning(f"Unknown log level: {level_name}")

    def _get_caller_info(self):
        frame = inspect.currentframe()
        outer_frames = inspect.getouterframes(frame)
        for frm in outer_frames:
            if 'Logger' not in frm.frame.f_globals.get('__name__', ''):
                return frm.filename.split('/')[-1], frm.lineno
        return "(unknown)", 0

    def _log(self, level_name, message):
        level_num = self.LEVELS.get(level_name, 99)
        if level_num < self.level:
            return  # Skip logs lower than current level

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename, lineno = self._get_caller_info()
        color = self.COLORS.get(level_name, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        output = f"{now} {color}[{level_name}] {filename}:{lineno}{reset} {message}"
        print(output, file=sys.stderr if level_name == "ERROR" else sys.stdout)

    def debug(self, message):
        self._log("DEBUG", message)

    def info(self, message):
        self._log("INFO", message)

    def warning(self, message):
        self._log("WARNING", message)

    def error(self, message):
        self._log("ERROR", message)


# Example usage
if __name__ == "__main__":
    log = Logger(level="INFO")
    log.debug("This debug message will NOT show")
    log.info("This info message will show")
    log.set_level("DEBUG")
    log.debug("This debug message WILL show now")
