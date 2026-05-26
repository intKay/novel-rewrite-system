# 任务交接记录：Task M — Ollama 本地模型客户端

## 任务名称

- Task M：Ollama 本地模型客户端

## 修改范围

- 新增 `src/novel_rewrite_system/ollama_client.py` Ollama 本地模型客户端
- 新增 `tests/test_ollama_client.py` 单元测试（mock HTTP）
- 更新 `src/novel_rewrite_system/__init__.py` 导出 `OllamaClient`
- 更新 `docs/task_status.md` 和 `docs/interface_registry.md`
- **未修改**：DeepSeekClient、模型接口抽象层、错误类型模块、Task H 提示词构建器、风格分析服务、初稿生成服务、项目索引 JSON、文本处理集成

## 新增/修改文件

| 文件 | 操作 |
|------|------|
| `src/novel_rewrite_system/ollama_client.py` | 新增 |
| `tests/test_ollama_client.py` | 新增 |
| `src/novel_rewrite_system/__init__.py` | 修改（新增导出） |
| `docs/task_status.md` | 修改（新增 Task M 行） |
| `docs/interface_registry.md` | 修改（新增 Ollama 客户端行） |

## 暴露接口

- `OllamaClient` 类（满足 `ModelClient` 协议）
- 构造函数签名：
  ```python
  OllamaClient(
      base_url: str = "http://localhost:11434",
      model: str = "qwen3:4b",
      *,
      timeout: float = 120.0,
      http_client: httpx.Client | None = None,
  )
  ```
- `OllamaClient.generate(request: ModelRequest) -> ModelResponse`
- 从 `novel_rewrite_system.ollama_client` 或 `novel_rewrite_system` 导入

## 输入/输出

### 构造参数
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `base_url` | `http://localhost:11434` | Ollama 服务地址，自动追加 `/api/chat` |
| `model` | `qwen3:4b` | 模型名称 |
| `timeout` | `120.0` | HTTP 请求超时时间（秒） |
| `http_client` | `None` | 可选外部 `httpx.Client`，用于测试时注入 mock transport |

### `generate()` 方法
| 输入 | 输出 | 错误 |
|------|------|------|
| `ModelRequest` | `ModelResponse(provider="ollama", model=..., text=..., finish_reason=..., usage=..., raw=...)` | 网络失败 → `ProjectError`（中文消息）；非 2xx → `ProjectError`；JSON 解析失败 → `ProjectError`；缺少 message 字段 → `ProjectError` |

### ModelRequest 到 Ollama API 的映射
| ModelRequest 字段 | Ollama API 字段 |
|---|---|
| `prompt` | `messages[].role="user"` |
| `system_prompt` | `messages[].role="system"`（可选） |
| `temperature` | `options.temperature` |
| `top_p` | `options.top_p` |
| `max_tokens` | `options.num_predict` |

- `stream` 固定为 `false`
- 无 option 字段时整个 `options` 键省略

## 配置变化

- 无。`OllamaClient` 通过构造参数接收配置，不读取 YAML 配置文件，不读取环境变量（Ollama 不需要 API key）。

## 测试命令

```bash
.venv/bin/python -m pytest -q -s tests/test_ollama_client.py
.venv/bin/python -m pytest -q -s
```

## 测试结果

- Task M 专测：20 passed in 3.62s
- 全量：190 passed in 4.20s
- 所有测试使用 `httpx.MockTransport`，零真实网络请求

## 未完成事项

- 无。只实现 Ollama 客户端，未实现本地改写服务。

## 对其他模块的影响

- 无破坏性影响。`OllamaClient` 是实现类，不影响已有模块。
- `__init__.py` 中新增了 `OllamaClient` 到 `__all__`。
- 上游依赖：Task C（`ModelClient`/`ModelRequest`/`ModelResponse`）、Task E（`ProjectError`）、`httpx`。

## 业务层使用方式

```python
from novel_rewrite_system import OllamaClient, ModelClient, ModelRequest

# 生产环境 —— 需要 Ollama 在 localhost:11434 运行
client: ModelClient = OllamaClient(model="qwen3:4b")
response = client.generate(ModelRequest(prompt="改写以下文本..."))

# 测试环境 —— 注入 FakeModelClient，业务逻辑只依赖 ModelClient
from novel_rewrite_system import FakeModelClient
fake_client: ModelClient = FakeModelClient(text="改写后的文本")
```

## 下一步建议

- 本模块已完成，建议先进行 code review，再开始本地改写服务。
- 本地改写服务可串联：Task H 的 `build_local_rewrite_prompt()` 构建 ModelRequest → 传入 `OllamaClient.generate()` → 获取改写后的文本。
