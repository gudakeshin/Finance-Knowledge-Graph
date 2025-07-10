import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from config.env file
load_dotenv("config.env")

class Settings(BaseSettings):
    # Neo4j Configuration
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    
    # Redis Configuration (for Celery)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Finance Knowledge Graph"
    
    class Config:
        case_sensitive = True

settings = Settings() 