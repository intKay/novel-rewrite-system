"""最小 Streamlit WebUI 入口。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from novel_rewrite_system.deepseek_client import DeepSeekClient
from novel_rewrite_system.errors import ModelConfigError, ProjectError
from novel_rewrite_system.models import FakeModelClient, ModelClient
from novel_rewrite_system.pipeline import PipelineResult, run_minimal_pipeline


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


def run_webui_pipeline(
    *,
    project_path: str | Path,
    reference_text: str,
    user_requirement_text: str,
    mode: str = "fake",
    deepseek_model: str = "deepseek-v4-flash",
    source_id: str = "webui_manual_input",
    rewrite_instruction: str = "请用更细腻的描写改写当前片段",
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


def main() -> None:
    """启动 Streamlit 单页 WebUI。"""

    import streamlit as st

    st.set_page_config(page_title="小说改写 MVP", layout="wide")
    st.title("小说改写 MVP")

    with st.form("webui-run-form"):
        project_path = st.text_input("项目路径", value=str(Path("outputs") / "webui-demo"))
        reference_text = st.text_area("参考文本", height=220)
        user_requirement_text = st.text_area("用户创作需求", height=140)
        mode = st.radio("模式", options=["fake", "cloud-only"], horizontal=True, index=0)

        with st.expander("高级参数", expanded=False):
            deepseek_model = st.text_input("DeepSeek 模型", value="deepseek-v4-flash")
            rewrite_instruction = st.text_input("改写指令", value="请用更细腻的描写改写当前片段")
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
        with st.spinner("正在运行..."):
            run_result = run_webui_pipeline(
                project_path=project_path,
                reference_text=reference_text,
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
            return

        status_box.success(run_result.status)
        result = run_result.pipeline_result
        if result is None:
            st.error("运行结束但没有返回结果。")
            return

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


if __name__ == "__main__":
    main()
