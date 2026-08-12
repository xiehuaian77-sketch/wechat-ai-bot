"""AI 提供商工厂。"""
from __future__ import annotations

from typing import ClassVar

from app.services.ai.anthropic_provider import AnthropicProvider
from app.services.ai.custom_provider import CustomProvider
from app.services.ai.openai_provider import OpenAIProvider


class ProviderFactory:
    """AI 提供商工厂，支持动态创建不同模型的实例。"""

    _providers: ClassVar[dict[str, type]] = {
        # OpenAI 兼容接口（OpenAI / DeepSeek / OpenRouter / Qwen / GLM / Moonshot / Yi / Baichuan / MiniMax）
        "openai": OpenAIProvider,
        "deepseek": OpenAIProvider,
        "openrouter": OpenAIProvider,
        "qwen": OpenAIProvider,
        "glm": OpenAIProvider,
        "moonshot": OpenAIProvider,
        "yi": OpenAIProvider,
        "baichuan": OpenAIProvider,
        "minimax": OpenAIProvider,
        # 自定义 OpenAI 兼容接口（代理 / 中转）
        "custom": CustomProvider,
        # Anthropic 接口（Claude）
        "anthropic": AnthropicProvider,
        "claude": AnthropicProvider,
    }

    # 模型 -> (provider_key, model_name) 映射
    _model_map: ClassVar[dict[str, tuple[str, str]]] = {
        # OpenAI
        "gpt-4o": ("openai", "gpt-4o"),
        "gpt-4o-mini": ("openai", "gpt-4o-mini"),
        "gpt-4-turbo": ("openai", "gpt-4-turbo"),
        "gpt-4": ("openai", "gpt-4"),
        "o1-preview": ("openai", "o1-preview"),
        # DeepSeek
        "deepseek-chat": ("deepseek", "deepseek-chat"),
        "deepseek-reasoner": ("deepseek", "deepseek-reasoner"),
        # Qwen (通义千问)
        "qwen-turbo": ("qwen", "qwen-turbo"),
        "qwen-plus": ("qwen", "qwen-plus"),
        "qwen-max": ("qwen", "qwen-max"),
        "qwen-long": ("qwen", "qwen-long"),
        # GLM (智谱)
        "glm-4": ("glm", "glm-4"),
        "glm-4-flash": ("glm", "glm-4-flash"),
        "glm-4v": ("glm", "glm-4v"),
        # Moonshot (Kimi)
        "moonshot-v1-8k": ("moonshot", "moonshot-v1-8k"),
        "moonshot-v1-32k": ("moonshot", "moonshot-v1-32k"),
        "moonshot-v1-128k": ("moonshot", "moonshot-v1-128k"),
        # Yi (零一万物)
        "yi-lightning": ("yi", "yi-lightning"),
        "yi-large": ("yi", "yi-large"),
        "yi-medium": ("yi", "yi-medium"),
        # Baichuan (百川)
        "baichuan2-turbo": ("baichuan", "Baichuan2-Turbo"),
        "baichuan2-53b": ("baichuan", "Baichuan2-53B"),
        # MiniMax
        "minimax/minimax-01": ("minimax", "minimax/MiniMax-Mini-01"),
        # Anthropic
        "claude-3-5-sonnet-20241022": ("anthropic", "claude-3-5-sonnet-20241022"),
        "claude-3-5-haiku-20241022": ("anthropic", "claude-3-5-haiku-20241022"),
        "claude-3-opus-20240229": ("anthropic", "claude-3-opus-20240229"),
        "claude-3-sonnet-20240229": ("anthropic", "claude-3-sonnet-20240229"),
    }

    @classmethod
    def resolve_model(cls, model_name: str) -> tuple[str, str]:
        """解析模型名，返回 (provider_key, model_name)。

        如果 model_name 是已知 provider 名称，直接返回该 provider 和空模型名。
        如果 model_name 不在映射表中，尝试直接作为 OpenAI 兼容模型使用。
        """
        if model_name in cls._providers:
            return (model_name, "")
        if model_name in cls._model_map:
            return cls._model_map[model_name]
        # 默认当作 OpenAI 兼容
        return ("openai", model_name)

    @classmethod
    def create(cls, provider_name: str, **kwargs):
        """创建指定提供商实例。"""
        provider_name = provider_name.lower()
        if provider_name not in cls._providers:
            raise ValueError(f"未知的 AI 提供商: {provider_name}")
        return cls._providers[provider_name](**kwargs)

    @classmethod
    def list_models(cls) -> dict[str, list[str]]:
        """列出所有支持的模型。"""
        models: dict[str, list[str]] = {}
        for model, (provider, _) in cls._model_map.items():
            models.setdefault(provider, []).append(model)
        return models


__all__ = ["ProviderFactory"]
