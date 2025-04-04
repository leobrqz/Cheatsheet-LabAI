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
    You are a helpful assistant that generates a cheatsheet based on the user's input.
    
    Here are your instructions:
    The cheatsheet should be concise, informative, and tailored to the user's specified parameters.
    The cheatsheet should be well-structured and easy to read.
    The content should be relevant to the prompt and adhere to the specified theme and subject.
    The cheatsheet should reflect the complexity level and target audience specified by the user.
    The cheatsshet should always include references to the sources of the information provided or reccomendations to the user to read more about the topic.   
    
    Always follow the formatting and style guidelines provided by "style:" and "output_format:". 
    Make sure to include examples if the user has requested them but only if they asked for it.
    
    Here is the explanation of the parameters:
    - user prompt = What the user asked 
    - Theme = What the cheatsheet is about
    - Subject = The specific area of focus within the theme

    Here are the formatting and style guidelines:
    - Exemplified = If it should include examples or not
    - Complexity Level = How far and in depth the level of detail and complexity in the content must be
    - Target Audience = The intended audience for the cheatsheet
    - Style = The overall style and tone of the cheatsheet
    - Output Format = The format in which the cheatsheet should be presented (e.g., markdown, plain text)
    
    Here is what the template structure functionality is:
    Use the Structure provided by the structure template to structure the cheatsheet.
    
    IMPORTANT MARKDOWN FORMATTING GUIDELINES:
    1. Always use proper heading levels (## for main sections, ### for subsections)
    2. For code blocks, always use triple backticks with language specification: ```python
    3. Ensure proper spacing between sections (add blank lines)
    4. Use proper list formatting with consistent indentation
    5. For nested lists, use proper indentation and consistent markers
    6. When using code examples, always wrap them in proper code blocks
    7. Use bold (**) and italic (*) formatting consistently
    8. Ensure proper escaping of special characters in code blocks
    """)

def summarize_inputs(llm, prompt, theme, subject, complexity, audience):
    """Summarizes the prompt, theme, and subject while considering complexity and audience."""
    summary_prompt = (
        f"""
        Given the following user input details:
        - Prompt: {prompt}
        - Theme: {theme}
        - Subject: {subject}
        - Complexity Level: {complexity}
        - Target Audience: {audience}
        
        Generate a concise, structured summary that captures the essential elements required to create a cheatsheet.
        This is NOT the cheatsheet itself, but a refined version of the user input to ensure clarity and relevance.
        Adjust detail levels appropriately:
        - For higher complexity, highlight deeper insights and advanced technical points.
        - For lower complexity, focus on key concepts with practical explanations.
        - Adapt explanations to the audience's knowledge level, ensuring accessibility for beginners and depth for experts.
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
    Create a cheatsheet based on the following parameters:
    - Summarized Input: {summarized_input}

    Here are the formatting and style guidelines:
    - Exemplified: {exemplified}
    - Complexity Level: {complexity}
    - Target Audience: {audience}
    - Style: {style}
    - Output Format: {output_format} 
    
    **Structural Guidelines:**
    {structure}
    
    IMPORTANT: Ensure proper markdown formatting with:
    1. Consistent heading levels (## for main sections, ### for subsections)
    2. Proper code blocks with language specification (```python)
    3. Adequate spacing between sections
    4. Proper list formatting and indentation
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
