from langchain_openai import ChatOpenAI
from database import Database
from config import API_KEY, MODEL_NAME, TEMPERATURE

class OpenAIClient:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ChatOpenAI(model=MODEL_NAME, api_key=API_KEY, temperature=TEMPERATURE)
        return cls._instance

class DatabaseInstance:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Database()
        return cls._instance 