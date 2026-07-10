# Writer Skill 架构全景图

> v8.3 · 2026-07-10 — 四层写权限架构，novel-pipeline 协作模式

---

## 一、规模

```
writer/                     ~ 380 KB / 47 文件
├── SKILL.md              700+ 行  入口 + 8 场景 + 路由 + 禁令速查 + 协作说明
├── WORKFLOW.md           170 行   完整答题流程（10 阶段）
├── ARCHITECTURE.md              本文件
├── CHANGELOG.md                  版本历史
├── .gitignore
├── references/           ~ 25 文件  AI 执行指令
├── agents/               4 文件    Full 审查子代理
├── scripts/              12 文件   Python 工具（含 archive_facts / render_tracking / lib.ensure_git_snapshot）
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

写章 Step 5:  archive_facts.py → .writer/state/*.json（原子事实追加）
             render_tracking.py → tracking/*.md（人读派生，保留 user-edit 块）

批量润色:      交给 novel-pipeline skill polish_chapter.py（豆包 MCP + git 快照 + 断点续传）
批量出稿:      交给 novel-pipeline skill novel-deepseek MCP.generate_draft
```

---

## 三、四层写权限（v8.3 核心架构）

```
{project}/
├── novel.json                # 项目元数据
├── setting/*.md              # 【用户领地】静态约束（世界观/角色/战力/势力/writing_rules）
├── outline/                  # 【用户 + Agent 协作】大纲
├── chapters/                 # 【Agent 主写】正文 ch_NNN.md
├── tracking/*.md             # 【Agent 派生渲染】人读快照 + 用户 <!-- user-edit --> 块
└── .writer/
    ├── state/*.json          # 【Agent 独写】原子事实源（archive_facts.py 写入）
    ├── project_memory.json   # skill 学到的项目习惯
    └── runtime/              # 临时文件（.gitignore）
```

| 层 | 写方 | 改方 | 用途 |
|---|---|---|---|
| `.writer/state/*.json` | Agent 独写 | 只 Agent | 原子事实 |
| `tracking/*.md` | Agent 派生 | 用户 user-edit 块可补 | 人读快照 |
| `setting/*.md` | Agent 初始 + 用户改 | 用户为主 | 静态约束 |
| `chapters/*.md` | Agent 主写 | 用户可修 | 正文 |
| `outline/*.md` | Agent 生成 + 用户改 | 双方 | 大纲 |

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

审查读取源：`.writer/state/*.json`（当前事实）+ `setting/*.md`（原始设定）+ `chapters/*.md`（正文）+ `outline/*.md`（大纲计划），四方交叉对比。

---

## 五、状态归档链（v8.3 替代 memory-novel MCP）

```
写章 Step 3 完成 → chapters/ch_NNN.md 落盘
                ↓
       Agent 分析变更 → 构造 JSON payload
                ↓
       stdin ─→ archive_facts.py
                ↓
                ├─ .writer/state/characters.json（增量合并 + 版本自增）
                ├─ .writer/state/foreshadowing.json（active 新增 / resolved 转移）
                ├─ .writer/state/power_system.json
                ├─ .writer/state/world_setting.json
                └─ .bak 备份（每份 JSON 写前自动）
                ↓
       render_tracking.py
                ↓
                ├─ 读现有 tracking/*.md 提取 <!-- user-edit --> 块
                ├─ 从 state JSON 重新渲染表格/列表
                ├─ 把 user-edit 块按锚点回填
                └─ .md.bak 备份
```

**关键设计**：
- state JSON = 机读源（结构化，Agent 归档准确，可 diff）
- tracking md = 人读快照（Agent 派生，用户可在 `<!-- user-edit -->` 块内补规划意图）
- setting md = 静态约束（用户手写，写章前 Agent 加载）
- 三层职责清晰不重合

---

## 六、脚本 (12个)

