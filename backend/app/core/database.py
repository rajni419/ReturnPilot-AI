"""
Database configuration and session management for SQLite using SQLAlchemy.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

# Anchor database file in the backend root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_FILE = BASE_DIR / "returnpilot.db"
DEFAULT_DB_URL = f"sqlite:///{DB_FILE.as_posix()}"

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

if "sqlite" in DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency yielding a SQLAlchemy session.
    Closes the session automatically upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Creates all database tables defined in the metadata.
    """
    try:
        from ..models import (  # noqa: F401
            Order,
            OrderItem,
            ReturnRequest,
            User,
            EmailVerificationToken,
            PasswordResetToken,
            UserSession,
        )
    except (ImportError, ValueError):
        from backend.app.models import (  # noqa: F401
            Order,
            OrderItem,
            ReturnRequest,
            User,
            EmailVerificationToken,
            PasswordResetToken,
            UserSession,
        )

    Base.metadata.create_all(bind=engine)
