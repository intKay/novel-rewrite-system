"""最小 WebUI 入口测试。"""

from pathlib import Path

import pytest

from novel_rewrite_system.models import FakeModelClient
from novel_rewrite_system.tags import get_default_tags
from novel_rewrite_system.webui import (
    _DEFAULT_REWRITE_INSTRUCTION,
    _resolve_reference_text,
    run_webui_continuation,
    run_webui_pipeline,
)


REFERENCE_TEXT = "夜色沉下来。她推开门，听见远处的钟声。院中无人。\n\n她缓步走向庭中老槐，心中涌起千般思绪。"


# ── 默认常量 ─────────────────────────────────────────────────


def test_default_rewrite_instruction_is_non_empty() -> None:
    assert isinstance(_DEFAULT_REWRITE_INSTRUCTION, str)
    assert len(_DEFAULT_REWRITE_INSTRUCTION) > 10


# ── _resolve_reference_text 单元测试 ──────────────────────────────


def test_resolve_no_file_uses_manual_text() -> None:
    assert _resolve_reference_text(None, "手动粘贴文本") == "手动粘贴文本"


def test_resolve_uploaded_file_uses_file_content() -> None:
    content = "文件内容".encode("utf-8")
    assert _resolve_reference_text(content, "手动文本") == "文件内容"


def test_resolve_empty_file_returns_empty() -> None:
    assert _resolve_reference_text(b"", "手动文本") == ""


def test_resolve_decode_error_raises_value_error() -> None:
    with pytest.raises(ValueError, match="文件解码失败"):
        _resolve_reference_text(b"\xff\xfe", "手动文本")


# ── run_webui_pipeline 集成测试 ─────────────────────────────────


def test_fake_mode_runs_minimal_pipeline(tmp_path: Path) -> None:
    project = tmp_path / "webui-output"

    result = run_webui_pipeline(
        project_path=project,
        reference_text=REFERENCE_TEXT,
        user_requirement_text="创作一个仙侠故事。",
        mode="fake",
    )

    assert result.ok
    assert result.pipeline_result is not None
    assert (project / "analysis" / "style_analysis_report.md").is_file()
    assert (project / "drafts" / "draft.md").is_file()
    assert (project / "revisions" / "rewritten.md").is_file()


def test_fake_mode_with_upload_content_runs_successfully(tmp_path: Path) -> None:
    """模拟上传文件内容作为参考文本，fake 模式仍可正常运行。"""
    project = tmp_path / "webui-upload-output"

    uploaded_bytes = "夜色沉下来。她推开门。".encode("utf-8")
    ref_text = _resolve_reference_text(uploaded_bytes, "")

    result = run_webui_pipeline(
        project_path=project,
        reference_text=ref_text,
        user_requirement_text="创作一个仙侠故事。",
        mode="fake",
    )

    assert result.ok
    assert result.pipeline_result is not None


def test_cloud_only_missing_api_key_returns_clear_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    result = run_webui_pipeline(
        project_path=tmp_path / "webui-output",
        reference_text=REFERENCE_TEXT,
        user_requirement_text="创作一个仙侠故事。",
        mode="cloud-only",
    )

    assert not result.ok
    assert result.error_code == "model_config_error"
    assert result.error_message is not None
    assert "DEEPSEEK_API_KEY" in result.error_message
    assert result.error_suggestion is not None
    assert "fake" in result.error_suggestion


def test_cloud_only_uses_deepseek_for_both_clients(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
    created_models: list[str] = []

    def _mock_deepseek(model: str = "deepseek-v4-flash") -> FakeModelClient:
        created_models.append(model)
        return FakeModelClient(text="mocked deepseek", provider="deepseek", model=model)

    monkeypatch.setattr("novel_rewrite_system.webui.DeepSeekClient", _mock_deepseek)

    result = run_webui_pipeline(
        project_path=tmp_path / "webui-output",
        reference_text=REFERENCE_TEXT,
        user_requirement_text="创作一个仙侠故事。",
        mode="cloud-only",
        deepseek_model="deepseek-v4-flash",
    )

    assert result.ok
    assert created_models == ["deepseek-v4-flash"]


def test_invalid_mode_returns_error(tmp_path: Path) -> None:
    result = run_webui_pipeline(
        project_path=tmp_path / "webui-output",
        reference_text=REFERENCE_TEXT,
        user_requirement_text="创作一个仙侠故事。",
        mode="real",
    )

    assert not result.ok
    assert result.error_code == "invalid_webui_mode"


# ── run_webui_continuation 测试 ──────────────────────────────


def test_continuation_fake_mode_returns_continuation() -> None:
    result = run_webui_continuation(
        current_text="夜色沉下来。她推开门。",
        continuation_instruction="续写下一段。",
        mode="fake",
    )

    assert result.ok
    assert result.continuation_text is not None
    assert len(result.continuation_text) > 0


def test_continuation_empty_current_text_returns_error() -> None:
    result = run_webui_continuation(
        current_text="",
        continuation_instruction="续写下一段。",
        mode="fake",
    )

    assert not result.ok
    assert result.error_code == "invalid_input"


def test_continuation_empty_instruction_returns_error() -> None:
    result = run_webui_continuation(
        current_text="夜色沉下来。",
        continuation_instruction="",
        mode="fake",
    )

    assert not result.ok
    assert result.error_code == "invalid_input"


def test_continuation_cloud_only_missing_api_key_returns_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    result = run_webui_continuation(
        current_text="夜色沉下来。",
        continuation_instruction="续写下一段。",
        mode="cloud-only",
    )

    assert not result.ok
    assert result.error_code == "model_config_error"


def test_continuation_fake_mode_no_network() -> None:
    """fake 模式不访问网络。"""
    result = run_webui_continuation(
        current_text="夜色沉下来。",
        continuation_instruction="续写下一段。",
        mode="fake",
    )

    assert result.ok
    assert result.continuation_text is not None


def test_continuation_with_tags_still_works() -> None:
    """选择标签后能正常续写。"""
    tags = get_default_tags()[:2]
    result = run_webui_continuation(
        current_text="夜色沉下来。",
        continuation_instruction="续写下一段。",
        mode="fake",
        selected_tags=tags,
    )

    assert result.ok
    assert result.continuation_text is not None


def test_continuation_without_tags_still_works() -> None:
    """不选择标签时续写行为不变。"""
    result = run_webui_continuation(
        current_text="夜色沉下来。",
        continuation_instruction="续写下一段。",
        mode="fake",
        selected_tags=None,
    )

    assert result.ok
    assert result.continuation_text is not None
