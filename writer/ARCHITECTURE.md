# Writer Skill 架构全景图

> v7.8 | 2026-06-30 | 由 `SKILL.md` + 磁盘扫描生成

---

## 一、规模总览

```
writer/                        377 KB / 46 文件
├── SKILL.md                   445行  21KB  入口 + 路由 + 禁令速查 + 安全策略
├── CHANGELOG.md                       3KB   版本历史
├── ARCHITECTURE.md                     -   本文件
├── references/          30 文件 207KB  按需加载参考文档
├── agents/               4 文件  25KB  Full 审查子代理模板
├── scripts/             10 文件 116KB  Python 工具脚本
├── templates/            1 文件   5KB  审查报告模板
└── .gitignore
```

**v7.6 → v7.8 减法历程：** 39→30 references | 13→10 scripts | 34→30 路由 | 55→46 总文件

---

## 二、Reference 文件 (30个 — 按功能分组)

```
★ 核心管线 (11) — 每次写作预加载
  hard-bans.md             6KB  禁令单一事实来源 P0-P2
  review.md               15KB  43维审查 + 6模式 (quick/daily/solo/lean/full/manual)
  review-cycle.md          7KB  5步审查管线 (Step0-5)
  write.md                11KB  写作管线 (5步/9步/4步 + batch + short)
  write-pitfalls.md        9KB  批量写作避坑 (19项)
  quality.md              10KB  质检工单 (禁令→字数→审查→去AI味→验证)
  plan.md                  4KB  大纲规划 (总纲→卷纲→章纲)
  project-init.md          5KB  项目初始化 + import模式
  pre-write-alignment.md   7KB  批量写前总线对齐 (5层)
  pre-write-checklist.md   3KB  写前30秒检查清单
  manual-polish.md        31KB  纯手动润色 (三零原则 + 技法手册)

● 审查与审计 (5)
  targeted-audit.md       12KB  用户指定维度定向审查
  post-review-fix.md       4KB  审查后修复 (决策树 + 问题模式)
  hooks-scan.md            4KB  伏笔全卷扫描 (5级优先级)
  longform-quality-monitor.md 4KB  >100章质量趋势
  master-outline-audit.md  4KB  总纲暗线对齐

○ 一致性 (2)
  setting-consistency-audit.md 9KB  设定跨文件审计
  track-character-state.md     3KB  角色状态追踪

◆ 文风 (2)
  style-sop.md             6KB  文风SOP (6维接口)
  style-transfer.md        3KB  文风转换管线 → polish.py
  presets/fanqie-quick-anti.md 2KB  番茄风预设

▲ 工作流 (6)
  scan.md                  3KB  跨平台扫榜
  analyze.md               4KB  爆款拆解 + 黄金三章
  deploy.md                3KB  多卷部署 + 卷间衔接(B10)
  fanqie-submission.md     3KB  番茄投稿格式兼容
  cover.md                 3KB  封面生成
  optimize.md              5KB  钩子+爽点手工优化指南

▽ 工具与故障 (4)
  tool-pitfalls.md         5KB  通用工具陷阱
  tool-pitfalls-windows.md 7KB  Windows特有陷阱
  troubleshooting.md       1KB  故障排除速查
  encoding-fix-recipe.md   3KB  Git编码修复 (紧急参考)
```

---

## 三、Agent 模板 (4个 — Full 审查模式)

```
┌──────────────────────────────────────────────────────────────┐
│                     主会话 (汇总 + 裁决)                       │
│  冲突: 两Agent同维度判定不同 → 取更严格等级                     │
│  降级: >120s超时/连续2次失败 → lean/solo                       │
│  部分: 3/4成功→补做缺失维度 | ≤2/4成功→全部降级                 │
└────┬──────────────┬──────────────┬───────────────────────────┘
     │              │              │
┌────▼────────┐ ┌───▼────────┐ ┌──▼──────────────┐ ┌─────────▼──────┐
│story-architect│ │consistency │ │narrative-writer │ │character-      │
│D1-15,37-43   │ │D16-27      │ │D28-36+禁令+格式 │ │designer (按需) │
│First 5必检   │ │+ AI腔红线  │ │禁令3项优先      │ │触发: ≥3对话 or │
│ S1停止+降级  │ │First 3必检 │ │ S1停止+降级     │ │ 前次S2 OOC or │
│              │ │ S1停止+降级│ │                 │ │ >10角色+≥20章 │
└──────────────┘ └────────────┘ └─────────────────┘ └───────────────┘
```

---

## 四、脚本 (10个 — 按安全级别)

