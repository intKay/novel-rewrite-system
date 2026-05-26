# Task C 任务交接记录：模型接口抽象层

## 任务名称

- Task C：模型接口抽象层

## 修改范围

- 新增统一模型调用接口抽象，供后续云端模型、本地模型和业务流程共同依赖。
- 新增测试用 `FakeModelClient`，用于不接入真实模型服务时验证业务层调用路径。
- 未实现 DeepSeek、Ollama 或其他真实模型供应商客户端。
- 未新增网络调用、API key 读取或生成业务流程。

## 新增/修改文件

- `src/novel_rewrite_system/models.py`：新增模型请求、响应、客户端协议和假模型客户端。
- `src/novel_rewrite_system/__init__.py`：导出模型接口相关类型。
- `tests/test_models.py`：新增模型接口抽象层单元测试。
- `docs/handoffs/2026-05-26_task-c_model-interface.md`：本交接记录。
- `docs/interface_registry.md`：登记模型接口抽象层真实接口。
- `docs/task_status.md`：回填 Task C 状态、接口、测试命令和交接记录链接。

## 暴露接口

- `novel_rewrite_system.models.ModelRequest`
- `novel_rewrite_system.models.ModelResponse`
- `novel_rewrite_system.models.ModelClient`
- `novel_rewrite_system.models.FakeModelClient`
- `ModelClient.generate(request: ModelRequest) -> ModelResponse`
- `FakeModelClient.generate(request: ModelRequest) -> ModelResponse`

## 数据结构变化

- 新增 `ModelRequest`，字段为：
  - `prompt: str`
  - `system_prompt: str | None`
  - `temperature: float | None`
  - `top_p: float | None`
  - `max_tokens: int | None`
  - `metadata: dict[str, Any] | None`
- 新增 `ModelResponse`，字段为：
  - `text: str`
  - `provider: str`
  - `model: str`
  - `finish_reason: str | None`
  - `usage: dict[str, Any] | None`
  - `raw: dict[str, Any] | None`
- `ModelRequest` 和 `ModelResponse` 均使用 Pydantic，禁止额外字段。
- `FakeModelClient` 记录 `last_request: ModelRequest | None`，便于测试断言业务层传入的请求。

## 配置变化

- 无配置变化。
- 未读取真实 API key。
- 未新增 DeepSeek、Ollama 或其他供应商配置项。

## 测试命令

```bash
pytest -s
```

## 测试结果

- 最近一次验证结果：`37 passed in 1.90s`。
- 当前环境中普通 `pytest` 的输出捕获模式曾触发临时文件清理错误；使用 `pytest -s` 关闭捕获后测试通过。

## 未完成事项

- 未实现 `DeepSeekClient`。
- 未实现 `OllamaClient`。
- 未实现真实 HTTP 请求、重试、超时和错误映射。
- 未实现风格分析、初稿生成、本地改写等业务流程。

## 对其他模块的影响

- 现有文本切分模块、用户需求模块、项目目录模块和配置读取模块未改动。
- 后续业务层可以通过 `ModelClient` 协议依赖统一模型接口，测试中可注入 `FakeModelClient` 避免真实模型调用。
- 包入口 `novel_rewrite_system` 已导出新增接口，便于后续模块统一导入。

## 下一步建议

- 在实现风格分析、初稿生成或本地改写业务前，优先让业务函数接收 `ModelClient` 参数。
- 后续真实 DeepSeek/Ollama 接入应新增具体客户端实现 `ModelClient`，并将供应商 HTTP 细节、API key、错误处理封装在具体客户端内部。
- 为真实客户端补充独立单元测试，使用 mock HTTP，不在单元测试中访问网络。
