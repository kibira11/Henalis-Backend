# app/config.py

"""
configuration module for Henalis furniture e-commerce backend.
Loads environment variables and provides configuration settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """ Application settings loaded from environment variables.
    """

    # Database
    database_url: str

    # Supabase
    supabase_role_claim: str = "role"
    admin_role_value: str = "admin"
    jwt_user_id_claim = str = "sub"

    # API Configuration
    default_limit: int = 12

    # CORS (optional, configure as needed)
    cors_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = False


# gLOBAL SETTINGS INSTANCE
SETTINGS = Settings()

