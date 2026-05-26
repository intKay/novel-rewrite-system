"""DeepSeek 云端模型客户端 —— 实现 ModelClient 协议。"""

from __future__ import annotations

import os
from typing import Any

import httpx

from novel_rewrite_system.errors import ModelConfigError, ProjectError
from novel_rewrite_system.models import ModelRequest, ModelResponse


class DeepSeekClient:
    """DeepSeek API 云端模型客户端，满足 ``ModelClient`` 协议。

    业务层依赖 ``ModelClient`` 协议而非本类。测试时可注入 ``FakeModelClient``。
    """

    def __init__(
        self,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-v4-flash",
        api_key_env: str = "DEEPSEEK_API_KEY",
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key_env = api_key_env
        self._http = http_client

    # ---- ModelClient 协议 ----

    def generate(self, request: ModelRequest) -> ModelResponse:
        """调用 DeepSeek API 生成文本。"""

        api_key = _resolve_api_key(self._api_key_env)

        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": False,
        }
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.top_p is not None:
            body["top_p"] = request.top_p
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens

        endpoint = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        response = _post_json(endpoint, body, headers, http_client=self._http)
        return _parse_api_response(response, provider="deepseek", model=self._model)


def _resolve_api_key(env_var: str) -> str:
    key = os.getenv(env_var)
    if not key:
        raise ModelConfigError(
            message=f"DeepSeek API Key 未配置：环境变量 {env_var} 为空或未设置",
            suggestion=f"请在终端中设置 {env_var}，例如：\n  Linux/macOS: export {env_var}=\"sk-...\"\n  Windows: set {env_var}=sk-...",
        )
    return key


def _post_json(
    url: str,
    body: dict[str, Any],
    headers: dict[str, str],
    *,
    http_client: httpx.Client | None = None,
) -> httpx.Response:
    if http_client is not None:
        try:
            return http_client.post(url, json=body, headers=headers)
        except Exception as exc:
            raise ProjectError(
                message=f"DeepSeek API 网络请求失败：{exc}",
                suggestion="请检查网络连接、API 地址是否正确，稍后重试。",
                details={"error": str(exc)},
            ) from exc

    try:
        with httpx.Client(timeout=httpx.Timeout(120.0)) as client:
            return client.post(url, json=body, headers=headers)
    except Exception as exc:
        raise ProjectError(
            message=f"DeepSeek API 网络请求失败：{exc}",
            suggestion="请检查网络连接、API 地址是否正确，稍后重试。",
            details={"error": str(exc)},
        ) from exc


def _parse_api_response(
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
            message="DeepSeek API 返回内容无法解析为 JSON",
            suggestion="请重试。如果持续失败请联系 API 供应商。",
            details={"status_code": response.status_code, "body_preview": response.text[:300]},
        )

    choices = data.get("choices", [])
    if not choices:
        raise ProjectError(
            message="DeepSeek API 返回结果中没有 choices",
            suggestion="请检查模型名称是否正确，或重试。",
            details={"response_keys": list(data.keys()) if isinstance(data, dict) else None},
        )

    choice = choices[0]
    message = choice.get("message", {})
    content = message.get("content", "")

    return ModelResponse(
        text=content,
        provider=provider,
        model=model,
        finish_reason=choice.get("finish_reason"),
        usage=data.get("usage"),
        raw=data,
    )


def _raise_http_error(response: httpx.Response) -> None:
    status = response.status_code
    body_preview = response.text[:500] if response.text else ""

    if status == 401:
        raise ProjectError(
            message="DeepSeek API 认证失败（401）：API Key 无效或已过期",
            suggestion="请检查环境变量中的 API Key 是否正确，是否需要重新生成。",
            details={"status_code": status, "body_preview": body_preview},
        )
    if status == 429:
        raise ProjectError(
            message="DeepSeek API 请求频率超限（429）",
            suggestion="请稍后重试，或降低请求频率。",
            details={"status_code": status},
        )
    if status >= 500:
        raise ProjectError(
            message=f"DeepSeek API 服务器错误（{status}）",
            suggestion="请稍后重试。如果持续失败请联系 API 供应商。",
            details={"status_code": status, "body_preview": body_preview},
        )

    raise ProjectError(
        message=f"DeepSeek API 返回异常 HTTP 状态 {status}",
        suggestion="请检查请求参数是否正确，或稍后重试。",
        details={"status_code": status, "body_preview": body_preview},
    )
