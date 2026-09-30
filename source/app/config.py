import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = "Forms Builder"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 5003
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/forms.db"
    
    # Email (optional - for notifications)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "Forms Builder <noreply@forms.local>"
    SMTP_USE_TLS: bool = True
    
    # Webhook (optional - for notifications)
    WEBHOOK_URL: str = ""
    WEBHOOK_SECRET: str = ""
    WEBHOOK_TIMEOUT: int = 10
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Spam protection
    HONEYPOT_FIELD_NAME: str = "website"  # hidden field name
    HONEYPOT_ENABLED: bool = True
    
    # File uploads
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,gif,pdf,txt,doc,docx"
    
    # CORS
    ALLOWED_ORIGINS: str = "*"
    
    # Admin
    ADMIN_TOKEN: str = "changeme"  # Change in production!


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# Ensure upload directory exists
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path("./data").mkdir(parents=True, exist_ok=True)