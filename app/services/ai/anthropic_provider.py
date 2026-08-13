"""Anthropic (Claude) 提供商。"""

from __future__ import annotations

import os
from typing import Any

from anthropic import AsyncAnthropic

from app.services.ai.base import BaseAIProvider
from config.settings import settings


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude 提供商。"""

    name = "anthropic"

    def __init__(self) -> None:
        self._client: AsyncAnthropic | None = None

    @property
    def client(self) -> AsyncAnthropic:
        if self._client is None:
            self._client = AsyncAnthropic(
                api_key=settings.ANTHROPIC_API_KEY.get_secret_value()
                or os.getenv("ANTHROPIC_API_KEY", ""),
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
            messages=chat_messages,  # type: ignore[arg-type]
            max_tokens=4096,
            **kwargs,
        )
        content = response.content[0] if response.content else None
        # SDK 返回 TextBlock 联合类型，运行期保证为 TextBlock
        return content.text if content else ""  # type: ignore[union-attr]

    async def stream_chat(self, messages: list[dict[str, str]], **kwargs: Any):
        system_message = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                chat_messages.append(msg)

        # 注意：AsyncAnthropic 必须使用 async with 打开流
        async with self.client.messages.stream(
            model=settings.ANTHROPIC_MODEL,
            system=system_message,
            messages=chat_messages,  # type: ignore[arg-type]
            max_tokens=4096,
            **kwargs,
        ) as stream:
            async for text in stream.text_stream:
                yield text


__all__ = ["AnthropicProvider"]
