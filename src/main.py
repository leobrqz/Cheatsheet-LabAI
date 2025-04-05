from dotenv import load_dotenv
import gradio as gr
from config import config
from generators import (
    generate_cheatsheet,
    generate_quiz,
    generate_flashcards,
    generate_practice_problems,
    generate_summary,
    summarize_content_for_features,
    get_token_logs,
    calculate_total_usage,
    get_token_logs_by_date_range,
    get_token_logs_by_function,
    get_token_logs_by_token_range,
    get_token_logs_by_cost_range,
    get_unique_functions,
    calculate_total_usage_by_function,
    calculate_total_usage_by_date
)
from utils import validate_date_format
from formatters import LogFormatter
from singletons import OpenAIClient, DatabaseInstance
from datetime import datetime, timedelta
from logger import get_logger
from typing import Union, List, Any

# Get logger instance
logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client and database
llm = OpenAIClient.get_instance()
db = DatabaseInstance.get_instance()

def generate_cheatsheet_and_summarize(prompt, theme, subject, template_name, style, exemplified, complexity, audience, enforce_formatting):
    """Generates a cheatsheet and creates a summary for use in other features."""
    try:
        cheatsheet, raw_cheatsheet = generate_cheatsheet(
            prompt, theme, subject, template_name, style,
            exemplified, complexity, audience, enforce_formatting
        )
        
        # Create a summary of the cheatsheet for use in other features
        summarized_content = summarize_content_for_features(cheatsheet)
        
        return cheatsheet, raw_cheatsheet, summarized_content
    except Exception as e:
        logger.error(f"Error generating cheatsheet: {str(e)}")
        error_message = f"Error: {str(e)}"
        return error_message, error_message, ""

def check_summarized_content(summarized_content, feature_name, generate_func, *args):
    """Checks if a cheatsheet has been generated before allowing feature generation."""
    if not summarized_content or summarized_content.strip() == "":
        return f"Please generate a cheatsheet first before using the {feature_name} feature.", ""
    
    result = generate_func(summarized_content, *args)
    if isinstance(result, tuple):
        return result
    return result, result  # Return both formatted and raw content if only one value is returned

def quiz_with_check(summarized_content, quiz_type, difficulty, quiz_count):
    """Checks if a cheatsheet has been generated before allowing quiz generation."""
    return check_summarized_content(summarized_content, "Quiz", generate_quiz, quiz_type, difficulty, quiz_count)

def flashcards_with_check(summarized_content, flashcard_count):
    """Checks if a cheatsheet has been generated before allowing flashcard generation."""
    if not summarized_content or summarized_content.strip() == "":
        return "Please generate a cheatsheet first before using the Flashcards feature.", ""
    
    result = generate_flashcards(summarized_content, flashcard_count)
    return result, result  # Return both formatted and raw content

def problems_with_check(summarized_content, problem_type, problem_count):
    """Checks if a cheatsheet has been generated before allowing problem generation."""
    return check_summarized_content(summarized_content, "Practice Problems", generate_practice_problems, problem_type, problem_count)

def summary_with_check(summarized_content, summary_level, summary_focus):
    """Checks if a cheatsheet has been generated before allowing summary generation."""
    return check_summarized_content(summarized_content, "Summary", generate_summary, summary_level, summary_focus)

def update_logs():
    """Update the logs display with the latest token usage data."""
    logs = get_token_logs()
    if not logs:
        return [], "No usage data available"
    
    # Use LogFormatter to format logs
    log_data = LogFormatter.format_for_display(logs)
    
    # Calculate totals
    totals = LogFormatter.calculate_totals(logs)
    stats = LogFormatter.format_stats(totals)
    
    return log_data, stats

def update_logs_by_date_range(start_date, end_date, limit):
    """Update the logs display with data filtered by date range."""
    try:
        # Validate dates
        start_date = validate_date_format(start_date)
        end_date = validate_date_format(end_date)
        
        logs = get_token_logs_by_date_range(start_date, end_date, limit)
        if not logs:
            return [], "No usage data available for the selected date range"
        
        # Use LogFormatter to format logs
        log_data = LogFormatter.format_for_display(logs)
        
        # Calculate totals for the date range
        totals = LogFormatter.calculate_totals(logs)
        stats = LogFormatter.format_stats(totals)
        
        return log_data, stats
    except ValueError as e:
        return [], f"Error: {str(e)}"

