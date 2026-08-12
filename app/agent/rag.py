"""Agent 轻量级 RAG 知识库。"""
from __future__ import annotations

from typing import Any

from app.utils.logger import logger


class AgentRAG:
    """Agent RAG 知识库接口。"""

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """检索相关知识。"""
        logger.info(f"RAG search: {query}")
        return []

    async def add_document(self, title: str, content: str) -> None:
        """添加文档到知识库。"""
        logger.info(f"RAG add document: {title}")


agent_rag = AgentRAG()

__all__ = ["AgentRAG", "agent_rag"]
