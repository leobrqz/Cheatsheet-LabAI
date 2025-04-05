from langchain_openai import ChatOpenAI
import re
from config import config
from langchain_community.callbacks.manager import get_openai_callback
from datetime import datetime
from singletons import OpenAIClient, DatabaseInstance
from typing import List, Dict, Any, Optional
from logger import get_logger
import time
from functools import wraps
import backoff

# Get logger instance
logger = get_logger(__name__)

# Initialize database and OpenAI client
db = DatabaseInstance.get_instance()
llm = OpenAIClient.get_instance()

class RateLimiter:
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        # Remove calls older than 1 minute
        self.calls = [call for call in self.calls if now - call < 60]
        
        if len(self.calls) >= self.calls_per_minute:
            # Wait until oldest call is 1 minute old
            sleep_time = 60 - (now - self.calls[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, waiting {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        self.calls.append(now)

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
    """Decorator to handle API calls with retries and error handling."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            with get_openai_callback() as cb:
                result = func(*args, **kwargs)
                # Log token usage
                logger.info(f"API call completed - Tokens: {cb.total_tokens}, Cost: ${cb.total_cost}")
                return result
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg:
                raise RateLimitError("API rate limit exceeded")
            elif "maximum context length" in error_msg:
                raise TokenLimitError("Token limit exceeded")
            elif "content filter" in error_msg:
                raise ContentFilterError("Content filtered by OpenAI")
            else:
                logger.error(f"API call failed: {e}")
                raise APIError(f"API call failed: {e}")
    return wrapper

class TokenUsageTracker:
    def __init__(self):
        self.db = DatabaseInstance.get_instance()
    
    def add_log(self, function_name: str, prompt_tokens: int, 
                completion_tokens: int, total_tokens: int, 
                cost: float, output: Optional[str] = None) -> None:
        """Add a log entry to the database."""
        try:
            self.db.add_log(function_name, prompt_tokens, completion_tokens, 
                          total_tokens, cost, output)
        except Exception as e:
            logger.error(f"Failed to add log entry: {e}")
            raise
    
    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs from database."""
        try:
            return self.db.get_logs(limit)
        except Exception as e:
            logger.error(f"Failed to retrieve logs: {e}")
            raise
    
    def get_logs_by_date_range(self, start_date: str, end_date: str, 
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs from database filtered by date range."""
        try:
            return self.db.get_logs_by_date_range(start_date, end_date, limit)
        except Exception as e:
            logger.error(f"Failed to retrieve logs by date range: {e}")
            raise
    
    def get_logs_by_function(self, function_name: str, 
                            limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs from database filtered by function name."""
        try:
            return self.db.get_logs_by_function(function_name, limit)
        except Exception as e:
            logger.error(f"Failed to retrieve logs by function: {e}")
            raise
    
    def get_logs_by_token_range(self, min_tokens: int, max_tokens: int, 
                               limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs from database filtered by token range."""
        try:
            return self.db.get_logs_by_token_range(min_tokens, max_tokens, limit)
        except Exception as e:
            logger.error(f"Failed to retrieve logs by token range: {e}")
            raise
    
    def get_logs_by_cost_range(self, min_cost: float, max_cost: float, 
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs from database filtered by cost range."""
        try:
            return self.db.get_logs_by_cost_range(min_cost, max_cost, limit)
        except Exception as e:
            logger.error(f"Failed to retrieve logs by cost range: {e}")
            raise
    
    def get_unique_functions(self) -> List[str]:
        """Get list of unique function names from database."""
        try:
            return self.db.get_unique_functions()
        except Exception as e:
            logger.error(f"Failed to retrieve unique functions: {e}")
            raise

# Create global token tracker instance
token_tracker = TokenUsageTracker()

def fix_markdown_formatting(text):
    """Fixes common markdown formatting issues."""
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
    
    return text

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
    """Generate a cheatsheet with the given parameters."""
    try:
        # Get template from config
        template = config.get_templates().get(template_name)
        if not template:
            raise ValueError(f"Invalid template name: {template_name}")
        
        # Construct the prompt
        full_prompt = f"""
        Theme: {theme}
        Subject: {subject}
        Style: {style}
        Complexity: {complexity}
        Audience: {audience}
        Include Examples: {exemplified}
        
        {template['structure']}
        
        Additional Instructions:
        {prompt}
        """
        
        # Generate content using the correct method
        response = llm.invoke([("human", full_prompt)])
        
        # Fix formatting if requested
        if enforce_formatting:
            response = fix_markdown_formatting(response.content)
        else:
            response = response.content
        
        return response, response
    except Exception as e:
        logger.error(f"Failed to generate cheatsheet: {e}")
        raise

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
    
    response = llm.invoke([("human", summary_prompt)])
    return response.content

@make_api_call
def generate_quiz(content, quiz_type, difficulty, count):
    """Generate a quiz based on the content."""
    try:
        # Validate quiz type
        valid_types = config.get_learning_features()["Quiz Generation"]["types"]
        if quiz_type not in valid_types:
            raise ValueError(f"Invalid quiz type. Must be one of: {valid_types}")
        
        # Validate difficulty
        valid_difficulties = config.get_learning_features()["Quiz Generation"]["difficulty"]
        if difficulty not in valid_difficulties:
            raise ValueError(f"Invalid difficulty. Must be one of: {valid_difficulties}")
        
        prompt = f"""
        Generate a {difficulty} difficulty {quiz_type} quiz with {count} questions based on:
        
        {content}
        
        Format each question with:
        1. Question text
        2. Options (for multiple choice)
        3. Correct answer
        4. Explanation
        """
        
        response = llm.invoke([("human", prompt)])
        return response.content
    except Exception as e:
        logger.error(f"Failed to generate quiz: {e}")
        raise

@make_api_call
def generate_flashcards(content, count):
    """Generate flashcards based on the content."""
    try:
        prompt = f"""
        Generate {count} flashcards based on:
        
        {content}
        
        Format each flashcard as:
        Front: [Term or Question]
        Back: [Definition or Answer]
        """
        
        response = llm.invoke([("human", prompt)])
        return response.content
    except Exception as e:
        logger.error(f"Failed to generate flashcards: {e}")
        raise

@make_api_call
def generate_practice_problems(content, problem_type, count):
    """Generate practice problems based on the content."""
    try:
        # Validate problem type
        valid_types = config.get_learning_features()["Practice Problems"]["types"]
        if problem_type not in valid_types:
            raise ValueError(f"Invalid problem type. Must be one of: {valid_types}")
        
        prompt = f"""
        Generate {count} {problem_type} problems based on:
        
        {content}
        
        Format each problem with:
        1. Problem statement
        2. Solution
        3. Explanation
        """
        
        response = llm.invoke([("human", prompt)])
        return response.content
    except Exception as e:
        logger.error(f"Failed to generate practice problems: {e}")
        raise

@make_api_call
def generate_summary(content, level, focus):
    """Generate a summary of the content."""
    try:
        # Validate level
        valid_levels = config.get_ai_features()["Smart Summarization"]["levels"]
        if level not in valid_levels:
            raise ValueError(f"Invalid summary level. Must be one of: {valid_levels}")
        
        # Validate focus
        valid_focus = config.get_ai_features()["Smart Summarization"]["focus"]
        if focus not in valid_focus:
            raise ValueError(f"Invalid focus. Must be one of: {valid_focus}")
        
        prompt = f"""
        Generate a {level} summary focusing on {focus} from:
        
        {content}
        """
        
        response = llm.invoke([("human", prompt)])
        return response.content
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        raise

# Token usage tracking functions
def get_token_logs():
    """Get all token logs."""
    return token_tracker.get_logs()

def get_token_logs_by_date_range(start_date, end_date, limit=100):
    """Get token logs by date range."""
    return token_tracker.get_logs_by_date_range(start_date, end_date, limit)

def get_token_logs_by_function(function_name, limit=100):
    """Get token logs by function."""
    return token_tracker.get_logs_by_function(function_name, limit)

def get_token_logs_by_token_range(min_tokens, max_tokens, limit=100):
    """Get token logs by token range."""
    return token_tracker.get_logs_by_token_range(min_tokens, max_tokens, limit)

def get_token_logs_by_cost_range(min_cost, max_cost, limit=100):
    """Get token logs by cost range."""
    return token_tracker.get_logs_by_cost_range(min_cost, max_cost, limit)

def get_unique_functions():
    """Get list of unique functions."""
    return token_tracker.get_unique_functions()

def calculate_total_usage():
    """Calculate total token usage."""
    logs = token_tracker.get_logs()
    total_tokens = sum(log['total_tokens'] for log in logs)
    total_cost = sum(log['cost'] for log in logs)
    return {'total_tokens': total_tokens, 'total_cost': total_cost}

def calculate_total_usage_by_function():
    """Calculate total token usage by function."""
    logs = token_tracker.get_logs()
    usage_by_function = {}
    for log in logs:
        function_name = log['function_name']
        if function_name not in usage_by_function:
            usage_by_function[function_name] = {'total_tokens': 0, 'total_cost': 0}
        usage_by_function[function_name]['total_tokens'] += log['total_tokens']
        usage_by_function[function_name]['total_cost'] += log['cost']
    return usage_by_function

def calculate_total_usage_by_date(start_date, end_date):
    """Calculate total token usage by date range."""
    logs = token_tracker.get_logs_by_date_range(start_date, end_date)
    total_tokens = sum(log['total_tokens'] for log in logs)
    total_cost = sum(log['cost'] for log in logs)
    return {'total_tokens': total_tokens, 'total_cost': total_cost} 