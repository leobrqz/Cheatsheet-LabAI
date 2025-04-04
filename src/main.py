from dotenv import load_dotenv
import gradio as gr
from langchain_openai import ChatOpenAI
from config import (
    TEMPLATES,
    LEARNING_FEATURES,
    AI_FEATURES,
    CSS,
    STYLE_CHOICES,
    EXEMPLIFIED_CHOICES,
    COMPLEXITY_CHOICES,
    AUDIENCE_CHOICES,
    API_KEY,
    MODEL_NAME,
    TEMPERATURE,
)
from generators import (
    generate_cheatsheet,
    generate_quiz,
    generate_flashcards,
    generate_practice_problems,
    generate_summary,
    summarize_content_for_features,
    get_token_logs,
    calculate_total_usage
)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
llm = ChatOpenAI(model=MODEL_NAME, api_key=API_KEY, temperature=TEMPERATURE)

def generate_cheatsheet_and_summarize(prompt, theme, subject, template_name, style, exemplified, complexity, audience, enforce_formatting):
    """Generates a cheatsheet and creates a summary for use in other features."""
    cheatsheet, raw_cheatsheet = generate_cheatsheet(
        prompt, theme, subject, template_name, style,
        exemplified, complexity, audience, enforce_formatting
    )
    
    # Create a summary of the cheatsheet for use in other features
    summarized_content = summarize_content_for_features(cheatsheet)
    
    return cheatsheet, raw_cheatsheet, summarized_content

def quiz_with_check(summarized_content, quiz_type, difficulty, quiz_count):
    """Checks if a cheatsheet has been generated before allowing quiz generation."""
    if not summarized_content or summarized_content.strip() == "":
        return "Please generate a cheatsheet first before using this feature.", ""
    
    return generate_quiz(summarized_content, quiz_type, difficulty, quiz_count)

def flashcards_with_check(summarized_content, flashcard_count):
    """Checks if a cheatsheet has been generated before allowing flashcard generation."""
    if not summarized_content or summarized_content.strip() == "":
        return "Please generate a cheatsheet first before using this feature.", ""
    
    return generate_flashcards(summarized_content, flashcard_count)

def problems_with_check(summarized_content, problem_type, problem_count):
    """Checks if a cheatsheet has been generated before allowing problem generation."""
    if not summarized_content or summarized_content.strip() == "":
        return "Please generate a cheatsheet first before using this feature.", ""
    
    return generate_practice_problems(summarized_content, problem_type, problem_count)

def summary_with_check(summarized_content, summary_level, summary_focus):
    """Checks if a cheatsheet has been generated before allowing summary generation."""
    if not summarized_content or summarized_content.strip() == "":
        return "Please generate a cheatsheet first before using this feature.", ""
    
    return generate_summary(summarized_content, summary_level, summary_focus)

def clear_loading_message(cheatsheet, raw_cheatsheet, quiz, raw_quiz, flashcards, raw_flashcards, problems, raw_problems, summary, raw_summary):
    """Clears only the loading messages while preserving the content."""
    return "", "", "", "", ""  # Only clear the 5 loading indicators

def update_logs():
    """Updates the token usage logs and statistics."""
    logs = get_token_logs()
    if not logs:
        return [], "No usage data available"
    
    # Convert logs to list format for dataframe
    log_data = [[
        log['timestamp'],
        log['function'],
        log['prompt_tokens'],
        log['completion_tokens'],
        log['total_tokens'],
        log['cost']
    ] for log in logs]
    
    # Calculate totals
    totals = calculate_total_usage()
    stats = f"""
### Total Usage Statistics
- **Total Prompt Tokens:** {totals['total_prompt_tokens']:,}
- **Total Completion Tokens:** {totals['total_completion_tokens']:,}
- **Total Tokens:** {totals['total_tokens']:,}
- **Total Cost:** ${totals['total_cost']:.4f}
    """
    
    return log_data, stats

# Create Gradio interface using Blocks
with gr.Blocks(css=CSS) as demo:
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
                    choices=list(TEMPLATES.keys()),
                    label="Template",
                    value="Study Guide"
                )
                style = gr.Dropdown(
                    choices=STYLE_CHOICES,
                    label="Style",
                    value="Minimal"
                )
                exemplified = gr.Dropdown(
                    choices=EXEMPLIFIED_CHOICES,
                    label="Include Examples",
                    value="Yes include examples"
                )
                complexity = gr.Dropdown(
                    choices=COMPLEXITY_CHOICES,
                    label="Complexity",
                    value="Intermediate"
                )
                audience = gr.Dropdown(
                    choices=AUDIENCE_CHOICES,
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
                        choices=LEARNING_FEATURES["Quiz Generation"]["types"],
                        label="Quiz Type",
                        value="multiple_choice"
                    )
                with gr.Column(scale=1):
                    difficulty = gr.Dropdown(
                        choices=LEARNING_FEATURES["Quiz Generation"]["difficulty"],
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
                        choices=LEARNING_FEATURES["Practice Problems"]["types"],
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
                        choices=AI_FEATURES["Smart Summarization"]["levels"],
                        label="Summary Level",
                        value="detailed"
                    )
                with gr.Column(scale=1):
                    summary_focus = gr.Dropdown(
                        choices=AI_FEATURES["Smart Summarization"]["focus"],
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
    
    # Connect the buttons to their respective functions
    generate_btn.click(
        lambda: ("<div style='text-align: center; padding: 20px; background-color: var(--background-fill-secondary); border-radius: 8px;'><p style='font-size: 16px;'>Generating cheatsheet...</p></div>", None, None),
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
        clear_loading_message,
        inputs=[output, raw_output, quiz_output, raw_quiz_output, flashcard_output, raw_flashcard_output, problem_output, raw_problem_output, summary_output, raw_summary_output],
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
        clear_loading_message,
        inputs=[output, raw_output, quiz_output, raw_quiz_output, flashcard_output, raw_flashcard_output, problem_output, raw_problem_output, summary_output, raw_summary_output],
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
        clear_loading_message,
        inputs=[output, raw_output, quiz_output, raw_quiz_output, flashcard_output, raw_flashcard_output, problem_output, raw_problem_output, summary_output, raw_summary_output],
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
        clear_loading_message,
        inputs=[output, raw_output, quiz_output, raw_quiz_output, flashcard_output, raw_flashcard_output, problem_output, raw_problem_output, summary_output, raw_summary_output],
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
        clear_loading_message,
        inputs=[output, raw_output, quiz_output, raw_quiz_output, flashcard_output, raw_flashcard_output, problem_output, raw_problem_output, summary_output, raw_summary_output],
        outputs=[loading_output, quiz_loading, flashcard_loading, problem_loading, summary_loading]
    )

    # Connect refresh button
    refresh_logs.click(
        update_logs,
        outputs=[token_usage_table, total_stats]
    )
    
    # Add automatic log updates after each generation
    def update_after_generation(*args):
        """Updates logs after content generation."""
        logs, stats = update_logs()
        return [*args, logs, stats]

if __name__ == "__main__":
    demo.launch()
