---
name: officialdocuments-zhangtiao
version: 1.0.0
description: 章条式（第X章/第X条）制度排版指南 — gb_gongwen.py 只支持条标式，本 skill 提供章条式的生成方案（自定义XML脚本）、附件表格规范、质检注意事项和用户偏好。
tags: [official-documents, 公文, 制度, 章条式, 排版]
category: document
---

# 章条式制度排版指南

## 背景

`gb_gongwen.py` 仅支持**条标式**（`一、` / `（一）` / `1．`）三级标题层次，其 `H1_RE`/`H2_RE`/`H3_RE` 正则不识别 `第X章` / `第X条` 格式。直接喂入章条式 md 会使整篇降级为正文，标题样式全部丢失。

本章条式又称"总则/采购方式/附则"式，适用于制度/管理办法/实施细则类文档。与条标式的区别：

| 层次 | 条标式（默认） | 章条式（本指南） |
|------|----------------|-----------------|
| 篇首 | 公司名称 + 办法名 | 同左 |
| 一级（章） | 一、二、三……（"一、总则"） | 第X章（"第一章　总则"） |
| 二级（条） | （一）（二）（三）…… | 第X条（全篇连续编号） |
| 三级（款） | 1．2．3．…… | （一）（二）……（每条约重置） |
| 四级（项） | （1）（2）（3）…… | 同左 |

## 生成方案

### 方案A：条标式 md + 手动替换（最简单）

1. 按条标式撰写 md（`一、总则` / `（一）目的与依据` / `1．` / `（1）`）
2. `python gb_gongwen.py input.md output.docx`
3. 在 Word 中替换：`一、总则` → `第一章　总则`（保留黑体三号），`（一）` → `第一条　`（保留正文样式）
4. 逐条调整字体与编号。**注意**：手动操作后须重新跑 `qa_docx.py`——仅样式ID判断，章标题用style14时质检会报"没找到'一、'"，属误报，忽略。

### 方案B：自定义脚本（推荐，完整验证通过）

核心思路：复用 gb_gongwen 的 `STYLES`（字体/行距/页边距定义）和 `_xml_styles()` / `_xml_content_types()` / `_xml_rels()` 等样板部件，仅自行发射 document.xml。

```python
import importlib.util
spec = importlib.util.spec_from_file_location("g", r"path/to/gb_gongwen.py")
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)

# 关键常量
LS = g.LINE_SPACING      # 600（固定30磅）
FI = g.FIRST_INDENT      # 640（首行缩进2字符）

def run(text, bold=False):
    b = "<w:b/>" if bold else ""
    return f'<w:r><w:rPr>{b}</w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r>'

# 章标题：黑体三号居中，无首行缩进，上下留空
def p_chapter(text):
    return (f'<w:p><w:pPr><w:pStyle w:val="14"/>'
            f'<w:jc w:val="center"/>'
            f'<w:spacing w:line="{LS}" w:lineRule="exact" '
            f'w:before="120" w:after="60"/></w:pPr>{run(text)}</w:p>')

# 条文/款项：仿宋_GB2312三号正文，首行缩进
def p_body(text):
    return (f'<w:p><w:pPr><w:pStyle w:val="19"/>'
            f'<w:jc w:val="both"/>'
            f'<w:ind w:firstLine="{FI}"/>'
            f'<w:spacing w:line="{LS}" w:lineRule="exact"/>'
            f'</w:pPr>{run(text)}</w:p>')

# 章/条识别
CH_RE = re.compile(r"^第[一二三四五六七八九十]+章")
ART_RE = re.compile(r"^第[一二三四五六七八九十]+条")
```

然后遍历纯文字段落列表，用 `CH_RE`/`ART_RE` 区分后调用相应发射函数，组装 document.xml，使用 gb_gongwen 的 `_xml_styles()`/`_xml_content_types()` 等样板部件打包为 zip。

## 附件表格规范

章条式制度中的附件表（采购需求单等）必须：

1. **宽度 ≤ 版心宽** = `PAGE["width"] - PAGE["left"] - PAGE["right"]` = 11906 − 1588 − 1474 = **8844 twips**
2. **按 GB/T 9704 页边距对齐**：表左缘对齐正文左缘，与页面左边距保持 28mm
3. **行高 hex 数**：`<w:trHeight w:val="560" w:hRule="atLeast"/>`（留出手写空间的空行）

列宽计算公式：用源表的列宽等比例缩放到 8844。单元格合并用 `<w:gridSpan w:val="N"/>`。

附件以分页符开始：`<w:pageBreakBefore/>`。

## 质检注意事项

| 检查项 | 章条式下行为 |
|--------|-------------|
| 样式13（标题） | ✅ 正常 |
| 样式14（一级标题） | ✅ 但 14-num 子检查会报"不存在'一、'"——**误报，属质检器缺陷**，忽略 |
| 样式19（正文） | ✅ 正常 |
| Markdown残留 | ✅ 正常 |
| 二级编号（一）（二） | ✅ 每条约重置 |
| 三级编号 1．2． | ✅ 不受章条式影响 |
| 段落版式 | ✅ 首行缩进640 + 固定行距600 |
| 页边距 | ✅ 2098/1985/1588/1474 twips |
| 表格宽度 | ✅ 不超8844 |

## 用户偏好（中言地产 Sandhill）

该用户的制度类文件偏好 —— 写入 `documents/officialdocuments-zhangtiao` 参考：

- 优先使用**章条式**而非条标式
- 附件表嵌入正文同一 docx，不单独生成
- 制度开头："正确的废话"风格——原则性标准性内容，不增加甲方落地动作量
- 弹性措辞："定期或不定期""协调参与"等，不写死频次/成员
- 评分/等级/区间归附件不入正文
- 篇幅约2.5–3页（标准公文排版）

## 参考

- `officialdocuments/references/docx-md-structure-mapping.md` — 条标式↔章条式转换的层面对应关系
- `officialdocuments/references/errors.md` 缺陷4 — `cn_num()` >10 编号修复
- `officialdocuments/references/manual-edit-qc.md` — 用户手工编辑 docx 后恢复版式的检测流程
- `officialdocuments/scripts/gb_gongwen.py` — 排版引擎源码
- `officialdocuments/scripts/qa_docx.py` — 质检工具