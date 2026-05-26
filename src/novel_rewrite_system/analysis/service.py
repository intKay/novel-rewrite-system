"""风格分析服务 —— 串联提示词构建器与模型客户端。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from novel_rewrite_system.analysis.prompts.style import build_style_analysis_prompt
from novel_rewrite_system.errors import EmptyTextError, ProjectError
from novel_rewrite_system.models import ModelClient
from novel_rewrite_system.text_chunks import TextChunk


@dataclass(frozen=True)
class StyleAnalysisResult:
    """风格分析结果。"""

    report: str
    source_count: int
    chunk_count: int


def analyze_style(
    chunks: list[TextChunk],
    model_client: ModelClient,
    *,
    analysis_focus: list[str] | None = None,
    max_chunks: int | None = None,
    project_path: str | Path | None = None,
) -> StyleAnalysisResult:
    """对参考文本切片进行风格分析并将结果返回，可选保存到项目 analysis/ 目录。

    Args:
        chunks: 参考文本切片列表，必须非空。
        model_client: 实现了 ModelClient 协议的模型客户端。
        analysis_focus: 可选分析关注点列表，默认覆盖全部九项。
        max_chunks: 可选参与分析的切片数量上限。
        project_path: 可选项目路径，若提供则将报告保存到 analysis/ 目录下。

    Returns:
        StyleAnalysisResult，包含报告文本、参考来源数和实际分析切片数。

    Raises:
        EmptyTextError: chunks 为空。
        ProjectError: 模型返回空文本。
    """

    if not chunks:
        raise EmptyTextError(
            message="风格分析的参考文本切片不能为空",
            suggestion="请提供至少一个非空文本切片后重试。",
        )

    request = build_style_analysis_prompt(
        chunks,
        analysis_focus=analysis_focus,
        max_chunks=max_chunks,
    )

    response = model_client.generate(request)

    if not response.text.strip():
        raise ProjectError(
            code="empty_response",
            message="模型返回空文本，风格分析失败",
            suggestion="请重试，或调整分析参数（如减少 max_chunks）后重试。",
        )

    processed_chunks: int = (
        min(len(chunks), max_chunks) if max_chunks is not None else len(chunks)
    )

    result = StyleAnalysisResult(
        report=response.text,
        source_count=len({chunk.source_id for chunk in chunks}),
        chunk_count=processed_chunks,
    )

    if project_path is not None:
        _save_report(Path(project_path), result)

    return result


def _save_report(project_path: Path, result: StyleAnalysisResult) -> None:
    analysis_dir = project_path / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    report_path = analysis_dir / "style_analysis_report.md"
    report_path.write_text(result.report, encoding="utf-8")
