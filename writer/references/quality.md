# 质检工单：全链路质量控制

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

检查目标文件（默认当前最后写的章节或指定章节）。

> **禁令定义**：`references/hard-bans.md`（单一事实来源）。**执行扫描**：`scripts/audit.py`。

对 blocking 级问题逐项修复：

> **禁令定义**：`references/hard-bans.md`（单一事实来源，P0-P2 分级）。`quality.md` 不定义禁令，仅定义修复策略。
> **项目扩展**：如项目 `setting/writing_rules.md` 中有更严格的禁止词，以项目规范为准，但与 hard-bans.md 冲突时 hard-bans.md 优先。

| 修复维度 | 修复规则 |
|------|---------|
| 破折号/引号 | `audit.py` + `sed` 批量清除；对话打断可保留但标注 |
| 「不是…而是…」句式 | 删除否定部分，仅保留正面陈述 |
| 元叙事标签 | 直接删除 |
| 分析术语 | 改写为具体动作和描写 |
| AI高频词 | 逐词替换（忽然→猛地/突然；深吸一口气→缓了缓；他知道→意识到/察觉） |
| 模板复制 | `audit.py` 自动检测；章末相同→S1 阻塞，逐章重写 |

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
- 每段≤60汉字（对话和内心独白除外，项目规范以 `设定/写作规范.md` 为准）
- 对话独立成段
- 标题与正文间隔空行

**注意：批量字数扩充时的段落陷阱。** 用 `echo >>` 或批处理追加文字来扩充字数时，追加内容通常会变成一行超长段落（数百汉字）。扩充完成后必须跑句号拆分——按 `。！？` 断段，确保每段≤60汉字。拆分脚本见 `scripts/split_paragraphs.py`。

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
    # 项目规范优先：≥2500 汉字（部分项目要求 ≥2000，以 `设定/写作规范.md` 为准）
    threshold = 2500  # 默认值，项目规范可能覆盖
    if chinese_chars < threshold:
        issues.append(f"WARNING: 汉字数 {chinese_chars} < {threshold}")
    
    # 段落检查
    # 段落检查：每段≤60汉字（对话和内心独白除外）
    paras = [p.strip() for p in content.split('\n') if p.strip()]
    long_paras = [p for p in paras if len(re.findall(r'[\u4e00-\u9fff]', p)) > 60]
    if long_paras:
        issues.append(f"ERROR: {len(long_paras)} 段超过60汉字上限")
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

专注于改写 AI 味文本，不审查不修禁令。

> **选择指引**：批量快速清除（≥10章）用 deslop；逐句精修（≤5章或作者要求高标准）用 [`manual-polish.md`](manual-polish.md)。

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
- 检查 `writer.json` 是否存在且 JSON 合法
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

### RAG 健康检查（利用项目知识库）

当项目知识库工具已部署时，doctor 额外执行以下健康检查：

```bash
# 1. 检查知识库工具是否可连接
IDX_TOOL="index-tool"
if ! command -v $IDX_TOOL &>/dev/null; then
    echo "❌ 项目知识库工具未安装"
else
    # 2. 索引状态
    STATUS=$($IDX_TOOL cli index_status '{"project":"<project>"}' 2>/dev/null)
    echo "📊 索引状态: $STATUS"

    # 3. 索引覆盖：统计已索引文件 vs 实际文件
    INDEXED=$($IDX_TOOL cli query_graph '{"project":"<project>","query":"MATCH (f:File) RETURN count(f)"}' 2>/dev/null)
    ACTUAL=$(find chapters/ -maxdepth 1 -name '*.md' | wc -l)
    echo "📁 索引覆盖: ${INDEXED:-?} 已索引 / ${ACTUAL} 实际"

    # 4. 抽样验证：最新5章是否在索引中
    LATEST=$(ls -t chapters/*.md | head -5 | xargs -I{} basename {})
    for f in $LATEST; do
        FOUND=$($IDX_TOOL cli query_graph "{\"project\":\"<project>\",\"query\":\"MATCH (f:File) WHERE f.name = \\\"$f\\\" RETURN f.name\"}" 2>/dev/null)
        if [ -z "$FOUND" ] || [ "$FOUND" = "{}" ]; then
            echo "⚠️  最新章未索引: $f"
        fi
    done
fi
```

**检查清单**：
- □ 项目知识库 CLI 可访问
- □ 索引状态为 ready
- □ 已索引文件数 ≈ 实际文件数（偏差 < 5% 为正常）
- □ 最新 5 章均在索引中
- □ stderr 日志无异常（检查 2>/dev/null 过滤是否正常）

### 事实库状态检查

当 facts.db 存在时，doctor 额外检查：

```bash
if [ -f ".writer/facts.db" ]; then
    echo "📦 facts.db 存在"
    python3 scripts/fact_db.py status .
else
    echo "📦 facts.db 未初始化 — 运行: python3 scripts/fact_db.py init ."
fi
```

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

---

## 批量章节质检工作流

连续写多章后的质检，用一体化扫描命令一次性检查所有章节，然后逐章定点修复。

### 批量字数 + 禁令一体化扫描命令

