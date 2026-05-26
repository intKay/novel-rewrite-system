"""续写提示词构建器 —— 纯函数，不进行真实模型调用。"""

from __future__ import annotations

from novel_rewrite_system.models import ModelRequest

_CONTINUATION_SYSTEM_PROMPT = (
    "你是一位专业的中文小说创作者。你的任务是根据当前小说正文和扩写要求，续写下一段正文。\n"
    "你必须严格遵守以下规则：\n"
    "1. 严格承接当前文本继续创作，不得重复或重写已有内容。\n"
    "2. 保持人物设定、叙事视角、语言风格和语气完全一致。\n"
    "3. 按扩写要求自然推进剧情，不出现突兀的跳跃。\n"
    "4. 如果扩写要求比较模糊，按当前文本的自然风格和节奏延展。\n"
    "5. 所有输出使用自然流畅的中文，不要附带解释、分析或评论。\n"
    "6. 不得改变已有的人物设定、世界观规则和核心事实。"
)

_CONTINUATION_TEMPLATE = """# 小说续写任务

## 当前文本
请严格承接以下内容继续创作，不得重复或改写已有文本：

{current_text}

{style_reference_section}## 扩写要求
{continuation_instruction}

{word_count_section}{tag_hints_section}## 生成要求
- 只输出续写的新正文
- 保持人物、视角、语气一致
- 按扩写要求推进下一段
- 不附带任何解释或分析"""


def build_continuation_prompt(
    current_text: str,
    continuation_instruction: str,
    *,
    style_reference: str | None = None,
    target_word_count: int | None = None,
    tag_hints: str | None = None,
) -> ModelRequest:
    """构建续写提示词。

    Args:
        current_text: 当前小说正文，必须非空。
        continuation_instruction: 用户扩写要求，必须非空。
        style_reference: 可选风格分析或参考画像摘要。
        target_word_count: 可选目标续写字数。

    Returns:
        构造好的 ModelRequest。

    Raises:
        ValueError: current_text 或 continuation_instruction 为空。
    """

    if not current_text.strip():
        raise ValueError("current_text 不能为空")
    if not continuation_instruction.strip():
        raise ValueError("continuation_instruction 不能为空")

    style_reference_section = ""
    if style_reference and style_reference.strip():
        style_reference_section = (
            f"## 风格参考\n以下风格描述可帮助你保持语气一致：\n\n"
            f"{style_reference.strip()}\n\n"
        )

    word_count_section = ""
    if target_word_count is not None and target_word_count > 0:
        word_count_section = f"请续写约 **{target_word_count}** 字的正文。\n\n"

    tag_hints_section = ""
    if tag_hints and tag_hints.strip():
        tag_hints_section = f"{tag_hints.strip()}\n\n"

    prompt = _CONTINUATION_TEMPLATE.format(
        current_text=current_text.strip(),
        style_reference_section=style_reference_section,
        continuation_instruction=continuation_instruction.strip(),
        word_count_section=word_count_section,
        tag_hints_section=tag_hints_section,
    )

    return ModelRequest(
        prompt=prompt,
        system_prompt=_CONTINUATION_SYSTEM_PROMPT,
        temperature=0.8,
        top_p=0.9,
    )
