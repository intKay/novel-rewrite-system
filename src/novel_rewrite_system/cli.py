"""最小 CLI 入口 —— 调用 5.4 编排器跑端到端闭环。

支持三种模式：
- fake（默认）：使用 FakeModelClient，无需外部依赖
- cloud（推荐）：全部使用 DeepSeek API（风格分析、初稿生成、片段改写），无需本地模型
- real：风格分析/初稿用 DeepSeek + 改写用 Ollama（需本地 Ollama 服务）
"""

from __future__ import annotations

import argparse
from pathlib import Path

from novel_rewrite_system.deepseek_client import DeepSeekClient
from novel_rewrite_system.errors import ProjectError
from novel_rewrite_system.models import FakeModelClient, ModelClient
from novel_rewrite_system.ollama_client import OllamaClient
from novel_rewrite_system.pipeline import run_minimal_pipeline


def main(argv: list[str] | None = None) -> int:
    """最小 CLI 入口，默认使用 FakeModelClient。

    Args:
        argv: 命令行参数列表，为 None 时使用 sys.argv[1:]。

    Returns:
        0 表示成功，非零表示失败。
    """

    parser = argparse.ArgumentParser(
        prog="story-rewrite",
        description="中文小说生成与本地改写系统 — 最小端到端闭环",
    )
    parser.add_argument(
        "--reference-file", "-r",
        required=True,
        help="参考小说文本文件路径",
    )
    parser.add_argument(
        "--requirement", "-q",
        required=True,
        help="用户创作要求文本",
    )
    parser.add_argument(
        "--project-path", "-p",
        required=True,
        help="项目输出目录路径",
    )
    parser.add_argument(
        "--source-id",
        default="manual_input",
        help="参考文本来源标识（默认：manual_input）",
    )
    parser.add_argument(
        "--rewrite-instruction",
        default="请用更细腻的描写改写当前片段",
        help="本地改写指令（默认：更细腻描写）",
    )
    parser.add_argument(
        "--chunk-chars",
        type=int,
        default=2000,
        help="文本切分字数上限（默认：2000）",
    )
    parser.add_argument(
        "--rewrite-fragment-chars",
        type=int,
        default=600,
        help="本地改写片段字数上限（默认：600）",
    )
    parser.add_argument(
        "--model-mode",
        choices=["fake", "cloud", "real"],
        default="fake",
        help="模型模式：fake=测试假模型（默认），cloud=全部 DeepSeek API（推荐），real=DeepSeek+Ollama",
    )
    parser.add_argument(
        "--deepseek-model",
        default="deepseek-v4-flash",
        help="DeepSeek 模型名称（默认：deepseek-v4-flash）",
    )
    parser.add_argument(
        "--ollama-base-url",
        default="http://localhost:11434",
        help="Ollama 服务地址（默认：http://localhost:11434）",
    )
    parser.add_argument(
        "--ollama-model",
        default="qwen3:4b",
        help="Ollama 模型名称（默认：qwen3:4b）",
    )
    parser.add_argument(
        "--ollama-timeout",
        type=float,
        default=120.0,
        help="Ollama 请求超时秒数（默认：120）",
    )
    parser.add_argument(
        "--ollama-num-ctx",
        type=int,
        default=2048,
        help="Ollama 上下文窗口 token 数（默认：2048）",
    )

    args = parser.parse_args(argv)

    ref_path = Path(args.reference_file)
    if not ref_path.is_file():
        print(f"[错误] 参考文本文件不存在：{args.reference_file}")
        return 1

    try:
        reference_text = ref_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"[错误] 无法读取参考文本文件：{exc}")
        return 1

    if args.model_mode == "fake":
        cloud_client: ModelClient = FakeModelClient()
        local_client: ModelClient = FakeModelClient()
    elif args.model_mode == "cloud":
        cloud_client = DeepSeekClient(model=args.deepseek_model)
        local_client = DeepSeekClient(model=args.deepseek_model)
        print(f"[诊断] cloud 模式：风格分析/初稿/改写均使用 DeepSeek model={args.deepseek_model}")
    else:
        cloud_client = DeepSeekClient(model=args.deepseek_model)
        local_client = OllamaClient(
            base_url=args.ollama_base_url,
            model=args.ollama_model,
            timeout=args.ollama_timeout,
            num_ctx=args.ollama_num_ctx,
        )
        print(f"[诊断] real 模式：Ollama model={args.ollama_model} num_ctx={args.ollama_num_ctx} fragment_max={args.rewrite_fragment_chars}")

    try:
        result = run_minimal_pipeline(
            reference_text=reference_text,
            user_requirement_text=args.requirement,
            project_path=args.project_path,
            source_id=args.source_id,
            model_client=cloud_client,
            local_client=local_client,
            rewrite_instruction=args.rewrite_instruction,
            chunk_chars=args.chunk_chars,
            rewrite_fragment_chars=args.rewrite_fragment_chars,
        )
    except ProjectError as exc:
        print(f"[错误] {exc.message}")
        print(f"建议：{exc.suggestion}")
        return 1

    print(f"风格分析报告：{result.style_report_path}")
    print(f"初稿：{result.draft_path}")
    print(f"改写稿：{result.rewritten_path}")
    print(f"日志：{result.project_path / 'logs' / 'pipeline.log'}")
    print()
    print(f"摘要：参考文本 {result.style_source_count} 来源 / {result.style_chunk_count} 切片")
    print(f"初稿字数：{len(result.draft_text)}")
    print(f"改写片段字数：{len(result.rewritten_fragment)}")

    if result.error_log:
        print(f"\n非致命错误：{len(result.error_log)} 条")
        for entry in result.error_log:
            print(f"  - {entry}")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
