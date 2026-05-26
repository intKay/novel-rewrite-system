import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from novel_rewrite_system.source_processing import process_manual_source
from novel_rewrite_system.sources import ManualTextInput


def test_process_manual_source_cleans_splits_and_saves(tmp_path: Path) -> None:
    created_at = datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc)
    manual_input = ManualTextInput(
        source_id="source-1",
        title="参考小说",
        text="  第一章 初见\r\n  第一段内容。\r\n\r\n\r\n第二段内容。  ",
    )

    result = process_manual_source(
        tmp_path,
        manual_input,
        chunk_chars=100,
        created_at=created_at,
    )

    sources_path = tmp_path / "sources"
    assert result.source_id == "source-1"
    assert result.cleaned_text_path == sources_path / "source-1.txt"
    assert result.chunks_path == sources_path / "source-1.chunks.json"
    assert result.chunk_count == 1

    assert result.cleaned_text_path.read_text(encoding="utf-8") == (
        "第一章 初见\n第一段内容。\n\n第二段内容。"
    )

    metadata_data = json.loads((sources_path / "source-1.json").read_text(encoding="utf-8"))
    assert metadata_data == {
        "source_id": "source-1",
        "title": "参考小说",
        "created_at": "2026-05-26T12:00:00Z",
        "input_type": "manual",
    }

    chunks_data = json.loads(result.chunks_path.read_text(encoding="utf-8"))
    assert chunks_data == {
        "source_id": "source-1",
        "title": "参考小说",
        "chunk_count": 1,
        "chunks": [
            {
                "source_id": "source-1",
                "chapter_title": "第一章 初见",
                "text": "第一段内容。\n\n第二段内容。",
                "order": 1,
            }
        ],
    }


def test_process_manual_source_respects_chunk_chars(tmp_path: Path) -> None:
    manual_input = ManualTextInput(
        source_id="source-1",
        title="参考小说",
        text="第一句比较短。第二句也比较短。",
    )

    result = process_manual_source(tmp_path, manual_input, chunk_chars=8)

    chunks_data = json.loads(result.chunks_path.read_text(encoding="utf-8"))
    assert result.chunk_count == 2
    assert [chunk["text"] for chunk in chunks_data["chunks"]] == [
        "第一句比较短。",
        "第二句也比较短。",
    ]


def test_process_manual_source_rejects_empty_cleaned_text(tmp_path: Path) -> None:
    manual_input = ManualTextInput(source_id="source-1", title="参考小说", text=" \n ")

    with pytest.raises(ValueError, match="text 不能为空"):
        process_manual_source(tmp_path, manual_input)

    assert not (tmp_path / "sources").exists()
