"""
database.py - SQLite Database Setup
====================================
Uses SQLAlchemy async engine with aiosqlite for non-blocking DB access.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sahitya.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency that provides a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables."""
    import models  # noqa
    Base.metadata.create_all(bind=engine)
    print("[Database] SQLite initialized at", DB_PATH)
