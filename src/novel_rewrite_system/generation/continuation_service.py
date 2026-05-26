"""续写生成服务 —— 串联提示词构建器与模型客户端。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from novel_rewrite_system.errors import EmptyTextError, ProjectError
from novel_rewrite_system.generation.prompts.continuation import build_continuation_prompt
from novel_rewrite_system.models import ModelClient
from novel_rewrite_system.tags import CreativeTag, format_tags_for_prompt


@dataclass(frozen=True)
class ContinuationResult:
    """续写生成结果。"""

    continuation_text: str


def generate_continuation(
    current_text: str,
    continuation_instruction: str,
    model_client: ModelClient,
    *,
    style_reference: str | None = None,
    target_word_count: int | None = 500,
    selected_tags: list[CreativeTag] | None = None,
    project_path: str | Path | None = None,
) -> ContinuationResult:
    """基于当前文本和扩写要求生成下一段正文，可选保存到项目 drafts/ 目录。

    Args:
        current_text: 当前小说正文，必须非空。
        continuation_instruction: 用户扩写要求，必须非空。
        model_client: 实现了 ModelClient 协议的模型客户端。
        style_reference: 可选风格分析或参考画像摘要。
        target_word_count: 可选目标续写字数，默认 500。
        selected_tags: 可选选中的创作控制标签列表。
        project_path: 可选项目路径，若提供则将续写结果保存到 drafts/ 目录下。

    Returns:
        ContinuationResult，包含续写文本。

    Raises:
        EmptyTextError: current_text 或 continuation_instruction 为空。
        ProjectError: 模型返回空文本。
    """

    if not current_text.strip():
        raise EmptyTextError(
            message="当前文本不能为空",
            suggestion="请提供需要续写的文本后重试。",
        )

    if not continuation_instruction.strip():
        raise EmptyTextError(
            message="扩写需求不能为空",
            suggestion="请提供扩写要求后重试。",
        )

    tag_hints = format_tags_for_prompt(selected_tags) if selected_tags else ""

    request = build_continuation_prompt(
        current_text,
        continuation_instruction,
        style_reference=style_reference,
        target_word_count=target_word_count,
        tag_hints=tag_hints or None,
    )

    response = model_client.generate(request)

    if not response.text.strip():
        raise ProjectError(
            code="empty_response",
            message="模型返回空文本，续写生成失败",
            suggestion="请重试，或调整扩写需求后重试。",
        )

    result = ContinuationResult(continuation_text=response.text)

    if project_path is not None:
        _save_continuation(Path(project_path), result)

    return result


def _save_continuation(project_path: Path, result: ContinuationResult) -> None:
    drafts_dir = project_path / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    continuation_path = drafts_dir / "continuation.md"
    continuation_path.write_text(result.continuation_text, encoding="utf-8")
