"""续写提示词构建器测试。"""

import pytest

from novel_rewrite_system.generation.prompts.continuation import build_continuation_prompt

CURRENT_TEXT = "夜色沉下来。她推开门，听见远处的钟声。院中无人。"


def test_contains_current_text() -> None:
    request = build_continuation_prompt(CURRENT_TEXT, "请续写下一段")
    assert CURRENT_TEXT in request.prompt


def test_contains_continuation_instruction() -> None:
    instruction = "请描写庭院中的老槐树"
    request = build_continuation_prompt(CURRENT_TEXT, instruction)
    assert instruction in request.prompt


def test_contains_style_reference_when_provided() -> None:
    style = "叙事风格冷峻，短句为主"
    request = build_continuation_prompt(CURRENT_TEXT, "续写", style_reference=style)
    assert "风格参考" in request.prompt
    assert style in request.prompt


def test_no_style_reference_when_not_provided() -> None:
    request = build_continuation_prompt(CURRENT_TEXT, "续写")
    assert "风格参考" not in request.prompt


def test_contains_target_word_count_when_provided() -> None:
    request = build_continuation_prompt(CURRENT_TEXT, "续写", target_word_count=300)
    assert "300" in request.prompt


def test_no_word_count_when_not_provided() -> None:
    request = build_continuation_prompt(CURRENT_TEXT, "续写", target_word_count=None)
    assert "续写约" not in request.prompt


def test_has_system_prompt() -> None:
    request = build_continuation_prompt(CURRENT_TEXT, "续写")
    assert request.system_prompt is not None
    assert len(request.system_prompt) > 10


def test_empty_current_text_raises_error() -> None:
    with pytest.raises(ValueError, match="current_text 不能为空"):
        build_continuation_prompt("", "续写")


def test_empty_instruction_raises_error() -> None:
    with pytest.raises(ValueError, match="continuation_instruction 不能为空"):
        build_continuation_prompt(CURRENT_TEXT, "")


def test_contains_tag_hints_when_provided() -> None:
    hints = "## 创作控制标签\n\n### 情绪\n- **紧张压迫**：营造紧张感。"
    request = build_continuation_prompt(CURRENT_TEXT, "续写", tag_hints=hints)
    assert "创作控制标签" in request.prompt
    assert "紧张压迫" in request.prompt


def test_no_tag_hints_when_not_provided() -> None:
    request = build_continuation_prompt(CURRENT_TEXT, "续写")
    assert "创作控制标签" not in request.prompt
