import os
from dotenv import load_dotenv
import gradio as gr
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

def initialize_llm():
    """Initialize the OpenAI model."""
    return ChatOpenAI(model="gpt-4o-mini-2024-07-18", api_key=os.getenv("OPENAI_API_KEY"), temperature=0.7)

def construct_instruction_prompt():
    """Constructs the system instruction message for the LLM."""
    return ("""
    You are a helpful assistant that generates a cheatsheet based on the user's input.
    
    Here are your instructions:
    The cheatsheet should be concise, informative, and tailored to the user's specified parameters.
    The cheatsheet should be well-structured and easy to read.
    The content should be relevant to the prompt and adhere to the specified theme and subject.
    The cheatsheet should reflect the complexity level and target audience specified by the user.    
    
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

def construct_input_prompt(llm, prompt, theme, subject, complexity, audience, style, output_format, exemplified):

    """Constructs the user input message for the LLM, summarizing key fields first."""
    summarized_input = summarize_inputs(llm, prompt, theme, subject, complexity, audience)
    return f"""
    Create a cheatsheet based on the following parameters:
    - Summarized Input: {summarized_input}

    Here are the formatting and style guidelines:
    - Exemplified: {exemplified}
    - Complexity Level: {complexity}
    - Target Audience: {audience}
    - Style: {style}
    - Output Format: {output_format} 
    """


def generate_response(prompt, theme, subject, style, output_format, exemplified, complexity, audience):
    """Generates a cheatsheet response based on user inputs."""
    llm = initialize_llm()
    system_message = construct_instruction_prompt()
    user_message = construct_input_prompt(llm, prompt, theme, subject, complexity, audience, style, output_format, exemplified)


    
    messages = [
        ("system", system_message),
        ("human", user_message)
    ]
    
    response = llm.invoke(messages)
    return response.content

def create_interface():
    """Creates the Gradio interface."""
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

        submit_btn.click(
            fn=generate_response,
            inputs=[prompt, theme, subject, complexity, audience, style, output_format, exemplified],
            outputs=output,
            show_progress=True
        )
    
    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch()
