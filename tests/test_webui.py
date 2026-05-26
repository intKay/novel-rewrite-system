"""最小 WebUI 入口测试。"""

from pathlib import Path

import pytest

from novel_rewrite_system.models import FakeModelClient
from novel_rewrite_system.webui import run_webui_pipeline


REFERENCE_TEXT = "夜色沉下来。她推开门，听见远处的钟声。院中无人。\n\n她缓步走向庭中老槐，心中涌起千般思绪。"


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
