"""工具注册表。"""
from __future__ import annotations

from typing import Any

from app.tools.base import BaseTool


class ToolRegistry:
    """工具注册表，管理所有可用工具。"""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """注册一个工具。"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        """获取工具实例。"""
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        """列出所有工具 schema。"""
        return [tool.to_schema() for tool in self._tools.values()]

    def all(self) -> dict[str, BaseTool]:
        """返回所有工具。"""
        return dict(self._tools)


tool_registry = ToolRegistry()
