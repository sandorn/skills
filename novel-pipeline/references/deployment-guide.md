# novel-pipeline 部署指南

## 一、前置依赖
- Python ≥ 3.10（含 `httpx` / `mcp` 两个 pip 包）
- API 端点：豆包/DeepSeek（或任一 OpenAI 兼容端点，火山方舟 `/api/plan/v3` 亦可）
- 可选：Hermes CLI（若要自动向 Hermes 注册 MCP）

**不再依赖** LiteLLM 网关、firstory、uno、publishready、memory-novel 等外部服务。项目当前状态由 writer skill 的 `novel_project` MCP 承载（本 skill 不读不写）。

---

## 二、Skill 部署步骤

1. **放置 Skill 目录**
   将 `novel-pipeline/` 放到你的 skills 目录：
   - Hermes：`C:\Users\<用户名>\AppData\Roaming\cn.org.hermesagent.desktop\runtime\hermes-home\skills\`
   - 通用：`C:\Users\<用户名>\.agents\skills\`
   - Claude Code：`~/.claude/skills/` 或项目内 `.claude/skills/`

2. **配置环境变量**
   在 `<Skill 目录>\.env` 中填 6 个必需项：

   ```ini
   DEEPSEEK_API_KEY=...
   DEEPSEEK_BASE_URL=...
   DEEPSEEK_MODEL=...
   DOUBAO_API_KEY=...
   DOUBAO_BASE_URL=...
   DOUBAO_MODEL=...
   ```

   优先级：Skill 本地 `.env` → 系统环境变量。缺一即 server 启动失败。

3. **诊断**
   ```powershell
   python <Skill路径>\scripts\verify_env.py
   ```
   `summary.ok: true` 即通过。

---

## 三、MCP 注册

### Hermes 环境（自动）
首次调用 `scripts/polish_chapter.py` 时会自动向 Hermes 注册 `novel-doubao` 与 `novel-deepseek`（通过 `hermes mcp add`）。

### 非 Hermes 环境（手动）
运行 `polish_chapter.py` 会检测到 `hermes` 命令缺失，打印手动注册片段。将其粘贴到你的客户端配置：

- **Claude Desktop**：`%APPDATA%\Claude\claude_desktop_config.json`
- **Claude Code**：项目根 `.mcp.json` 或用户级 `~/.claude/mcp.json`

配置形如：
```json
{
  "mcpServers": {
    "novel-doubao": {
      "command": "C:\\Python313\\python.exe",
      "args": ["C:\\...\\novel-pipeline\\mcp\\novel-doubao\\doubao_server.py"]
    },
    "novel-deepseek": {
      "command": "C:\\Python313\\python.exe",
      "args": ["C:\\...\\novel-pipeline\\mcp\\novel-deepseek\\deepseek_server.py"]
    }
  }
}
```

---

## 四、项目初始化

**本 skill v3.4 起不再负责项目初始化**——请使用 `writer` skill 的 `project-init`：

```
writer skill 会话 → "开新书" → 交互创建标准目录 + novel.json
```

生成的目录结构（含 `novel.json` + setting/*.md + chapters/）可直接被本 skill 的 `polish_chapter.py` 识别使用。项目当前状态由 writer 侧的 `novel_project` MCP 管理（本 skill 只碰 chapters/）。

若只是独立运行 novel-pipeline 做纯润色，只需：
1. 有 `chapters/ch_NNN.md` 一批
2. `polish_chapter.py --range 1-N <chapters_dir> [--force]`

不需要 novel.json，也不需要任何 setting/state 目录。

