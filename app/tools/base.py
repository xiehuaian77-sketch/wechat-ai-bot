"""工具基类。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    """工具执行结果。"""
    success: bool
    output: str
    error: str | None = None


class BaseTool(ABC):
    """工具抽象基类。"""

    name: str = "base"
    description: str = ""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """执行工具逻辑。"""
        raise NotImplementedError

    def to_schema(self) -> dict[str, Any]:
        """返回工具 schema（用于 Function Calling）。"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {},
        }


__all__ = ["BaseTool", "ToolResult"]
