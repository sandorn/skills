# 质检工单：全链路质量控制

---

## 核心原则

1. **一次执行，全线通过。** 质检工单 = 禁令扫描 → 字数/段落修复 → 审查 → 去AI味。
2. **硬性禁令是红线。** blocking 问题不通过就不往下走。
3. **改最少，效果最大。** 去AI味不重写剧情。
4. **本地判断为主。** v8.3 起去 AI 味不再依赖外部 MCP 语义检测——主 Agent 在会话内直接读原文做定性判断，配合 `audit.py` 的规则扫描。

---

## 完整质检流程（全链）

```
命令：quality
```

### Step 1：禁令扫描

检查目标文件（默认当前最后写的章节或指定章节）。

> **禁令定义**：`references/hard-bans.md`（单一事实来源）。**执行扫描**：`scripts/audit.py`。

对 blocking 级问题逐项修复：

| 修复维度 | 修复规则 |
|------|---------|
| 破折号/引号 | `python scripts/audit.py <dir> --fix-escaped`；修复后立即验证章节文件完整性 |
| 「不是…而是…」句式 | 删除否定部分，仅保留正面陈述 |
| 元叙事标签 | 直接删除 |
| 分析术语 | 改写为具体动作和描写 |
| AI高频词 | 逐词替换（忽然→猛地/突然；深吸一口气→缓了缓；他知道→意识到/察觉） |
| 模板复制 | `audit.py` 自动检测；章末相同→S1 阻塞，逐章重写 |

### Step 2：字数 / 段落修复

扫描字数不足和段落超标的章节，用专用脚本修复：

```bash
# 段落拆分（拆分后章节文件即真实来源）
python scripts/split_paragraphs.py --batch chapters/
# 无需镜像 — 章节文件本身就是真实来源
```

字数不足时：`audit.py` 标记不足章 → 作者/主模型手工扩充 → 段落拆分 → mirror 数据库。

**禁止 `echo >>` 或手工拼接追加**（见 `hard-bans.md` B08）。

### Step 3：审查

运行 review solo 模式（15 项核心 + AI 痕迹 + 硬禁令）。

### Step 4：去AI味（6 Gate + 3 级力度）

基于 review 结果执行去AI味。采用 6 Gate 逐项清除法，分三级力度：

#### 级别选择

| 级别 | 适用场景 | 处理范围 |
|------|---------|---------|
| **轻度** (`--level mild`) | 日更快速去味 | Gate A + B |
| **中度** (`--level moderate`) | 常规章节质检 | Gate A + B + C + D |
| **重度** (`--level heavy`) | 全章精修/完稿 | Gate A→F 全量 |

#### 6 Gate 详解

| Gate | 检查内容 | 处理方式 |
|------|----------|----------|
| **A 禁用词** | AI 高频词替换 | `audit.py` 定位命中词位置 → 逐词替换（参考 hard-bans B05 替换池）|
| **B 句式** | AI 惯用句式重写 | 主 Agent 读原文识别套话/排比/对称 → 打散重写 |
| **C 心理外化** | 情绪用动作展示 | 主 Agent 找抽象情感词（"愤怒/绝望"）→ 改为身体动作（"拳头攥白"）|
| **D 节奏** | 打断排比，长短交错 | 主 Agent 检查段落长度分布 → 连续排比保留 1-2 个 |
| **E 对话** | 去 AI 腔，加口语化 | 主 Agent 对照 setting/writing_rules.md 的角色声音 → 逐句改口语化 |
| **F 结尾** | 去升华，用动作收尾 | 主 Agent 检查章末 300 字 → 升华/哲理句改为具体动作/细节定格 |

#### 系统性去AI三遍法

```
Pass 1 — 去泛化：抽象词替换为具体细节
Pass 2 — 去书面化：书面腔替换为口语/动作
Pass 3 — 回自然感：注入停顿、犹豫、矛盾和口语感
```

