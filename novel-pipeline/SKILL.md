---
name: novel-pipeline
version: "2.5.0-generic"
description: "通用三模型网文写作流水线：初稿生成 → 润色 → Hermes Agent 调度管控"
category: writing
tags: [网文, 写作, pipeline, MCP, hermes]
---

# novel-pipeline: 网文写作流水线（精简版）

## 体系架构

| 角色 | 组件 | 职责 |
|------|------|------|
| **调度中枢** | **Hermes Agent（本 Skill）** | 任务拆解、规则下发、质量校验、伏笔存档 |\n| **初稿生成** | MCP 服务（默认 novel-deepseek） | 产出剧情骨架，禁止文笔修饰 |\n| **后置润色** | MCP 服务（默认 novel-doubao） | 仅文字优化，锁定全部剧情/人物/事件 |\n| **自动检查** | `hooks/*.py` + 质检 MCP | 参数校验、内容质量分析(uno)、RED LINE 审计(publishready) |\n| **持久化** | `state-files/*.json` + memory-novel 知识图谱 | 世界观/人物/伏笔/战力状态管理 |

> 双模型职责完全切割，Hermes Agent 编排全流程。

---

## Layer 1 规则（最高权重，不可违反）

### 1.1 编排器定位（禁令）

⛔ 禁止自行生成长篇正文（>200 字的小说内容）
⛔ 禁止自行润色文本
⛔ 禁止跳过检查点直接输出
⛔ 禁止绕过 MCP 工具直接调用模型 API
✅ 只做：路由任务 → 提取上下文 → 调用 MCP → 执行检查脚本 → 汇总输出 → 归档

### 1.2 可用工具

| 工具 | MCP Server | 参数 |
|------|-----------|------|
| `generate_draft` | 初稿生成 MCP | `global_setting`, `chapter_outline`, `chapter_number`, `revision_instructions` |
| `polish_chapter` | 润色 MCP | `chapter_characters`, `draft_text`, `chapter_mood_tone` |
| `analyze_text` | uno MCP | `text` — 内容质量分析（通过 `check_uno.py` 调用） |
| `store_state` | memory-novel | 钩子自动同步（`archive_state.py`） |
| `search_nodes` | memory-novel | 钩子自动查询（`load_state.py`） |

### 1.3 内容红线
- 禁止：现实政治影射、色情/低俗描写、违法犯罪鼓吹、平台违禁内容

### 1.4 人设底线
主角 `core_values`/`bottom_lines`/`personality_traits` 不可突破，除非细纲标注弧线且有 ≥3 章铺垫。

---

## Layer 2 规则（硬性执行）

### 2.1 任务自动路由

| 用户意图 | 触发词 | 处理链路 |
|---------|--------|---------|
| 初始化设定 | 世界观/设定/力量体系 | 引导填写 state-files |
| 大纲编排 | 大纲/章纲 | 辅助规划 → 写入章纲文件 |
| **写单章** | 写第N章 | 初稿(novel-deepseek)→自检→[润色开关]→润色(novel-doubao)→审计(publishready+uno)→归档 |
| 章节返工 | 重写/修改第N章 | 读现有章 → 初稿(含修订指令) → 自检 → 输出 |
| 独立润色 | 润色/文笔修饰 | \*\*publishready审计→uno检查→综合评估→uno修复→publishready复检\*\* → `polish_independent.py` |
| 批量生成 | 批量/第X-Y章 | 逐章循环 + 每章归档 |
| 伏笔审查 | 伏笔/回收 | 读 foreshadowing.json → 报告 |
| **卷审查(轻量)** | 审查/审核/全文审查 + 卷/章 | **Mode A** — 3轮自检(OOC→伏笔→设定) + 细纲对比 + 汇总报告 |
| **卷审查(深度)** | 全面审查/深度审查 + 卷/章 | **Mode B** — 对接 writer 43维管线 + First 5 Triage + 5步审查循环（禁止先机械扫描再批量修复而不做深筛） |

### 2.2 写单章核心流程

