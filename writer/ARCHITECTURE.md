# Writer Skill 架构全景图

> v8.5 · 2026-07-16 — B11 Markdown 零容忍；v8.4 起记忆层迁至 `novel_project` MCP，`.writer/state/` 与 `tracking/` 全面废除

---

## 一、规模

```
writer/                     ~ 380 KB / 47 文件
├── SKILL.md              700+ 行  入口 + 8 场景 + 路由 + 禁令速查 + 协作说明
├── WORKFLOW.md           170 行   完整答题流程（10 阶段）
├── ARCHITECTURE.md              本文件
├── CHANGELOG.md                  版本历史
├── .gitignore
├── references/           ~ 26 文件  AI 执行指令（新增 memory-mcp.md）
├── agents/               4 文件    Full 审查子代理
├── scripts/              12 文件   Python 工具（含 archive_facts / import_state_to_mcp / lib.ensure_git_snapshot）
└── templates/            1 文件    审查报告模板
```

---

## 二、管线全景

```
扫榜→拆文→开书→大纲→写前检查→写章→审查→质检→润色→发布
                        │           │        │
                  batch:对齐    daily:8维  quality:5步
                  single:自检   solo:15维  post-fix:判定
                               lean:27维
                               full:43维(4Agent)

审查替代升级:  daily(每章) → solo(每5章) → lean(每10章) → full(每卷)
              ↑ 嵌套包含，只运行最高级，不叠加
              longform(每100章) 与 full 叠加 — 正交维度

写章前:        Agent 调 novel_project MCP（get_entity_with_relations + search_nodes）
              拉主要角色/势力/未回收伏笔当前状态

写章 Step 3:  archive_facts.py 生成 MCP tool_calls (read→merge→write 三段式)
             Agent 依此顺序调 novel_project MCP：
               phase=read  → get_entity_with_relations（拿旧观测）
               phase=write → create_entities（合并后写回）
               phase=write → create_relations（有向关系边）

批量润色:      交给 novel-pipeline skill polish_chapter.py（豆包 MCP + git 快照 + 断点续传）
批量出稿:      交给 novel-pipeline skill novel-deepseek MCP.generate_draft
```

---

## 三、三层写权限（v8.4 核心架构）

```
{project}/
├── novel.json                # 项目元数据（含 memory_mcp: novel_project）
├── setting/*.md              # 【用户领地】静态设定原稿 + <!-- user-edit --> 规划意图
├── outline/                  # 【用户 + Agent 协作】大纲
├── chapters/                 # 【Agent 主写】正文 ch_NNN.md
└── .writer/
    └── runtime/              # 临时文件（.gitignore）

+ novel_project MCP           # 【Agent 独写】当前状态原子事实 + 关系图谱
  落盘: ~/.agents/skills/writer/memory/novel_project.db
```

| 层 | 写方 | 改方 | 用途 |
|---|---|---|---|
| **`novel_project` MCP** | Agent 独写（archive_facts 生成 payload）| 只 Agent | 原子事实 + 关系图谱 |
| `setting/*.md` | Agent 初始 + 用户改（含 `<!-- user-edit -->`）| 用户为主 | 静态约束 + 规划意图 |
| `chapters/*.md` | Agent 主写 | 用户可修 | 正文 |
| `outline/*.md` | Agent 生成 + 用户改 | 双方 | 大纲 |

**v8.4 与 v8.3 差异**：
- 废除 `.writer/state/*.json`（4 份原子事实文件）→ 全部迁至 MCP
- 废除 `tracking/*.md`（人读派生层）→ 需要人读快照时用 `report_graph.py` 从 MCP 生成
- 用户规划意图从 `tracking/*.md` 挪到 `setting/*.md` 里的 `<!-- user-edit -->` 块

---

## 四、审查体系 (10项)

```
自动触发 (替代升级，零冗余):
  ch1-4:   daily(8维)               每章 3min
  ch5-9:   solo(15维)               每5章 5min  ← 替代 daily
  ch10-19: lean(27维)               每10章 10min ← 替代 solo
  ch20+:   full(43维,4Agent)        每卷 30min   ← 替代 lean
  ch100:   full + longform-quality  叠加(正交)   ← longform 独立

人工触发 (4项):
  manual-pass            逐章检查/不用脚本
  targeted-audit         定向审查/专项审查
  setting-consistency    设定审查/交叉审查
  master-outline         暗线审查/总纲对齐
```

审查读取源：`novel_project` MCP（当前事实 + 关系）+ `setting/*.md`（原始设定）+ `chapters/*.md`（正文）+ `outline/*.md`（大纲计划），四方交叉对比。

---

## 五、状态归档链（v8.4 · MCP-based）

```
写章 Step 3 完成 → chapters/ch_NNN.md 落盘
                ↓
       Agent 分析变更 → 构造 JSON payload（人物/伏笔/势力/关系）
                ↓
       stdin ─→ archive_facts.py（READONLY，只生成 payload）
                ↓
       输出 tool_calls: [phase=read, phase=write, ...]
                ↓
       Agent 按顺序调 novel_project MCP：
         1. phase=read  → get_entity_with_relations（每个已存在实体）
         2. 合并 old_obs + new_obs（替换 <merge_with_old> 占位符）
         3. phase=write → create_entities（覆盖式写回）
         4. phase=write → create_relations（有向边幂等）
                ↓
       novel_project.db (SQLite) 落盘
       WAL 模式，读写并发安全
```

**关键设计**：
- MCP = 单一事实源（结构化实体 + 观测 + 关系，Agent 归档准确，可 `search_nodes` 检索）
- setting md = 静态约束（用户手写，seed MCP 的原稿）
- 用户规划意图 = `setting/*.md` 里的 `<!-- user-edit -->` 块（不落 MCP，但写章前 Agent 会读）
- 两层职责清晰不重合

