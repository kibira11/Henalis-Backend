"""
Database configuration and Session Management.
Provides async AQLAlchemy engine and session factory
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# create async engine
engine = create_async_engine(
    settings.database_url,
    echo = False, # Set to True for SQL query logging during development
    future = True,
    pool_pre_ping = True, # Verify connections before using them
    pool_size = 10, # Connection pool size
    max_overflow = 20, # Max overflow connections

    )

# create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit = False,
    autoflush = False,
    )

# Base class for declarative models
Base = declarative_base()

async def get_db() -> AsyncSession:
    """
    Dependency that provides an async database session.
    Yields a session and ensures it's closed sfter use.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()




