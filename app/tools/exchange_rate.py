"""汇率查询工具。"""

from __future__ import annotations

from typing import Any

import httpx

from app.tools.base import BaseTool, ToolResult
from app.utils.logger import logger


class ExchangeRateTool(BaseTool):
    """汇率查询工具。"""

    name = "exchange_rate"
    description = "查询货币汇率"

    async def execute(self, **kwargs: Any) -> ToolResult:
        from_currency = kwargs.get("from_currency", "USD")
        to_currency = kwargs.get("to_currency", "CNY")
        try:
            # 使用免费的汇率 API
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
                )
                if resp.status_code == 200:
                    data = resp.json()
                    rate = data.get("rates", {}).get(to_currency)
                    if rate:
                        return ToolResult(
                            success=True,
                            output=f"1 {from_currency} = {rate} {to_currency}",
                        )
                    return ToolResult(success=False, output="", error="Currency not found")
                return ToolResult(success=False, output="", error=f"HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"Exchange rate tool error: {e}")
            return ToolResult(success=False, output="", error=str(e))


__all__ = ["ExchangeRateTool"]
