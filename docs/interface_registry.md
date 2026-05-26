# 接口与数据结构登记

本文件记录模块之间共享的接口、数据结构和调用约定。新增或修改共享接口时，应同步更新本文件；如果暂时不清楚具体函数名，不要猜测，先写“待从实现中补充”。

| 模块 | 主要职责 | 暴露接口 | 输入 | 输出 | 数据结构 | 配置依赖 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 配置读取模块 | 读取 YAML 配置并校验系统配置结构 | `load_settings(config_path)`；`AppConfig`；`CloudModelConfig`；`LocalModelConfig`；`GenerationConfig`；`Settings` | `config_path: str | Path`，YAML 顶层为映射对象 | `Settings`；非映射 YAML 抛出 `ValueError`；字段校验失败抛出 Pydantic `ValidationError` | `AppConfig(project_root)`；`CloudModelConfig(provider, model, api_key_env, base_url)`；`LocalModelConfig(provider, model, endpoint)`；`GenerationConfig(temperature, max_tokens)`；`Settings(app, cloud_model, local_model, generation)` | YAML 配置包含 `app`、`cloud_model`、`local_model`、`generation` 四段 | Phase 1 已登记；模型供应商只作为配置字段，不写死在业务逻辑中 |
| 项目目录创建模块 | 根据项目根目录和项目 ID 创建标准项目目录 | `create_project_directories(project_root, project_id)`；`PROJECT_SUBDIRECTORIES` | `project_root: str | Path`；`project_id: str` | 返回项目目录 `Path`，并创建标准子目录 | `PROJECT_SUBDIRECTORIES = ("config", "sources", "analysis", "drafts", "revisions", "final", "logs")` | 不依赖配置对象；调用方可使用 `Settings.app.project_root` 作为项目根目录 | `project_id` 不能为空，不能为 `.` 或 `..`，不能包含 `/` 或 `\` |
| 文本切分模块 | 将长文本切分为适合后续分析和改写的片段 | `TextChunk`; `split_text(source_id: str, raw_text: str, *, chapter_title: str \| None = None, chunk_chars: int = 2000) -> list[TextChunk]` | `source_id` 非空字符串；`raw_text` 原始文本；可选 `chapter_title`；`chunk_chars > 0` | `list[TextChunk]`，空白文本返回空列表 | `TextChunk(source_id: str, chapter_title: str \| None, text: str, order: int)` | 无全局配置依赖；`chunk_chars` 为函数参数 | 优先按章节切分；章节过长按段落组合；单段过长按句子组合；仅单句超过限制时硬切；每个 chunk 保留 `source_id`、`chapter_title`、`order` |
| 用户需求结构化模块 | 将用户创作要求整理为结构化数据 | `StoryRequirement`; `StoryRequirement.from_text(raw_text: str) -> StoryRequirement` | 用户自由文本需求 `raw_text: str`；也可直接构造部分字段 | `StoryRequirement` 实例 | Pydantic 模型 `StoryRequirement`；字段：`raw_text`, `theme`, `worldview`, `protagonist`, `supporting_characters`, `character_relationships`, `plot_direction`, `style_preferences`, `forbidden_content`, `required_plot_points`, `ending_preference` | 无 | 当前 `from_text` 只保存 `raw_text`，不调用模型、不抽取字段；后续接入模型解析时需保持字段白名单、处理空/缺失/格式错误结果，并保持禁止内容和必须情节为列表语义 |
| 模型接口抽象层 | 统一云端模型和本地模型调用方式，避免业务逻辑写死供应商 | `ModelRequest`; `ModelResponse`; `ModelClient.generate(request: ModelRequest) -> ModelResponse`; `FakeModelClient.generate(request: ModelRequest) -> ModelResponse` | `ModelRequest(prompt, system_prompt=None, temperature=None, top_p=None, max_tokens=None, metadata=None)` | `ModelResponse(text, provider, model, finish_reason=None, usage=None, raw=None)` | `ModelRequest`、`ModelResponse` 为 Pydantic 模型；`ModelClient` 为 Protocol；`FakeModelClient` 可传入固定 `text/provider/model` 并记录 `last_request` | 无；不读取 API key；不访问网络 | FakeModelClient 用于后续业务单元测试：业务函数依赖 `ModelClient`，测试时注入 fake 并断言返回文本和 `last_request` |
| 手动参考文本输入模块 | 保存用户手动粘贴的参考小说正文及元数据 | `ManualTextInput`; `ManualSourceMetadata`; `save_manual_source(project_path, manual_input, *, created_at=None) -> ManualSourceMetadata` | `project_path: str \| Path`；`manual_input.source_id/title/text`；可选 `created_at` | 创建 `sources/{source_id}.txt` 与 `sources/{source_id}.json`，并返回元数据 | `ManualTextInput(source_id, title, text)`；`ManualSourceMetadata(source_id, title, created_at, input_type="manual")` | 无 | 只负责保存手动输入，不抓取网页、不切分文本、不调用模型；`source_id` 不能为空、不能为 `.`/`..`、不能包含路径分隔符；`title` 和 `text` 不能为空；正文换行统一为 `\n` |

## 更新规则

- 新增共享接口时，补充模块、输入、输出和测试入口。
- 修改已有接口时，同步说明影响范围，并更新 `docs/task_status.md` 中相关任务。
- 不确定的实现细节保持“待从实现中补充”，由负责该模块的会话核对后填写。
