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
from query_builder import LogQueryBuilder
from pathlib import Path
import json

# Get logger instance
logger = get_logger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client and database
llm = OpenAIClient.get_instance()
db = DatabaseInstance.get_instance()

def migrate_default_templates():
    """Migrate default templates to database if they don't exist."""
    try:
        # Define default templates
        default_templates = {
            "Study Guide": {
                "type": "study",
                "structure": {
                    "sections": [
                        {"title": "Key Concepts", "content": "List and explain the main concepts"},
                        {"title": "Important Formulas", "content": "List and explain key formulas"},
                        {"title": "Examples", "content": "Provide worked examples"},
                        {"title": "Practice Problems", "content": "Include practice problems with solutions"}
                    ]
                }
            },
            "Coding Cheatsheet": {
                "type": "coding",
                "structure": {
                    "sections": [
                        {"title": "Syntax", "content": "Show basic syntax and examples"},
                        {"title": "Common Functions", "content": "List frequently used functions"},
                        {"title": "Best Practices", "content": "Include coding best practices"},
                        {"title": "Tips & Tricks", "content": "Add useful tips and tricks"}
                    ]
                }
            },
            "Quick Reference Card": {
                "type": "reference",
                "structure": {
                    "sections": [
                        {"title": "Overview", "content": "Brief overview of the topic"},
                        {"title": "Key Points", "content": "List of key points to remember"},
                        {"title": "Common Issues", "content": "List common issues and solutions"},
                        {"title": "Resources", "content": "Additional resources for learning"}
                    ]
                }
            }
        }

        # Get existing templates from database
        existing_templates = db.get_all_templates()
        existing_names = {t['name'] for t in existing_templates}

        # Add missing default templates
        for name, template in default_templates.items():
            if name not in existing_names:
                logger.info(f"Adding default template: {name}")
                db.add_template(
                    name=name,
                    template_type=template['type'],
                    structure=template['structure']
                )

        logger.info("Default templates migration completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error migrating default templates: {e}")
        return False

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

def update_template_list(template_search: str, template_filter: str) -> List[List[str]]:
    """Update the template list with search and filter functionality."""
    try:
        # Get all templates from database
        templates = db.get_all_templates()
        formatted_templates = []
        
        for template in templates:
            try:
                # Parse ISO format timestamp
                updated_at = datetime.fromisoformat(template['updated_at'])
                formatted_date = updated_at.strftime('%Y-%m-%d')
                
                formatted_templates.append([
                    template['name'],
                    template['type'],
                    formatted_date
                ])
            except (ValueError, TypeError) as e:
                logger.warning(f"Error formatting template date: {e}")
                # Use current date as fallback
                formatted_date = datetime.now().strftime('%Y-%m-%d')
                formatted_templates.append([
                    template['name'],
                    template['type'],
                    formatted_date
                ])
        
        # Apply search filter if provided
        if template_search:
            search_lower = template_search.lower()
            formatted_templates = [
                t for t in formatted_templates 
                if search_lower in t[0].lower()
            ]
        
        # Apply type filter if provided
        if template_filter and template_filter != 'all':
            formatted_templates = [
                t for t in formatted_templates 
                if t[1].lower() == template_filter.lower()
            ]
        
        # Update the template selector dropdown
        template_names = [t[0] for t in formatted_templates]
        
        return formatted_templates, gr.update(choices=template_names)
        
    except Exception as e:
        logger.error(f"Error updating template list: {e}")
        return [], gr.update(choices=[])

def update_template_dropdown():
    """Update the template dropdown with all available templates."""
    try:
        # Get all templates from config (includes both default and custom)
        all_templates = list(config.get_instance().get_templates().keys())
        return gr.update(choices=all_templates)
    except Exception as e:
        logger.error(f"Error updating template dropdown: {e}")
        return gr.update(choices=[])

def save_template(name, type, content):
    """Save template to database."""
    if not name or not content:
        return "Template name and content are required", update_template_list("", "all")
    
    try:
        # Check if template already exists
        db = DatabaseInstance.get_instance()
        templates = db.get_all_templates()
        
        # Find the template by name
        existing_template = next((t for t in templates if t['name'] == name), None)
        
        if existing_template:
            # Update existing template
            db.update_template(existing_template['id'], name, type, content)
            message = f"Template '{name}' updated successfully"
        else:
            # Create new template
            db.add_template(name, type, content)
            message = f"Template '{name}' saved successfully"
        
        # Update UI components
        templates, dropdown = update_template_list("", "all")
        
        return message, templates, dropdown
    except Exception as e:
        logger.error(f"Error saving template: {e}")
        return f"Error saving template: {str(e)}", update_template_list("", "all"), gr.update(choices=[])

