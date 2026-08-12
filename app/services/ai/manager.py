"""AI 提供商管理器。"""
from __future__ import annotations

from app.services.ai.factory import ProviderFactory
from app.utils.logger import logger


class AIManager:
    """AI 提供商管理器，支持多模型负载均衡和故障转移。"""

    def __init__(self) -> None:
        self._providers: dict[str, Any] = {}

    def get_provider(self, provider_name: str, model: str | None = None):
        """获取 AI 提供商实例（懒加载）。"""
        key = f"{provider_name}:{model}" if model else provider_name
        if key not in self._providers:
            # custom provider 不走 model map，直接创建
            if provider_name == "custom":
                instance = ProviderFactory.create("custom")
                if model and hasattr(instance, "_model"):
                    instance._model = model
                self._providers[key] = instance
            else:
                provider_key, resolved_model = ProviderFactory.resolve_model(model or provider_name)
                instance = ProviderFactory.create(provider_key)
                # 如果是 OpenAI 兼容，注入自定义 model
                if hasattr(instance, "_model") and resolved_model:
                    instance._model = resolved_model
                elif hasattr(instance, "_model") and not resolved_model:
                    # 使用 provider 默认 model（从 settings 或构造函数参数）
                    pass
                self._providers[key] = instance
        return self._providers[key]

    async def chat(self, provider_name: str, messages: list[dict[str, str]], model: str | None = None, **kwargs: dict):
        """发送聊天请求。"""
        provider = self.get_provider(provider_name, model)
        logger.info(f"Using provider: {provider.name} / model: {getattr(provider, '_model', 'unknown')}")
        return await provider.chat(messages, **kwargs)

    async def stream_chat(self, provider_name: str, messages: list[dict[str, str]], model: str | None = None, **kwargs: dict):
        """流式聊天。"""
        provider = self.get_provider(provider_name, model)
        logger.info(f"Streaming with provider: {provider.name} / model: {getattr(provider, '_model', 'unknown')}")
        async for chunk in provider.stream_chat(messages, **kwargs):
            yield chunk


ai_manager = AIManager()
