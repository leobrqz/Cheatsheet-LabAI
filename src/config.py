import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import json
from pathlib import Path
from logger import get_logger

# Get logger instance
logger = get_logger(__name__)

class ConfigManager:
    _instance: Optional['ConfigManager'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_config()
            self._initialized = True
    
    def _load_config(self):
        """Load and validate configuration."""
        # Load environment variables
        load_dotenv()
        
        # Validate required environment variables
        required_vars = ['OPENAI_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # API Settings with validation
        self.API_KEY = os.getenv("OPENAI_API_KEY")
        self.MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini-2024-07-18")
        self.TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        
        # Validate temperature range
        if not 0 <= self.TEMPERATURE <= 1:
            raise ValueError("Temperature must be between 0 and 1")
        
        # Load templates from external file if exists
        templates_path = Path("src/config/templates.json")
        if templates_path.exists():
            with open(templates_path, 'r') as f:
                self.TEMPLATES = json.load(f)
        else:
            self.TEMPLATES = {
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
        
        # Load learning features from external file if exists
        features_path = Path("src/config/features.json")
        if features_path.exists():
            with open(features_path, 'r') as f:
                features = json.load(f)
                self.LEARNING_FEATURES = features.get('learning_features', {})
                self.AI_FEATURES = features.get('ai_features', {})
        else:
            self.LEARNING_FEATURES = {
                "Quiz Generation": {
                    "types": ["multiple_choice", "fill_blanks", "true_false"],
                    "difficulty": ["basic", "intermediate", "advanced"],
                    "count": 5
                },
                "Flashcards": {
                    "format": "term -> definition",
                    "categories": "auto-tagged",
                    "count": 10
                },
                "Practice Problems": {
                    "types": ["exercises", "code_challenges", "scenarios"],
                    "solutions": "included but hidden",
                    "count": 3
                }
            }
            
            self.AI_FEATURES = {
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
        self.CSS = """
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
        self.STYLE_CHOICES = ["Minimal", "Detailed", "Summarized"]
        self.EXEMPLIFIED_CHOICES = ["Yes include examples", "No do not include examples"]
        self.COMPLEXITY_CHOICES = ["Basic", "Intermediate", "Advanced"]
        self.AUDIENCE_CHOICES = ["Student", "Intermediate", "Professional"]
        
        logger.info("Configuration loaded successfully")
    
    @classmethod
    def get_instance(cls) -> 'ConfigManager':
        """Get the singleton instance of ConfigManager."""
        if cls._instance is None:
            cls()
        return cls._instance
    
    def get_api_key(self) -> str:
        """Get the API key."""
        return self.API_KEY
    
    def get_model_name(self) -> str:
        """Get the model name."""
        return self.MODEL_NAME
    
    def get_temperature(self) -> float:
        """Get the temperature setting."""
        return self.TEMPERATURE
    
    def get_templates(self) -> Dict[str, Any]:
        """Get the templates configuration."""
        return self.TEMPLATES
    
    def get_learning_features(self) -> Dict[str, Any]:
        """Get the learning features configuration."""
        return self.LEARNING_FEATURES
    
    def get_ai_features(self) -> Dict[str, Any]:
        """Get the AI features configuration."""
        return self.AI_FEATURES

# Create global config instance
config = ConfigManager.get_instance() 