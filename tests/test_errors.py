from novel_rewrite_system.errors import (
    ConfigError,
    DuplicateProjectError,
    EmptyTextError,
    ModelConfigError,
    ProjectError,
    ProjectNotFoundError,
    error_to_dict,
    error_to_text,
)


def test_project_error_has_user_readable_fields() -> None:
    error = ProjectError(
        "处理失败",
        suggestion="请检查输入。",
        details={"field": "title"},
        code="custom_error",
    )

    assert str(error) == "处理失败"
    assert error.to_dict() == {
        "code": "custom_error",
        "message": "处理失败",
        "suggestion": "请检查输入。",
        "details": {"field": "title"},
    }


def test_project_error_omits_empty_details() -> None:
    error = EmptyTextError()

    assert error.to_dict() == {
        "code": "empty_text",
        "message": "文本不能为空",
        "suggestion": "请提供非空文本后重试。",
    }


def test_error_to_dict_uses_project_error_format() -> None:
    error = ProjectNotFoundError(details={"project_id": "novel-001"})

    assert error_to_dict(error) == {
        "code": "project_not_found",
        "message": "项目不存在",
        "suggestion": "请确认项目 ID 是否正确，或先创建项目。",
        "details": {"project_id": "novel-001"},
    }


def test_error_to_text_uses_user_readable_chinese_message() -> None:
    text = error_to_text(DuplicateProjectError(details={"project_id": "novel-001"}))

    assert "[duplicate_project] 项目已存在" in text
    assert "建议：请更换 project_id，或使用已有项目。" in text
    assert "详情：{'project_id': 'novel-001'}" in text


def test_current_error_types_have_stable_codes() -> None:
    assert ConfigError().code == "config_error"
    assert EmptyTextError().code == "empty_text"
    assert ProjectNotFoundError().code == "project_not_found"
    assert DuplicateProjectError().code == "duplicate_project"
    assert ModelConfigError().code == "model_config_error"
