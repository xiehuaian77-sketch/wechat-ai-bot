"""工具管理器。"""

from __future__ import annotations

from typing import Any

from app.tools.base import ToolResult
from app.tools.registry import tool_registry
from app.utils.logger import logger


class ToolManager:
    """工具管理器，负责工具的注册、发现和执行。"""

    def __init__(self) -> None:
        self._registry = tool_registry

    def register(self, tool: Any) -> None:
        """注册工具。"""
        self._registry.register(tool)
        logger.info(f"Tool registered: {tool.name}")

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """执行指定工具。"""
        tool = self._registry.get(tool_name)
        if tool is None:
            return ToolResult(success=False, output="", error=f"工具未找到: {tool_name}")
        try:
            return await tool.execute(**arguments)
        except Exception as e:
            logger.error(f"Tool execution error: {tool_name} - {e}")
            return ToolResult(success=False, output="", error=str(e))

    def get_schemas(self) -> list[dict[str, Any]]:
        """获取所有工具的 Function Calling schema。"""
        return self._registry.list_tools()


tool_manager = ToolManager()
