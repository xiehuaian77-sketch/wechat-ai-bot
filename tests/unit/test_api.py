"""API 端点集成测试。"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_health_endpoint(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


@pytest.mark.anyio
async def test_root_endpoint(client: AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "name" in data
    assert "version" in data
    assert "docs" in data


@pytest.mark.anyio
async def test_login_creates_user(client: AsyncClient):
    wechat_id = f"test_{uuid.uuid4().hex[:8]}"
    resp = await client.post("/api/auth/login", json={"wechat_id": wechat_id, "nickname": "Test"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "customer"
    assert data["user_id"] is not None


@pytest.mark.anyio
async def test_tools_call_requires_auth(client: AsyncClient):
    resp = await client.post("/api/tools/call", json={"tool_name": "datetime", "arguments": {}})
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_knowledge_search_requires_auth(client: AsyncClient):
    resp = await client.post("/api/knowledge/search", json={"query": "test", "top_k": 3})
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_admin_whitelist_requires_admin(client: AsyncClient):
    # 先登录获取 customer token
    login_resp = await client.post(
        "/api/auth/login", json={"wechat_id": f"user_{uuid.uuid4().hex[:8]}", "nickname": "User"}
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/api/admin/whitelist", headers=headers)
    assert resp.status_code == 403
