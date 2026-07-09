# 自定义 MCP 服务器开发

## Python FastMCP 模板

自制服务器统一放在 `~/.litellm/servers/<name>/` 目录下。

```python
from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("server-name", instructions="Server description")

@mcp.tool(name="tool_name", description="工具描述（包含完整约束规则）")
async def my_tool(param1: str, param2: int = 0) -> str:
    # 调用外部 API
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            "https://api.example.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={...},
        )
        return resp.text

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

**依赖**: `mcp` 和 `httpx`（Hermes venv 已内置）。

## .env 读取

```python
from pathlib import Path
SKILL_DIR = Path(__file__).resolve().parent.parent  # → ~/.litellm/servers/
DOTENV_PATH = SKILL_DIR / ".env"                     # → ~/.litellm/servers/.env

if DOTENV_PATH.exists():
    for line in DOTENV_PATH.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            if k.strip() == "MY_KEY":
                API_KEY = v.strip().strip("'\"")
```

## 直接测试 MCP 脚本（无需启动 LiteLLM）

```python
# 检查语法和导入
python -c "exec(open('path/to/server.py').read().split('if __name__')[0]); print('OK')"
```

## 在 LiteLLM 中注册（当 Hermes 原生 stdio 不可行时）

```yaml
# ~/.litellm/config.yaml mcp_servers:
my_server:
    command: 'C:\path\to\venv\Scripts\python.exe'
    args:
        - 'C:\Users\Administrator\.litellm\servers\my_server\server.py'
    env:
        PYTHONUNBUFFERED: '1'
        MY_API_KEY: sk-xxx
```

> 注意：LiteLLM mcp_servers key 用下划线 `_`，禁止连字符 `-`
