"""初稿生成提示词构建器 —— 纯函数，不进行真实模型调用。"""

from __future__ import annotations

from novel_rewrite_system.models import ModelRequest
from novel_rewrite_system.requirements import StoryRequirement

_DRAFT_SYSTEM_PROMPT = (
    "你是一位专业的中文小说创作者。你的任务是根据给定的风格参考、人物设定和剧情要求，"
    "创作原创的中文小说正文。你必须严格遵守以下规则：\n"
    "1. 创作必须为完全原创的中文文本，不得照搬、改写或大量借鉴任何参考原文的具体表达。\n"
    "2. 角色设定必须保持一致：人物姓名、性别、身份在故事中不得自相矛盾。\n"
    "3. 剧情必须有明确的推进：每个章节/段落应有事件发展、冲突和转折。\n"
    "4. 严格遵守用户给出的禁止内容清单。\n"
    "5. 确保用户要求的情节点被完整包含在故事中。\n"
    "6. 所有输出使用自然流畅的中文。"
)

_DRAFT_TEMPLATE = """# 原创小说创作任务

## 风格参考
以下是目标风格的抽象分析报告，请参考其中的叙事特征来指导创作，但不得使用参考文本中的任何具体表述：

{style_report}

{requirement_section}

{chapter_plan_section}

## 创作要求

- **必须完全原创**：不得照搬、改写或大量借鉴任何已有文本的具体表达，只能借鉴抽象的风格特征和叙事模式。
- **角色一致**：所有角色的姓名、性别、身份、关系在全文必须保持一致。
- **剧情有推进**：故事应有明确的开端、发展、冲突和转折。
- **使用中文**：所有输出使用自然流畅的中文。

{word_count_section}

"""


def build_draft_generation_prompt(
    style_report: str,
    requirement: StoryRequirement,
    *,
    chapter_plan: str | None = None,
    target_word_count: int | None = None,
    chapter_count: int | None = None,
) -> ModelRequest:
    """根据风格报告和用户需求构建初稿生成提示词。

    Args:
        style_report: 风格分析报告文本，必须非空。
        requirement: 用户需求结构化对象。
        chapter_plan: 可选章节计划描述。
        target_word_count: 可选目标总字数。
        chapter_count: 可选目标章节数。

    Returns:
        构造好的 ModelRequest，包含 system_prompt、prompt、temperature=0.8。

    Raises:
        ValueError: 如果 style_report 为空或仅含空白。
    """

    if not style_report.strip():
        raise ValueError("style_report 不能为空")

    requirement_section = _build_requirement_section(requirement)
    chapter_plan_section = _build_chapter_plan_section(chapter_plan, chapter_count)
    word_count_section = _build_word_count_section(target_word_count)

    prompt = _DRAFT_TEMPLATE.format(
        style_report=style_report.strip(),
        requirement_section=requirement_section,
        chapter_plan_section=chapter_plan_section,
        word_count_section=word_count_section,
    )

    return ModelRequest(
        prompt=prompt,
        system_prompt=_DRAFT_SYSTEM_PROMPT,
        temperature=0.8,
        top_p=0.9,
    )


def _build_requirement_section(requirement: StoryRequirement) -> str:
    lines: list[str] = []

    if requirement.raw_text:
        lines.append(f"## 用户原始需求\n\n{requirement.raw_text}")

    structured: list[str] = ["## 结构化需求明细"]

    if requirement.theme:
        structured.append(f"- **主题**：{requirement.theme}")
    if requirement.worldview:
        structured.append(f"- **世界观**：{requirement.worldview}")
    if requirement.protagonist:
        structured.append(f"- **主角设定**：{requirement.protagonist}")
    if requirement.supporting_characters:
        structured.append(f"- **配角设定**：{requirement.supporting_characters}")
    if requirement.character_relationships:
        structured.append(f"- **人物关系**：{requirement.character_relationships}")
    if requirement.plot_direction:
        structured.append(f"- **情节方向**：{requirement.plot_direction}")
    if requirement.style_preferences:
        structured.append(f"- **风格偏好**：{requirement.style_preferences}")
    if requirement.ending_preference:
        structured.append(f"- **结局倾向**：{requirement.ending_preference}")

    if requirement.required_plot_points:
        structured.append("\n### 必须出现的情节")
        for point in requirement.required_plot_points:
            structured.append(f"- {point}")

    if requirement.forbidden_content:
        structured.append("\n### 禁止内容")
        for item in requirement.forbidden_content:
            structured.append(f"- {item}")

    lines.append("\n".join(structured))
    return "\n\n".join(lines)


def _build_chapter_plan_section(
    chapter_plan: str | None, chapter_count: int | None
) -> str:
    lines: list[str] = ["## 章节计划"]

    if chapter_plan:
        lines.append(chapter_plan)

    if chapter_count is not None:
        lines.append(f"\n请按以上计划生成共 **{chapter_count}** 个章节的正文。")

    return "\n".join(lines)


def _build_word_count_section(target_word_count: int | None) -> str:
    if target_word_count is None:
        return ""
    return f"请生成约 **{target_word_count}** 字的原创正文。"
