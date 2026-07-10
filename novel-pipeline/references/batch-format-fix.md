# 批量格式修复工作流

> **适用范围**：全卷格式禁令修复（B01-B06）、AI 高频词精修、段落拆分（**格式/文风层**的批量修改）
> **与 `mass-edit-workflow.md` 的分工**：
> - 本文 → 引号/破折号/AI 高频词/超长段等**格式层**修复
> - mass-edit-workflow.md → 修为/称呼/伏笔/名词等**剧情/设定层**跨章统一

## 修复执行顺序

```
Step 1: B02 破折号     → 替换为，或……
Step 2: B01 对话引号    → 弯引号→「」
Step 3: B06 超长段拆分  → 句号处断段
Step 4: B03 不是而是    → 重组为肯定句
Step 5: B05 AI高频词    → 轮换替换池
Step 6: state-files更新 → archive_state.py同步
```

**为什么要按这个顺序**：破折号和引号替换会改变句子结构，先做再拆分段落。B03 会导致句式变化，也先于段落拆分。B05 只替换单个词，不改变句子结构，放最后。

---

## Step 1: B02 破折号修复

将 `——`（U+2014×2）替换为上下文合适的标点。

| 位置 | 替换方案 | 示例 |
|------|---------|------|
| 对话内（「」包围） | `……` | 「啊——」→「啊……」 |
| 叙述中（解释性） | `，` | 正西方向——那是黑石镇 → 正西方向，那是黑石镇 |
| 叙述中（强调性） | `，` 或删除 | 这件事——他必须做 → 这件事，他必须做 |

```python
def fix_b02(text):
    """修复 —— 破折号"""
    in_dialogue = False
    result = []
    for i, ch in enumerate(text):
        if ch in '「「':
            in_dialogue = True
        elif ch in '」」':
            in_dialogue = False
        if i+1 < len(text) and text[i:i+2] == '\u2014\u2014':
            result.append('……' if in_dialogue else '，')
            continue  # skip the second dash (handled by skipping next iter)
        result.append(ch)
    return ''.join(result)
```

---

## Step 2: B01 对话引号统一

将弯引号 `""`（U+201C/U+201D）和直引号 `"` 统一替换为 `「」`。

关键：**全量替换是幂等的**——对已使用 `「」` 的章节无害，因为 `「` 和 `」` 不在替换目标中。

```python
def fix_b01(text):
    text = text.replace('\u201c', '\u300c')  # 左弯引→「
    text = text.replace('\u201d', '\u300d')  # 右弯引→」
    text = text.replace('\u2018', '\u300c')  # 左单弯→「(兜底)
    text = text.replace('\u2019', '\u300d')  # 右单弯→」(兜底)
    text = text.replace('"', '\u300c')       # ASCII直引号→「
    return text
```

> ⚠️ ASCII直引号 `"` 替换为 `「` 会丢失左右区分——如果章节中有配对使用 `"text"` 的场景，需要后续手动补 `」` 在结尾。但网文中裸露的直引号远少于弯引号，可接受。

---

## Step 3: B06 超长段拆分

对每段超过 42 汉字的段落，按句末标点拆分子段。

```python
import re

def split_paragraph(para):
    """按句末标点拆分，递归处理仍超长的子段"""
    han_count = len(re.findall(r'[\u4e00-\u9fff]', para))
    if han_count <= 42:
        return [para]
    
    parts = re.split(r'(?<=[。！？」…])\s*', para)
    parts = [p.strip() for p in parts if p.strip()]
    
    result = []
    for part in parts:
        if len(re.findall(r'[\u4e00-\u9fff]', part)) > 42:
            # 在分号/逗号处二次拆分
            sub = re.split(r'(?<=[；，])\s*', part)
            result.extend(s.strip() for s in sub if s.strip())
        else:
            result.append(part)
    return result
```

---

## Step 4: B03 不是…而是…修复

将「不是A，而是B」结构重组为肯定句或分句。

