# app/config.py
"""
Configuration module for Henalis furniture e-commerce backend.
Loads environment variables and provides configuration settings.
"""

from pydantic_settings import BaseSettings
from typing import ClassVar


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database connection string (Neon/Postgres)
    database_url: str  # required in .env

    # API Configuration
    default_limit: int = 12  # default page size for list endpoints

    # CORS (optional, configure as needed)
    cors_origins: list[str] = ["*"]

    # ✅ Constant (not an env var): claim field in JWT for user ID
    jwt_user_id_claim: ClassVar[str] = "sub"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance (importable anywhere)
settings = Settings()
