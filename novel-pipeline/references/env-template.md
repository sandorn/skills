# 环境变量模板

> 唯一权威配置位置：Skill 本地 `.env`
> 路径：`C:\Users\Administrator\.cc-switch\skills\novel-pipeline\.env`
> 优先级：**skill 本地 .env → 系统环境变量**。两级都缺则 server 启动报错退出。

```ini
# ==================== 豆包润色配置 ====================
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/plan/v3
DOUBAO_API_KEY=ark-your-key-here
DOUBAO_MODEL=doubao-seed-2-0-pro-260215

# ==================== DeepSeek 初稿配置 ====================
DEEPSEEK_BASE_URL=https://ark.cn-beijing.volces.com/api/plan/v3
DEEPSEEK_API_KEY=ark-your-key-here
DEEPSEEK_MODEL=deepseek-v4-pro

# ==================== 路径配置（可选，供 hooks 使用） ====================
# MCP 子进程 Python 解释器（缺省则用当前 sys.executable；旧变量名 HERMES_PYTHON 仍向后兼容）
# 推荐指向本 skill 自带 venv（由 uv 创建，依赖见 requirements.txt）
PIPELINE_PYTHON=C:\Users\Administrator\.cc-switch\skills\novel-pipeline\.venv\Scripts\python.exe
# 默认小说项目章节目录
CHAPTERS_DIR=D:\Writer\novel-project\chapters
```

## 独立 venv

本 skill 自带独立 venv（`<Skill>\.venv`），不依赖 Hermes 主环境：

```powershell
# 重建（Python 3.13）
cd <Skill>
uv venv --python 3.13 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
```

⚠️ **必须锁定 `mcp<2`**：mcp 2.x 已将 `FastMCP` 改名为 `MCPServer`，
现有 MCP server 代码使用 `from mcp.server.fastmcp import FastMCP`，装 2.x 会直接导入失败。

## 说明

- 全部 6 个必需项：`DEEPSEEK_{API_KEY,BASE_URL,MODEL}`、`DOUBAO_{API_KEY,BASE_URL,MODEL}`。
- server 端不提供任何兜底默认，缺一项 → `sys.exit(1)`。
- 已移除：`MCP_FIRSTORY_ENDPOINT`、`MCP_MEMORY_NOVEL_ENDPOINT`、`publishready` 相关变量（对应 MCP 均已下线）。
- 章节文件名统一为三位数补零：`ch_001.md`、`ch_010.md`、`ch_101.md`（下划线分隔，与 writer skill 一致）。
