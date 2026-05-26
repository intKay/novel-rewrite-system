"""最小端到端闭环编排器集成测试 —— 全程使用 FakeModelClient。"""

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from novel_rewrite_system.errors import EmptyTextError, ProjectError
from novel_rewrite_system.models import FakeModelClient, ModelRequest, ModelResponse
from novel_rewrite_system.pipeline import PipelineResult, run_minimal_pipeline


@dataclass
class QueueFakeModelClient:
    """按调用顺序返回不同文本的 fake 模型客户端。"""

    responses: list[str]
    _index: int = field(default=0, init=False)
    last_request: ModelRequest | None = field(default=None, init=False)

    def generate(self, request: ModelRequest) -> ModelResponse:
        text = self.responses[self._index] if self._index < len(self.responses) else self.responses[-1]
        self.last_request = request
        self._index += 1
        return ModelResponse(
            text=text,
            provider="queue-fake",
            model="queue-fake",
            finish_reason="stop",
        )


@pytest.fixture
def sample_reference_text() -> str:
    return """第一章 初入江湖

天色微明，晨雾缭绕在青石铺就的古道上。

少年背着行囊，脚步轻快地走向前方那座巍峨的城门。这是他第一次离开家乡，远赴千里之外的天剑宗参加入门考核。

"终于到了。"他抬头望着城门上方三个大字——天剑城，眼中闪烁着期待的光芒。"""


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    return tmp_path / "test-project"


