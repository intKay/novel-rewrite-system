"""本地改写服务单元测试。"""

from pathlib import Path

import pytest

from novel_rewrite_system.errors import EmptyTextError, ProjectError
from novel_rewrite_system.models import FakeModelClient
from novel_rewrite_system.rewrite.service import LocalRewriteResult, rewrite_locally


def _make_args(**overrides: str | list[str] | None) -> dict:
    defaults: dict = {
        "global_summary": "这是一个武侠世界，有内功、轻功和剑术三大修炼体系。",
        "character_sheet": "主角：林逸，剑客。配角：苏晴，医者。",
        "chapter_summary": "本章讲述林逸在破庙中偶遇受伤的苏晴，两人初次交锋。",
        "current_fragment": (
            "林逸推开破庙的木门，一阵寒风灌入。地上躺着一个白衣女子，"
            "肩头染血，面色苍白。他脚步一顿，手按剑柄。"
        ),
        "rewrite_instruction": "将场景从破庙改为废弃道观，林逸的性格从孤傲改为内敛。",
        "must_keep": ["林逸遇到了受伤的苏晴", "林逸最初保持警惕"],
        "forbidden_changes": ["苏晴的性别", "两人初次相遇的事实"],
    }
    defaults.update(overrides)
    return defaults


class TestRewriteLocally:
    def test_returns_rewrite_result_with_valid_input(self) -> None:
        fake_client = FakeModelClient(text="改写道观后的文本。\n修改说明：场景已替换为废弃道观。")

        result = rewrite_locally(**_make_args(), model_client=fake_client)

        assert isinstance(result, LocalRewriteResult)
        assert "改写道观" in result.rewritten_text
        assert "修改说明" in result.rewritten_text
        assert fake_client.last_request is not None

    def test_model_request_built_from_inputs(self) -> None:
        fake_client = FakeModelClient()

        rewrite_locally(**_make_args(), model_client=fake_client)

        assert fake_client.last_request is not None
        request = fake_client.last_request
        assert "武侠世界" in request.prompt
        assert "林逸" in request.prompt
        assert "破庙" in request.prompt
        assert "废弃道观" in request.prompt
        assert request.system_prompt is not None

    def test_must_keep_in_request(self) -> None:
        fake_client = FakeModelClient()

        rewrite_locally(**_make_args(), model_client=fake_client)

        assert "林逸遇到了受伤的苏晴" in fake_client.last_request.prompt
        assert "必须保留的剧情点" in fake_client.last_request.prompt

    def test_forbidden_changes_in_request(self) -> None:
        fake_client = FakeModelClient()

        rewrite_locally(**_make_args(), model_client=fake_client)

        assert "苏晴的性别" in fake_client.last_request.prompt
        assert "禁止改变的事实" in fake_client.last_request.prompt

    def test_rejects_empty_current_fragment(self) -> None:
        fake_client = FakeModelClient()

        with pytest.raises(EmptyTextError, match="current_fragment"):
            rewrite_locally(**_make_args(current_fragment=""), model_client=fake_client)

    def test_rejects_empty_rewrite_instruction(self) -> None:
        fake_client = FakeModelClient()

        with pytest.raises(EmptyTextError, match="rewrite_instruction"):
            rewrite_locally(**_make_args(rewrite_instruction=""), model_client=fake_client)

    def test_rejects_empty_global_summary(self) -> None:
        fake_client = FakeModelClient()

        with pytest.raises(EmptyTextError, match="global_summary"):
            rewrite_locally(**_make_args(global_summary=""), model_client=fake_client)

    def test_rejects_whitespace_only_fragment(self) -> None:
        fake_client = FakeModelClient()

        with pytest.raises(EmptyTextError):
            rewrite_locally(**_make_args(current_fragment="   \n  "), model_client=fake_client)

    def test_rejects_empty_model_response(self) -> None:
        fake_client = FakeModelClient(text="   ")

        with pytest.raises(ProjectError, match="空文本"):
            rewrite_locally(**_make_args(), model_client=fake_client)

    def test_rejects_empty_string_model_response(self) -> None:
        fake_client = FakeModelClient(text="")

        with pytest.raises(ProjectError, match="空文本"):
            rewrite_locally(**_make_args(), model_client=fake_client)

    def test_saves_rewrite_when_project_path_given(self, tmp_path: Path) -> None:
        fake_client = FakeModelClient(text="改写后的片段。\n修改说明：场景替换。")

        rewrite_locally(**_make_args(), model_client=fake_client, project_path=tmp_path)

        revision_file = tmp_path / "revisions" / "rewritten.md"
        assert revision_file.exists()
        assert revision_file.read_text(encoding="utf-8") == "改写后的片段。\n修改说明：场景替换。"

    def test_creates_revisions_dir_if_missing(self, tmp_path: Path) -> None:
        fake_client = FakeModelClient(text="改写文本。")
        assert not (tmp_path / "revisions").exists()

        rewrite_locally(**_make_args(), model_client=fake_client, project_path=tmp_path)

        assert (tmp_path / "revisions").is_dir()

    def test_does_not_save_when_no_project_path(self, tmp_path: Path) -> None:
        fake_client = FakeModelClient(text="改写文本。")

        rewrite_locally(**_make_args(), model_client=fake_client)

        assert not (tmp_path / "revisions").exists()

    def test_empty_must_keep_handled(self) -> None:
        fake_client = FakeModelClient()

        rewrite_locally(**_make_args(must_keep=[]), model_client=fake_client)

        assert "无特殊要求" in fake_client.last_request.prompt

    def test_empty_forbidden_changes_handled(self) -> None:
        fake_client = FakeModelClient()

        rewrite_locally(**_make_args(forbidden_changes=[]), model_client=fake_client)

        assert "无特殊限制" in fake_client.last_request.prompt

    def test_custom_generation_params_passed(self) -> None:
        fake_client = FakeModelClient()

        rewrite_locally(
            **_make_args(),
            model_client=fake_client,
            temperature=0.7,
            top_p=0.95,
            max_tokens=2048,
        )

        assert fake_client.last_request is not None
        assert fake_client.last_request.temperature == 0.7
        assert fake_client.last_request.top_p == 0.95
        assert fake_client.last_request.max_tokens == 2048

    def test_default_generation_params(self) -> None:
        fake_client = FakeModelClient()

        rewrite_locally(**_make_args(), model_client=fake_client)

        assert fake_client.last_request.temperature == 0.8
        assert fake_client.last_request.top_p == 0.9

    def test_fake_client_records_last_request(self) -> None:
        fake_client = FakeModelClient()
        assert fake_client.last_request is None

        rewrite_locally(**_make_args(), model_client=fake_client)

        assert fake_client.last_request is not None
        assert isinstance(fake_client.last_request.prompt, str)

    def test_does_not_call_network(self) -> None:
        fake_client = FakeModelClient(text="纯函数改写的文本。")

        result = rewrite_locally(**_make_args(), model_client=fake_client)

        assert result.rewritten_text == "纯函数改写的文本。"
