import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
# Default: a SQLite file next to the backend folder. No install needed.
# To use PostgreSQL instead, set DATABASE_URL (and install psycopg2-binary).
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'skillgap.db'}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
