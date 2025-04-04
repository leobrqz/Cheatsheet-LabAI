import logging
from typing import Optional

class LoggingManager:
    _instance: Optional['LoggingManager'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggingManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logging()
            self._initialized = True
    
    def _setup_logging(self):
        """Set up logging configuration for the application."""
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Suppress httpx logs
        logging.getLogger("httpx").setLevel(logging.WARNING)
        
        # Create loggers for each module
        loggers = [
            "main",
            "database",
            "generators",
            "formatters",
            "query_builder",
            "utils"
        ]
        
        for logger_name in loggers:
            logger = logging.getLogger(logger_name)
            # Ensure the logger has a handler
            if not logger.handlers:
                logger.addHandler(logging.StreamHandler())
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger instance, ensuring logging is set up."""
        if cls._instance is None:
            cls()
        return logging.getLogger(name)

# Global function to get logger
def get_logger(name: str) -> logging.Logger:
    return LoggingManager.get_logger(name) 