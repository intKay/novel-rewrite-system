"""初稿生成服务单元测试。"""

from pathlib import Path

import pytest

from novel_rewrite_system.errors import EmptyTextError, ProjectError
from novel_rewrite_system.generation.service import DraftGenerationResult, generate_draft
from novel_rewrite_system.models import FakeModelClient
from novel_rewrite_system.requirements import StoryRequirement


def _make_requirement(**kwargs: str | list[str] | None) -> StoryRequirement:
    return StoryRequirement(**kwargs)


class TestGenerateDraft:
    def test_returns_draft_text_with_valid_input(self) -> None:
        requirement = _make_requirement(theme="仙侠故事")
        style_report = "叙事视角：第三人称全知。句式偏长，描写细腻。"
        fake_client = FakeModelClient(text="第一章 剑出寒山\n\n天光微亮，云雾缭绕的孤峰上。")

        result = generate_draft(style_report, requirement, fake_client)

        assert isinstance(result, DraftGenerationResult)
        assert "第一章" in result.draft_text
        assert fake_client.last_request is not None

    def test_model_request_built_from_inputs(self) -> None:
        requirement = _make_requirement(raw_text="创作一个赛博修仙故事。")
        style_report = "风格分析：叙事紧凑，节奏快。"
        fake_client = FakeModelClient()

        generate_draft(style_report, requirement, fake_client)

        assert fake_client.last_request is not None
        request = fake_client.last_request
        assert "赛博修仙" in request.prompt
        assert "叙事紧凑" in request.prompt
        assert request.temperature == 0.8
        assert request.top_p == 0.9
        assert request.system_prompt is not None

    def test_prompt_requires_original_content(self) -> None:
        requirement = _make_requirement()
        style_report = "风格分析报告。"
        fake_client = FakeModelClient()

        generate_draft(style_report, requirement, fake_client)

        assert "完全原创" in fake_client.last_request.prompt

    def test_rejects_empty_style_report(self) -> None:
        requirement = _make_requirement()
        fake_client = FakeModelClient()

        with pytest.raises(EmptyTextError, match="风格分析报告不能为空"):
            generate_draft("", requirement, fake_client)

    def test_rejects_whitespace_only_style_report(self) -> None:
        requirement = _make_requirement()
        fake_client = FakeModelClient()

        with pytest.raises(EmptyTextError, match="风格分析报告不能为空"):
            generate_draft("   \n\t  ", requirement, fake_client)

    def test_rejects_empty_model_response(self) -> None:
        requirement = _make_requirement()
        style_report = "风格分析。"
        fake_client = FakeModelClient(text="   ")

        with pytest.raises(ProjectError, match="空文本"):
            generate_draft(style_report, requirement, fake_client)

    def test_rejects_empty_string_model_response(self) -> None:
        requirement = _make_requirement()
        style_report = "风格分析。"
        fake_client = FakeModelClient(text="")

        with pytest.raises(ProjectError, match="空文本"):
            generate_draft(style_report, requirement, fake_client)

    def test_passes_chapter_plan_to_prompt_builder(self) -> None:
        requirement = _make_requirement()
        style_report = "风格分析。"
        fake_client = FakeModelClient()

        generate_draft(
            style_report,
            requirement,
            fake_client,
            chapter_plan="第一章：觉醒；第二章：修炼；第三章：决战。",
        )

        assert "觉醒" in fake_client.last_request.prompt
        assert "修炼" in fake_client.last_request.prompt
        assert "决战" in fake_client.last_request.prompt

    def test_passes_target_word_count_to_prompt_builder(self) -> None:
        requirement = _make_requirement()
        style_report = "风格分析。"
        fake_client = FakeModelClient()

        generate_draft(style_report, requirement, fake_client, target_word_count=5000)

        assert "约 **5000** 字" in fake_client.last_request.prompt

    def test_passes_chapter_count_to_prompt_builder(self) -> None:
        requirement = _make_requirement()
        style_report = "风格分析。"
        fake_client = FakeModelClient()

        generate_draft(style_report, requirement, fake_client, chapter_count=3)

        assert "共 **3** 个章节" in fake_client.last_request.prompt

    def test_prompt_includes_requirement_fields(self) -> None:
        requirement = _make_requirement(
            theme="废土修仙",
            protagonist="独臂刀客",
            forbidden_content=["不要后宫"],
            required_plot_points=["主角最终重铸断刀"],
        )
        style_report = "风格分析报告。"
        fake_client = FakeModelClient()

        generate_draft(style_report, requirement, fake_client)

        prompt = fake_client.last_request.prompt
        assert "废土修仙" in prompt
        assert "独臂刀客" in prompt
        assert "不要后宫" in prompt
        assert "主角最终重铸断刀" in prompt

    def test_saves_draft_when_project_path_given(self, tmp_path: Path) -> None:
        requirement = _make_requirement()
        style_report = "风格分析。"
        fake_client = FakeModelClient(text="第一章 测试初稿内容。")

        generate_draft(style_report, requirement, fake_client, project_path=tmp_path)

        draft_file = tmp_path / "drafts" / "draft.md"
        assert draft_file.exists()
        assert draft_file.read_text(encoding="utf-8") == "第一章 测试初稿内容。"

    def test_creates_drafts_dir_if_missing(self, tmp_path: Path) -> None:
        requirement = _make_requirement()
        style_report = "风格分析。"
        fake_client = FakeModelClient(text="初稿文本。")
        assert not (tmp_path / "drafts").exists()

        generate_draft(style_report, requirement, fake_client, project_path=tmp_path)

        assert (tmp_path / "drafts").is_dir()

    def test_does_not_save_when_no_project_path(self, tmp_path: Path) -> None:
        requirement = _make_requirement()
        style_report = "风格分析。"
        fake_client = FakeModelClient(text="初稿文本。")

        generate_draft(style_report, requirement, fake_client)

        assert not (tmp_path / "drafts").exists()

    def test_fake_client_records_last_request(self) -> None:
        requirement = _make_requirement()
        style_report = "风格分析。"
        fake_client = FakeModelClient()
        assert fake_client.last_request is None

        generate_draft(style_report, requirement, fake_client)

        assert fake_client.last_request is not None
        assert isinstance(fake_client.last_request.prompt, str)

    def test_does_not_call_network(self) -> None:
        requirement = _make_requirement()
        style_report = "风格分析。"
        fake_client = FakeModelClient(text="纯函数生成的初稿。")

        result = generate_draft(style_report, requirement, fake_client)

        assert result.draft_text == "纯函数生成的初稿。"

    def test_empty_requirement_still_produces_result(self) -> None:
        requirement = StoryRequirement()
        style_report = "风格分析报告。"
        fake_client = FakeModelClient(text="初稿内容。")

        result = generate_draft(style_report, requirement, fake_client)

        assert isinstance(result, DraftGenerationResult)
        assert result.draft_text == "初稿内容。"
