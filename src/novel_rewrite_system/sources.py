"""手动参考文本输入与保存。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ManualTextInput(BaseModel):
    """用户手动粘贴的参考小说文本。"""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(description="参考文本唯一标识")
    title: str = Field(description="参考文本标题")
    text: str = Field(description="参考正文")


class ManualSourceMetadata(BaseModel):
    """手动参考文本元数据。"""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    title: str
    created_at: datetime
    input_type: Literal["manual"] = "manual"


def save_manual_source(
    project_path: str | Path,
    manual_input: ManualTextInput,
    *,
    created_at: datetime | None = None,
) -> ManualSourceMetadata:
    """保存手动输入正文和对应元数据到项目 sources 目录。"""

    source_id = _validate_path_part(manual_input.source_id, "source_id")
    title = manual_input.title.strip()
    if not title:
        raise ValueError("title 不能为空")

    text = _normalize_text(manual_input.text)
    if not text:
        raise ValueError("text 不能为空")

    sources_path = Path(project_path) / "sources"
    sources_path.mkdir(parents=True, exist_ok=True)

    metadata = ManualSourceMetadata(
        source_id=source_id,
        title=title,
        created_at=created_at or datetime.now(timezone.utc),
    )

    (sources_path / f"{source_id}.txt").write_text(text, encoding="utf-8")
    (sources_path / f"{source_id}.json").write_text(
        metadata.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )

    return metadata


def _validate_path_part(value: str, field_name: str) -> str:
    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError(f"{field_name} 不能为空")
    if normalized_value in {".", ".."} or "/" in normalized_value or "\\" in normalized_value:
        raise ValueError(f"{field_name} 不能包含路径分隔符")
    return normalized_value


def _normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()
