"""风格分析提示词构建器单元测试。"""

import pytest

from novel_rewrite_system.analysis.prompts.style import build_style_analysis_prompt
from novel_rewrite_system.models import ModelRequest
from novel_rewrite_system.text_chunks import TextChunk


def _make_chunks(*texts: str) -> list[TextChunk]:
    return [
        TextChunk(source_id="src-1", chapter_title=None, text=text, order=i + 1)
        for i, text in enumerate(texts)
    ]


class TestBuildStyleAnalysisPrompt:
    def test_returns_model_request_with_single_chunk(self) -> None:
        chunks = _make_chunks("夜色沉下来。她推开门，听见远处的钟声。")

        result = build_style_analysis_prompt(chunks)

        assert isinstance(result, ModelRequest)
        assert result.prompt
        assert result.system_prompt
        assert "夜色沉下来" in result.prompt
        assert result.temperature == 0.3

    def test_returns_model_request_with_multiple_chunks(self) -> None:
        chunks = _make_chunks(
            "第一段测试文本。",
            "第二段测试文本，包含更多内容。",
            "第三段测试文本。",
        )

        result = build_style_analysis_prompt(chunks)

        assert isinstance(result, ModelRequest)
        assert "第一段测试文本" in result.prompt
        assert "第二段测试文本" in result.prompt
        assert "第三段测试文本" in result.prompt
        assert "片段 1" in result.prompt
        assert "片段 2" in result.prompt
        assert "片段 3" in result.prompt

    def test_rejects_empty_chunks(self) -> None:
        with pytest.raises(ValueError, match="chunks 不能为空"):
            build_style_analysis_prompt([])

    def test_max_chunks_limits_selected(self) -> None:
        chunks = _make_chunks("甲乙丙丁", "子丑寅卯", "辰巳午未", "申酉戌亥", "ABCD")

        result = build_style_analysis_prompt(chunks, max_chunks=2)

        assert "甲乙丙丁" in result.prompt
        assert "子丑寅卯" in result.prompt
        assert "辰巳午未" not in result.prompt
        assert "申酉戌亥" not in result.prompt
        assert "ABCD" not in result.prompt

    def test_max_chunks_equal_to_total_includes_all(self) -> None:
        chunks = _make_chunks("甲乙丙丁", "子丑寅卯", "辰巳午未")

        result = build_style_analysis_prompt(chunks, max_chunks=3)

        assert "甲乙丙丁" in result.prompt
        assert "子丑寅卯" in result.prompt
        assert "辰巳午未" in result.prompt

    def test_prompt_includes_chapter_title(self) -> None:
        chunks = [
            TextChunk(
                source_id="src-1",
                chapter_title="第一章 初遇",
                text="她第一次见到他是在雨夜的桥头。",
                order=1,
            )
        ]

        result = build_style_analysis_prompt(chunks)

        assert "第一章 初遇" in result.prompt

    def test_prompt_contains_all_analysis_fields(self) -> None:
        chunks = _make_chunks("测试文本内容。")

        result = build_style_analysis_prompt(chunks)
        prompt = result.prompt

        required_fields = [
            "叙事视角",
            "句式特点",
            "对话比例",
            "描写密度",
            "情绪基调",
            "节奏特点",
            "冲突类型",
            "人物互动模式",
            "章节推进方式",
        ]

        for field in required_fields:
            assert field in prompt, f"prompt 缺少分析字段: {field}"

    def test_prompt_forbids_quoting_large_original_text(self) -> None:
        chunks = _make_chunks("测试文本。")

        result = build_style_analysis_prompt(chunks)
        full_text = result.system_prompt + result.prompt

        assert "不得复述" in full_text or "不要复述" in full_text or "禁止大段" in full_text
        assert "抽象" in full_text

    def test_system_prompt_forbids_quoting(self) -> None:
        chunks = _make_chunks("测试文本。")

        result = build_style_analysis_prompt(chunks)

        assert "不得复述或引用大段原文" in result.system_prompt

    def test_uses_chinese_in_system_prompt(self) -> None:
        chunks = _make_chunks("测试文本。")

        result = build_style_analysis_prompt(chunks)

        assert any(
            "\u4e00" <= char <= "\u9fff" for char in result.system_prompt
        )

    def test_no_real_api_key_in_prompt(self) -> None:
        chunks = _make_chunks("测试文本。")

        result = build_style_analysis_prompt(chunks)

        assert "api_key" not in result.prompt.lower()
        assert "sk-" not in result.prompt.lower()
        assert "bearer" not in result.prompt.lower()

    def test_custom_analysis_focus_overrides_default(self) -> None:
        chunks = _make_chunks("测试文本。")
        custom_focus = ["叙事视角", "情绪基调"]

        result = build_style_analysis_prompt(chunks, analysis_focus=custom_focus)

        assert "重点关注：叙事视角" in result.prompt
        assert "重点关注：情绪基调" in result.prompt
        assert "重点关注：对话比例" not in result.prompt

    def test_empty_analysis_focus_suppresses_section(self) -> None:
        chunks = _make_chunks("测试文本。")

        result = build_style_analysis_prompt(chunks, analysis_focus=[])

        assert "特别关注" not in result.prompt
        assert "重点关注" not in result.prompt

    def test_entry_in_package_init(self) -> None:
        from novel_rewrite_system.analysis.prompts import build_style_analysis_prompt as imported

        assert imported is build_style_analysis_prompt
