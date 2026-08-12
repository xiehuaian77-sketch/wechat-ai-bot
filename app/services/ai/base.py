"""AI 提供商基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAIProvider(ABC):
    """AI 提供商抽象基类。"""

    name: str = "base"

    @abstractmethod
    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """发送聊天请求并返回回复文本。"""
        raise NotImplementedError

    @abstractmethod
    async def stream_chat(self, messages: list[dict[str, str]], **kwargs: Any):
        """流式聊天，yield 文本片段。"""
        raise NotImplementedError


__all__ = ["BaseAIProvider"]
