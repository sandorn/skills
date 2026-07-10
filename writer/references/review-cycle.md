# 审查循环：5 步完整管线（单一权威版本）

> 本文件是 writer skill 审查流程的**唯一权威定义**。SKILL.md 通过引用本文档获取完整流程。
> **审查维度定义**：`references/review.md`（43维 / 日更8维 / solo15维 / 模式标志 --daily --solo --lean --full）。

大规模写章后（>20章），必须执行全面审查。日常审查可仅执行 Step 1-3 的定向子集。

---

## 管线概览

```
Step 0: 项目体检 ──→ Step 1: 粗筛 ──→ Step 2: 深筛
Step 3: 终验      ──→ Step 4: 追踪+事实库 → Step 5: 全景报告
```

| Step | 名称 | 执行方式 | 产出 |
|------|------|---------|------|
| 0 | 项目体检 | 主会话 solo | 环境状态声明（目录 + `.writer/state/` 完整性）|
| 1 | 粗筛 | delegate 并行 / solo | 违规模板清单 + 5维数据表 |
| 2 | 深筛 | delegate 并行 | S1-S4 分级问题清单 + 追读力报告 |
| 3 | 终验 | 主会话 solo / delegate | 阻塞清零确认 |
| 4 | 追踪+事实库 | 主会话 solo | 追踪文件更新（archive_facts + render_tracking）|
| 5 | 全景报告 | 主会话 solo | 健康评分 + 修复排序 + 趋势对比 |

---

## Step 0：项目体检

调用 `quality.md` 的 doctor 模式，确认审查环境完整：

- **目录/文件完整性检查**：`setting/` / `outline/` / `chapters/` / `.writer/state/` 是否存在
- **状态文件检查**：`.writer/state/*.json` 4 份是否格式合法（`python <writer>/scripts/archive_facts.py --dry-run` 诊断）
- 发现问题 → 先修复再进入 Step 1

### 状态文件缺失时的降级

