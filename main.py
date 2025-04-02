import os
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_response(prompt, theme, subject, style, output_format, exemplified, complexity, audience):
    # Construct the system message based on inputs
    
    instruction_prompt = f"""You are a helpful assistant that generates a cheatsheet based on the user's input.
    
    Here are your instructions:
    The cheatsheet should be concise, informative, and tailored to the user's specified parameters.
    The cheatsheet should be well-structured and easy to read.
    The content should be relevant to the prompt and adhere to the specified theme and subject.
    The cheatsheet should reflect the complexity level and target audience specified by the user.    
    
    Always follow the formmating and style guidelines provided by "style:" and "output_format:". 
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
    """
    
    input_prompt = f"""
    Create a cheatsheet based on the following parameters:
    - User prompt: {prompt}
    - Theme: {theme}
    - Subject: {subject}

    Here are the formatting and style guidelines:
    - Exemplified: {exemplified}
    - Complexity Level: {complexity}
    - Target Audience: {audience}
    - Style: {style}
    - Output Format: {output_format} 

    """

    # Get response from OpenAI
    response = client.responses.create(
        model="gpt-4o-mini",
        instructions=instruction_prompt,
        input=input_prompt,
        temperature=0.7
    )

    # Extract the content from the response
    return response.output_text

# Create Gradio interface using Blocks
with gr.Blocks() as demo:
    gr.Markdown("# Cheatsheet Generator")
    gr.Markdown("Provide the necessary inputs to generate a customized cheatsheet.")

    with gr.Row():
        with gr.Column():
            prompt = gr.Textbox(label="Prompt", placeholder="Enter your specific question or topic...")
            theme = gr.Textbox(label="Theme", placeholder="Enter the theme or context...")
            subject = gr.Textbox(label="Subject", placeholder="Enter the subject area...")
            style = gr.Dropdown(choices=["Minimal", "Detailed", "Summarized"], label="Style")
            output_format = gr.Dropdown(choices=["Only markdown", "Plain text with markdown"], label="Output Format")
            exemplified = gr.Dropdown(choices=["Yes include examples", "No do not include examples"], label="Exemplified")
            complexity = gr.Dropdown(choices=["Basic", "Intermediate", "Advanced"], label="Complexity Level")
            audience = gr.Dropdown(choices=["Student", "Intermediate", "Professional"], label="Target Audience")
            
            submit_btn = gr.Button("Generate Cheatsheet")

        with gr.Column():
            gr.Markdown("### Generated Response")
            output = gr.Markdown(value="Your generated cheatsheet will appear here...", show_copy_button=True, container=True)
            with gr.Row():
                    download_btn = gr.Button("Download as TXT")
                    download_btn.click(
                        lambda x: gr.File.update(value=x, visible=True),
                        inputs=[output],
                        outputs=[gr.File(label="Download", visible=False)]
                    )

    # Connect the button to the function with loading state
    submit_btn.click(
        fn=generate_response,
        inputs=[prompt, theme, subject, style, output_format, exemplified, complexity, audience],
        outputs=output,
        show_progress=True
    )

if __name__ == "__main__":
    demo.launch()
