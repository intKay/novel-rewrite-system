"""项目通用错误类型与用户可读消息。"""

from __future__ import annotations

from typing import Any


class ProjectError(Exception):
    """带错误码、用户消息和处理建议的项目基础异常。"""

    code = "project_error"
    default_message = "项目处理失败"
    default_suggestion = "请检查输入后重试。"

    def __init__(
        self,
        message: str | None = None,
        *,
        suggestion: str | None = None,
        details: dict[str, Any] | None = None,
        code: str | None = None,
    ) -> None:
        self.code = code or self.code
        self.message = message or self.default_message
        self.suggestion = suggestion or self.default_suggestion
        self.details = details
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """转换为适合 API 或日志消费的用户可读字典。"""

        data: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "suggestion": self.suggestion,
        }
        if self.details is not None:
            data["details"] = self.details
        return data

    def to_text(self) -> str:
        """转换为适合 CLI 或纯文本界面展示的消息。"""

        text = f"[{self.code}] {self.message}\n建议：{self.suggestion}"
        if self.details is not None:
            text += f"\n详情：{self.details}"
        return text


class ConfigError(ProjectError):
    code = "config_error"
    default_message = "配置读取或校验失败"
    default_suggestion = "请检查配置文件路径、YAML 格式和必填字段。"


class EmptyTextError(ProjectError):
    code = "empty_text"
    default_message = "文本不能为空"
    default_suggestion = "请提供非空文本后重试。"


class ProjectNotFoundError(ProjectError):
    code = "project_not_found"
    default_message = "项目不存在"
    default_suggestion = "请确认项目 ID 是否正确，或先创建项目。"


class DuplicateProjectError(ProjectError):
    code = "duplicate_project"
    default_message = "项目已存在"
    default_suggestion = "请更换 project_id，或使用已有项目。"


class ModelConfigError(ProjectError):
    code = "model_config_error"
    default_message = "模型配置无效"
    default_suggestion = "请检查模型供应商、模型名称、接口地址和 API Key 环境变量。"


def error_to_dict(error: ProjectError) -> dict[str, Any]:
    """将项目错误转换为用户可读字典。"""

    return error.to_dict()


def error_to_text(error: ProjectError) -> str:
    """将项目错误转换为用户可读文本。"""

    return error.to_text()