```bash
cd "{project_root}" && python3 -c "
import re, os
for f in sorted(os.listdir('chapters')):  # 或 'chapters'
    if f.endswith('.md'):
        path = os.path.join('chapters', f)
        text = open(path, 'r', encoding='utf-8').read()
        chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
        dashes = len(re.findall('——', text))
        ai_phrases = len(re.findall(r'不是.*而是|眼中闪过一丝|深吸一口气|忽然(?![的])|突然(?![的])|心中一动|他知道|似乎|仿佛', text))
        status = 'PASS' if chinese >= 2500 and dashes == 0 and ai_phrases == 0 else 'FAIL'
        issues = []
        if chinese < 2500: issues.append(f'字数{chinese}')
        if dashes > 0: issues.append(f'破折号{dashes}')
        if ai_phrases > 0: issues.append(f'AI句式{ai_phrases}')
        print(f'{f}: {chinese}字 破折号={dashes} AI={ai_phrases} [{status}]')
"
```

> **注意**：字数阈值按项目写作规范调整（默认 2500）。禁止词清单见 `hard-bans.md` B05。

### 破折号批量修复命令

```bash
# 两遍修复法
python3 -c "
import re, os
base = '正文'
for f in os.listdir(base):
    if not f.endswith('.md'): continue
    p = os.path.join(base, f)
    t = open(p, encoding='utf-8').read()
    lines = t.split('\n')
    title = lines[0]
    body = '\n'.join(lines[1:])
    body = body.replace('\u2014\u2014', '\u3002')
    body = body.replace('\u2014', '\u3002')
    body = re.sub(r'\u3002{2,}', '\u3002', body)
    open(p, 'w', encoding='utf-8').write(title + '\n' + body)
print('破折号清零完毕')
"
```

> ⚠️ **引号断裂陷阱**：直接用 `replace('——', '。')` 会导致引号断裂。上述 Python 脚本已内置句号连接修复。

### AI 句式批量替换

```bash
python3 -c "
import re, os
os.chdir('正文')
REPLACE = {
    '\u2014\u2014': '\u2014',
    '他知道': '他清楚',
    '突然': '一下子',
    '忽然': '骤然',
    '似乎': '好像',
    '仿佛': '像',
    '眼中闪过一丝': '眼里掠过一丝',
    '深吸一口气': '深深吸了口气',
    '心中一动': '心头一跳',
}
for f in sorted(os.listdir('.')):
    if not f.endswith('.md'): continue
    t = open(f, encoding='utf-8').read()
    orig = t
    for old, new in REPLACE.items():
        t = t.replace(old, new)
    if t != orig:
        open(f, 'w', encoding='utf-8').write(t)
        print(f'{f}: fixed')
print('Done.')
"
```

> **注意**：AI 句式批量替换是粗粒度操作。推荐先用批量替换快速过一遍，再手动检查替换后的句子是否通顺。

### 通用段落重复扫描（模板复制检测）

```python
# 在内联脚本/代码执行中运行
import re, os
from difflib import SequenceMatcher

base = '正文'
files = sorted([f for f in os.listdir(base) if f.endswith('.md')])

def get_paragraphs(path):
    text = open(os.path.join(base, path), encoding='utf-8').read()
    lines = text.split('\n')
    paras = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'): continue
        cn = len(re.findall(r'[\u4e00-\u9fff]', stripped))
        if cn >= 30:
            paras.append(stripped)
    return paras

chapter_paras = {f: get_paragraphs(f) for f in files}

for i in range(len(files)):
    for j in range(i+1, len(files)):
        fi, fj = files[i], files[j]
        for pi, pa in enumerate(chapter_paras[fi]):
            for pj, pb in enumerate(chapter_paras[fj]):
                if abs(len(pa) - len(pb)) / max(len(pa), len(pb)) > 0.2:
                    continue
                ratio = SequenceMatcher(None, pa, pb).ratio()
                if ratio > 0.85:
                    print(f'DUPLICATE {ratio:.2%}: {fi} L{pi+1} ↔ {fj} L{pj+1}')
```

> **检测标准**：同一段落在≥5章出现即构成模板复制（S1）。2-4章出现为警告（S2）。

### 因果句扫描（部分项目禁用）

```bash
grep -cE '因为|所以|由于' 正文/ch*.md
```

违规阈值：单章内 `因为 + 所以 + 由于` 合计 > 1 即不合格。

流程：
1. **批量扫描**：用 Python 一体化命令输出所有章节的字数+禁令状态
2. **标记 FAIL**：找出所有 FAIL 章节
3. **逐章修复**：优先修破折号（可批量 sed），再逐项修 AI 句式
4. **扩充短章**：字数不足的章节通过**五层叠料法**扩充：
   - **感官层**：加环境细节（气味、温度、光线、声音、材质触感）
   - **围观层**：加配角/围观者反应（表情、低语、动作、姿态变化）
   - **心理层**：延长主角内心动作（回忆、对比、预判，但不用「他知道」「他想起」等套话）
   - **物件层**：加场景道具的物理细节（新旧、磨损、位置、触感）
   - **对话层**：延长对话中的沉默、停顿、小动作，让对话有呼吸感
   
   注意：叠料不改情节。所有新增内容必须落在已有场景内，不另起新事件。

   **⚠️ 扩充后必须跑段落拆分。** 无论用何种方式追加文字（echo >>、批处理、Python write），追加内容极易变成超长行（数百汉字挤在一行）。扩充完成后立即运行 `scripts/split_paragraphs.py --batch <正文目录>` 按句号拆分，确保每段≤60汉字。

5. **复检**：修完后重新运行一体化扫描确认全部 PASS（段落≤60 + 字数≥2500 + 禁令清零 + 标题格式）
