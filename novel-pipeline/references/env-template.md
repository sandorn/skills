# 环境变量模板

> 唯一权威配置位置：Skill 本地 `.env`
> 路径：`C:\Users\Administrator\.agents\skills\novel-pipeline\.env`
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
# Hermes Python 解释器路径
HERMES_PYTHON=C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe
# Node.js 可执行文件路径（可选）
NODE_EXE=C:\Program Files\nodejs\node.exe
# NPX 可执行文件路径（可选）
NPX_CMD=C:\Program Files\nodejs\npx.cmd
# 默认小说项目章节目录
CHAPTERS_DIR=D:\Writer\novel-project\chapters
```

## 说明

- 全部 6 个必需项：`DEEPSEEK_{API_KEY,BASE_URL,MODEL}`、`DOUBAO_{API_KEY,BASE_URL,MODEL}`。
- server 端不提供任何兜底默认，缺一项 → `sys.exit(1)`。
- 已移除：`MCP_FIRSTORY_ENDPOINT`、`MCP_MEMORY_NOVEL_ENDPOINT`、`publishready` 相关变量（对应 MCP 均已下线）。
- 章节文件名统一为三位数补零：`ch001.md`、`ch010.md`、`ch101.md`。
