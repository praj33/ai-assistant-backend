import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import Integer, String, Text, DateTime
from datetime import datetime
from typing import Optional

# Ensure data directory exists for SQLite
DATABASE_DIR = "data"
os.makedirs(DATABASE_DIR, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{os.path.join(DATABASE_DIR, 'tasks.db')}")

# Disable echo in production for performance
echo = os.getenv("ENV") != "production"
engine = create_async_engine(DATABASE_URL, echo=echo)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def create_tables():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        # Log error but don't fail startup if database is read-only
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating database tables: {e}")
        # Re-raise to ensure we know about the issue
        raise