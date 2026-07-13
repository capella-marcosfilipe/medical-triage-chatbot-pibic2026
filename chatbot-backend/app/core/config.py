"""Application configuration settings."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Downstream chatbot microservice
    chatbot_microservice_url: str = "http://chat-rag-microservice:8000"
    chatbot_microservice_timeout_seconds: float = 30.0
    
    # Application Settings
    app_host: str = "0.0.0.0"
    app_port: int = 8001
    debug: bool = False
    
    # CORS Settings
    frontend_url: str = "http://localhost:4200"

    # PostgreSQL (prepared for SQLAlchemy integration)
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "triagem"
    postgres_user: str = "triagem"
    postgres_password: str = "triagem"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
