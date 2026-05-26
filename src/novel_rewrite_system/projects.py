"""项目目录初始化。"""

from pathlib import Path


PROJECT_SUBDIRECTORIES = (
    "config",
    "sources",
    "analysis",
    "drafts",
    "revisions",
    "final",
    "logs",
)


def create_project_directories(project_root: str | Path, project_id: str) -> Path:
    """根据 project_id 创建项目目录及标准子目录。"""

    project_name = project_id.strip()
    if not project_name:
        raise ValueError("project_id 不能为空")
    if project_name in {".", ".."} or "/" in project_name or "\\" in project_name:
        raise ValueError("project_id 不能包含路径分隔符")

    project_path = Path(project_root) / project_name
    project_path.mkdir(parents=True, exist_ok=True)

    for directory in PROJECT_SUBDIRECTORIES:
        (project_path / directory).mkdir(exist_ok=True)

    return project_path
