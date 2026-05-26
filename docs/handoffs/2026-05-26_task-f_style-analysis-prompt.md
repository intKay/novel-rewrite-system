# 任务交接记录：Task F — 风格分析提示词构建器

## 任务名称

- Task F：风格分析提示词构建器

## 修改范围

- 新增 `src/novel_rewrite_system/analysis/` 子包及 `analysis/prompts/` 子包
- 新增 `src/novel_rewrite_system/analysis/prompts/style.py` 风格分析提示词构建器
- 新增 `tests/test_style_analysis_prompt.py` 单元测试
- **未修改**：文本切分、模型接口抽象层、错误类型、项目索引 JSON、文本处理小集成、docs/task_status.md、docs/interface_registry.md

## 新增/修改文件

- `src/novel_rewrite_system/analysis/__init__.py`（新增）
- `src/novel_rewrite_system/analysis/prompts/__init__.py`（新增）
- `src/novel_rewrite_system/analysis/prompts/style.py`（新增）
- `tests/test_style_analysis_prompt.py`（新增）

## 暴露接口

- `build_style_analysis_prompt(chunks: list[TextChunk], *, analysis_focus: list[str] | None = None, max_chunks: int | None = None) -> ModelRequest`
- 从 `novel_rewrite_system.analysis.prompts` 导入

## 输入

| 参数 | 类型 | 说明 |
|------|------|------|
| `chunks` | `list[TextChunk]` | 参考文本切片列表，必须非空 |
| `analysis_focus` | `list[str] \| None` | 可选分析关注点，默认覆盖全部九项 |
| `max_chunks` | `int \| None` | 可选限制参与分析的切片数量 |

## 输出

- `ModelRequest` 实例，包含：
  - `prompt`：中文风格分析提示词，含九项分析字段和参考文本片段
  - `system_prompt`：中文系统指令，禁止大段复述原文
  - `temperature=0.3`
  - `top_p=0.9`

## 数据结构变化

- 无新增数据结构；复用已有 `TextChunk` 和 `ModelRequest`

## 配置变化

- 无

## 测试命令

```bash
.venv/bin/python -m pytest -q -s tests/test_style_analysis_prompt.py
.venv/bin/python -m pytest -q -s
```

## 测试结果

- Task F 专测：15 passed
- 全量：94 passed in 2.16s

## 未完成事项

- 无。Task F 仅实现提示词构建，不包含真实模型调用。

## 对其他模块的影响

- 无破坏性影响。新增子包不影响已有模块导入路径。
- 后续风格分析调用方可导入 `build_style_analysis_prompt`，将返回的 `ModelRequest` 传给 `ModelClient.generate()` 进行真实分析。

## 下一步建议

- Task 4（模型调用封装）完成后，可将 `build_style_analysis_prompt` 输出与 DeepSeek/Ollama 客户端串联实现真实风格分析。
- 若后续需要将 prompt 中的九项分析字段改为可配置的白名单/黑名单，可在 `analysis_focus` 参数上扩展。
