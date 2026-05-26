# 本地任务状态

本文件记录各 Codex 会话之间需要共享的任务进度、输出接口和验证方式。每个任务开始前应先查看本表；任务完成后应更新对应行。

| 任务编号 | 任务名称 | 状态 | 所属模块 | 负责会话 | 主要输出 | 暴露接口 | 测试命令 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Phase 1 | 项目基础骨架 | 已完成 | 项目基础 | Codex | 最小 Python 项目结构、YAML 配置读取、Pydantic 配置模型、项目目录创建、单元测试 | `load_settings`；`Settings`；`AppConfig`；`CloudModelConfig`；`LocalModelConfig`；`GenerationConfig`；`create_project_directories`；`PROJECT_SUBDIRECTORIES` | `.venv/bin/python -m pytest -q -s` | 交接记录：[`2026-05-26_phase-1_project-skeleton.md`](handoffs/2026-05-26_phase-1_project-skeleton.md) |
| Task A | 文本切分模块 | 已完成 | 文本处理 | Codex | `TextChunk` 与 `split_text` 纯函数文本切分 | `TextChunk`; `split_text(...) -> list[TextChunk]` | `python3 -m pytest -s tests` | 交接记录：[2026-05-26_task-a_text-chunking.md](handoffs/2026-05-26_task-a_text-chunking.md)；测试结果：`37 passed` |
| Task B | 用户需求结构化数据模型 | 已完成 | 用户需求 | Codex | `StoryRequirement` Pydantic 模型和 `from_text` 占位入口 | `StoryRequirement`; `StoryRequirement.from_text(raw_text: str) -> StoryRequirement` | `python3 -m pytest -q -s tests/test_requirements.py`; `python3 -m pytest -q -s` | 交接记录：[`2026-05-26_task-b_story-requirements.md`](handoffs/2026-05-26_task-b_story-requirements.md) |
| Task C | 模型接口抽象层 | 已完成 | 模型调用 | Codex | `ModelRequest`、`ModelResponse`、`ModelClient`、`FakeModelClient` | `ModelClient.generate(request: ModelRequest) -> ModelResponse`; `FakeModelClient.last_request` | `pytest -s` | 交接记录：[2026-05-26_task-c_model-interface.md](handoffs/2026-05-26_task-c_model-interface.md) |
| Parallel Task 1 | 手动参考文本输入与保存 | 已完成 | 参考文本输入 | Codex | `ManualTextInput`、`ManualSourceMetadata` 和 `save_manual_source`，可将手动粘贴正文保存到项目 `sources/` 目录并写入 JSON 元数据 | `ManualTextInput`; `ManualSourceMetadata`; `save_manual_source(project_path, manual_input, *, created_at=None) -> ManualSourceMetadata` | `python3 -m pytest -q -s tests/test_sources.py`; `python3 -m pytest -q -s` | 已同步 README 与接口登记；覆盖正文/元数据写入、空正文拒绝、非法 `source_id` 拒绝 |

## 状态说明

- 未开始：尚未有会话处理。
- 进行中：已有会话正在处理，其他会话应避免重复修改同一模块。
- 已完成：功能或文档已交付，并记录主要输出和验证方式。
- 阻塞：存在依赖、环境或设计问题，需要先解决。
