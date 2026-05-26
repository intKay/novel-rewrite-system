# 任务交接记录：5.3 — 本地改写服务

## 任务名称

- 5.3：本地改写服务

## 修改范围

- 新增 `src/novel_rewrite_system/rewrite/service.py` 本地改写服务
- 更新 `src/novel_rewrite_system/rewrite/__init__.py` 导出新接口
- 更新 `src/novel_rewrite_system/__init__.py` 导出 `LocalRewriteResult` 和 `rewrite_locally`
- 新增 `tests/test_local_rewrite_service.py` 单元测试
- 更新 `docs/task_status.md` 和 `docs/interface_registry.md`
- **未修改**：3.4 本地改写提示词构建器、4.3 Ollama 客户端、5.1 风格分析服务、5.2 初稿生成服务、错误类型模块、项目索引 JSON、文本处理集成

## 新增/修改文件

| 文件 | 操作 |
|------|------|
| `src/novel_rewrite_system/rewrite/service.py` | 新增 |
| `src/novel_rewrite_system/rewrite/__init__.py` | 修改（新增导出） |
| `src/novel_rewrite_system/__init__.py` | 修改（新增导出） |
| `tests/test_local_rewrite_service.py` | 新增 |
| `docs/task_status.md` | 修改（新增 5.3 行） |
| `docs/interface_registry.md` | 修改（新增本地改写服务行） |

## 暴露接口

- `LocalRewriteResult(rewritten_text: str)` — frozen dataclass
- `rewrite_locally(global_summary: str, character_sheet: str, chapter_summary: str, current_fragment: str, rewrite_instruction: str, must_keep: list[str], forbidden_changes: list[str], model_client: ModelClient, *, temperature: float | None = None, top_p: float | None = None, max_tokens: int | None = None, project_path: str | Path | None = None) -> LocalRewriteResult`
- 导入路径：`from novel_rewrite_system.rewrite import LocalRewriteResult, rewrite_locally`

## 数据流

```
global_summary + character_sheet + chapter_summary
+ current_fragment + rewrite_instruction
+ must_keep + forbidden_changes
    ↓
rewrite_locally()
    ↓
build_local_rewrite_prompt(...) → ModelRequest
    ↓
model_client.generate(request) → ModelResponse
    ↓
LocalRewriteResult(rewritten_text=response.text)
    ↓ (可选)
{project_path}/revisions/rewritten.md
```

## 数据结构变化

- 新增 `LocalRewriteResult`（frozen dataclass），字段为 `rewritten_text`（改写后的文本，含模型附带的修改说明）
- 改写稿保存路径：`{project_path}/revisions/rewritten.md`

## 配置变化

- 无

## 测试命令

```bash
.venv/bin/python -m pytest -q -s tests/test_local_rewrite_service.py
.venv/bin/python -m pytest -q -s
```

## 测试结果

- 5.3 专测：19 passed in 2.21s
- 全量：209 passed in 3.25s
- 所有测试使用 FakeModelClient，零真实网络请求

## 未完成事项

- 无。5.3 只实现 prompt 构建器与模型客户端的串联服务，不包含真实模型调用。

## 对其他模块的影响

- 无破坏性影响。新增 `rewrite/service.py` 不影响已有模块导入路径。
- 上游依赖：3.4（`build_local_rewrite_prompt`）、4.3/Task C（`ModelClient`/`FakeModelClient`）、Task E（`EmptyTextError`/`ProjectError`）。

## 下一步建议

- 可将 5.1（风格分析）+ 5.2（初稿生成）+ 5.3（本地改写）串联为端到端闭环。
- 建议先进行 code review，再开始 5.4 最小端到端闭环。
