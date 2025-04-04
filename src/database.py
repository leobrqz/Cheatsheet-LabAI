import sqlite3
from datetime import datetime
import json
import os

class Database:
    def __init__(self, db_path="db/debug_logs.db"):
        """Initialize database connection and create tables if they don't exist."""
        self.db_path = db_path
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self._create_tables()
    
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
    
    def add_log(self, function_name, prompt_tokens, completion_tokens, total_tokens, cost, output=None):
        """Add a new token usage log entry with optional output."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO token_logs 
                (timestamp, function_name, prompt_tokens, completion_tokens, total_tokens, cost, output)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), function_name, prompt_tokens, 
                 completion_tokens, total_tokens, cost, output))
            conn.commit()
    
    def get_logs(self, limit=100):
        """Retrieve the most recent logs."""
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
    
    def get_total_usage(self):
        """Calculate total token usage and cost."""
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