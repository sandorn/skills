# Writer Skill 架构全景图

> v7.8 final | 2026-06-30

---

## 一、规模

```
writer/
├── SKILL.md                443行  22KB  入口 + 路由 + 禁令速查 + 安全策略
├── references/        29 文件 176KB  AI 执行指令（零作者教材）
├── agents/             4 文件  26KB  Full 审查子代理模板
├── scripts/           10 文件 120KB  Python 工具（全部标注安全级别）
├── templates/          1 文件   4KB  审查报告模板
└── presets/            1 文件   2KB  文风预设
```

---

## 二、Reference 文件 (29个)

```
★ 核心管线 (11)
  hard-bans.md             6KB  禁令 P0-P2 (单一事实来源)
  review.md               15KB  43维审查 + 6模式
  review-cycle.md          7KB  5步审查管线
  write.md                11KB  写作管线 (5步/9步/4步 + batch + short)
  write-pitfalls.md        9KB  批量写作避坑
  quality.md              10KB  质检工单 (5步)
  plan.md                  4KB  大纲规划
  project-init.md          5KB  项目初始化 + import
  pre-write-alignment.md   7KB  批量写前总线对齐
  pre-write-checklist.md   3KB  写前30秒检查
  manual-polish.md        18KB  纯手动润色 (AI执行指令，已净化作者教材)

● 审查与审计 (5)
  targeted-audit.md       12KB  定向审查
  post-review-fix.md       4KB  审查后修复 (判定+策略)
  hooks-scan.md            4KB  伏笔全卷扫描
  longform-quality-monitor.md 4KB  >100章质量趋势
  master-outline-audit.md  4KB  总纲暗线对齐

○ 一致性 (2)
  setting-consistency-audit.md 9KB  设定跨文件审计
  track-character-state.md     3KB  角色状态追踪

◆ 文风 (2)
  style-sop.md             6KB  文风SOP (6维接口)
  style-transfer.md        3KB  文风转换管线 → polish.py

▲ 工作流 (5)
  scan.md                  3KB  跨平台扫榜
  analyze.md               4KB  爆款拆解
  deploy.md                3KB  多卷部署 + 卷间衔接
  fanqie-submission.md     3KB  番茄投稿检查
  cover.md                 3KB  封面生成

▽ 工具 (4)
  tool-pitfalls.md         5KB  通用工具陷阱
  tool-pitfalls-windows.md 7KB  Windows特有陷阱
  troubleshooting.md       1KB  故障排除
  encoding-fix-recipe.md   3KB  Git编码修复 (紧急)
```

---

## 三、Agent 模板 (4个)

```
story-architect      D1-15,37-43 | First 5必检 | S1停止 | 降级协议
consistency-checker  D16-27 + AI腔红线 | First 3必检 | S1停止 | 降级协议
narrative-writer     D28-36 + 禁令3项 + 格式 | S1停止 | 降级协议
character-designer   角色+对话 | 按需(4条件) | S1停止 | 降级协议

冲突裁决: 两Agent同维度判定不同 → 取更严格等级
降级兜底: >120s超时/连续2次失败 → lean/solo
         3/4成功→补做缺失维度 | ≤2/4成功→全部降级
```

---

## 四、脚本 (10个)

```
READONLY (5) — 只读分析
  analyze_hook        追读力分析 (钩子/爽点)
  analyze_rhythm      节奏查询 (等级/金币/感情线)
  fact_db             SQLite事实库 (6表)
  report_panorama     项目全景报告
  report_graph        实体关系图谱 (Mermaid)

SAFE_WRITE (1) — 修改但.bak备份
  split_paragraphs    段落拆分 (按句号, ≤42汉字)

EXPORT_ONLY (1) — 独立输出目录
  export              多平台导出 (番茄/起点/飞卢)

CAUTION (2) — 需确认
  audit               统一审计 (默认--verify只读, --fix-escaped仅修转义)
  polish              AI润色 (API, 独立输出目录, 断点续传)

INFRA (1)
  lib                 共享工具 (count_chinese, safe_write, ...)
```

---

## 五、管线全景

```
扫榜→拆文→开书→大纲→写前检查→写章→审查→质检
                        │           │      │
                  batch:对齐    daily:8维  quality:5步
                  single:自检   solo:15维  post-fix:判定
                               full:43维(4Agent)

润色: style-transfer(API批量) | manual-polish(零脚本逐章)
```

---

## 六、禁令速查

```
P0 阻塞 (有一条即不可发布):
  B01 对话「」  B02 禁止——  B03 不是…而是…
  B04 元叙事    B05 AI高频词(8词)

P1 强制:
  B06 ≤42字/段  B07 ≥2500字/章
  B08 禁止脚本注入文本  B09 子代理≤5章/批

P2 建议:
  B10 卷间衔接检查
```

---

## 七、路由表 (29条)

```
扫榜/排行榜          → scan           开书/初始化      → project-init
拆书/黄金三章        → analyze        导入/迁移        → project-init(import)
大纲/卷纲/章纲       → plan           写章/续写/日更    → write
批量写/连续写        → write(batch)   短篇            → write(short)
审查/审计            → review(6模式)  全面审查         → review-cycle(5步)
定向/专项审查        → targeted-audit 逐章/不用脚本    → review(manual)
质检/全线            → quality        去AI味           → quality(deslop)
纯手动润色/手工打磨  → manual-polish  文风转换/润色     → style-transfer
文风SOP/禁令         → style-sop      钩子/爽点分析    → analyze_hook
修复/有问题          → post-review-fix 开新卷/下一卷    → deploy
追读力/钩子强度      → analyze_hook    升级节奏/金币     → analyze_rhythm
声音漂移/情绪单调    → longform-quality 查询/查角色     → fact_db query
设定审查/交叉        → setting-consistency  角色追踪    → track-character-state
关系/图谱            → report_graph    全景/概览       → report_panorama
番茄投稿            → fanqie-submission 导出           → export
封面                → cover           备份            → git commit
段落拆分            → split_paragraphs 故障/报错       → troubleshooting
```

---

## 八、关键数字

| 指标 | 数值 |
|------|------|
| 总文件 | 46 |
| Reference | 29 |
| 脚本 | 10 (R:5, SW:1, E:1, C:2, I:1) |
| 路由 | 29 |
| 审查维度 | 43 (4 Agent) |
| 禁令 | 10 (P0:5, P1:4, P2:1) |
| 段落上限 | 42 汉字 |
| 字数下限 | 2500 汉字 |
| 子代理批次 | ≤5章(写) / ≤40章(审) |
| 引用断裂 | 0 |
| 作者教材 | 0 |
| 累计删除 | 12 文件 |

---

## 九、减法历程

```
v7.6 → v7.8 final:
  删除脚本: pad_chapter, audit_5dim, backup
  删除参考: optimize, opening-craft, project-knowledge-base,
            corruption-fix-bu-shi, publishable-check, memory,
            fix-template-cleanup, setting-audit-gaming-manifest,
            project-review-novel-gaming-manifest
  净化: manual-polish 砍 41% 作者教材
  修复: 所有 pad_chapter 残留引用清零
  路由: 34→29 (合并6对重叠, 补6缺口, 删4死路由)
```
