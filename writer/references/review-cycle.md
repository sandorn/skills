# 审查循环：5 步完整管线（单一权威版本）

> 本文件是 writer skill 审查流程的**唯一权威定义**。SKILL.md 通过引用本文档获取完整流程。
> **审查维度定义**：`references/review.md`（43维 / 日更8维 / solo15维 / 模式标志 --daily --solo --lean --full）。

大规模写章后（>20章），必须执行全面审查。日常审查可仅执行 Step 1-3 的定向子集。

---

## 管线概览

```
Step 0: 项目体检 ──→ Step 1: 粗筛 ──→ Step 2: 深筛
Step 3: 终验      ──→ Step 4: 事实库增量归档 → Step 5: 全景报告
```

| Step | 名称 | 执行方式 | 产出 |
|------|------|---------|------|
| 0 | 项目体检 | 主会话 solo | 环境状态声明（目录 + `novel_project` MCP 可用性）|
| 1 | 粗筛 | delegate 并行 / solo | 违规模板清单 + 5维数据表 |
| 2 | 深筛 | delegate 并行 | S1-S4 分级问题清单 + 追读力报告 |
| 3 | 终验 | 主会话 solo / delegate | 阻塞清零确认 + MCP 增量校验 |
| 4 | 事实库增量归档 | 主会话 solo | 审查发现的新事实 → `archive_facts.py` → `novel_project` MCP |
| 5 | 全景报告 | 主会话 solo | 健康评分 + 修复排序 + 趋势对比 |

---

## Step 0：项目体检

调用 `quality.md` 的 doctor 模式，确认审查环境完整：

- **目录/文件完整性检查**：`setting/` / `outline/` / `chapters/` 是否存在
- **MCP 可用性检查**：`novel_project` MCP 是否连通（通过 `read_graph` 抽样调用；不通则见下方降级）
- **MCP 覆盖率抽样**：主角实体是否存在、最近章节的观测是否入库（用 `get_entity_with_relations` 查主角，看是否有 `ch{最近章}: xxx` 观测）
- 发现问题 → 先修复再进入 Step 1

### MCP 状态不健康时的降级

| 状态 | 降级行为 |
|---------------|---------|
| ✅ `novel_project` MCP 连通 + 主角实体存在 + 最近 5 章观测齐 | Step 3b 增量校验 + Step 4 事实归档 全部启用 |
| ⚠️ MCP 连通但主角实体缺失（老项目未迁移） | 提示先跑 `scripts/import_state_to_mcp.py` 完成迁移再审查 |
| ⚠️ MCP 连通但最近 N 章观测缺失（写章时跳过了归档） | Step 4 补写：用当前审查发现的事实构造 payload，追加归档 |
| ⛔ MCP 不可达 | 降级为文件级交叉校验（对照 `setting/*.md`）；Step 4 跳过；报告顶部注明"MCP 离线降级" |

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

> **MCP 健康时**启用增量校验；**不可达时**降级为文件级交叉校验（见 Step 0 降级声明）。

### 2a. 43 维质量审计（`review.md`）

按 S1-S4 分级输出问题清单。执行前先过 **Triage**（见 `review.md` 审查 Triage 章节）：
- First 5 必检（设定冲突/OOC/章末钩子/时间线/战力崩坏）
- 命中 blocking → 停止，修复，重查 First 5
- 通过后按章节类型定向激活其余维度

### 2b. 跨设定交叉校验（`setting-consistency-audit.md`）

对照设定文件的数值基准值 + MCP 里的当前观测，逐章检查正文一致性。统一入口，覆盖设定内部→大纲→正文→卷间→修复全链路。

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

### 3b. 事实库增量校验（MCP）

> **仅在 Step 0 确认 `novel_project` MCP 可用时执行。** 不可达时降级为文件级交叉校验——人工对照 `setting/*.md` 逐条验证，以注释形式追加到审查报告。

MCP 可用时：将审查中发现的新事件通过 `archive_facts.py` 生成 payload → 调 MCP 归档，并与已有观测交叉验证：
- 等级事件：从 MCP 主角实体的观测拉出所有 `ch*: 修为 xxx` 时间线，检查递增性
- 金币事件：观测里 `ch*: 金币余额` 序列可追溯
- 伏笔事件：`search_nodes("伏笔:")` 拿全部伏笔实体，检查未回收伏笔是否已埋线过久（>50 章未回收 → 风险预警）
- 关系一致性：`get_entity_with_relations` 抽查主角势力/敌友关系是否与正文一致

### 3c. 阻塞清零确认

S1 问题未全部清零前不进入 Step 4。

---

## Step 4：事实库增量归档（强制执行）

### archive_facts.py + MCP 归档

审查中发现的新事实（写章时漏提取的）→ 构造 payload → `python <writer>/scripts/archive_facts.py`：

```bash
cat <<EOF | python <writer>/scripts/archive_facts.py
{
  "chapter_number": <审查发现的章号>,
  "changes": {
    "characters": [...],
    "foreshadowing": {"new": [...], "resolved": [...]},
    "factions": [...],
    "power":    {...},
    "world":    {...},
    "relations":[...]
  }
}
EOF
```

archive_facts 输出 tool_calls 序列 → Agent 按 phase=read → phase=write 顺序调 `novel_project` MCP：
1. 先执行所有 `get_entity_with_relations`（拿旧 observations）
2. 把 `create_entities` payload 里的 `<merge_with_old>` 占位符替换
3. 依次调 `create_entities` 和 `create_relations`

**契约与陷阱详见** `references/memory-mcp.md`。

### 检查清单

- □ 审查发现的新伏笔已入 MCP（`search_nodes("伏笔:")` 能查到）
- □ 审查发现的新势力已入 MCP（`get_entity_with_relations("<势力名>")` 有返回）
- □ 已回收伏笔的实体观测里有 `chNNN: 已回收 - <resolution>` 条目
- □ `novel.json` 已更新 `updated_at` 时间戳

---

## Step 5：全景报告输出（`report_panorama.py`）

```bash
python scripts/report_panorama.py . --output 审查报告-全景.md
```

报告包含：
- **健康评分**（0-100）：基于字数/禁令/段落/MCP 归档覆盖率
  - 若 MCP 不可达，健康评分不含事实库维度，权重重新分配
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

novel_project MCP 状态: ✅ 连通完整 / ⚠️ 部分覆盖({降级原因}) / ⛔ 离线降级
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
| 2026-07-13 | v8.4 — `.writer/state/*.json` + `render_tracking.py` 三件套全部替换为 `novel_project` MCP + `archive_facts.py` 单件套；健康评分维度从"事实库覆盖率"改为"MCP 归档覆盖率" |
| 2026-07-10 | v8.3 — memory-novel MCP 相关字段全部替换为 `.writer/state/*.json` + `archive_facts.py` + `render_tracking.py` 三件套 |
| 2026-06-23 | 与 SKILL.md 5步管线统一，增加 Triage 引用、Step 5 全景报告 |
