"""文档加载器。"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class DocumentLoader:
    """文档加载器，支持多种格式。"""

    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".csv", ".xlsx"}

    def load(self, file_path: str) -> dict[str, Any]:
        """加载文档。"""
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file format: {ext}")

        text = path.read_text(encoding="utf-8", errors="ignore")
        return {
            "title": path.name,
            "content": text,
            "source": str(path),
            "format": ext,
        }


__all__ = ["DocumentLoader"]
