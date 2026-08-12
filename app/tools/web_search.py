"""网络搜索工具。"""
from __future__ import annotations

from typing import Any

import httpx

from app.tools.base import BaseTool, ToolResult
from app.utils.logger import logger


class WebSearchTool(BaseTool):
    """网络搜索工具。"""

    name = "web_search"
    description = "搜索互联网信息"

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query", "")
        if not query:
            return ToolResult(success=False, output="", error="No query provided")

        try:
            # 使用 DuckDuckGo 即时回答 API（无需 API Key）
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_html": 1},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    abstract = data.get("AbstractText") or data.get("Abstract", "")
                    if abstract:
                        return ToolResult(success=True, output=abstract)
                    return ToolResult(
                        success=True,
                        output="No direct answer found. Try rephrasing your query.",
                    )
                return ToolResult(success=False, output="", error=f"HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return ToolResult(success=False, output="", error=str(e))


__all__ = ["WebSearchTool"]
