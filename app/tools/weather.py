"""天气查询工具。"""

from __future__ import annotations

from typing import Any

import httpx

from app.tools.base import BaseTool, ToolResult
from app.utils.logger import logger


class WeatherTool(BaseTool):
    """天气查询工具。"""

    name = "weather"
    description = "查询指定城市的天气信息"

    async def execute(self, **kwargs: Any) -> ToolResult:
        city = kwargs.get("city", "Beijing")
        # 这里使用免费的天气 API，实际生产环境应替换为稳定的天气服务
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 使用 wttr.in 免费天气服务
                resp = await client.get(f"https://wttr.in/{city}?format=%l:+%c+%t+%h+%w+%p")
                if resp.status_code == 200:
                    text = resp.text.strip()
                    return ToolResult(success=True, output=text)
                return ToolResult(success=False, output="", error=f"HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"Weather tool error: {e}")
            return ToolResult(success=False, output="", error=str(e))


__all__ = ["WeatherTool"]