```
[0] 读取状态 → hooks/load_state.py + 读取 state-files/*.json + (补充) memory-novel 知识图谱查询
[1] 参数预校验 → hooks/validate_draft.py（检查点 A）
[2] MCP: generate_draft(global_setting, chapter_outline, chapter_number)
[3] 初稿自检 → hooks/check_draft_quality.py + check_ooc_firstory.py + check_uno.py（检查点 B）
    ├─ passed → 进入 [4]
    └─ failed → 组装 revision_instructions → 回到 [1]（最多重试 2 次）
[4] 润色开关判定（见 2.4）
[5] 润色链路 → validate_polish → MCP: polish_chapter → audit_polish（检查点 D）→ audit_publishready（检查点 E）→ check_uno.py（检查点 F）
[6] 输出 + 归档 → hooks/archive_state.py（state-files + memory-novel 知识图谱同步）
```

> 完整3轮自检协议 → `skill_view('novel-pipeline', 'references/quality_check.md')`

### 2.2B 卷审查核心流程（非破坏性审计）

触发词：审查/审核/全面审查/全文审查 + 卷/章/完成

#### 模式A：内置 3 轮审查（轻量级、零外部依赖）

```
[0] 确认范围 → 读取 novel-pipeline.json 获取卷定义 → 收集目标卷所有章节文件
[1] 加载参照基准 → 读取 state-files/*.json + 本卷细纲 → 提取设定/人设/伏笔/战力规则
[2] 批量读章 → 按章号顺序读取全部章节正文（chN1.md ~ chN2.md）
[3] Round 1 执行 → 逐人物逐章节检查 OOC一致性（对比 characters.json）
    ├─ 记录偏离点位 + 标注严重度（阻断/建议/信息）
[4] Round 2 执行 → 逐章比对细纲关键点覆盖 + 伏笔推进状态（对比 foreshadowing.json）
    ├─ 统计覆盖率 + 列出未执行剧情点 + 列出窗口期未推进伏笔
[5] Round 3 执行 → 战力/设定/逻辑一致性检查（对比 power_system.json + world_setting.json）
    ├─ 跨章横向检查：装备等级、修为爬升曲线、地理时间一致性
    ├─ 逐章内部检查：数值矛盾、设定自相矛盾、时间线漏洞
[6] 质量评估 → 写作质量：章末钩子、节奏控制、文笔水平、感官细节
[7] 汇总报告 → 结构化输出：通过/警告/阻断 + 每项详情 + 综合评分 + 建议列表
    ├─ 不修改任何文件
    └─ 不触发 MCP 调用（只读审计）
```

#### 模式B：跨 skill 深度审查（对接 writer 43 维管线）

当用户要求**全面审查**或项目质量要求高时（如新卷完工/批量写章后），可启用 writer skill 的 full review 管线，对 novel-pipeline 项目做 43 维深度审查。这种跨 skill 集成模式提供禁令扫描、字数合规、段落规范、文风一致性等 novel-pipeline 内置 3 轮审查不覆盖的维度。

**适用条件**：
- writer skill 已安装（`skill_view('writer', 'references/review-cycle.md')` 返回内容）
- 项目根目录有 `chapters/` + `state-files/*.json`

**前置适配**（novel-pipeline 项目无 writer 标准目录）：
- 无 `writer.json` → 以 `novel-pipeline.json` 替代项目状态源
- 无 `tracking/` 目录 → 审查后追踪更新走 `archive_state.py`（而非 writer 的 tracking/ 文件）
- 无可用的 `scripts/audit.py` → 审查 Step 1 粗筛的机械扫描（禁令/字数/段落）**必须手动执行**（脚本不可用时不跳过，改为手动扫描，扫描方法见下表）
- memory-novel MCP 状态 → 按降级处理（只做文件级分析，不做 KG 增量校验）

**对接步骤**：