```
READONLY (5) — 只读分析，不修改任何文件
  analyze_hook.py     12KB  追读力分析 (钩子强度/爽点分布/钩力衰减)
  analyze_rhythm.py   13KB  节奏状态查询 (等级/金币/感情线/钩力趋势)
  fact_db.py          13KB  SQLite事实库 (6表, init/query/insert/status)
  report_panorama.py  14KB  项目全景报告 (健康评分+建议)
  report_graph.py     13KB  实体关系图谱 (Mermaid输出, 动态角色加载)

SAFE_WRITE (1) — 修改文件但自动 .bak，不涉及文本替换
  split_paragraphs.py  6KB  段落拆分 (按句号, ≤42汉字, 自动.bak)

EXPORT_ONLY (1) — 写入独立输出目录，不动源文件
  export.py            8KB  多平台格式导出 (番茄/起点/飞卢)

CAUTION (2) — 需确认后运行
  audit.py            10KB  统一审计 (默认 --verify 只读, --fix-escaped 仅修转义)
  polish.py           21KB  AI润色 (API调用, 输出到独立目录, 断点续传)

INFRA (1)
  lib.py               9KB  共享工具模块 (count_chinese, safe_write, ...)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
已删除 (v7.7-v7.8):
  pad_chapter.py     → 字数注入器, 改为手工扩充
  audit_5dim.py      → 功能集成到 audit.py
  backup.py          → 改为 git commit
```

---

## 五、管线全景图

```
                    ┌─────────────┐
                    │ 扫榜 (scan)  │
                    │ 拆文 (analyze)│
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ 开书/导入    │
                    │(project-init)│
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ 大纲 (plan)  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼──────┐ ┌──▼─────────┐  │
     │ 写前对齐(batch)│ │写前自检(单章)│  │
     │(pre-write-    │ │(pre-write-  │  │
     │ alignment)    │ │ checklist)  │  │
     └────────┬──────┘ └──┬─────────┘  │
              │            │            │
     ┌────────▼────────────▼───────────▼──┐
     │           写章 (write)              │
     │  单章: Plan→Architect→Write→Audit→Revise │
     │  批量: 预对齐→子代理(≤5章)→质检+修复    │
     └────────────────┬──────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
  ┌─────▼──────┐ ┌───▼────┐ ┌─────▼──────┐
  │日更审查     │ │审查    │ │全面审查     │
  │daily 8维   │ │solo/   │ │review-cycle│
  │3min发布闸  │ │lean    │ │5步管线     │
  └─────┬──────┘ └───┬────┘ └─────┬──────┘
        │             │             │
  ┌─────▼──────┐ ┌───▼────┐ ┌─────▼──────┐
  │ 可发布?    │ │质检    │ │修复        │
  │ (daily     │ │(quality│ │(post-      │
  │  内嵌)     │ │ 5步)   │ │ review-fix)│
  └────────────┘ └────────┘ └────────────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
  ┌─────▼──────┐ ┌───▼────┐ ┌─────▼──────┐
  │纯手动润色   │ │文风转换 │ │钩子/爽点    │
  │(manual-    │ │(style-  │ │优化        │
  │ polish)    │ │transfer)│ │(optimize)  │
  │三零原则    │ │→polish  │ │            │
  └────────────┘ └────────┘ └────────────┘
```

---

## 六、禁令体系

```
               ┌──────────────┐
               │ hard-bans.md │ ← 单一事实来源
               │  P0-P2 分级   │
               └──────┬───────┘
      ┌───────────────┼───────────────┐
      │               │               │
┌─────▼─────┐  ┌──────▼──────┐  ┌────▼─────┐
│ P0 阻塞(5)│  │ P1 强制(4)  │  │P2 建议(1)│
│ 有一条即   │  │ 批量阻断    │  │ 允许例外  │
│ 不可发布   │  │ 日更warning │  │          │
└─────┬─────┘  └──────┬──────┘  └────┬─────┘
      │               │               │
  B01 对话「」    B06 每段≤42字    B10 卷间衔接
  B02 禁止——      B07 每章≥2500字
  B03 不是…而是…  B08 禁止脚本注入文本
  B04 元叙事标签  B09 子代理≤5章/批
  B05 AI高频词(8词)
```

---

## 七、路由表 (30条)