def delete_template(template_name):
    """Show delete confirmation dialog."""
    # Check if template_name is empty or None
    if not template_name:
        return "No template selected", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
    
    return (
        f"Are you sure you want to delete the template '{template_name}'?",
        gr.update(visible=True),
        gr.update(visible=True),
        gr.update(visible=True),
        gr.update(visible=True)
    )

def confirm_delete(template_name):
    """Delete the selected template after confirmation."""
    # Check if template_name is empty or None
    if not template_name:
        templates, dropdown = update_template_list("", "all")
        return "No template selected", templates, dropdown, gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
    
    try:
        # Get template from database
        db = DatabaseInstance.get_instance()
        templates = db.get_all_templates()
        
        # Find the template by name
        template = next((t for t in templates if t['name'] == template_name), None)
        
        if template:
            # Delete the template using its ID
            success = db.delete_template(template['id'])
            if not success:
                raise RuntimeError("Failed to delete template from database")
        else:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Update UI components
        templates, dropdown = update_template_list("", "all")
        
        return (
            f"Template '{template_name}' deleted successfully",
            templates,
            dropdown,
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False)
        )
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        templates, dropdown = update_template_list("", "all")
        return (
            f"Error deleting template: {str(e)}",
            templates,
            dropdown,
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False)
        )

def quiz_with_check(summarized_content, quiz_type, difficulty, quiz_count):
    """Generate a quiz with error handling."""
    if not summarized_content:
        return "Please generate a cheatsheet first", "No content available for quiz generation"
    
    try:
        quiz = generate_quiz(summarized_content, quiz_type, difficulty, quiz_count)
        return quiz, quiz
    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        error_message = f"Error generating quiz: {str(e)}"
        return error_message, error_message

def flashcards_with_check(summarized_content, flashcard_count):
    """Generate flashcards with error handling."""
    if not summarized_content:
        return "Please generate a cheatsheet first", "No content available for flashcard generation"
    
    try:
        flashcards = generate_flashcards(summarized_content, flashcard_count)
        return flashcards, flashcards
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}")
        error_message = f"Error generating flashcards: {str(e)}"
        return error_message, error_message

def problems_with_check(summarized_content, problem_type, problem_count):
    """Generate practice problems with error handling."""
    if not summarized_content:
        return "Please generate a cheatsheet first", "No content available for problem generation"
    
    try:
        problems = generate_practice_problems(summarized_content, problem_type, problem_count)
        return problems, problems
    except Exception as e:
        logger.error(f"Error generating practice problems: {e}")
        error_message = f"Error generating practice problems: {str(e)}"
        return error_message, error_message

def summary_with_check(summarized_content, summary_level, summary_focus):
    """Generate a summary with error handling."""
    if not summarized_content:
        return "Please generate a cheatsheet first", "No content available for summary generation"
    
    try:
        summary = generate_summary(summarized_content, summary_level, summary_focus)
        return summary, summary
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        error_message = f"Error generating summary: {str(e)}"
        return error_message, error_message

def update_logs():
    """Update the token usage logs table."""
    try:
        logs = get_token_logs()
        if not logs:
            return [], "No usage data available"
        
        # Format logs for display
        formatted_logs = []
        for log in logs:
            formatted_logs.append([
                log['timestamp'],
                log['function_name'],
                log['prompt_tokens'],
                log['completion_tokens'],
                log['total_tokens'],
                f"${log['cost']:.4f}"
            ])
        
        # Calculate total usage by function
        usage_by_function = calculate_total_usage_by_function()
        if not usage_by_function:
            return formatted_logs, "No usage data available by function"
        
        # Format the usage statistics as a markdown table
        table = "### Usage by Function\n\n"
        table += "| Function | Total Tokens | Total Cost |\n"
        table += "|----------|--------------|------------|\n"
        
        for func_name, stats in usage_by_function.items():
            table += f"| {func_name} | {stats['total_tokens']:,} | ${stats['total_cost']:.4f} |\n"
        
        return formatted_logs, table
    except Exception as e:
        logger.error(f"Error updating logs: {e}")
        return [], f"Error updating logs: {str(e)}"

