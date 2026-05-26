"""配置结构与 YAML 读取。"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class AppConfig(BaseModel):
    """应用级配置。"""

    model_config = ConfigDict(extra="forbid")

    project_root: Path = Field(..., description="项目数据根目录")


class CloudModelConfig(BaseModel):
    """云端模型配置，不绑定具体供应商。"""

    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str
    api_key_env: str | None = None
    base_url: str | None = None


class LocalModelConfig(BaseModel):
    """本地模型配置，不绑定具体供应商。"""

    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str
    endpoint: str | None = None


class GenerationConfig(BaseModel):
    """生成参数配置。"""

    model_config = ConfigDict(extra="forbid")

    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, gt=0)


class Settings(BaseModel):
    """系统总配置。"""

    model_config = ConfigDict(extra="forbid")

    app: AppConfig
    cloud_model: CloudModelConfig
    local_model: LocalModelConfig
    generation: GenerationConfig


def load_settings(config_path: str | Path) -> Settings:
    """从 YAML 文件读取并校验系统配置。"""

    path = Path(config_path)
    with path.open("r", encoding="utf-8") as file:
        raw_config: Any = yaml.safe_load(file)

    if raw_config is None:
        raw_config = {}

    if not isinstance(raw_config, dict):
        raise ValueError("配置文件顶层必须是 YAML 映射对象")

    try:
        return Settings.model_validate(raw_config)
    except ValidationError:
        raise
