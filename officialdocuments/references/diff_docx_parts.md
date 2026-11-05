# 修复稿内容零影响验证脚本

用途：对存量 docx 做包级修复（fix_theme_fonts.py 等）后，证明「除指定目标部件外，包内一切未动、正文逐字未变」。这是向用户交付修复结果前的强制验证步骤。

用法（3 个参数起：修复前 docx、修复后 docx、额外允许改动的部件）：

```bash
python diff_docx_parts.py 修复前.docx 修复后.docx word/styles.xml word/fontTable.xml
```

判定标准：
- 部件清单前后无增减；
- 非目标部件（除 theme1.xml/settings.xml + 命令行允许的部件外）字节完全一致；
- `word/document.xml` 逐段 `<w:t>` 文本 diff 为空。

已知陷阱：
- docx 被 Word/WPS 打开占用时，zipfile 打开会报 "used by another process"（PowerShell ZipFile 同样受限），需先让用户关闭文件再跑验证；
- 比对脚本用完即删（临时文件），或落地在项目 _tmp 命名下由调用方清理。

```python
#!/usr/bin/env python3
"""对比 docx 修复前后：正文文本逐段 diff + 除指定部件外全部字节比对。"""
import sys, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

old, new = Path(sys.argv[1]), Path(sys.argv[2])
EXTRA_ALLOWED = set(sys.argv[3:])  # 额外允许改动的部件

def load(p):
    with zipfile.ZipFile(p) as z:
        return {i.filename: z.read(i.filename) for i in z.infolist()}

a, b = load(old), load(new)
ka, kb = set(a), set(b)
print("仅修复前有:", ka - kb or "无")
print("仅修复后有:", kb - ka or "无")

TARGETS = {"word/theme/theme1.xml", "word/settings.xml"} | EXTRA_ALLOWED
changed = [n for n in ka & kb if n not in TARGETS and a[n] != b[n]]
print("被改动的非目标部件:", changed or "无")

NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
def paras(d):
    root = ET.fromstring(d["word/document.xml"])
    return ["".join(t.text or "" for t in p.iter("{%s}t" % NS))
            for p in root.iter("{%s}p" % NS)]

pa, pb = paras(a), paras(b)
print("段落数: %d -> %d" % (len(pa), len(pb)))
print("✅ 全部 %d 段文本逐字一致，内容零影响" % len(pa) if pa == pb else "❌ 段落存在差异")
```
