import pytest

from novel_rewrite_system.text_chunks import TextChunk, split_text


def test_split_text_prefers_chapter_titles() -> None:
    chunks = split_text(
        "source-1",
        """第一章 初见
这是第一章第一段。

这是第一章第二段。

第二章 风起
这是第二章内容。""",
        chunk_chars=100,
    )

    assert chunks == [
        TextChunk("source-1", "第一章 初见", "这是第一章第一段。\n\n这是第一章第二段。", 1),
        TextChunk("source-1", "第二章 风起", "这是第二章内容。", 2),
    ]


def test_split_text_uses_fallback_chapter_title_without_detected_titles() -> None:
    chunks = split_text(
        " source-1 ",
        "第一段内容。\n\n第二段内容。",
        chapter_title="序幕",
        chunk_chars=100,
    )

    assert chunks == [
        TextChunk("source-1", "序幕", "第一段内容。\n\n第二段内容。", 1)
    ]


def test_split_text_splits_long_chapter_by_paragraphs() -> None:
    chunks = split_text(
        "source-1",
        """第一章 初见
第一段内容很短。

第二段内容也很短。

第三段内容也很短。""",
        chunk_chars=18,
    )

    assert [chunk.text for chunk in chunks] == [
        "第一段内容很短。",
        "第二段内容也很短。",
        "第三段内容也很短。",
    ]
    assert [chunk.chapter_title for chunk in chunks] == ["第一章 初见"] * 3
    assert [chunk.order for chunk in chunks] == [1, 2, 3]


def test_split_text_avoids_breaking_sentences_in_long_paragraph() -> None:
    chunks = split_text(
        "source-1",
        "第一句比较短。第二句也比较短。第三句收尾。",
        chunk_chars=12,
    )

    assert [chunk.text for chunk in chunks] == [
        "第一句比较短。",
        "第二句也比较短。",
        "第三句收尾。",
    ]


def test_split_text_hard_splits_only_when_single_sentence_is_too_long() -> None:
    chunks = split_text("source-1", "没有标点的一长串文字", chunk_chars=5)

    assert [chunk.text for chunk in chunks] == ["没有标点的", "一长串文字"]


def test_split_text_returns_empty_list_for_blank_text() -> None:
    assert split_text("source-1", "  ", chunk_chars=10) == []


@pytest.mark.parametrize(
    ("source_id", "chunk_chars", "message"),
    [
        (" ", 10, "source_id 不能为空"),
        ("source-1", 0, "chunk_chars 必须大于 0"),
    ],
)
def test_split_text_rejects_invalid_arguments(
    source_id: str, chunk_chars: int, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        split_text(source_id, "正文。", chunk_chars=chunk_chars)
