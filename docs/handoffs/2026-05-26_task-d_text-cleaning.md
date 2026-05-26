# Task D 基础文本清洗模块交接记录

## 任务名称

- Task D：基础文本清洗模块

## 修改范围

- 新增纯函数文本清洗模块，仅处理内存中的字符串。
- 实现首尾空白去除、Windows/Unix/混合换行统一、连续空白段落压缩、空白段落删除。
- 保留中文章节标题和基本段落结构。
- 空文本或清洗后为空时抛出明确 `ValueError`。
- 未实现网页抓取、HTML 解析、DeepSeek/Ollama 调用、WebUI、SQLite 或端到端流程。

## 新增/修改文件

- `src/novel_rewrite_system/text_cleaning.py`：新增 `clean_text` 文本清洗函数。
- `src/novel_rewrite_system/__init__.py`：导出 `clean_text`。
- `tests/test_text_cleaning.py`：新增文本清洗单元测试。
- `docs/task_status.md`：登记 Task D 状态、接口、测试命令和交接记录。
- `docs/interface_registry.md`：登记基础文本清洗模块接口。
- `docs/handoffs/2026-05-26_task-d_text-cleaning.md`：本交接记录。

## 暴露接口

- `clean_text(raw_text: str) -> str`
  - 输入原始字符串。
  - 输出清洗后的字符串。
  - 空文本或清洗后为空时抛出 `ValueError("text 不能为空")`。

## 数据结构变化

- 无新增数据结构。

## 配置变化

- 无配置变化。

## 测试命令

```bash
python3 -m pytest -q -s tests/test_text_cleaning.py
python3 -m pytest -q -s
```

## 测试结果

- 定向测试：`10 passed in 0.45s`。
- 全量测试：`47 passed in 1.81s`。

## 未完成事项

- 未将 `clean_text` 接入手动文本保存模块，避免改变已完成模块行为。
- 未将 `clean_text` 接入文本切分模块，避免改变已完成模块逻辑。
- 后续网页抓取或手动输入流程需要使用统一清洗策略时，可在调用边界显式调用该函数。

## 对其他模块的影响

- 对已完成模块无行为影响。
- 仅在包入口新增 `clean_text` 导出。
- 文本切分模块、手动文本保存模块、模型接口模块均未修改逻辑。

## 下一步建议

- 后续实现网页抓取文本入库前，先调用 `clean_text`，再进入切分或保存流程。
- 如需让手动参考文本保存复用该清洗函数，应单独开小任务并补充保存模块回归测试。
