import os
from dotenv import load_dotenv
import gradio as gr
from langchain_openai import ChatOpenAI
import re

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

def construct_input_prompt(llm, prompt, theme, subject, complexity, audience, style, output_format, exemplified, template_name):
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
    - Format: {output_format} 
    
    Structure:
    {structure}
    
    FORMATTING REQUIREMENTS:
    1. Use proper heading levels (## main, ### sub)
    2. Format code blocks with language spec (```python)
    3. Add spacing between sections
    4. Use consistent list formatting
    """

def generate_response(prompt, theme, subject, template_name, style, output_format, exemplified, complexity, audience):
    """Generates a cheatsheet response based on user inputs."""
    system_message = construct_instruction_prompt()
    user_message = construct_input_prompt(llm, prompt, theme, subject, complexity, audience, style, output_format, exemplified, template_name)
    
    messages = [
        ("system", system_message),
        ("human", user_message)
    ]
    
    response = llm.invoke(messages)
    
    # Fix markdown formatting issues
    formatted_response = fix_markdown_formatting(response.content)
    
    # Return both the formatted response and the raw text
    return formatted_response, formatted_response

# Create Gradio interface using Blocks
with gr.Blocks() as demo:
    gr.Markdown("# Cheatsheet Generator")
    gr.Markdown("Provide the necessary inputs to generate a customized cheatsheet.")

    with gr.Row():
        with gr.Column():
            prompt = gr.Textbox(label="Prompt", placeholder="Enter your specific question or topic...")
            theme = gr.Textbox(label="Theme", placeholder="Enter the theme or context...")
            subject = gr.Textbox(label="Subject", placeholder="Enter the subject area...")
            
            # Add template selector
            template_choices = ["Custom"] + list(TEMPLATES.keys())
            template_name = gr.Dropdown(choices=template_choices, label="Template", value="Custom")
            
            style = gr.Dropdown(choices=["Minimal", "Detailed", "Summarized"], label="Style")
            output_format = gr.Dropdown(choices=["Only markdown", "Plain text with markdown"], label="Output Format")
            exemplified = gr.Dropdown(choices=["Yes include examples", "No do not include examples"], label="Exemplified")
            complexity = gr.Dropdown(choices=["Basic", "Intermediate", "Advanced"], label="Complexity Level")
            audience = gr.Dropdown(choices=["Student", "Intermediate", "Professional"], label="Target Audience")
            
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
                    inputs=[raw_output],  # Use raw_output for better text formatting
                    outputs=[gr.File(label="Download", visible=False)]
                )

    # Connect the button to the function with loading state
    submit_btn.click(
        fn=generate_response,
        inputs=[prompt, theme, subject, template_name, style, output_format, exemplified, complexity, audience],
        outputs=[markdown_output, raw_output],
        show_progress=True
    )

if __name__ == "__main__":
    demo.launch()
