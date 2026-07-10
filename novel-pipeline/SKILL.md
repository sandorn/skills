---
name: novel-pipeline
version: "3.4.0-writer-align"
description: "网文批量生产线：DeepSeek 初稿 + 豆包润色两个 stdio MCP。专注于章节生成和润色，状态管理由 writer skill 负责。可独立运行，也可作为 writer skill 的子服务"
category: writing
tags: [网文, 写作, pipeline, MCP, 逐章润色, writer 协作]
---

# novel-pipeline: 网文批量生产线（精简版 v3.4）

> 🔴 所有润色请求走逐章顺序模式，禁止批量/后台运行
> 📌 状态管理（角色/伏笔/世界观）**不再本 skill 职责**，交给 writer skill

---

## 定位

本 skill 只做两件事：

1. **批量初稿生成** — `novel-deepseek` MCP `generate_draft`
2. **章节润色** — `novel-doubao` MCP `polish_chapter`（支持字数循环 + 文风预设 override）

配合 `scripts/polish_chapter.py` 提供：
- 前置 git 快照（`ensure_git_snapshot`）
- 断点续传（`.polish_progress.json`）
- 批量 CLI（`--range N-M`）
- 字数循环（`--min-words` / `--max-words`）
- 文风预设 override（`--style-file`）

**明确不做**（v3.4 起）：
- 项目初始化、大纲规划
- 状态归档（伏笔/角色/世界观）
- 43 维审查、禁令扫描
- 批量格式修复、跨卷审查
- 题材适配、tracking 维护

以上全部交给 `writer` skill。

---

## 环境与配置

### `.env` 位置
`<Skill目录>\.env`

必需 6 个变量：`DEEPSEEK_{API_KEY,BASE_URL,MODEL}` + `DOUBAO_{API_KEY,BASE_URL,MODEL}`。

优先级：Skill 本地 .env → 系统环境变量。两级都缺则 MCP server 启动即 `sys.exit(1)`。

### novel-doubao 调用规范
禁止 `subprocess.communicate()` 立即关闭 stdin（会触发 `anyio.ClosedResourceError`）。必须用 `hooks/utils.py::BaseMCPClient`（队列+线程读 stdout）。

### 章节文件命名（强制）
统一 `chapters/ch_NNN.md`（三位数补零 + 下划线，与 writer 一致）。
入口：`hooks/utils.py::chapter_filename(n)`。

---

## 使用场景

### 场景 A：writer 主导 + 本 skill 出稿/润色（推荐）

```powershell
# 1. writer 会话内规划（不涉及本 skill）
#    → outline/chapter_outline/ch_NNN.md

# 2. writer 主 Agent 调 novel-deepseek MCP 出初稿
#    → chapters/ch_NNN.md
#    → writer 侧 archive_facts.py 归档事实到 .writer/state/*.json

# 3. 本 skill 批量润色（豆包 + writer 番茄预设）
python <novel-pipeline>/scripts/polish_chapter.py --range 1-30 <project>/chapters `
    --style-file <writer>/references/presets/fanqie-quick-anti.md `
    --min-words 2500 --max-words 3000

# 4. writer 侧审查
python <writer>/scripts/audit.py <project>/chapters
# 或 writer 会话中 review --daily
```

### 场景 B：本 skill 独立运行（无 writer 项目结构）

```powershell
python <novel-pipeline>/scripts/polish_chapter.py --range 1-20 <chapters_dir>
```

行为：
- MCP 调用不带 `style_prompt_override`，走内嵌通用锁定式 prompt
- ensure_git_snapshot 检测非 git repo → 除非 `--force` 否则拒绝
- 原地覆写 `chapters/*.md`

---

## 项目根识别

识别以下三种标记（优先 `novel.json`）：

| 标记 | 场景 |
|---|---|
| `novel.json` | 新项目推荐（writer + novel-pipeline 共用）|
| `writer.json` | writer skill 项目（协作场景）|
| `novel-pipeline.json` | 老项目（向后兼容） |

