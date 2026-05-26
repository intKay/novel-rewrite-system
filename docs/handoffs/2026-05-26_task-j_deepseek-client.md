# 任务交接记录：Task J — DeepSeek 云端模型客户端

## 任务名称

- Task J：DeepSeek 云端模型客户端

## 修改范围

- 新增 DeepSeek API 客户端，实现 `ModelClient` 协议
- 新增单元测试（全程 mock HTTP，不访问真实网络）
- 添加 `httpx` 运行时依赖
- 更新 `docs/task_status.md` 和 `docs/interface_registry.md`
- **未修改**：模型接口抽象层、错误类型模块、项目索引 JSON、文本处理集成、Task F/G 提示词构建器

## 新增/修改文件

| 文件 | 操作 |
|------|------|
| `src/novel_rewrite_system/deepseek_client.py` | 新增 |
| `tests/test_deepseek_client.py` | 新增 |
| `pyproject.toml` | 新增 `httpx>=0.24` 依赖 |
| `src/novel_rewrite_system/__init__.py` | 新增 `DeepSeekClient` 导出 |
| `docs/task_status.md` | 新增 Task J 行 |
| `docs/interface_registry.md` | 新增 DeepSeek 客户端行 |

## 暴露接口

- `DeepSeekClient` 类（满足 `ModelClient` 协议）
- 构造函数签名：
  ```python
  DeepSeekClient(
      base_url: str = "https://api.deepseek.com",
      model: str = "deepseek-v4-flash",
      api_key_env: str = "DEEPSEEK_API_KEY",
      *,
      http_client: httpx.Client | None = None,
  )
  ```
- `DeepSeekClient.generate(request: ModelRequest) -> ModelResponse`
- 从 `novel_rewrite_system.deepseek_client` 或 `novel_rewrite_system` 导入

## 输入/输出

### 构造参数
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `base_url` | `https://api.deepseek.com` | DeepSeek API 基础地址，自动追加 `/chat/completions` |
| `model` | `deepseek-v4-flash` | 模型名称 |
| `api_key_env` | `DEEPSEEK_API_KEY` | 读取 API key 的环境变量名 |
| `http_client` | `None` | 可选外部 `httpx.Client`，用于测试时注入 mock transport |

### `generate()` 方法
| 输入 | 输出 | 错误 |
|------|------|------|
| `ModelRequest` | `ModelResponse(provider="deepseek", model=..., text=..., finish_reason=..., usage=..., raw=...)` | API key 缺失 → `ModelConfigError`；网络失败/非 2xx/空响应 → `ProjectError`（中文消息） |

## 环境变量配置

```bash
# Linux / macOS
export DEEPSEEK_API_KEY="sk-your-key-here"

# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-your-key-here"

# Windows CMD
set DEEPSEEK_API_KEY=sk-your-key-here
```

可通过 `api_key_env` 参数使用不同的环境变量名。

## 测试命令

```bash
.venv/bin/python -m pytest -q -s tests/test_deepseek_client.py
.venv/bin/python -m pytest -q -s
```

## 测试结果

- Task J 专测：17 passed
- 全量：111 passed in 2.29s
- 所有测试使用 `httpx.MockTransport`，零真实网络请求

## 未完成事项

- 无。只实现 DeepSeek 客户端，未实现 Ollama 客户端和业务流程。

## 对其他模块的影响

- 无破坏性影响。`DeepSeekClient` 是实现类，不影响已有模块。
- `__init__.py` 中新增了 `DeepSeekClient` 到 `__all__`。

## 业务层使用方式

```python
from novel_rewrite_system import DeepSeekClient, ModelClient, ModelRequest

# 生产环境 —— 需要设置 DEEPSEEK_API_KEY 环境变量
client: ModelClient = DeepSeekClient(model="deepseek-v4-flash")
response = client.generate(ModelRequest(prompt="写一段小说"))

# 测试环境 —— 注入 FakeModelClient，业务逻辑只依赖 ModelClient
from novel_rewrite_system import FakeModelClient
fake_client: ModelClient = FakeModelClient(text="测试回复")
```

## 下一步建议

- Task 4 中可添加配置集成：让 `DeepSeekClient` 从 `Settings.cloud_model` 读取 `base_url`、`model`、`api_key_env`。
- 后续风格分析流程应：用 `build_style_analysis_prompt()` 构建 `ModelRequest` → 传入 `DeepSeekClient.generate()` → 获取 `ModelResponse.text`。
- 初稿生成流程同理：用 `build_draft_generation_prompt()` → `DeepSeekClient.generate()`。
