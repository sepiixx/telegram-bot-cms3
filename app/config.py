# ==========================================
# MODULE: APPLICATION CONFIGURATION
# PURPOSE: Centralized configuration management
# ==========================================

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """
    Application configuration settings.
    Loads from environment variables and .env file.
    """

    # ========== FastAPI Configuration ==========
    FAST_API_HOST: str = "0.0.0.0"
    FAST_API_PORT: int = 8000
    FAST_API_RELOAD: bool = True
    FAST_API_DEBUG: bool = True
    APP_NAME: str = "Telegram Bot CMS"
    APP_VERSION: str = "1.0.0"

    # ========== Telegram Configuration ==========
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_BOT_USERNAME: str
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = None
    TELEGRAM_POLLING: bool = True  # Use polling if True, webhook if False

    # ========== Database Configuration ==========
    DATABASE_URL: str = "sqlite:///./telegram_bot.db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_ECHO: bool = False  # Set to True for SQL logging

    # ========== JWT Authentication ==========
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 30

    # ========== Admin Configuration ==========
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_EMAIL: str = "admin@example.com"

    # ========== Security Configuration ==========
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    RATE_LIMIT_PER_MINUTE: int = 60
    PASSWORD_MIN_LENGTH: int = 8

    # ========== File Upload Configuration ==========
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list = ["jpg", "jpeg", "png", "gif", "pdf", "doc", "docx", "zip"]
    UPLOAD_DIR: str = "uploads"

    # ========== Logging Configuration ==========
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # ========== Email Configuration ==========
    EMAIL_ENABLED: bool = False
    EMAIL_SMTP_HOST: str = "smtp.gmail.com"
    EMAIL_SMTP_PORT: int = 587
    EMAIL_SENDER: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None

    # ========== Scheduler Configuration ==========
    SCHEDULER_TIMEZONE: str = "UTC"

    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Cached to avoid repeated file reads.
    """
    return Settings()


# ========== Derived Configuration ==========
def get_upload_dir() -> Path:
    """
    Get or create upload directory.
    """
    settings = get_settings()
    upload_path = Path(settings.UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


def get_log_dir() -> Path:
    """
    Get or create logs directory.
    """
    settings = get_settings()
    log_path = Path(settings.LOG_FILE).parent
    log_path.mkdir(parents=True, exist_ok=True)
    return log_path