**v3.4 起**：识别到项目根后**不再要求 state-files/**——本 skill 只用 `chapters/` 目录 + MCP 生成/润色文本。项目状态由 writer 侧的 `.writer/state/*.json` 管理，本 skill 不读不写。

---

## MCP 调用超时
| 服务 | 建议 timeout | 说明 |
|------|------------|------|
| novel-doubao polish_chapter | 300s | 大章 9000+ 字需 160s+，可延至 600s |
| novel-deepseek generate_draft | 300s | 一般 30-90s |

---

## 目录结构

```
novel-pipeline/
├── SKILL.md
├── .env
├── hooks/
│   ├── utils.py                    # 环境变量 + 章节命名 + BaseMCPClient
│   └── polish_independent.py       # 润色核心管线（stdin 输入 chapter，输出 polished）
├── mcp/
│   ├── novel-doubao/doubao_server.py     # 润色 MCP
│   └── novel-deepseek/deepseek_server.py # 初稿 MCP
├── scripts/
│   ├── polish_chapter.py           # 官方唯一润色入口（CLI）
│   ├── mcp_utils.py                # Hermes 自动注册（可选）
│   └── verify_env.py               # 环境诊断
└── references/                     # 6 份必要文档
    ├── polish-pipeline.md          # 润色核心规则
    ├── mcp-integration-guide.md    # MCP 配置
    ├── env-template.md
    ├── deployment-guide.md
    ├── troubleshooting.md
    └── webnovel_triggers.md        # DeepSeek 出稿时用的网文技法参考
```

---

## Layer 1 规则（不可违反）

- ⛔ 禁止在本 skill 内做状态归档（伏笔/角色/世界观）——交给 writer
- ⛔ 禁止编写审查/大纲/项目初始化脚本——交给 writer
- ⛔ 禁止批量/并行/后台润色（前端卡顿）
- ⛔ 禁止绕过 MCP 工具直接调用模型 API（除 MCP server 内部）
- ✅ 只做：单章顺序路由 → 调 MCP → 覆写 chapters/*.md → 下一章

---

## 脚本速查

| 脚本 | 功能 |
|------|------|
| `scripts/polish_chapter.py` | 唯一润色入口（前置 git 快照 + 断点续传 + 字数循环 + 文风 override）|
| `scripts/verify_env.py` | 环境诊断（Python/依赖包/.env/MCP server 文件）|
| `scripts/mcp_utils.py` | Hermes 会话内自动注册 MCP（非 Hermes 环境打印手动配置片段）|

Hook 脚本（被 polish_chapter.py 调用，无独立入口）：
| `hooks/polish_independent.py` | 润色核心管线（读 stdin → 调 MCP → 完整性检查 → 输出 JSON）|
| `hooks/utils.py` | 共享工具（BaseMCPClient / chapter_filename / find_project_root）|

---

## 与 writer skill 协作

| 能力 | writer | novel-pipeline |
|---|---|---|
| 大纲规划、状态追踪、审查、发布、封面 | ✅ | — |
| 初稿写章（主 Agent 直写） | ✅ 5/9 步管线 | — |
| 批量豆包润色（`DOUBAO_MODEL`） | 不自持 | ✅ `polish_chapter.py` |
| DeepSeek MCP 批量出稿 | 调本 skill MCP | ✅ `generate_draft` |
| 硬禁令 B01-B10、43 维审查 | ✅ | — |
| Git 前置快照 | writer 侧有 `lib.ensure_git_snapshot`（供批量写章/修复用） | 本 skill 自持（供批量润色用）|
| 状态归档（`.writer/state/*.json`）| ✅（`scripts/archive_facts.py`）| ❌ |
| tracking 派生（`tracking/*.md`）| ✅（`scripts/render_tracking.py`）| ❌ |

---

## 详细参考（按需加载）

| 内容 | 跳转 |
|------|---------|
| 润色管线详细规则 | `references/polish-pipeline.md` |
| 环境变量模板 | `references/env-template.md` |
| 部署指南 | `references/deployment-guide.md` |
| MCP 集成详细说明 | `references/mcp-integration-guide.md` |
| 故障排查手册 | `references/troubleshooting.md` |
| 网文写作技巧（DeepSeek 出稿参考）| `references/webnovel_triggers.md` |
