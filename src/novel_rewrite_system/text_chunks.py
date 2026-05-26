"""纯函数文本切分。"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    """文本切分结果。"""

    source_id: str
    chapter_title: str | None
    text: str
    order: int


_CHAPTER_TITLE_PATTERN = re.compile(
    r"^(?:"
    r"第[零〇一二三四五六七八九十百千万两\d]+[章节卷回部篇][^\n]{0,60}"
    r"|Chapter\s+\d+[^\n]{0,60}"
    r"|CHAPTER\s+\d+[^\n]{0,60}"
    r"|序章|楔子|尾声|后记|番外[^\n]{0,60}"
    r")$"
)
_SENTENCE_PATTERN = re.compile(r".+?(?:[。！？!?；;]+[”’」』】）)]*|$)", re.S)


def split_text(
    source_id: str,
    raw_text: str,
    *,
    chapter_title: str | None = None,
    chunk_chars: int = 2000,
) -> list[TextChunk]:
    """将原始文本切分为按顺序排列的文本块。

    切分策略依次为：先识别章节标题，章节过长时按段落组合，单段过长时按句子组合。
    """

    normalized_source_id = source_id.strip()
    if not normalized_source_id:
        raise ValueError("source_id 不能为空")
    if chunk_chars <= 0:
        raise ValueError("chunk_chars 必须大于 0")

    normalized_text = _normalize_text(raw_text)
    if not normalized_text:
        return []

    chunks: list[TextChunk] = []
    for detected_title, chapter_text in _split_chapters(normalized_text, chapter_title):
        for chunk_text in _split_chapter_text(chapter_text, chunk_chars):
            chunks.append(
                TextChunk(
                    source_id=normalized_source_id,
                    chapter_title=detected_title,
                    text=chunk_text,
                    order=len(chunks) + 1,
                )
            )
    return chunks


def _normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def _split_chapters(
    text: str, fallback_chapter_title: str | None
) -> list[tuple[str | None, str]]:
    chapters: list[tuple[str | None, list[str]]] = []
    current_title = fallback_chapter_title.strip() if fallback_chapter_title else None
    current_lines: list[str] = []

    for line in text.split("\n"):
        stripped_line = line.strip()
        if _is_chapter_title(stripped_line):
            if _has_content(current_lines):
                chapters.append((current_title, current_lines))
            current_title = stripped_line
            current_lines = []
            continue
        current_lines.append(line)

    if _has_content(current_lines):
        chapters.append((current_title, current_lines))

    return [
        (title, _normalize_text("\n".join(lines)))
        for title, lines in chapters
        if _normalize_text("\n".join(lines))
    ]


def _is_chapter_title(line: str) -> bool:
    return bool(line) and bool(_CHAPTER_TITLE_PATTERN.match(line))


def _has_content(lines: list[str]) -> bool:
    return any(line.strip() for line in lines)


def _split_chapter_text(text: str, chunk_chars: int) -> list[str]:
    paragraphs = _split_paragraphs(text)
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > chunk_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_long_paragraph(paragraph, chunk_chars))
            continue

        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= chunk_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = paragraph

    if current:
        chunks.append(current)
    return chunks


def _split_paragraphs(text: str) -> list[str]:
    return [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]


def _split_long_paragraph(paragraph: str, chunk_chars: int) -> list[str]:
    chunks: list[str] = []
    current = ""

    for sentence in _split_sentences(paragraph):
        if len(sentence) > chunk_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_hard_split(sentence, chunk_chars))
            continue

        candidate = sentence if not current else f"{current}{sentence}"
        if len(candidate) <= chunk_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)
    return chunks


def _split_sentences(paragraph: str) -> list[str]:
    return [
        match.group(0).strip()
        for match in _SENTENCE_PATTERN.finditer(paragraph)
        if match.group(0).strip()
    ]


def _hard_split(text: str, chunk_chars: int) -> list[str]:
    return [text[index : index + chunk_chars] for index in range(0, len(text), chunk_chars)]
