"""中间件单元测试。"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.middleware.rate_limit import RateLimitMiddleware


@pytest.fixture
def app_with_rate_limit() -> FastAPI:
    application = FastAPI()
    application.add_middleware(RateLimitMiddleware)

    @application.get("/ok")
    async def ok() -> dict[str, str]:
        return {"status": "ok"}

    return application


@pytest.fixture
def client(app_with_rate_limit: FastAPI):
    return TestClient(app_with_rate_limit)


def test_rate_limit_allows_normal_requests(client: TestClient):
    for _ in range(5):
        resp = client.get("/ok")
        assert resp.status_code == 200


def test_rate_limit_blocks_excessive_requests(client: TestClient):
    # 快速发送超过限流阈值的请求
    for _ in range(120):
        resp = client.get("/ok")
        if resp.status_code == 429:
            assert "Too many requests" in resp.json()["detail"]
            return
    pytest.fail("Expected 429 Too Many Requests")
