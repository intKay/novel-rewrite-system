# 中文小说生成与本地改写系统

当前项目包含小说改写系统的本地基础模块：配置读取、项目目录初始化、参考文本保存、文本切分、用户需求结构化模型，以及模型调用抽象层。

## 已有模块

- 配置读取：从 YAML 文件读取系统配置，并使用 Pydantic 校验结构。
- 项目目录初始化：创建 `config/`、`sources/`、`analysis/`、`drafts/`、`revisions/`、`final/`、`logs/` 等标准目录。
- 手动参考文本输入与保存：保存用户粘贴的参考小说正文和元数据。
- 文本切分：将长文本切分为后续分析和改写可使用的 `TextChunk`。
- 用户需求结构化模型：提供 `StoryRequirement` 数据结构和 `from_text` 占位入口。
- 模型接口抽象层：提供 `ModelClient` 协议、请求/响应模型和测试用 `FakeModelClient`。

## 手动参考文本输入与保存

`novel_rewrite_system.sources` 用于保存用户手动粘贴的参考小说文本。它只负责把正文和简单元数据写入项目目录的 `sources/` 下，不负责网页抓取、文本切分或模型调用。

输入数据结构：

- `ManualTextInput`：包含 `source_id`、`title`、`text`
- `ManualSourceMetadata`：包含 `source_id`、`title`、`created_at`、`input_type`
- `save_manual_source(project_path, manual_input, *, created_at=None)`：保存正文和元数据，返回 `ManualSourceMetadata`

保存后文件结构：

```text
project/
  sources/
    {source_id}.txt
    {source_id}.json
```

其中 `{source_id}.txt` 保存正文文本，`{source_id}.json` 保存元数据，元数据中的 `input_type=manual`。

最小示例：

```python
from novel_rewrite_system.sources import ManualTextInput, save_manual_source

manual_input = ManualTextInput(
    source_id="source-001",
    title="参考小说",
    text="第一章\n正文内容。",
)

metadata = save_manual_source("projects/demo", manual_input)
```

保存时会去除标题和正文首尾空白，并将换行统一为 `\n`。如果 `source_id` 为空、为 `.` / `..`、包含路径分隔符，或 `title` / `text` 为空，`save_manual_source` 会抛出 `ValueError`。

## 项目文档

- [开发环境基线](docs/dev_environment.md)
- [接口与数据结构登记](docs/interface_registry.md)
- [任务状态](docs/task_status.md)
- [任务交接模板](docs/task_handoff_template.md)

## 运行测试

推荐使用 Python 3.11 或 3.12。完整环境说明见 [docs/dev_environment.md](docs/dev_environment.md)。

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
python -m pip install -e .[dev]
python -m pytest
```
