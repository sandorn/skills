# Writer Skill 架构全景图

> v7.9 final | 2026-06-30 — 5 轮审查完成，零污染，零断裂引用

---

## 一、规模

```
writer/                        380 KB / 48 文件
├── SKILL.md                456行  22KB  入口 + 路由 + 禁令速查 + 安全策略
├── WORKFLOW.md              156行   7KB  完整答题流程
├── ARCHITECTURE.md          172行   7KB  本文件
├── REVIEW_TRIGGERS.md       104行   3KB  审查触发体系
├── RELEASE_REVIEW.md               4KB  发布评估
├── CHANGELOG.md                    3KB  版本历史
├── .gitignore                       -   已配置
├── references/           29+2 文件 185KB  AI 执行指令
├── agents/                4 文件  26KB  Full 审查子代理（已去重+编号）
├── scripts/              10 文件 120KB  Python 工具（安全标注+增强正则）
├── templates/             1 文件   5KB  审查报告模板
├── presets/               1 文件   2KB  文风预设
└── project-skeleton/     11 文件   5KB  新项目模板（已修复 60→42）
```

---

## 二、管线全景

```
扫榜→拆文→开书→大纲→写前检查→写章→审查→质检→发布
                        │           │      │
                  batch:对齐    daily:8维  quality:5步
                  single:自检   solo:15维  post-fix:判定
                               lean:27维
                               full:43维(4Agent)

审查替代升级:  daily(每章) → solo(每5章) → lean(每10章) → full(每卷)
              ↑ 嵌套包含，只运行最高级，不叠加
              longform(每100章) 与 full 叠加 — 正交维度

写章自动记录:  Step1→memory-novel read_graph(读状态) → Step3→MCP add_observations
              Step4→writer.json version update + 自动审查
质检/润色/修复: 完成后→writer.json version update + 自动审查

知识图谱: memory-novel MCP, 4实体/5关系, 写章自动维护, 全管线读写闭环
质量增强: publishready(AI腔审计) + firstory(OOC检测) + uno(叙事增强)
```

---

## 三、审查体系 (10项)

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
  master-outline         暗线审查/总纲对齐/大纲一致性/大纲有没有问题
```

---

## 四、知识图谱 (memory-novel MCP, 4实体/5关系)

memory-novel MCP (`@pepk/mcp-memory-sqlite`) 替代了原来的 SQLite fact_db。
它是运行 `npx @pepk/mcp-memory-sqlite` 的 stdio MCP 服务器。

### 数据模型
4 实体类型: Character / Chapter / Hook / Project
5 关系类型: loves / friends_with / hostile_to / family_of / mentors / appears_in / planted_in

实体存储 observations（每章状态快照），关系编码角色连接。
详见 `references/memory-novel-schema.md`

### 存储
SQLite 文件位于 `{project}/novel_memory_db/`（由 MEMORY_DB_DIR 环境变量设置）。

### 生命周期
- 自动创建：npx 在首次 write 时自动创建
- 写入点：write.Step3（Claude 通过 MCP 添加 observations）
- 读取点：write.Step1（Claude 通过 MCP 读取 graph/搜索节点）
- 章节正文直接来自文件系统（chapters/ch_NNN.md）

### 版本控制
4 阶段版本（draft → reviewed → polished → final）移至 writer.json。
`scripts/fact_db.py` 已删除，功能完全由 memory-novel MCP 替代。

---

## 五、脚本 (10个)

```
READONLY (4) — 只读分析
  analyze_hook        追读力 (钩子/爽点)
  analyze_rhythm      节奏 (等级/金币/感情线) ← 章节文件
  report_panorama     全景报告 ← 章节文件 + tracking/
  report_graph        关系图谱 ← 章节文件 + tracking/

SAFE_WRITE (1) — 仅操作独立数据文件
  split_paragraphs    段落拆分 (.bak备份)

EXPORT_ONLY (1)
  export              多平台导出

CAUTION (2)
  audit               统一审计 (默认--verify只读)
  polish              AI润色 (独立输出目录)

INFRA (1)
  lib                 共享工具
```

---

## 六、禁令速查

```
P0 阻塞 (5): B01对话「」 B02禁止—— B03不是…而是… B04元叙事 B05 AI高频词
P1 强制 (4): B06 ≤42字/段 B07 ≥2500字/章 B08 禁止脚本注入 B09 ≤5章/批
P2 建议 (1): B10 卷间衔接
```

---

## 七、路由表 (31条)

```
扫榜/排行榜          → scan              开书/初始化      → project-init
拆书/黄金三章        → analyze           导入/迁移        → project-init(import)
大纲/卷纲/章纲       → plan              写章/续写/日更    → write
批量写/连续写        → write(batch)      短篇            → write(short)
审查/审计            → review(6模式)     全面审查         → review-cycle(5步)
定向/专项审查        → targeted-audit    逐章/不用脚本    → review(manual)
质检/全线            → quality           去AI味           → quality(deslop)
纯手动润色/手工打磨  → manual-polish     文风转换/润色     → style-transfer
文风SOP/禁令         → style-sop         钩子/爽点分析    → analyze_hook
修复/有问题          → post-review-fix   开新卷/下一卷    → deploy
追读力/钩子强度      → analyze_hook      升级节奏/金币     → analyze_rhythm
声音漂移/情绪单调    → longform-quality  查询/查角色      → search_nodes MCP
设定审查/交叉        → setting-consistency 角色追踪       → track-character-state
暗线审查/总纲对齐    → master-outline    关系/图谱        → report_graph
全景/概览            → report_panorama   番茄投稿        → fanqie-submission
导出                → export            封面            → cover
备份                → git commit        段落拆分        → split_paragraphs
审查触发规则        → REVIEW_TRIGGERS    故障/报错       → troubleshooting
```

---

## 八、关键数字

| 指标 | 数值 |
|------|------|
| 总文件 | 48 |
| Reference | 29+2 (00-index + REVIEW_TRIGGERS) |
| 脚本 | 10 (R:4, SW:2, E:1, C:2, I:1) |
| Agent | 4 (去重:AI腔红线→narrative-writer独占, OOC→character-designer权威) |
| 路由 | 31 |
| 审查 | 10 (6自动+替代升级, 4人工) |
| 禁令 | 10 (P0:5, P1:4, P2:1) |
| 数据库表 | 9 (全自动读写闭环) |
| 段落上限 | 42 汉字 |
| 字数下限 | 2500 汉字 |
| 子代理批次 | ≤5章(写) / ≤40章(审) |
| writer.json | skill_version: "8.1" |
| 引用断裂 | 0 |
| 硬编码残留 | 0 |
| 作者教材 | 0 |
| 累计删除 | 12 文件 |
| 审查轮次 | 5 轮 |
| 实战验证 | 待进行 |
