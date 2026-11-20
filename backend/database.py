"""SQLite connection and SQLAlchemy setup for Society Doom."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    """Base class shared by all database models."""


# Keep the database beside this file so commands work from any directory.
DATABASE_PATH = Path(__file__).resolve().parent / "society_doom.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def create_tables() -> None:
    """Create any tables that do not exist yet."""
    # Import models here so SQLAlchemy knows about them before creating tables.
    from backend import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