def apply_combined_filters(start_date, end_date, function_name, min_tokens, max_tokens, min_cost, max_cost, limit):
    """Apply combined filters to token usage logs."""
    try:
        # Validate date format
        if start_date and not validate_date_format(start_date):
            return [], "Invalid start date format. Use YYYY-MM-DD"
        if end_date and not validate_date_format(end_date):
            return [], "Invalid end date format. Use YYYY-MM-DD"
        
        # Build query
        query_builder = LogQueryBuilder()
        
        if start_date:
            query_builder.add_date_range(start_date, end_date or datetime.now().strftime('%Y-%m-%d'))
        
        if function_name:
            query_builder.add_function_filter(function_name)
        
        if min_tokens is not None:
            query_builder.add_token_range(min_tokens, max_tokens)
        
        if min_cost is not None:
            query_builder.add_cost_range(min_cost, max_cost)
        
        if limit:
            query_builder.set_limit(limit)
        
        # Execute query
        logs = db.query_logs(query_builder.build())
        
        # Format logs for display
        formatted_logs = []
        for log in logs:
            formatted_logs.append([
                log['timestamp'],
                log['function_name'],
                log['prompt_tokens'],
                log['completion_tokens'],
                log['total_tokens'],
                f"${log['cost']:.4f}"
            ])
        
        # Calculate total usage by function for filtered logs
        usage_by_function = calculate_total_usage_by_function(logs)
        if not usage_by_function:
            return formatted_logs, "No usage data available by function"
        
        # Format the usage statistics as a markdown table
        table = "### Usage by Function\n\n"
        table += "| Function | Total Tokens | Total Cost |\n"
        table += "|----------|--------------|------------|\n"
        
        for func_name, stats in usage_by_function.items():
            table += f"| {func_name} | {stats['total_tokens']:,} | ${stats['total_cost']:.4f} |\n"
        
        return formatted_logs, table
    except Exception as e:
        logger.error(f"Error applying filters: {e}")
        return [], f"Error applying filters: {str(e)}"

