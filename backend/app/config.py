"""
AutoTestAI - Configuration Module
Manages all application settings via environment variables.
"""
from pydantic_settings import BaseSettings
from typing import Optional
from enum import Enum
import os


class AIProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    OLLAMA = "ollama"


class Settings(BaseSettings):
    """Application configuration loaded from .env file."""

    # App
    APP_NAME: str = "AutoTestAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "autotestai-secret-key-change-in-production"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./autotestai.db"

    # Redis (optional for Phase 1)
    REDIS_URL: str = "redis://localhost:6379"

    # AI Providers
    ACTIVE_AI_PROVIDER: AIProvider = AIProvider.OPENAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-pro"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "codellama"

    # Storage
    UPLOAD_DIR: str = "./uploads"
    OUTPUT_DIR: str = "./generated"
    MAX_UPLOAD_SIZE_MB: int = 50

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton settings instance
settings = Settings()


def ensure_directories():
    """Create necessary directories if they don't exist."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "testcases"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "html"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "screenshots"), exist_ok=True)
