# novel-pipeline MCP 集成现状

> 最后更新: 2026-07-10
> 基于实地验证，非理论规划。

---

## 一、实际 MCP 服务器清单

pipeline 目前仅依赖两个 stdio MCP，全部由 Skill 自带（`mcp/novel-*/`），通过 `scripts/mcp_utils.py` 的 `ensure_mcps_ready()` 首次执行时自动向 Hermes 注册。

| MCP | 位置 | 用途 | 工具 |
|-----|------|------|------|
| **novel-deepseek** | `mcp/novel-deepseek/deepseek_server.py` | 初稿生成 | `generate_draft` |
| **novel-doubao** | `mcp/novel-doubao/doubao_server.py` | 章节润色 | `polish_chapter` |

两个 server 都通过 stdio 由子进程直接调用（`hooks/polish_independent.py` → `BaseMCPClient`），不经 LiteLLM 网关。

---

## 二、配置来源（唯一权威）

两个 server 都严格按以下顺序读取环境变量：

1. **Skill 本地 `.env`** — `C:\Users\Administrator\.agents\skills\novel-pipeline\.env`
2. **系统环境变量** — 兜底

**没有内置默认值**：任一 KEY 缺失，server 启动即 `sys.exit(1)`，避免打错误端点。

必需变量：

```ini
DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=...
DEEPSEEK_MODEL=...
DOUBAO_API_KEY=...
DOUBAO_BASE_URL=...
DOUBAO_MODEL=...
```

`DOUBAO_BASE_URL` 允许含/不含 `/chat/completions`，代码会自动判断避免双路径。

---

## 三、调用规范（doubao 长响应）

`polish_chapter` 通过火山方舟 `/api/plan/v3` agent plan 链路推理，单章响应 60–170s，大章 9000+ 字可到 200s+。

- **禁止** `subprocess.communicate()` 立即关 stdin，会触发 `anyio.ClosedResourceError`。
- **正确做法**：`hooks/utils.py::BaseMCPClient` 通过 `queue + thread` 逐行读 stdout，stdin 常开直到收到匹配 id 的响应。
- **超时**：`polish_chapter` 建议 `timeout=300`，最大 600s。

---

## 四、状态存储

state-files 全部为本地 JSON（`state-files/{world_setting,characters,foreshadowing,power_system}.json`），由 `load_state.py` / `archive_state.py` 读写。**不依赖任何外部知识图谱或 memory MCP**。

多项目隔离：`hooks/utils.py::find_state_dir()` 从 CWD 向上找 `novel-pipeline.json` 标记，命中则用项目自己的 `state-files/`，未命中回退 Skill 模板（只读）。
