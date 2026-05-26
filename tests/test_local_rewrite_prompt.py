"""本地改写提示词构建器单元测试。"""

import pytest

from novel_rewrite_system.models import ModelRequest
from novel_rewrite_system.rewrite.prompts.local import build_local_rewrite_prompt


def _make_args(**overrides: str | list[str] | None) -> dict:
    defaults: dict = {
        "global_summary": "这是一个武侠世界，有内功、轻功和剑术三大修炼体系。",
        "character_sheet": "主角：林逸，剑客，性格孤傲。配角：苏晴，医者，性格温和。",
        "chapter_summary": "本章讲述林逸在破庙中偶遇受伤的苏晴，两人初次交锋。",
        "current_fragment": (
            "林逸推开破庙的木门，一阵寒风灌入。地上躺着一个白衣女子，"
            "肩头染血，面色苍白。他脚步一顿，手按剑柄。"
        ),
        "rewrite_instruction": "将场景从破庙改为废弃道观，林逸的性格从孤傲改为内敛。",
        "must_keep": ["林逸遇到了受伤的苏晴", "林逸最初保持警惕"],
        "forbidden_changes": ["苏晴的性别", "两人初次相遇的事实"],
    }
    defaults.update(overrides)
    return defaults


class TestBuildLocalRewritePrompt:
    def test_returns_model_request_with_full_input(self) -> None:
        result = build_local_rewrite_prompt(**_make_args())

        assert isinstance(result, ModelRequest)
        assert result.prompt
        assert result.system_prompt

    def test_prompt_contains_global_summary(self) -> None:
        result = build_local_rewrite_prompt(**_make_args())

        assert "武侠世界" in result.prompt
        assert "内功" in result.prompt

    def test_prompt_contains_character_sheet(self) -> None:
        result = build_local_rewrite_prompt(**_make_args())

        assert "林逸" in result.prompt
        assert "苏晴" in result.prompt

    def test_prompt_contains_chapter_summary(self) -> None:
        result = build_local_rewrite_prompt(**_make_args())

        assert "破庙" in result.prompt
        assert "初次交锋" in result.prompt

    def test_prompt_contains_current_fragment(self) -> None:
        result = build_local_rewrite_prompt(**_make_args())

        assert "推开破庙的木门" in result.prompt
        assert "肩头染血" in result.prompt

    def test_prompt_contains_rewrite_instruction(self) -> None:
        result = build_local_rewrite_prompt(**_make_args())

        assert "废弃道观" in result.prompt
        assert "内敛" in result.prompt

    def test_prompt_contains_must_keep(self) -> None:
        result = build_local_rewrite_prompt(**_make_args())

        assert "林逸遇到了受伤的苏晴" in result.prompt
        assert "林逸最初保持警惕" in result.prompt
        assert "必须保留的剧情点" in result.prompt
        assert "完整保留" in result.prompt

    def test_prompt_contains_forbidden_changes(self) -> None:
        result = build_local_rewrite_prompt(**_make_args())

        assert "苏晴的性别" in result.prompt
        assert "两人初次相遇的事实" in result.prompt
        assert "禁止改变的事实" in result.prompt
        assert "不得以任何方式改变" in result.prompt

    def test_prompt_requires_chinese_output(self) -> None:
        result = build_local_rewrite_prompt(**_make_args())

        assert any(
            "\u4e00" <= char <= "\u9fff" for char in result.system_prompt
        )
        assert any(
            "\u4e00" <= char <= "\u9fff" for char in result.prompt
        )

    def test_system_prompt_requires_modification_notes(self) -> None:
        result = build_local_rewrite_prompt(**_make_args())

        assert "修改说明" in result.system_prompt

    def test_system_prompt_requires_avoid_character_confusion(self) -> None:
        result = build_local_rewrite_prompt(**_make_args())

        assert "称呼" in result.system_prompt

    def test_system_prompt_requires_preserve_core_plot(self) -> None:
        result = build_local_rewrite_prompt(**_make_args())

        assert "核心剧情" in result.system_prompt

    def test_system_prompt_limits_to_single_fragment(self) -> None:
        result = build_local_rewrite_prompt(**_make_args())

        assert "只改写当前" in result.system_prompt

    def test_empty_must_keep_handled_gracefully(self) -> None:
        args = _make_args(must_keep=[])

        result = build_local_rewrite_prompt(**args)

        assert "必须保留的剧情点" in result.prompt
        assert "无特殊要求" in result.prompt

    def test_empty_forbidden_changes_handled_gracefully(self) -> None:
        args = _make_args(forbidden_changes=[])

        result = build_local_rewrite_prompt(**args)

        assert "禁止改变的事实" in result.prompt
        assert "无特殊限制" in result.prompt

    def test_default_temperature_and_top_p(self) -> None:
        result = build_local_rewrite_prompt(**_make_args())

        assert result.temperature == 0.8
        assert result.top_p == 0.9

    def test_custom_generation_params(self) -> None:
        result = build_local_rewrite_prompt(
            **_make_args(),
            temperature=0.7,
            top_p=0.95,
            max_tokens=2048,
        )

        assert result.temperature == 0.7
        assert result.top_p == 0.95
        assert result.max_tokens == 2048

    def test_default_max_tokens_is_none(self) -> None:
        result = build_local_rewrite_prompt(**_make_args())

        assert result.max_tokens is None

    def test_rejects_empty_global_summary(self) -> None:
        with pytest.raises(ValueError, match="global_summary 不能为空"):
            build_local_rewrite_prompt(**_make_args(global_summary=""))

    def test_rejects_whitespace_global_summary(self) -> None:
        with pytest.raises(ValueError, match="global_summary 不能为空"):
            build_local_rewrite_prompt(**_make_args(global_summary="   "))

    def test_rejects_empty_character_sheet(self) -> None:
        with pytest.raises(ValueError, match="character_sheet 不能为空"):
            build_local_rewrite_prompt(**_make_args(character_sheet=""))

    def test_rejects_empty_chapter_summary(self) -> None:
        with pytest.raises(ValueError, match="chapter_summary 不能为空"):
            build_local_rewrite_prompt(**_make_args(chapter_summary=""))

    def test_rejects_empty_current_fragment(self) -> None:
        with pytest.raises(ValueError, match="current_fragment 不能为空"):
            build_local_rewrite_prompt(**_make_args(current_fragment=""))

    def test_rejects_empty_rewrite_instruction(self) -> None:
        with pytest.raises(ValueError, match="rewrite_instruction 不能为空"):
            build_local_rewrite_prompt(**_make_args(rewrite_instruction=""))

    def test_no_real_model_call(self) -> None:
        result = build_local_rewrite_prompt(**_make_args())

        assert isinstance(result, ModelRequest)
        assert len(result.prompt) > 0
        assert result.model_extra is None or not result.model_extra

    def test_prompt_limits_to_current_fragment(self) -> None:
        result = build_local_rewrite_prompt(**_make_args())

        assert "文本片段" in result.system_prompt or "当前片段" in result.prompt

    def test_entry_in_package_init(self) -> None:
        from novel_rewrite_system.rewrite.prompts import build_local_rewrite_prompt as imported

        assert imported is build_local_rewrite_prompt
