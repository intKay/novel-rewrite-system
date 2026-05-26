from pathlib import Path

import pytest

from novel_rewrite_system.projects import PROJECT_SUBDIRECTORIES, create_project_directories


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
