# 中文小说生成与本地改写系统

第一阶段只包含基础骨架：配置读取、配置结构校验、项目目录初始化。

## 运行测试

推荐使用 Python 3.11 或 3.12。完整环境说明见 [docs/dev_environment.md](docs/dev_environment.md)。

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
python -m pip install -e .[dev]
python -m pytest
```
