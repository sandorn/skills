# 手工编辑后版式检测与恢复流程

## 场景

用户在 Word 中手工修改了 `gb_gongwen.py` 生成的 `.docx`（增删条文、调整文字、改附件等），保存后样式体系可能被 Word 重排。**直接运行 `qa_docx.py` 会发现版式项目大量不通过**，但实际渲染字体可能正确。

本文件描述如何区分"真排版错误"与"假阳性"、如何诊断恢复、以及什么情况下可以接受。

## 检测工具链（5层）

### 第1层：`qa_docx.py` 初筛

```bash
python qa_docx.py 输出.docx
```

典型手工编辑后结果：版式项全部标❌，但内容完整性和编号连续性通过。区分假阳性。

### 第2层：PDF 渲染字体提取

```python
import fitz
from collections import Counter
d = fitz.open(r"文档.pdf")
fonts = Counter()
for b in d[0].get_text("dict")["blocks"]:
    for l in b.get("lines", []):
        for s in l["spans"]:
            fonts[(s["font"], round(s["size"]), bool(s["flags"] & 16))] += len(s["text"])
for k, v in fonts.most_common():
    print(f"字体={k[0]:30s} 字号={k[1]:5.1f} 粗={k[2]} 字数={v:4d}")
```

标准渲染值：标题=FZXBSJW--GB1-0 (22pt) / 章=SimHei (16pt) / 正文=FangSong_GB2312 (16pt)。

### 第3层：字符级扫描

```python
import zipfile, re
x = zipfile.ZipFile(r"文档.docx").read("word/document.xml").decode("utf-8")
paras = re.findall(r"<w:p[ >].*?</w:p>", x, re.S)
texts = ["".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", s, re.S)) for s in paras]
full = "\n".join(texts)
print("全角直引号:", full.count("＂"))
print("全角百分号:", full.count("％"))
print("弯引号 左:", full.count("“"), " 右:", full.count("”"))
half = [(i, t[:15]) for i, t in enumerate(texts) if re.match(r"^第[一二三四五六七八九十]+[条章] ", t)]
print("条号后半角空格:", len(half))
```

### 第4层：条号连续性

```python
CN = "〇一二三四五六七八九十"
def cn2int(s):
    if s == "十": return 10
    if s.startswith("十"): return 10 + CN.index(s[1])
    if "十" in s:
        a, b = s.split("十"); return CN.index(a)*10 + (CN.index(b) if b else 0)
    return CN.index(s)
nums = [cn2int(t) for t in texts if re.match(r"^第[一二三四五六七八九十]+条", t)]
print("条号连续:", nums == list(range(1,len(nums)+1)), "首:", nums[0], "末:", nums[-1] if nums else None)
```

### 第5层（可选）：附件表单一致性

正文新增字段与附件表头是否匹配、正文已删字段是否在附件中残留、签字栏与审批流程是否一致。

### 第6层（章条式专用）：表格出界检测

附件表宽度可能超版心导致右缘出界。从 PDF 的矢量图形提取边框：

```python
draws = last.get_drawings()
xs0 = [r["rect"].x0 for r in draws if r["type"] in ("s","f")]
xs1 = [r["rect"].x1 for r in draws if r["type"] in ("s","f")]
print(f"表格范围: {min(xs0):.0f}-{max(xs1):.0f}pt (版心79-516pt)")
```

版心右缘 = (11906 − 1588 − 1474) / 20 = 521.6pt。超出应等比缩放列宽。

### 第7层：附件表单元格合并结构

从原始 docx 提取真实合并结构，再重建：

```python
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
root = ET.fromstring(zipfile.ZipFile(src).read("word/document.xml"))
tbl = root.find(f".//{W}tbl")
for ri, tr in enumerate(tbl.findall(W+"tr")):
    out=[]
    for tc in tr.findall(W+"tc"):
        tcpr = tc.find(W+"tcPr")
        span = tcpr.find(W+"gridSpan") if tcpr is not None else None
        txt = "".join(t.text or "" for t in tc.iter(W+"t")).strip()
        tag = f"[span{span.get(W+'val')}]" if span is not None else ""
        out.append(f"{txt}{tag}")
    print(ri, " ‖ ".join(out))
```

## 恢复方案

如果版式检查通过量 < 20/25，或者表格溢出、用户要求标准版式，**不要手工修复 docx**：

1. 从当前 docx 或备份提取全文文本
2. 重新整理为正确格式的排版源 md
3. 条标式：`gb_gongwen.py` 重新生成；章条式：见 `officialdocuments-zhangtiao` skill 的方案B
4. 重跑 qa_docx → 要求 25/25 通过
5. 渲染 PDF 核验字体和表格范围
6. 删除中间 PDF（不交付）

## 参考

- `officialdocuments-zhangtiao/references/zhangtiao-layout.md` — 章条式制度排版指南
- `officialdocuments/references/format-spec.md` — GB/T 9704 排版规范