from typing import Optional
from langchain_openai import ChatOpenAI
from config import config

class OpenAIClient:
    _instance: Optional[ChatOpenAI] = None
    
    @classmethod
    def get_instance(cls) -> ChatOpenAI:
        if cls._instance is None:
            api_key = config.get_api_key()
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            cls._instance = ChatOpenAI(
                model=config.get_model_name(), 
                api_key=api_key, 
                temperature=config.get_temperature()
            )
        return cls._instance

class DatabaseInstance:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            # Lazy import to avoid circular dependency
            from database import Database
            cls._instance = Database()
        return cls._instance 