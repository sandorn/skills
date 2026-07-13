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

# novel-pipeline MCP 集成现状

> 最后更新: 2026-07-10（v3.4）
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

## 四、状态存储（v3.5 起委托给 writer + `novel_project` MCP）

本 skill **不再持有任何状态文件**。项目当前状态（角色/伏笔/世界观/战力）由 writer skill 的 `novel_project` MCP 独占管理，通过 `writer/scripts/archive_facts.py` 生成 payload 后由 writer 侧 Agent 调 MCP 写入。**本 skill 不读也不写 `novel_project` MCP。**

本 skill 只操作 `chapters/*.md`：读原文 → 调 MCP → 覆写。

项目根识别（`hooks/utils.py::find_project_root()`）从 CWD 向上找 `novel.json` / `writer.json` / `novel-pipeline.json` 任一标记，用于 git 快照路径解析。识别不到不阻塞——独立场景（无项目根）仍可跑，只是无 git 快照保护。

