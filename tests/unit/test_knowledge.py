"""知识库（ChromaDB）单元测试。"""
from __future__ import annotations

import pytest

from app.knowledge.vector_store import KnowledgeStore


@pytest.fixture
def temp_knowledge(tmp_path: pytest.TempPathFactory) -> KnowledgeStore:
    store = KnowledgeStore()
    store.setup(collection_name="test_collection")
    yield store
    # 清理测试集合


def test_knowledge_store_add_and_search(temp_knowledge: KnowledgeStore):
    import asyncio

    async def do() -> None:
        await temp_knowledge.add_documents(
            documents=["Python 是一种编程语言", "FastAPI 是一个 Web 框架"],
            metadatas=[{"source": "test1"}, {"source": "test2"}],
        )
        results = await temp_knowledge.search("Python 是什么", top_k=2)
        assert len(results) > 0
        assert "Python" in results[0]["text"]

    asyncio.run(do())


def test_knowledge_store_stats(temp_knowledge: KnowledgeStore):
    import asyncio

    async def do() -> None:
        await temp_knowledge.add_documents(documents=["测试文档"], metadatas=[{"source": "test"}])
        stats = temp_knowledge.get_stats()
        assert "count" in stats
        assert stats["count"] >= 1

    asyncio.run(do())
