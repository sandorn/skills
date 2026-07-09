# LiteLLM MCP 服务器清单

> 来源: `~/.litellm/config.yaml` 的 `mcp_servers:` 段
> 更新: 2026-07-04 | 总计: 19 个服务器

## 按类型分组

### npx 包（npm registry, 10 个）

| LiteLLM key | npm 包 | 特殊配置 |
|------------|--------|---------|
| `context7` | `@upstash/context7-mcp` | — |
| `playwright` | `@playwright/mcp@latest` | — |
| `github` | `@github/mcp-server-github` | — |
| `filesystem` | `@modelcontextprotocol/server-filesystem` | args: `D:/CODES` |
| `firecrawl` | `firecrawl-mcp` | env: `FIRECRAWL_API_KEY` |
| `officecli` | `officecli` | args: `mcp` |
| `sequential_thinking` | `@modelcontextprotocol/server-sequential-thinking` | — |
| `memory_official` | `@modelcontextprotocol/server-memory` | — |
| `publishready` | `@veldica/publishready-mcp` | — |
| `firstory` | `firstory-mcp` | — |

### uvx 包（4 个）

| LiteLLM key | 包名 |
|------------|------|
| `windows_admin` | `mcp-windows-admin` |
| `yaml_lint` | `mcp-yaml-lint` |
| `git` | `mcp-server-git` |
| `pandoc` | `mcp-pandoc` |

### 本地 Node.js（1 个）

| LiteLLM key | 路径 |
|------------|------|
| `uno` | `~/.litellm/servers/uno-mcp/dist/index.js` |

### 本地 Python FastMCP（4 个）

| LiteLLM key | 脚本路径 | 环境依赖 |
|------------|---------|---------|
| `novel_deepseek` | `~/.litellm/servers/novel-deepseek/deepseek_server.py` | `pip install mcp httpx` |
| `novel_doubao` | `~/.litellm/servers/novel-doubao/doubao_server.py` | `pip install mcp httpx` |
| `litellm_admin` | `~/.litellm/servers/litellm-admin/litellm_admin_mcp.py` | `pip install mcp httpx` |
| `memory_novel` | npx `@pepk/mcp-memory-sqlite` | env: `MEMORY_DB_DIR`, `MEMORY_PROJECT` |

## Hermes 同步状态

| 接入方式 | 数量 | Hermes key 模式 | 示例 |
|---------|------|-----------------|------|
| HTTP proxy（通过 LiteLLM） | 17 | `litellm-<name>` | `litellm-publishready` → `http://127.0.0.1:4000/mcp/publishready` |
| 原生 stdio | 2 | `<name>` | `novel-deepseek` → `python deepseek_server.py` |

> **全部 19 个已同步到 `~/.hermes/config.yaml` 的 `mcp_servers:` 段。**
