"""Database configuration and connection utilities."""

import os
from typing import Generator

try:
    from sqlalchemy import create_engine, MetaData
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import QueuePool
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

from app.utils.logging import configure_logging, get_logger


logger = get_logger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:bthn@localhost:5432/trading_bot"
)

# Initialize database components only if SQLAlchemy is available
if SQLALCHEMY_AVAILABLE:
    # Create engine with connection pooling
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=os.getenv("SQL_DEBUG", "false").lower() == "true"
    )

    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create base class for models
    Base = declarative_base()

    # Metadata for migrations
    metadata = MetaData()
else:
    engine = None
    SessionLocal = None
    Base = None
    metadata = None


def get_db() -> Generator:
    """
    Database dependency for FastAPI.

    Yields:
        Database session
    """
    if not SQLALCHEMY_AVAILABLE or not SessionLocal:
        logger.error("SQLAlchemy not available")
        raise RuntimeError("Database not available")

    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database session error", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session():
    """
    Get a database session for use outside of FastAPI dependency injection.

    Returns:
        Database session
    """
    if not SQLALCHEMY_AVAILABLE or not SessionLocal:
        logger.error("SQLAlchemy not available")
        return None

    return SessionLocal()


def init_database():
    """
    Initialize database with tables and any required setup.
    This is useful for testing and initial setup.
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("SQLAlchemy not available")
        return False

    try:
        if not Base or not engine:
            logger.error("SQLAlchemy Base or engine not available")
            return False
            
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        return False