#### 4.1 段落拆分（所有级别必做）

- 句号处换行，一句一段
- 每段≤42 汉字（对话和内心独白除外）
- 对话独立成段
- 标题与正文间隔空行

**注意：批量字数扩充时的段落陷阱。** 用 `echo >>` 或批处理追加文字来扩充字数时，追加内容通常会变成一行超长段落（数百汉字）。扩充完成后必须跑句号拆分——按 `。！？` 断段，确保每段≤42 汉字：

```bash
python scripts/split_paragraphs.py --batch chapters/
```

#### 4.2 AI 痕迹修复

| 问题 | 修复方法 |
|------|---------|
| 段落等长 | 合并语义相关的短段或拆分过长的段落 |
| 套话密度 | 删除或替换「似乎」「可能」「或许」等模糊词，除非角色对话中有意使用 |
| 公式化转折 | 删除多余转折词，或用自然过渡替代 |
| 列表式结构 | 改写开头结构，避免连续三句相同句式 |
| AI标记词 | 替换「值得注意的是」「不可否认」「显而易见」等 |

#### 4.3 自然化（可选）

针对轻度 AI 味：

- 增加口语停顿（「呃」「这个嘛」等，适度）
- 让句子有点"跳跃"，不要过度圆滑
- 把完美的说明改为有侧重点的叙述

### Step 5：字数 / 段落验证

```bash
python scripts/audit.py chapters/
```

输出逐章字数/违禁/段落超标状态。如果全部 PASS（字数≥2500 + 禁令清零 + 段落≤42），质检完成。

质检通过后更新版本状态：
```bash
# 更新 writer.json 版本记录（polished）
# 章节文件即真实来源，无需独立镜像
```

---

## 单项质检命令

| 命令 | 功能 | 说明 |
|------|------|------|
| `deslop` | 仅去AI味 | 不跑禁令和审查，纯文本改写 |
| `ban-scan` | 仅禁令扫描 | 只检查硬性禁令 |
| `repair-paragraphs` | 仅段落修复 | `python scripts/split_paragraphs.py --batch chapters/` |
| `doctor` / `preflight` | 项目体检 | 检查状态文件、目录结构、JSON 合法性 |

### deslop（去AI味 — 6 Gate）

专注于改写 AI 味文本，不审查不修禁令。

> **选择指引**：批量快速清除（≥10章）用 deslop；逐句精修（≤5章或作者要求高标准）用 [`manual-polish.md`](manual-polish.md)。

1. **级别选择**：默认自动检测级别；可指定 `--level mild|moderate|heavy`
2. **Gate A 禁用词**：查禁止词表，逐词替换
3. **Gate B 句式**：打散排比/对称/空洞抒情
4. **Gate C 心理外化**（中/重度）：情绪词→动作展示
5. **Gate D 节奏**（中/重度）：连续排比保留1-2个
6. **Gate E 对话**（重度）：去AI腔，加口语化
7. **Gate F 结尾**（重度）：去升华，动作收尾
8. **段落拆分**：`python scripts/split_paragraphs.py --batch chapters/`
9. **验证**：确保改写后字数变化不超过 ±10%

### ban-scan（禁令扫描）

纯扫描模式——不修改文件，只输出违规报告。

```bash
python scripts/audit.py --verify chapters/
```

### doctor / preflight（项目体检 — 含缺口检测）

只读诊断，包含 6 项缺口检查：

**基础检查：**
- 检查 `writer.json` 是否存在且 JSON 合法
- 检查 `setting/`、`outline/`、`chapters/`、`.writer/runtime/` 是否存在
- 统计正文章数、最近章节、低于 2500 汉字章节
- 扫描占位符：`TODO`、`待补`、`{}`、`【待】`

