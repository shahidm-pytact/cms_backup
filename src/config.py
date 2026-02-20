"""Application configuration using Pydantic BaseSettings."""
from typing import Union
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    # REQUIRED: Set DATABASE_URL environment variable
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    database_url: str = ""  # Must be set via environment variable
    
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
    allowed_image_types: Union[str, list[str]] = ["png", "jpg", "jpeg", "gif", "webp"]
    
    @field_validator("allowed_image_types", mode="before")
    @classmethod
    def parse_allowed_image_types(cls, v):
        """Parse allowed_image_types from comma-separated string or list.
        
        Supports both JSON array format: ["png","jpg","jpeg"]
        and comma-separated string format: png,jpg,jpeg
        
        This validator runs before Pydantic's JSON parsing to handle
        comma-separated strings from .env files.
        """
        # Handle None or empty values
        if v is None:
            return ["png", "jpg", "jpeg", "gif", "webp"]  # Default value
        
        # If already a list (from JSON parsing or default), return as-is
        if isinstance(v, list):
            return v
        
        # If it's a string, parse as comma-separated values
        if isinstance(v, str):
            v = v.strip()
            # Handle empty string
            if not v:
                return ["png", "jpg", "jpeg", "gif", "webp"]  # Default if empty
            
            # Try to parse as JSON first (in case user provided JSON format)
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                # Not JSON, treat as comma-separated string
                pass
            
            # Parse as comma-separated string
            items = [item.strip() for item in v.split(",") if item.strip()]
            return items if items else ["png", "jpg", "jpeg", "gif", "webp"]
        
        # Fallback to default
        return ["png", "jpg", "jpeg", "gif", "webp"]
    
    # Blog Revalidation Webhook Configuration
    blog_revalidation_webhook_secret: str = ""
    blog_revalidation_webhook_url: str = "http://192.168.1.27:3000/api/revalidate"
    
    # Next.js API Secret for public access
    next_api_secret: str = ""
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",  # Ignore extra fields from .env that are handled by other config classes
    }


settings = Settings()  # Singleton instance


def validate_required_settings() -> None:
    """Validate that all required settings are set."""
    errors = []
    
    if not settings.database_url:
        errors.append("DATABASE_URL environment variable is required")
    
    if not settings.smtp_username and settings.smtp_password:
        # Only warn if password is set but username is not
        pass
    
    if errors:
        raise ValueError(
            "Missing required environment variables:\n" + "\n".join(f"  - {error}" for error in errors)
        )


# Validate required settings on import
validate_required_settings()
