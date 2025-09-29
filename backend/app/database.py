import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Provide a stable default if not configured
if not DATABASE_URL or not DATABASE_URL.strip():
    _HERE = os.path.dirname(__file__)
    _DB_PATH = os.path.join(_HERE, "data.db")
    # Ensure absolute path for SQLite
    _DB_PATH = os.path.abspath(_DB_PATH)
    DATABASE_URL = f"sqlite:///{_DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()