"""ChromaDB 向量存储。"""

from __future__ import annotations

from typing import Any

import chromadb
from chromadb.api.client import ClientAPI
from chromadb.api.models.Collection import Collection

from app.utils.logger import logger
from config.settings import settings


class KnowledgeStore:
    """ChromaDB 知识库存储。"""

    def __init__(self) -> None:
        self._client: ClientAPI | None = None
        self._collection: Collection | None = None

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
        assert self._collection is not None
        ids = [f"doc_{i}_{hash(d)}" for i, d in enumerate(documents)]
        self._collection.add(
            documents=documents,
            metadatas=metadatas or [],  # type: ignore[arg-type]
            ids=ids,
        )

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """检索相似文档。"""
        if self._collection is None:
            self.setup()
        assert self._collection is not None
        results = self._collection.query(query_texts=[query], n_results=top_k)
        docs: list[str] = list((results.get("documents") or [[]])[0] or [])
        dists: list[float] = list((results.get("distances") or [[]])[0] or [])
        return [{"text": doc, "score": float(dist)} for doc, dist in zip(docs, dists, strict=True)]

    def get_stats(self) -> dict[str, Any]:
        """获取知识库统计信息。"""
        if self._collection is None:
            return {"count": 0}
        return {"count": self._collection.count()}


knowledge_store = KnowledgeStore()

__all__ = ["KnowledgeStore", "knowledge_store"]