```text
[0] 项目体检（writer review-cycle.md Step 0 修改版）
    ├─ 用 novel-pipeline.json 替代 writer.json
    ├─ 检查 state-files/ 完整性而非 writer 的 setting/tracking/
    ├─ 可用 writer 的 scripts/audit.py 则执行；不可用则声明降级
    └─ memory-novel MCP 声明

[1] 粗筛（writer 机械扫描，无脚本时手动替代）
    ├─ 破折号扫描 → PowerShell: [regex]::Matches($c, '——').Count
    ├─ 字数统计 → PowerShell: [regex]::Matches($c, '\p{IsCJKUnifiedIdeographs}').Count
    ├─ AI 句式扫描（忽然/突然/仿佛/似乎）→ 同模式
    ├─ 段落长度 → 按行检测 >42 汉字比例
    └─ 输出表格（章号 × 禁令项 × 字数 × 超长段比例）

[2] 深筛（43 维审计 — 主会话 solo 或 delegate 并行）
    ├─ First 5 Triage：设定冲突 / OOC / 钩子 / 时间线 / 战力
    ├─ 15 维核心：逐维度定性评估
    ├─ 对照 state-files/*.json 做设定校验
    └─ 输出 S1-S4 分级问题清单

[3] 终验（阻塞清零确认）
    ├─ 核对 Step 1 S1 问题是否全部记录
    └─ 状态：通过 / 需修复后再审

[4] 追踪更新（走 novel-pipeline 的 archive_state.py，不走 writer 的 tracking/）
    ├─ 构建变更 payload（伏笔/角色/势力/规则）
    └─ 执行 archive_state.py 写入 state-files/*.json

[5] 全景报告（仿 writer 格式输出）
    ├─ 健康评分（0-100）
    ├─ 修复优先级排序
    └─ S1→S4 逐项列表
```

**机械扫描命令速查**（writer 的 audit.py 不可用时使用）：

> ⚠️ **PowerShell 中文正则陷阱**：PowerShell 5.1 的 `[regex]::Matches` 在 UTF-8 无 BOM 文件上常返回空匹配（假阴性），且中文正则中的引号/反斜杠在内联模式中极难转义。**可靠做法**：`write_file` 写 Python 脚本到临时路径，`terminal` 执行 `python <script_path>`。见下表格「Python 替代方案」列。

| 扫描项 | PowerShell 命令（不推荐） | Python 替代方案（推荐） |
|--------|--------------------------|------------------------|
| 破折号 `——` | 不推荐（见上方陷阱） | `content.count('\u2014\u2014')` |
| 字数（汉字） | 不推荐 | `len(re.findall(r'[\u4e00-\u9fff]', content))` |
| 超长段落(>42汉字) | 不推荐 | `sum(1 for p in content.split('\\n') if len(re.findall(r'[\u4e00-\u9fff]', p)) > 42 and not p.startswith('#'))` |
| AI 句式 | 不推荐 | `{w: content.count(w) for w in ['突然','忽然','仿佛','似乎','他知道','眼中闪过一丝','深吸一口气']}` |
| 对话引号格式 | — | `has_cn = '\u300c' in content`<br>判定：含「」则B01通过；仅含弯引号`""`则B01违规 |

**批量多章扫描模板**（Python 脚本模式，覆盖所有检查项）：
```python
import re
for ch in range(31, 81):  # 替换为目标卷起止
    path = f'chapters/ch{ch}.md'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    cn = len(re.findall(r'[\u4e00-\u9fff]', content))
    dashes = content.count('\u2014\u2014')
    has_cn_quotes = '\u300c' in content  # True=正确使用「」
    curly_quotes = content.count('\u201c') + content.count('\u201d')
    paras = content.split('\n')
    total = sum(1 for p in paras if len(p.strip()) > 0 and not p.startswith('#'))
    long_p = sum(1 for p in paras if len(re.findall(r'[\u4e00-\u9fff]', p)) > 42 and not p.startswith('#'))
    ai_words = ['突然','忽然','仿佛','似乎','他知道','眼中闪过一丝','深吸一口气','心中一动']
    ai_total = sum(content.count(w) for w in ai_words)
    ratio = long_p / max(total, 1) * 100
    print(f'ch{ch}: 汉字={cn}, 破折号={dashes}, 「」={has_cn_quotes}, 弯引号={curly_quotes}, 超长={long_p}/{total}({ratio:.1f}%), AI={ai_total}')
```

**修复策略**：审查发现的 S1-S2 问题，参照本 skill 2.2E「跨卷修为/设定一致性的处理策略」的决策树（策略 A 回滚偏差来源 / 策略 B 批量修正），按体量测试结果选择。

**跨卷连续性补充**：卷审查还必须执行跨卷连续性检查——见 writer skill 的 `references/cross-volume-audit.md`（5步：卷间时间线/修为状态/伏笔追踪/修复策略/归档）。这是 vol N 审查中唯一覆盖 vol N-1→vol N 断裂维度的检查。

