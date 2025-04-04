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
    TEMPERATURE
)
from generators import (
    generate_cheatsheet,
    generate_quiz,
    generate_flashcards,
    generate_practice_problems,
    generate_summary
)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
llm = ChatOpenAI(model=MODEL_NAME, api_key=API_KEY, temperature=TEMPERATURE)

# Create Gradio interface using Blocks
with gr.Blocks(css=CSS) as demo:
    gr.Markdown("# Cheatsheet Generator")
    gr.Markdown("Provide the necessary inputs to generate a customized cheatsheet.")

    # Main cheatsheet section
    with gr.Row():
        with gr.Column():
            prompt = gr.Textbox(label="Prompt", placeholder="Enter your specific question or topic...")
            theme = gr.Textbox(label="Theme", placeholder="Enter the theme or context...")
            subject = gr.Textbox(label="Subject", placeholder="Enter the subject area...")
            
            template_choices = ["Custom"] + list(TEMPLATES.keys())
            template_name = gr.Dropdown(choices=template_choices, label="Template", value="Custom")
            
            style = gr.Dropdown(choices=STYLE_CHOICES, label="Style")
            exemplified = gr.Dropdown(choices=EXEMPLIFIED_CHOICES, label="Exemplified")
            complexity = gr.Dropdown(choices=COMPLEXITY_CHOICES, label="Complexity Level")
            audience = gr.Dropdown(choices=AUDIENCE_CHOICES, label="Target Audience")
            
            enforce_formatting = gr.Checkbox(label="Enforce Markdown Formatting", value=True)
            
            submit_btn = gr.Button("Generate Cheatsheet")

        with gr.Column():
            gr.Markdown("### Generated Response")
            with gr.Tabs():
                with gr.Tab("Rendered Markdown"):
                    markdown_output = gr.Markdown(
                        value="Your generated cheatsheet will appear here...",
                        show_copy_button=True
                    )
                with gr.Tab("Raw Text"):
                    raw_output = gr.Code(
                        value="Your raw text will appear here...",
                        language="markdown"
                    )
            
            with gr.Row():
                    download_btn = gr.Button("Download as TXT")
                    download_btn.click(
                        lambda x: gr.File.update(value=x, visible=True),
                        inputs=[raw_output],
                        outputs=[gr.File(label="Download", visible=False)]
                    )

    gr.Markdown('<div class="feature-divider"></div>')
    
    # Quiz Generator Section
    gr.Markdown('<p class="feature-header">Quiz Generator</p>')
    with gr.Column():
        with gr.Row():
            quiz_type = gr.Dropdown(choices=LEARNING_FEATURES["Quiz Generation"]["types"], label="Quiz Type", value="multiple_choice")
            quiz_difficulty = gr.Dropdown(choices=LEARNING_FEATURES["Quiz Generation"]["difficulty"], label="Difficulty", value="intermediate")
            quiz_count = gr.Slider(minimum=1, maximum=10, value=5, step=1, label="Number of Questions")
        generate_quiz_btn = gr.Button("Generate Quiz")
        with gr.Tabs():
            with gr.Tab("Rendered Output"):
                quiz_output = gr.Markdown(value="Your quiz will appear here...", show_copy_button=True)
            with gr.Tab("Raw Text"):
                quiz_output_raw = gr.Code(value="Your raw quiz will appear here...", language="markdown")
    
    gr.Markdown('<div class="feature-divider"></div>')
    
    # Flashcards Section
    gr.Markdown('<p class="feature-header">Flashcards</p>')
    with gr.Column():
        with gr.Row():
            flashcard_count = gr.Slider(
                minimum=1,
                maximum=20,
                value=5,
                step=1,
                label="Number of Flashcards"
            )
        generate_flashcards_btn = gr.Button("Generate Flashcards")
        with gr.Tabs():
            with gr.Tab("Rendered Output"):
                flashcard_output = gr.Markdown(
                    value="Your flashcards will appear here...",
                    show_copy_button=True
                )
            with gr.Tab("Raw Text"):
                flashcard_output_raw = gr.Code(
                    value="Your raw flashcards will appear here...",
                    language="markdown"
                )
    
    gr.Markdown('<div class="feature-divider"></div>')
    
    # Practice Problems Section
    gr.Markdown('<p class="feature-header">Practice Problems</p>')
    with gr.Column():
        with gr.Row():
            problem_type = gr.Dropdown(choices=LEARNING_FEATURES["Practice Problems"]["types"], label="Problem Type", value="exercises")
            problem_count = gr.Slider(minimum=1, maximum=5, value=3, step=1, label="Number of Problems")
        generate_problems_btn = gr.Button("Generate Practice Problems")
        with gr.Tabs():
            with gr.Tab("Rendered Output"):
                problem_output = gr.Markdown(value="Your practice problems will appear here...", show_copy_button=True)
            with gr.Tab("Raw Text"):
                problem_output_raw = gr.Code(value="Your raw practice problems will appear here...", language="markdown")
    
    gr.Markdown('<div class="feature-divider"></div>')
    
    # Smart Summarization Section
    gr.Markdown('<p class="feature-header">Smart Summarization</p>')
    with gr.Column():
        with gr.Row():
            summary_level = gr.Dropdown(choices=AI_FEATURES["Smart Summarization"]["levels"], label="Summary Level", value="detailed")
            summary_focus = gr.Dropdown(choices=AI_FEATURES["Smart Summarization"]["focus"], label="Focus", value="concepts")
        generate_summary_btn = gr.Button("Generate Summary")
        with gr.Tabs():
            with gr.Tab("Rendered Output"):
                summary_output = gr.Markdown(value="Your summary will appear here...", show_copy_button=True)
            with gr.Tab("Raw Text"):
                summary_output_raw = gr.Code(value="Your raw summary will appear here...", language="markdown")

    # Connect the main cheatsheet button
    submit_btn.click(
        fn=generate_cheatsheet,
        inputs=[prompt, theme, subject, template_name, style, exemplified, complexity, audience, enforce_formatting],
        outputs=[markdown_output, raw_output],
        show_progress=True
    )

    # Connect the interactive learning feature buttons
    generate_quiz_btn.click(
        fn=generate_quiz,
        inputs=[raw_output, quiz_type, quiz_difficulty, quiz_count],
        outputs=[quiz_output, quiz_output_raw],
        show_progress=True
    )
    
    generate_flashcards_btn.click(
        fn=generate_flashcards,
        inputs=[raw_output, flashcard_count],
        outputs=[flashcard_output, flashcard_output_raw],
        show_progress=True
    )
    
    generate_problems_btn.click(
        fn=generate_practice_problems,
        inputs=[raw_output, problem_type, problem_count],
        outputs=[problem_output, problem_output_raw],
        show_progress=True
    )
    
    # Connect the AI-enhanced content feature buttons
    generate_summary_btn.click(
        fn=generate_summary,
        inputs=[raw_output, summary_level, summary_focus],
        outputs=[summary_output, summary_output_raw],
        show_progress=True
    )

if __name__ == "__main__":
    demo.launch()
