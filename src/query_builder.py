from typing import List, Optional, Tuple, Any, Dict
from datetime import datetime
import re
from logger import get_logger
import backoff
from functools import wraps
from utils import validate_date_format, validate_numeric_range, validate_positive_integer

# Get logger instance
logger = get_logger(__name__)

def handle_query_errors(func):
    """Decorator to handle query builder errors with retries."""
    @wraps(func)
    @backoff.on_exception(
        backoff.expo,
        (QueryBuilderError, Exception),
        max_tries=3,
        max_time=30
    )
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except QueryBuilderError as e:
            logger.error(f"Query builder error in {func.__name__}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise QueryBuilderError(f"Unexpected error: {str(e)}")
    return wrapper

class QueryBuilderError(Exception):
    """Base exception class for query builder errors."""
    pass

class InvalidDateError(QueryBuilderError):
    """Exception raised for invalid date formats."""
    pass

class InvalidRangeError(QueryBuilderError):
    """Exception raised for invalid numeric ranges."""
    pass

class InvalidFunctionError(QueryBuilderError):
    """Exception raised for invalid function names."""
    pass

class LogQueryBuilder:
    def __init__(self):
        self.conditions: List[Dict[str, Any]] = []
    
    @handle_query_errors
    def _validate_date(self, date_str: str) -> bool:
        """
        Validate date string format.
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            InvalidDateError: If date format is invalid
        """
        if not validate_date_format(date_str):
            raise InvalidDateError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD format")
        return True
    
    @handle_query_errors
    def _validate_numeric_range(self, min_val: float, max_val: float) -> bool:
        """
        Validate numeric range.
        
        Args:
            min_val: Minimum value
            max_val: Maximum value
            
        Returns:
            True if valid
            
        Raises:
            InvalidRangeError: If range is invalid
        """
        if not validate_numeric_range(min_val, max_val):
            raise InvalidRangeError(f"Invalid range: min ({min_val}) must be less than or equal to max ({max_val})")
        return True
    
    @handle_query_errors
    def add_date_range(self, start_date: str, end_date: str) -> 'LogQueryBuilder':
        """Add date range filter to the query.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Self for method chaining
        """
        try:
            # Validate dates
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            if start_dt > end_dt:
                raise ValueError("Start date must be before end date")
            
            # Set start of day for start_dt (00:00:00)
            start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            # Set end of day for end_dt (23:59:59)
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Add conditions directly without nesting $and
            self.conditions.append({"timestamp": {"$gte": start_dt.timestamp()}})
            self.conditions.append({"timestamp": {"$lte": end_dt.timestamp()}})
            
            return self
        except ValueError as e:
            raise InvalidDateError(f"Invalid date format: {str(e)}")
    
    @handle_query_errors
    def add_function_filter(self, function_name: str) -> 'LogQueryBuilder':
        """Add function name filter to the query.
        
        Args:
            function_name: Name of the function to filter by
            
        Returns:
            Self for method chaining
        """
        if not function_name or not isinstance(function_name, str):
            raise InvalidFunctionError("Function name must be a non-empty string")
            
        self.conditions.append({"function_name": function_name})
        return self
    
    @handle_query_errors
    def add_token_range(self, min_tokens: int, max_tokens: int) -> 'LogQueryBuilder':
        """Add token range filter to the query.
        
        Args:
            min_tokens: Minimum number of tokens
            max_tokens: Maximum number of tokens
            
        Returns:
            Self for method chaining
        """
        if min_tokens < 0 or max_tokens < 0:
            raise InvalidRangeError("Token counts must be non-negative")
            
        if min_tokens > max_tokens:
            raise InvalidRangeError("Minimum tokens must be less than or equal to maximum tokens")
            
        # Add conditions directly without nesting $and
        self.conditions.append({"total_tokens": {"$gte": min_tokens}})
        self.conditions.append({"total_tokens": {"$lte": max_tokens}})
        return self
    
    @handle_query_errors
    def add_cost_range(self, min_cost: float, max_cost: float) -> 'LogQueryBuilder':
        """Add cost range filter to the query.
        
        Args:
            min_cost: Minimum cost
            max_cost: Maximum cost
            
        Returns:
            Self for method chaining
        """
        if min_cost < 0 or max_cost < 0:
            raise InvalidRangeError("Costs must be non-negative")
            
        if min_cost > max_cost:
            raise InvalidRangeError("Minimum cost must be less than or equal to maximum cost")
            
        # Add conditions directly without nesting $and
        self.conditions.append({"cost": {"$gte": min_cost}})
        self.conditions.append({"cost": {"$lte": max_cost}})
        return self
    
    @handle_query_errors
    def has_filters(self) -> bool:
        """
        Check if any filters are set.
        
        Returns:
            True if any filters are set, False otherwise
        """
        return bool(self.conditions)
    
    @handle_query_errors
    def set_limit(self, limit: int) -> 'LogQueryBuilder':
        """Set the limit for the number of results.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            Self for method chaining
        """
        if limit < 0:
            raise InvalidRangeError("Limit must be non-negative")
            
        self.limit = limit
        return self
    
    def get_query(self) -> Dict[str, Any]:
        """Get the query dictionary.
        
        Returns:
            Dictionary containing the query conditions and limit
        """
        query = {"$and": self.conditions} if self.conditions else {}
        if hasattr(self, 'limit'):
            query['$limit'] = self.limit
        return query
    
    def build(self) -> 'LogQueryBuilder':
        """Build the query and return the builder instance.
        
        Returns:
            Self for method chaining
        """
        return self
    
    def __str__(self) -> str:
        """String representation of the query builder."""
        return f"LogQueryBuilder(conditions={self.conditions})" 