**修复执行**：禁令替换（Python 脚本逐处替换）→ 字数扩充（手工，禁止注入）→ 段落拆分（split_paragraphs.py）→ 终验复查。

#### ⚠️ 关键陷阱：机械修复 ≠ 审查完成

批量修复（B01-B06 格式修正）只解决了**表层机械问题**。修复完成后**必须补做 Step 2 深筛**（43 维定性审计），否则会漏掉 S1 级别的核心矛盾：

| 遗漏类型 | 实例 |
|---------|------|
| **卷间时间线断裂** | vol2 ch80 结尾已到丹塔，vol3 ch81 开头回到战场废墟，无过渡标记 |
| **修为设定冲突** | ch91 写"练气八层冲击金丹"，但卷2 ch48 已突破筑基初期 |
| **地点名称错误** | ch110 写"九天灵域的天空"，但实际位于苍玄大陆青云宗 |
| **state-files 过期** | characters.json 中修为未随剧情推进更新 |

**典型错误流程**（禁止）：
```
机械扫描通过 → 批量修复完成 → 报告"全部通过" ✗
```

**正确流程**（必须）：
```
机械扫描 → 批量修复 → Step 2 深筛(43维) → 发现叙事矛盾 → 修复 → 终验 → 报告
                                                           ↻
```
每次深度审查的 First 5 Triage 中，**设定冲突(维3)** 和 **时间线(维2)** 必须逐章对照 state-files + 卷细纲验证，不能只靠扫描脚本。

### 2.2C 卷审查后必做：归档到 memory-novel

**卷审查和修正结束后，必须手动调用 `archive_state.py` 将状态变更写入 memory-novel。**

这是整卷审查中最容易被遗漏的步骤——因为审查不是"写单章"流水线，`archive_state.py` 不会自动触发。

**遗漏后果**：state-files 中的伏笔、人物变更、势力更新停留在审查前的版本，后续写作复用旧数据。

