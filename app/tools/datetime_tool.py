"""日期时间查询工具。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.tools.base import BaseTool, ToolResult
from app.utils.logger import logger


class DateTimeTool(BaseTool):
    """日期时间查询工具。"""

    name = "datetime"
    description = "获取当前日期和时间"

    async def execute(self, **kwargs: Any) -> ToolResult:
        del kwargs
        try:
            now = datetime.now(UTC)
            formatted = now.strftime("%Y-%m-%d %H:%M:%S %Z")
            return ToolResult(success=True, output=formatted)
        except Exception as e:
            logger.error(f"DateTime tool error: {e}")
            return ToolResult(success=False, output="", error=str(e))


__all__ = ["DateTimeTool"]
