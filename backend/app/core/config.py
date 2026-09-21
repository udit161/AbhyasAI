import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "AI Learning Assistant & Mock Interview Platform"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    
    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-haiku-20240307-v1:0"
    
    # LLM Settings
    OPENAI_API_KEY: str = ""
    
    # Vector DB
    VECTOR_DB_PATH: str = "./data/vector_store"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
