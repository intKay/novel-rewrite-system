# 任务交接记录：Task L — 初稿生成服务

## 任务名称

- Task L：初稿生成服务

## 修改范围

- 新增 `src/novel_rewrite_system/generation/service.py` 初稿生成服务
- 更新 `src/novel_rewrite_system/generation/__init__.py` 导出新接口
- 更新 `src/novel_rewrite_system/__init__.py` 导出 `DraftGenerationResult` 和 `generate_draft`
- 新增 `tests/test_draft_generation_service.py` 单元测试
- 更新 `docs/task_status.md` 和 `docs/interface_registry.md`
- **未修改**：Task G 提示词构建器、Task C 模型接口抽象层、Task J DeepSeek 客户端、Task K 风格分析服务、错误类型模块、项目索引 JSON、文本处理集成

## 新增/修改文件

| 文件 | 操作 |
|------|------|
| `src/novel_rewrite_system/generation/service.py` | 新增 |
| `src/novel_rewrite_system/generation/__init__.py` | 修改（新增导出） |
| `src/novel_rewrite_system/__init__.py` | 修改（新增导出） |
| `tests/test_draft_generation_service.py` | 新增 |
| `docs/task_status.md` | 修改（新增 Task L 行） |
| `docs/interface_registry.md` | 修改（新增初稿生成服务行） |

## 暴露接口

- `DraftGenerationResult(draft_text: str)` — frozen dataclass
- `generate_draft(style_report: str, requirement: StoryRequirement, model_client: ModelClient, *, chapter_plan: str | None = None, target_word_count: int | None = None, chapter_count: int | None = None, project_path: str | Path | None = None) -> DraftGenerationResult`
- 导入路径：`from novel_rewrite_system.generation import DraftGenerationResult, generate_draft`

## 数据流

```
style_report (str)
requirement (StoryRequirement)
    ↓
generate_draft()
    ↓
build_draft_generation_prompt(style_report, requirement, ...) → ModelRequest
    ↓
model_client.generate(request) → ModelResponse
    ↓
DraftGenerationResult(draft_text=response.text)
    ↓ (可选)
{project_path}/drafts/draft.md
```

## 数据结构变化

- 新增 `DraftGenerationResult`（frozen dataclass），字段为 `draft_text`（初稿文本）
- 初稿保存路径：`{project_path}/drafts/draft.md`

## 配置变化

- 无

## 测试命令

```bash
.venv/bin/python -m pytest -q -s tests/test_draft_generation_service.py
.venv/bin/python -m pytest -q -s
```

## 测试结果

- Task L 专测：17 passed in 1.96s
- 全量：143 passed in 2.50s
- 所有测试使用 FakeModelClient，零真实网络请求

## 未完成事项

- 无。Task L 只实现 prompt 构建器与模型客户端的串联服务，不包含真实模型调用。

## 对其他模块的影响

- 无破坏性影响。新增 `generation/service.py` 不影响已有模块导入路径。
- 上游依赖：Task G（`build_draft_generation_prompt`）、Task C（`ModelClient`/`FakeModelClient`）、Task E（`EmptyTextError`/`ProjectError`）、Task B（`StoryRequirement`）。
- 不依赖 Task K（风格分析服务），两者可并行独立开发和测试。

## 下一步建议

- 可将 Task K（风格分析服务）和 Task L（初稿生成服务）串联：先 `analyze_style()` 获取风格报告 → 再 `generate_draft()` 生成初稿，形成完整的端到端生成闭环。
- 建议先进行 code review，再开始端到端生成闭环开发。
