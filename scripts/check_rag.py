"""检查 RAG 知识库。"""

import sys
from pathlib import Path

from app.knowledge.vector_store import knowledge_store

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

knowledge_store.setup("auto")
r = knowledge_store.search("微信", top_k=3)
print(f"Search results: {len(r)}")
for x in r:
    print(f"  [{x['score']}] {x.get('text', '')[:50]}")
print(f"\nStats: {knowledge_store.get_stats()}")
