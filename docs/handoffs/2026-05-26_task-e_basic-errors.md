# 任务名称

- 任务E：基础错误类型与用户可读错误消息

## 修改范围

- 新增独立的项目基础错误模块。
- 新增错误格式单元测试。
- 更新任务状态与接口登记。

## 新增/修改文件

- `src/novel_rewrite_system/errors.py`
- `src/novel_rewrite_system/__init__.py`
- `tests/test_errors.py`
- `docs/task_status.md`
- `docs/interface_registry.md`
- `docs/handoffs/2026-05-26_task-e_basic-errors.md`

## 暴露接口

- `ProjectError`
- `ConfigError`
- `EmptyTextError`
- `ProjectNotFoundError`
- `DuplicateProjectError`
- `ModelConfigError`
- `error_to_dict(error: ProjectError) -> dict`
- `error_to_text(error: ProjectError) -> str`

## 数据结构变化

- `ProjectError` 最小字段：`code`、`message`、`suggestion`、可选 `details`。
- `to_dict()` 输出默认不包含空 `details`。

## 配置变化

- 无。

## 测试命令

```bash
.venv/bin/python -m pytest -q -s tests/test_errors.py
.venv/bin/python -m pytest -q -s
```

## 测试结果

- Python 3.11.15 可用。
- `tests/test_errors.py`：`5 passed in 1.17s`。
- 全量测试：`63 passed in 3.47s`。

## 未完成事项

- 未接入 FastAPI exception handler。
- 未接入 WebUI 错误展示。
- 未接入 DeepSeek 或 Ollama 重试。
- 未批量替换既有 `ValueError`。

## 对其他模块的影响

- 当前模块独立，不要求现有模块立刻接入。
- 后续配置读取、文本清洗、项目管理、模型调用模块可以逐步改用这些错误类型。

## 下一步建议

- 在后续任务中按模块逐步接入，避免一次性大规模替换。
