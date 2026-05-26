# 最小开发环境基线

本项目第一版优先面向 Windows 本地开发和测试，后续再迁移到 Ubuntu / Fedora。

## Python 版本

推荐安装 Python 3.11 或 Python 3.12。本项目要求 Python `>=3.11`，不能使用 `/usr/bin/python3=3.10` 作为测试解释器。

在 Windows 中确认版本：

```powershell
py -3.11 --version
python --version
```

如果当前 shell 没有 `python` 命令，优先使用：

```powershell
py -3.11
```

如果系统中安装的是独立命令，也可以使用：

```bash
python3.11 --version
```

## 创建虚拟环境

Windows 推荐命令：

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
```

如果使用 Python 3.12，可将 `py -3.11` 改为 `py -3.12`。

WSL / Linux 环境如果已经安装 `python3.11`，推荐同样创建项目本地虚拟环境，不要直接向受管理的全局解释器安装依赖：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
```

## 安装依赖

项目使用 `pyproject.toml` 管理依赖。安装运行依赖和测试依赖：

```powershell
python -m pip install -e .[dev]
```

其中 `pytest` 来自 `dev` 可选依赖组。

## 运行测试

激活虚拟环境后运行：

```powershell
python -m pytest
```

如果 shell 中没有 `python` 命令，也可以直接指定解释器：

```powershell
py -3.11 -m pytest
```

WSL / Linux 下可使用虚拟环境中的解释器：

```bash
.venv/bin/python -m pytest
```

如果在 Windows 挂载目录或 Codex 环境中遇到 pytest 输出捕获的临时文件异常，可关闭捕获后重试：

```bash
.venv/bin/python -m pytest -s
```

## 模型策略

- **cloud 模式（推荐）**：`story-rewrite --model-mode cloud`，全流程 DeepSeek API，仅需 `DEEPSEEK_API_KEY` 环境变量
- **real 模式（可选）**：`story-rewrite --model-mode real`，改写阶段使用 Ollama，需本地安装 Ollama 并拉取模型
- **fake 模式（测试）**：`story-rewrite`（默认），使用 FakeModelClient，不访问网络

详见 `agent.md` §5 和 §12。

## Codex 沙箱说明

如果 Codex 本地沙箱报错提示缺少 `bwrap` / `bubblewrap`，这是 Codex 本机沙箱环境问题，不是项目代码问题。该问题可能导致普通 shell 命令无法启动，但不应通过降低项目 Python 版本要求来规避。
