"""Ollama 本地模型客户端单元测试 —— 使用 httpx.MockTransport，不访问真实网络。"""

import json

import httpx
import pytest

from novel_rewrite_system.errors import ProjectError
from novel_rewrite_system.models import ModelRequest
from novel_rewrite_system.ollama_client import OllamaClient


def _mock_response(*, status: int = 200, json_body: dict | None = None) -> httpx.Response:
    if json_body is None:
        json_body = {
            "model": "qwen3:4b",
            "created_at": "2024-01-01T00:00:00Z",
            "message": {"role": "assistant", "content": "这是一个本地模型测试回复。"},
            "done": True,
            "total_duration": 1234567890,
            "load_duration": 234567890,
            "prompt_eval_count": 50,
            "eval_count": 100,
        }
    return httpx.Response(status, json=json_body)


def _make_request(**kwargs) -> ModelRequest:
    defaults = {"prompt": "你好，请写一段小说。", "system_prompt": "你是小说家。", "temperature": 0.8}
    defaults.update(kwargs)
    return ModelRequest(**defaults)


def _make_client(**kwargs) -> OllamaClient:
    return OllamaClient(
        base_url="http://localhost:11434",
        model="qwen3:4b",
        **kwargs,
    )


class TestOllamaClientGenerate:
    def test_generate_returns_model_response(self) -> None:
        transport = httpx.MockTransport(lambda req: _mock_response())
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)

        response = client.generate(_make_request())

        assert response.text == "这是一个本地模型测试回复。"
        assert response.provider == "ollama"
        assert response.model == "qwen3:4b"
        assert response.finish_reason == "stop"
        assert response.usage == {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150}
        assert response.raw is not None

    def test_http_404_raises_project_error(self) -> None:
        transport = httpx.MockTransport(
            lambda req: httpx.Response(404, json={"error": "not found"})
        )
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)

        with pytest.raises(ProjectError, match="404"):
            client.generate(_make_request())

    def test_http_500_raises_project_error(self) -> None:
        transport = httpx.MockTransport(
            lambda req: httpx.Response(500, json={"error": "server error"})
        )
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)

        with pytest.raises(ProjectError, match="500"):
            client.generate(_make_request())

    def test_http_400_raises_project_error(self) -> None:
        transport = httpx.MockTransport(
            lambda req: httpx.Response(400, json={"error": "bad request"})
        )
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)

        with pytest.raises(ProjectError, match="400"):
            client.generate(_make_request())

    def test_non_json_response_raises_project_error(self) -> None:
        transport = httpx.MockTransport(lambda req: httpx.Response(200, content=b"not json"))
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)

        with pytest.raises(ProjectError, match="无法解析为 JSON"):
            client.generate(_make_request())

    def test_missing_message_field_raises_project_error(self) -> None:
        transport = httpx.MockTransport(
            lambda req: _mock_response(
                json_body={"model": "qwen3:4b", "done": True, "created_at": "..."}
            )
        )
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)

        with pytest.raises(ProjectError, match="message"):
            client.generate(_make_request())

    def test_system_prompt_included_in_request(self) -> None:
        captured_body: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_body.append(json.loads(request.content))
            return _mock_response()

        transport = httpx.MockTransport(handler)
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)

        client.generate(_make_request(system_prompt="你是专业小说家。"))

        assert len(captured_body) == 1
        messages = captured_body[0]["messages"]
        assert messages[0] == {"role": "system", "content": "你是专业小说家。"}
        assert messages[1]["role"] == "user"

    def test_temperature_top_p_in_options(self) -> None:
        captured_body: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_body.append(json.loads(request.content))
            return _mock_response()

        transport = httpx.MockTransport(handler)
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)

        client.generate(_make_request(temperature=0.7, top_p=0.9))

        options = captured_body[0]["options"]
        assert options["temperature"] == 0.7
        assert options["top_p"] == 0.9

    def test_max_tokens_becomes_num_predict(self) -> None:
        captured_body: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_body.append(json.loads(request.content))
            return _mock_response()

        transport = httpx.MockTransport(handler)
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)

        client.generate(_make_request(max_tokens=4096))

        options = captured_body[0]["options"]
        assert options["num_predict"] == 4096

    def test_optional_params_omitted_when_none(self) -> None:
        captured_body: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_body.append(json.loads(request.content))
            return _mock_response()

        transport = httpx.MockTransport(handler)
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)

        client.generate(ModelRequest(prompt="你好"))

        body = captured_body[0]
        assert "options" in body
        assert body["options"] == {"num_ctx": 4096}

    def test_stream_is_false(self) -> None:
        captured_body: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_body.append(json.loads(request.content))
            return _mock_response()

        transport = httpx.MockTransport(handler)
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)

        client.generate(_make_request())

        assert captured_body[0]["stream"] is False

    def test_uses_custom_base_url(self) -> None:
        captured_url: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_url.append(str(request.url))
            return _mock_response()

        transport = httpx.MockTransport(handler)
        http = httpx.Client(transport=transport)
        client = OllamaClient(
            base_url="http://192.168.1.100:11434",
            model="qwen2.5:3b",
            http_client=http,
        )

        client.generate(_make_request())

        assert captured_url[0] == "http://192.168.1.100:11434/api/chat"

    def test_satisfies_model_client_protocol(self) -> None:
        from novel_rewrite_system.models import ModelClient

        assert hasattr(OllamaClient, "generate")

    def test_no_real_network_call(self) -> None:
        transport = httpx.MockTransport(lambda req: _mock_response())
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)

        result = client.generate(_make_request())

        assert isinstance(result.text, str)
        assert len(result.text) > 0

    def test_error_messages_are_chinese(self) -> None:
        transport = httpx.MockTransport(lambda req: httpx.Response(500))
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)

        with pytest.raises(ProjectError) as exc_info:
            client.generate(_make_request())

        message = exc_info.value.message
        assert any("\u4e00" <= c <= "\u9fff" for c in message)

    def test_empty_content_returns_empty_text(self) -> None:
        transport = httpx.MockTransport(
            lambda req: _mock_response(
                json_body={
                    "model": "qwen3:4b",
                    "created_at": "2024-01-01T00:00:00Z",
                    "message": {"role": "assistant", "content": ""},
                    "done": True,
                }
            )
        )
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)

        result = client.generate(_make_request())

        assert result.text == ""

    def test_network_error_raises_project_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        transport = httpx.MockTransport(handler)
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)

        with pytest.raises(ProjectError, match="网络请求失败"):
            client.generate(_make_request())

    def test_exported_in_package(self) -> None:
        from novel_rewrite_system import OllamaClient as Exported

        assert Exported is OllamaClient

    def test_usage_omitted_when_no_token_counts(self) -> None:
        transport = httpx.MockTransport(
            lambda req: _mock_response(
                json_body={
                    "model": "qwen3:4b",
                    "message": {"role": "assistant", "content": "回复内容。"},
                    "done": True,
                }
            )
        )
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)

        result = client.generate(_make_request())

        assert result.usage is None

    def test_default_values(self) -> None:
        client = OllamaClient()

        assert client._base_url == "http://localhost:11434"
        assert client._model == "qwen3:4b"
        assert client._timeout == 120.0
        assert client._http is None
