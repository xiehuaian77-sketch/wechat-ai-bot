"""工具层单元测试。"""
from __future__ import annotations

import pytest

from app.tools.datetime_tool import DateTimeTool
from app.tools.weather import WeatherTool
from app.tools.registry import tool_registry
from app.tools.base import ToolResult


@pytest.mark.anyio
async def test_datetime_tool_utc():
    tool = DateTimeTool()
    result: ToolResult = await tool.execute()
    assert result.success is True
    assert result.error is None
    assert "UTC" in result.output


@pytest.mark.anyio
async def test_datetime_tool_custom_timezone():
    tool = DateTimeTool()
    result: ToolResult = await tool.execute(timezone="Asia/Shanghai")
    assert result.success is True
    assert result.error is None


@pytest.mark.anyio
async def test_weather_tool_success(monkeypatch: pytest.MonkeyPatch):
    class FakeResponse:
        status_code = 200
        text = "Beijing: ☀️ +25°C"

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args: object) -> None:
            pass

        async def get(self, url: str, timeout: float = 10.0) -> FakeResponse:
            return FakeResponse()

    import app.tools.weather as weather_module
    monkeypatch.setattr(weather_module.httpx, "AsyncClient", lambda timeout: FakeClient())

    tool = WeatherTool()
    result: ToolResult = await tool.execute(city="Beijing")
    assert result.success is True
    assert "Beijing" in result.output


@pytest.mark.anyio
async def test_weather_tool_http_error(monkeypatch: pytest.MonkeyPatch):
    class FakeResponse:
        status_code = 500
        text = "Internal Server Error"

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args: object) -> None:
            pass

        async def get(self, url: str, timeout: float) -> FakeResponse:
            return FakeResponse()

    import app.tools.weather as weather_module
    monkeypatch.setattr(weather_module.httpx, "AsyncClient", lambda timeout: FakeClient())

    tool = WeatherTool()
    result: ToolResult = await tool.execute(city="Unknown")
    assert result.success is False
    assert result.error is not None


def test_tool_registry_register_and_get():
    tool_registry._tools.clear()
    tool = DateTimeTool()
    tool_registry.register(tool)
    assert tool_registry.get("datetime") is tool


def test_tool_registry_list_tools():
    tool_registry._tools.clear()
    tool = DateTimeTool()
    tool_registry.register(tool)
    schemas = tool_registry.list_tools()
    assert isinstance(schemas, list)
    assert len(schemas) == 1
    assert schemas[0]["name"] == "datetime"


def test_tool_registry_get_missing():
    tool_registry._tools.clear()
    assert tool_registry.get("not_exist") is None


@pytest.mark.anyio
async def test_tool_manager_execute_success():
    from app.tools.manager import tool_manager

    tool_registry._tools.clear()
    tool = DateTimeTool()
    tool_registry.register(tool)

    result = await tool_manager.execute("datetime", {})
    assert result.success is True


@pytest.mark.anyio
async def test_tool_manager_execute_not_found():
    from app.tools.manager import tool_manager

    tool_registry._tools.clear()
    result = await tool_manager.execute("not_exist", {})
    assert result.success is False
    assert "未找到" in result.error
