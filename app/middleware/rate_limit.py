"""滑动窗口限流中间件。"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from config.settings import settings
from app.utils.logger import logger


class RateLimitMiddleware(BaseHTTPMiddleware):
    """基于滑动窗口的限流中间件。"""

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self._global: deque[float] = deque()
        self._user: dict[str, deque[float]] = defaultdict(deque)
        self._ip: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        now = time.time()
        window = 60.0

        # 全局限流
        self._global.append(now)
        while self._global and now - self._global[0] > window:
            self._global.popleft()
        if len(self._global) > settings.RATE_LIMIT_GLOBAL:
            logger.warning("Global rate limit exceeded")
            return JSONResponse(status_code=429, content={"detail": "Too many requests"})

        # IP 限流
        client_ip = request.client.host if request.client else "unknown"
        self._ip[client_ip].append(now)
        while self._ip[client_ip] and now - self._ip[client_ip][0] > window:
            self._ip[client_ip].popleft()
        if len(self._ip[client_ip]) > settings.RATE_LIMIT_IP:
            logger.warning(f"IP rate limit exceeded: {client_ip}")
            return JSONResponse(status_code=429, content={"detail": "Too many requests from this IP"})

        return await call_next(request)


__all__ = ["RateLimitMiddleware"]
