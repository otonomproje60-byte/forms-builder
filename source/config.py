# Forms Builder - Configuration

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Forms Builder"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 5003

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/forms.db"

    # Security
    ADMIN_API_KEY: str = Field(default="", description="Admin API key for form management")
    SECRET_KEY: str = Field(default="dev-secret-change-in-production", description="JWT secret key")

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "10/minute"
    RATE_LIMIT_STORAGE_URL: str = "memory://"

    # Email (SMTP)
    SMTP_ENABLED: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "Forms Builder <noreply@localhost>"
    SMTP_TLS: bool = True

    # Webhooks
    WEBHOOK_ENABLED: bool = True
    WEBHOOK_TIMEOUT: int = 10
    WEBHOOK_MAX_RETRIES: int = 3
    WEBHOOK_RETRY_DELAY: int = 5

    # Spam Protection
    HONEYPOT_ENABLED: bool = True
    HONEYPOT_FIELD_NAME: str = "website"

    # File Uploads
    UPLOAD_ENABLED: bool = True
    UPLOAD_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "./data/uploads"
    UPLOAD_ALLOWED_TYPES: list[str] = ["image/*", "application/pdf", "text/*"]

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()