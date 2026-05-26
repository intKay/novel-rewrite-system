# Parallel Task 1 手动参考文本输入与保存模块交接记录

## 任务名称

- 并行任务 1：手动参考文本输入与保存模块

## 修改范围

- 新增手动参考小说文本的数据结构和保存函数。
- 将用户手动粘贴的正文保存到项目目录 `sources/` 下。
- 同步保存简单 JSON 元数据，标记来源类型为 `manual`。
- 未接入网页抓取、文本切分、风格分析、模型调用、WebUI、SQLite、初稿生成或本地改写。

## 新增/修改文件

- `src/novel_rewrite_system/sources.py`：新增 `ManualTextInput`、`ManualSourceMetadata` 和 `save_manual_source`。
- `tests/test_sources.py`：新增手动参考文本保存单元测试。
- `docs/handoffs/2026-05-26_parallel-1_manual-source-input.md`：本交接记录。
- `docs/interface_registry.md`：登记手动参考文本输入与保存模块接口。
- `docs/task_status.md`：更新并行任务 1 状态和交接记录链接。

## 暴露接口

- `novel_rewrite_system.sources.ManualTextInput`
  - Pydantic 模型，禁止额外字段。
  - 字段：`source_id: str`、`title: str`、`text: str`。
- `novel_rewrite_system.sources.ManualSourceMetadata`
  - Pydantic 模型，禁止额外字段。
  - 字段：`source_id: str`、`title: str`、`created_at: datetime`、`input_type: Literal["manual"] = "manual"`。
- `save_manual_source(project_path: str | Path, manual_input: ManualTextInput, *, created_at: datetime | None = None) -> ManualSourceMetadata`
  - 保存正文到 `Path(project_path) / "sources" / f"{source_id}.txt"`。
  - 保存元数据到 `Path(project_path) / "sources" / f"{source_id}.json"`。
  - 返回 `ManualSourceMetadata`。

## 数据结构变化

- 新增 `ManualTextInput`，用于承载手动粘贴的参考文本输入。
- 新增 `ManualSourceMetadata`，用于承载保存后的来源元数据。
- 元数据字段包括 `source_id`、`title`、`created_at`、`input_type=manual`。
- 保存函数会对 `source_id`、`title`、`text` 做首尾空白处理；正文换行统一为 `\n`。
- `text` 为空或只包含空白字符时抛出 `ValueError("text 不能为空")`。
- `source_id` 为空、为 `.` / `..` 或包含 `/`、`\` 时抛出 `ValueError`。
- `title` 为空或只包含空白字符时抛出 `ValueError("title 不能为空")`。

## 配置变化

- 无配置变化。
- 未新增 API key、模型供应商、WebUI、SQLite 或全局路径配置。

## 测试命令

```bash
.venv/bin/python -m pytest -s
```

## 测试结果

- 已按 `docs/dev_environment.md` 使用项目 `.venv` 中的 Python 3.11.15 安装开发依赖并复测。
- `.venv/bin/python -m pytest` 默认捕获模式在当前 `/mnt/c` 挂载环境中触发 pytest 临时文件异常：`FileNotFoundError`。
- 使用同一 Python 3.11 虚拟环境关闭捕获运行 `.venv/bin/python -m pytest -s`，结果：`47 passed in 2.83s`。

## 未完成事项

- 未导出到 `novel_rewrite_system.__init__` 包入口；当前通过 `novel_rewrite_system.sources` 导入。
- 未实现网页抓取、文本切分、风格分析、模型调用、WebUI、SQLite、初稿生成或本地改写。
- 当前只保存单份手动来源的 `.txt` 与 `.json` 文件，不维护全局索引。

## 对其他模块的影响

- 对模型接口抽象层没有依赖，也未修改模型接口相关文件。
- 对文本切分模块没有运行时依赖；后续可由调用方读取保存后的 `.txt` 再传入 `split_text`。
- 对项目目录模块只有目录约定上的关系：保存目标是项目目录下的 `sources/`。
- 保存函数会在缺失时创建 `sources/` 目录，调用方无需提前手动创建该目录。

## 下一步建议

- 在接入项目流程时，由项目创建模块先创建项目目录，再调用 `save_manual_source` 保存参考正文。
- 后续如需把保存后的来源送入文本切分，应新增独立编排函数，保持保存模块不直接调用 `split_text`。
- 如需 UI 或 API 输入，应在外层处理表单和请求，不把 WebUI/FastAPI 逻辑放入 `sources.py`。
- 配置好 Python 3.11/3.12 虚拟环境并安装 `.[dev]` 后，重新运行 `python -m pytest`。
