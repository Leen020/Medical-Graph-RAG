# logger
import sys
from datetime import datetime

class Logger:
    def __init__(self, filename="processing.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "w", encoding="utf-8")  # Use "a" for append mode
    
    def write(self, message):
        self.terminal.write(message)
        self.log.write(f"[{datetime.now().isoformat()}] {message}")
    
    def flush(self):  # Required for Python 3 compatibility
        pass
    
    def __getattr__(self, attr):
        return getattr(self.terminal, attr)