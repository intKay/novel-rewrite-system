"""风格分析提示词构建器 —— 纯函数，不进行真实模型调用。"""

from __future__ import annotations

from novel_rewrite_system.models import ModelRequest
from novel_rewrite_system.text_chunks import TextChunk

_STYLE_ANALYSIS_SYSTEM_PROMPT = (
    "你是一位专业的小说风格分析师。你的任务是对给定的中文小说文本进行抽象风格分析。"
    "你必须严格遵守以下规则：\n"
    "1. 只分析抽象的风格特征和叙事模式，不得复述或引用大段原文。\n"
    "2. 如果需要举例，只能用高度概括的一句话说明，不得展开复述具体情节。\n"
    "3. 所有输出必须使用中文。\n"
    "4. 分析结果必须结构化，按字段输出。"
)

_STYLE_ANALYSIS_TEMPLATE = """# 风格分析任务

请根据以下参考文本片段，分析其抽象风格特征。请按以下字段输出结构化分析结果：

## 叙事视角
- 分析当前文本使用的叙事视角类别（第一人称、第三人称全知、第三人称限知等），说明其特征和变化模式。

## 句式特点
- 分析句子长度分布、句式复杂度、修饰语使用习惯等抽象特征。

## 对话比例
- 估计对话在文中的大致占比，分析对话的结构特点和叙事功能。

## 描写密度
- 分析环境描写、心理描写、动作描写的密度和分布特征。

## 情绪基调
- 识别文本的整体情绪色彩和情感变化模式。

## 节奏特点
- 分析叙述节奏的快慢变化、章节推进速度和张力控制方式。

## 冲突类型
- 识别文中的主要冲突类型（人物冲突、内部冲突、社会冲突等）及其处理方式。

## 人物互动模式
- 分析人物之间的互动方式、对话风格、关系变化的抽象模式。

## 章节推进方式
- 分析章节如何推进剧情：事件驱动、人物驱动还是设定驱动，以及章节之间的衔接方式。

{extra_requirements}
---

## 参考文本片段

{chunk_texts}
"""

DEFAULT_ANALYSIS_FOCUS = [
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


def build_style_analysis_prompt(
    chunks: list[TextChunk],
    *,
    analysis_focus: list[str] | None = None,
    max_chunks: int | None = None,
) -> ModelRequest:
    """根据参考文本切片构建风格分析提示词。

    Args:
        chunks: 参考文本切片列表。必须非空。
        analysis_focus: 可选分析关注点列表；默认覆盖全部九项分析字段。
        max_chunks: 可选最多参与分析的切片数量。

    Returns:
        构造好的 ModelRequest，包含 system_prompt、prompt、temperature=0.3。

    Raises:
        ValueError: 如果 chunks 为空。
    """

    if not chunks:
        raise ValueError("chunks 不能为空")

    selected: list[TextChunk] = chunks[:max_chunks] if max_chunks is not None else list(chunks)
    chunk_texts: str = _format_chunks(selected)
    extra_requirements: str = _build_extra_requirements(analysis_focus)

    prompt = _STYLE_ANALYSIS_TEMPLATE.format(
        chunk_texts=chunk_texts,
        extra_requirements=extra_requirements,
    )

    return ModelRequest(
        prompt=prompt,
        system_prompt=_STYLE_ANALYSIS_SYSTEM_PROMPT,
        temperature=0.3,
        top_p=0.9,
    )


def _format_chunks(chunks: list[TextChunk]) -> str:
    parts: list[str] = []
    for chunk in chunks:
        header = f"### 片段 {chunk.order}"
        if chunk.chapter_title:
            header += f"（{chunk.chapter_title}）"
        parts.append(f"{header}\n\n{chunk.text}")
    return "\n\n---\n\n".join(parts)


def _build_extra_requirements(analysis_focus: list[str] | None) -> str:
    focus: list[str] = analysis_focus if analysis_focus is not None else DEFAULT_ANALYSIS_FOCUS
    if not focus:
        return ""

    items = [f"- 重点关注：{item}" for item in focus]
    return "## 特别关注\n额外重点关注以下方面：\n" + "\n".join(items)
