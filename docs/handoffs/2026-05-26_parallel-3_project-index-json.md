# 并行任务 3：项目索引 JSON 模块

## 任务名称

- 项目索引 JSON 模块

## 修改范围

- 在项目管理模块中新增轻量 JSON 项目索引能力。
- 约定项目根目录下的 `projects_index.json` 保存项目索引。
- 保持现有项目目录创建逻辑不重构。

## 新增/修改文件

- `src/novel_rewrite_system/projects.py`
- `src/novel_rewrite_system/__init__.py`
- `tests/test_projects.py`
- `docs/task_status.md`
- `docs/interface_registry.md`
- `docs/handoffs/2026-05-26_parallel-3_project-index-json.md`
- `src/novel_rewrite_system/source_processing.py`：仅修复既有导入时暴露的换行字符串语法错误，未改变其业务逻辑。

## 暴露接口

- `PROJECT_INDEX_FILENAME = "projects_index.json"`
- `ProjectIndexRecord(project_id: str, name: str, created_at: datetime = 当前 UTC 时间)`
- `add_project_record(project_root, record) -> ProjectIndexRecord`
- `list_project_records(project_root) -> list[ProjectIndexRecord]`
- `get_project_record(project_root, project_id) -> ProjectIndexRecord | None`

## 数据结构变化

- 新增 Pydantic 模型 `ProjectIndexRecord`。
- 索引文件结构：

```json
{
  "projects": [
    {
      "project_id": "novel-001",
      "name": "第一本小说",
      "created_at": "2026-05-26T12:00:00Z"
    }
  ]
}
```

## 配置变化

- 无新增配置。
- 调用方可继续使用 `Settings.app.project_root` 作为项目根目录。

## 测试命令

```bash
.venv/bin/python -m pytest -q -s tests/test_projects.py
.venv/bin/python -m pytest -q -s
```

## 测试结果

- `tests/test_projects.py`：`15 passed in 3.02s`
- 全量测试：`58 passed in 5.96s`

## 未完成事项

- 无。

## 对其他模块的影响

- 不依赖模型接口、文本清洗、网页抓取或 WebUI。
- 不引入 SQLite。
- 不创建项目目录，也不重构现有 `create_project_directories` 行为。

## 下一步建议

- 后续项目创建流程可先调用 `create_project_directories`，再调用 `add_project_record` 登记项目。
- WebUI 或 API 层需要展示项目列表时，可直接调用 `list_project_records`。
