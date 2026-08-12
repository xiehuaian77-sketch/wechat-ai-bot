"""OpenAI 兼容提供商（OpenAI / DeepSeek / OpenRouter / Qwen / GLM 等）。"""
from __future__ import annotations

import os
from typing import Any

from openai import AsyncOpenAI

from app.services.ai.base import BaseAIProvider
from app.utils.logger import logger
from config.settings import settings


class OpenAIProvider(BaseAIProvider):
    """OpenAI 兼容提供商，支持自定义 base_url 和 model。"""

    name = "openai"

    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or settings.OPENAI_API_KEY.get_secret_value() or os.getenv("OPENAI_API_KEY", "")
        self._base_url = base_url or settings.OPENAI_BASE_URL
        self._model = model or settings.OPENAI_MODEL
        self._client = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )
        return self._client

    @property
    def model(self) -> str:
        return self._model

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """发送聊天请求并返回完整回复。"""
        try:
            response = await self.client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2048),
                **{k: v for k, v in kwargs.items() if k not in ("temperature", "max_tokens")},
            )
            content = response.choices[0].message.content or ""
            logger.info(f"[{self.name}/{self._model}] Response: {content[:100]}...")
            return content
        except Exception as e:
            logger.error(f"[{self.name}/{self._model}] Chat error: {e}")
            raise

    async def stream_chat(self, messages: list[dict[str, str]], **kwargs: Any):
        """流式聊天，yield 文本片段。"""
        try:
            stream = await self.client.chat.completions.create(
                model=self._model,
                messages=messages,
                stream=True,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2048),
                **{k: v for k, v in kwargs.items() if k not in ("temperature", "max_tokens")},
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"[{self.name}/{self._model}] Stream error: {e}")
            raise


__all__ = ["OpenAIProvider"]
