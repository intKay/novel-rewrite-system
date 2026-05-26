from pathlib import Path

import pytest
from pydantic import ValidationError

from novel_rewrite_system.config import Settings, load_settings


def test_load_settings_from_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.yaml"
    config_path.write_text(
        """
app:
  project_root: ./workspace
cloud_model:
  provider: cloud-provider
  model: cloud-model
  api_key_env: CLOUD_API_KEY
  base_url: https://example.test/api
local_model:
  provider: local-provider
  model: local-model
  endpoint: http://localhost:11434
generation:
  temperature: 0.8
  max_tokens: 2048
""",
        encoding="utf-8",
    )

    settings = load_settings(config_path)

    assert isinstance(settings, Settings)
    assert settings.app.project_root == Path("workspace")
    assert settings.cloud_model.provider == "cloud-provider"
    assert settings.local_model.model == "local-model"
    assert settings.generation.temperature == 0.8
    assert settings.generation.max_tokens == 2048


def test_load_settings_rejects_unknown_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.yaml"
    config_path.write_text(
        """
app:
  project_root: ./workspace
  unexpected: true
cloud_model:
  provider: cloud-provider
  model: cloud-model
local_model:
  provider: local-provider
  model: local-model
generation:
  temperature: 0.7
  max_tokens: 1024
""",
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_settings(config_path)


def test_load_settings_rejects_non_mapping_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.yaml"
    config_path.write_text("- item\n", encoding="utf-8")

    with pytest.raises(ValueError, match="顶层必须是 YAML 映射对象"):
        load_settings(config_path)
