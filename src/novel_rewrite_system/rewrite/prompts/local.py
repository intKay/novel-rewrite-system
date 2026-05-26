"""本地改写提示词构建器 —— 纯函数，不进行真实模型调用。"""

from __future__ import annotations

from novel_rewrite_system.models import ModelRequest

_LOCAL_REWRITE_SYSTEM_PROMPT = (
    "你是一位专业的中文小说改写编辑。你的任务是根据用户提供的设定、角色表和改写要求，"
    "对给定的文本片段进行改写。你必须严格遵守以下规则：\n"
    "1. 只改写当前给定的文本片段，不得自行扩写或生成后续章节。\n"
    "2. 必须保留核心剧情逻辑，不得随意改变故事走向。\n"
    "3. 严格按照用户指令替换角色、关系、设定或场景。\n"
    "4. 保持人物称呼一致，不得出现前后称呼混乱。\n"
    "5. 严格遵守「必须保留的剧情点」和「禁止改变的事实」。\n"
    "6. 所有输出使用自然流畅的中文。\n"
    "7. 改写完成后，必须在回复末尾附上一段简短的修改说明，列出所做的具体改动。"
)

_LOCAL_REWRITE_TEMPLATE = """# 本地改写任务

你正在处理一篇中文小说的一个文本片段。请根据以下信息进行改写。

## 全局设定摘要

{global_summary}

## 角色表

{character_sheet}

## 当前章节摘要

{chapter_summary}

## 用户改写要求

{rewrite_instruction}

{must_keep_section}

{forbidden_section}

## 当前待改写片段

{current_fragment}

---

请根据以上所有信息对当前片段进行改写。改写完成后，请务必在回复末尾附上修改说明。"""


def build_local_rewrite_prompt(
    global_summary: str,
    character_sheet: str,
    chapter_summary: str,
    current_fragment: str,
    rewrite_instruction: str,
    must_keep: list[str],
    forbidden_changes: list[str],
    *,
    temperature: float | None = 0.8,
    top_p: float | None = 0.9,
    max_tokens: int | None = None,
) -> ModelRequest:
    """为本地模型构建单个文本片段的改写提示词。

    Args:
        global_summary: 全局设定摘要，必须非空。
        character_sheet: 角色表，必须非空。
        chapter_summary: 当前章节摘要，必须非空。
        current_fragment: 当前待改写片段，必须非空。
        rewrite_instruction: 用户改写要求，必须非空。
        must_keep: 必须保留的剧情点列表，可为空。
        forbidden_changes: 禁止改变的事实列表，可为空。
        temperature: 可选温度参数，默认 0.8。
        top_p: 可选核采样阈值，默认 0.9。
        max_tokens: 可选最大输出 token 数。

    Returns:
        构造好的 ModelRequest，包含 system_prompt 和 prompt。

    Raises:
        ValueError: 如果任一必填字段为空或仅含空白。
    """

    _validate_required("global_summary", global_summary)
    _validate_required("character_sheet", character_sheet)
    _validate_required("chapter_summary", chapter_summary)
    _validate_required("current_fragment", current_fragment)
    _validate_required("rewrite_instruction", rewrite_instruction)

    prompt = _LOCAL_REWRITE_TEMPLATE.format(
        global_summary=global_summary.strip(),
        character_sheet=character_sheet.strip(),
        chapter_summary=chapter_summary.strip(),
        current_fragment=current_fragment.strip(),
        rewrite_instruction=rewrite_instruction.strip(),
        must_keep_section=_build_must_keep_section(must_keep),
        forbidden_section=_build_forbidden_section(forbidden_changes),
    )

    return ModelRequest(
        prompt=prompt,
        system_prompt=_LOCAL_REWRITE_SYSTEM_PROMPT,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
    )


def _validate_required(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} 不能为空")


def _build_must_keep_section(must_keep: list[str]) -> str:
    if not must_keep:
        return "## 必须保留的剧情点\n\n（无特殊要求）"

    items = [f"- {point}" for point in must_keep]
    return "## 必须保留的剧情点\n\n以下剧情点必须完整保留，不得删除或改变其核心含义：\n\n" + "\n".join(items)


def _build_forbidden_section(forbidden_changes: list[str]) -> str:
    if not forbidden_changes:
        return "## 禁止改变的事实\n\n（无特殊限制）"

    items = [f"- {item}" for item in forbidden_changes]
    return "## 禁止改变的事实\n\n以下事实在改写中不得以任何方式改变：\n\n" + "\n".join(items)