```
触发词                              → 路由
──────────────────────────────────────────────────────────
扫榜/排行榜/什么火                  → scan.md
拆书/黄金三章/深度拆解              → analyze.md
开书/新书/初始化/创建项目           → project-init.md
导入小说/迁移                       → project-init.md (import)
大纲/卷纲/章纲/规划                 → plan.md
写前检查 (批量→对齐, 单章→自检)     → pre-write-alignment / pre-write-checklist
写第N章/续写/日更                   → write.md
批量写/写N章/连续写                 → write.md (batch)
短篇/写个故事                       → write.md (short)
审查/审稿/审计 (>20章→全面审查)     → review.md (6模式)
全面审查/全量审查/深度审查          → review-cycle.md (5步)
定向审查/专项审查                   → targeted-audit.md
逐章检查/不用脚本/一章一章过        → review.md (manual-pass)
质检/全线检查                       → quality.md
去AI味/太AI了                       → quality.md (deslop)
纯手动润色/逐章逐段润色/手工打磨    → manual-polish.md
文风转换/转写/润色/批量润色         → style-transfer.md → polish.py
文风SOP/文风参数/禁令清单           → style-sop.md
钩子强度/爽点优化                   → optimize.md
修一下/修复/帮我修/有问题           → post-review-fix.md → quality.md
开新卷/第二卷/下一卷                → deploy.md
追读力/钩子强度/爽点分析            → analyze_hook.py
升级节奏/金币趋势/感情线            → analyze_rhythm.py
声音漂移/风格指纹/情绪单调          → longform-quality-monitor.md
查角色/查伏笔/等级查询/什么状态     → fact_db.py query
设定审查/交叉审查                   → setting-consistency-audit.md
更新角色状态/角色追踪               → track-character-state.md
关系/图谱/谁和谁                    → report_graph.py
全景/概览/项目状态                  → report_panorama.py
番茄投稿/格式兼容                   → fanqie-submission.md
导出/起点格式/番茄格式              → export.py
封面/生成封面                       → cover.md
备份/存档                           → git commit
段落太长/拆分段落                   → split_paragraphs.py
报错/不工作/问题/怎么办             → troubleshooting.md
帮助/功能/命令                      → 列出路由表
```

---

## 八、脚本依赖图

```
                 ┌─────────┐
                 │ lib.py  │ ← INFRA (全脚本基础依赖)
                 └────┬────┘
      ┌───────────────┼───────────────────┐
      │               │                   │
 ┌────▼────┐   ┌──────▼──────┐   ┌───────▼───────┐
 │audit.py │   │split_para-  │   │report_panorama│
 │CAUTION  │   │graphs.py    │   │  READONLY     │
 │默认--verify│ │SAFE_WRITE   │   └───────────────┘
 └────┬────┘   └──────┬──────┘
      │               │
 ┌────▼────┐   ┌──────▼──────┐   ┌───────────────┐
 │analyze_ │   │analyze_     │   │report_graph   │
 │hook.py  │   │rhythm.py    │   │  READONLY     │
 │READONLY │   │READONLY     │   └───────────────┘
 └─────────┘   └────┬────────┘
                    │
               ┌────▼────┐
               │fact_db  │
               │READONLY │
               └─────────┘

  export.py      EXPORT_ONLY  ← lib
  polish.py      CAUTION      ← standalone (OpenAI兼容API)
```

---

## 九、文件大小分布

```
manual-polish.md       31KB ██████████████████████████████
review.md              15KB ███████████████
targeted-audit.md      12KB ████████████
write.md               11KB ███████████
quality.md             10KB ██████████
write-pitfalls.md       9KB █████████
setting-consistency.md  9KB █████████
review-cycle.md         7KB ███████
tool-pitfalls-win.md    7KB ███████
pre-write-alignment.md  7KB ███████
style-sop.md            6KB ██████
hard-bans.md            6KB ██████
optimize.md             5KB █████
tool-pitfalls.md        5KB █████
project-init.md         5KB █████
其余 15 文件           ≤4KB each
```

---

## 十、关键数字

| 指标 | 数值 |
|------|------|
| 总文件数 | 46 |
| 总大小 | 377 KB |
| SKILL.md | 445 行 / 21 KB |
| Reference | 30 文件 / 207 KB |
| Agent 模板 | 4 文件 / 25 KB |
| Python 脚本 | 10 文件 / 116 KB |
| 路由条目 | 30 |
| 审查维度 | 43 (分4 Agent) |
| 禁令 | 10条 (P0:5, P1:4, P2:1) |
| 写章步骤 | 5(默认) / 9(full) / 4(fast) |
| 审查模式 | 6 (quick/daily/solo/lean/full/manual) |
| 段落上限 | **42** 汉字 |
| 字数下限 | **2500** 汉字 |
| 子代理批次 | ≤5章(写) / ≤40章(审) |
| 累计已删 | **11 文件** (3脚本 + 8参考) |
