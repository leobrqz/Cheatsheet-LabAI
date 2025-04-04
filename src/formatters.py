from dataclasses import dataclass
from typing import List, Dict, Any
import logging
from logger import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

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
            return [[
                log['timestamp'],
                log['function_name'],
                log['prompt_tokens'],
                log['completion_tokens'],
                log['total_tokens'],
                log['cost']
            ] for log in logs]
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
        return f"""
### Usage Statistics
- **Total Prompt Tokens:** {stats['total_prompt_tokens']:,}
- **Total Completion Tokens:** {stats['total_completion_tokens']:,}
- **Total Tokens:** {stats['total_tokens']:,}
- **Total Cost:** ${stats['total_cost']:.4f}
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