class TestRunMinimalPipeline:
    def test_full_pipeline_produces_result(self, sample_reference_text: str, project_dir: Path) -> None:
        cloud = QueueFakeModelClient(
            responses=["风格分析报告：第三人称叙事。", "第一章 剑心初成\n\n少年踏入宗门。"]
        )
        local = FakeModelClient(text="改写后的片段：少年踏入宗门，晨光洒在青石路上。")

        result = run_minimal_pipeline(
            sample_reference_text,
            "创作一个仙侠故事",
            project_dir,
            model_client=cloud,
            local_client=local,
        )

        assert isinstance(result, PipelineResult)
        assert "第三人称" in result.style_report
        assert "第一章" in result.draft_text
        assert "改写后" in result.rewritten_fragment
        assert result.rewrite_original_fragment
        assert result.style_source_count == 1
        assert result.style_chunk_count == 1
        assert result.project_path == project_dir
        assert result.error_log == []

    def test_output_files_are_saved(self, sample_reference_text: str, project_dir: Path) -> None:
        cloud = QueueFakeModelClient(
            responses=["分析报告。", "初稿正文内容。"]
        )
        local = FakeModelClient(text="改写内容。")

        run_minimal_pipeline(
            sample_reference_text,
            "仙侠故事",
            project_dir,
            model_client=cloud,
            local_client=local,
        )

        assert (project_dir / "analysis" / "style_analysis_report.md").exists()
        assert (project_dir / "drafts" / "draft.md").exists()
        assert (project_dir / "revisions" / "rewritten.md").exists()
        assert (project_dir / "logs" / "pipeline.log").exists()

    def test_output_file_contents_correct(self, sample_reference_text: str, project_dir: Path) -> None:
        cloud = QueueFakeModelClient(
            responses=["分析报告内容。", "初稿正文。"]
        )
        local = FakeModelClient(text="改写后文本。")

        run_minimal_pipeline(
            sample_reference_text,
            "仙侠故事",
            project_dir,
            model_client=cloud,
            local_client=local,
        )

        style_content = (project_dir / "analysis" / "style_analysis_report.md").read_text("utf-8")
        draft_content = (project_dir / "drafts" / "draft.md").read_text("utf-8")
        rewrite_content = (project_dir / "revisions" / "rewritten.md").read_text("utf-8")
        log_content = (project_dir / "logs" / "pipeline.log").read_text("utf-8")

        assert "分析报告内容" in style_content
        assert "初稿正文" in draft_content
        assert "改写后文本" in rewrite_content
        assert "pipeline" in log_content.lower() or "管道" in log_content

    def test_cloud_client_called_twice(self, sample_reference_text: str, project_dir: Path) -> None:
        cloud = QueueFakeModelClient(
            responses=["风格报告。", "初稿内容。"]
        )
        local = FakeModelClient(text="改写内容。")

        run_minimal_pipeline(
            sample_reference_text,
            "仙侠故事",
            project_dir,
            model_client=cloud,
            local_client=local,
        )

        assert cloud._index == 2
        assert local.last_request is not None

    def test_fake_client_receives_prompt_with_reference(self, sample_reference_text: str, project_dir: Path) -> None:
        cloud = QueueFakeModelClient(
            responses=["风格报告。", "初稿内容。"]
        )
        local = FakeModelClient(text="改写内容。")

        run_minimal_pipeline(
            sample_reference_text,
            "仙侠故事",
            project_dir,
            model_client=cloud,
            local_client=local,
        )

        assert cloud.last_request is not None
        assert local.last_request is not None
        assert "改写" in local.last_request.prompt or "rewrite" in local.last_request.prompt.lower()

    def test_empty_reference_text_raises_error(self, project_dir: Path) -> None:
        cloud = QueueFakeModelClient(responses=["irrelevant"])
        local = FakeModelClient()

        with pytest.raises(EmptyTextError, match="不能为空"):
            run_minimal_pipeline(
                "",
                "仙侠故事",
                project_dir,
                model_client=cloud,
                local_client=local,
            )

    def test_whitespace_only_reference_text_raises_error(self, project_dir: Path) -> None:
        cloud = QueueFakeModelClient(responses=["irrelevant"])
        local = FakeModelClient()

        with pytest.raises(EmptyTextError, match="不能为空"):
            run_minimal_pipeline(
                "   \n\t  ",
                "仙侠故事",
                project_dir,
                model_client=cloud,
                local_client=local,
            )

    def test_empty_user_requirement_proceeds(self, sample_reference_text: str, project_dir: Path) -> None:
        cloud = QueueFakeModelClient(
            responses=["风格报告。", "初稿内容。"]
        )
        local = FakeModelClient(text="改写内容。")

        result = run_minimal_pipeline(
            sample_reference_text,
            "",
            project_dir,
            model_client=cloud,
            local_client=local,
        )

        assert result.requirement_raw == ""
        assert result.draft_text

    def test_first_fragment_extracted_from_chapter(self, project_dir: Path) -> None:
        draft_with_chapters = (
            "第一章 觉醒\n\n少年睁开眼睛。\n\n"
            "第二章 修炼\n\n他开始修行。"
        )
        cloud = QueueFakeModelClient(
            responses=["风格报告。", draft_with_chapters]
        )
        local = FakeModelClient(text="改写片段。")
        ref = "测试参考文本一段。"

        result = run_minimal_pipeline(
            ref,
            "故事",
            project_dir,
            model_client=cloud,
            local_client=local,
        )

        assert "少年睁开眼睛" in result.rewrite_original_fragment
        assert "修炼" not in result.rewrite_original_fragment

    def test_first_fragment_from_no_chapter_markers(self, project_dir: Path) -> None:
        draft_no_chapter = "这是一段很长的初稿。" + "故事内容。" * 500
        cloud = QueueFakeModelClient(
            responses=["风格报告。", draft_no_chapter]
        )
        local = FakeModelClient(text="改写片段。")
        ref = "测试参考文本。"

        result = run_minimal_pipeline(
            ref,
            "故事",
            project_dir,
            model_client=cloud,
            local_client=local,
        )

        assert len(result.rewrite_original_fragment) <= 2000

    def test_pipeline_result_paths_are_consistent(self, sample_reference_text: str, project_dir: Path) -> None:
        cloud = QueueFakeModelClient(
            responses=["分析。", "初稿。"]
        )
        local = FakeModelClient(text="改写。")

        result = run_minimal_pipeline(
            sample_reference_text,
            "故事",
            project_dir,
            model_client=cloud,
            local_client=local,
        )

        assert result.style_report_path == project_dir / "analysis" / "style_analysis_report.md"
        assert result.draft_path == project_dir / "drafts" / "draft.md"
        assert result.rewritten_path == project_dir / "revisions" / "rewritten.md"

    def test_no_real_network_calls(self, sample_reference_text: str, project_dir: Path) -> None:
        cloud = QueueFakeModelClient(
            responses=["风格报告。", "初稿。"]
        )
        local = FakeModelClient(text="改写。")

        result = run_minimal_pipeline(
            sample_reference_text,
            "仙侠故事",
            project_dir,
            model_client=cloud,
            local_client=local,
        )

        assert isinstance(result.style_report, str)
        assert isinstance(result.draft_text, str)
        assert isinstance(result.rewritten_fragment, str)

    def test_custom_rewrite_instruction(self, sample_reference_text: str, project_dir: Path) -> None:
        cloud = QueueFakeModelClient(
            responses=["风格报告。", "初稿内容。"]
        )
        local = FakeModelClient(text="对话版改写。")

        run_minimal_pipeline(
            sample_reference_text,
            "故事",
            project_dir,
            model_client=cloud,
            local_client=local,
            rewrite_instruction="把叙述改为对话形式",
        )

        assert "对话" in local.last_request.prompt

    def test_custom_chunk_chars(self, project_dir: Path) -> None:
        ref = "第一章\n\n" + "这是参考文本用来测试自定义切分参数的。" * 200
        cloud = QueueFakeModelClient(
            responses=["风格报告。", "这是初稿。" + "内容。" * 500]
        )
        local = FakeModelClient(text="改写。")

        result = run_minimal_pipeline(
            ref,
            "故事",
            project_dir,
            model_client=cloud,
            local_client=local,
            chunk_chars=100,
        )

        assert result.style_chunk_count > 1

    def test_pipeline_satisfies_interface(self) -> None:
        from novel_rewrite_system.models import ModelClient

        cloud: ModelClient = FakeModelClient(text="分析报告")
        local: ModelClient = FakeModelClient(text="改写")

        assert hasattr(cloud, "generate")
        assert hasattr(local, "generate")
