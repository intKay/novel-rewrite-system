"""初稿生成提示词构建器单元测试。"""

import pytest

from novel_rewrite_system.generation.prompts.draft import build_draft_generation_prompt
from novel_rewrite_system.models import ModelRequest
from novel_rewrite_system.requirements import StoryRequirement


class TestBuildDraftGenerationPrompt:
    def test_returns_model_request_with_minimal_input(self) -> None:
        requirement = StoryRequirement(raw_text="创作一个仙侠故事。")
        style_report = "叙事视角：第三人称全知。句式偏长，描写细腻。"

        result = build_draft_generation_prompt(style_report, requirement)

        assert isinstance(result, ModelRequest)
        assert result.prompt
        assert result.system_prompt
        assert "创作一个仙侠故事" in result.prompt
        assert "第三人称全知" in result.prompt
        assert result.temperature == 0.8

    def test_rejects_empty_style_report(self) -> None:
        requirement = StoryRequirement()

        with pytest.raises(ValueError, match="style_report 不能为空"):
            build_draft_generation_prompt("", requirement)

    def test_rejects_whitespace_only_style_report(self) -> None:
        requirement = StoryRequirement()

        with pytest.raises(ValueError, match="style_report 不能为空"):
            build_draft_generation_prompt("   \n\t  ", requirement)

    def test_prompt_requires_original_content(self) -> None:
        requirement = StoryRequirement()
        style_report = "测试风格报告。"

        result = build_draft_generation_prompt(style_report, requirement)

        assert "完全原创" in result.prompt
        assert "不得照搬" in result.prompt

    def test_system_prompt_requires_original_content(self) -> None:
        requirement = StoryRequirement()
        style_report = "测试风格报告。"

        result = build_draft_generation_prompt(style_report, requirement)

        assert "完全原创" in result.system_prompt
        assert "不得照搬" in result.system_prompt

    def test_prompt_includes_structured_requirement_fields(self) -> None:
        requirement = StoryRequirement(
            theme="赛博修仙",
            protagonist="失忆剑修",
            forbidden_content=["不要血腥描写", "不要后宫"],
            required_plot_points=["主角必须在结局完成自我和解"],
        )
        style_report = "风格分析报告内容。"

        result = build_draft_generation_prompt(style_report, requirement)
        prompt = result.prompt

        assert "赛博修仙" in prompt
        assert "失忆剑修" in prompt
        assert "不要血腥描写" in prompt
        assert "不要后宫" in prompt
        assert "主角必须在结局完成自我和解" in prompt

    def test_prompt_includes_worldview_and_ending(self) -> None:
        requirement = StoryRequirement(
            worldview="灵气复苏后的现代都市",
            ending_preference="开放式结局",
        )
        style_report = "风格分析报告。"

        result = build_draft_generation_prompt(style_report, requirement)

        assert "灵气复苏后的现代都市" in result.prompt
        assert "开放式结局" in result.prompt

    def test_prompt_includes_chapter_plan(self) -> None:
        requirement = StoryRequirement()
        style_report = "风格分析。"
        chapter_plan = "第一章：主角觉醒；第二章：初入宗门；第三章：首次试炼。"

        result = build_draft_generation_prompt(
            style_report, requirement, chapter_plan=chapter_plan
        )

        assert "主角觉醒" in result.prompt
        assert "初入宗门" in result.prompt

    def test_prompt_includes_chapter_count(self) -> None:
        requirement = StoryRequirement()
        style_report = "风格分析。"

        result = build_draft_generation_prompt(
            style_report, requirement, chapter_count=5
        )

        assert "共 **5** 个章节" in result.prompt

    def test_prompt_includes_target_word_count(self) -> None:
        requirement = StoryRequirement()
        style_report = "风格分析。"

        result = build_draft_generation_prompt(
            style_report, requirement, target_word_count=10000
        )

        assert "约 **10000** 字" in result.prompt

    def test_prompt_includes_role_consistency_requirement(self) -> None:
        requirement = StoryRequirement()
        style_report = "风格分析。"

        result = build_draft_generation_prompt(style_report, requirement)

        assert "角色一致" in result.prompt

    def test_prompt_includes_plot_progression_requirement(self) -> None:
        requirement = StoryRequirement()
        style_report = "风格分析。"

        result = build_draft_generation_prompt(style_report, requirement)

        assert "剧情有推进" in result.prompt

    def test_no_real_api_key_in_prompt(self) -> None:
        requirement = StoryRequirement()
        style_report = "风格分析。"

        result = build_draft_generation_prompt(style_report, requirement)
        full_text = result.prompt + result.system_prompt

        assert "api_key" not in full_text.lower()
        assert "sk-" not in full_text.lower()
        assert "bearer" not in full_text.lower()

    def test_uses_chinese_in_output(self) -> None:
        requirement = StoryRequirement()
        style_report = "风格分析。"

        result = build_draft_generation_prompt(style_report, requirement)

        assert any(
            "\u4e00" <= char <= "\u9fff" for char in result.prompt
        )
        assert any(
            "\u4e00" <= char <= "\u9fff" for char in result.system_prompt
        )

    def test_no_real_model_call(self) -> None:
        requirement = StoryRequirement()
        style_report = "风格分析。"

        result = build_draft_generation_prompt(style_report, requirement)

        assert isinstance(result, ModelRequest)
        assert result.model_extra is None or not result.model_extra

    def test_empty_requirement_still_produces_prompt(self) -> None:
        requirement = StoryRequirement()
        style_report = "风格分析报告。"

        result = build_draft_generation_prompt(style_report, requirement)

        assert isinstance(result, ModelRequest)
        assert len(result.prompt) > 0

    def test_entry_in_package_init(self) -> None:
        from novel_rewrite_system.generation.prompts import build_draft_generation_prompt as imported

        assert imported is build_draft_generation_prompt