| 状态 | 降级行为 |
|---------------|---------|
| ✅ `.writer/state/*.json` 完整 | Step 3b 增量校验 + Step 4 事实归档 全部启用 |
| ⚠️ `.writer/state/` 缺失或为空 | Step 3b 降级为文件级交叉校验（对照 setting/*.md）；Step 4 用当前审查发现补建 state 骨架 |
| ⚠️ state 断层 >20 章（chapters 增长但 state version 未更新） | 提示用户跑 `archive_facts.py` 补齐再审查 |

降级声明写入审查报告顶部。

---

## Step 1：粗筛（禁令 + 字数 + 段落 + 5维提取）

扫描全部目标章节。**只发现问题并提取数据，不动手修。**

### 扫描项

```
✅ 破折号 `——`
✅ AI句式 (忽然/突然/他知道/不是…而是/似乎/仿佛)
✅ 元叙事标签
✅ 字数 (≥2500中文汉字)
✅ 标题格式
✅ 句号断段 (≤42 汉字/段)
✅ 硬性禁令 (眼中闪过一丝/深吸一口气/心中一动 — 见 hard-bans.md)
✅ 模板复制检测（章首+章末双端，相邻3章200字指纹匹配）
✅ ASCII引号/弯引号扫描
✅ 5维数据提取：权限(L0-L6)、等级(级数)、金额(售价/消耗)、属性(同步值)、感情线(段落级统计)
```

### 执行命令

```bash
python scripts/audit.py chapters/                    # 批量扫描（含5维交叉校验）
```

### 注意事项

- **段落扫描必须是审查的最后一步**：禁令清零 + 字数补足全部完成后才跑段落检查
- **感情线占比按段落级统计，不按章级**：仅当有感情线互动场景的段落才计入

---

## Step 2：深筛（43维审计 + 交叉校验 + 追读力）

> **`.writer/state/*.json` 完整时**启用增量校验；**不完整时**降级为文件级交叉校验（见 Step 0 降级声明）。

### 2a. 43 维质量审计（`review.md`）

按 S1-S4 分级输出问题清单。执行前先过 **Triage**（见 `review.md` 审查 Triage 章节）：
- First 5 必检（设定冲突/OOC/章末钩子/时间线/战力崩坏）
- 命中 blocking → 停止，修复，重查 First 5
- 通过后按章节类型定向激活其余维度

### 2b. 跨设定交叉校验（`setting-consistency-audit.md`）

对照设定文件的数值基准值，逐章检查正文一致性。统一入口，覆盖设定内部→大纲→正文→卷间→修复全链路。

### 2c. 追读力分析（`analyze_hook.py`）

```
✅ 钩子强度（章末500字，0-10分）
✅ 爽点分布（升级/打脸/暴富/智谋/情感/装备/势力/逆转）
✅ 5章区间爽点间隔
✅ 钩力衰减检测（连续3章下降 → 预警）
✅ 末句截断检测（番茄投稿兼容性）
```

### ⚠️ 感情线占比陷阱

按段落级统计，不按章级——仅当有感情线互动场景时才计入该段字数，避免虚高。

---

## Step 3：终验（阻塞清零）

### 3a. 节奏趋势异常检测（`analyze_rhythm.py`）

```
--dim level    等级升级间隔是否合理（>20章一级？<3章一级？）
--dim gold     金币余额趋势是否通胀或断裂
--dim love     感情线里程碑间隔是否合理
```

### 3b. 事实库增量校验

> **仅在 Step 0 确认 `.writer/state/*.json` 存在时执行。** 不存在时降级为文件级交叉校验——人工对照 `setting/*.md` 与 `tracking/*.md` 逐条验证，以注释形式追加到审查报告。

state 完整时：将审查中发现的新事件通过 `archive_facts.py` 写入 `.writer/state/*.json`，并与已有记录交叉验证：
- 等级事件：确认不倒退、不自相矛盾（`characters.json` cultivation 字段递增性检查）
- 金币事件：余额可追溯（`recent_changes` 时间线）
- 伏笔事件：新增伏笔标记「未埋」，回收伏笔标记「已回收」（`foreshadowing.json` active/resolved 迁移）

### 3c. 阻塞清零确认

S1 问题未全部清零前不进入 Step 4。

---

## Step 4：追踪更新 + 事实库归档（强制执行）

### 事实库归档（archive_facts.py）

审查中发现的新事实（写章时漏提取的）→ 构造 payload → `python <writer>/scripts/archive_facts.py`：

```bash
cat <<EOF | python <writer>/scripts/archive_facts.py
{
  "chapter_number": <审查发现的章号>,
  "changes": {
    "characters": [...],
    "foreshadowing": {...},
    "power_system": {...},
    "world_setting": {...}
  }
}
EOF
```

- `.writer/state/*.json` 版本号自增 + .bak 备份

### 追踪派生（render_tracking.py）

```bash
python <writer>/scripts/render_tracking.py
```

- 从最新 `.writer/state/*.json` 派生 `tracking/*.md`
- 保留用户 `<!-- user-edit -->` 块

### 检查清单

- □ `.writer/state/foreshadowing.json` 版本号已递增（若有新伏笔发现）
- □ `.writer/state/characters.json` 版本号已递增（若有角色状态变更）
- □ `tracking/*.md` 已重新派生
- □ 用户 user-edit 块保留数 == 派生前提取数（无丢失）

---

## Step 5：全景报告输出（`report_panorama.py`）

```bash
python scripts/report_panorama.py . --output 审查报告-全景.md
```

报告包含：
- **健康评分**（0-100）：基于字数/禁令/段落/追踪/状态归档完整度
  - 若 `.writer/state/*.json` 不完整，健康评分不含事实库覆盖率，权重重新分配
- **修复优先级排序**：S1 > S2 > S3 按章节排序
- **项目整体建议**：下一步写作方向、风险提示
- **趋势对比**：本次审查 vs 上次审查的健康评分变化

---

## 审查报告卡片格式

每轮审查后输出：

```
═════════════════════════════
第N轮审查报告 (区间: ch{M}-{K})
═════════════════════════════

S1 (阻塞 — 必须修)
  [chXX-L{b}行] {问题描述}
  → 修复: {修复方式}

S2 (建议 — 应该修)
  [chXX] {问题描述}
  → 修复: {修复方式}

S3 (提示 — 可忽略)
  {分析}

.writer/state 状态: ✅ 完整 / ⚠️ 降级（{降级原因}）
阻塞统计: S1={N}个, S2={M}个, S3={K}个
最终判定: 通过 / 需修复后再审 / 阻塞未清
```

S1 未全部清零前不进入下一轮审查。

---

## 批量修复命令

审查发现问题后，委派产出必须走完修复管线：

```
禁令修复 → 追加字数 → 段落拆分 → 终验 → 5维交叉校验
```

详细流程和陷阱说明见 `post-review-fix.md`。

---

## 版本

| 日期 | 变更 |
|------|------|
| 2026-07-10 | v8.3 — memory-novel MCP 相关字段全部替换为 `.writer/state/*.json` + `archive_facts.py` + `render_tracking.py` 三件套 |
| 2026-06-23 | 与 SKILL.md 5步管线统一，增加 Triage 引用、Step 5 全景报告 |
