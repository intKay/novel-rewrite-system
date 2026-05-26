"""初稿生成服务 —— 串联提示词构建器与模型客户端。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from novel_rewrite_system.errors import EmptyTextError, ProjectError
from novel_rewrite_system.generation.prompts.draft import build_draft_generation_prompt
from novel_rewrite_system.models import ModelClient
from novel_rewrite_system.requirements import StoryRequirement


@dataclass(frozen=True)
class DraftGenerationResult:
    """初稿生成结果。"""

    draft_text: str


def generate_draft(
    style_report: str,
    requirement: StoryRequirement,
    model_client: ModelClient,
    *,
    chapter_plan: str | None = None,
    target_word_count: int | None = None,
    chapter_count: int | None = None,
    project_path: str | Path | None = None,
) -> DraftGenerationResult:
    """根据风格报告和用户需求生成原创小说初稿，可选保存到项目 drafts/ 目录。

    Args:
        style_report: 风格分析报告文本，必须非空。
        requirement: 用户需求结构化对象。
        model_client: 实现了 ModelClient 协议的模型客户端。
        chapter_plan: 可选章节计划描述。
        target_word_count: 可选目标总字数。
        chapter_count: 可选目标章节数。
        project_path: 可选项目路径，若提供则将初稿保存到 drafts/ 目录下。

    Returns:
        DraftGenerationResult，包含初稿文本。

    Raises:
        EmptyTextError: style_report 为空或仅含空白。
        ProjectError: 模型返回空文本。
    """

    if not style_report.strip():
        raise EmptyTextError(
            message="风格分析报告不能为空",
            suggestion="请先执行风格分析获取报告后再重试。",
        )

    request = build_draft_generation_prompt(
        style_report,
        requirement,
        chapter_plan=chapter_plan,
        target_word_count=target_word_count,
        chapter_count=chapter_count,
    )

    response = model_client.generate(request)

    if not response.text.strip():
        raise ProjectError(
            code="empty_response",
            message="模型返回空文本，初稿生成失败",
            suggestion="请重试，或调整生成参数（如减少 chapter_count）后重试。",
        )

    result = DraftGenerationResult(draft_text=response.text)

    if project_path is not None:
        _save_draft(Path(project_path), result)

    return result


def _save_draft(project_path: Path, result: DraftGenerationResult) -> None:
    drafts_dir = project_path / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    draft_path = drafts_dir / "draft.md"
    draft_path.write_text(result.draft_text, encoding="utf-8")
