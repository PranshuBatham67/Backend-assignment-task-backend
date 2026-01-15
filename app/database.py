from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create the database engine
# Using pool_pre_ping to handle stale connections
# SQLite uses different connection parameters than PostgreSQL
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},  # Allow multi-threading for SQLite
        echo=settings.DEBUG  # Log SQL queries in debug mode
    )
else:
    # PostgreSQL configuration with connection pooling
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,  # Max 10 connections in pool
        max_overflow=20,  # Allow 20 extra connections if needed
        echo=settings.DEBUG  # Log SQL queries in debug mode
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    """
    Creates a new database session for each request.
    Automatically closes the session after the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper function to create all tables
def create_tables():
    """Create all database tables. Usually done via Alembic migrations."""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all tables - use with caution!"""
    Base.metadata.drop_all(bind=engine)