**权威规范**：`references/memory-mcp.md`（8 个 MCP 工具目录 + entityType/relations 受控词表 + FTS 检索最佳实践）
**治理禁令**：`references/memory-governance.md`

---

## 六、脚本 (12个)

```
READONLY (5) — 只读分析
  analyze_hook        追读力 (钩子/爽点)
  analyze_rhythm      节奏 (等级/金币/感情线)
  report_panorama     全景报告 ← 章节文件 + MCP
  report_graph        关系图谱 ← MCP（v8.4 数据源迁到 MCP）
  archive_facts       事实归档 payload 生成（v8.4：只输出 MCP tool_calls，不写文件）
  import_state_to_mcp 老项目一次性迁移（生成 MCP tool_calls）

SAFE_WRITE (2) — 幂等/可回滚
  split_paragraphs    段落拆分 (.bak备份)
  fix_dashes          B02 破折号四类上下文修复 (.bak备份)

EXPORT_ONLY (1)
  export              多平台导出

CAUTION (1)
  audit               统一审计 (默认 --verify 只读)

INFRA (1)
  lib                 共享工具（含 ensure_git_snapshot 快照钩子）

DEPRECATED (1) — v8.4 已停用
  render_tracking     v8.3 tracking/*.md 派生器；v8.4 起 tracking 层已废
```

> 润色能力（原 `polish.py`）自 v8.3 迁移到 **novel-pipeline** skill 的 `scripts/polish_chapter.py`。writer 通过 `references/style-transfer.md` 调用；文风预设仍在 writer 侧 `references/presets/`。

---

## 七、禁令速查

```
P0 阻塞 (6): B01对话「」 B02禁止—— B03不是…而是… B04元叙事 B05 AI高频词 B11章节正文禁用Markdown格式
P1 强制 (4): B06 ≤42字/段 B07 ≥2500字/章 B08 禁止脚本注入 B09 ≤5章/批
P2 建议 (1): B10 卷间衔接
```

详见 `references/hard-bans.md`（单一事实来源）。

---

## 八、协作 Skill：novel-pipeline

| 能力 | writer | novel-pipeline |
|---|---|---|
| 项目初始化、大纲、写章、审查、发布 | ✅ | — |
| **`novel_project` MCP 归档** | ✅ archive_facts.py（生成 payload → Agent 调 MCP）| ❌ |
| 批量豆包润色 | 不自持 | ✅ `polish_chapter.py` |
| DeepSeek 批量出稿 | 调本 skill MCP | ✅ `novel-deepseek MCP` |
| Git 前置快照 | ✅ `lib.ensure_git_snapshot`（写章/修复）| ✅ 内置（润色）|

**项目根统一识别**：`novel.json`（首选）/ `writer.json` / `novel-pipeline.json`。章节文件统一 `ch_NNN.md`。

---

## 九、关键数字

| 指标 | 数值 |
|------|------|
| 脚本 | 12 (R:5, SW:2, E:1, C:1, I:1, DEP:1, + archive_facts / import_state_to_mcp / lib) |
| Agent | 4 (story-architect / consistency-checker / narrative-writer / character-designer) |
| 路由 | 31 |
| 审查模式 | 10 (6 自动替代升级 + 4 人工) |
| 禁令 | 11 (P0:6, P1:4, P2:1) |
| 使用场景 | 8 (见 SKILL.md 「使用场景全景」章节) |
| 段落上限 | 42 汉字 |
| 字数下限 | 2500 汉字 |
| 子代理批次 | ≤5章(写) / ≤40章(审) |
| MCP 工具 | 8（详见 references/memory-mcp.md） |
| skill_version | 8.5 |

---

## 十、v8.5 关键变更

1. **B11 Markdown 零容忍**：章节正文禁止加粗、反引号代码、链接、HTML 标签、分隔线、正文内 Markdown 标题等格式污染
2. **audit 参考池修复**：模板复制检测只比较当前章之前的 3 章，避免自比误报

## 十一、v8.4 关键变更

1. **迁记忆层至 novel_project MCP**：`.writer/state/*.json` 四份原子事实文件、`tracking/*.md` 派生层**全部废除**
2. **archive_facts.py 从 SAFE_WRITE 改为 READONLY**：只生成 MCP tool_calls 序列，不写任何 JSON
3. **新增 import_state_to_mcp.py**：老项目一次性迁移（老 `.writer/state/*.json` → MCP）
4. **新增 references/memory-mcp.md**：8 个 MCP 工具目录 + entityType/relations 受控词表 + 覆盖式陷阱 + FTS 检索最佳实践
5. **render_tracking.py deprecated**：tracking/*.md 派生逻辑已废，人读快照按需用 `report_graph.py` 从 MCP 生成
6. **project-init 骨架精简**：不再创建 `.writer/state/`、不再创建 `tracking/`，改为 seed MCP 首批实体
7. **审查报告增加 MCP 覆盖率维度**：健康评分含 MCP 归档完整度

## v8.3 关键变更（保留背景）

1. 删除 memory-novel MCP 依赖（改用 `.writer/state/*.json`，v8.4 又迁回 MCP）
2. 四层写权限设计（state/tracking/setting/chapters，v8.4 简化为三层）
3. archive_facts.py / render_tracking.py（v8.4 前者改造后者废）
4. 协作 novel-pipeline v3.4+：润色/出稿委托
5. 章节命名统一 ch_NNN.md
6. 项目根三 marker 兼容：novel.json > writer.json > novel-pipeline.json