| 原句 | 替换 |
|------|------|
| 不是暴动，而是起义 | 是起义，不是暴动 |
| 不是冲着他去的，而是冲着宝物 | 冲着他去的，更是冲着宝物 |
| 根本不是天魔殿的路数，而是青云宗的功法 | 根本不是什么天魔殿的路数，实则是青云宗的功法 |

注意上下文：有的「不是…而是…」是角色对话的自然表达（「我不是这个意思，而是……」），这类应保留。

```python
def fix_b03(text):
    """修复不是...而是... 模式"""
    # 叙述中的先替换
    text = re.sub(r'不是([^，。]*?)，而是([^，。]*?)[。，]',
                  lambda m: f'{m.group(2)}，不是{m.group(1)}。', text)
    # 跨行模式
    text = re.sub(r'不是([^，。\n]*?)\n而是([^，。\n]*?)[。，\n]',
                  lambda m: f'{m.group(2)}，不是{m.group(1)}。', text)
    return text
```

---

## Step 5: B05 AI高频词精修

### 诊断先行

```python
# 先扫描全卷确定频次分布
AI_WORDS = ['突然','忽然','仿佛','似乎','他知道','眼中闪过一丝','深吸一口气','心中一动']
for ch in range(31, 81):  # 扫全卷或目标卷
    text = open(f'chapters/ch{ch}.md').read()
    for w in AI_WORDS:
        count = text.count(w)
        if count > 0: print(f'ch{ch}: {w}x{count}')
```

### 红黄分区

| 区级 | 频次/章 | 目标 |
|------|---------|------|
| 红区 | ≥10次 | 降到≤4 |
| 黄区 | 5-9次 | 降到≤3 |
| 绿区 | ≤4次 | 可跳过 |

### 轮换替换池

关键：**使用轮换池避免替换词单调重复**（例如整章全是「猛地」也显得AI化）。

```python
REPLACEMENTS = {
    '突然':     ['猛地', '骤然', '猝然', '冷不丁', '瞬间'],
    '忽然':     ['猛然', '霎时', '转眼', '骤然间'],
    '深吸一口气': [None, None, '吸了口气', '深呼吸了一下', '缓缓吐气'],
    '他知道':   [None, None, '心里清楚', '心中明白'],
    '仿佛':     ['像是', '如同', '就好比'],
    '眼中闪过一丝': ['眼底掠过一丝', '目光微闪', '眼中闪过一抹', '神色微动'],
    '心中一动': ['心念电转', '心头一跳', '心神微动'],
}
```

- `None` = 直接删除该词（常用于「他知道」「深吸一口气」）
- 轮换索引 `idx % len(pool)` 确保不同位置用不同替换

### 对话保护

**核心规则：对话内的 AI 高频词不替换**。角色说话时用「突然」「他知道」是自然的。

```python
def is_in_dialogue(text, pos):
    """检查位置pos是否在「」对话内"""
    before = text[max(0, pos-500):pos]
    opens = before.count('「') + before.count('「')
    closes = before.count('」') + before.count('」')
    return opens > closes
```

### 验证

修复后用同一诊断脚本复扫，确认：
- 红区章节清零（全卷无≥10次/章的章节）
- 残留词在对话内（人工抽查确认自然）

---

## Step 6: state-files + archive 同步

格式修复后，如果卷内有关键剧情进展（突破/救出/获取物品），必须更新 state-files：

```json
{
  "changes": {
    "chapter_number": 80,
    "foreshadowing": {
      "new": [{"id": "f-008", "description": "...", "planted_chapter": 80}],
      "resolved_ids": ["f-002"]
    },
    "characters": [
      {"name": "林尘", "cultivation_level": "筑基初期", "chapter_number": 80}
    ]
  }
}
```

通过 `archive_state.py` 写入：

```python
# 通过子进程调用，避免BOM问题
import subprocess, json
payload = json.dumps({"changes": {...}})
proc = subprocess.run(
    [python_path, 'hooks/archive_state.py'],
    input=payload, capture_output=True, text=True, encoding='utf-8'
)
```

