"""标签词库测试。"""

from novel_rewrite_system.tags import CATEGORIES, CreativeTag, format_tags_for_prompt, get_default_tags


def test_default_tags_count_in_range() -> None:
    tags = get_default_tags()
    assert 8 <= len(tags) <= 15


def test_each_tag_has_required_fields() -> None:
    for tag in get_default_tags():
        assert isinstance(tag, CreativeTag)
        assert tag.name
        assert tag.category
        assert tag.description
        assert tag.prompt_hint


def test_all_categories_valid() -> None:
    for tag in get_default_tags():
        assert tag.category in CATEGORIES, f"标签 '{tag.name}' 的分类 '{tag.category}' 不在 {CATEGORIES}"


def test_tag_names_unique() -> None:
    tags = get_default_tags()
    names = [t.name for t in tags]
    assert len(names) == len(set(names))


def test_format_tags_for_prompt_empty() -> None:
    assert format_tags_for_prompt([]) == ""


def test_format_tags_for_prompt_contains_tag_names() -> None:
    tags = get_default_tags()[:2]
    result = format_tags_for_prompt(tags)
    for tag in tags:
        assert tag.name in result


def test_format_tags_for_prompt_contains_fallback_hints() -> None:
    tags = [t for t in get_default_tags() if t.fallback_hint]
    assert tags, "至少有一个标签包含 fallback_hint"
    result = format_tags_for_prompt(tags[:1])
    assert "若具体表达受限" in result


def test_format_tags_for_prompt_groups_by_category() -> None:
    tags = get_default_tags()
    result = format_tags_for_prompt(tags)
    categories_in_result = set()
    for line in result.split("\n"):
        if line.startswith("### "):
            categories_in_result.add(line[4:])
    for tag in tags:
        assert tag.category in categories_in_result
