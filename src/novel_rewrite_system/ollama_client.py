"""Ollama 本地模型客户端 —— 实现 ModelClient 协议。"""

from __future__ import annotations

from typing import Any

import httpx

from novel_rewrite_system.errors import ModelConfigError, ProjectError
from novel_rewrite_system.models import ModelRequest, ModelResponse


class OllamaClient:
    """Ollama 本地模型客户端，满足 ``ModelClient`` 协议。

    业务层依赖 ``ModelClient`` 协议而非本类。测试时可注入 ``FakeModelClient``。
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3:4b",
        *,
        timeout: float = 120.0,
        num_ctx: int = 4096,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._num_ctx = num_ctx
        self._http = http_client

    # ---- ModelClient 协议 ----

    def generate(self, request: ModelRequest) -> ModelResponse:
        """调用 Ollama API 生成文本。"""

        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        options: dict[str, Any] = {}
        options["num_ctx"] = self._num_ctx
        if request.temperature is not None:
            options["temperature"] = request.temperature
        if request.top_p is not None:
            options["top_p"] = request.top_p
        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens

        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": False,
        }
        if options:
            body["options"] = options

        endpoint = f"{self._base_url}/api/chat"
        headers: dict[str, str] = {"Content-Type": "application/json"}

        response = _post_json(
            endpoint, body, headers,
            http_client=self._http,
            timeout=self._timeout,
        )
        return _parse_ollama_response(response, provider="ollama", model=self._model)


def _post_json(
    url: str,
    body: dict[str, Any],
    headers: dict[str, str],
    *,
    http_client: httpx.Client | None = None,
    timeout: float = 120.0,
) -> httpx.Response:
    if http_client is not None:
        try:
            return http_client.post(url, json=body, headers=headers)
        except Exception as exc:
            raise ProjectError(
                message=f"Ollama 本地模型网络请求失败：{exc}",
                suggestion="请检查 Ollama 是否已启动（可运行 ollama serve 或 ollama list），稍后重试。",
                details={"error": str(exc)},
            ) from exc

    try:
        with httpx.Client(timeout=httpx.Timeout(timeout)) as client:
            return client.post(url, json=body, headers=headers)
    except Exception as exc:
        raise ProjectError(
            message=f"Ollama 本地模型网络请求失败：{exc}",
            suggestion="请检查 Ollama 是否已启动（可运行 ollama serve 或 ollama list），稍后重试。",
            details={"error": str(exc)},
        ) from exc


def _parse_ollama_response(
    response: httpx.Response,
    *,
    provider: str,
    model: str,
) -> ModelResponse:
    if response.status_code != 200:
        _raise_http_error(response)

    try:
        data = response.json()
    except Exception:
        raise ProjectError(
            message="Ollama 本地模型返回内容无法解析为 JSON",
            suggestion="请重试。如果持续失败请检查 Ollama 服务状态。",
            details={"status_code": response.status_code, "body_preview": response.text[:300]},
        )

    if "message" not in data:
        raise ProjectError(
            message="Ollama 本地模型返回结果中没有 message 字段",
            suggestion="请检查模型名称是否正确，或重试。",
            details={"response_keys": list(data.keys()) if isinstance(data, dict) else None},
        )
    message = data["message"]
    if not isinstance(message, dict):
        raise ProjectError(
            message="Ollama 本地模型返回结果中 message 字段格式异常",
            suggestion="请检查模型名称是否正确，或重试。",
            details={"message_type": str(type(message))},
        )

    content = message.get("content", "")

    usage: dict[str, Any] | None = None
    if "eval_count" in data or "prompt_eval_count" in data:
        usage = {}
        if "prompt_eval_count" in data:
            usage["prompt_tokens"] = data["prompt_eval_count"]
        if "eval_count" in data:
            usage["completion_tokens"] = data["eval_count"]
        if "prompt_eval_count" in data and "eval_count" in data:
            usage["total_tokens"] = data["prompt_eval_count"] + data["eval_count"]

    return ModelResponse(
        text=content,
        provider=provider,
        model=data.get("model", model),
        finish_reason="stop" if data.get("done") else None,
        usage=usage,
        raw=data,
    )


def _raise_http_error(response: httpx.Response) -> None:
    status = response.status_code
    body_preview = response.text[:500] if response.text else ""

    if status == 404:
        raise ProjectError(
            message="Ollama 本地模型接口不存在（404）：请确认 Ollama 版本是否支持 /api/chat 接口",
            suggestion="请更新 Ollama 到最新版本（v0.1.14 及以上支持 /api/chat），或检查 base_url 配置是否正确。",
            details={"status_code": status},
        )
    if status >= 500:
        raise ProjectError(
            message=f"Ollama 本地模型服务器错误（{status}）",
            suggestion="请检查 Ollama 服务日志，稍后重试。",
            details={"status_code": status, "body_preview": body_preview},
        )

    raise ProjectError(
        message=f"Ollama 本地模型返回异常 HTTP 状态 {status}",
        suggestion="请检查 base_url 和模型名称是否正确，或稍后重试。",
        details={"status_code": status, "body_preview": body_preview},
    )
