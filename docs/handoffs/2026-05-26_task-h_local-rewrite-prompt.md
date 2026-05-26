# 任务交接记录：Task H — 本地改写提示词构建器

## 任务名称

- Task H：本地改写提示词构建器

## 修改范围

- 新增 `src/novel_rewrite_system/rewrite/` 子包及 `rewrite/prompts/` 子包
- 新增 `src/novel_rewrite_system/rewrite/prompts/local.py` 本地改写提示词构建器
- 新增 `tests/test_local_rewrite_prompt.py` 单元测试
- 更新 `docs/task_status.md` 和 `docs/interface_registry.md`
- **未修改**：模型接口抽象层、DeepSeek 客户端、Task K/L/F/G 文件、错误类型模块、项目索引 JSON、文本处理集成

## 新增/修改文件

| 文件 | 操作 |
|------|------|
| `src/novel_rewrite_system/rewrite/__init__.py` | 新增 |
| `src/novel_rewrite_system/rewrite/prompts/__init__.py` | 新增 |
| `src/novel_rewrite_system/rewrite/prompts/local.py` | 新增 |
| `tests/test_local_rewrite_prompt.py` | 新增 |
| `docs/task_status.md` | 修改（新增 Task H 行） |
| `docs/interface_registry.md` | 修改（新增本地改写提示词构建器行） |

## 暴露接口

- `build_local_rewrite_prompt(global_summary: str, character_sheet: str, chapter_summary: str, current_fragment: str, rewrite_instruction: str, must_keep: list[str], forbidden_changes: list[str], *, temperature: float | None = 0.8, top_p: float | None = 0.9, max_tokens: int | None = None) -> ModelRequest`
- 导入路径：`from novel_rewrite_system.rewrite.prompts import build_local_rewrite_prompt`

## 输入

| 参数 | 类型 | 说明 |
|------|------|------|
| `global_summary` | `str` | 全局设定摘要，必须非空 |
| `character_sheet` | `str` | 角色表，必须非空 |
| `chapter_summary` | `str` | 当前章节摘要，必须非空 |
| `current_fragment` | `str` | 当前待改写片段，必须非空 |
| `rewrite_instruction` | `str` | 用户改写要求，必须非空 |
| `must_keep` | `list[str]` | 必须保留的剧情点，可为空 |
| `forbidden_changes` | `list[str]` | 禁止改变的事实，可为空 |
| `temperature` | `float \| None` | 可选，默认 0.8 |
| `top_p` | `float \| None` | 可选，默认 0.9 |
| `max_tokens` | `int \| None` | 可选，默认 None |

## 输出

- `ModelRequest` 实例，包含：
  - `system_prompt`：中文改写编辑指令，要求只改当前片段、保留核心剧情、按指令替换角色/设定、保持称呼一致、附修改说明
  - `prompt`：包含全局设定摘要、角色表、章节摘要、待改写片段、改写要求、must_keep（空则显示"无特殊要求"）、forbidden_changes（空则显示"无特殊限制"）
  - `temperature=0.8`（默认）、`top_p=0.9`（默认）、`max_tokens=None`（默认）

## 数据结构变化

- 无新增数据结构；复用已有 `ModelRequest`

## 配置变化

- 无

## 测试命令

```bash
.venv/bin/python -m pytest -q -s tests/test_local_rewrite_prompt.py
.venv/bin/python -m pytest -q -s
```

## 测试结果

- Task H 专测：27 passed in 2.67s
- 全量：170 passed in 2.70s
- 所有测试不访问网络、不进行真实模型调用

## 未完成事项

- 无。Task H 仅实现提示词构建，不包含模型调用。
- 未实现 OllamaClient、本地改写服务。

## 对其他模块的影响

- 无破坏性影响。新增 `rewrite/` 子包不影响已有模块导入路径。
- 上游依赖：仅依赖 `ModelRequest`（Task C），不依赖 Task K 或 Task L。
- 后续本地改写服务可导入 `build_local_rewrite_prompt`，将返回的 `ModelRequest` 传给 OllamaClient 或任意 `ModelClient` 实现。

## 下一步建议

- 实现 OllamaClient（实现 `ModelClient` 协议）后，可串联：`build_local_rewrite_prompt()` → `ollama_client.generate()` → 获取改写文本。
- 建议先进行 code review，再开始 OllamaClient 或本地改写服务开发。
