"""Pytest 配置与 fixtures。"""
from __future__ import annotations

import os

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

# 覆盖为内存 SQLite
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_ENABLED", "false")

from app.main import create_app
from app.database.session import Base, engine, get_session


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def app():
    application = create_app()
    # 使用 app 实际使用的 engine 初始化表，确保内存库共享
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return application


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session(app):
    async for session in get_session():
        yield session
