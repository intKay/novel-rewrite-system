from typing import cast

import pytest
from pydantic import ValidationError

from novel_rewrite_system.models import (
    FakeModelClient,
    ModelClient,
    ModelRequest,
    ModelResponse,
)


def test_model_request_construction() -> None:
    request = ModelRequest(
        prompt="生成一段开场白",
        system_prompt="你是中文小说助手",
        temperature=0.8,
        top_p=0.9,
        max_tokens=1024,
        metadata={"project_id": "novel-001"},
    )

    assert request.prompt == "生成一段开场白"
    assert request.system_prompt == "你是中文小说助手"
    assert request.temperature == 0.8
    assert request.top_p == 0.9
    assert request.max_tokens == 1024
    assert request.metadata == {"project_id": "novel-001"}


@pytest.mark.parametrize(
    "request_data",
    [
        {"prompt": ""},
        {"prompt": "正文", "temperature": -0.1},
        {"prompt": "正文", "top_p": 1.1},
        {"prompt": "正文", "max_tokens": 0},
        {"prompt": "正文", "unexpected": True},
    ],
)
def test_model_request_rejects_invalid_data(request_data: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ModelRequest.model_validate(request_data)


def test_fake_model_client_returns_fixed_response() -> None:
    client = FakeModelClient(
        "固定返回文本",
        provider="test-provider",
        model="test-model",
    )

    response = client.generate(ModelRequest(prompt="任意提示词"))

    assert response == ModelResponse(
        text="固定返回文本",
        provider="test-provider",
        model="test-model",
        finish_reason="stop",
    )


def test_fake_model_client_records_last_request() -> None:
    client = FakeModelClient()
    request = ModelRequest(prompt="记录这个请求", metadata={"step": "unit-test"})

    client.generate(request)

    assert client.last_request == request


def test_business_layer_can_depend_on_model_client_interface() -> None:
    def generate_preview(client: ModelClient, prompt: str) -> str:
        response = client.generate(ModelRequest(prompt=prompt))
        return response.text

    client = cast(ModelClient, FakeModelClient("业务层只关心统一接口"))

    assert generate_preview(client, "写一个片段") == "业务层只关心统一接口"
