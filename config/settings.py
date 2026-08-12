"""全局配置（Pydantic Settings）。"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def get_settings() -> "Settings":
    """单例配置加载。"""
    return Settings()


class Settings(BaseSettings):
    """应用全局配置。"""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # =========================================================================
    # 应用基础
    # =========================================================================
    APP_NAME: str = "WeChat AI Bot"
    APP_VERSION: str = "0.1.0"
    APP_ENV: Literal["development", "staging", "production", "testing"] = "development"
    DEBUG: bool = Field(default=True, description="调试模式")

    # =========================================================================
    # 服务器
    # =========================================================================
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    SERVER_WORKERS: int = 1
    SERVER_RELOAD: bool = False

    # =========================================================================
    # ComWeChatRobot
    # =========================================================================
    WECHAT_HOOK_URL: str = Field(
        default="http://127.0.0.1:19088",
        description="ComWeChatRobot HTTP Hook 地址",
    )
    WECHAT_HOOK_SECRET: SecretStr = Field(
        default=SecretStr(""),
        description="Hook 鉴权密钥（可空）",
    )
    WECHAT_RECONNECT_MAX_RETRIES: int = Field(default=10, description="微信断线最大重试次数")

    # =========================================================================
    # AI 模型配置
    # =========================================================================
    OPENAI_API_KEY: SecretStr = Field(default=SecretStr(""), description="OpenAI API Key")
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    DEEPSEEK_API_KEY: SecretStr = Field(default=SecretStr(""), description="DeepSeek API Key")
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    ANTHROPIC_API_KEY: SecretStr = Field(default=SecretStr(""), description="Anthropic API Key")
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-20241022"

    GOOGLE_API_KEY: SecretStr = Field(default=SecretStr(""), description="Google API Key")
    GOOGLE_MODEL: str = "gemini-pro"

    OPENROUTER_API_KEY: SecretStr = Field(default=SecretStr(""), description="OpenRouter API Key")
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"

    # =========================================================================
    # 自定义 OpenAI 兼容接口（如代理 / 中转）
    # =========================================================================
    CUSTOM_API_KEY: SecretStr = Field(default=SecretStr(""), description="Custom OpenAI-compatible API Key")
    CUSTOM_BASE_URL: str = Field(default="https://api.openai.com/v1", description="Custom OpenAI-compatible Base URL")
    CUSTOM_MODEL: str = Field(default="gpt-4o-mini", description="Custom OpenAI-compatible Model")

    # =========================================================================
    # 数据库
    # =========================================================================
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/wechat_ai_bot.db"

    # =========================================================================
    # Redis (可选)
    # =========================================================================
    REDIS_ENABLED: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"

    # =========================================================================
    # 知识库
    # =========================================================================
    CHROMA_DB_PATH: str = "./data/chroma_db"
    CHROMA_COLLECTION_NAME: str = "wechat_knowledge"

    # =========================================================================
    # 日志
    # =========================================================================
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    # =========================================================================
    # 限流
    # =========================================================================
    RATE_LIMIT_GLOBAL: int = 100
    RATE_LIMIT_USER: int = 20
    RATE_LIMIT_IP: int = 50

    # =========================================================================
    # 管理后台
    # =========================================================================
    ADMIN_WHITELIST: str = Field(default="", description="管理员微信 ID 列表，逗号分隔")
    GROUP_BLACKLIST: str = Field(default="", description="群黑名单，逗号分隔")

    # =========================================================================
    # JWT
    # =========================================================================
    JWT_SECRET_KEY: SecretStr = Field(
        default=SecretStr(""), description="JWT 签名密钥（生产环境必须修改）"
    )

    # =========================================================================
    # Sentry（错误追踪）
    # =========================================================================
    SENTRY_DSN: str = Field(default="", description="Sentry DSN（为空时禁用）")


settings = get_settings()
