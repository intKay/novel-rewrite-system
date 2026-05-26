"""CLI 入口单元测试。"""

from pathlib import Path

import pytest

from novel_rewrite_system.cli import main
from novel_rewrite_system.errors import ProjectError
from novel_rewrite_system.models import FakeModelClient


REFERENCE_TEXT = "夜色沉下来。她推开门，听见远处的钟声。院中无人。\n\n她缓步走向庭中老槐，手指抚过粗糙树皮，心中涌起千般思绪。往事如昨。\n\n忽然，身后传来一声轻咳。"


class TestCliFakeMode:
    """6.1 已有行为回归测试。"""

    def test_returns_zero_on_success(self, tmp_path: Path) -> None:
        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--reference-file", str(ref_file),
            "--requirement", "创作一个仙侠故事。",
            "--project-path", str(project),
        ]
        exit_code = main(argv)

        assert exit_code == 0

    def test_output_paths_printed(self, capsys, tmp_path: Path) -> None:
        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--reference-file", str(ref_file),
            "--requirement", "仙侠故事。",
            "--project-path", str(project),
        ]
        main(argv)
        captured = capsys.readouterr()

        assert "风格分析报告" in captured.out
        assert "初稿" in captured.out
        assert "改写稿" in captured.out
        assert "日志" in captured.out

    def test_output_files_exist(self, tmp_path: Path) -> None:
        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--reference-file", str(ref_file),
            "--requirement", "仙侠故事。",
            "--project-path", str(project),
        ]
        main(argv)

        assert (project / "analysis" / "style_analysis_report.md").is_file()
        assert (project / "drafts" / "draft.md").is_file()
        assert (project / "revisions" / "rewritten.md").is_file()
        assert (project / "logs" / "pipeline.log").is_file()

    def test_missing_reference_file_returns_nonzero(self, tmp_path: Path) -> None:
        argv = [
            "--reference-file", str(tmp_path / "nonexistent.txt"),
            "--requirement", "仙侠故事。",
            "--project-path", str(tmp_path / "output"),
        ]
        exit_code = main(argv)

        assert exit_code == 1

    def test_missing_reference_file_prints_error(self, capsys, tmp_path: Path) -> None:
        argv = [
            "--reference-file", str(tmp_path / "nonexistent.txt"),
            "--requirement", "仙侠故事。",
            "--project-path", str(tmp_path / "output"),
        ]
        main(argv)
        captured = capsys.readouterr()

        assert "错误" in captured.out
        assert "不存在" in captured.out

    def test_summary_printed(self, capsys, tmp_path: Path) -> None:
        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--reference-file", str(ref_file),
            "--requirement", "创作一个武侠故事。",
            "--project-path", str(project),
        ]
        main(argv)
        captured = capsys.readouterr()

        assert "摘要" in captured.out
        assert "来源" in captured.out
        assert "切片" in captured.out
        assert "初稿字数" in captured.out
        assert "改写片段字数" in captured.out

    def test_custom_source_id_passed(self, capsys, tmp_path: Path) -> None:
        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--reference-file", str(ref_file),
            "--requirement", "武侠故事。",
            "--project-path", str(project),
            "--source-id", "my_source",
            "--rewrite-instruction", "请简化语言。",
            "--chunk-chars", "1000",
        ]
        exit_code = main(argv)

        assert exit_code == 0

    def test_no_network_calls(self, capsys, tmp_path: Path) -> None:
        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--reference-file", str(ref_file),
            "--requirement", "仙侠故事。",
            "--project-path", str(project),
        ]
        exit_code = main(argv)

        assert exit_code == 0

    def test_short_option_forms(self, tmp_path: Path) -> None:
        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "-r", str(ref_file),
            "-q", "短篇武侠故事。",
            "-p", str(project),
        ]
        exit_code = main(argv)

        assert exit_code == 0


