import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = None

def get_engine():
    """Lazily creates the database engine on the first request that needs it."""
    global engine
    if engine is None:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is not set.")
        print("DEBUG: Creating database engine for the first time.")
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False} if "sqlite" in str(DATABASE_URL) else {}
        )
    return engine

def get_db():
    """FastAPI dependency to get a DB session for each request."""
    db_engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()