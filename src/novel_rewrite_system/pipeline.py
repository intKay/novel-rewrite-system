"""最小端到端闭环编排器 —— 串联清洗、切分、风格分析、初稿生成、本地改写。"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from novel_rewrite_system.analysis.service import analyze_style
from novel_rewrite_system.errors import EmptyTextError, ProjectError
from novel_rewrite_system.generation.service import generate_draft
from novel_rewrite_system.models import ModelClient
from novel_rewrite_system.requirements import StoryRequirement
from novel_rewrite_system.rewrite.service import rewrite_locally
from novel_rewrite_system.text_cleaning import clean_text
from novel_rewrite_system.text_chunks import split_text


@dataclass(frozen=True)
class PipelineResult:
    """最小闭环编排结果。"""

    style_report: str
    style_source_count: int
    style_chunk_count: int

    requirement_raw: str

    draft_text: str

    rewritten_fragment: str
    rewrite_original_fragment: str

    project_path: Path
    style_report_path: Path
    draft_path: Path
    rewritten_path: Path

    error_log: list[str] = field(default_factory=list)


def run_minimal_pipeline(
    reference_text: str,
    user_requirement_text: str,
    project_path: str | Path,
    *,
    source_id: str = "manual_input",
    model_client: ModelClient,
    local_client: ModelClient,
    rewrite_instruction: str = "请用更细腻的描写改写当前片段",
    chunk_chars: int = 2000,
    rewrite_fragment_chars: int = 600,
) -> PipelineResult:
    """执行 MVP 最小端到端闭环。

    流程：清洗 → 切分 → 风格分析 → 需求整理 → 初稿生成 → 本地改写 → 保存输出。

    Args:
        reference_text: 用户粘贴的参考小说正文。
        user_requirement_text: 用户自由文本创作要求。
        project_path: 项目根目录路径。
        source_id: 参考文本来源标识。
        model_client: 云端模型客户端（风格分析 + 初稿生成）。
        local_client: 本地模型客户端（改写）。
        rewrite_instruction: 本地改写指令。
        chunk_chars: 文本切分字数上限。

    Returns:
        PipelineResult，包含各阶段产物和落盘路径。

    Raises:
        EmptyTextError: 参考文本清洗后为空。
        ProjectError: 风格分析、初稿生成或本地改写返回空文本。
    """

    project = Path(project_path)
    error_log: list[str] = []

    try:
        cleaned = clean_text(reference_text)
    except ValueError as exc:
        raise EmptyTextError(
            message=str(exc),
            suggestion="请提供非空参考文本后重试。",
        ) from exc

    if not cleaned.strip():
        raise EmptyTextError(
            message="参考文本清洗后为空",
            suggestion="请提供非空参考文本后重试。",
        )

    chunks = split_text(source_id, cleaned, chunk_chars=chunk_chars)
    if not chunks:
        raise EmptyTextError(
            message="参考文本切分后为空",
            suggestion="请提供足够长度的参考文本后重试。",
        )

    style_result = analyze_style(chunks, model_client, project_path=project)

    requirement = StoryRequirement.from_text(user_requirement_text)

    draft_result = generate_draft(
        style_result.report,
        requirement,
        model_client,
        project_path=project,
    )

    fragment = _extract_first_fragment(draft_result.draft_text, rewrite_fragment_chars)

    style_report_short = _truncate_report(style_result.report, max_chars=1200)

    rewrite_result = rewrite_locally(
        global_summary=style_report_short,
        character_sheet=requirement.theme or "原创角色设定",
        chapter_summary="第一章：故事开篇",
        current_fragment=fragment,
        rewrite_instruction=rewrite_instruction,
        must_keep=requirement.required_plot_points or [],
        forbidden_changes=requirement.forbidden_content or [],
        model_client=local_client,
        project_path=project,
    )

    style_report_path = project / "analysis" / "style_analysis_report.md"
    draft_path = project / "drafts" / "draft.md"
    rewritten_path = project / "revisions" / "rewritten.md"

    _write_pipeline_log(
        project,
        {
            "source_id": source_id,
            "chunk_count": len(chunks),
            "style_source_count": style_result.source_count,
            "style_chunk_count": style_result.chunk_count,
            "draft_chars": len(draft_result.draft_text),
            "fragment_chars": len(fragment),
            "rewrite_chars": len(rewrite_result.rewritten_text),
            "error_count": len(error_log),
        },
        error_log,
    )

    return PipelineResult(
        style_report=style_result.report,
        style_source_count=style_result.source_count,
        style_chunk_count=style_result.chunk_count,
        requirement_raw=user_requirement_text,
        draft_text=draft_result.draft_text,
        rewritten_fragment=rewrite_result.rewritten_text,
        rewrite_original_fragment=fragment,
        project_path=project,
        style_report_path=style_report_path,
        draft_path=draft_path,
        rewritten_path=rewritten_path,
        error_log=error_log,
    )


def _extract_first_fragment(draft_text: str, chunk_chars: int) -> str:
    """从初稿中提取首个片段用于本地改写。

    优先取第一章内容（含"第X章"标记），否则取前 chunk_chars 字符，
    在句子边界（。！？）截断。
    """
    chapter_pattern = re.compile(r"第[一二三四五六七八九十百千0-9]+章")
    chapter_match = chapter_pattern.search(draft_text)

    if chapter_match:
        start = chapter_match.start()
        after_first = draft_text[start:]
        second_match = chapter_pattern.search(after_first, 1)
        if second_match:
            return after_first[: second_match.start()].strip()
        return _cut_at_sentence(after_first, chunk_chars).strip()

    return _cut_at_sentence(draft_text, chunk_chars).strip()


def _cut_at_sentence(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars]
    sentence_end = max(truncated.rfind("。"), truncated.rfind("！"), truncated.rfind("？"))

    if sentence_end > max_chars // 2:
        return text[: sentence_end + 1]

    return truncated + "。"


def _truncate_report(report: str, max_chars: int) -> str:
    """将风格报告截断到 max_chars 以内，在段落边界截断。"""
    if len(report) <= max_chars:
        return report
    truncated = report[:max_chars]
    last_break = max(truncated.rfind("\n\n"), truncated.rfind("。"), truncated.rfind("！"), truncated.rfind("？"))
    if last_break > max_chars // 2:
        return report[: last_break + 1]
    return truncated


def _write_pipeline_log(
    project_path: Path,
    summary: dict[str, object],
    error_log: list[str],
) -> None:
    logs_dir = project_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "pipeline.log"

    now = datetime.now(timezone.utc).isoformat()
    lines: list[str] = []
    lines.append(f"# 管道运行日志 — {now}")
    lines.append("")
    for key, value in summary.items():
        lines.append(f"- **{key}**: {value}")
    if error_log:
        lines.append("")
        lines.append("## 错误")
        for entry in error_log:
            lines.append(f"- {entry}")
    lines.append("")

    try:
        log_path.write_text("\n".join(lines), encoding="utf-8")
    except OSError as exc:
        logging.warning("pipeline log write failed: %s", exc)
