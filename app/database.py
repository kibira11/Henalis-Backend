"""
Database configuration and session management for Henalis backend.
Uses SQLAlchemy with async engine and session factory.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings


# ----------------------------------------------------------------------------
# Database Engine
# ----------------------------------------------------------------------------
# We use asyncpg with SQLAlchemy for async database operations.
# Pool settings help manage concurrent connections efficiently.
# ----------------------------------------------------------------------------
engine = create_async_engine(
    settings.database_url,       # Loaded from .env (Neon/Postgres)
    echo=False,                  # Set True for SQL query logs in dev
    future=True,                 # Enable SQLAlchemy 2.0 style
    pool_pre_ping=True,          # Check connection health
    pool_size=10,                # Default pool size
    max_overflow=20,             # Extra connections if pool is full
)


# ----------------------------------------------------------------------------
# Session Factory
# ----------------------------------------------------------------------------
# AsyncSessionLocal is used in dependency injection (FastAPI routes).
# ----------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,      # Don’t expire objects after commit
    autocommit=False,
    autoflush=False,
)


# ----------------------------------------------------------------------------
# Base Class for ORM Models
# ----------------------------------------------------------------------------
Base = declarative_base()


# ----------------------------------------------------------------------------
# Dependency: Get DB Session
# ----------------------------------------------------------------------------
async def get_db() -> AsyncSession:
    """
    Provide an async database session.
    This function is used with FastAPI Depends in routes.
    Ensures session is closed after request is finished.
    """
    async with AsyncSessionLocal() as session:
        yield session
