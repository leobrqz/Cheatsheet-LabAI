from typing import List, Optional
from datetime import datetime
import logging
from logger import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

class LogQueryBuilder:
    def __init__(self):
        self.conditions: List[str] = []
        self.parameters: List[any] = []
    
    def add_date_range(self, start_date: str, end_date: str) -> 'LogQueryBuilder':
        """
        Adds date range filter to the query.
        
        Args:
            start_date: Start date in ISO format
            end_date: End date in ISO format
            
        Returns:
            self for method chaining
        """
        self.conditions.append("timestamp BETWEEN ? AND ?")
        self.parameters.extend([start_date, end_date])
        return self
    
    def add_function_filter(self, function_name: str) -> 'LogQueryBuilder':
        """
        Adds function name filter to the query.
        
        Args:
            function_name: Name of the function to filter by
            
        Returns:
            self for method chaining
        """
        self.conditions.append("function_name = ?")
        self.parameters.append(function_name)
        return self
    
    def add_token_range(self, min_tokens: int, max_tokens: int) -> 'LogQueryBuilder':
        """
        Adds token range filter to the query.
        
        Args:
            min_tokens: Minimum number of tokens
            max_tokens: Maximum number of tokens
            
        Returns:
            self for method chaining
        """
        self.conditions.append("total_tokens BETWEEN ? AND ?")
        self.parameters.extend([min_tokens, max_tokens])
        return self
    
    def add_cost_range(self, min_cost: float, max_cost: float) -> 'LogQueryBuilder':
        """
        Adds cost range filter to the query.
        
        Args:
            min_cost: Minimum cost
            max_cost: Maximum cost
            
        Returns:
            self for method chaining
        """
        self.conditions.append("cost BETWEEN ? AND ?")
        self.parameters.extend([min_cost, max_cost])
        return self
    
    def build(self, limit: Optional[int] = None) -> tuple[str, List[any]]:
        """
        Builds the final SQL query.
        
        Args:
            limit: Optional limit for the number of results
            
        Returns:
            Tuple of (SQL query, parameters)
        """
        query = "SELECT timestamp, function_name, prompt_tokens, completion_tokens, total_tokens, cost, output FROM token_logs"
        
        if self.conditions:
            query += " WHERE " + " AND ".join(self.conditions)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += " LIMIT ?"
            self.parameters.append(limit)
        
        return query, self.parameters 