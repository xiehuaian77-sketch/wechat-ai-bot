"""Anthropic (Claude) 提供商。"""
from __future__ import annotations

import os
from typing import Any

from anthropic import AsyncAnthropic
from app.services.ai.base import BaseAIProvider
from config.settings import settings
from app.utils.logger import logger


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude 提供商。"""

    name = "anthropic"

    def __init__(self) -> None:
        self._client: AsyncAnthropic | None = None

    @property
    def client(self) -> AsyncAnthropic:
        if self._client is None:
            self._client = AsyncAnthropic(
                api_key=settings.ANTHROPIC_API_KEY.get_secret_value() or os.getenv("ANTHROPIC_API_KEY", ""),
            )
        return self._client

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        # Anthropic 使用 system 参数分开传递
        system_message = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                chat_messages.append(msg)

        response = await self.client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            system=system_message,
            messages=chat_messages,
            max_tokens=4096,
            **kwargs,
        )
        return response.content[0].text if response.content else ""

    async def stream_chat(self, messages: list[dict[str, str]], **kwargs: Any):
        system_message = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                chat_messages.append(msg)

        with self.client.messages.stream(
            model=settings.ANTHROPIC_MODEL,
            system=system_message,
            messages=chat_messages,
            max_tokens=4096,
            **kwargs,
        ) as stream:
            async for text in stream.text_stream:
                yield text


__all__ = ["AnthropicProvider"]