class TestCliRealMode:
    """6.2 real 模式测试 —— 全部 mock，不访问真实网络。"""

    def test_real_mode_runs_with_mocked_clients(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
        monkeypatch.setattr(
            "novel_rewrite_system.cli.DeepSeekClient",
            lambda model="deepseek-v4-flash": FakeModelClient(
                text="mocked deepseek response", provider="deepseek", model=model,
            ),
        )
        monkeypatch.setattr(
            "novel_rewrite_system.cli.OllamaClient",
            lambda base_url="http://localhost:11434", model="qwen3:4b", timeout=120.0, num_ctx=2048: (
                FakeModelClient(
                    text="mocked ollama response", provider="ollama", model=model,
                )
            ),
        )

        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--model-mode", "real",
            "--reference-file", str(ref_file),
            "--requirement", "创作一个仙侠故事。",
            "--project-path", str(project),
        ]
        exit_code = main(argv)

        assert exit_code == 0
        assert (project / "analysis" / "style_analysis_report.md").is_file()
        assert (project / "drafts" / "draft.md").is_file()
        assert (project / "revisions" / "rewritten.md").is_file()

    def test_real_mode_missing_api_key_returns_nonzero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--model-mode", "real",
            "--reference-file", str(ref_file),
            "--requirement", "创作一个仙侠故事。",
            "--project-path", str(project),
        ]
        exit_code = main(argv)

        assert exit_code == 1

    def test_real_mode_missing_api_key_prints_chinese_error(
        self, tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--model-mode", "real",
            "--reference-file", str(ref_file),
            "--requirement", "创作一个仙侠故事。",
            "--project-path", str(project),
        ]
        main(argv)
        captured = capsys.readouterr()

        assert "错误" in captured.out
        assert "建议" in captured.out

    def test_real_mode_custom_ollama_params(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
        called_kwargs: dict = {}

        def _mock_ollama(**kwargs):
            called_kwargs.update(kwargs)
            return FakeModelClient(text="mocked ollama")

        monkeypatch.setattr("novel_rewrite_system.cli.DeepSeekClient",
                            lambda model="x": FakeModelClient(text="mocked"))
        monkeypatch.setattr("novel_rewrite_system.cli.OllamaClient", _mock_ollama)

        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--model-mode", "real",
            "--reference-file", str(ref_file),
            "--requirement", "故事。",
            "--project-path", str(project),
            "--ollama-base-url", "http://192.168.1.1:9999",
            "--ollama-model", "qwen2.5:3b",
            "--ollama-timeout", "60",
        ]
        main(argv)

        assert called_kwargs["base_url"] == "http://192.168.1.1:9999"
        assert called_kwargs["model"] == "qwen2.5:3b"
        assert called_kwargs["timeout"] == 60.0

    def test_real_mode_pipeline_error_caught(
        self, tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")

        def _failing_client(*args, **kwargs):
            client = FakeModelClient(text="   ")
            return client

        monkeypatch.setattr("novel_rewrite_system.cli.DeepSeekClient", _failing_client)
        monkeypatch.setattr("novel_rewrite_system.cli.OllamaClient",
                            lambda **kw: FakeModelClient(text="ok"))

        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--model-mode", "real",
            "--reference-file", str(ref_file),
            "--requirement", "故事。",
            "--project-path", str(project),
        ]
        exit_code = main(argv)
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "错误" in captured.out or "模型" in captured.out

    def test_real_mode_no_network(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
        monkeypatch.setattr("novel_rewrite_system.cli.DeepSeekClient",
                            lambda **kw: FakeModelClient(text="test"))
        monkeypatch.setattr("novel_rewrite_system.cli.OllamaClient",
                            lambda **kw: FakeModelClient(text="test"))

        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--model-mode", "real",
            "--reference-file", str(ref_file),
            "--requirement", "故事。",
            "--project-path", str(project),
        ]
        exit_code = main(argv)

        assert exit_code == 0


