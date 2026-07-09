# 配置文件审计记录：LiteLLM vs Hermes 对比

> 最后更新：2026-07-04 | 当前状态：LiteLLM (17 MCP) vs Hermes (18 HTTP proxy + 4 native stdio) ✅

---

## 一、LiteLLM 网关 (`~/.litellm/config.yaml`)

### 模型清单（14 个）

| 名称 | 提供商 | API Base |
|------|--------|----------|
| `deepseek-v4-flash` | DeepSeek | `https://api.deepseek.com/v1` |
| `deepseek-v4-pro` | DeepSeek | `https://api.deepseek.com/v1` |
| `glm-5.2` | 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` |
| `glm-5-turbo` | 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` |
| `qwen3.7-max` | 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `qwen3.7-plus` | 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `doubao-evolving` | 豆包 / Volc Ark | `https://ark.cn-beijing.volces.com/api/v3` |
| `doubao-turbo` | 豆包 / Volc Ark | `https://ark.cn-beijing.volces.com/api/v3` |
| `fenno/gpt-5.5` | Fenno API | `https://api.fenno.ai/v1` |
| `agnes-ai` | Agnes AI | `https://apihub.agnes-ai.com/v1` |
| `fun-gpt-5.5` | apikey.fun | `https://api.apikey.fun/v1` |
| `fun-codex` | apikey.fun | `https://api.apikey.fun/v1` |
| `fun-claude-opus-4-8` | apikey.fun (Anthropic) | `https://api.apikey.fun` |
| `fun-claude` | apikey.fun (Anthropic) | `https://api.apikey.fun` |

### MCP 清单（19 个）

**通用**: context7, playwright, officecli, pandoc, yaml_lint
**版本控制**: github (*@github/mcp-server-github*), git (*mcp-server-git*)
**思维/记忆**: sequential_thinking, memory_official, memory_novel
**文件/代码**: filesystem, firecrawl
**Windows 管理**: windows_admin
**小说创作**: publishready, firstory, uno, novel_deepseek, novel_doubao
**AI 管理**: litellm_admin

> **命名演变**: `github_official` → `github`, `litellm-manager` → `litellm_admin`, `mcp_audit`/`shell` 已移除

### 自定义 MCP 服务器 (`servers/*/`)

| 服务器 | 路径 | 说明 |
|--------|------|------|
| `litellm-admin` | `servers/litellm-admin/litellm_admin_mcp.py` | MCP 工具管理 LiteLLM 模型/Key/配置 |
| `novel-deepseek` | `servers/novel-deepseek/deepseek_server.py` | 小说专用 DeepSeek 代理 |
| `novel-doubao` | `servers/novel-doubao/doubao_server.py` | 小说专用豆包代理 |
| `uno-mcp` | `servers/uno-mcp/dist/index.js` | UNO 写作工具 MCP |

---

## 二、Hermes `config.yaml`（当前激活）

### MCP 服务（19 个，全部 LiteLLM 代理模式）

| Hermes 配置键 | LiteLLM 对应名 | URL路径 |
|--------------|---------------|---------|
| `litellm-context7` | context7 | `/mcp/context7` |
| `litellm-playwright` | playwright | `/mcp/playwright` |
| `litellm-officecli` | officecli | `/mcp/officecli` |
| `litellm-git` | git | `/mcp/git` |
| `litellm-pandoc` | pandoc | `/mcp/pandoc` |
| `litellm-windows-admin` | windows_admin | `/mcp/windows_admin` |
| `litellm-yaml-lint` | yaml_lint | `/mcp/yaml_lint` |
| `litellm-sequential-thinking` | sequential_thinking | `/mcp/sequential_thinking` |
| `litellm-memory-official` | memory_official | `/mcp/memory_official` |
| `litellm-memory-novel` | memory_novel | `/mcp/memory_novel` |
| `litellm-publishready` | publishready | `/mcp/publishready` |
| `litellm-firstory` | firstory | `/mcp/firstory` |
| `litellm-uno` | uno | `/mcp/uno` |
| `litellm-novel-deepseek` | novel_deepseek | `/mcp/novel_deepseek` |
| `litellm-novel-doubao` | novel_doubao | `/mcp/novel_doubao` |
| `litellm-litellm-admin` | litellm_admin | `/mcp/litellm_admin` |
| `litellm-github` | github | `/mcp/github` |
| `litellm-filesystem` | filesystem | `/mcp/filesystem` |
| `litellm-firecrawl` | firecrawl | `/mcp/firecrawl` |

---

## 三、各配置文件的 MCP 服务数量

| 文件 | MCP 数量 | 连接模式 | 备注 |
|------|---------|---------|------|
| **`config.yaml`** ✅ 当前激活 | 19 | LiteLLM 代理 (HTTP) | 与 LiteLLM 完全同步 |
| `config - litellm.yaml` | 3 | 本地 Stdio | 已修复 YAML 语法 |
| `config - 直连.yaml` | 3 | 本地 Stdio | 纯直连模式 |
| `config - 副本.yaml` | 3 | 本地 Stdio | 备份 |
| `config-01.yaml` | 4 | 本地 Stdio | 含 codebase-memory-mcp |
| `config-02.yaml` | 3 | 本地 Stdio | Fenno 多提供商 |

---

## 四、Hermes provider 映射

| Hermes provider | 实际指向 | 可用模型 |
|----------------|---------|---------|
| `deepseek` | 直连 DeepSeek API | deepseek-v4-flash, deepseek-v4-pro |
| `custom:127-0-0-1-4000` | LiteLLM 网关 `:4000/v1` | 仅 deepseek-v4-flash（可扩展） |

---

## 五、客户端同步状态

| 客户端 | MCP 文件 | 同步状态 |
|--------|---------|---------|
| **Hermes** (本进程) | `config.yaml` → LiteLLM HTTP | ✅ 19 MCP 已同步 |
| **Claude Desktop** | `~/.claude.json (projects.*.mcpServers)` | ✅ 19 MCP 已同步 |
| **VS Code MCP** | `AppData/Roaming/Code/User/mcp.json` | ✅ 19 MCP 已同步 |
| **CodeBuddy** | `~/.codebuddy/mcp.json` | ✅ 19 MCP + hermes-mcp 保留 |
| **Continue** | `~/.continue/config.yaml` | ✅ 19 MCP 已同步，14 模型保留 |

> 各客户端维护独立的 MCP 白名单，**不**随 LiteLLM 自动同步。MCP 变更后需执行全量同步流程。