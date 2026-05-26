import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from novel_rewrite_system.projects import (
    PROJECT_INDEX_FILENAME,
    PROJECT_SUBDIRECTORIES,
    ProjectIndexRecord,
    add_project_record,
    create_project_directories,
    get_project_record,
    list_project_records,
)


def test_create_project_directories(tmp_path: Path) -> None:
    project_path = create_project_directories(tmp_path, "novel-001")

    assert project_path == tmp_path / "novel-001"
    assert project_path.is_dir()
    for directory in PROJECT_SUBDIRECTORIES:
        assert (project_path / directory).is_dir()


def test_create_project_directories_is_idempotent(tmp_path: Path) -> None:
    first_path = create_project_directories(tmp_path, "novel-001")
    second_path = create_project_directories(tmp_path, "novel-001")

    assert first_path == second_path
    for directory in PROJECT_SUBDIRECTORIES:
        assert (second_path / directory).is_dir()


def test_create_project_directories_rejects_blank_project_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="project_id 不能为空"):
        create_project_directories(tmp_path, " ")


@pytest.mark.parametrize("project_id", ["../novel", "novel/001", r"novel\001", "."])
def test_create_project_directories_rejects_path_like_project_id(
    tmp_path: Path, project_id: str
) -> None:
    with pytest.raises(ValueError, match="project_id 不能包含路径分隔符"):
        create_project_directories(tmp_path, project_id)


def test_list_project_records_returns_empty_list_when_index_missing(tmp_path: Path) -> None:
    assert list_project_records(tmp_path) == []


def test_add_project_record_writes_readable_json_index(tmp_path: Path) -> None:
    created_at = datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc)
    record = ProjectIndexRecord(
        project_id="novel-001",
        name="第一本小说",
        created_at=created_at,
    )

    added_record = add_project_record(tmp_path, record)

    assert added_record == record
    index_path = tmp_path / PROJECT_INDEX_FILENAME
    index_text = index_path.read_text(encoding="utf-8")
    assert index_text.endswith("\n")
    assert "\n  \"projects\": [\n" in index_text

    index_data = json.loads(index_text)
    assert index_data == {
        "projects": [
            {
                "project_id": "novel-001",
                "name": "第一本小说",
                "created_at": "2026-05-26T12:00:00Z",
            }
        ]
    }


def test_add_project_record_appends_and_list_records_preserves_order(tmp_path: Path) -> None:
    first = ProjectIndexRecord(project_id="novel-001", name="第一本小说")
    second = ProjectIndexRecord(project_id="novel-002", name="第二本小说")

    add_project_record(tmp_path, first)
    add_project_record(tmp_path, second)

    records = list_project_records(tmp_path)
    assert [record.project_id for record in records] == ["novel-001", "novel-002"]
    assert [record.name for record in records] == ["第一本小说", "第二本小说"]


def test_get_project_record_returns_record_by_project_id(tmp_path: Path) -> None:
    record = ProjectIndexRecord(project_id="novel-001", name="第一本小说")
    add_project_record(tmp_path, record)

    found_record = get_project_record(tmp_path, "novel-001")

    assert found_record is not None
    assert found_record.project_id == "novel-001"
    assert found_record.name == "第一本小说"


def test_get_project_record_returns_none_when_missing(tmp_path: Path) -> None:
    assert get_project_record(tmp_path, "novel-001") is None


def test_add_project_record_rejects_duplicate_project_id(tmp_path: Path) -> None:
    add_project_record(tmp_path, ProjectIndexRecord(project_id="novel-001", name="第一本小说"))

    with pytest.raises(ValueError, match="project_id 已存在: novel-001"):
        add_project_record(
            tmp_path,
            ProjectIndexRecord(project_id="novel-001", name="重复项目"),
        )


def test_list_project_records_rejects_duplicate_project_id_in_index(tmp_path: Path) -> None:
    index_path = tmp_path / PROJECT_INDEX_FILENAME
    index_path.write_text(
        json.dumps(
            {
                "projects": [
                    {
                        "project_id": "novel-001",
                        "name": "第一本小说",
                        "created_at": "2026-05-26T12:00:00Z",
                    },
                    {
                        "project_id": "novel-001",
                        "name": "重复项目",
                        "created_at": "2026-05-26T12:01:00Z",
                    },
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="project_id 重复: novel-001"):
        list_project_records(tmp_path)


def test_add_project_record_rejects_blank_name(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="name 不能为空"):
        add_project_record(tmp_path, ProjectIndexRecord(project_id="novel-001", name=" "))
