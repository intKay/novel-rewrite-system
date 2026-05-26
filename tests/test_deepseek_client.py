"""DeepSeek 云端模型客户端单元测试 —— 使用 httpx.MockTransport，不访问真实网络。"""

import json
import os
from unittest.mock import patch

import httpx
import pytest

from novel_rewrite_system.deepseek_client import DeepSeekClient
from novel_rewrite_system.errors import ModelConfigError, ProjectError
from novel_rewrite_system.models import ModelRequest


def _mock_response(*, status: int = 200, json_body: dict | None = None) -> httpx.Response:
    if json_body is None:
        json_body = {
            "id": "test-id",
            "model": "deepseek-v4-flash",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "这是一个测试回复。"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 100,
                "total_tokens": 150,
            },
        }
    return httpx.Response(status, json=json_body)


def _make_request(**kwargs) -> ModelRequest:
    defaults = {"prompt": "你好，请写一段小说。", "system_prompt": "你是小说家。", "temperature": 0.8}
    defaults.update(kwargs)
    return ModelRequest(**defaults)


def _make_client(**kwargs) -> DeepSeekClient:
    return DeepSeekClient(
        base_url="https://api.deepseek.com",
        model="deepseek-v4-flash",
        api_key_env="TEST_DEEPSEEK_KEY",
        **kwargs,
    )


