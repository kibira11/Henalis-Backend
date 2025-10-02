# app/config.py
"""
Configuration module for Henalis furniture e-commerce backend.
Loads environment variables and provides configuration settings.
"""

from pydantic_settings import BaseSettings   # ✅ import BaseSettings
from typing import ClassVar                  # ✅ import ClassVar


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database connection string (Neon/Postgres)
    database_url: str

    # JWT secret key (loaded from .env)
    jwt_secret: str

    # API Configuration
    default_limit: int = 12

    # CORS (optional)
    cors_origins: list[str] = ["*"]

    # Constant (not from .env)
    jwt_user_id_claim: ClassVar[str] = "sub"

    class Config:
        env_file = ".env"
        case_sensitive = False


# ✅ Global settings instance
settings = Settings()
