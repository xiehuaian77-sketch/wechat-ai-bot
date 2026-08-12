"""FastAPI 应用入口。"""

from __future__ import annotations

from datetime import UTC
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.api.router import router as api_router
from app.database.session import Base, engine
from app.knowledge.vector_store import knowledge_store
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers.wechat import router as wechat_router
from app.tools import register_all_tools
from config.settings import PROJECT_ROOT, settings

# =============================================================================
# Sentry 初始化（可选）
# =============================================================================
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.loguru import LoguruIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                LoguruIntegration(),
            ],
            traces_sample_rate=0.1 if settings.APP_ENV == "production" else 1.0,
            profiles_sample_rate=0.1 if settings.APP_ENV == "production" else 1.0,
            environment=settings.APP_ENV,
            release=f"wechat-ai-bot@{settings.APP_VERSION}",
        )
        logger.info("Sentry initialized")
    except Exception as exc:  # pragma: no cover - 初始化失败不影响服务启动
        logger.warning(f"Sentry init failed: {exc}")


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用。"""
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="基于 ComWeChatRobot 的 AI 智能微信机器人助手",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 限流中间件（应在其他中间件之前）
    application.add_middleware(RateLimitMiddleware)

    # CORS 配置
    if settings.APP_ENV == "development":
        allow_origins = ["http://localhost:3000", "http://localhost:8000"]
    else:
        allow_origins = [str(settings.WECHAT_HOOK_URL).rsplit("/", 1)[0]]

    application.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
        max_age=600,
    )

    # 注册工具
    register_all_tools()

    # 初始化知识库
    knowledge_store.setup()

    application.include_router(wechat_router, prefix="/hook", tags=["wechat"])
    application.include_router(api_router, prefix="/api", tags=["api"])

    # 挂载静态资源（管理面板）
    static_dir = PROJECT_ROOT / "static"
    if static_dir.exists():
        application.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @application.get("/health", tags=["system"])
    async def health() -> dict[str, Any]:
        """健康检查。"""
        from datetime import datetime

        return {
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
            "providers": [],
        }

    @application.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        """项目信息 / 管理面板入口。"""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "admin": "/static/index.html",
        }

    # 启动/关闭事件
    @application.on_event("startup")
    async def on_startup() -> None:
        logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        Path("data").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)

        # 仅在开发环境或单 worker 模式下初始化数据库表
        if settings.SERVER_WORKERS == 1 or settings.APP_ENV == "development":
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables initialized")
        else:
            logger.info("Skipping database initialization (multi-worker mode)")

    @application.on_event("shutdown")
    async def on_shutdown() -> None:
        logger.info("Shutting down...")

    return application


app = create_app()