**缺口检测（仅在发现问题时报告）：**
1. **正文多设定少**：章节 > 10 但设定文件 < 3 → 建议补充设定
2. **AI味密度**：跑 `audit.py` 快速禁令扫描
3. **异常伏笔**：从 `novel_project` MCP 查询异常状态伏笔；老项目 `tracking/` 仅作只读参考
4. **大纲缺失**：有正文但无大纲目录 → 建议创建大纲
5. **拆文未完成**：analysis_lib/ 下有 _progress.md → 提示继续拆解
6. **部署完整性**：.writer/ 结构是否完整

**所有检查只读，不修改任何文件。**

---

## 批量章节质检工作流

连续写多章后的质检，用专用脚本一次性检查所有章节，然后逐章定点修复。

### 批量字数 + 禁令一体化扫描

```bash
python scripts/audit.py chapters/
```

输出逐章字数/违禁/段落超标状态（含引号检测、模板复制检测）。

> **注意**：字数阈值按项目写作规范调整（默认 2500）。禁止词清单见 `hard-bans.md` B05。

### 破折号与禁令修复

```bash
python scripts/audit.py chapters/ --fix-escaped
```

如需仅检测不修改：`python scripts/audit.py --verify chapters/`

### AI 句式修复

不建议批量全局替换。用 `audit.py` 先扫描出违规位置，再逐句判断是否需要替换：

```bash
python scripts/audit.py chapters/
# 根据输出逐章逐句手动替换
```

### 通用段落重复扫描（模板复制检测）

`audit.py` 内置模板复制检测——对比相邻章节的章首/章末 200 字指纹：

```bash
python scripts/audit.py chapters/
```

检测标准：章首/章末 200 字与近 3 章完全一致即为 S1 阻塞。

### 因果句扫描（部分项目禁用）

`audit.py` 的禁令扫描已覆盖因果句式检测。违规阈值：单章内 `因为 + 所以 + 由于` 合计 > 1 即不合格。

---

## 修复流程

1. **批量扫描**：`python scripts/audit.py chapters/`
2. **标记 FAIL**：找出所有 FAIL 章节
3. **逐章修复**：优先修破折号（`audit.py --fix-escaped`），再逐项修 AI 句式
4. **扩充短章**：字数不足的章节由作者/主模型手工扩充，遵循五层叠料法：
   - **感官层**：加环境细节（气味、温度、光线、声音、材质触感）
   - **围观层**：加配角/围观者反应（表情、低语、动作、姿态变化）
   - **心理层**：延长主角内心动作（回忆、对比、预判，但不用「他知道」「他想起」等套话）
   - **物件层**：加场景道具的物理细节（新旧、磨损、位置、触感）
   - **对话层**：延长对话中的沉默、停顿、小动作，让对话有呼吸感

   注意：叠料不改情节。所有新增内容必须落在已有场景内。扩充完成后必须运行段落拆分：`python scripts/split_paragraphs.py --batch chapters/`

5. **复检**：`python scripts/audit.py chapters/` 确认全部 PASS

---

## 质检报告

```markdown
# 质检报告

| 目标文件：chapters/ch_{NNN}.md

## 禁令扫描
- 破折号：PASS / FAIL ({N}处)
- 不是…而是…：PASS / FAIL ({N}处)
- 元叙事：PASS / FAIL ({N}处)
- 分析术语：PASS / FAIL ({N}处)
- AI高频词：PASS / FAIL ({N}处)
- 模板复制：PASS / FAIL

## 审查结果
- blocking：{N} 项
- warning：{N} 项
- info：{N} 项

## 去AI味（6 Gate）
- Gate A 禁用词：{PASS/WARNING}
- Gate B 句式：{PASS/WARNING}
- Gate C 心理外化：{PASS/WARNING}
- Gate D 节奏：{PASS/WARNING}
- Gate E 对话：{PASS/WARNING}
- Gate F 结尾：{PASS/WARNING}

## 最终验证
- 汉字数：{N}（≥2500: {PASS/FAIL})
- 段均长：{N}（变异系数: {N}）
- 可发布：{YES/NEEDS_REVISION}
```
