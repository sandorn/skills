# 发布流程

## 模型变更
1. 改 `~/.litellm/config.yaml` → 重启 LiteLLM → 同步 Continue

## MCP 变更
1. 改 `~/.litellm/config.yaml` → 重启 LiteLLM → 全量同步所有客户端 → 重启客户端

## 新增 Hermes 原生 MCP
1. 创建包装脚本（如有 @ 符号）
2. 配到 Hermes mcp_servers → /reload-mcp 测试 → /new 确认

## 迁移从 LiteLLM 代理到 Hermes 原生 stdio

当一个 MCP 从 LiteLLM 代理改为 Hermes 原生 stdio 直连时，需要「新增 + 删除 + 清理」三步同时做，缺一不可：

1. **Hermes 侧新增**：在 `~/.hermes/config.yaml` 的 `mcp_servers:` 中添加原生 stdio 条目（command/args/env 格式）
2. **LiteLLM 侧删除**：从 `~/.litellm/config.yaml` 的 `mcp_servers:` 中删除对应条目
3. **客户端清理**：从所有 4 个客户端配置中删除对应的 `litellm-*` HTTP proxy 条目（Continue / VS Code MCP / Claude Desktop / CodeBuddy）
4. **重启 LiteLLM**（移除生效）
5. **生效**：`/new` 新会话验证

**注意**：如果仅做步骤 1 而不做步骤 2-3，会导致：
- LiteLLM 和 Hermes 同时运行同一 MCP 的重复进程
- 客户端仍通过已删除的 LiteLLM 端点连接（连接失败）

## MCP 全量同步流程：LiteLLM → Hermes

1. **提取 LiteLLM MCP 列表**：从 `~/.litellm/config.yaml` 的 `mcp_servers:` 段获取所有 key
2. **对比 Hermes 已有条目**：`~/.hermes/config.yaml` 的 `mcp_servers:` 段
3. **决策接入方式**：
   - LiteLLM 能正常代理 → HTTP proxy: `url: http://127.0.0.1:4000/mcp/<name>`
   - stdio 服务器 tools/list 为空 → 原生 stdio: `command: python ...`
   - npm scoped 包（含 @） → 包装脚本 + stdio
4. **编辑** `~/.hermes/config.yaml` 新增条目（用 Python ruamel.yaml 或 PowerShell，避免编码损坏）
5. **验证 YAML**：`python -c "import yaml; yaml.safe_load(open('~/.hermes/config.yaml'))"`
6. **生效**：`/new` 新会话

## MCP 移除流程（全量客户端清理）

1. **从 LiteLLM 删除**：编辑 `~/.litellm/config.yaml` 删除 mcp_servers 条目
2. **重启 LiteLLM**
3. **逐客户端精准清理**（只删 litellm-* 条目，保留其他，**不要 search_files**）：
   - `~/.continue/config.yaml`
   - `AppData/Roaming/Code/User/mcp.json`
   - `~/.claude.json` → projects.claude_desktop_config.mcpServers
   - `~/.codebuddy/mcp.json`（**保留 hermes-mcp 等非 litellm- 条目**）
4. **删除 Hermes 侧条目**（如果存在）
5. **验证**：`/new` 新会话
