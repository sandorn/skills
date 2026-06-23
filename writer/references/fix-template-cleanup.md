# 模板复制与乱码清除修复工作流

## 适用场景

`pad_chapter.py` 或批量字数追加后，发现多章章末存在相同/近似的收尾段落，或 safe_pad 乱码残留。

---

## 根因演进

| 版本 | 问题 | 修复 |
|------|------|------|
| v2 | 主题句池每类仅2-3句，耗尽后回退到3个硬编码收尾句 | 跨章模板复制 |
| v3 | 句池翻倍但共享同一意象体系——「梧桐叶轻轻晃了一下」跨60章命中108次 | 关键词注入不解决意象共享问题 |
| v4 | 关键词注入式唯一收尾（「他把X又看了一遍」），虽消除共享意象但结构骨架相同 | 审查Agent误报模板，截断残留93章（「他端起杯子喝了一口。水是温」） |
| **v5.1（当前）** | 彻底废除模板池和收尾句体系。从章节末段提取有效名词+感官元素，生成与正文自然衔接的内容延伸，无独立收尾段结构 | 无模板风险 |

---

## 乱码模式（safe_pad v4及以前）

### 1. 关键词注入截断：`X的数据还在屏幕上。没有变化。他`

**正则**：`\S{1,6}的数据还在屏幕上[。，]?\s*没有变化[。，]?\s*他\s*$`

示例：`的月亮的数据还在屏幕上。没有变化。他`、`黑色的数据还在屏幕上。没有变化。他`

### 2. 乱码收尾：`他把X又看了一遍`

**正则**：`他把.{1,8}又看了一遍[。，]?\s*$`

当 X 是碎片词时清除：`色的`、`面写着`、`咯噔`、`他说`、`看又看`、`把笔放`、`把灯关`

### 3. 变量错位：`在X的边上写了一个字`

**正则**：`在.{1,8}的边上写了一个字[。，]?\s*`

当 X 不是实体名词时清除：`饺子`、`魏之明`、`黑色`、`深蓝色`、`赫兹`

### 4. 占位符未替换

| 占位符 | 含义 | 出现 |
|--------|------|------|
| `的月亮` | 关键词碎片 | 13+章 |
| `黑色` | 未替换变量 | 数章 |
| `深蓝色` | 未替换变量 | ch420 |
| `赫兹` | 未替换变量 | ch419 |

### 5. Shell命令混入正文

**模式**：`>> ch298-除夕.md; done && for f in ...; do echo ...`

出现在批处理脚本合并文件时操作残留。

---

## 通用段落重复扫描

检测任意两章之间是否存在高度相似的段落（Jaccard 相似度 > 0.85 的 100 字以上段落）：

```python
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
                    print(f'  A: {pa[:80]}...')
                    print(f'  B: {pb[:80]}...')
```

**检测标准**：同一段落在≥5章出现即构成模板复制（S1）。2-4章出现为警告（S2）。

---

## 修复流程

### Step 1：sed 批量清除非唯一模板

```bash
cd "D:/Writer/项目/正文/"
for f in ch*.md; do
  sed -i 's/他靠在椅背上。闭上眼睛。窗外的风穿过梧桐叶。沙沙地响。//g' "$f"
  sed -i 's/从一个人翻到一群人。书还很长。但他不急。一步一步来。//g' "$f"
  sed -i 's/他把灯关了。屏幕上的蓝光映在墙上。//g' "$f"
done
```

### Step 2：正则清除乱码

```python
import re, os

garbage_patterns = [
    (r'\S{1,6}的数据还在屏幕上[。，]?\s*没有变化[。，]?\s*他\s*$', ''),
    (r'他把(?:色的|面写着|咯噔|他说|看又看|把笔放|把灯关)又看了一遍[。，]?\s*$', ''),
    (r'在(?:饺子|魏之明|黑色|深蓝色|赫兹)的边上写了一个字[。，]?\s*', ''),
    (r'>> ch\d.*$', ''),
]

base = '正文'
for f in sorted(os.listdir(base)):
    if not f.endswith('.md'): continue
    fp = os.path.join(base, f)
    with open(fp, 'r', encoding='utf-8') as fh:
        t = fh.read()
    orig = t
    for pat, repl in garbage_patterns:
        t = re.sub(pat, repl, t)
    if t != orig:
        with open(fp, 'w', encoding='utf-8') as fh:
            fh.write(t)
        print(f'{f}: garbage cleared')
```

### Step 3：清理多余空行 + 重新生成延伸

```python
import re, os

base = '正文'
for f in sorted(os.listdir(base)):
    if not f.startswith('ch'): continue
    fp = os.path.join(base, f)
    with open(fp, 'r', encoding='utf-8') as fh:
        t = fh.read()
    # 清理连续空行
    lines = t.split('\n')
    clean = []
    prev_empty = True
    for l in lines:
        e = l.strip() == '' and not l.startswith('#')
        if e and prev_empty: continue
        clean.append(l)
        prev_empty = e
    with open(fp, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(clean))
```

### Step 4：全量验证

```python
# 确认模板清零 + 字数达标
bad_pats = [
    r'从第一页翻到最后一页。从宁市的铺面翻到冰城的风雪',
    r'这些声音他听了很久。从来没有听腻。他把灯关了。靠在椅背上。闭上眼睛。',
]
for f in sorted(os.listdir(base)):
    if not f.startswith('ch'): continue
    with open(os.path.join(base,f),'r',encoding='utf-8') as fh:
        t = fh.read()
    for p in bad_pats:
        if re.search(p, t):
            print(f"❌ {f}: 模板残留")
```

## 实战数据

| 修复轮次 | 方法 | 版本 | 清除章数 | 残留 |
|---------|------|------|---------|------|
| 第1轮 | 连续块删除 | v2残留 | 32 | 79 |
| 第2轮 | 精确多行模板 | v2残留 | ~400 | 5 |
| 第3轮 | sed 批量替换 | v2残留 | 34 | **0** |
| 第4轮 | sed + v4独特结尾 | v3残留 | 47 | **0** |
| 第5轮 | 正则清除+parse截断行+v5补全 | v4截断残留 | 78 | **0** |

## 关键教训

1. **不要用宽泛正则**：`梧桐叶.*沙沙地响` 会误伤正常白描
2. **精确多行模板优先**：先匹配完整模板段，再匹配单行片段
3. **关键词注入不解决模板复制**：共享意象骨架即使注入不同关键词，跨章仍形成语义模板
4. **独立收尾段本身就是问题**：v5.1 彻底废除——延伸内容与正文融为一体，无独立段落
5. **关键词注入必须过滤碎片词**：任意2-4字中文字符≠有效名词
6. **占位符替换必须有回退**：模板变量名未被实例化时，应跳过而非写入占位符文本
