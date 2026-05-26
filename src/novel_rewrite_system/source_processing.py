"""手动参考文本清洗、切分与保存的小集成入口。"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from novel_rewrite_system.sources import (
    ManualSourceMetadata,
    ManualTextInput,
    save_manual_source,
)
from novel_rewrite_system.text_cleaning import clean_text
from novel_rewrite_system.text_chunks import TextChunk, split_text


class ManualSourceProcessingResult(BaseModel):
    """手动参考文本处理后的保存摘要。"""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    cleaned_text_path: Path
    chunk_count: int
    chunks_path: Path


def process_manual_source(
    project_path: str | Path,
    manual_input: ManualTextInput,
    *,
    chunk_chars: int = 2000,
    created_at: datetime | None = None,
) -> ManualSourceProcessingResult:
    """保存手动参考文本的清洗正文，并将切片结果写入 sources 目录。"""

    cleaned_text = clean_text(manual_input.text)
    cleaned_input = manual_input.model_copy(update={"text": cleaned_text})
    metadata = save_manual_source(project_path, cleaned_input, created_at=created_at)

    chunks = split_text(metadata.source_id, cleaned_text, chunk_chars=chunk_chars)
    sources_path = Path(project_path) / "sources"
    cleaned_text_path = sources_path / f"{metadata.source_id}.txt"
    chunks_path = sources_path / f"{metadata.source_id}.chunks.json"
    _write_chunks_json(chunks_path, metadata, chunks)

    return ManualSourceProcessingResult(
        source_id=metadata.source_id,
        cleaned_text_path=cleaned_text_path,
        chunk_count=len(chunks),
        chunks_path=chunks_path,
    )


def _write_chunks_json(
    chunks_path: Path,
    metadata: ManualSourceMetadata,
    chunks: list[TextChunk],
) -> None:
    chunks_payload = {
        "source_id": metadata.source_id,
        "title": metadata.title,
        "chunk_count": len(chunks),
        "chunks": [asdict(chunk) for chunk in chunks],
    }
    chunks_path.write_text(
        json.dumps(chunks_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
