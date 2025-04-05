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
from query_builder import LogQueryBuilder
from singletons import OpenAIClient, DatabaseInstance
from datetime import datetime, timedelta
from logger import get_logger

# Get logger instance
logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client and database
llm = OpenAIClient.get_instance()
db = DatabaseInstance.get_instance()

def generate_cheatsheet_and_summarize(prompt, theme, subject, template_name, style, exemplified, complexity, audience, enforce_formatting):
    """Generates a cheatsheet and creates a summary for use in other features."""
    cheatsheet, raw_cheatsheet = generate_cheatsheet(
        prompt, theme, subject, template_name, style,
        exemplified, complexity, audience, enforce_formatting
    )
    
    # Create a summary of the cheatsheet for use in other features
    summarized_content = summarize_content_for_features(cheatsheet)
    
    return cheatsheet, raw_cheatsheet, summarized_content

def check_summarized_content(summarized_content, feature_name, generate_func, *args):
    """Checks if a cheatsheet has been generated before allowing feature generation."""
    if not summarized_content or summarized_content.strip() == "":
        return f"Please generate a cheatsheet first before using the {feature_name} feature.", ""
    
    return generate_func(summarized_content, *args)

def quiz_with_check(summarized_content, quiz_type, difficulty, quiz_count):
    """Checks if a cheatsheet has been generated before allowing quiz generation."""
    return check_summarized_content(summarized_content, "Quiz", generate_quiz, quiz_type, difficulty, quiz_count)

def flashcards_with_check(summarized_content, flashcard_count):
    """Checks if a cheatsheet has been generated before allowing flashcard generation."""
    return check_summarized_content(summarized_content, "Flashcards", generate_flashcards, flashcard_count)

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

