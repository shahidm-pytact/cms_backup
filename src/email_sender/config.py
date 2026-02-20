"""Email configuration and settings."""
from pydantic_settings import BaseSettings


class EmailSettings(BaseSettings):
    """Email settings loaded from environment variables."""
    
    # SMTP Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "CMS System"
    smtp_use_tls: bool = True
    
    # Frontend URL for invitation links
    frontend_url: str = "http://localhost:3000"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "env_prefix": "EMAIL_",
        "extra": "ignore",
    }


email_settings = EmailSettings()
