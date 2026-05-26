"""续写生成服务测试。"""

from pathlib import Path

import pytest

from novel_rewrite_system.errors import EmptyTextError, ProjectError
from novel_rewrite_system.generation.continuation_service import generate_continuation
from novel_rewrite_system.models import FakeModelClient
from novel_rewrite_system.tags import get_default_tags

CURRENT_TEXT = "夜色沉下来。她推开门，听见远处的钟声。院中无人。"
INSTRUCTION = "续写下一段，描写庭院中的老槐树。"


def test_returns_continuation_text() -> None:
    client = FakeModelClient(text="续写内容：月光洒在老槐树上。")
    result = generate_continuation(CURRENT_TEXT, INSTRUCTION, client)
    assert result.continuation_text == "续写内容：月光洒在老槐树上。"


def test_empty_current_text_raises_error() -> None:
    with pytest.raises(EmptyTextError, match="不能为空"):
        generate_continuation("", INSTRUCTION, FakeModelClient())


def test_empty_instruction_raises_error() -> None:
    with pytest.raises(EmptyTextError, match="不能为空"):
        generate_continuation(CURRENT_TEXT, "", FakeModelClient())


def test_model_empty_response_raises_error() -> None:
    client = FakeModelClient(text="")
    with pytest.raises(ProjectError, match="返回空文本"):
        generate_continuation(CURRENT_TEXT, INSTRUCTION, client)


def test_style_reference_passed_through() -> None:
    client = FakeModelClient(text="续写内容。")
    style = "冷峻风格"
    generate_continuation(CURRENT_TEXT, INSTRUCTION, client, style_reference=style)
    assert client.last_request is not None
    assert style in client.last_request.prompt


def test_saves_continuation_when_project_path_provided(tmp_path: Path) -> None:
    client = FakeModelClient(text="续写结果。")
    result = generate_continuation(
        CURRENT_TEXT,
        INSTRUCTION,
        client,
        project_path=tmp_path,
    )
    continuation_path = tmp_path / "drafts" / "continuation.md"
    assert continuation_path.is_file()
    assert continuation_path.read_text(encoding="utf-8") == result.continuation_text


def test_fake_model_client_no_network() -> None:
    """fake 模式不访问网络。"""
    client = FakeModelClient(text="fake continuation")
    result = generate_continuation(CURRENT_TEXT, INSTRUCTION, client)
    assert client.last_request is not None
    assert result.continuation_text == "fake continuation"


def test_selected_tags_appear_in_prompt() -> None:
    client = FakeModelClient(text="续写结果。")
    tags = get_default_tags()[:2]
    generate_continuation(CURRENT_TEXT, INSTRUCTION, client, selected_tags=tags)
    assert client.last_request is not None
    assert tags[0].name in client.last_request.prompt
    assert tags[1].name in client.last_request.prompt


def test_no_tags_does_not_add_tag_section() -> None:
    client = FakeModelClient(text="续写结果。")
    generate_continuation(CURRENT_TEXT, INSTRUCTION, client, selected_tags=None)
    assert client.last_request is not None
    assert "创作控制标签" not in client.last_request.prompt
