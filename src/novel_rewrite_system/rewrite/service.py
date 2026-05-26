"""本地改写服务 —— 串联提示词构建器与模型客户端。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from novel_rewrite_system.errors import EmptyTextError, ProjectError
from novel_rewrite_system.models import ModelClient
from novel_rewrite_system.rewrite.prompts.local import build_local_rewrite_prompt


@dataclass(frozen=True)
class LocalRewriteResult:
    """本地改写结果。"""

    rewritten_text: str


def rewrite_locally(
    global_summary: str,
    character_sheet: str,
    chapter_summary: str,
    current_fragment: str,
    rewrite_instruction: str,
    must_keep: list[str],
    forbidden_changes: list[str],
    model_client: ModelClient,
    *,
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
    project_path: str | Path | None = None,
) -> LocalRewriteResult:
    """对单个文本片段进行本地改写，可选保存到项目 revisions/ 目录。

    Args:
        global_summary: 全局设定摘要，必须非空。
        character_sheet: 角色表，必须非空。
        chapter_summary: 当前章节摘要，必须非空。
        current_fragment: 当前待改写片段，必须非空。
        rewrite_instruction: 用户改写要求，必须非空。
        must_keep: 必须保留的剧情点列表，可为空。
        forbidden_changes: 禁止改变的事实列表，可为空。
        model_client: 实现了 ModelClient 协议的模型客户端。
        temperature: 可选温度参数，透传给 prompt 构建器。
        top_p: 可选核采样阈值，透传给 prompt 构建器。
        max_tokens: 可选最大输出 token 数，透传给 prompt 构建器。
        project_path: 可选项目路径，若提供则将改写结果保存到 revisions/ 目录下。

    Returns:
        LocalRewriteResult，包含改写后的文本。

    Raises:
        EmptyTextError: 任一必填字符串字段为空或仅含空白。
        ProjectError: 模型返回空文本。
    """

    _validate_required("global_summary", global_summary)
    _validate_required("character_sheet", character_sheet)
    _validate_required("chapter_summary", chapter_summary)
    _validate_required("current_fragment", current_fragment)
    _validate_required("rewrite_instruction", rewrite_instruction)

    request = build_local_rewrite_prompt(
        global_summary,
        character_sheet,
        chapter_summary,
        current_fragment,
        rewrite_instruction,
        must_keep,
        forbidden_changes,
        temperature=temperature if temperature is not None else 0.8,
        top_p=top_p if top_p is not None else 0.9,
        max_tokens=max_tokens,
    )

    response = model_client.generate(request)

    if not response.text.strip():
        raise ProjectError(
            code="empty_response",
            message="模型返回空文本，本地改写失败",
            suggestion="请重试，或调整改写参数后重试。",
        )

    result = LocalRewriteResult(rewritten_text=response.text)

    if project_path is not None:
        _save_rewrite(Path(project_path), result)

    return result


def _validate_required(name: str, value: str) -> None:
    if not value.strip():
        raise EmptyTextError(
            message=f"本地改写参数 {name} 不能为空",
            suggestion=f"请提供 {name} 后重试。",
        )


def _save_rewrite(project_path: Path, result: LocalRewriteResult) -> None:
    revisions_dir = project_path / "revisions"
    revisions_dir.mkdir(parents=True, exist_ok=True)
    revision_path = revisions_dir / "rewritten.md"
    revision_path.write_text(result.rewritten_text, encoding="utf-8")
