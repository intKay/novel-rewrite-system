"""最小 Streamlit WebUI 入口。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from novel_rewrite_system.deepseek_client import DeepSeekClient
from novel_rewrite_system.errors import ModelConfigError, ProjectError
from novel_rewrite_system.generation.continuation_service import generate_continuation
from novel_rewrite_system.models import FakeModelClient, ModelClient
from novel_rewrite_system.pipeline import PipelineResult, run_minimal_pipeline
from novel_rewrite_system.tags import CreativeTag, get_default_tags

_DEFAULT_REWRITE_INSTRUCTION = (
    "请在不改变核心剧情和人物设定的前提下，润色当前片段，使描写更自然、节奏更流畅。"
)


@dataclass(frozen=True)
class WebUiRunResult:
    """WebUI 单次运行结果。"""

    ok: bool
    mode: str
    status: str
    pipeline_result: PipelineResult | None = None
    error_code: str | None = None
    error_message: str | None = None
    error_suggestion: str | None = None


@dataclass(frozen=True)
class WebUiContinuationResult:
    """WebUI 续写结果。"""

    ok: bool
    continuation_text: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    error_suggestion: str | None = None


def run_webui_pipeline(
    *,
    project_path: str | Path,
    reference_text: str,
    user_requirement_text: str,
    mode: str = "fake",
    deepseek_model: str = "deepseek-v4-flash",
    source_id: str = "webui_manual_input",
    rewrite_instruction: str = _DEFAULT_REWRITE_INSTRUCTION,
    chunk_chars: int = 2000,
    rewrite_fragment_chars: int = 600,
) -> WebUiRunResult:
    """从 WebUI 表单参数运行 MVP 闭环。

    mode 只支持 fake 和 cloud-only。cloud-only 下风格分析、初稿和改写都使用 DeepSeek。
    """

    try:
        cloud_client, local_client = _build_model_clients(mode, deepseek_model)
        result = run_minimal_pipeline(
            reference_text=reference_text,
            user_requirement_text=user_requirement_text,
            project_path=project_path,
            source_id=source_id,
            model_client=cloud_client,
            local_client=local_client,
            rewrite_instruction=rewrite_instruction,
            chunk_chars=chunk_chars,
            rewrite_fragment_chars=rewrite_fragment_chars,
        )
    except ProjectError as exc:
        return WebUiRunResult(
            ok=False,
            mode=mode,
            status="运行失败",
            error_code=exc.code,
            error_message=exc.message,
            error_suggestion=exc.suggestion,
        )

    return WebUiRunResult(
        ok=True,
        mode=mode,
        status="运行完成",
        pipeline_result=result,
    )


def run_webui_continuation(
    *,
    current_text: str,
    continuation_instruction: str,
    mode: str,
    style_reference: str | None = None,
    selected_tags: list[CreativeTag] | None = None,
    deepseek_model: str = "deepseek-v4-flash",
    project_path: str | Path | None = None,
    target_word_count: int = 500,
) -> WebUiContinuationResult:
    """从 WebUI 表单参数运行继续扩写。"""

    try:
        if not current_text.strip():
            raise ValueError("当前文本不能为空")
        if not continuation_instruction.strip():
            raise ValueError("扩写需求不能为空")

        client, _ = _build_model_clients(mode, deepseek_model)

        result = generate_continuation(
            current_text=current_text,
            continuation_instruction=continuation_instruction,
            model_client=client,
            style_reference=style_reference,
            selected_tags=selected_tags,
            target_word_count=target_word_count,
            project_path=project_path,
        )
    except ValueError as exc:
        return WebUiContinuationResult(
            ok=False,
            error_code="invalid_input",
            error_message=str(exc),
        )
    except ProjectError as exc:
        return WebUiContinuationResult(
            ok=False,
            error_code=exc.code,
            error_message=exc.message,
            error_suggestion=exc.suggestion,
        )

    return WebUiContinuationResult(ok=True, continuation_text=result.continuation_text)


def _build_model_clients(mode: str, deepseek_model: str) -> tuple[ModelClient, ModelClient]:
    if mode == "fake":
        client = FakeModelClient()
        return client, client

    if mode == "cloud-only":
        if not os.getenv("DEEPSEEK_API_KEY"):
            raise ModelConfigError(
                message="DeepSeek API Key 未配置：环境变量 DEEPSEEK_API_KEY 为空或未设置",
                suggestion=(
                    "请先设置 DEEPSEEK_API_KEY 后再运行 cloud-only 模式；"
                    "fake 模式无需 API key。"
                ),
            )
        client = DeepSeekClient(model=deepseek_model)
        return client, client

    raise ProjectError(
        message=f"不支持的 WebUI 模式：{mode}",
        suggestion="请选择 fake 或 cloud-only。",
        code="invalid_webui_mode",
    )


def _resolve_reference_text(
    uploaded_bytes: bytes | None,
    manual_text: str,
) -> str:
    """有上传文件则读取上传文件，否则使用手动粘贴文本。

    Args:
        uploaded_bytes: 上传文件读出的字节，None 表示未上传文件。
        manual_text: 用户手动粘贴的文本。

    Returns:
        最终参考文本。

    Raises:
        ValueError: 文件无法用 UTF-8 解码。
    """
    if uploaded_bytes is not None:
        try:
            return uploaded_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(
                "文件解码失败：请使用 UTF-8 编码的文本文件。"
            ) from exc
    return manual_text


def main() -> None:
    """启动 Streamlit 单页 WebUI。"""

    import streamlit as st

    st.set_page_config(page_title="小说改写 MVP", layout="wide")
    st.title("小说改写 MVP")

    with st.form("webui-run-form"):
        project_path = st.text_input("项目路径", value=str(Path("outputs") / "webui-demo"))
        reference_text = st.text_area("参考文本", height=220)
        uploaded_file = st.file_uploader(
            "上传 .txt 参考文件（可选；上传后优先于上方文本输入）",
            type="txt",
        )
        st.caption("填写创作需求即可开始生成。生成后可在结果区继续扩写当前片段。")
        user_requirement_text = st.text_area("用户创作需求", height=140)
        mode = st.radio("模式", options=["fake", "cloud-only"], horizontal=True, index=0)

        with st.expander("高级参数", expanded=False):
            deepseek_model = st.text_input("DeepSeek 模型", value="deepseek-v4-flash")
            rewrite_instruction = st.text_input("内部默认改写指令（可选）", value=_DEFAULT_REWRITE_INSTRUCTION)
            chunk_chars = st.number_input("切分字数上限", min_value=100, max_value=10000, value=2000, step=100)
            rewrite_fragment_chars = st.number_input(
                "改写片段字数上限",
                min_value=100,
                max_value=3000,
                value=600,
                step=100,
            )

        submitted = st.form_submit_button("运行")

    status_box = st.empty()

    if submitted:
        try:
            uploaded_bytes = uploaded_file.read() if uploaded_file is not None else None
            ref_text = _resolve_reference_text(uploaded_bytes, reference_text)
        except ValueError as exc:
            status_box.error(str(exc))
            _clear_session_state()
            return

        with st.spinner("正在运行..."):
            run_result = run_webui_pipeline(
                project_path=project_path,
                reference_text=ref_text,
                user_requirement_text=user_requirement_text,
                mode=mode,
                deepseek_model=deepseek_model,
                rewrite_instruction=rewrite_instruction,
                chunk_chars=int(chunk_chars),
                rewrite_fragment_chars=int(rewrite_fragment_chars),
            )

        if not run_result.ok:
            status_box.error(run_result.status)
            st.error(run_result.error_message or "运行失败")
            if run_result.error_suggestion:
                st.info(run_result.error_suggestion)
            if run_result.error_code:
                st.caption(f"错误码：{run_result.error_code}")
            _clear_session_state()
            return

        status_box.success(run_result.status)
        if run_result.pipeline_result is None:
            st.error("运行结束但没有返回结果。")
            _clear_session_state()
            return

        st.session_state.pipeline_result = run_result.pipeline_result
        st.session_state.run_mode = mode
        st.session_state.run_deepseek_model = deepseek_model
        st.session_state.run_project_path = str(project_path)

    # ── Display results from session state ──
    result: PipelineResult | None = st.session_state.get("pipeline_result")
    if result is not None:
        st.subheader("风格分析结果")
        st.text_area("风格分析", value=result.style_report, height=220, disabled=True)

        st.subheader("初稿结果")
        st.text_area("初稿", value=result.draft_text, height=260, disabled=True)

        st.subheader("改写结果")
        st.text_area("改写", value=result.rewritten_fragment, height=220, disabled=True)

        st.subheader("输出路径")
        st.code(
            "\n".join(
                [
                    f"项目目录：{result.project_path}",
                    f"风格分析：{result.style_report_path}",
                    f"初稿：{result.draft_path}",
                    f"改写稿：{result.rewritten_path}",
                    f"日志：{result.project_path / 'logs' / 'pipeline.log'}",
                ]
            )
        )

        # ── Continuation ──
        st.subheader("继续扩写")
        cont_instruction = st.text_area(
            "扩写需求",
            height=100,
            placeholder="例如：续写下一段，主角发现了一个隐藏的线索……",
        )

        all_tags = get_default_tags()
        tag_options = {f"{t.name}（{t.category}）": t for t in all_tags}
        selected_labels = st.multiselect("创作控制标签（可选）", options=list(tag_options.keys()))
        selected_tags = [tag_options[label] for label in selected_labels]

        cont_clicked = st.button("生成下一段")

        if cont_clicked:
            if not cont_instruction.strip():
                st.error("请输入扩写需求。")
            else:
                with st.spinner("正在续写..."):
                    cont_result = run_webui_continuation(
                        current_text=result.draft_text,
                        continuation_instruction=cont_instruction,
                        mode=st.session_state.get("run_mode", "fake"),
                        style_reference=result.style_report,
                        selected_tags=selected_tags or None,
                        deepseek_model=st.session_state.get("run_deepseek_model", "deepseek-v4-flash"),
                        project_path=result.project_path,
                    )

                if cont_result.ok:
                    st.text_area("续写结果", value=cont_result.continuation_text, height=220, disabled=True)
                else:
                    st.error(cont_result.error_message or "续写失败")
                    if cont_result.error_suggestion:
                        st.info(cont_result.error_suggestion)
                    if cont_result.error_code:
                        st.caption(f"错误码：{cont_result.error_code}")


def _clear_session_state() -> None:
    """清除已保存的运行会话状态。"""
    import streamlit as st
    for key in ("pipeline_result", "run_mode", "run_deepseek_model", "run_project_path"):
        st.session_state.pop(key, None)


if __name__ == "__main__":
    main()
