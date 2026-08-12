"""Agent 记忆管理。"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.database.session import get_session
from app.database.models import Conversation, Message
from app.utils.logger import logger


class AgentMemory:
    """Agent 记忆管理，负责对话历史的持久化。"""

    async def save_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        model: str | None = None,
    ) -> None:
        """保存消息到数据库。"""
        try:
            async for session in get_session():
                conv = Conversation(
                    user_id=user_id,
                    session_id=session_id,
                    expires_at=datetime.utcnow() + timedelta(days=7),
                )
                session.add(conv)
                await session.flush()

                msg = Message(
                    conversation_id=conv.id,
                    role=role,
                    content=content,
                    model=model,
                )
                session.add(msg)
                await session.commit()
                break
        except Exception as e:
            logger.error(f"Save message error: {e}")

    async def get_history(self, user_id: str, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """获取对话历史。"""
        result = []
        try:
            async for session in get_session():
                from sqlalchemy import select
                from app.database.models import Conversation

                stmt = (
                    select(Conversation)
                    .where(Conversation.user_id == user_id, Conversation.session_id == session_id)
                    .order_by(Conversation.created_at.desc())
                    .limit(1)
                )
                conv = (await session.execute(stmt)).scalar_one_or_none()
                if conv:
                    from app.database.models import Message
                    msgs = (
                        await session.execute(
                            select(Message)
                            .where(Message.conversation_id == conv.id)
                            .order_by(Message.created_at.asc())
                            .limit(limit)
                        )
                    ).scalars().all()
                    result = [
                        {"role": m.role, "content": m.content, "model": m.model}
                        for m in msgs
                    ]
                break
        except Exception as e:
            logger.error(f"Get history error: {e}")
        return result


agent_memory = AgentMemory()

__all__ = ["AgentMemory", "agent_memory"]
