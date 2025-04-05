import logging
from logging.handlers import RotatingFileHandler
import json
from typing import Optional, Dict, Any
import os
from datetime import datetime

class StructuredLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
            
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

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
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            'logs/app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(StructuredLogFormatter())
        
        # Create console handler with simpler format
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        # Add handlers to root logger
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
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
            logger.setLevel(logging.INFO)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger instance, ensuring logging is set up."""
        if cls._instance is None:
            cls()
        return logging.getLogger(name)

# Global function to get logger
def get_logger(name: str) -> logging.Logger:
    return LoggingManager.get_logger(name) 