def update_logs_by_function(function_name, limit):
    """Update the logs display with data filtered by function."""
    logs = get_token_logs_by_function(function_name, limit)
    if not logs:
        return [], f"No usage data available for function: {function_name}"
    
    # Use LogFormatter to format logs
    log_data = LogFormatter.format_for_display(logs)
    
    # Calculate totals for the function
    totals = LogFormatter.calculate_totals(logs)
    stats = LogFormatter.format_stats(totals)
    
    return log_data, stats

def update_logs_by_token_range(min_tokens, max_tokens, limit):
    """Update the logs display with data filtered by token range."""
    logs = get_token_logs_by_token_range(min_tokens, max_tokens, limit)
    if not logs:
        return [], f"No usage data available for token range: {min_tokens} - {max_tokens}"
    
    # Use LogFormatter to format logs
    log_data = LogFormatter.format_for_display(logs)
    
    # Calculate totals for the token range
    totals = LogFormatter.calculate_totals(logs)
    stats = LogFormatter.format_stats(totals)
    
    return log_data, stats

def update_logs_by_cost_range(min_cost, max_cost, limit):
    """Update the logs display with data filtered by cost range."""
    logs = get_token_logs_by_cost_range(min_cost, max_cost, limit)
    if not logs:
        return [], f"No usage data available for cost range: ${min_cost:.4f} - ${max_cost:.4f}"
    
    # Use LogFormatter to format logs
    log_data = LogFormatter.format_for_display(logs)
    
    # Calculate totals for the cost range
    totals = LogFormatter.calculate_totals(logs)
    stats = LogFormatter.format_stats(totals)
    
    return log_data, stats

def validate_date_format(date_str: str) -> str:
    """Validate and format date string."""
    try:
        if not date_str:
            raise ValueError("Date cannot be empty")
        # Try to parse the date
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format. Please use YYYY-MM-DD format: {str(e)}")

def format_number(num: Union[int, float]) -> str:
    """Format number with thousands separator."""
    if isinstance(num, int):
        return f"{num:,}"
    return f"{num:,.2f}"

def update_usage_by_function() -> str:
    """Update the usage statistics grouped by function."""
    function_usage = calculate_total_usage_by_function()
    if not function_usage:
        return "No usage data available by function"
    
    # Calculate totals
    total_tokens = sum(stats['total_tokens'] for stats in function_usage.values())
    total_cost = sum(stats['total_cost'] for stats in function_usage.values())
    
    # Create a markdown table for function usage
    markdown = "### Usage Overview by Function\n\n"
    markdown += "| Function | Total Tokens | % of Total | Cost | % of Total |\n"
    markdown += "|----------|--------------|------------|------|------------|\n"
    
    # Sort functions by total tokens in descending order
    sorted_functions = sorted(
        function_usage.items(),
        key=lambda x: x[1]['total_tokens'],
        reverse=True
    )
    
    for function_name, stats in sorted_functions:
        token_percentage = (stats['total_tokens'] / total_tokens * 100) if total_tokens > 0 else 0
        cost_percentage = (stats['total_cost'] / total_cost * 100) if total_cost > 0 else 0
        
        markdown += (
            f"| {function_name} | "
            f"{format_number(stats['total_tokens'])} | "
            f"{token_percentage:.1f}% | "
            f"${format_number(stats['total_cost'])} | "
            f"{cost_percentage:.1f}% |\n"
        )
    
    # Add total row
    markdown += "|----------|--------------|------------|------|------------|\n"
    markdown += (
        f"| **Total** | "
        f"**{format_number(total_tokens)}** | "
        f"**100%** | "
        f"**${format_number(total_cost)}** | "
        f"**100%** |\n"
    )
    
    return markdown