def update_usage_by_function():
    """Update the usage statistics grouped by function."""
    function_usage = calculate_total_usage_by_function()
    if not function_usage:
        return "No usage data available by function"
    
    # Create a markdown table for function usage
    table = "### Usage Statistics by Function\n\n"
    table += "| Function | Total Tokens | Cost |\n"
    table += "|----------|--------------|------|\n"
    
    for function_name, stats in function_usage.items():
        table += f"| {function_name} | {stats['total_tokens']:,} | ${stats['total_cost']:.4f} |\n"
    
    return table

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
        
        # Execute query
        logs = db.query_logs(query_builder, limit)
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
                        output = gr.Markdown(label="Generated Cheatsheet")
                        loading_output = gr.Markdown(visible=True)
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
                    quiz_output = gr.Markdown(label="Generated Quiz")
                    quiz_loading = gr.Markdown(visible=True)
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
                    flashcard_output = gr.Markdown(label="Generated Flashcards")
                    flashcard_loading = gr.Markdown(visible=True)
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
                    problem_output = gr.Markdown(label="Generated Problems")
                    problem_loading = gr.Markdown(visible=True)
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
                    summary_output = gr.Markdown(label="Generated Summary")
                    summary_loading = gr.Markdown(visible=True)
                with gr.TabItem("Raw Text"):
                    raw_summary_output = gr.Code(label="Raw Markdown", language="markdown")
    
    with gr.Tab("Debug Logs"):
        gr.Markdown("<h1 style='text-align: center; font-size: 32px; margin-bottom: 30px;'>Debug Logs</h1>")
        gr.Markdown("<p style='text-align: center; color: #666;'>Monitor token usage and costs for debugging and optimization</p>")
        
        with gr.Row():
            refresh_logs = gr.Button("Refresh Logs", scale=0)
        
        with gr.Row():
            token_usage_table = gr.Dataframe(
                headers=["Time", "Function", "Prompt Tokens", "Completion Tokens", "Total Tokens", "Cost"],
                label="Token Usage Logs",
                interactive=False
            )
        
        with gr.Row():
            total_stats = gr.Markdown("No usage data available")
        
        with gr.Accordion("Advanced Query Options", open=False):
            gr.Markdown("## Combined Filters")
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Date Range")
                    start_date = gr.Textbox(
                        label="Start Date (YYYY-MM-DD)",
                        value=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                    )
                    end_date = gr.Textbox(
                        label="End Date (YYYY-MM-DD)",
                        value=datetime.now().strftime("%Y-%m-%d")
                    )
                with gr.Column(scale=1):
                    gr.Markdown("### Function")
                    function_dropdown = gr.Dropdown(
                        choices=get_unique_functions(),
                        label="Select Function",
                        value=None
                    )
                with gr.Column(scale=1):
                    gr.Markdown("### Token Range")
                    min_tokens = gr.Number(
                        label="Minimum Tokens",
                        value=0,
                        precision=0
                    )
                    max_tokens = gr.Number(
                        label="Maximum Tokens",
                        value=10000,
                        precision=0
                    )
                with gr.Column(scale=1):
                    gr.Markdown("### Cost Range")
                    min_cost = gr.Number(
                        label="Minimum Cost ($)",
                        value=0.0,
                        precision=4
                    )
                    max_cost = gr.Number(
                        label="Maximum Cost ($)",
                        value=1.0,
                        precision=4
                    )
            gr.Markdown("---")
            gr.Markdown("## Limit Results")
            with gr.Row():
                limit = gr.Slider(
                    minimum=10,
                    maximum=1000,
                    value=100,
                    step=10,
                    label="Limit Results"
                )
                apply_filters = gr.Button("Apply Filters")
            gr.Markdown("---")
            gr.Markdown("## Individual Filters")
            with gr.Row():
                date_limit = gr.Slider(
                    minimum=10,
                    maximum=1000,
                    value=100,
                    step=10,
                    label="Limit Results"
                )
                query_by_date = gr.Button("Query by Date Range")
            with gr.Row():
                function_limit = gr.Slider(
                    minimum=10,
                    maximum=1000,
                    value=100,
                    step=10,
                    label="Limit Results"
                )
                query_by_function = gr.Button("Query by Function")
            with gr.Row():
                token_limit = gr.Slider(
                    minimum=10,
                    maximum=1000,
                    value=100,
                    step=10,
                    label="Limit Results"
                )
                query_by_tokens = gr.Button("Query by Token Range")
            with gr.Row():
                cost_limit = gr.Slider(
                    minimum=10,
                    maximum=1000,
                    value=100,
                    step=10,
                    label="Limit Results"
                )
                query_by_cost = gr.Button("Query by Cost Range")
            
            gr.Markdown("### Usage Statistics by Function")
            with gr.Row():
                usage_by_function = gr.Markdown("No usage data available by function")
                refresh_function_usage = gr.Button("Refresh Function Usage")
        
        # Connect the buttons to their respective functions
        generate_btn.click(
            fn=lambda: ("<div style='text-align: center; padding: 20px; background-color: var(--background-fill-secondary); border-radius: 8px;'><p style='font-size: 16px;'>Generating cheatsheet...</p></div>", None, None),
            outputs=[loading_output, output, raw_output]
        ).then(
            generate_cheatsheet_and_summarize,
            inputs=[
                prompt, theme, subject, template_name, style,
                exemplified, complexity, audience, enforce_formatting
            ],
            outputs=[output, raw_output, summarized_content]
        ).then(
            update_logs,
            outputs=[token_usage_table, total_stats]
        ).then(
            lambda: ("", "", "", "", ""),  # Clear loading indicators
            outputs=[loading_output, quiz_loading, flashcard_loading, problem_loading, summary_loading]
        )
        
        # Quiz generation with check
        generate_quiz_btn.click(
            lambda: ("<div style='text-align: center; padding: 20px; background-color: var(--background-fill-secondary); border-radius: 8px;'><p style='font-size: 16px;'>Generating quiz...</p></div>", None),
            outputs=[quiz_loading, quiz_output]
        ).then(
            quiz_with_check,
            inputs=[summarized_content, quiz_type, difficulty, quiz_count],
            outputs=[quiz_output, raw_quiz_output]
        ).then(
            update_logs,
            outputs=[token_usage_table, total_stats]
        ).then(
            lambda: ("", "", "", "", ""),  # Clear loading indicators
            outputs=[loading_output, quiz_loading, flashcard_loading, problem_loading, summary_loading]
        )
        
        # Flashcards generation with check
        generate_flashcards_btn.click(
            lambda: ("<div style='text-align: center; padding: 20px; background-color: var(--background-fill-secondary); border-radius: 8px;'><p style='font-size: 16px;'>Generating flashcards...</p></div>", None),
            outputs=[flashcard_loading, flashcard_output]
        ).then(
            flashcards_with_check,
            inputs=[summarized_content, flashcard_count],
            outputs=[flashcard_output, raw_flashcard_output]
        ).then(
            update_logs,
            outputs=[token_usage_table, total_stats]
        ).then(
            lambda: ("", "", "", "", ""),  # Clear loading indicators
            outputs=[loading_output, quiz_loading, flashcard_loading, problem_loading, summary_loading]
        )
        
        # Practice problems generation with check
        generate_problems_btn.click(
            lambda: ("<div style='text-align: center; padding: 20px; background-color: var(--background-fill-secondary); border-radius: 8px;'><p style='font-size: 16px;'>Generating practice problems...</p></div>", None),
            outputs=[problem_loading, problem_output]
        ).then(
            problems_with_check,
            inputs=[summarized_content, problem_type, problem_count],
            outputs=[problem_output, raw_problem_output]
        ).then(
            update_logs,
            outputs=[token_usage_table, total_stats]
        ).then(
            lambda: ("", "", "", "", ""),  # Clear loading indicators
            outputs=[loading_output, quiz_loading, flashcard_loading, problem_loading, summary_loading]
        )
        
        # Summary generation with check
        generate_summary_btn.click(
            lambda: ("<div style='text-align: center; padding: 20px; background-color: var(--background-fill-secondary); border-radius: 8px;'><p style='font-size: 16px;'>Generating summary...</p></div>", None),
            outputs=[summary_loading, summary_output]
        ).then(
            summary_with_check,
            inputs=[summarized_content, summary_level, summary_focus],
            outputs=[summary_output, raw_summary_output]
        ).then(
            update_logs,
            outputs=[token_usage_table, total_stats]
        ).then(
            lambda: ("", "", "", "", ""),  # Clear loading indicators
            outputs=[loading_output, quiz_loading, flashcard_loading, problem_loading, summary_loading]
        )

        # Connect refresh button
        refresh_logs.click(
            update_logs,
            outputs=[token_usage_table, total_stats]
        )
        
        # Connect combined filters
        apply_filters.click(
            apply_combined_filters,
            inputs=[start_date, end_date, function_dropdown, min_tokens, max_tokens, min_cost, max_cost, limit],
            outputs=[token_usage_table, total_stats]
        )
        
        # Connect individual filters
        query_by_date.click(
            update_logs_by_date_range,
            inputs=[start_date, end_date, date_limit],
            outputs=[token_usage_table, total_stats]
        )
        
        query_by_function.click(
            update_logs_by_function,
            inputs=[function_dropdown, function_limit],
            outputs=[token_usage_table, total_stats]
        )
        
        query_by_tokens.click(
            update_logs_by_token_range,
            inputs=[min_tokens, max_tokens, token_limit],
            outputs=[token_usage_table, total_stats]
        )
        
        query_by_cost.click(
            update_logs_by_cost_range,
            inputs=[min_cost, max_cost, cost_limit],
            outputs=[token_usage_table, total_stats]
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

if __name__ == "__main__":
    demo.launch()
