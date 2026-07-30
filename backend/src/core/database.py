"""Async SQLAlchemy engine and session factory.

Uses SQLAlchemy 2.0 async style with asyncpg driver.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
import os

from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import get_settings

_settings = get_settings()

_DB_URL = os.environ.get("DATABASE_URL", _settings.database_url)

engine = create_async_engine(
    _DB_URL,
    echo=_settings.DEBUG,
    future=True,
    poolclass=NullPool if _settings.APP_ENV == "development" else None,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an AsyncSession and closes it after the request."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
