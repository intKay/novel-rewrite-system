"""统一模型调用接口与测试用假模型。"""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class ModelRequest(BaseModel):
    """模型生成请求。"""

    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(..., min_length=1, description="用户提示词")
    system_prompt: str | None = Field(default=None, description="系统提示词")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="温度")
    top_p: float | None = Field(default=None, ge=0.0, le=1.0, description="核采样阈值")
    max_tokens: int | None = Field(default=None, gt=0, description="最大输出 token 数")
    metadata: dict[str, Any] | None = Field(default=None, description="调用元数据")


class ModelResponse(BaseModel):
    """模型生成响应。"""

    model_config = ConfigDict(extra="forbid")

    text: str
    provider: str
    model: str
    finish_reason: str | None = None
    usage: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None


class ModelClient(Protocol):
    """统一模型客户端协议。"""

    def generate(self, request: ModelRequest) -> ModelResponse:
        """根据请求生成文本。"""


class FakeModelClient:
    """测试和占位用模型客户端，不进行任何真实模型调用。"""

    def __init__(
        self,
        text: str = "fake response",
        *,
        provider: str = "fake",
        model: str = "fake-model",
    ) -> None:
        self.text = text
        self.provider = provider
        self.model = model
        self.last_request: ModelRequest | None = None

    def generate(self, request: ModelRequest) -> ModelResponse:
        """记录请求并返回固定响应。"""

        self.last_request = request
        return ModelResponse(
            text=self.text,
            provider=self.provider,
            model=self.model,
            finish_reason="stop",
        )
