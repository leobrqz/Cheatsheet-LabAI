from langchain_openai import ChatOpenAI
import re
from config import API_KEY, MODEL_NAME, TEMPERATURE, TEMPLATES
from langchain_community.callbacks.manager import get_openai_callback
from datetime import datetime
from database import Database

# Initialize database
db = Database()

class TokenUsageTracker:
    def __init__(self):
        self.logs = []
    
    def add_log(self, function_name, prompt_tokens, completion_tokens, total_tokens, cost, output=None):
        """Add a log entry to both memory and database."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'function_name': function_name,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': total_tokens,
            'cost': cost
        }
        self.logs.append(log_entry)
        # Also store in database with output
        db.add_log(function_name, prompt_tokens, completion_tokens, total_tokens, cost, output)
    
    def get_logs(self):
        """Get logs from both memory and database."""
        # Get logs from database
        db_logs = db.get_logs()
        # Update memory logs with database logs
        self.logs = [{
            'timestamp': log[0],
            'function_name': log[1],
            'prompt_tokens': log[2],
            'completion_tokens': log[3],
            'total_tokens': log[4],
            'cost': log[5]
        } for log in db_logs]
        return self.logs

# Create global token tracker instance
token_tracker = TokenUsageTracker()

# Initialize OpenAI client
llm = ChatOpenAI(model=MODEL_NAME, api_key=API_KEY, temperature=TEMPERATURE)

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
        template = TEMPLATES.get(template_name)
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

def generate_cheatsheet(prompt, theme, subject, template_name, style, exemplified, complexity, audience, enforce_formatting):
    """Generates a cheatsheet response based on user inputs."""
    with get_openai_callback() as cb:
        system_message = construct_instruction_prompt()
        user_message = construct_input_prompt(prompt, theme, subject, complexity, audience, style, exemplified, template_name)
        
        messages = [
            ("system", system_message),
            ("human", user_message)
        ]
        
        response = llm.invoke(messages)
        
        # Track token usage
        token_tracker.add_log('generate_cheatsheet', cb.prompt_tokens, cb.completion_tokens, cb.total_tokens, cb.total_cost, response.content)
        
        # Fix markdown formatting issues if enabled
        if enforce_formatting:
            formatted_response = fix_markdown_formatting(response.content)
        else:
            formatted_response = response.content
        
        return formatted_response, formatted_response

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

def generate_quiz(content, quiz_type, difficulty, count):
    """Generates a quiz based on the summarized cheatsheet content."""
    with get_openai_callback() as cb:
        quiz_prompt = f"""
        Based on the following summarized cheatsheet content, generate a {quiz_type} quiz with {count} questions at {difficulty} difficulty level.
        
        Content:
        {content}
        
        For multiple choice questions, provide 4 options with one correct answer.
        For fill-in-the-blank questions, provide the sentence with a blank and the correct answer.
        For true/false questions, provide the statement and whether it's true or false.
        
        Format the quiz in markdown with the following structure:
        # Quiz: [Topic]
        
        ## Question 1
        [Question text]
        
        **Options:**
        - A) [Option A]
        - B) [Option B]
        - C) [Option C]
        - D) [Option D]
        
        **Correct Answer:** [Letter of correct option]
        
        **Explanation:** [Brief explanation of why this is correct]
        
        [Repeat for all questions]
        
        ## Answer Key
        1. [Letter]
        2. [Letter]
        ...
        """
        
        response = llm.invoke([("human", quiz_prompt)])
        
        # Track token usage
        token_tracker.add_log('generate_quiz', cb.prompt_tokens, cb.completion_tokens, cb.total_tokens, cb.total_cost, response.content)
        
        return response.content, response.content

def generate_flashcards(content, count):
    """Generates flashcards based on the summarized cheatsheet content."""
    with get_openai_callback() as cb:
        flashcard_prompt = f"""
        Based on the following summarized cheatsheet content, generate exactly {count} flashcards.
        Each flashcard should cover a key concept from the content.
        
        Content:
        {content}
        
        Format the flashcards in markdown with the following structure:
        # Flashcards: Key Concepts ({count} cards)

        ## Card 1
        **Question:** [Question text]
        
        **Answer:** [Answer text]

        ## Card 2
        **Question:** [Question text]
        
        **Answer:** [Answer text]

        [Continue for exactly {count} cards]
        
        Make each flashcard focused on testing understanding of a specific concept.
        Ensure questions are clear and answers are concise but complete.
        Number each card sequentially.
        Add a blank line between cards for better readability.
        """
        
        response = llm.invoke([("human", flashcard_prompt)])
        
        # Track token usage
        token_tracker.add_log('generate_flashcards', cb.prompt_tokens, cb.completion_tokens, cb.total_tokens, cb.total_cost, response.content)
        
        return response.content, response.content

def generate_practice_problems(content, problem_type, count):
    """Generates practice problems based on the summarized cheatsheet content."""
    with get_openai_callback() as cb:
        problem_prompt = f"""
        Based on the following summarized cheatsheet content, generate {count} {problem_type} practice problems.
        
        Content:
        {content}
        
        Format the problems in markdown with the following structure:
        # Practice Problems: [Topic]
        
        ## Problem 1
        [Problem description]
        
        **Solution:**
        [Solution details]
        
        [Repeat for all problems]
        
        Make sure the problems are challenging but solvable based on the content provided.
        For code challenges, include sample code and expected output.
        """
        
        response = llm.invoke([("human", problem_prompt)])
        
        # Track token usage
        token_tracker.add_log('generate_practice_problems', cb.prompt_tokens, cb.completion_tokens, cb.total_tokens, cb.total_cost, response.content)
        
        return response.content, response.content

def generate_summary(content, level, focus):
    """Generates a summary of the cheatsheet content."""
    with get_openai_callback() as cb:
        summary_prompt = f"""
        Create a {level} summary of the following content, focusing on {focus}.
        
        Content:
        {content}
        
        Guidelines based on level:
        - tldr: 2-3 sentences capturing the most important points
        - detailed: Key points with brief explanations (1-2 paragraphs)
        - comprehensive: Full analysis with examples and connections
        
        Focus areas based on selection:
        - concepts: Core theories and principles
        - examples: Practical applications and cases
        - applications: Real-world usage and implementation
        
        Format the summary in markdown with appropriate headings and structure.
        Use bullet points for clarity when appropriate.
        Include specific examples from the content when relevant.
        """
        
        response = llm.invoke([("human", summary_prompt)])
        
        # Track token usage
        token_tracker.add_log('generate_summary', cb.prompt_tokens, cb.completion_tokens, cb.total_tokens, cb.total_cost, response.content)
        
        return response.content, response.content

def get_token_logs():
    """Returns the current token usage logs."""
    return token_tracker.get_logs()

def calculate_total_usage():
    """Calculate total token usage and cost from database."""
    total_prompt_tokens, total_completion_tokens, total_tokens, total_cost = db.get_total_usage()
    return {
        'total_prompt_tokens': total_prompt_tokens or 0,
        'total_completion_tokens': total_completion_tokens or 0,
        'total_tokens': total_tokens or 0,
        'total_cost': total_cost or 0
    } 