def update_usage_by_function():
    """Update the usage by function statistics."""
    try:
        usage_by_function = calculate_total_usage_by_function()
        if not usage_by_function:
            return "No usage data available by function"
        
        # Format the usage statistics as a markdown table
        table = "### Usage by Function\n\n"
        table += "| Function | Total Tokens | Total Cost |\n"
        table += "|----------|--------------|------------|\n"
        
        for func_name, stats in usage_by_function.items():
            table += f"| {func_name} | {stats['total_tokens']:,} | ${stats['total_cost']:.4f} |\n"
        
        return table
    except Exception as e:
        logger.error(f"Error updating usage by function: {e}")
        return f"Error updating usage by function: {str(e)}"

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
                    choices=list(config.get_instance().get_templates().keys()),
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

    with gr.Tab("Templates"):
        gr.Markdown("<h1 style='text-align: center; font-size: 32px; margin-bottom: 30px;'>Template Management</h1>")
        
        with gr.Row():
            with gr.Column(scale=2):
                # Template List Section
                gr.Markdown("### Available Templates")
                
                # Search and filter
                with gr.Row():
                    template_search = gr.Textbox(
                        label="Search Templates",
                        placeholder="Search by name or type...",
                        scale=3
                    )
                    template_filter = gr.Dropdown(
                        choices=["All", "Default", "Custom"],
                        label="Filter by Type",
                        value="All",
                        scale=1
                    )
                
                # Template Selection Dropdown
                template_selector = gr.Dropdown(
                    label="Select Template",
                    choices=[],
                    value=None,
                    interactive=True
                )
                
                # Template List
                template_list = gr.Dataframe(
                    headers=["Name", "Type", "Last Updated"],
                    datatype=["str", "str", "str"],
                    label="Templates",
                    interactive=True
                )
                
                # Template Actions
                with gr.Row():
                    new_template_btn = gr.Button("New Template", variant="primary", scale=1)
                    refresh_templates_btn = gr.Button("Refresh Templates", variant="secondary", scale=1)
                
                with gr.Row():
                    edit_template_btn = gr.Button("Edit Template", variant="secondary", scale=1)
                    delete_template_btn = gr.Button("Delete Template", variant="stop", scale=1)
                
                # Delete confirmation
                delete_confirmation = gr.Markdown("", visible=False)
                with gr.Row(visible=False) as delete_confirm_row:
                    confirm_delete_btn = gr.Button("Confirm Delete", variant="stop", scale=1)
                    cancel_delete_btn = gr.Button("Cancel", variant="secondary", scale=1)
            
            with gr.Column(scale=3):
                # Template Editor Section
                gr.Markdown("### Template Editor")
                
                with gr.Row():
                    template_editor_name = gr.Textbox(
                        label="Template Name",
                        placeholder="Enter template name...",
                        scale=2
                    )
                    template_editor_type = gr.Dropdown(
                        choices=["Default", "Custom"],
                        label="Template Type",
                        value="Custom",
                        scale=1
                    )
                
                # Template Content Editor
                gr.Markdown("#### Template Content")
                template_editor_content = gr.Code(
                    label="",
                    language="markdown",
                    value="# Enter template content in markdown format..."
                )
                
                # Template Actions
                with gr.Row():
                    save_template_btn = gr.Button("Save Template", variant="primary", scale=1)
                    preview_template_btn = gr.Button("Preview Template", variant="secondary", scale=1)
                
                # Template Preview
                gr.Markdown("#### Preview")
                template_preview = gr.Markdown(label="Template Preview")

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

    # Template Management Event Handlers
    def refresh_templates():
        """Refresh the template list."""
        return update_template_list("", "all")

    def new_template():
        """Create a new template."""
        return "", "Custom", "# Enter template content in markdown format..."

    def edit_template(template_name):
        """Load template data into editor."""
        # Check if template_name is empty or None
        if not template_name:
            return "", "Custom", "# Enter template content in markdown format..."
        
        try:
            # Check if it's a default template
            default_templates = config.get_instance().get_templates()
            if template_name in default_templates:
                return template_name, "Default", default_templates[template_name]["structure"]
            
            # Get template from database
            db = DatabaseInstance.get_instance()
            templates = db.get_all_templates()
            
            # Find the template by name
            template = next((t for t in templates if t['name'] == template_name), None)
            
            if template:
                return template['name'], template['type'], template['structure']
            else:
                return template_name, "Custom", "# Template Content"
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            return "", "Custom", "# Error loading template"

    def cancel_delete():
        """Cancel template deletion."""
        return (
            "Deletion cancelled",
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False)
        )

    def preview_template(content):
        """Preview template content."""
        if not content:
            return "No content to preview"
        return content

    # Search and filter event handlers
    template_search.change(
        fn=update_template_list,
        inputs=[template_search, template_filter],
        outputs=[template_list, template_selector]
    )
    
    template_filter.change(
        fn=update_template_list,
        inputs=[template_search, template_filter],
        outputs=[template_list, template_selector]
    )
    
    # Refresh templates button
    refresh_templates_btn.click(
        fn=lambda: update_template_list("", "all"),
        inputs=[],
        outputs=[template_list, template_selector]
    )

    # New template button
    new_template_btn.click(
        fn=new_template,
        inputs=[],
        outputs=[template_editor_name, template_editor_type, template_editor_content]
    )

    # Edit template button
    edit_template_btn.click(
        fn=edit_template,
        inputs=[template_selector],
        outputs=[template_editor_name, template_editor_type, template_editor_content]
    )

    # Delete template button
    delete_template_btn.click(
        fn=delete_template,
        inputs=[template_selector],
        outputs=[template_preview, delete_confirmation, delete_confirm_row, confirm_delete_btn, cancel_delete_btn]
    )

    # Confirm delete button
    confirm_delete_btn.click(
        fn=confirm_delete,
        inputs=[template_selector],
        outputs=[template_preview, template_list, template_selector, delete_confirmation, delete_confirm_row, delete_confirm_row]
    )
    
    # Cancel delete button
    cancel_delete_btn.click(
        fn=cancel_delete,
        inputs=[],
        outputs=[template_preview, delete_confirmation, delete_confirm_row, delete_confirm_row, confirm_delete_btn]
    )

    # Save template button
    save_template_btn.click(
        fn=save_template,
        inputs=[template_editor_name, template_editor_type, template_editor_content],
        outputs=[template_preview, template_list, template_selector]
    ).then(
        fn=update_template_dropdown,
        inputs=[],
        outputs=[template_name]
    )

    # Preview template button
    preview_template_btn.click(
        fn=preview_template,
        inputs=[template_editor_content],
        outputs=[template_preview]
    )

    # Initialize template list with initial data
    template_list.value, template_selector.value = update_template_list("", "all")

    # Initialize template dropdown with all templates
    template_name.value = update_template_dropdown()

    # Make sure the template list is properly set up for selection
    template_list.select(
        fn=lambda x: x,  # Just pass through the selection
        inputs=[template_list],
        outputs=[template_list]
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