class TestDeepSeekClientGenerate:
    def test_generate_returns_model_response(self) -> None:
        transport = httpx.MockTransport(lambda req: _mock_response())
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)
        with patch.dict(os.environ, {"TEST_DEEPSEEK_KEY": "sk-test"}):
            response = client.generate(_make_request())

        assert response.text == "这是一个测试回复。"
        assert response.provider == "deepseek"
        assert response.model == "deepseek-v4-flash"
        assert response.finish_reason == "stop"
        assert response.usage == {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150}
        assert response.raw is not None

    def test_missing_api_key_raises_model_config_error(self) -> None:
        client = _make_client()
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ModelConfigError, match="未配置"):
                client.generate(_make_request())

    def test_http_401_raises_project_error(self) -> None:
        transport = httpx.MockTransport(
            lambda req: _mock_response(status=401, json_body={"error": "invalid api key"})
        )
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)
        with patch.dict(os.environ, {"TEST_DEEPSEEK_KEY": "sk-test"}):
            with pytest.raises(ProjectError, match="401"):
                client.generate(_make_request())

    def test_http_429_raises_project_error(self) -> None:
        transport = httpx.MockTransport(
            lambda req: _mock_response(status=429, json_body={"error": "rate limited"})
        )
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)
        with patch.dict(os.environ, {"TEST_DEEPSEEK_KEY": "sk-test"}):
            with pytest.raises(ProjectError, match="429"):
                client.generate(_make_request())

    def test_http_500_raises_project_error(self) -> None:
        transport = httpx.MockTransport(
            lambda req: _mock_response(status=500, json_body={"error": "server error"})
        )
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)
        with patch.dict(os.environ, {"TEST_DEEPSEEK_KEY": "sk-test"}):
            with pytest.raises(ProjectError, match="500"):
                client.generate(_make_request())

    def test_http_403_raises_project_error(self) -> None:
        transport = httpx.MockTransport(
            lambda req: _mock_response(status=403, json_body={"error": "forbidden"})
        )
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)
        with patch.dict(os.environ, {"TEST_DEEPSEEK_KEY": "sk-test"}):
            with pytest.raises(ProjectError, match="403"):
                client.generate(_make_request())

    def test_empty_choices_raises_project_error(self) -> None:
        transport = httpx.MockTransport(
            lambda req: _mock_response(
                json_body={
                    "id": "test-id",
                    "model": "test-model",
                    "choices": [],
                }
            )
        )
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)
        with patch.dict(os.environ, {"TEST_DEEPSEEK_KEY": "sk-test"}):
            with pytest.raises(ProjectError, match="没有 choices"):
                client.generate(_make_request())

    def test_non_json_response_raises_project_error(self) -> None:
        transport = httpx.MockTransport(lambda req: httpx.Response(200, content=b"not json"))
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)
        with patch.dict(os.environ, {"TEST_DEEPSEEK_KEY": "sk-test"}):
            with pytest.raises(ProjectError, match="无法解析为 JSON"):
                client.generate(_make_request())

    def test_system_prompt_included_in_request(self) -> None:
        captured_body: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            captured_body.append(body)
            return _mock_response()

        transport = httpx.MockTransport(handler)
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)
        with patch.dict(os.environ, {"TEST_DEEPSEEK_KEY": "sk-test"}):
            client.generate(_make_request(system_prompt="你是专业小说家。"))

        assert len(captured_body) == 1
        messages = captured_body[0]["messages"]
        assert messages[0] == {"role": "system", "content": "你是专业小说家。"}
        assert messages[1]["role"] == "user"

    def test_temperature_top_p_max_tokens_in_request(self) -> None:
        captured_body: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_body.append(json.loads(request.content))
            return _mock_response()

        transport = httpx.MockTransport(handler)
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)
        with patch.dict(os.environ, {"TEST_DEEPSEEK_KEY": "sk-test"}):
            client.generate(_make_request(temperature=0.7, top_p=0.9, max_tokens=4096))

        assert captured_body[0]["temperature"] == 0.7
        assert captured_body[0]["top_p"] == 0.9
        assert captured_body[0]["max_tokens"] == 4096

    def test_optional_params_omitted_when_none(self) -> None:
        captured_body: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_body.append(json.loads(request.content))
            return _mock_response()

        transport = httpx.MockTransport(handler)
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)
        with patch.dict(os.environ, {"TEST_DEEPSEEK_KEY": "sk-test"}):
            client.generate(ModelRequest(prompt="你好"))

        body = captured_body[0]
        assert "temperature" not in body
        assert "top_p" not in body
        assert "max_tokens" not in body

    def test_stream_is_false(self) -> None:
        captured_body: list[dict] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_body.append(json.loads(request.content))
            return _mock_response()

        transport = httpx.MockTransport(handler)
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)
        with patch.dict(os.environ, {"TEST_DEEPSEEK_KEY": "sk-test"}):
            client.generate(_make_request())

        assert captured_body[0]["stream"] is False

    def test_uses_custom_base_url(self) -> None:
        captured_url: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured_url.append(str(request.url))
            return _mock_response()

        transport = httpx.MockTransport(handler)
        http = httpx.Client(transport=transport)
        client = DeepSeekClient(
            base_url="https://custom.api.example.com/v1",
            model="custom-model",
            api_key_env="TEST_KEY",
            http_client=http,
        )
        with patch.dict(os.environ, {"TEST_KEY": "sk-test"}):
            client.generate(_make_request())

        assert captured_url[0] == "https://custom.api.example.com/v1/chat/completions"

    def test_satisfies_model_client_protocol(self) -> None:
        from novel_rewrite_system.models import ModelClient

        assert hasattr(DeepSeekClient, "generate")

    def test_no_real_network_call(self) -> None:
        transport = httpx.MockTransport(lambda req: _mock_response())
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)
        with patch.dict(os.environ, {"TEST_DEEPSEEK_KEY": "sk-test"}):
            result = client.generate(_make_request())

        assert isinstance(result.text, str)
        assert len(result.text) > 0

    def test_error_messages_are_chinese(self) -> None:
        transport = httpx.MockTransport(lambda req: _mock_response(status=401))
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)
        with patch.dict(os.environ, {"TEST_DEEPSEEK_KEY": "sk-test"}):
            with pytest.raises(ProjectError) as exc_info:
                client.generate(_make_request())

        message = exc_info.value.message
        assert any("\u4e00" <= c <= "\u9fff" for c in message)

    def test_empty_content_returns_empty_text(self) -> None:
        transport = httpx.MockTransport(
            lambda req: _mock_response(
                json_body={
                    "id": "test-id",
                    "model": "test-model",
                    "choices": [{"index": 0, "message": {"role": "assistant", "content": ""}, "finish_reason": "stop"}],
                }
            )
        )
        http = httpx.Client(transport=transport)
        client = _make_client(http_client=http)
        with patch.dict(os.environ, {"TEST_DEEPSEEK_KEY": "sk-test"}):
            result = client.generate(_make_request())

        assert result.text == ""

    def test_exported_in_package(self) -> None:
        from novel_rewrite_system import DeepSeekClient as Exported

        assert Exported is DeepSeekClient