class TestCliCloudMode:
    """7.5 cloud 模式测试 —— 全部 mock，不访问真实网络。"""

    def test_cloud_mode_runs_with_mocked_client(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
        monkeypatch.setattr(
            "novel_rewrite_system.cli.DeepSeekClient",
            lambda model="deepseek-v4-flash": FakeModelClient(
                text="mocked deepseek response", provider="deepseek", model=model,
            ),
        )

        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--model-mode", "cloud",
            "--reference-file", str(ref_file),
            "--requirement", "创作一个仙侠故事。",
            "--project-path", str(project),
        ]
        exit_code = main(argv)

        assert exit_code == 0
        assert (project / "analysis" / "style_analysis_report.md").is_file()
        assert (project / "drafts" / "draft.md").is_file()
        assert (project / "revisions" / "rewritten.md").is_file()
        assert (project / "logs" / "pipeline.log").is_file()

    def test_cloud_mode_output_paths_printed(
        self, tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
        monkeypatch.setattr(
            "novel_rewrite_system.cli.DeepSeekClient",
            lambda model="deepseek-v4-flash": FakeModelClient(
                text="mocked", provider="deepseek", model=model,
            ),
        )

        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--model-mode", "cloud",
            "--reference-file", str(ref_file),
            "--requirement", "故事。",
            "--project-path", str(project),
        ]
        main(argv)
        captured = capsys.readouterr()

        assert "风格分析报告" in captured.out
        assert "初稿" in captured.out
        assert "改写稿" in captured.out
        assert "日志" in captured.out

    def test_cloud_mode_missing_api_key_returns_nonzero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--model-mode", "cloud",
            "--reference-file", str(ref_file),
            "--requirement", "创作一个仙侠故事。",
            "--project-path", str(project),
        ]
        exit_code = main(argv)

        assert exit_code == 1

    def test_cloud_mode_missing_api_key_prints_chinese_error(
        self, tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--model-mode", "cloud",
            "--reference-file", str(ref_file),
            "--requirement", "创作一个仙侠故事。",
            "--project-path", str(project),
        ]
        main(argv)
        captured = capsys.readouterr()

        assert "错误" in captured.out
        assert "建议" in captured.out

    def test_cloud_mode_pipeline_error_caught(
        self, tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
        monkeypatch.setattr(
            "novel_rewrite_system.cli.DeepSeekClient",
            lambda **kw: FakeModelClient(text="   "),
        )

        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--model-mode", "cloud",
            "--reference-file", str(ref_file),
            "--requirement", "故事。",
            "--project-path", str(project),
        ]
        exit_code = main(argv)
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "错误" in captured.out or "模型" in captured.out

    def test_cloud_mode_no_network(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
        monkeypatch.setattr(
            "novel_rewrite_system.cli.DeepSeekClient",
            lambda **kw: FakeModelClient(text="test"),
        )

        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--model-mode", "cloud",
            "--reference-file", str(ref_file),
            "--requirement", "故事。",
            "--project-path", str(project),
        ]
        exit_code = main(argv)

        assert exit_code == 0

    def test_cloud_mode_custom_deepseek_model(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
        called_args: list = []

        def _mock_deepseek(model="default"):
            called_args.append(model)
            return FakeModelClient(text="mocked", provider="deepseek", model=model)

        monkeypatch.setattr("novel_rewrite_system.cli.DeepSeekClient", _mock_deepseek)

        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--model-mode", "cloud",
            "--reference-file", str(ref_file),
            "--requirement", "故事。",
            "--project-path", str(project),
            "--deepseek-model", "deepseek-v4-pro",
        ]
        exit_code = main(argv)

        assert exit_code == 0
        assert "deepseek-v4-pro" in called_args

    def test_cloud_mode_does_not_use_ollama(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
        monkeypatch.setattr(
            "novel_rewrite_system.cli.DeepSeekClient",
            lambda model="deepseek-v4-flash": FakeModelClient(
                text="mocked", provider="deepseek", model=model,
            ),
        )
        ollama_called = False

        def _fail_ollama(*args, **kwargs):
            nonlocal ollama_called
            ollama_called = True
            raise RuntimeError("Ollama should not be used in cloud mode")

        monkeypatch.setattr("novel_rewrite_system.cli.OllamaClient", _fail_ollama)

        ref_file = tmp_path / "reference.txt"
        ref_file.write_text(REFERENCE_TEXT, encoding="utf-8")
        project = tmp_path / "output"

        argv = [
            "--model-mode", "cloud",
            "--reference-file", str(ref_file),
            "--requirement", "故事。",
            "--project-path", str(project),
        ]
        exit_code = main(argv)

        assert exit_code == 0
        assert not ollama_called
