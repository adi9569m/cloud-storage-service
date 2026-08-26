"""Database engine, session factory, and base model configuration."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Configure SQLAlchemy engine
# pool_pre_ping=True checks connection health before issuing queries
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG and settings.APP_ENV == "development",
)

# Session factory for database transactions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for all ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency provider for FastAPI route handlers to obtain a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
