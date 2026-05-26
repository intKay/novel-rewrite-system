# 任务交接记录：Task K — 风格分析服务

## 任务名称

- Task K：风格分析服务

## 修改范围

- 新增 `src/novel_rewrite_system/analysis/service.py` 风格分析服务
- 更新 `src/novel_rewrite_system/analysis/__init__.py` 导出新接口
- 更新 `src/novel_rewrite_system/__init__.py` 导出 `StyleAnalysisResult` 和 `analyze_style`
- 新增 `tests/test_style_analysis_service.py` 单元测试
- 更新 `docs/task_status.md` 和 `docs/interface_registry.md`
- **未修改**：Task F 提示词构建器、Task C 模型接口抽象层、Task J DeepSeek 客户端、错误类型模块、项目索引 JSON、文本处理集成

## 新增/修改文件

| 文件 | 操作 |
|------|------|
| `src/novel_rewrite_system/analysis/service.py` | 新增 |
| `src/novel_rewrite_system/analysis/__init__.py` | 修改（新增导出） |
| `src/novel_rewrite_system/__init__.py` | 修改（新增导出） |
| `tests/test_style_analysis_service.py` | 新增 |
| `docs/task_status.md` | 修改（新增 Task K 行） |
| `docs/interface_registry.md` | 修改（新增风格分析服务行） |

## 暴露接口

- `StyleAnalysisResult(report: str, source_count: int, chunk_count: int)` — frozen dataclass
- `analyze_style(chunks: list[TextChunk], model_client: ModelClient, *, analysis_focus: list[str] | None = None, max_chunks: int | None = None, project_path: str | Path | None = None) -> StyleAnalysisResult`
- 导入路径：`from novel_rewrite_system.analysis import StyleAnalysisResult, analyze_style`

## 数据结构变化

- 新增 `StyleAnalysisResult`（frozen dataclass），字段为 `report`（分析报告文本）、`source_count`（唯一来源数）、`chunk_count`（实际分析切片数）
- 报告保存路径：`{project_path}/analysis/style_analysis_report.md`

## 配置变化

- 无

## 测试命令

```bash
.venv/bin/python -m pytest -q -s tests/test_style_analysis_service.py
.venv/bin/python -m pytest -q -s
```

## 测试结果

- Task K 专测：14 passed in 1.97s
- 全量：126 passed in 2.70s
- 所有测试使用 FakeModelClient，零真实网络请求

## 未完成事项

- 无。Task K 只实现 prompt 构建器与模型客户端的串联服务，不包含真实模型调用。

## 对其他模块的影响

- 无破坏性影响。新增 `analysis/service.py` 不影响已有模块导入路径。
- 上游依赖：Task F（`build_style_analysis_prompt`）、Task C（`ModelClient`/`FakeModelClient`）、Task E（`EmptyTextError`/`ProjectError`）。
- 后续风格分析调用方可直接使用 `analyze_style()` 传入真实/假模型客户端。

## 下一步建议

- 本模块完成后，可在初稿生成服务（Task L）中复用此模式：串联 Task G 提示词构建器与 `ModelClient`。
- 建议先进行 code review，再开始初稿生成服务。
