from typing import Optional
from langchain_openai import ChatOpenAI
from config import API_KEY, MODEL_NAME, TEMPERATURE

class OpenAIClient:
    _instance: Optional[ChatOpenAI] = None
    
    @classmethod
    def get_instance(cls) -> ChatOpenAI:
        if cls._instance is None:
            if not API_KEY:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            cls._instance = ChatOpenAI(model=MODEL_NAME, api_key=API_KEY, temperature=TEMPERATURE)
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