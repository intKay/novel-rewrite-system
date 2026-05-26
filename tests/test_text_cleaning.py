import pytest

from novel_rewrite_system.text_cleaning import clean_text


@pytest.mark.parametrize("raw_text", ["", "   \n\t  \r\n"])
def test_clean_text_rejects_empty_text(raw_text: str) -> None:
    with pytest.raises(ValueError, match="text 不能为空"):
        clean_text(raw_text)


def test_clean_text_normalizes_windows_newlines() -> None:
    assert clean_text("第一段\r\n\r\n第二段") == "第一段\n\n第二段"


def test_clean_text_normalizes_mixed_newlines() -> None:
    assert clean_text("第一段\r\n第二行\r第三段") == "第一段\n第二行\n第三段"


def test_clean_text_collapses_excess_blank_lines() -> None:
    assert clean_text("第一段\n\n\n \n第二段") == "第一段\n\n第二段"


def test_clean_text_keeps_chinese_paragraphs() -> None:
    raw_text = "  夜色沉下来。\n\n她推开门，听见远处的钟声。  "

    assert clean_text(raw_text) == "夜色沉下来。\n\n她推开门，听见远处的钟声。"


@pytest.mark.parametrize("chapter_title", ["第1章", "第一章", "第十二章"])
def test_clean_text_keeps_chapter_titles(chapter_title: str) -> None:
    assert clean_text(f"{chapter_title}\n正文内容。") == f"{chapter_title}\n正文内容。"


def test_clean_text_keeps_paragraph_separator_after_cleaning() -> None:
    assert clean_text("第一段。\n  \n第二段。") == "第一段。\n\n第二段。"
