from langchain_openai import ChatOpenAI
import re
from config import config
from langchain_community.callbacks.manager import get_openai_callback
from datetime import datetime
from singletons import OpenAIClient, DatabaseInstance
from typing import List, Dict, Any, Optional, Tuple
from logger import get_logger
import time
from functools import wraps
import backoff
import threading

# Get logger instance
logger = get_logger(__name__)

# Initialize database and OpenAI client
db = DatabaseInstance.get_instance()
llm = OpenAIClient.get_instance()

class TokenUsageTracker:
    _instance = None
    _lock = threading.Lock()
    _cache = {}
    _cache_lock = threading.Lock()
    _cache_ttl = 300  # 5 minutes cache TTL
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(TokenUsageTracker, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        with self._lock:
            if self._initialized:
                return
                
            self.db = DatabaseInstance.get_instance()
            self._initialized = True
    
    def _get_cache_key(self, method: str, *args, **kwargs) -> str:
        """Generate a cache key from method name and arguments."""
        key_parts = [method]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        return ":".join(key_parts)
    
    def _get_cached_result(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached result if it exists and is not expired."""
        with self._cache_lock:
            if cache_key in self._cache:
                timestamp, result = self._cache[cache_key]
                if time.time() - timestamp < self._cache_ttl:
                    return result
                del self._cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: List[Dict[str, Any]]) -> None:
        """Cache a result with current timestamp."""
        with self._cache_lock:
            self._cache[cache_key] = (time.time(), result)
    
    def add_log(self, function_name: str, prompt_tokens: int, 
                completion_tokens: int, total_tokens: int, 
                cost: float, output: Optional[str] = None) -> None:
        """Add a log entry to the database."""
        try:
            with self._lock:  # Ensure thread-safe log addition
                self.db.add_log(function_name, prompt_tokens, completion_tokens, 
                              total_tokens, cost, output)
                # Invalidate relevant caches
                with self._cache_lock:
                    self._cache.clear()  # Simple invalidation strategy
        except Exception as e:
            logger.error(f"Failed to add log entry: {e}")
            raise
    
    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs from database with caching."""
        cache_key = self._get_cache_key("get_logs", limit=limit)
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
            
        try:
            result = self.db.get_logs(limit)
            self._cache_result(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"Failed to retrieve logs: {e}")
            raise
    
    def get_logs_by_date_range(self, start_date: str, end_date: str, 
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs from database filtered by date range with caching."""
        cache_key = self._get_cache_key("get_logs_by_date_range", 
                                      start_date=start_date, 
                                      end_date=end_date, 
                                      limit=limit)
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
            
        try:
            result = self.db.get_logs_by_date_range(start_date, end_date, limit)
            self._cache_result(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"Failed to retrieve logs by date range: {e}")
            raise
    
    def get_logs_by_function(self, function_name: str, 
                            limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs from database filtered by function name with caching."""
        cache_key = self._get_cache_key("get_logs_by_function", 
                                      function_name=function_name, 
                                      limit=limit)
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
            
        try:
            result = self.db.get_logs_by_function(function_name, limit)
            self._cache_result(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"Failed to retrieve logs by function: {e}")
            raise
    
    def get_logs_by_token_range(self, min_tokens: int, max_tokens: int, 
                               limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs from database filtered by token range with caching."""
        cache_key = self._get_cache_key("get_logs_by_token_range", 
                                      min_tokens=min_tokens, 
                                      max_tokens=max_tokens, 
                                      limit=limit)
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
            
        try:
            result = self.db.get_logs_by_token_range(min_tokens, max_tokens, limit)
            self._cache_result(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"Failed to retrieve logs by token range: {e}")
            raise
    
    def get_logs_by_cost_range(self, min_cost: float, max_cost: float, 
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs from database filtered by cost range with caching."""
        cache_key = self._get_cache_key("get_logs_by_cost_range", 
                                      min_cost=min_cost, 
                                      max_cost=max_cost, 
                                      limit=limit)
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
            
        try:
            result = self.db.get_logs_by_cost_range(min_cost, max_cost, limit)
            self._cache_result(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"Failed to retrieve logs by cost range: {e}")
            raise
    
    def get_unique_functions(self) -> List[str]:
        """Get list of unique function names from database with caching."""
        cache_key = self._get_cache_key("get_unique_functions")
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result
            
        try:
            result = self.db.get_unique_functions()
            self._cache_result(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"Failed to retrieve unique functions: {e}")
            raise

# Create global token tracker instance
token_tracker = TokenUsageTracker()

class RateLimiter:
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.calls = []
        self._lock = threading.Lock()  # Add thread lock
        self._cleanup_interval = 60  # Cleanup interval in seconds
        self._last_cleanup = time.time()
    
    def _cleanup_old_calls(self):
        """Clean up calls older than 1 minute."""
        now = time.time()
        if now - self._last_cleanup >= self._cleanup_interval:
            with self._lock:
                self.calls = [call for call in self.calls if now - call < 60]
                self._last_cleanup = now
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        with self._lock:  # Use lock for thread safety
            now = time.time()
            self._cleanup_old_calls()
            
            if len(self.calls) >= self.calls_per_minute:
                # Wait until oldest call is 1 minute old
                sleep_time = 60 - (now - self.calls[0])
                if sleep_time > 0:
                    logger.debug(f"Rate limit reached, waiting {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
            
            self.calls.append(now)
    
    def __enter__(self):
        """Support for context manager protocol."""
        self.wait_if_needed()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support for context manager protocol."""
        # Clean up any remaining calls
        self._cleanup_old_calls()
        # Log any errors that occurred
        if exc_type is not None:
            logger.error(f"Error in rate limiter: {exc_val}")
            return False  # Re-raise the exception
        return True  # Exception was handled

# Create rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(func):
    """Decorator to apply rate limiting to API calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        rate_limiter.wait_if_needed()
        return func(*args, **kwargs)
    return wrapper

class APIError(Exception):
    """Base class for API-related errors."""
    pass

class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    pass

class TokenLimitError(APIError):
    """Raised when token limit is exceeded."""
    pass

class ContentFilterError(APIError):
    """Raised when content is filtered by OpenAI."""
    pass

@backoff.on_exception(
    backoff.expo,
    (RateLimitError, TokenLimitError),
    max_tries=3
)
@rate_limit
def make_api_call(func):
    """Decorator to handle API calls with rate limiting and error handling."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            with get_openai_callback() as cb:
                result = func(*args, **kwargs)
                # Log token usage
                logger.info(f"API call completed - Tokens: {cb.total_tokens}, Cost: ${cb.total_cost}")
                # Add to token tracker
                token_tracker.add_log(
                    function_name=func.__name__,
                    prompt_tokens=cb.prompt_tokens,
                    completion_tokens=cb.completion_tokens,
                    total_tokens=cb.total_tokens,
                    cost=cb.total_cost
                )
                return result
        except Exception as e:
            logger.error(f"API call failed in {func.__name__}: {str(e)}")
            raise
    return wrapper

def fix_markdown_formatting(text: str) -> str:
    """Fix common markdown formatting issues."""
    # Remove extra newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Fix code block formatting
    text = re.sub(r'```(\w+)?\n', r'```\1\n', text)
    
    # Fix list formatting
    text = re.sub(r'^\s*[-*]\s+', '- ', text, flags=re.MULTILINE)
    
    # Fix heading formatting
    text = re.sub(r'^(#{1,6})\s*([^#\n]+)', r'\1 \2', text, flags=re.MULTILINE)
    
    # Fix code blocks without language specification
    text = re.sub(r'```\s*\n', '```python\n', text)
    
    # Fix headings without proper spacing
    text = re.sub(r'([^\n])\n(#+)', r'\1\n\n\2', text)
    
    # Fix lists without proper spacing
    text = re.sub(r'([^\n])\n(\d+\.|\*)', r'\1\n\n\2', text)
    
    # Fix nested lists without proper indentation
    text = re.sub(r'(\n\d+\.|\n\*)\s+([^\s])', r'\1  \2', text)
    
    # Fix code blocks without proper closing
    text = re.sub(r'```([^\n]*)\n(.*?)(?=\n\n|\Z)', lambda m: f'```{m.group(1)}\n{m.group(2)}\n```', text, flags=re.DOTALL)
    
    return text.strip()

class LogFormatter:
    """Utility class for formatting log data."""
    
    @staticmethod
    def calculate_totals(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate total tokens and cost from logs."""
        total_tokens = sum(log['total_tokens'] for log in logs)
        total_cost = sum(log['cost'] for log in logs)
        return {
            'total_tokens': total_tokens,
            'total_cost': total_cost
        }
    
    @staticmethod
    def format_log_entry(log: Dict[str, Any]) -> str:
        """Format a single log entry as a string."""
        return (
            f"Function: {log['function_name']}\n"
            f"Tokens: {log['total_tokens']}\n"
            f"Cost: ${log['cost']:.4f}\n"
            f"Timestamp: {log['timestamp']}"
        )
    
    @staticmethod
    def format_logs_as_table(logs: List[Dict[str, Any]]) -> str:
        """Format logs as a markdown table."""
        if not logs:
            return "No logs found."
        
        # Create table header
        table = "| Function | Tokens | Cost | Timestamp |\n"
        table += "|----------|--------|------|-----------|\n"
        
        # Add rows
        for log in logs:
            table += (
                f"| {log['function_name']} | "
                f"{log['total_tokens']} | "
                f"${log['cost']:.4f} | "
                f"{log['timestamp']} |\n"
            )
        
        return table

def construct_instruction_prompt():
    """Constructs the system instruction message for the LLM."""
    return ("""
    You are a cheatsheet generator that creates concise, well-structured content based on user inputs.
    
    Core Requirements:
    - Create concise, informative content tailored to user parameters
    - Ensure well-structured, readable output
    - Maintain relevance to prompt, theme, and subject
    - Match complexity level and target audience
    - Always include references or recommendations for further reading
    
    Parameter Guide:
    - Prompt: User's specific request
    - Theme: Overall topic area
    - Subject: Specific focus within theme
    - Exemplified: Include examples only if requested
    - Complexity: Detail depth (Basic/Intermediate/Advanced)
    - Audience: Target knowledge level (Student/Intermediate/Professional)
    - Style: Tone and presentation approach
    - Output Format: Presentation format (markdown/plain text)
    
    Template Usage:
    Follow the provided structure template to organize content.
    
    MARKDOWN FORMATTING:
    1. Use proper heading levels (## main, ### sub)
    2. Format code blocks with triple backticks and language: ```python
    3. Add blank lines between sections
    4. Use consistent list formatting and indentation
    5. Maintain proper nested list structure
    6. Wrap code examples in proper blocks
    7. Apply bold (**) and italic (*) consistently
    8. Escape special characters in code blocks
    """)

def summarize_inputs(prompt, theme, subject, complexity, audience):
    """Summarizes the input parameters."""
    summary_prompt = (
        f"""
        Summarize these cheatsheet parameters:
        - Prompt: {prompt}
        - Theme: {theme}
        - Subject: {subject}
        - Complexity: {complexity}
        - Audience: {audience}
        
        Create a concise, structured summary that captures essential elements for the cheatsheet.
        This is NOT the cheatsheet itself, but a refined version of the user input.
        
        Adjust detail levels based on:
        - Higher complexity: Focus on deeper insights and advanced technical points
        - Lower complexity: Emphasize key concepts with practical explanations
        - Audience level: Ensure accessibility for beginners or depth for experts
        """
    )
    llm = OpenAIClient.get_instance()
    response = llm.invoke([("human", summary_prompt)])
    return response.content

def construct_input_prompt(prompt, theme, subject, complexity, audience, style, exemplified, template_name):
    """Constructs the user input message for the LLM."""
    summarized_input = summarize_inputs(prompt, theme, subject, complexity, audience)
    
    # Get template structure if selected
    structure = ""
    if template_name and template_name != "Custom":
        template = config.get_templates().get(template_name)
        if template:
            structure = template["structure"]
    
    return f"""
    Create a cheatsheet based on:
    - Summarized Input: {summarized_input}

    Style Parameters:
    - Exemplified: {exemplified}
    - Complexity: {complexity}
    - Audience: {audience}
    - Style: {style}
    
    Structure:
    {structure}
    
    FORMATTING REQUIREMENTS:
    1. Use proper heading levels (## main, ### sub)
    2. Format code blocks with language spec (```python)
    3. Add spacing between sections
    4. Use consistent list formatting
    """

@make_api_call
def generate_cheatsheet(prompt, theme, subject, template_name, style, exemplified, complexity, audience, enforce_formatting):
    """Generate a cheatsheet based on the given parameters."""
    try:
        # Get template from config
        template = config.get_instance().get_templates().get(template_name, {})
        
        # Construct the full prompt
        full_prompt = f"""Create a cheatsheet about {subject} with the following parameters:
        - Theme: {theme}
        - Style: {style}
        - Complexity: {complexity}
        - Target Audience: {audience}
        - Include Examples: {exemplified}
        
        Additional Instructions:
        {prompt}
        
        Template Structure:
        {template.get('structure', '')}
        
        Format the output in markdown."""
        
        # Make the API call
        response = llm.invoke([("human", full_prompt)])
        
        # Format the response if requested
        if enforce_formatting:
            response = fix_markdown_formatting(response.content)
        else:
            response = response.content
            
        return response, response
    except Exception as e:
        logger.error(f"Error in generate_cheatsheet: {str(e)}")
        error_message = f"Error generating cheatsheet: {str(e)}"
        return error_message, error_message

def summarize_content_for_features(content):
    """Creates a concise summary of the cheatsheet content for use in other features.
    This helps reduce token usage when generating quizzes, flashcards, etc."""
    summary_prompt = f"""
    Create a concise summary of the following cheatsheet content that captures all key concepts and information.
    This summary will be used to generate other learning materials, so it needs to be comprehensive yet concise.
    
    Content:
    {content}
    
    Guidelines:
    - Extract the most important concepts, definitions, and information
    - Maintain the hierarchical structure of the content
    - Include key examples and code snippets if present
    - Keep the summary to about 30-40% of the original length
    - Preserve markdown formatting for proper rendering
    
    Format the summary in markdown with appropriate headings and structure.
    """
    
    llm = OpenAIClient.get_instance()
    response = llm.invoke([("human", summary_prompt)])
    return response.content

@make_api_call
def generate_quiz(content, quiz_type, difficulty, count):
    """Generate a quiz based on the content."""
    try:
        # Validate quiz type and difficulty
        valid_types = ["multiple_choice", "true_false", "short_answer"]
        valid_difficulties = ["easy", "medium", "hard", "intermediate", "advanced"]
        
        if quiz_type not in valid_types:
            raise ValueError(f"Invalid quiz type. Must be one of: {', '.join(valid_types)}")
        
        # Map intermediate/advanced to medium/hard
        difficulty_map = {
            "intermediate": "medium",
            "advanced": "hard"
        }
        normalized_difficulty = difficulty_map.get(difficulty.lower(), difficulty.lower())
        
        if normalized_difficulty not in ["easy", "medium", "hard"]:
            raise ValueError(f"Invalid difficulty. Must be one of: easy, medium, hard, intermediate, advanced")
        
        # Construct the prompt
        prompt = f"""Create a {normalized_difficulty} difficulty {quiz_type} quiz with {count} questions based on this content:
        
        {content}
        
        Format each question as:
        Q: [Question text]
        A: [Answer]
        E: [Explanation]
        
        For multiple choice, include options A, B, C, D.
        For true/false, just state True or False.
        For short answer, provide a brief expected answer."""
        
        # Make the API call
        response = llm.invoke([("human", prompt)])
        return fix_markdown_formatting(response.content)
    except Exception as e:
        logger.error(f"Error in generate_quiz: {str(e)}")
        return f"Error generating quiz: {str(e)}"

@make_api_call
def generate_flashcards(content, count):
    """Generate flashcards based on the content."""
    try:
        # Validate input
        if count < 1 or count > 20:
            raise ValueError("Flashcard count must be between 1 and 20")
        
        # Construct the prompt
        prompt = f"""Create {count} flashcards based on this content:
        
        {content}
        
        Format each flashcard as:
        Front: [Question or concept]
        Back: [Answer or explanation]
        
        Make the flashcards concise and focused on key concepts."""
        
        # Make the API call
        response = llm.invoke([("human", prompt)])
        return fix_markdown_formatting(response.content)
    except Exception as e:
        logger.error(f"Error in generate_flashcards: {str(e)}")
        return f"Error generating flashcards: {str(e)}"

@make_api_call
def generate_practice_problems(content, problem_type, count):
    """Generate practice problems based on the content."""
    try:
        # Validate problem type
        valid_types = ["coding", "math", "concept", "exercises"]
        if problem_type.lower() not in valid_types:
            raise ValueError(f"Invalid problem type. Must be one of: {', '.join(valid_types)}")
        
        # Map exercises to concept
        problem_type_map = {
            "exercises": "concept"
        }
        normalized_type = problem_type_map.get(problem_type.lower(), problem_type.lower())
        
        # Construct the prompt
        prompt = f"""Create {count} {normalized_type} practice problems based on this content:
        
        {content}
        
        Format each problem as:
        Problem: [Problem statement]
        Solution: [Detailed solution]
        Explanation: [Key concepts and reasoning]
        
        Make the problems challenging but solvable."""
        
        # Make the API call
        response = llm.invoke([("human", prompt)])
        return fix_markdown_formatting(response.content)
    except Exception as e:
        logger.error(f"Error in generate_practice_problems: {str(e)}")
        return f"Error generating practice problems: {str(e)}"

@make_api_call
def generate_summary(content, level, focus):
    """Generate a summary based on the content."""
    try:
        # Validate summary level and focus
        valid_levels = ["brief", "detailed", "comprehensive"]
        valid_focus = ["concepts", "examples", "key_points"]
        
        if level not in valid_levels:
            raise ValueError(f"Invalid summary level. Must be one of: {', '.join(valid_levels)}")
        if focus not in valid_focus:
            raise ValueError(f"Invalid focus area. Must be one of: {', '.join(valid_focus)}")
        
        # Construct the prompt
        prompt = f"""Create a {level} summary of this content, focusing on {focus}:
        
        {content}
        
        Format the summary in markdown with appropriate headings and sections."""
        
        # Make the API call
        response = llm.invoke([("human", prompt)])
        return fix_markdown_formatting(response.content)
    except Exception as e:
        logger.error(f"Error in generate_summary: {str(e)}")
        return f"Error generating summary: {str(e)}"

# Log-related functions that use the token tracker
def get_token_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """Get logs from database."""
    return token_tracker.get_logs(limit)

def get_token_logs_by_date_range(start_date: str, end_date: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get logs from database filtered by date range."""
    return token_tracker.get_logs_by_date_range(start_date, end_date, limit)

def get_token_logs_by_function(function_name: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get logs from database filtered by function name."""
    return token_tracker.get_logs_by_function(function_name, limit)

def get_token_logs_by_token_range(min_tokens: int, max_tokens: int, limit: int = 100) -> List[Dict[str, Any]]:
    """Get logs from database filtered by token range."""
    return token_tracker.get_logs_by_token_range(min_tokens, max_tokens, limit)

def get_token_logs_by_cost_range(min_cost: float, max_cost: float, limit: int = 100) -> List[Dict[str, Any]]:
    """Get logs from database filtered by cost range."""
    return token_tracker.get_logs_by_cost_range(min_cost, max_cost, limit)

def get_unique_functions() -> List[str]:
    """Get list of unique function names from database."""
    return token_tracker.get_unique_functions()

def calculate_total_usage() -> Dict[str, Any]:
    """Calculate total token usage and cost."""
    logs = get_token_logs()
    return LogFormatter.calculate_totals(logs)

def calculate_total_usage_by_function() -> Dict[str, Dict[str, Any]]:
    """Calculate total token usage and cost by function."""
    logs = get_token_logs()
    function_usage = {}
    
    for log in logs:
        function_name = log['function_name']
        if function_name not in function_usage:
            function_usage[function_name] = {
                'total_tokens': 0,
                'total_cost': 0.0
            }
        function_usage[function_name]['total_tokens'] += log['total_tokens']
        function_usage[function_name]['total_cost'] += log['cost']
    
    return function_usage

def calculate_total_usage_by_date(start_date: str, end_date: str) -> Dict[str, Any]:
    """Calculate total token usage and cost for a date range."""
    logs = get_token_logs_by_date_range(start_date, end_date)
    return LogFormatter.calculate_totals(logs) 