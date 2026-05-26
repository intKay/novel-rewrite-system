# Phase 1 项目基础骨架交接记录

## 任务名称

- Phase 1：项目基础骨架

## 修改范围

- 创建最小 Python 项目结构。
- 实现 YAML 配置读取与 Pydantic 配置校验。
- 实现按 `project_id` 初始化项目目录的基础能力。
- 添加配置读取与项目目录创建的单元测试。
- 未实现 WebUI、模型调用、抓取、分析、生成或改写逻辑。

## 新增/修改文件

- `pyproject.toml`
- `README.md`
- `.gitignore`
- `src/novel_rewrite_system/__init__.py`
- `src/novel_rewrite_system/config.py`
- `src/novel_rewrite_system/projects.py`
- `tests/test_config.py`
- `tests/test_projects.py`

## 暴露接口

- `novel_rewrite_system.config.load_settings(config_path: str | Path) -> Settings`
- `novel_rewrite_system.config.AppConfig`
- `novel_rewrite_system.config.CloudModelConfig`
- `novel_rewrite_system.config.LocalModelConfig`
- `novel_rewrite_system.config.GenerationConfig`
- `novel_rewrite_system.config.Settings`
- `novel_rewrite_system.projects.PROJECT_SUBDIRECTORIES`
- `novel_rewrite_system.projects.create_project_directories(project_root: str | Path, project_id: str) -> Path`
- 包级导出：`AppConfig`、`CloudModelConfig`、`LocalModelConfig`、`GenerationConfig`、`Settings`、`load_settings`、`PROJECT_SUBDIRECTORIES`、`create_project_directories`

## 数据结构变化

- 新增 `AppConfig`：包含 `project_root: Path`。
- 新增 `CloudModelConfig`：包含 `provider: str`、`model: str`、`api_key_env: str | None`、`base_url: str | None`。
- 新增 `LocalModelConfig`：包含 `provider: str`、`model: str`、`endpoint: str | None`。
- 新增 `GenerationConfig`：包含 `temperature: float`、`max_tokens: int`。
- 新增 `Settings`：聚合 `app`、`cloud_model`、`local_model`、`generation` 四类配置。
- 所有 Phase 1 配置模型均使用 Pydantic，并禁止未知字段。

## 配置变化

- `pyproject.toml` 声明 Python 版本要求为 `>=3.11`。
- 新增运行依赖：`pydantic>=2.0`、`PyYAML>=6.0`。
- 新增开发测试依赖：`pytest>=8.0`。
- `pytest` 配置使用 `tests` 作为测试目录，并将 `src` 加入 `pythonpath`。

## 测试命令

```bash
.venv/bin/python -m pytest -q -s
```

## 测试结果

- 已重新运行测试。
- 结果：`37 passed in 2.94s`。

## 未完成事项

- Phase 1 不包含 WebUI、抓取、分析、生成、改写或真实模型调用。
- 未提供默认配置文件样例；后续可在需要启动完整流程时补充。
- 未实现项目元数据索引、持久化记录或配置文件写入。

## 对其他模块的影响

- 后续模块可通过 `load_settings` 读取统一配置对象，避免把模型供应商写死在业务逻辑中。
- 后续模块可通过 `create_project_directories` 初始化项目目录，并依赖 `PROJECT_SUBDIRECTORIES` 获取标准目录清单。
- `project_id` 当前只允许单层目录名，空白值、`.`、`..` 和包含路径分隔符的值会被拒绝。

## 下一步建议

- 为后续项目管理模块补充项目元数据文件或索引结构。
- 增加配置样例文件，并明确运行环境中的路径约定。
- 在模型调用模块接入前继续保持模型供应商与业务逻辑解耦。
