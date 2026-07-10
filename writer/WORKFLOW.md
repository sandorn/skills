# Writer Skill 完整答题流程

> 从一个新选题开始，模拟使用本 skill 的端到端流程。
> 每个阶段标注激活词、自动行为、状态归档。

**架构版本**：v8.3（协作 novel-pipeline，四层写权限：`.writer/state/*.json` / `tracking/*.md` / `setting/*.md` / `chapters/*.md`）

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
> 自动: 交互 4 波次 → 创建目录 → 生成 novel.json → 复制 setting/*.md 模板 → 建 `.writer/state/*.json` 空骨架（4 份 JSON）

**产物**：
```
{project}/
├── novel.json            # 项目根（首选命名）
├── setting/              # 4 份 md（story_bible/characters/power_system/factions）+ writing_rules.md
├── outline/              # 空（等 plan 阶段）
├── chapters/             # 空
├── tracking/             # 空（第一次写章后由 render_tracking.py 生成）
└── .writer/
    ├── state/            # 4 份空 JSON（{"version": 1, ...: []}）
    └── runtime/
```

---

## 阶段三：大纲规划

```
用户:「帮我规划大纲，写三卷每卷60章」
```
> 路由: `plan.md`
> 自动: 总纲 → 卷纲 → 章纲（`outline/chapter_outline/ch_NNN.md`）

---

## 阶段四：写前检查

```
用户:「写前检查」（批量自动走 pre-write-alignment，单章走 pre-write-checklist）
```
> 自动: 批量 → 5 层总线对齐 | 单章 → 30 秒自检

---

## 阶段五：写章

### 单章（主 Agent 亲写）
```
用户:「写下一章」
```
> 路由: `write.md`（5步管线）
> **Step 1**: 读 `.writer/state/*.json`（原子事实）+ `setting/*.md` + `outline/` + `tracking/*.md`（含 user-edit 块）
> **Step 3**: 写正文 → `chapters/ch_NNN.md`
> **Step 5**: `archive_facts.py` 追加事实到 `.writer/state/*.json` → `render_tracking.py` 派生 `tracking/*.md` → 更新 `novel.json`
> **审查**: 自动 daily 8 维

### 批量（writer 主 Agent 直写，≤5 章/批）
```
用户:「批量写3章」
```
> 路由: `write.md`（batch）
> 自动: ① 预对齐 → ② 子代理并行 → ③ 每章各自跑 Step 5 → ④ 批次末尾 solo 审查

### 批量（novel-pipeline 出初稿）
```
用户:「用 DeepSeek 帮我批量出 30 章初稿」
```
> 路由: `write.md` + **novel-pipeline** `novel-deepseek MCP.generate_draft`
> 主 Agent 读章纲 + `.writer/state/*.json` → 调 MCP → 收初稿 → 落 `chapters/*.md` → Step 5 归档

### 自动审查升级（写后按章节数触发，替代升级）
```
每章:   daily(8维)
每5章:  solo(15维)     ← 替代 daily
每10章: lean(27维)      ← 替代 solo
每卷:   full(43维,4Agent) ← 替代 lean
每100章:full + longform  ← longform 叠加
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

**交叉源**：审查读 `.writer/state/*.json`（当前事实）+ `setting/*.md`（原始设定）+ `chapters/*.md`（正文）+ `outline/*.md`（大纲计划），四方交叉对比。

---

## 阶段七：质检与修复

```
用户:「质检」              → quality.md（5步全链路）
用户:「太AI了」            → quality.md（deslop 去AI味）
用户:「修一下」            → post-review-fix.md（判定）→ quality.md（执行）
```
> 自动: 修复后 → git 快照（`lib.ensure_git_snapshot`）→ re-audit 验证

---

## 阶段八：润色

### 主 Agent 手动润色
```
用户:「纯手动润色」        → manual-polish.md（三零原则：零脚本/零子代理/零批量替换）
```

### 批量豆包润色（novel-pipeline 主导）
```
用户:「批量润色 ch_001-020，用番茄风」
```
> 路由: `style-transfer.md` → **novel-pipeline** `polish_chapter.py --range`
> 命令示例：
> ```powershell
> python <novel-pipeline>/scripts/polish_chapter.py --range 1-20 <project>/chapters `
>     --style-file <writer>/references/presets/fanqie-quick-anti.md `
>     --min-words 2500 --max-words 3000
> ```
> 前置：novel-pipeline 自带 `ensure_git_snapshot()` 快照
> 边界：novel-pipeline **只碰 chapters/**，不动 state/tracking/setting
> 后续：writer 跑 daily 审查确认润色无禁令冲入

---

## 阶段九：发布

```
用户:「番茄投稿检查」      → fanqie-submission.md
用户:「导出起点格式」      → export.py
用户:「生成封面」          → cover.md
用户:「备份」              → git commit
```
> 可发布判定: daily 审查通过 = 可发布

---

## 阶段十：持续维护

```
用户:「开第二卷」          → deploy.md（卷间衔接 7 维检查）
用户:「全景报告」          → report_panorama.py
用户:「查一下主角等级」    → 读 .writer/state/characters.json 或 tracking/current_state.md
用户:「追读力怎么样」      → analyze_hook.py
用户:「升级是不是太慢了」  → analyze_rhythm.py
用户:「角色关系图谱」      → report_graph.py
用户:「有没有声音漂移」    → longform-quality-monitor.md（>100章时）
用户:「更新角色状态」      → 手动编辑 setting/*.md，或让 Agent 归档到 .writer/state/*.json
用户:「加个规划笔记」      → 在 tracking/*.md 的相应 ## 下方插 `<!-- user-edit -->...<!-- /user-edit -->` 块
用户:「报错了」            → troubleshooting.md
```

---

## 用户手补 tracking 场景（专项说明）

**触发**：用户读到 ch_010 突然想给某条伏笔留回收线索规划。

**做法**：
```markdown
# 打开 tracking/hooks.md
# 找到 "## 待回收（active）" 下方
# 追加：

<!-- user-edit -->
我的规划：神秘声音是主角父亲的残魂，计划 ch_030 揭晓；
先在 ch_015 让主角梦见父亲。
<!-- /user-edit -->
```

**保护规则**：
- render_tracking.py 每次重跑时**保留 user-edit 块**在原锚点下方
- 锚点 = user-edit 块前最近的 `##` 或 `###` 标题
- 找不到锚点的块统一移到文末"# 用户笔记"节

**注入**：下次写章时 Agent 读 tracking/hooks.md → user-edit 块作为规划意图进入 context，指导剧情走向。

---

## 全自动行为总结

| 触发 | 自动行为 | 涉及文件 |
|------|---------|---------|
| 创建项目 | project-init 生成 8 目录 + 11 文件 + `.writer/state/*.json` 骨架 | 全部 |
| 每章写前 | 读 `.writer/state/*.json` + `setting/*.md` + `outline/` + `tracking/` | 只读 |
| 每章写后 Step 5 | `archive_facts.py` 追加事实 + `render_tracking.py` 派生 md + 更新 novel.json | .writer/state/*, tracking/*, novel.json |
| 每章审计后 | novel.json chapters_done +1 → daily 审查触发 | novel.json + 审查报告 |
| 每 5/10/卷 | solo/lean/full 审查（替代升级） | 审查报告 |
| 每 100 章 | full + longform-quality（叠加） | 审查报告 |
| 批量写章/修复前 | `lib.ensure_git_snapshot()` 快照 | git |
| 批量润色前 | novel-pipeline 自带 `ensure_git_snapshot()` | git |
| 审查命中 blocking | 立即停止 → 修复 → 重跑 → 通过后继续 | 无 |
