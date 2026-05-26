import pytest
from pydantic import ValidationError

from novel_rewrite_system.requirements import StoryRequirement


def test_story_requirement_allows_partial_fields() -> None:
    requirement = StoryRequirement(theme="赛博修仙", protagonist="失忆剑修")

    assert requirement.theme == "赛博修仙"
    assert requirement.worldview is None
    assert requirement.protagonist == "失忆剑修"
    assert requirement.supporting_characters is None
    assert requirement.character_relationships is None
    assert requirement.plot_direction is None
    assert requirement.style_preferences is None
    assert requirement.forbidden_content == []
    assert requirement.required_plot_points == []
    assert requirement.ending_preference is None


def test_story_requirement_from_text_preserves_raw_text_only() -> None:
    raw_text = "想要一个东方玄幻故事，主角从边城出发，结局偏燃。"

    requirement = StoryRequirement.from_text(raw_text)

    assert requirement.raw_text == raw_text
    assert requirement.theme is None
    assert requirement.worldview is None
    assert requirement.protagonist is None
    assert requirement.required_plot_points == []


def test_story_requirement_lists_are_not_shared() -> None:
    first = StoryRequirement()
    second = StoryRequirement()

    first.forbidden_content.append("不要血腥描写")
    first.required_plot_points.append("主角必须完成和解")

    assert second.forbidden_content == []
    assert second.required_plot_points == []


def test_story_requirement_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        StoryRequirement.model_validate({"theme": "悬疑", "unknown": "value"})
