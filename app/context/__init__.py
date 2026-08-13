"""上下文工程：用户记忆 + 知识库检索 + 工具结果缓存。"""

from __future__ import annotations

import hashlib
import json
from contextlib import suppress
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select

from app.database.models import Conversation, KnowledgeDocument, User
from app.database.session import session_scope


class UserMemory:
    """用户长期记忆管理。"""

    @staticmethod
    async def get_user_memory(user_id: str) -> dict[str, Any]:
        """获取用户长期记忆（偏好、历史问题、画像）。"""
        async with session_scope() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return {}

            return {
                "user_id": str(user.id),
                "wechat_id": user.wechat_id,
                "nickname": user.nickname,
                "role": user.role,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }

    @staticmethod
    async def get_conversation_context(conversation_id: str) -> dict[str, Any]:
        """获取对话上下文（用户画像、当前场景、意图等）。"""
        async with session_scope() as session:
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conv = result.scalar_one_or_none()
            if not conv:
                return {}

            context = {
                "conversation_id": str(conv.id),
                "session_id": conv.session_id,
                "status": conv.status,
            }
            if conv.context:
                with suppress(json.JSONDecodeError):
                    context.update(json.loads(str(conv.context)))
            return context


class KnowledgeBase:
    """知识库检索。"""

    @staticmethod
    async def search(query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """检索知识库（简单关键词匹配）。"""
        async with session_scope() as session:
            result = await session.execute(
                select(KnowledgeDocument)
                .where(KnowledgeDocument.content.contains(query))
                .limit(top_k)
            )
            docs = result.scalars().all()
            return [{"id": str(d.id), "title": d.title, "content": d.content} for d in docs]

    @staticmethod
    async def get_by_id(doc_id: str) -> dict[str, Any] | None:
        """获取知识库文档详情。"""
        async with session_scope() as session:
            result = await session.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
            )
            doc = result.scalar_one_or_none()
            if not doc:
                return None
            return {"id": str(doc.id), "title": doc.title, "content": doc.content}


class ToolResultCache:
    """工具调用结果缓存（避免重复调用）。"""

    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}

    def _make_key(self, tool_name: str, input_hash: str) -> str:
        return hashlib.md5(f"{tool_name}:{input_hash}".encode()).hexdigest()

    def get(self, tool_name: str, input_hash: str, ttl_seconds: int = 300) -> dict[str, Any] | None:
        """获取缓存结果（TTL 5 分钟）。"""
        key = self._make_key(tool_name, input_hash)
        entry = self._cache.get(key)
        if not entry:
            return None
        if datetime.utcnow() - entry["created_at"] > timedelta(seconds=ttl_seconds):
            del self._cache[key]
            return None
        return entry["data"]

    def set(self, tool_name: str, input_hash: str, data: dict[str, Any]) -> None:
        """写入缓存。"""
        key = self._make_key(tool_name, input_hash)
        self._cache[key] = {"created_at": datetime.utcnow(), "data": data}

    def clear(self) -> None:
        """清空缓存。"""
        self._cache.clear()


# 全局单例
tool_result_cache = ToolResultCache()
