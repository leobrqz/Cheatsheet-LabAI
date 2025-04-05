import sqlite3
from datetime import datetime
import json
import os
import stat
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import platform
import threading
from queue import Queue, Empty

from utils import validate_date_format
from formatters import LogFormatter, LogEntry
from query_builder import LogQueryBuilder
from logger import get_logger

# Get logger instance
logger = get_logger(__name__)

class DatabaseConnectionPool:
    def __init__(self, db_path: str, max_connections: int = 5):
        self.db_path = db_path
        self.pool: Queue = Queue(maxsize=max_connections)
        self._lock = threading.Lock()
        
        # Initialize pool with connections
        for _ in range(max_connections):
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                self.pool.put(conn)
            except Exception as e:
                logger.error(f"Failed to create database connection: {e}")
                raise
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool."""
        try:
            return self.pool.get(timeout=5)  # 5 second timeout
        except Empty:
            logger.error("Timeout waiting for database connection")
            raise TimeoutError("No database connection available")
    
    def return_connection(self, conn: sqlite3.Connection):
        """Return a connection to the pool."""
        try:
            self.pool.put(conn, timeout=5)
        except Exception as e:
            logger.error(f"Failed to return connection to pool: {e}")
            conn.close()
    
    def close_all(self):
        """Close all connections in the pool."""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except Empty:
                break
            except Exception as e:
                logger.error(f"Error closing connection: {e}")

class Database:
    def __init__(self, db_path="db/debug_logs.db"):
        """Initialize database connection and create tables if they don't exist."""
        self.db_path = db_path
        self._local = threading.local()
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Set appropriate file permissions based on OS
        self._set_permissions()
        
        # Initialize connection pool
        self.pool = DatabaseConnectionPool(db_path)
        
        self._create_tables()
    
    def _set_permissions(self):
        """Set appropriate permissions based on the operating system."""
        try:
            if platform.system() == 'Windows':
                # Windows doesn't use the same permission system
                return
            
            # Unix-like systems
            db_dir = os.path.dirname(self.db_path)
            os.chmod(db_dir, 0o700)  # Owner read/write/execute only
            if os.path.exists(self.db_path):
                os.chmod(self.db_path, 0o600)  # Owner read/write only
            
            logger.info(f"Set permissions for database at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to set permissions: {e}")
            # Don't raise the error as it's not critical
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection from the pool."""
        conn = None
        try:
            conn = self.pool.get_connection()
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                self.pool.return_connection(conn)
    
    def __del__(self):
        """Cleanup when the database instance is destroyed."""
        try:
            self.pool.close_all()
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
    
    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        try:
            with self._get_connection() as conn:
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
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def _validate_parameters(self, function_name: str, prompt_tokens: int, 
                           completion_tokens: int, total_tokens: int, 
                           cost: float, output: Optional[str] = None) -> bool:
        """Validate parameter types and values for database operations."""
        try:
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
            
            if len(function_name) > 100:
                raise ValueError("function_name is too long (max 100 characters)")
            
            return True
        except Exception as e:
            logger.error(f"Parameter validation error: {e}")
            raise
    
    def add_log(self, function_name: str, prompt_tokens: int, 
                completion_tokens: int, total_tokens: int, 
                cost: float, output: Optional[str] = None) -> None:
        """Add a new token usage log entry with optional output."""
        try:
            self._validate_parameters(function_name, prompt_tokens, 
                                   completion_tokens, total_tokens, cost, output)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO token_logs 
                    (timestamp, function_name, prompt_tokens, completion_tokens, 
                     total_tokens, cost, output)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (datetime.now().isoformat(), function_name, prompt_tokens, 
                     completion_tokens, total_tokens, cost, output))
                conn.commit()
                logger.info(f"Added log entry for function: {function_name}")
        except Exception as e:
            logger.error(f"Failed to add log entry: {e}")
            raise
    
    def _execute_query(self, query: str, params: tuple = (), 
                      limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results as a list of dictionaries."""
        try:
            if limit is not None:
                query += " LIMIT ?"
                params = params + (limit,)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve the most recent logs."""
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        
        return self._execute_query(
            "SELECT * FROM token_logs ORDER BY timestamp DESC",
            limit=limit
        )
    
    def get_logs_by_date_range(self, start_date: str, end_date: str, 
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve logs within a specific date range."""
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        
        start_date = validate_date_format(start_date)
        end_date = validate_date_format(end_date)
        
        return self._execute_query(
            "SELECT * FROM token_logs WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp DESC",
            (start_date, end_date),
            limit
        )
    
    def get_logs_by_function(self, function_name: str, 
                            limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve logs for a specific function."""
        if not isinstance(function_name, str):
            raise TypeError("function_name must be a string")
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        
        return self._execute_query(
            "SELECT * FROM token_logs WHERE function_name = ? ORDER BY timestamp DESC",
            (function_name,),
            limit
        )
    
    def get_logs_by_token_range(self, min_tokens: int, max_tokens: int, 
                               limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve logs within a specific token range."""
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        
        return self._execute_query(
            "SELECT * FROM token_logs WHERE total_tokens BETWEEN ? AND ? ORDER BY timestamp DESC",
            (min_tokens, max_tokens),
            limit
        )
    
    def get_logs_by_cost_range(self, min_cost: float, max_cost: float, 
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve logs within a specific cost range."""
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        
        return self._execute_query(
            "SELECT * FROM token_logs WHERE cost BETWEEN ? AND ? ORDER BY timestamp DESC",
            (min_cost, max_cost),
            limit
        )
    
    def get_unique_functions(self) -> List[str]:
        """Get list of unique function names."""
        return [row['function_name'] for row in self._execute_query(
            "SELECT DISTINCT function_name FROM token_logs ORDER BY function_name"
        )]
    
    def query_logs(self, query_builder: LogQueryBuilder, 
                  limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Execute a custom query using the query builder."""
        try:
            query, params = query_builder.build(limit)
            return self._execute_query(query, params)
        except Exception as e:
            logger.error(f"Custom query execution error: {e}")
            raise 