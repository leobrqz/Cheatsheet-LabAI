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
    
    def get_logs_by_date_range(self, start_date, end_date, limit=100):
        """Retrieve logs within a specific date range."""
        # Validate parameters
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT timestamp, function_name, prompt_tokens, completion_tokens, 
                           total_tokens, cost
                    FROM token_logs
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (start_date, end_date, limit))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Database error when retrieving logs by date range: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error when retrieving logs by date range: {e}")
            raise
    
    def get_logs_by_function(self, function_name, limit=100):
        """Retrieve logs for a specific function."""
        # Validate parameters
        if not isinstance(function_name, str):
            raise TypeError("function_name must be a string")
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT timestamp, function_name, prompt_tokens, completion_tokens, 
                           total_tokens, cost
                    FROM token_logs
                    WHERE function_name = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (function_name, limit))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Database error when retrieving logs by function: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error when retrieving logs by function: {e}")
            raise
    
    def get_logs_by_token_range(self, min_tokens, max_tokens, limit=100):
        """Retrieve logs with total tokens within a specific range."""
        # Validate parameters
        if not isinstance(min_tokens, int) or min_tokens < 0:
            raise ValueError("min_tokens must be a non-negative integer")
        if not isinstance(max_tokens, int) or max_tokens < min_tokens:
            raise ValueError("max_tokens must be an integer greater than or equal to min_tokens")
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT timestamp, function_name, prompt_tokens, completion_tokens, 
                           total_tokens, cost
                    FROM token_logs
                    WHERE total_tokens BETWEEN ? AND ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (min_tokens, max_tokens, limit))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Database error when retrieving logs by token range: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error when retrieving logs by token range: {e}")
            raise
    
    def get_logs_by_cost_range(self, min_cost, max_cost, limit=100):
        """Retrieve logs with cost within a specific range."""
        # Validate parameters
        if not isinstance(min_cost, (int, float)) or min_cost < 0:
            raise ValueError("min_cost must be a non-negative number")
        if not isinstance(max_cost, (int, float)) or max_cost < min_cost:
            raise ValueError("max_cost must be a number greater than or equal to min_cost")
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT timestamp, function_name, prompt_tokens, completion_tokens, 
                           total_tokens, cost
                    FROM token_logs
                    WHERE cost BETWEEN ? AND ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (min_cost, max_cost, limit))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Database error when retrieving logs by cost range: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error when retrieving logs by cost range: {e}")
            raise
    
    def get_unique_functions(self):
        """Retrieve a list of unique function names in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT function_name
                    FROM token_logs
                    ORDER BY function_name
                ''')
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Database error when retrieving unique functions: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error when retrieving unique functions: {e}")
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
    
    def get_total_usage_by_function(self):
        """Calculate total token usage and cost grouped by function."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        function_name,
                        SUM(prompt_tokens) as total_prompt_tokens,
                        SUM(completion_tokens) as total_completion_tokens,
                        SUM(total_tokens) as total_tokens,
                        SUM(cost) as total_cost
                    FROM token_logs
                    GROUP BY function_name
                    ORDER BY total_tokens DESC
                ''')
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Database error when calculating total usage by function: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error when calculating total usage by function: {e}")
            raise
    
    def get_total_usage_by_date(self, start_date, end_date):
        """Calculate total token usage and cost for a specific date range."""
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
                    WHERE timestamp BETWEEN ? AND ?
                ''', (start_date, end_date))
                return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Database error when calculating total usage by date: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error when calculating total usage by date: {e}")
            raise 