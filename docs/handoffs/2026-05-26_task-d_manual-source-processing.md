# 任务交接记录：任务D 手动参考文本处理小集成

## 任务名称

- 任务D：手动参考文本 -> 清洗 -> 切分 -> 保存切片

## 修改范围

- 新增一个薄编排入口，串联已完成的手动保存、基础清洗和文本切分能力。
- 输出清洗后的正文、原有手动来源元数据和切片 JSON。
- 未实现网页抓取、模型调用、风格分析、初稿生成、WebUI、SQLite。
- 未修改项目索引 JSON，避免与并行任务 3 冲突。

## 新增/修改文件

- `src/novel_rewrite_system/source_processing.py`：新增集成入口和返回摘要模型。
- `src/novel_rewrite_system/__init__.py`：导出 `ManualSourceProcessingResult` 与 `process_manual_source`。
- `tests/test_source_processing.py`：新增集成测试。
- `docs/task_status.md`：登记本任务完成状态。
- `docs/interface_registry.md`：登记新入口、返回数据结构和切片 JSON 格式。
- `docs/handoffs/2026-05-26_task-d_manual-source-processing.md`：新增本交接记录。

## 暴露接口

- `ManualSourceProcessingResult`
- `process_manual_source(project_path, manual_input, *, chunk_chars=2000, created_at=None) -> ManualSourceProcessingResult`

## 数据结构变化

- 新增 `ManualSourceProcessingResult(source_id, cleaned_text_path, chunk_count, chunks_path)`。
- 新增 `sources/{source_id}.chunks.json` 文件格式：
  - 顶层字段：`source_id`, `title`, `chunk_count`, `chunks`
  - `chunks[]` 字段：`source_id`, `chapter_title`, `text`, `order`

## 配置变化

- 无。

## 测试命令

```bash
.venv/bin/python -m pytest -q -s tests/test_source_processing.py
.venv/bin/python -m pytest -s
```

## 测试结果

- 新增测试：`3 passed in 2.09s`
- 全量测试：`.venv/bin/python -m pytest -s`，`58 passed in 4.92s`
- 备注：按开发环境文档运行 `.venv/bin/python -m pytest` 时，pytest 默认捕获层在收集前触发 `FileNotFoundError`；关闭捕获后全量通过。

## 未完成事项

- 未接入项目索引 JSON。
- 未提供 WebUI 或 API 层。
- 未实现风格分析消费逻辑。

## 对其他模块的影响

- 风格分析或剧情分析模块后续可直接读取清洗正文路径或 `chunks_path`，无需重复清洗和切分。
- 现有 `save_manual_source`、`clean_text`、`split_text` 接口未改动。

## 下一步建议

- 后续风格分析模块优先消费 `sources/{source_id}.chunks.json`，按 `order` 保持上下文顺序。
- 如果需要批量处理多个来源，可在本入口外层新增批量编排，不要把批量逻辑塞进当前单来源函数。
