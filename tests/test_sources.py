import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from novel_rewrite_system.sources import ManualTextInput, save_manual_source


def test_save_manual_source_writes_text_and_metadata(tmp_path: Path) -> None:
    created_at = datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc)
    manual_input = ManualTextInput(
        source_id="source-1",
        title="参考小说",
        text="第一章\n正文内容。",
    )

    metadata = save_manual_source(tmp_path, manual_input, created_at=created_at)

    sources_path = tmp_path / "sources"
    assert (sources_path / "source-1.txt").read_text(encoding="utf-8") == "第一章\n正文内容。"

    metadata_data = json.loads((sources_path / "source-1.json").read_text(encoding="utf-8"))
    assert metadata_data == {
        "source_id": "source-1",
        "title": "参考小说",
        "created_at": "2026-05-26T12:00:00Z",
        "input_type": "manual",
    }
    assert metadata.source_id == "source-1"
    assert metadata.title == "参考小说"
    assert metadata.created_at == created_at
    assert metadata.input_type == "manual"


def test_save_manual_source_rejects_blank_text(tmp_path: Path) -> None:
    manual_input = ManualTextInput(source_id="source-1", title="参考小说", text="  ")

    with pytest.raises(ValueError, match="text 不能为空"):
        save_manual_source(tmp_path, manual_input)


@pytest.mark.parametrize(
    ("source_id", "message"),
    [
        (" ", "source_id 不能为空"),
        ("../source", "source_id 不能包含路径分隔符"),
        (r"source\1", "source_id 不能包含路径分隔符"),
        (".", "source_id 不能包含路径分隔符"),
    ],
)
def test_save_manual_source_rejects_invalid_source_id(
    tmp_path: Path, source_id: str, message: str
) -> None:
    manual_input = ManualTextInput(source_id=source_id, title="参考小说", text="正文")

    with pytest.raises(ValueError, match=message):
        save_manual_source(tmp_path, manual_input)
