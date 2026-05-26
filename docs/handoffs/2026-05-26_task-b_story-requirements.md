# Task B 任务交接记录：用户需求结构化数据模型

## 任务名称

- Task B：用户需求结构化数据模型

## 修改范围

- 新增用户自由文本需求的 Pydantic 数据结构，用于承载后续故事生成、改写和模型解析前后的结构化需求。
- 新增 `from_text` 占位解析入口，第一版只保存原始用户文本到 `raw_text`。
- 新增对应单元测试，验证部分字段为空、占位入口行为、列表默认值隔离和额外字段拒绝。
- 未接入 DeepSeek 或任何真实模型解析。
- 未新增 WebUI 表单。
- 未引入数据库或持久化逻辑。

## 新增/修改文件

- `src/novel_rewrite_system/requirements.py`：新增 `StoryRequirement` 数据模型和 `from_text` 类方法。
- `src/novel_rewrite_system/__init__.py`：导出 `StoryRequirement`。
- `tests/test_requirements.py`：新增 Task B 单元测试。
- `docs/handoffs/2026-05-26_task-b_story-requirements.md`：本交接记录。
- `docs/interface_registry.md`：登记用户需求结构化模块真实接口。
- `docs/task_status.md`：回填 Task B 状态、接口、测试命令和交接记录链接。

## 暴露接口

- `novel_rewrite_system.requirements.StoryRequirement`
- `StoryRequirement.from_text(raw_text: str) -> StoryRequirement`
- 包入口已导出：`from novel_rewrite_system import StoryRequirement`

## 数据结构变化

- 新增 Pydantic 模型 `StoryRequirement`，禁止额外字段。
- 字段列表：
  - `raw_text: str = ""`
  - `theme: str | None = None`
  - `worldview: str | None = None`
  - `protagonist: str | None = None`
  - `supporting_characters: str | None = None`
  - `character_relationships: str | None = None`
  - `plot_direction: str | None = None`
  - `style_preferences: str | None = None`
  - `forbidden_content: list[str] = []`
  - `required_plot_points: list[str] = []`
  - `ending_preference: str | None = None`
- `forbidden_content` 和 `required_plot_points` 使用 `default_factory=list`，实例之间不共享列表。
- 当前 `from_text` 只保存 `raw_text`，不会抽取主题、人物、情节、禁忌内容或结局倾向。

## 配置变化

- 无配置变化。
- 未新增 API key、模型供应商、WebUI 或数据库配置。

## 测试命令

```bash
python3 -m pytest -q -s tests/test_requirements.py
python3 -m pytest -q -s
```

## 测试结果

- `python3 -m pytest -q -s tests/test_requirements.py`：`4 passed in 0.37s`。
- `python3 -m pytest -q -s`：`37 passed in 2.59s`。
- 当前环境普通沙箱命令会因缺少 `bubblewrap` 无法启动；本次验证使用提权方式运行命令。

## 未完成事项

- 未实现 DeepSeek 结构化解析。
- 未实现基于规则或模型的字段抽取。
- 未实现 WebUI 表单输入。
- 未实现数据库存储。
- 未实现需求对象与生成流程、模型接口或项目文件的集成。

## 对其他模块的影响

- `StoryRequirement` 可作为后续风格分析、剧情规划、初稿生成和本地改写模块的用户需求输入对象。
- 当前实现不调用模型、不访问网络、不读写数据库，对现有项目目录、文本切分、配置读取和模型接口模块没有运行时依赖。
- 包入口导出 `StoryRequirement` 后，其他模块可以从 `novel_rewrite_system` 或 `novel_rewrite_system.requirements` 导入。

## 下一步建议

- 后续接入模型解析时，在 `from_text` 内部或新建独立解析服务中填充结构化字段，避免让 Pydantic 模型直接承担外部 API 调用职责。
- 模型解析结果进入 `StoryRequirement` 前应做字段白名单校验，防止引入未登记字段。
- 对 `forbidden_content` 和 `required_plot_points` 保持列表语义，不要把多个条目拼接成一个字符串。
- 若接入 DeepSeek，应新增独立客户端或解析函数，并用 mock 测试覆盖成功、空结果、格式错误和字段缺失场景。
