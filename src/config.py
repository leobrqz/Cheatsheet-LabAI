import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Settings
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-4o-mini-2024-07-18"
TEMPERATURE = 0.7

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

# UI Style Configuration
CSS = """
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
"""

# Dropdown Choices
STYLE_CHOICES = ["Minimal", "Detailed", "Summarized"]
EXEMPLIFIED_CHOICES = ["Yes include examples", "No do not include examples"]
COMPLEXITY_CHOICES = ["Basic", "Intermediate", "Advanced"]
AUDIENCE_CHOICES = ["Student", "Intermediate", "Professional"] 