**正确做法**：
1. 构建变更 JSON payload，包含：新伏笔、人物修为/位置更新、新势力、新装备规则
2. 通过 `python hooks/archive_state.py` 传入（注意 PowerShell BOM 问题，用临时文件 + Python subprocess 方式）
3. 验证：检查 state-files/*.json 中的 `version` 字段是否 +1，确认 `foreshadowing.json` 中新增 `id` 已写入

**变更 payload 示例**（适用于审查后整体归档）：
```json
{
  "changes": {
    "chapter_number": <本卷末章号>,
    "foreshadowing": {
      "new": [
        {"id": "f-00X", "description": "...", "planted_chapter": <章号>, ...}
      ],
      "resolved_ids": []
    },
    "characters": [
      {"name": "林尘", "cultivation_level": "...", "chapter_number": <末章号>, ...}
    ],
    "world_setting": { "factions": [...], "special_rules": [...] },
    "power_system": { "equipment": [...], "combat_rules": [...] }
  }
}
```

### 2.2D 批量格式修复工作流

批量审查后发现的 B01-B06 机械问题，按以下顺序执行修复：

```text
[Step 1] B02 破折号 → 替换为，或……
[Step 2] B01 对话引号 → 弯引号→「」
[Step 3] B06 超长段拆分 → 句号处断段
[Step 4] B03 不是…而是… → 重组为肯定句
[Step 5] B05 AI高频词 → 轮换替换池（对话内保留）
[Step 6] state-files更新 → archive_state.py同步
```

每步用独立 Python 脚本执行（`write_file` 写脚本 → `terminal` 运行），不用 `patch` 工具。

B05 精修关键策略：轮换替换池避免替换词单调重复（如「突然→猛地/骤然/猝然/冷不丁/瞬间」轮流使用），`is_in_dialogue()` 检查确保对话内原词保留。

> 详细实现 → `skill_view('novel-pipeline', 'references/batch-format-fix.md')`

### 2.2E 章节编辑注意事项

卷审查报告中列出的问题需要修复时，注意以下陷阱：

- **`patch` 工具在中文 `.md` 文件上可能反复失败**（Windows `\\r\\n` 编码 + 高频中文字符匹配失效）
- **可靠工作流**：Python 脚本原地替换。见 `skill_view('novel-pipeline', 'references/troubleshooting.md')`
- **修复前通读全章**：确认替换文本在文件内唯一，避免误替换
- **修复后验证**：重新读取被改行，或使用 `terminal` 执行 Python 检查确认标记字符串存在
- **避免大型单脚本多段修改**：当需要在同一文件中插入多个段落时，不要把所有修改写在一个脚本中最后一次性写入。若中间某个 assert 失败或文本不匹配，前面已成功的修改也会丢失。更可靠的模式：每段修复后立即保存，或拆成独立脚本逐个运行。
- **扫描结果冲突处理**：项目中可能遗留多个版本的扫描结果文件（如 `_v2_scan.json` 和 `_vol2_scan_result.json`），不同工具对同一指标的判定标准（如「破折号」计数、段落定义）可能不同。**不要信任任何既有扫描文件**——直接写一个纯净的 Python 脚本对目标章节重新做全量扫描，并借此机会补充既有扫描未覆盖的维度（如对话引号格式）。

### 2.2F 跨卷修为/设定一致性的处理策略

跨卷审查后常发现海量"不一致"引用（如 ch36 突破筑基但后续 130 章仍写练气八层）。处理策略分两类：

| 策略 | 适用场景 | 工作量 | 风险 |
|------|---------|--------|------|
| **A. 修正偏差来源** | 单章偏差 vs 130+章正文 | 低（改1章） | ✅ 最低 |
| **B. 批量修正后续** | 偏差在叙事上是"正确的"且读者不能接受原设定 | 高（100+处） | ⚠️ 可能引入新矛盾 |

**决策树**：
该章节的"偏差"是作者主动做的叙事改进（如提前突破让读者爽）
  → 策略B。接受高工作量，用 mass-edit-workflow 批量修正
  → 策略A。回滚偏差章节的对应段落，恢复原设定

**体量测试**：扫描全卷，统计不一致引用的数量：
  < 20 处 → 策略B（手动或脚本逐个修正）
  > 50 处 → 策略A（回滚偏差来源，只改 1 章）
  50~200 处 → 看是否涉及读者体验的核心矛盾

**回滚偏差来源的通用做法**：
1. 定位偏差发生的章节和具体段落
2. 恢复该段落为原始文本（删除突破/升级/关键剧情变动）
3. 保留该章节的其他内容不变
4. 验证后续章节的文本是否自然恢复一致性

### 2.3 重生成决策
- 第 1 次重试：汇总所有 issues → `revision_instructions` → 调 `generate_draft`（retry=1）
- 第 2 次重试：仅保留 OOC + 逻辑冲突检查，放宽剧情执行检查
- 仍失败：选最优版本 → 标注 `⚠ 需人工介入`

### 2.4 润色开关判定
**任一满足自动跳过润色：**
- 过渡章节关键词命中 ≥ 3 个（前往/赶路/飞行/传送/休整/采购/日常/疗伤）
- 本章字数 < 2500
- 章节 ≤ 3（前期攒设定，后期统一润色）

### 2.5 下发指令标准化协议

**generate_draft 参数：**
```
global_setting:      <从 world_setting.json + power_system.json 提取本章相关摘要>
chapter_outline:     <本章细纲（关键剧情点列表）>
chapter_number:      <整数>
revision_instructions: <首次留空，重试时填入自检反馈>
```

**polish_chapter 参数：**
```
chapter_characters:  <仅本章出场角色状态摘要>
chapter_mood_tone:   <可选: 紧张/爽快/压抑/热血/温情/悬疑/中性>
draft_text:          <原始初稿全文>
```

### 2.6 持久化存档
每章完成后：
1. **伏笔提取** → 识别新增伏笔 → 记录到 `foreshadowing.json`
2. **人物变更** → 能力/位置/情绪更新
3. **势力变动** → 新势力/同盟关系更新
4. **规则更新** → 新设定规则写入

存档格式：`{"foreshadowing": {...}, "characters": [...], "world_setting": {...}}` → 传入 `archive_state.py`

---

## Layer 3 规则（软性优化建议）

- 每 3-4 段一个小转折，每 10 段一个大节奏点，章末 90-95% 埋钩子
- 对话口语化（符合人物性格），感官细节每场景 1-2 处
- 情绪通过身体反应外化（握拳、瞳孔收缩等）
- 拆分"然后…然后…"流水账句式
- ⮕ 详见 `skill_view('novel-pipeline', 'references/webnovel_triggers.md')`

---

## Hook 脚本调用速查

> 调用：`python <Skill路径>\hooks\<script>.py`
> 输入：stdin JSON | 输出：stdout JSON

| 脚本 | 触发点 | 关键输出 | 失败处理 |
|------|--------|---------|---------|
| `validate_draft.py` | generate_draft 前 | `valid`, `errors` | 修复重试 |
| `validate_polish.py` | polish_chapter 前 | `valid`, `errors` | 修复重试 |
| `check_draft_quality.py` | 初稿返回后 | `passed`, `issues` | 重生成 |
| `check_ooc_firstory.py` | 初稿返回后 | `passed`, `issues` | 标记不阻断 |
| **`check_uno.py`** | 初稿/润色返回后 | `passed`, `analysis` | 标记不阻断 |
| `audit_polish.py` | 润色返回后 | `passed`, `violations` | 重新润色 |
| `audit_publishready.py` | 润色返回后 | `passed`, `issues` | 标记不阻断 |
| `load_state.py` | 流水线启动 | `loaded`, `summary` | 不阻断 |
| `polish_independent.py` | 独立润色入口 | `polished`, `report`, `issues` | 降级: uno不可用时保留原文 |
| `archive_state.py` | 每章完成 | `archived`, `message` | 记错 |

---

## MCP 服务器集成状态

详细集成状态见 `skill_view('novel-pipeline', 'references/mcp-integration-guide.md')`。速览：

| MCP 服务 | 类型 | 实际调用 | 状态 |
|---------|------|---------|------|
| novel-deepseek | 原生 stdio | ✅ pipeline step [2] | 正常 |
| novel-doubao | 原生 stdio | ✅ pipeline step [5] | 正常 |
| publishready | 原生 stdio | ✅ `audit_publishready.py` 子进程调用（末尾链式调用 check_uno.py） | 正常，16 tools |
| uno | 原生 stdio | ✅ `check_uno.py` 子进程调用(analyze_text) | 正常 |
| memory-novel | 原生 stdio | ✅ `load_state.py` 读取 + `archive_state.py` 写入 | 正常(标准 memory server) |
| firstory | — | 🗑️ 已移除(Windows ESM bug) | OOC 降级本地规则 |

---

## 详细参考（按需加载）

| 内容 | 加载方式 |
|------|---------|
| 部署指南 + MCP 客户端配置 | `skill_view('novel-pipeline', 'references/deployment-guide.md')` |
| 环境变量模板 | `skill_view('novel-pipeline', 'references/env-template.md')` |
| 3 轮自检详细协议 | `skill_view('novel-pipeline', 'references/quality_check.md')` |
| 任务路由决策树 | `skill_view('novel-pipeline', 'references/task_routing.md')` |
| 项目隔离 + 新建项目 + 升级 | `skill_view('novel-pipeline', 'references/project-setup.md')` |
| 使用指引 | `skill_view('novel-pipeline', 'references/usage-guide.md')` |
| 故障排查 | `skill_view('novel-pipeline', 'references/troubleshooting.md')` |
| **MCP 集成现状（推荐先看这个）** | `skill_view('novel-pipeline', 'references/mcp-integration-guide.md')` |
| 旧版升级 | `skill_view('novel-pipeline', 'references/legacy-project-upgrade.md')` |
| 流派适配参考 | `skill_view('novel-pipeline', 'references/genre-adaptation.md')` |
| 项目配置模板 | `state-files/config.example.json` |
| 批量审计脚本 | `scripts/batch_audit.py` |
| 卷审查协议（含子代理验证 + 跨卷伏笔延续） | `skill_view('novel-pipeline', 'references/volume-audit-protocol.md')` |
| 卷审查抽样策略（大型卷的抽样+批量扫描方案） | `skill_view('novel-pipeline', 'references/volume-review-sampling.md')` |
| 批量章节编辑工作流（patch 替代方案 + 修为统一模板） | `skill_view('novel-pipeline', 'references/mass-edit-workflow.md')` |
| 润色管线选择（两条管线区别） | `skill_view('novel-pipeline', 'references/polish-pipeline.md')` |
| 环境诊断脚本 | `scripts/verify_env.py` |
