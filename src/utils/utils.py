import re
from datetime import datetime
from typing import Optional, Union, Tuple, List, Dict, Any
from src.utils.logger import get_logger

# Get logger instance
logger = get_logger(__name__)

# Common date formats
DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%d-%m-%Y %H:%M:%S",
    "%d/%m/%Y %H:%M:%S"
]

def validate_date(date_str: str, allow_time: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Validate a date string against multiple formats.
    
    Args:
        date_str: The date string to validate
        allow_time: Whether to allow time components in the date
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(date_str, str):
        return False, "Date string must be a string"
        
    date_str = date_str.strip()
    if not date_str:
        return False, "Date string cannot be empty"
        
    # Try each format
    for fmt in DATE_FORMATS:
        try:
            # Skip formats with time if not allowed
            if not allow_time and "%H" in fmt:
                continue
                
            dt = datetime.strptime(date_str, fmt)
            
            # Basic sanity checks
            if dt.year < 1900 or dt.year > 2100:
                return False, "Year must be between 1900 and 2100"
                
            return True, None
        except ValueError:
            continue
            
    return False, f"Invalid date format. Expected one of: {', '.join(DATE_FORMATS)}"

def parse_date(date_str: str, allow_time: bool = True) -> Optional[datetime]:
    """
    Parse a date string into a datetime object.
    
    Args:
        date_str: The date string to parse
        allow_time: Whether to allow time components in the date
        
    Returns:
        datetime object if successful, None otherwise
    """
    is_valid, error = validate_date(date_str, allow_time)
    if not is_valid:
        logger.warning(f"Failed to parse date: {error}")
        return None
        
    for fmt in DATE_FORMATS:
        try:
            # Skip formats with time if not allowed
            if not allow_time and "%H" in fmt:
                continue
                
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
            
    return None

def format_date(date_obj: Union[datetime, str], format_str: str = "%Y-%m-%d") -> Optional[str]:
    """
    Format a datetime object or string into a specified format.
    
    Args:
        date_obj: datetime object or date string
        format_str: Output format string
        
    Returns:
        Formatted date string if successful, None otherwise
    """
    try:
        if isinstance(date_obj, str):
            parsed_date = parse_date(date_obj)
            if parsed_date is None:
                return None
            date_obj = parsed_date
            
        return date_obj.strftime(format_str)
    except Exception as e:
        logger.error(f"Failed to format date: {e}")
        return None

def is_valid_date_range(start_date: str, end_date: str, allow_time: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Validate a date range.
    
    Args:
        start_date: Start date string
        end_date: End date string
        allow_time: Whether to allow time components in the dates
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate individual dates
    start_valid, start_error = validate_date(start_date, allow_time)
    if not start_valid:
        return False, f"Invalid start date: {start_error}"
        
    end_valid, end_error = validate_date(end_date, allow_time)
    if not end_valid:
        return False, f"Invalid end date: {end_error}"
        
    # Parse dates for range validation
    start_dt = parse_date(start_date, allow_time)
    end_dt = parse_date(end_date, allow_time)
    
    if start_dt is None or end_dt is None:
        return False, "Failed to parse dates for range validation"
        
    # Validate range
    if start_dt > end_dt:
        return False, "Start date must be before or equal to end date"
        
    return True, None

def validate_date_format(date_str: str) -> bool:
    """
    Validate date string format.
    
    Args:
        date_str: Date string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        try:
            datetime.fromisoformat(date_str)
            return True
        except ValueError:
            return False

def format_date_for_display(iso_date: str) -> str:
    """
    Formats ISO date string for display.
    
    Args:
        iso_date: ISO format date string
        
    Returns:
        Formatted date string (YYYY-MM-DD)
        
    Raises:
        ValueError: If the date string is invalid
    """
    try:
        date_obj = datetime.fromisoformat(iso_date)
        return date_obj.strftime("%Y-%m-%d")
    except ValueError as e:
        logger.error(f"Invalid ISO date format: {iso_date}")
        raise ValueError(f"Invalid ISO date format: {iso_date}. Error: {str(e)}")

def validate_numeric_range(min_val: float, max_val: float) -> bool:
    """
    Validate numeric range.
    
    Args:
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        if not isinstance(min_val, (int, float)) or not isinstance(max_val, (int, float)):
            return False
        return min_val <= max_val
    except Exception:
        return False

def validate_positive_integer(value: int) -> bool:
    """
    Validate if a value is a positive integer.
    
    Args:
        value: Value to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        return isinstance(value, int) and value > 0
    except Exception:
        return False 