import sqlite3
from datetime import datetime
import json
import os
import stat
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path="db/debug_logs.db"):
        """Initialize database connection and create tables if they don't exist."""
        self.db_path = db_path
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Set appropriate file permissions for the database directory
        self._set_directory_permissions(os.path.dirname(db_path))
        
        self._create_tables()
        
        # Set appropriate file permissions for the database file
        self._set_file_permissions(db_path)
    
    def _set_directory_permissions(self, directory_path):
        """Set appropriate permissions for the database directory."""
        try:
            # Set directory permissions to 755 (owner can read/write/execute, others can read/execute)
            os.chmod(directory_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            logger.info(f"Set permissions for directory: {directory_path}")
        except Exception as e:
            logger.error(f"Failed to set directory permissions: {e}")
    
    def _set_file_permissions(self, file_path):
        """Set appropriate permissions for the database file."""
        try:
            # Set file permissions to 644 (owner can read/write, others can read)
            os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            logger.info(f"Set permissions for file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to set file permissions: {e}")
    
    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS token_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    function_name TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    cost REAL NOT NULL,
                    output TEXT
                )
            ''')
            conn.commit()
    
    def _validate_parameters(self, function_name, prompt_tokens, completion_tokens, total_tokens, cost, output=None):
        """Validate parameter types and values for database operations."""
        # Type checking
        if not isinstance(function_name, str):
            raise TypeError("function_name must be a string")
        if not isinstance(prompt_tokens, int) or prompt_tokens < 0:
            raise ValueError("prompt_tokens must be a non-negative integer")
        if not isinstance(completion_tokens, int) or completion_tokens < 0:
            raise ValueError("completion_tokens must be a non-negative integer")
        if not isinstance(total_tokens, int) or total_tokens < 0:
            raise ValueError("total_tokens must be a non-negative integer")
        if not isinstance(cost, (int, float)) or cost < 0:
            raise ValueError("cost must be a non-negative number")
        if output is not None and not isinstance(output, str):
            raise TypeError("output must be a string or None")
        
        # Additional validation
        if len(function_name) > 100:
            raise ValueError("function_name is too long (max 100 characters)")
        
        return True
    
    def add_log(self, function_name, prompt_tokens, completion_tokens, total_tokens, cost, output=None):
        """Add a new token usage log entry with optional output."""
        # Validate parameters
        self._validate_parameters(function_name, prompt_tokens, completion_tokens, total_tokens, cost, output)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO token_logs 
                    (timestamp, function_name, prompt_tokens, completion_tokens, total_tokens, cost, output)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (datetime.now().isoformat(), function_name, prompt_tokens, 
                     completion_tokens, total_tokens, cost, output))
                conn.commit()
                logger.info(f"Added log entry for function: {function_name}")
        except sqlite3.Error as e:
            logger.error(f"Database error when adding log: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error when adding log: {e}")
            raise
    
    def get_logs(self, limit=100):
        """Retrieve the most recent logs."""
        # Validate limit parameter
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT timestamp, function_name, prompt_tokens, completion_tokens, 
                           total_tokens, cost
                    FROM token_logs
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Database error when retrieving logs: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error when retrieving logs: {e}")
            raise
    
    def get_total_usage(self):
        """Calculate total token usage and cost."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        SUM(prompt_tokens) as total_prompt_tokens,
                        SUM(completion_tokens) as total_completion_tokens,
                        SUM(total_tokens) as total_tokens,
                        SUM(cost) as total_cost
                    FROM token_logs
                ''')
                return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Database error when calculating total usage: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error when calculating total usage: {e}")
            raise 