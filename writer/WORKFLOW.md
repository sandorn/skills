# Writer Skill 完整答题流程

> 从一个新选题开始，模拟使用本 skill 的端到端流程。
> 每个阶段标注激活词、自动行为、数据库操作。

---

## 阶段一：市场调研

### 扫榜
```
用户:「最近都市重生文什么比较火」
```
> 路由: `scan.md` — 跨平台扫榜 + 趋势分析

### 拆文
```
用户:「拆一下排行第一的那本书」
```
> 路由: `analyze.md` — 爆款拆解 + 黄金三章

---

## 阶段二：项目创建

```
用户:「帮我开一本都市重生文，主角回到2001年开网吧」
```
> 路由: `project-init.md`
> 自动: 创建目录 → 生成 writer.json → 复制设定模板 → **fact_db.py init**（初始化数据库）

---

## 阶段三：大纲规划

```
用户:「帮我规划大纲，写三卷每卷60章」
```
> 路由: `plan.md`
> 自动: 总纲→卷纲→章纲
> 建议: 多卷大纲完成后运行「暗线都落地了吗」→ master-outline-audit.md

---

## 阶段四：写前检查

```
用户:「写前检查」（批量自动走 pre-write-alignment，单章走 pre-write-checklist）
```
> 自动: 批量→5层总线对齐 | 单章→30秒自检

---

## 阶段五：写章

### 单章
```
用户:「写下一章」
```
> 路由: `write.md`（5步管线）
> **Step 1**: 从 fact_db 读取上一章状态（等级/金币/角色/伏笔）
> **Step 3**: 写正文 → **自动 sync**（提取事实）→ **自动 mirror**（镜像正文）→ **自动 version draft**（保存快照）
> **Step 4**: 审计 → **自动 mirror**（修复后同步）→ **自动 version reviewed** → **自动 daily 审查**

### 批量
```
用户:「批量写3章」
```
> 路由: `write.md`（batch）
> 自动: ①预对齐 → ②子代理并行(≤5章) → ③质检+修复 → ④按章节数自动升级审查

### 自动审查（写后自动激发，不等待用户）
```
每章:   daily(8维)           ← 替代 quick
每5章:  solo(15维)           ← 替代 daily
每10章: lean(27维)           ← 替代 solo
每卷:   full(43维,4Agent)    ← 替代 lean
每100章:full + longform      ← longform 独立叠加
```

---

## 阶段六：审查（人工触发）

```
用户:「审查一下」          → review.md（≤20章）
用户:「全面审查」          → review-cycle.md（>20章, 5步管线）
用户:「定向审查感情线」    → targeted-audit.md（用户指定维度）
用户:「逐章检查，不用脚本」→ manual-pass（零脚本/零子代理）
用户:「设定审查」          → setting-consistency-audit.md（跨文件一致性）
用户:「暗线都落地了吗」    → master-outline-audit.md（总纲卷纲对齐）
```

---

## 阶段七：质检与修复

```
用户:「质检」              → quality.md（5步全链路）
用户:「太AI了」            → quality.md（deslop 去AI味）
用户:「修一下」            → post-review-fix.md（判定）→ quality.md（执行）
```
> 自动: 修复后 → mirror+version → re-audit 验证

---

## 阶段八：润色

```
用户:「转成番茄风」        → style-transfer.md → polish.py（API批量）
用户:「纯手动润色」        → manual-polish.md（三零原则）
```
> 自动: 润色后 → mirror+version → **自动 daily 审查**（润色可能引入新问题）

---

## 阶段九：发布

```
用户:「番茄投稿检查」      → fanqie-submission.md
用户:「导出起点格式」      → export.py
用户:「生成封面」          → cover.md
用户:「备份」              → git commit
```
> 可发布判定: daily 审查通过 = 可发布（publishable-check 已合并到 daily）

---

## 阶段十：持续维护

```
用户:「开第二卷」          → deploy.md（卷间衔接7维检查）
用户:「全景报告」          → report_panorama.py
用户:「查一下主角等级」    → fact_db.py query（从数据库秒回）
用户:「追读力怎么样」      → analyze_hook.py
用户:「升级是不是太慢了」  → analyze_rhythm.py（从 fact_db 读趋势）
用户:「角色关系图谱」      → report_graph.py（从 fact_db 读关系）
用户:「有没有声音漂移」    → longform-quality-monitor.md（>100章时）
用户:「更新角色状态」      → track-character-state.md
用户:「报错了」            → troubleshooting.md
```

---

## 全自动行为总结

| 触发 | 自动行为 |
|------|---------|
| 创建项目 | fact_db init（建表） |
| 每章写前 | fact_db query（读上一章状态） |
| 每章写后 | sync（提取事实）+ mirror（镜像正文）+ version draft（快照） |
| 每章审计后 | mirror（同步修复）+ version reviewed + daily 审查 |
| 每5/10/卷 | solo/lean/full 审查（替代升级） |
| 每100章 | full + longform-quality（叠加） |
| 质检/润色/修复后 | mirror + version + re-audit |
| 审查命中blocking | 立即停止 → 修复 → 重跑 → 通过后继续 |
