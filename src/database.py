"""Database configuration with SQLAlchemy 2.x async engine."""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from src.config import settings


# Create async engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    echo=settings.debug,
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for all models
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# Dependency for FastAPI routes
async def get_session() -> AsyncSession:
    """Get database session for dependency injection.
    
    Uses async context manager to ensure proper session cleanup:
    - Session is automatically closed when request completes
    - Session is properly closed even if an exception occurs
    - FastAPI's dependency injection system ensures cleanup in all error scenarios
    - The async context manager ensures session.close() is called even on exceptions
    
    Yields:
        AsyncSession: Database session for the current request
    """
    async with AsyncSessionLocal() as session:
        yield session