```
READONLY (4) — 只读分析
  analyze_hook        追读力 (钩子/爽点)
  analyze_rhythm      节奏 (等级/金币/感情线)
  report_panorama     全景报告 ← 章节文件 + tracking/
  report_graph        关系图谱 ← 章节文件 + tracking/

SAFE_WRITE (4) — 幂等/可回滚
  split_paragraphs    段落拆分 (.bak备份)
  fix_dashes          B02 破折号四类上下文修复 (.bak备份)
  archive_facts       事实归档到 .writer/state/*.json (.bak 备份 + 版本自增)
  render_tracking     从 state JSON 派生 tracking md (.md.bak 备份 + user-edit 块保护)

EXPORT_ONLY (1)
  export              多平台导出

CAUTION (1)
  audit               统一审计 (默认 --verify 只读)

INFRA (1)
  lib                 共享工具（含 ensure_git_snapshot 快照钩子）
```

> 润色能力（原 `polish.py`）自 v8.3 迁移到 **novel-pipeline** skill 的 `scripts/polish_chapter.py`。writer 通过 `references/style-transfer.md` 调用；文风预设仍在 writer 侧 `references/presets/`。

---

## 七、禁令速查

```
P0 阻塞 (5): B01对话「」 B02禁止—— B03不是…而是… B04元叙事 B05 AI高频词
P1 强制 (4): B06 ≤42字/段 B07 ≥2500字/章 B08 禁止脚本注入 B09 ≤5章/批
P2 建议 (1): B10 卷间衔接
```

详见 `references/hard-bans.md`（单一事实来源）。

---

## 八、协作 Skill：novel-pipeline

| 能力 | writer | novel-pipeline |
|---|---|---|
| 项目初始化、大纲、写章、审查、发布 | ✅ | — |
| 状态归档（`.writer/state/*.json`）| ✅ archive_facts.py | ❌ |
| tracking 派生（`tracking/*.md`）| ✅ render_tracking.py | ❌ |
| 批量豆包润色 | 不自持 | ✅ `polish_chapter.py` |
| DeepSeek 批量出稿 | 调本 skill MCP | ✅ `novel-deepseek MCP` |
| Git 前置快照 | ✅ `lib.ensure_git_snapshot`（写章/修复）| ✅ 内置（润色）|

**项目根统一识别**：`novel.json`（首选）/ `writer.json` / `novel-pipeline.json`。章节文件统一 `ch_NNN.md`。

---

## 九、关键数字

| 指标 | 数值 |
|------|------|
| 脚本 | 12 (R:4, SW:4, E:1, C:1, I:1, + archive_facts / render_tracking / lib) |
| Agent | 4 (story-architect / consistency-checker / narrative-writer / character-designer) |
| 路由 | 31 |
| 审查模式 | 10 (6 自动替代升级 + 4 人工) |
| 禁令 | 10 (P0:5, P1:4, P2:1) |
| 使用场景 | 8 (见 SKILL.md 「使用场景全景」章节) |
| 段落上限 | 42 汉字 |
| 字数下限 | 2500 汉字 |
| 子代理批次 | ≤5章(写) / ≤40章(审) |
| skill_version | 8.3 |

---

## 十、v8.3 关键变更

1. **删除 memory-novel MCP 依赖**：所有原来"知识图谱"的功能改由 `.writer/state/*.json` + `archive_facts.py` 承担
2. **删除 publishready / firstory / uno MCP 依赖**：所有审查/质检回归本地 audit.py + 主 Agent 判断
3. **新增四层写权限**：state/tracking/setting/chapters 职责清晰不重合
4. **新增 archive_facts.py / render_tracking.py**：状态归档链本地化
5. **协作 novel-pipeline v3.4+**：润色/出稿委托，writer 专注编辑/审查/发布
6. **章节命名统一 ch_NNN.md**：与 novel-pipeline 一致
7. **项目根三 marker 兼容**：novel.json > writer.json > novel-pipeline.json
