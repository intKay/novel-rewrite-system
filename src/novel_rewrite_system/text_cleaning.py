"""基础文本清洗。"""

from __future__ import annotations


def clean_text(raw_text: str) -> str:
    """清洗原始文本，保留基本段落结构。"""

    normalized_text = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized_text:
        raise ValueError("text 不能为空")

    paragraphs: list[str] = []
    current_lines: list[str] = []

    for line in normalized_text.split("\n"):
        stripped_line = line.strip()
        if stripped_line:
            current_lines.append(stripped_line)
            continue
        if current_lines:
            paragraphs.append("\n".join(current_lines))
            current_lines = []

    if current_lines:
        paragraphs.append("\n".join(current_lines))

    cleaned_text = "\n\n".join(paragraphs)
    if not cleaned_text:
        raise ValueError("text 不能为空")
    return cleaned_text
