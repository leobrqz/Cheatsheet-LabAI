import os
from dotenv import load_dotenv
import gradio as gr
from langchain_openai import ChatOpenAI
import re
import json
import random
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import networkx as nx
from PIL import Image

# Load environment variables
load_dotenv()

# Initialize OpenAI client
llm = ChatOpenAI(model="gpt-4o-mini-2024-07-18", api_key=os.getenv("OPENAI_API_KEY"), temperature=0.7)

# Define templates
TEMPLATES = {
    "Study Guide": {
        "structure": """
            Use as overall structure for the cheatsheet the following layout:
            1. **Overview:** A brief introduction to the topic.
            2. **Key Concepts:** A detailed list of key points.
            3. **In-Depth Analysis:** Further explanation of complex ideas.
            4. **Summary:** A concise summary of the content.
            (...)
            This is a overview of the layout, you can add more sections if you think it is necessary or tweak it.
        """
    },
    "Coding Cheatsheet": {
        "structure": """
            Use as overall structure for the cheatsheet the following layout:
            1. **Code Snippets:** Provide essential code examples.
            2. **Explanation:** Briefly explain each code snippet.
            3. **Best Practices:** List tips and best practices.
            4. **References:** Include links or citations for further reading.
            (...)
            This is a overview of the layout, you can add more sections if you think it is necessary or tweak it.
        """
    },
    "Quick Reference Card": {
        "structure": """
            Use as overall structure for the cheatsheet the following layout:
            1. **Header:** Title and quick context.
            2. **Bullet Points:** Concise, actionable points.
            3. **Footer:** A quick summary or conclusion.
            (...)
            This is a overview of the layout, you can add more sections if you think it is necessary or tweak it.
        """
    }
}

# Define Interactive Learning Features
LEARNING_FEATURES = {
    "Quiz Generation": {
        "types": ["multiple_choice", "fill_blanks", "true_false"],
        "difficulty": ["basic", "intermediate", "advanced"],
        "count": 5  # Default number of questions
    },
    "Flashcards": {
        "format": "term -> definition",
        "categories": "auto-tagged",
        "count": 10  # Default number of cards
    },
    "Practice Problems": {
        "types": ["exercises", "code_challenges", "scenarios"],
        "solutions": "included but hidden",
        "count": 3  # Default number of problems
    }
}

# Define AI-Enhanced Content Features
AI_FEATURES = {
    "Smart Summarization": {
        "levels": ["tldr", "detailed", "comprehensive"],
        "focus": ["concepts", "examples", "applications"]
    },
    "Content Enhancement": {
        "suggestions": ["examples", "diagrams", "references"],
        "citations": "auto-generated",
        "fact_checking": True
    }
}

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

def summarize_inputs(llm, prompt, theme, subject, complexity, audience):
    """Summarizes the prompt, theme, and subject while considering complexity and audience."""
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

def construct_input_prompt(llm, prompt, theme, subject, complexity, audience, style, exemplified, template_name):
    """Constructs the user input message for the LLM, summarizing key fields first."""
    summarized_input = summarize_inputs(llm, prompt, theme, subject, complexity, audience)
    
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

def generate_response(prompt, theme, subject, template_name, style, exemplified, complexity, audience, enforce_formatting):
    """Generates a cheatsheet response based on user inputs."""
    system_message = construct_instruction_prompt()
    user_message = construct_input_prompt(llm, prompt, theme, subject, complexity, audience, style, exemplified, template_name)
    
    messages = [
        ("system", system_message),
        ("human", user_message)
    ]
    
    response = llm.invoke(messages)
    
    # Fix markdown formatting issues if enabled
    if enforce_formatting:
        formatted_response = fix_markdown_formatting(response.content)
    else:
        formatted_response = response.content
    
    # Return both the formatted response and the raw text
    return formatted_response, formatted_response

def generate_quiz(content, quiz_type, difficulty, count):
    """Generates a quiz based on the cheatsheet content."""
    quiz_prompt = f"""
    Based on the following cheatsheet content, generate a {quiz_type} quiz with {count} questions at {difficulty} difficulty level.
    
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
    return response.content, response.content

def generate_flashcards(content, count):
    """Generates flashcards based on the cheatsheet content."""
    flashcard_prompt = f"""
    Based on the following cheatsheet content, generate exactly {count} flashcards.
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
    return response.content, response.content

def generate_practice_problems(content, problem_type, count):
    """Generates practice problems based on the cheatsheet content."""
    problem_prompt = f"""
    Based on the following cheatsheet content, generate {count} {problem_type} practice problems.
    
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
    return response.content, response.content

def generate_summary(content, level, focus):
    """Generates a summary of the cheatsheet content."""
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
    return response.content, response.content

# Create Gradio interface using Blocks
with gr.Blocks(css="""
    .feature-header { 
        text-align: center !important;
        margin: 20px 0 !important;
        font-size: 24px !important;
        font-weight: bold !important;
    }
    .feature-divider {
        border-top: 2px solid #444 !important;
        margin: 30px 0 !important;
        opacity: 0.3 !important;
    }
""") as demo:
    gr.Markdown("# Cheatsheet Generator")
    gr.Markdown("Provide the necessary inputs to generate a customized cheatsheet.")

    # Main cheatsheet section - keep as is
    with gr.Row():
        with gr.Column():
            prompt = gr.Textbox(label="Prompt", placeholder="Enter your specific question or topic...")
            theme = gr.Textbox(label="Theme", placeholder="Enter the theme or context...")
            subject = gr.Textbox(label="Subject", placeholder="Enter the subject area...")
            
            template_choices = ["Custom"] + list(TEMPLATES.keys())
            template_name = gr.Dropdown(choices=template_choices, label="Template", value="Custom")
            
            style = gr.Dropdown(choices=["Minimal", "Detailed", "Summarized"], label="Style")
            exemplified = gr.Dropdown(choices=["Yes include examples", "No do not include examples"], label="Exemplified")
            complexity = gr.Dropdown(choices=["Basic", "Intermediate", "Advanced"], label="Complexity Level")
            audience = gr.Dropdown(choices=["Student", "Intermediate", "Professional"], label="Target Audience")
            
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
    
    gr.Markdown('<div class="feature-divider"></div>')

    # Connect the main cheatsheet button
    submit_btn.click(
        fn=generate_response,
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