def apply_combined_filters(start_date, end_date, function_name, min_tokens, max_tokens, min_cost, max_cost, limit):
    """Apply multiple filters to the logs."""
    try:
        # Create query builder
        query_builder = LogQueryBuilder()
        
        # Add date range if provided
        if start_date and end_date:
            start_date = validate_date_format(start_date)
            end_date = validate_date_format(end_date)
            query_builder.add_date_range(start_date, end_date)
        
        # Add function filter if provided
        if function_name:
            query_builder.add_function_filter(function_name)
        
        # Add token range if provided
        if min_tokens is not None and max_tokens is not None:
            query_builder.add_token_range(min_tokens, max_tokens)
        
        # Add cost range if provided
        if min_cost is not None and max_cost is not None:
            query_builder.add_cost_range(min_cost, max_cost)
        
        # Execute query using the correct method
        logs = get_token_logs()  # Get all logs first
        
        # Apply filters manually if any are set
        if query_builder.has_filters():
            filtered_logs = []
            for log in logs:
                if query_builder.matches_filters(log):
                    filtered_logs.append(log)
            logs = filtered_logs[:limit]  # Apply limit after filtering
        else:
            logs = logs[:limit]  # Apply limit to unfiltered logs
        
        if not logs:
            return [], "No logs match the selected criteria"
        
        # Format results
        log_data = LogFormatter.format_for_display(logs)
        
        # Calculate totals
        totals = LogFormatter.calculate_totals(logs)
        stats = LogFormatter.format_stats(totals)
        
        return log_data, stats
    except ValueError as e:
        return [], f"Error: {str(e)}"

