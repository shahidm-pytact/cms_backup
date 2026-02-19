"""Application configuration using Pydantic BaseSettings."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = "postgresql+asyncpg://postgres:1112@db:5432/cms"
    
    # API Configuration
    api_title: str = "FastAPI Project"
    api_version: str = "v1"
    api_prefix: str = "/v1"
    
    # Environment Configuration
    environment: str = "local"
    debug: bool = True
    
    # SMTP Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "CMS System"
    smtp_use_tls: bool = True
    
    # File Storage Configuration
    storage_base_path: str = "static"
    max_image_size_mb: int = 10
    allowed_image_types: list[str] = ["png", "jpg", "jpeg", "gif", "webp"]
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",  # Ignore extra fields from .env that are handled by other config classes
    }


settings = Settings()  # Singleton instance
