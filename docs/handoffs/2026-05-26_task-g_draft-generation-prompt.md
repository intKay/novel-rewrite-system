# 任务交接记录：Task G — 初稿生成提示词构建器

## 任务名称

- Task G：初稿生成提示词构建器

## 修改范围

- 新增 `src/novel_rewrite_system/generation/` 子包及 `generation/prompts/` 子包
- 新增 `src/novel_rewrite_system/generation/prompts/draft.py` 初稿生成提示词构建器
- 新增 `tests/test_draft_generation_prompt.py` 单元测试
- **未修改**：用户需求结构化模块、模型接口抽象层、错误类型、项目索引 JSON、文本处理小集成、docs/task_status.md、docs/interface_registry.md

## 新增/修改文件

- `src/novel_rewrite_system/generation/__init__.py`（新增）
- `src/novel_rewrite_system/generation/prompts/__init__.py`（新增）
- `src/novel_rewrite_system/generation/prompts/draft.py`（新增）
- `tests/test_draft_generation_prompt.py`（新增）

## 暴露接口

- `build_draft_generation_prompt(style_report: str, requirement: StoryRequirement, *, chapter_plan: str | None = None, target_word_count: int | None = None, chapter_count: int | None = None) -> ModelRequest`
- 从 `novel_rewrite_system.generation.prompts` 导入

## 输入

| 参数 | 类型 | 说明 |
|------|------|------|
| `style_report` | `str` | 风格分析报告文本，必须非空 |
| `requirement` | `StoryRequirement` | 用户需求结构化对象 |
| `chapter_plan` | `str \| None` | 可选章节计划描述 |
| `target_word_count` | `int \| None` | 可选目标总字数 |
| `chapter_count` | `int \| None` | 可选目标章节数 |

## 输出

- `ModelRequest` 实例，包含：
  - `prompt`：中文原创小说创作提示词，含风格报告、用户需求明细（主题/主角/禁止内容/必须情节等）、章节计划、创作要求
  - `system_prompt`：中文系统指令，要求完全原创、角色一致、剧情推进
  - `temperature=0.8`
  - `top_p=0.9`

## 数据结构变化

- 无新增数据结构；复用已有 `StoryRequirement` 和 `ModelRequest`

## 配置变化

- 无

## 测试命令

```bash
.venv/bin/python -m pytest -q -s tests/test_draft_generation_prompt.py
.venv/bin/python -m pytest -q -s
```

## 测试结果

- Task G 专测：16 passed
- 全量：94 passed in 2.16s

## 未完成事项

- 无。Task G 仅实现提示词构建，不包含真实模型调用。

## 对其他模块的影响

- 无破坏性影响。新增子包不影响已有模块导入路径。
- 后续初稿生成方可导入 `build_draft_generation_prompt`，将风格分析结果和用户需求传入，将返回的 `ModelRequest` 传给 `ModelClient.generate()` 进行真实生成。

## 下一步建议

- Task 4（模型调用封装）完成后，可将 `build_draft_generation_prompt` 与 `build_style_analysis_prompt` 串联：先分析风格 → 再生成初稿。
- `StoryRequirement.from_text()` 目前只保存原始文本，后续接入模型解析后可自动填充结构化字段，从而让 prompt 中的需求明细更完整。
