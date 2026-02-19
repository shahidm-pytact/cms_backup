"""Authentication configuration and settings."""
from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    """Authentication settings loaded from environment variables."""
    
    # JWT Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"  # MUST be set via environment variable
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour (as per API spec: 15 minutes to 1 hour)
    
    # Password Reset Configuration
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24  # 24 hours (as per API spec)
    
    # Invitation Configuration
    INVITATION_TOKEN_EXPIRE_DAYS: int = 7  # 7 days (as per API spec)
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_prefix": "AUTH_",
        "extra": "ignore",  # Ignore extra fields from .env
    }


auth_settings = AuthSettings()