---

## 终验模板

修复完后执行全卷终验脚本，确认 S1 禁令清零：

```python
# 终验：B01-B07 逐章扫描
statuses = []
for ch in range(31, 81):
    text = open(f'chapters/ch{ch}.md').read()
    b02 = text.count('\u2014\u2014')
    b01 = text.count('\u201c') + text.count('\u201d')
    # ... etc
    statuses.append('✅' if b01==b02==b06_ok else '❌')
```

---

## 注意事项

1. **备份先行**：每步修复前 `_bak_*` 目录备份原始文件
2. **幂等脚本**：脚本设计为幂等——对已修复章节无害，可在已修复文件上重复运行
3. **对话内保留**：B03/B05 在对话内保留原词（角色自然语言）
4. **清理临时文件**：修复完成后删除 `_fix_tools/`、`_bak_*/` 和所有 `.py` 临时脚本
5. **跨行模式**：B03「不是……而是……」可能跨行（`\n`），正则需要用 `[^。\n]` 而非 `[^。]`
6. **扫描结果冲突处理**：项目中可能遗留多个版本的扫描结果文件（如 `_v2_scan.json` 和 `_vol2_scan_result.json`），不同工具对同一指标的判定标准可能不同。**不要信任任何既有扫描文件**——直接写一个纯净的 Python 脚本对目标章节重新做全量扫描。

## 常见陷阱：机械修复 ≠ 审查完成

批量修复只解决**格式层问题**。格式清零后**必须补做剧情/设定层深筛**（参见 `volume-audit-protocol.md` 的 Round 1-3 检查），否则会漏掉剧情层的 S1 级矛盾。

### 本会话实际发现的 S1 漏检案例

| 问题 | 章节 | 类型 | 说明 |
|------|------|------|------|
| 卷间时间线断裂 | ch80→ch81 | S1 | vol2 ch80 众人已传送至丹塔，vol3 ch81 开头回到天魔岭战场废墟，无过渡/闪回标记 |
| 修为设定冲突 | ch91 | S1 | 写"早已卡在练气八层巅峰"，但 vol2 ch48 林尘已突破筑基初期——跳过了整个筑基期 |
| 地点名称错误 | ch110 | S1 | 写"九天灵域的天空"，但此时故事仍在苍玄大陆青云宗 |

### 跨卷 state-files 校验清单

每次新卷审查时，用 outline + state-files 对前 5 章做三向校验：

1. **人物修为**：characters.json 中 cultivation_level vs 本卷开头正文 — 是否对齐？
2. **地理位置**：world_setting.json 中 geography vs 正文开头场景 — 是否一致？
3. **时间线延续**：vol_N 结尾事件时间与 vol_N+1 开头时间 — 有无断裂？
4. **已获物品**：power_system.json 中 equipment vs 正文中角色持有的物品 — 有无丢失/遗忘？
5. **角色状态**：characters.json 中 status vs 正文 — 已故角色是否仍在对话中活着？

### 可靠检测方法

不要依赖肉眼通读发现卷间断裂。推荐用 Python 脚本做三向交叉校验：

```python
# 三向校验：outline → state-files → 正文开头
import json, re

# 1. 加载 state-files
characters = json.load(open('state-files/characters.json', encoding='utf-8'))

# 2. 读本卷开头 3 章
for ch in [81, 82, 83]:
    text = open(f'chapters/ch{ch}.md', encoding='utf-8').read()
    first_500 = text[:500]
    
    # 检查 vol_N 结尾的关键事件是否被引用
    if '密林' in first_500 and ch == 81:
        print('[CHECK] vol2结尾在丹塔，vol3开头在密林 — 需加过渡')

    # 检查 characters.json 中标记的已故人物是否还在对话
    for char in characters['characters']:
        if char.get('status') == 'deceased':
            if char['name'] in text:
                print(f'[CHECK] {char["name"]}已标记为deceased但在ch{ch}中出现')
```