class LogQueryBuilder:
    def __init__(self):
        self.conditions: List[str] = []
        self.parameters: List[Any] = []
        # Initialize filter storage
        self.date_range = None
        self.function_name = None
        self.token_range = None
        self.cost_range = None
    
    def add_date_range(self, start_date: str, end_date: str) -> 'LogQueryBuilder':
        """Add date range filter."""
        self.date_range = (start_date, end_date)
        return self
    
    def add_function_filter(self, function_name: str) -> 'LogQueryBuilder':
        """Add function filter."""
        self.function_name = function_name
        return self
    
    def add_token_range(self, min_tokens: int, max_tokens: int) -> 'LogQueryBuilder':
        """Add token range filter."""
        self.token_range = (min_tokens, max_tokens)
        return self
    
    def add_cost_range(self, min_cost: float, max_cost: float) -> 'LogQueryBuilder':
        """Add cost range filter."""
        self.cost_range = (min_cost, max_cost)
        return self
    
    def has_filters(self):
        """Check if any filters are set."""
        return bool(self.date_range or self.function_name or self.token_range or self.cost_range)
    
    def matches_filters(self, log):
        """Check if a log entry matches all the set filters."""
        # Check date range
        if self.date_range:
            try:
                # Parse the full timestamp from the log
                timestamp = log.get('timestamp', '').split('.')[0]
                log_date = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S')
                # Parse the date-only strings from filters and set time to start/end of day
                start_date = datetime.strptime(self.date_range[0], '%Y-%m-%d').replace(hour=0, minute=0, second=0)
                end_date = datetime.strptime(self.date_range[1], '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                if not (start_date <= log_date <= end_date):
                    return False
            except (ValueError, KeyError) as e:
                logger.error(f"Date parsing error: {str(e)} for log: {log}")
                return False
        
        # Check function name
        if self.function_name:
            log_function = log.get('function_name', log.get('function', ''))
            if log_function != self.function_name:
                return False
        
        # Check token range
        if self.token_range:
            total_tokens = log.get('total_tokens', 0)
            if not (self.token_range[0] <= total_tokens <= self.token_range[1]):
                return False
        
        # Check cost range
        if self.cost_range:
            cost = log.get('cost', 0)
            if not (self.cost_range[0] <= cost <= self.cost_range[1]):
                return False
        
        return True

# Create Gradio interface using Blocks
with gr.Blocks(css=config.CSS) as demo:
    gr.Markdown("# AI Cheatsheet Generator")
    
    # Hidden state to store summarized content
    summarized_content = gr.State("")
    
    with gr.Tab("Generate Cheatsheet"):
        with gr.Row():
            with gr.Column():
                prompt = gr.Textbox(label="Prompt", placeholder="Enter your cheatsheet prompt...")
                theme = gr.Textbox(label="Theme", placeholder="Enter the theme...")
                subject = gr.Textbox(label="Subject", placeholder="Enter the subject...")
                template_name = gr.Dropdown(
                    choices=list(config.TEMPLATES.keys()),
                    label="Template",
                    value="Study Guide"
                )
                style = gr.Dropdown(
                    choices=config.STYLE_CHOICES,
                    label="Style",
                    value="Minimal"
                )
                exemplified = gr.Dropdown(
                    choices=config.EXEMPLIFIED_CHOICES,
                    label="Include Examples",
                    value="Yes include examples"
                )
                complexity = gr.Dropdown(
                    choices=config.COMPLEXITY_CHOICES,
                    label="Complexity",
                    value="Intermediate"
                )
                audience = gr.Dropdown(
                    choices=config.AUDIENCE_CHOICES,
                    label="Target Audience",
                    value="Student"
                )
                enforce_formatting = gr.Checkbox(
                    label="Enforce Markdown Formatting",
                    value=True
                )
                generate_btn = gr.Button("Generate Cheatsheet")
            
            with gr.Column():
                with gr.Tabs():
                    with gr.TabItem("Rendered Output"):
                        cheatsheet_loading = gr.Markdown("", elem_classes="loading-text")
                        output = gr.Markdown(label="Generated Cheatsheet")
                    with gr.TabItem("Raw Text"):
                        raw_output = gr.Code(label="Raw Markdown", language="markdown")
    
    with gr.Tab("Interactive Learning"):
        gr.Markdown("<h1 style='text-align: center; font-size: 32px; margin-bottom: 30px;'>Interactive Learning Features</h1>")
        gr.Markdown("<p style='text-align: center; color: #666;'>Generate a cheatsheet first to use these features</p>")
        
        # Quiz Section
        gr.Markdown("<h2 style='text-align: center; font-size: 28px; margin: 20px 0;'>Quiz Generator</h2>")
        with gr.Column():
            with gr.Row():
                with gr.Column(scale=1):
                    quiz_type = gr.Dropdown(
                        choices=config.LEARNING_FEATURES["Quiz Generation"]["types"],
                        label="Quiz Type",
                        value="multiple_choice"
                    )
                with gr.Column(scale=1):
                    difficulty = gr.Dropdown(
                        choices=config.LEARNING_FEATURES["Quiz Generation"]["difficulty"],
                        label="Difficulty",
                        value="intermediate"
                    )
                with gr.Column(scale=1):
                    quiz_count = gr.Slider(
                        minimum=1,
                        maximum=10,
                        value=5,
                        step=1,
                        label="Number of Questions"
                    )
            with gr.Row():
                generate_quiz_btn = gr.Button("Generate Quiz", scale=1)
            with gr.Tabs():
                with gr.TabItem("Rendered Output"):
                    quiz_loading = gr.Markdown("", elem_classes="loading-text")
                    quiz_output = gr.Markdown(label="Generated Quiz")
                with gr.TabItem("Raw Text"):
                    raw_quiz_output = gr.Code(label="Raw Markdown", language="markdown")
        
        gr.Markdown("<hr style='border: 2px solid #ddd; margin: 30px 0;'>")
        
        # Flashcards Section
        gr.Markdown("<h2 style='text-align: center; font-size: 28px; margin: 20px 0;'>Flashcards</h2>")
        with gr.Column():
            with gr.Row():
                with gr.Column(scale=1):
                    flashcard_count = gr.Slider(
                        minimum=1,
                        maximum=20,
                        value=10,
                        step=1,
                        label="Number of Flashcards"
                    )
            with gr.Row():
                generate_flashcards_btn = gr.Button("Generate Flashcards", scale=1)
            with gr.Tabs():
                with gr.TabItem("Rendered Output"):
                    flashcard_loading = gr.Markdown("", elem_classes="loading-text")
                    flashcard_output = gr.Markdown(label="Generated Flashcards")
                with gr.TabItem("Raw Text"):
                    raw_flashcard_output = gr.Code(label="Raw Markdown", language="markdown")
        
        gr.Markdown("<hr style='border: 2px solid #ddd; margin: 30px 0;'>")
        
        # Practice Problems Section
        gr.Markdown("<h2 style='text-align: center; font-size: 28px; margin: 20px 0;'>Practice Problems</h2>")
        with gr.Column():
            with gr.Row():
                with gr.Column(scale=1):
                    problem_type = gr.Dropdown(
                        choices=config.LEARNING_FEATURES["Practice Problems"]["types"],
                        label="Problem Type",
                        value="exercises"
                    )
                with gr.Column(scale=1):
                    problem_count = gr.Slider(
                        minimum=1,
                        maximum=10,
                        value=3,
                        step=1,
                        label="Number of Problems"
                    )
            with gr.Row():
                generate_problems_btn = gr.Button("Generate Practice Problems", scale=1)
            with gr.Tabs():
                with gr.TabItem("Rendered Output"):
                    problem_loading = gr.Markdown("", elem_classes="loading-text")
                    problem_output = gr.Markdown(label="Generated Problems")
                with gr.TabItem("Raw Text"):
                    raw_problem_output = gr.Code(label="Raw Markdown", language="markdown")
    
    with gr.Tab("AI-Enhanced Content"):
        gr.Markdown("<h1 style='text-align: center; font-size: 32px; margin-bottom: 30px;'>AI-Enhanced Content</h1>")
        gr.Markdown("<p style='text-align: center; color: #666;'>Generate a cheatsheet first to use these features</p>")
        
        # Smart Summarization Section
        gr.Markdown("<h2 style='text-align: center; font-size: 28px; margin: 20px 0;'>Smart Summarization</h2>")
        with gr.Column():
            with gr.Row():
                with gr.Column(scale=1):
                    summary_level = gr.Dropdown(
                        choices=config.AI_FEATURES["Smart Summarization"]["levels"],
                        label="Summary Level",
                        value="detailed"
                    )
                with gr.Column(scale=1):
                    summary_focus = gr.Dropdown(
                        choices=config.AI_FEATURES["Smart Summarization"]["focus"],
                        label="Focus Area",
                        value="concepts"
                    )
            with gr.Row():
                generate_summary_btn = gr.Button("Generate Summary", scale=1)
            with gr.Tabs():
                with gr.TabItem("Rendered Output"):
                    summary_loading = gr.Markdown("", elem_classes="loading-text")
                    summary_output = gr.Markdown(label="Generated Summary")
                with gr.TabItem("Raw Text"):
                    raw_summary_output = gr.Code(label="Raw Markdown", language="markdown")
    
    with gr.Tab("Debug Analytics", elem_classes="debug-analytics"):
        gr.Markdown("<h1>Debug Analytics</h1>")
        
        # Token Usage Monitor Section
        with gr.Column(elem_classes="token-monitor"):
            with gr.Row():
                with gr.Column(scale=3):
                    gr.Markdown("<h2>Token Usage Monitor</h2>")
                with gr.Column(scale=1):
                    with gr.Row(elem_classes="action-buttons"):
                        refresh_logs = gr.Button("🔄 Refresh Data", elem_classes="action-button")
                        clear_filters = gr.Button("❌ Clear Filters", elem_classes="action-button")
            
            token_usage_table = gr.Dataframe(
                headers=["Time", "Function", "Prompt Tokens", "Completion Tokens", "Total Tokens", "Cost"],
                row_count=10,
                col_count=(6, "fixed"),
                interactive=False,
                wrap=True,
                elem_classes="usage-table"
            )
            
            with gr.Row(elem_classes="usage-overview"):
                with gr.Column(scale=3):
                    gr.Markdown("<h3>Usage Overview</h3>")
                    usage_by_function = gr.Markdown("No usage data available by function")
                with gr.Column(scale=1):
                    with gr.Row(elem_classes="action-buttons"):
                        refresh_function_usage = gr.Button("Update Function Stats", elem_classes="action-button")

        # Query Builder Section
        with gr.Column(elem_classes="query-builder"):
            gr.Markdown("<h2>Query Builder</h2>")
            with gr.Tabs() as query_tabs:
                with gr.TabItem("Smart Filter"):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("📅 Date Range")
                            start_date = gr.Textbox(
                                label="Start Date",
                                placeholder="YYYY-MM-DD",
                                value="2025-03-29"
                            )
                            end_date = gr.Textbox(
                                label="End Date",
                                placeholder="YYYY-MM-DD",
                                value="2025-04-05"
                            )
                        
                        with gr.Column():
                            gr.Markdown("🔍 Function Filter")
                            function_dropdown = gr.Dropdown(
                                label="Select Function",
                                choices=get_unique_functions(),
                                multiselect=False
                            )
                        
                        with gr.Column():
                            gr.Markdown("🎯 Token Range")
                            min_tokens = gr.Number(
                                label="Min Tokens",
                                value=0
                            )
                            max_tokens = gr.Number(
                                label="Max Tokens",
                                value=10000
                            )
                        
                        with gr.Column():
                            gr.Markdown("💰 Cost Range")
                            min_cost = gr.Number(
                                label="Min Cost ($)",
                                value=0
                            )
                            max_cost = gr.Number(
                                label="Max Cost ($)",
                                value=1
                            )
                    
                    with gr.Row():
                        with gr.Column(scale=3):
                            result_limit = gr.Slider(
                                minimum=10,
                                maximum=1000,
                                value=100,
                                step=10,
                                label="Result Limit"
                            )
                        with gr.Column(scale=1):
                            apply_smart_filter = gr.Button("🔍 Apply Smart Filter", variant="primary", elem_classes="filter-button")

    with gr.Tab("About"):
        gr.Markdown("""
        # AI Cheatsheet Generator
        
        ## How This App Works
        
        ### 1. Cheatsheet Generation 🎯
        - Enter your prompt, theme, and subject
        - Choose from various templates and styles
        - Let AI generate high-quality content
        
        ### 2. Learning Features 📚
        - **Quizzes** 📝 - Test your knowledge with multiple-choice, fill-in-the-blank, or true/false questions
        - **Flashcards** 🗂️ - Create study cards for memorization and review
        - **Practice Problems** ✍️ - Generate exercises to reinforce learning
        - **Summaries** 📚 - Get concise summaries at different detail levels
        
        ### 3. Token Usage Tracking 📊
        - Monitor API usage and costs
        - View detailed logs of all API calls
        - Track usage patterns over time
        
        ## Technical Stack
        
        - 🐍 Built with Python
        - 🎨 Gradio UI Framework
        - 🤖 OpenAI API Integration
        - 🗄️ SQLite Database
        
        #
        ### Connect With Me
        **Created by Leonardo Briquezi**
        - [GitHub](https://github.com/leobrqz) 
        - [LinkedIn](https://www.linkedin.com/in/leonardobri/) 💼
        
        
    
        ### Documentation
        - [Gradio Documentation](https://www.gradio.app/docs) 🎨
        - [OpenAI API Documentation](https://platform.openai.com/docs/api-reference) 🤖
        - [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction) 🔗
        - [SQLite Documentation](https://www.sqlite.org/docs.html) 🗄️
        
        """)

    # Event handlers for the buttons
    def show_loading(loading_component, message):
        return gr.update(value=message, visible=True)

    def hide_loading(loading_component):
        return gr.update(value="", visible=False)

    generate_btn.click(
        fn=lambda: show_loading(cheatsheet_loading, "🔄 Generating cheatsheet..."),
        inputs=[],
        outputs=[cheatsheet_loading]
    ).then(
        generate_cheatsheet_and_summarize,
        inputs=[
            prompt, theme, subject, template_name, style,
            exemplified, complexity, audience, enforce_formatting
        ],
        outputs=[output, raw_output, summarized_content]
    ).then(
        fn=lambda: hide_loading(cheatsheet_loading),
        inputs=[],
        outputs=[cheatsheet_loading]
    )

    # Quiz generation event handler
    generate_quiz_btn.click(
        fn=lambda: show_loading(quiz_loading, "🔄 Generating quiz..."),
        inputs=[],
        outputs=[quiz_loading]
    ).then(
        quiz_with_check,
        inputs=[summarized_content, quiz_type, difficulty, quiz_count],
        outputs=[quiz_output, raw_quiz_output]
    ).then(
        fn=lambda: hide_loading(quiz_loading),
        inputs=[],
        outputs=[quiz_loading]
    )

    # Flashcard generation event handler
    generate_flashcards_btn.click(
        fn=lambda: show_loading(flashcard_loading, "🔄 Generating flashcards..."),
        inputs=[],
        outputs=[flashcard_loading]
    ).then(
        flashcards_with_check,
        inputs=[summarized_content, flashcard_count],
        outputs=[flashcard_output, raw_flashcard_output]
    ).then(
        fn=lambda: hide_loading(flashcard_loading),
        inputs=[],
        outputs=[flashcard_loading]
    )

    # Practice problems generation event handler
    generate_problems_btn.click(
        fn=lambda: show_loading(problem_loading, "🔄 Generating practice problems..."),
        inputs=[],
        outputs=[problem_loading]
    ).then(
        problems_with_check,
        inputs=[summarized_content, problem_type, problem_count],
        outputs=[problem_output, raw_problem_output]
    ).then(
        fn=lambda: hide_loading(problem_loading),
        inputs=[],
        outputs=[problem_loading]
    )

    # Summary generation event handler
    generate_summary_btn.click(
        fn=lambda: show_loading(summary_loading, "🔄 Generating summary..."),
        inputs=[],
        outputs=[summary_loading]
    ).then(
        summary_with_check,
        inputs=[summarized_content, summary_level, summary_focus],
        outputs=[summary_output, raw_summary_output]
    ).then(
        fn=lambda: hide_loading(summary_loading),
        inputs=[],
        outputs=[summary_loading]
    )

    refresh_logs.click(
        update_logs,
        outputs=[token_usage_table, usage_by_function]
    )

    clear_filters.click(
        lambda: ([], "No usage data available"),
        outputs=[token_usage_table, usage_by_function]
    )

    apply_smart_filter.click(
        apply_combined_filters,
        inputs=[
            start_date, end_date,
            function_dropdown,
            min_tokens, max_tokens,
            min_cost, max_cost,
            result_limit
        ],
        outputs=[token_usage_table, usage_by_function]
    )

    refresh_function_usage.click(
        update_usage_by_function,
        outputs=usage_by_function
    )

    # Update function dropdown choices when logs are refreshed
    refresh_logs.click(
        lambda: gr.Dropdown(choices=get_unique_functions()),
        outputs=function_dropdown
    )

    # Add CSS for better styling
    gr.Markdown("""
    <style>
    .gradio-container {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    h1 {
        font-size: 2.5em;
        font-weight: 600;
        margin-bottom: 1em;
    }
    
    h2 {
        font-size: 1.8em;
        font-weight: 500;
        margin: 0;
        padding: 0;
    }

    h3 {
        font-size: 1.4em;
        font-weight: 500;
        margin: 0;
        padding: 0;
    }
    
    /* Debug Analytics specific styles */
    .debug-analytics {
        padding: 20px;
    }

    .debug-analytics .token-monitor {
        margin-bottom: 32px;
    }

    .debug-analytics .action-buttons {
        display: flex;
        justify-content: flex-end;
        gap: 12px;
        margin-top: 8px;
    }

    .debug-analytics .action-button {
        min-width: 120px !important;
        height: 36px !important;
        border-radius: 6px !important;
        background-color: #f3f4f6 !important;
        border: 1px solid #e5e7eb !important;
        color: #374151 !important;
        font-weight: 500 !important;
        transition: all 0.2s ease-in-out;
    }

    .debug-analytics .action-button:hover {
        background-color: #e5e7eb !important;
        border-color: #d1d5db !important;
    }

    .debug-analytics .usage-table {
        margin: 16px 0;
        border-radius: 8px;
        overflow: hidden;
    }

    .debug-analytics .usage-overview {
        margin-top: 24px;
        padding: 16px;
        background-color: #f9fafb;
        border-radius: 8px;
    }

    .debug-analytics .query-builder {
        margin-top: 32px;
    }

    .debug-analytics .filter-button {
        width: 100% !important;
        height: 40px !important;
        margin-top: 24px !important;
    }

    /* General component styles */
    .tabs {
        margin-top: 1em;
    }
    
    button {
        border-radius: 6px !important;
        font-weight: 500 !important;
        height: 40px !important;
        min-width: 120px !important;
    }
    
    button[variant="primary"] {
        background-color: #2563eb !important;
        color: white !important;
    }
    
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        margin: 1em 0;
    }
    
    .dataframe th {
        background-color: #f3f4f6;
        padding: 12px;
        text-align: left;
        font-weight: 500;
    }
    
    .dataframe td {
        padding: 12px;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .markdown-body {
        padding: 1em;
        background-color: #f9fafb;
        border-radius: 8px;
        margin: 1em 0;
    }
    
    /* Loading indicator styles */
    .loading-text {
        padding: 12px;
        margin-bottom: 12px;
        background-color: #eef2ff;
        border-radius: 6px;
        color: #4f46e5;
        font-weight: 500;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.6; }
        100% { opacity: 1; }
    }
    </style>
    """)

if __name__ == "__main__":
    demo.launch()
