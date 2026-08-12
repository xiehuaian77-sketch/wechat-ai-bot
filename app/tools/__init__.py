"""工具注册与发现。"""
from __future__ import annotations

from app.tools.datetime_tool import DateTimeTool
from app.tools.exchange_rate import ExchangeRateTool
from app.tools.manager import tool_manager
from app.tools.python_exec import PythonExecTool
from app.tools.registry import tool_registry
from app.tools.weather import WeatherTool
from app.tools.web_search import WebSearchTool
from app.utils.logger import logger


def register_all_tools() -> None:
    """注册所有内置工具。"""
    builtin_tools = [
        WeatherTool(),
        DateTimeTool(),
        ExchangeRateTool(),
        PythonExecTool(),
        WebSearchTool(),
    ]
    for tool in builtin_tools:
        tool_manager.register(tool)
    logger.info(f"Registered {len(builtin_tools)} built-in tools")


__all__ = ["register_all_tools", "tool_manager", "tool_registry"]
