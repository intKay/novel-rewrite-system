"""项目目录初始化与项目索引。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


PROJECT_SUBDIRECTORIES = (
    "config",
    "sources",
    "analysis",
    "drafts",
    "revisions",
    "final",
    "logs",
)
PROJECT_INDEX_FILENAME = "projects_index.json"


class ProjectIndexRecord(BaseModel):
    """本地项目索引中的单条项目记录。"""

    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(description="项目唯一标识")
    name: str = Field(description="项目显示名称")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="项目记录创建时间",
    )


class ProjectIndex(BaseModel):
    """projects_index.json 文件结构。"""

    model_config = ConfigDict(extra="forbid")

    projects: list[ProjectIndexRecord] = Field(default_factory=list)


def create_project_directories(project_root: str | Path, project_id: str) -> Path:
    """根据 project_id 创建项目目录及标准子目录。"""

    project_name = _validate_path_part(project_id, "project_id")

    project_path = Path(project_root) / project_name
    project_path.mkdir(parents=True, exist_ok=True)

    for directory in PROJECT_SUBDIRECTORIES:
        (project_path / directory).mkdir(exist_ok=True)

    return project_path


def add_project_record(
    project_root: str | Path,
    record: ProjectIndexRecord,
) -> ProjectIndexRecord:
    """向项目索引追加一条记录，project_id 重复时抛出明确错误。"""

    normalized_record = _normalize_project_record(record)
    records = list_project_records(project_root)
    if any(existing.project_id == normalized_record.project_id for existing in records):
        raise ValueError(f"project_id 已存在: {normalized_record.project_id}")

    records.append(normalized_record)
    _write_project_index(project_root, records)
    return normalized_record


def list_project_records(project_root: str | Path) -> list[ProjectIndexRecord]:
    """读取项目索引中的所有项目记录。"""

    index_path = _project_index_path(project_root)
    if not index_path.exists():
        return []

    index = _read_project_index(index_path)
    records = [_normalize_project_record(record) for record in index.projects]
    _ensure_unique_project_ids(records)
    return records


def get_project_record(
    project_root: str | Path,
    project_id: str,
) -> ProjectIndexRecord | None:
    """按 project_id 查询项目索引记录，不存在时返回 None。"""

    normalized_project_id = _validate_path_part(project_id, "project_id")
    for record in list_project_records(project_root):
        if record.project_id == normalized_project_id:
            return record
    return None


def _project_index_path(project_root: str | Path) -> Path:
    return Path(project_root) / PROJECT_INDEX_FILENAME


def _read_project_index(index_path: Path) -> ProjectIndex:
    try:
        return ProjectIndex.model_validate_json(index_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise ValueError("projects_index.json 格式无效") from exc


def _write_project_index(
    project_root: str | Path,
    records: list[ProjectIndexRecord],
) -> None:
    index_path = _project_index_path(project_root)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index = ProjectIndex(projects=records)
    index_path.write_text(index.model_dump_json(indent=2) + "\n", encoding="utf-8")


def _normalize_project_record(record: ProjectIndexRecord) -> ProjectIndexRecord:
    project_id = _validate_path_part(record.project_id, "project_id")
    name = record.name.strip()
    if not name:
        raise ValueError("name 不能为空")
    return record.model_copy(update={"project_id": project_id, "name": name})


def _ensure_unique_project_ids(records: list[ProjectIndexRecord]) -> None:
    seen_project_ids: set[str] = set()
    for record in records:
        if record.project_id in seen_project_ids:
            raise ValueError(f"project_id 重复: {record.project_id}")
        seen_project_ids.add(record.project_id)


def _validate_path_part(value: str, field_name: str) -> str:
    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError(f"{field_name} 不能为空")
    if normalized_value in {".", ".."} or "/" in normalized_value or "\\" in normalized_value:
        raise ValueError(f"{field_name} 不能包含路径分隔符")
    return normalized_value
