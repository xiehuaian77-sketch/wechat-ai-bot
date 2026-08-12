"""日志配置。"""
from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)
logger.add(
    LOG_DIR / "app.log",
    rotation="10 MB",
    retention="7 days",
    encoding="utf-8",
    level="DEBUG",
)

__all__ = ["logger"]
