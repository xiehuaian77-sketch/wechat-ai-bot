"""数据库会话管理。"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config.settings import settings


def _ensure_data_dir() -> None:
    db_url = str(settings.DATABASE_URL)
    if "sqlite" in db_url and "///" in db_url:
        db_path = db_url.split("///", 1)[1]
        if db_path and not db_path.startswith(":"):
            path = Path(db_path)
            path.parent.mkdir(parents=True, exist_ok=True)


_ensure_data_dir()

engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,
    future=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


__all__ = ["Base", "async_session", "engine", "get_session"]
