import logging

def setup_logging():
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