import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Ensure data directory exists for SQLite
DATABASE_DIR = "data"
os.makedirs(DATABASE_DIR, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(DATABASE_DIR, 'tasks.db')}")

# Disable echo in production for performance
echo = os.getenv("ENV") != "production"
engine = create_engine(DATABASE_URL, echo=echo, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        # Log error but don't fail startup if database is read-only
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating database tables: {e}")
        # Re-raise to ensure we know about the issue
        raise