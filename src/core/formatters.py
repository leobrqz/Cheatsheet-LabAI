from dataclasses import dataclass
from typing import List, Dict, Any, Union
from ..utils.logger import get_logger
from datetime import datetime

# Get logger instance
logger = get_logger(__name__)

@dataclass
class LogEntry:
    timestamp: str
    function_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    output: str = None

class LogFormatter:
    @staticmethod
    def format_for_display(logs: List[Dict[str, Any]]) -> List[List[Any]]:
        """
        Formats log entries for display in the UI.
        
        Args:
            logs: List of log dictionaries
            
        Returns:
            List of formatted log entries for display
        """
        try:
            formatted_logs = []
            for log in logs:
                # Handle timestamp formatting
                timestamp = log['timestamp']
                if isinstance(timestamp, (int, float)):
                    # Convert Unix timestamp to datetime
                    formatted_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(timestamp, datetime):
                    formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    # If it's already a string, try to parse it
                    try:
                        formatted_time = datetime.fromisoformat(str(timestamp)).strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        formatted_time = str(timestamp)  # Fallback to string representation
                
                formatted_logs.append([
                    formatted_time,
                    log['function_name'],
                    log['prompt_tokens'],
                    log['completion_tokens'],
                    log['total_tokens'],
                    f"${log['cost']:.4f}"
                ])
            return formatted_logs
        except KeyError as e:
            logger.error(f"Missing required field in log entry: {e}")
            return []
    
    @staticmethod
    def format_for_database(log_entry: Dict[str, Any]) -> LogEntry:
        """
        Formats log entry for database storage.
        
        Args:
            log_entry: Dictionary containing log data
            
        Returns:
            LogEntry object
        """
        try:
            return LogEntry(
                timestamp=log_entry['timestamp'],
                function_name=log_entry['function_name'],
                prompt_tokens=log_entry['prompt_tokens'],
                completion_tokens=log_entry['completion_tokens'],
                total_tokens=log_entry['total_tokens'],
                cost=log_entry['cost'],
                output=log_entry.get('output')
            )
        except KeyError as e:
            logger.error(f"Missing required field in log entry: {e}")
            raise ValueError(f"Missing required field: {e}")
    
    @staticmethod
    def format_stats(stats: Dict[str, Any]) -> str:
        """
        Formats usage statistics for display.
        
        Args:
            stats: Dictionary containing usage statistics
            
        Returns:
            Formatted markdown string
        """
        def format_number(num: Union[int, float]) -> str:
            if isinstance(num, int):
                return f"{num:,}"
            return f"{num:,.2f}"

        total_tokens = stats.get('total_tokens', 0)
        total_cost = stats.get('total_cost', 0)
        
        return f"""### Usage Overview
| Metric | Value |
|--------|-------|
| Total Tokens | {format_number(total_tokens)} |
| Total Cost | ${format_number(total_cost)} |
"""
    
    @staticmethod
    def calculate_totals(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate totals from a list of log entries.
        
        Args:
            logs: List of log dictionaries
            
        Returns:
            Dictionary containing total tokens and cost
        """
        return {
            'total_prompt_tokens': sum(log['prompt_tokens'] for log in logs),
            'total_completion_tokens': sum(log['completion_tokens'] for log in logs),
            'total_tokens': sum(log['total_tokens'] for log in logs),
            'total_cost': sum(log['cost'] for log in logs)
        } 