# 质检工单：全链路质量控制

改编自 story-deslop + novel-pipeline 完稿质检链 + 硬性禁令规则。

---

## 核心原则

1. **一次执行，全线通过。** 质检工单 = 禁令扫描 → 审查 → 去AI味 → 段落修复。
2. **硬性禁令是红线。** blocking 问题不通过就不往下走。
3. **改最少，效果最大。** 去AI味不重写剧情。

---

## 完整质检流程（全链）

```
命令：quality
```

### Step 1：禁令扫描

检查目标文件（默认当前最后写的章节或指定章节）。路径按 `chapters/` → `正文/` 顺序解析：

```python
import re

BAN_RULES = {
    "破折号": r"——",
    "不是…而是…句式": r"不是.*而是",
    "元叙事标签": r"(正如前文所述|正如我们所知|这个场景|这一幕|如前所述)",
    "分析术语": r"(内心挣扎|表面.*实则|表面上.*实际上)",
    "AI高频词": r"(忽然|深吸一口气|眼中闪过|他知道|命运|如潮水般|仿佛春风)",
}

def detect_template_copy(content, prev_chapters):
    """模板复制检测：检查是否有连续3章相同的开篇句式"""
    # 取正文前50字作为指纹
    first_line = content.strip()[:50]
    matches = 0
    for prev in prev_chapters[:3]:  # 最近3章
        if prev and prev[:50] == first_line:
            matches += 1
    return matches >= 2  # 连续3章相同开头 → 警告

def scan_bans(content):
    results = {}
    for rule_name, pattern in BAN_RULES.items():
        matches = re.findall(pattern, content)
        if matches:
            results[rule_name] = {
                "count": len(matches),
                "samples": matches[:3],
                "level": "blocking"
            }
        else:
            results[rule_name] = {"count": 0, "level": "pass"}
    return results
```

### Step 2：自动修复禁令

对 blocking 级问题逐项修复：

| 禁令 | 修复规则 |
|------|---------|
| 破折号「——」 | 删除或替换为逗号/句号。对话中表示打断的「——」（单条半角）可保留但标注 |
| 「不是…而是…」 | 删除否定部分，仅保留正面陈述 |
| 元叙事标签 | 直接删除标签 |
| 分析术语 | 改写为具体动作和描写 |
| AI高频词 | 逐词替换（忽然→猛地/突然/一瞬；深吸一口气→停顿了一下/缓了缓；眼中闪过→垂下眼/别开目光；他知道→意识到/察觉；命运→去掉或用具体词；如潮水般→去掉；仿佛春风→去掉） |
| 模板复制 | 改写开篇句式，调整叙述切入点 |

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
| **A 禁用词** | AI 高频词替换 | 查禁止词表，逐词替换为具体动作。如：眼中闪过一丝→垂下眼；他知道→意识到；忽然→猛地/一瞬 |
| **B 句式** | AI 惯用句式重写 | 打散排比/对称/空洞抒情。「不是…而是…」→ 直述句。连续排比保留1-2个 |
| **C 心理外化** | 情绪用动作展示 | 抽象情绪词 → 身体状态/动作。「他很紧张」→「他的手在抖」「他加快脚步」 |
| **D 节奏** | 打断排比，长短交错 | 连续3+排比 → 保留1-2个。长句切短，短句接长，控制读速 |
| **E 对话** | 去 AI 腔，加口语化 | 删解释性对话（「你是说……」→「……？！」）。加口语词（嗯、行吧、啧） |
| **F 结尾** | 去升华，用动作收尾 | 删哲理收尾（「他知道…」「这一刻…」「命运…」）。改用具体动作/细节定格 |

#### 系统性去AI三遍法

```
Pass 1 — 去泛化：抽象词替换为具体细节
Pass 2 — 去书面化：书面腔替换为口语/动作
Pass 3 — 回自然感：注入停顿、犹豫、矛盾和口语感
```

#### 4.1 段落拆分（所有级别必做）

- 句号处换行，一句一段
- 对话独立成段
- 标题与正文间隔空行

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

```python
def validate_output(content):
    # 字数检查
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    issues = []
    if chinese_chars < 2000:
        issues.append(f"WARNING: 汉字数 {chinese_chars} < 2000")
    
    # 段落检查
    paras = [p for p in content.split('\n') if p.strip()]
    avg_len = sum(len(p) for p in paras) / len(paras) if paras else 0
    
    return issues, {"汉字数": chinese_chars, "段落数": len(paras), "平均段长": f"{avg_len:.0f}"}
```

---

## 单项质检命令

| 命令 | 功能 | 说明 |
|------|------|------|
| `deslop` | 仅去AI味 | 不跑禁令和审查，纯文本改写 |
| `ban-scan` | 仅禁令扫描 | 只检查硬性禁令 |
| `repair-paragraphs` | 仅段落修复 | 句号断段 + 对话独立 + 空行 |
| `doctor` / `preflight` | 项目体检 | 检查状态文件、设定/大纲/正文/追踪目录、JSON 合法性和缺失项 |

### deslop（去AI味 — 6 Gate）

专注于改写 AI 味文本，不审查不修禁令：

1. **级别选择**：默认自动检测级别；可指定 `--level mild|moderate|heavy`
2. **Gate A 禁用词**：查禁止词表，逐词替换
3. **Gate B 句式**：打散排比/对称/空洞抒情
4. **Gate C 心理外化**（中/重度）：情绪词→动作展示
5. **Gate D 节奏**（中/重度）：连续排比保留1-2个
6. **Gate E 对话**（重度）：去AI腔，加口语化
7. **Gate F 结尾**（重度）：去升华，动作收尾
8. **段落拆分**：句号换行，一句一段
9. **验证**：确保改写后字数变化不超过 ±10%

### ban-scan（禁令扫描）

纯扫描模式——不修改文件，只输出违规报告。

### doctor / preflight（项目体检 — 含缺口检测）

用于替代旧 `/webnovel-doctor` 的只读诊断，增加了从 detect-gaps 继承的 6 项缺口检查：

**基础检查：**
- 检查 `writer.json` / `project-state.json` 是否存在且 JSON 合法
- 检查 `setting/` 或 `设定/`、`outline/` 或 `大纲/`、`chapters/` 或 `正文/`、`tracking/` 或 `追踪/` 是否存在
- 统计正文章数、最近章节、低于 2000 汉字章节
- 扫描占位符：`TODO`、`待补`、`{}`、`【待】`

**缺口检测（仅在发现问题时报告）：**
1. **正文多设定少**：章节 > 10 但设定文件 < 3 → 建议补充设定
2. **AI味密度**：对正文执行快速禁令扫描（破折号/AI句式/AI高频词）
3. **异常伏笔**：检查追踪/伏笔.Hooks 中状态异常（非 未埋/已埋/已回收）的条目
4. **大纲缺失**：有正文但无大纲目录 → 建议创建大纲
5. **拆文未完成**：analysis_lib/ 下有 _progress.md → 提示继续拆解
6. **部署完整性**：.writer/ 结构是否完整

**所有检查只读，不修改任何文件。**

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
- 汉字数：{N}（≥2000: {PASS/FAIL})
- 段均长：{N}（变异系数: {N}）
- 可发布：{YES/NEEDS_REVISION}
```
