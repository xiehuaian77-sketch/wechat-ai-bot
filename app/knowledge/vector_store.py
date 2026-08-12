"""ChromaDB 向量存储。"""

from __future__ import annotations

from typing import Any

import chromadb

from app.utils.logger import logger
from config.settings import settings


class KnowledgeStore:
    """ChromaDB 知识库存储。"""

    def __init__(self) -> None:
        self._client = None
        self._collection = None

    def setup(self, collection_name: str | None = None) -> None:
        """初始化 ChromaDB。"""
        name = collection_name or settings.CHROMA_COLLECTION_NAME
        self._client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
        )
        self._collection = self._client.get_or_create_collection(name=name)
        logger.info(f"ChromaDB initialized: {name}")

    async def add_documents(
        self, documents: list[str], metadatas: list[dict] | None = None
    ) -> None:
        """添加文档到向量库。"""
        if self._collection is None:
            self.setup()
        ids = [f"doc_{i}_{hash(d)}" for i, d in enumerate(documents)]
        self._collection.add(documents=documents, metadatas=metadatas or [], ids=ids)

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """检索相似文档。"""
        if self._collection is None:
            self.setup()
        results = self._collection.query(query_texts=[query], n_results=top_k)
        docs = results.get("documents", [[]])[0]
        dists = results.get("distances", [[]])[0]
        return [{"text": doc, "score": float(dist)} for doc, dist in zip(docs, dists, strict=True)]

    def get_stats(self) -> dict[str, Any]:
        """获取知识库统计信息。"""
        if self._collection is None:
            return {"count": 0}
        return {"count": self._collection.count()}


knowledge_store = KnowledgeStore()

__all__ = ["KnowledgeStore", "knowledge_store"]
