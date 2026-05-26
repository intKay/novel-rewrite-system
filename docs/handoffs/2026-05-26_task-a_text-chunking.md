# Task A 文本切分模块交接记录

## 任务名称

- Task A：文本切分模块设计与实现

## 修改范围

- 新增纯函数文本切分模块，仅处理内存中的原始文本。
- 实现章节优先、章节过长按段落、段落过长按句子的切分策略。
- 未接入 FastAPI、数据库、模型接口、WebUI、网页抓取或存储逻辑。

## 新增/修改文件

- `src/novel_rewrite_system/text_chunks.py`：新增 `TextChunk` 数据结构与 `split_text` 切分函数。
- `src/novel_rewrite_system/__init__.py`：导出 `TextChunk` 与 `split_text`。
- `tests/test_text_chunks.py`：新增文本切分单元测试。

## 暴露接口

- `TextChunk`
  - 冻结 dataclass。
  - 字段：`source_id: str`、`chapter_title: str | None`、`text: str`、`order: int`。
- `split_text(source_id: str, raw_text: str, *, chapter_title: str | None = None, chunk_chars: int = 2000) -> list[TextChunk]`
  - 输入 source_id、原始文本、可选章节标题和 chunk 字符数配置。
  - 输出按 `order` 从 1 开始排列的 `TextChunk` 列表。

## 数据结构变化

- 新增 `TextChunk`，用于承载文本片段和来源元数据。
- 每个 chunk 保留 `source_id`、`chapter_title`、`text`、`order`。

## 配置变化

- 无全局配置文件变化。
- `chunk_chars` 是 `split_text` 的函数参数，默认值为 `2000`。

## 测试命令

```bash
python3 -m pytest -s tests
```

## 测试结果

- 已运行，结果：`37 passed`。

## 未完成事项

- 未实现网页抓取、模型调用、数据库存储或 WebUI，符合 Task A 边界。
- 章节标题识别目前覆盖常见中文章节格式、`Chapter N`、`CHAPTER N`、序章、楔子、尾声、后记、番外；如后续接入真实小说来源，可按样本扩展识别规则。

## 对其他模块的影响

- 后续风格分析、剧情分析、模型改写模块可以直接消费 `list[TextChunk]`。
- 当前模块不依赖其他业务模块，不产生存储副作用。
- `split_text` 会校验 `source_id` 非空、`chunk_chars > 0`；调用方需要处理 `ValueError`。

## 下一步建议

- 接入参考文本输入模块时，将保存后的原始文本传入 `split_text`，再把结果交给分析或改写流程。
- 若后续出现更多章节标题格式，优先补充单元测试，再扩展标题识别规则。
- 在模型调用模块使用前，根据具体模型上下文窗口调整 `chunk_chars` 默认策略。
