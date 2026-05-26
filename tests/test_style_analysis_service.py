"""风格分析服务单元测试。"""

from pathlib import Path

import pytest

from novel_rewrite_system.analysis.service import StyleAnalysisResult, analyze_style
from novel_rewrite_system.errors import EmptyTextError, ProjectError
from novel_rewrite_system.models import FakeModelClient
from novel_rewrite_system.text_chunks import TextChunk


def _make_chunks(*texts: str) -> list[TextChunk]:
    return [
        TextChunk(source_id="src-1", chapter_title=None, text=text, order=i + 1)
        for i, text in enumerate(texts)
    ]


class TestAnalyzeStyle:
    def test_returns_report_with_valid_chunks(self) -> None:
        chunks = _make_chunks("测试文本内容。")
        fake_client = FakeModelClient(text="风格分析结果：叙事视角为第三人称全知。")

        result = analyze_style(chunks, fake_client)

        assert isinstance(result, StyleAnalysisResult)
        assert "叙事视角" in result.report
        assert result.source_count == 1
        assert result.chunk_count == 1
        assert fake_client.last_request is not None

    def test_model_request_built_from_chunks(self) -> None:
        chunks = _make_chunks("夜色沉下来。她推开门。")
        fake_client = FakeModelClient()

        analyze_style(chunks, fake_client)

        assert fake_client.last_request is not None
        request = fake_client.last_request
        assert "夜色沉下来" in request.prompt
        assert request.temperature == 0.3
        assert request.top_p == 0.9
        assert request.system_prompt is not None

    def test_rejects_empty_chunks(self) -> None:
        fake_client = FakeModelClient()

        with pytest.raises(EmptyTextError, match="文本切片不能为空"):
            analyze_style([], fake_client)

    def test_rejects_empty_model_response(self) -> None:
        chunks = _make_chunks("测试文本。")
        fake_client = FakeModelClient(text="   ")

        with pytest.raises(ProjectError, match="空文本"):
            analyze_style(chunks, fake_client)

    def test_rejects_empty_string_model_response(self) -> None:
        chunks = _make_chunks("测试文本。")
        fake_client = FakeModelClient(text="")

        with pytest.raises(ProjectError, match="空文本"):
            analyze_style(chunks, fake_client)

    def test_passes_analysis_focus_to_prompt_builder(self) -> None:
        chunks = _make_chunks("测试文本。")
        fake_client = FakeModelClient()

        analyze_style(chunks, fake_client, analysis_focus=["叙事视角"])

        assert "重点关注：叙事视角" in fake_client.last_request.prompt

    def test_passes_max_chunks_and_reports_processed_count(self) -> None:
        chunks = _make_chunks("甲乙丙丁", "子丑寅卯", "辰巳午未")
        fake_client = FakeModelClient()

        result = analyze_style(chunks, fake_client, max_chunks=2)

        assert result.chunk_count == 2
        assert "甲乙丙丁" in fake_client.last_request.prompt
        assert "辰巳午未" not in fake_client.last_request.prompt

    def test_saves_report_when_project_path_given(self, tmp_path: Path) -> None:
        chunks = _make_chunks("测试文本。")
        fake_client = FakeModelClient(text="风格分析结果。")

        analyze_style(chunks, fake_client, project_path=tmp_path)

        report_file = tmp_path / "analysis" / "style_analysis_report.md"
        assert report_file.exists()
        assert report_file.read_text(encoding="utf-8") == "风格分析结果。"

    def test_creates_analysis_dir_if_missing(self, tmp_path: Path) -> None:
        chunks = _make_chunks("测试文本。")
        fake_client = FakeModelClient(text="分析报告。")
        assert not (tmp_path / "analysis").exists()

        analyze_style(chunks, fake_client, project_path=tmp_path)

        assert (tmp_path / "analysis").is_dir()

    def test_does_not_save_when_no_project_path(self, tmp_path: Path) -> None:
        chunks = _make_chunks("测试文本。")
        fake_client = FakeModelClient(text="分析报告。")

        analyze_style(chunks, fake_client)

        assert not (tmp_path / "analysis").exists()

    def test_source_count_counts_unique_sources(self) -> None:
        chunks = [
            TextChunk(source_id="source-a", chapter_title=None, text="文本一。", order=1),
            TextChunk(source_id="source-a", chapter_title=None, text="文本二。", order=2),
            TextChunk(source_id="source-b", chapter_title=None, text="文本三。", order=3),
        ]
        fake_client = FakeModelClient()

        result = analyze_style(chunks, fake_client)

        assert result.source_count == 2

    def test_chunk_count_equals_total_when_no_max_chunks(self) -> None:
        chunks = _make_chunks("甲乙丙丁", "子丑寅卯", "辰巳午未")
        fake_client = FakeModelClient()

        result = analyze_style(chunks, fake_client)

        assert result.chunk_count == 3

    def test_fake_client_records_last_request(self) -> None:
        chunks = _make_chunks("测试文本。")
        fake_client = FakeModelClient()
        assert fake_client.last_request is None

        analyze_style(chunks, fake_client)

        assert fake_client.last_request is not None
        assert isinstance(fake_client.last_request.prompt, str)

    def test_does_not_call_network(self) -> None:
        chunks = _make_chunks("测试文本。")
        fake_client = FakeModelClient(text="纯函数分析结果。")

        result = analyze_style(chunks, fake_client)

        assert result.report == "纯函数分析结果。"
