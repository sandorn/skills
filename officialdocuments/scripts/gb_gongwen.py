#!/usr/bin/env python3
"""GB/T 9704-2012 标准公文 docx 排版引擎（纯 XML+zipfile）。

用途：
    生成符合常用公文版式的 .docx，避免仅用 pandoc 导致中文字体、页边距、
    行距、首行缩进、标题层级等格式丢失。

两种用法：

1) 作为 Python 模块调用（保留原脚本接口）::

    from gb_gongwen import generate
    parts = [
        ("13", "关于XXX的报告"),
        ("19", "正文内容……", True),
        ("14", "主要问题"),      # 自动编号为：一、主要问题
        ("15", "具体表现"),      # 自动编号为：（一）具体表现
        ("16", "制度建设方面"),  # 自动编号为：1．制度建设方面
        ("19", "正文……", True),
        ("sign", "发文机关", "2026年6月19日"),
    ]
    generate(parts, "output.docx")

2) 命令行调用（供 Hermes skill 直接使用）::

    python scripts/gb_gongwen.py input.md output.docx \
        --author "子公司管理室" \
        --date "2026年6月19日"

PARTS 格式：
    (样式id, 文本[, 首行缩进?, 对齐?])
    - "13" = 标题（二号方正小标宋简体，居中）
    - "14" = 一级标题（三号黑体，自动加"一、"）
    - "15" = 二级标题（三号楷体_GB2312，自动加"（一）"）
    - "16" = 三级标题（三号仿宋_GB2312 加粗，自动加"1．"）
    - "19" = 正文（三号仿宋_GB2312）
    - "table" = 表格，格式 ("table", [["列1","列2"], ["数据1","数据2"]])
    - "sign" = 落款，格式 ("sign", "署名", "日期")

Markdown 输入规则：
    - 第一行作为标题；也可用 --title 覆盖。
    - 已带编号的标题（如"一、总体情况""（一）问题"）会识别层级并去掉编号，
      再由脚本统一自动编号，避免重复编号。
    - 普通段落作为正文。
    - 表格（|...|...|）识别为 Word 表格。
    - Markdown 图片语法会跳过；图片需人工插入或后续扩展处理。

实现说明：
    不依赖 python-docx 和 Word 模板，直接写 WordprocessingML。落款测宽如安装
    Pillow 则使用字体实测；否则使用近似缩进兜底。
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape as _xml_escape

# ═══════════════════ 排版规格（GB/T 9704-2012） ═══════════════════

STYLES = {
    "13": ("公文：标题", "方正小标宋简体", 44, False, "center"),  # 二号 22pt
    "14": ("公文：一级标题", "黑体", 32, False, "both"),  # 三号 16pt
    "15": ("公文：二级标题", "楷体_GB2312", 32, False, "both"),
    "16": ("公文：三级标题", "仿宋_GB2312", 32, True, "both"),
    "19": ("公文：正文", "仿宋_GB2312", 32, False, "both"),
}

LINE_SPACING = 600  # 固定行距 30 磅（twips）
FIRST_INDENT = 640  # 首行缩进 2 字符
TITLE_AFTER = 440  # 标题后空一行（二号字高约 22pt）
SIGN_INDENT = 1280  # 落款右空 4 字符

PAGE = {  # A4，单位 twips
    "width": 11906,
    "height": 16838,
    "top": 2098,      # 37mm
    "bottom": 1985,   # 35mm
    "left": 1588,     # 28mm
    "right": 1474,    # 26mm
}

INDENTED_HEADS = {"14", "15", "16"}
CN_NUM = "〇一二三四五六七八九十"


def cn_num(n: int) -> str:
    """整数转中文序号（1-99），公文标题层级编号用。

    修复：旧实现 CN_NUM[n] 仅覆盖 0-10，超过 10 时兜底 str(n)，
    导致二级标题出现"（11）"这类半角阿拉伯数字，与 GB/T 9704
    的"（一）（二）……（十一）（十二）"中式序号不一致。
    """
    if n <= 0:
        return str(n)
    if n <= 10:
        return CN_NUM[n]
    if n < 20:
        return "十" + CN_NUM[n - 10]
    if n < 100:
        tens, ones = divmod(n, 10)
        return CN_NUM[tens] + "十" + (CN_NUM[ones] if ones else "")
    return str(n)


# 制度类文档的"第X条"模式——正文中的一级结构边界，重置二级/三级编号
#
# 必须锚定段落开头（^）：制度条文以"第X条"起始，如"第七条 公司设立……"。
# 若用 search() 匹配任意位置，正文中引用条款的表述（如"依据《XX办法》第七条"、
# "第十二条规定……"）会被误判为条文边界，错误重置二级/三级计数器，
# 导致后续标题编号错乱。此为已修复的真实缺陷，勿改回 search()。
ART_RE = re.compile(r"^第[一二三四五六七八九十百千]+条(?=[\s　]|$)")


def _h1_num(n: int) -> str:
    """一级标题中文序号（1-99）。"""
    return cn_num(n)


def _h2_num(n: int) -> str:
    """二级标题中文序号（1-99）。"""
    return cn_num(n)

H1_RE = re.compile(r"^([一二三四五六七八九十]+)、\s*(.*)$")
H2_RE = re.compile(r"^（([一二三四五六七八九十]+)）\s*(.*)$")
H3_RE = re.compile(r"^(\d+)[.．、]\s*(.*)$")


def _parse_table_row(line: str) -> list[str]:
    """Parse a single pipe-separated table row into cells."""
    return [c.strip() for c in line.strip("|").split("|")]


def _xml_table(rows: list[list[str]]) -> list[str]:
    """Build WordprocessingML <w:tbl> from parsed table rows."""
    if not rows:
        return []

    col_count = max(len(r) for r in rows)
    for r in rows:
        while len(r) < col_count:
            r.append("")

    table_width = PAGE["width"] - PAGE["left"] - PAGE["right"]
    col_width = table_width // col_count

    lines = [
        '    <w:tbl>'
        '<w:tblPr>'
        '<w:tblW w:w="{}" w:type="dxa"/>'
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '</w:tblBorders>'
        '</w:tblPr>'
        '<w:tblGrid>'.format(table_width)
    ]
    for _ in range(col_count):
        lines.append('    <w:gridCol w:w="{}"/>'.format(col_width))
    lines.append('    </w:tblGrid>')

    is_header = True
    for row in rows:
        lines.append('    <w:tr>')
        for cell in row:
            lines.append('      <w:tc>')
            lines.append('        <w:tcPr><w:tcW w:w="{}" w:type="dxa"/>'.format(col_width))
            if is_header:
                lines.append('          <w:shd w:val="clear" w:color="auto" w:fill="D9E2F3"/>')
            lines.append('        </w:tcPr>')
            lines.append('        <w:p><w:pPr>'
                         '<w:spacing w:line="{}" w:lineRule="exact" w:before="40" w:after="40"/>'
                         '<w:jc w:val="center"/>'
                         '</w:pPr>'.format(LINE_SPACING))
            lines.append('          <w:r><w:rPr>')
            if is_header:
                lines.append('<w:b/>')
            lines.append(
                '<w:rFonts w:eastAsia="仿宋_GB2312" w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>'
                '<w:sz w:val="24"/><w:szCs w:val="24"/>'
                '</w:rPr><w:t xml:space="preserve">{}</w:t></w:r>'
                '</w:p>'.format(_esc(cell))
            )
            lines.append('      </w:tc>')
        lines.append('    </w:tr>')
        is_header = False

    lines.append('    </w:tbl>')
    return lines


def _esc(s: object) -> str:
    return _xml_escape(str(s), {"\"": "&quot;"})


def generate(parts: list[tuple], output_path: str | os.PathLike[str], *, author: str = "") -> None:
    """生成 docx。"""
    _build_docx(parts, Path(output_path), author=author)


def _build_docx(parts: list[tuple], output_path: Path, *, author: str = "") -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="gb_gongwen_"))
    try:
        (tmp / "_rels").mkdir(parents=True, exist_ok=True)
        (tmp / "word" / "_rels").mkdir(parents=True, exist_ok=True)
        (tmp / "word" / "theme").mkdir(parents=True, exist_ok=True)
        (tmp / "docProps").mkdir(parents=True, exist_ok=True)

        def w(rel: str, content: str) -> None:
            (tmp / rel).write_text(content, encoding="utf-8")

        w("[Content_Types].xml", _xml_content_types())
        w("_rels/.rels", _xml_rels())
        w("word/_rels/document.xml.rels", _xml_doc_rels())
        w("docProps/core.xml", _xml_core(parts, author=author))
        w("docProps/app.xml", _xml_app(author=author))
        w("word/styles.xml", _xml_styles())
        w("word/settings.xml", _xml_settings())
        w("word/theme/theme1.xml", _xml_theme())
        w("word/document.xml", _xml_document(parts))

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(tmp):
                for fn in files:
                    fp = Path(root) / fn
                    arc = fp.relative_to(tmp).as_posix()
                    z.write(fp, arc)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _xml_styles() -> str:
    items = []
    for sid, (name, cn_font, sz, bold, align) in STYLES.items():
        b = "<w:b/>" if bold else ""
        items.append(
            f'<w:style w:type="paragraph" w:styleId="{sid}">'
            f'<w:name w:val="{_esc(name)}"/>'
            f'<w:pPr><w:jc w:val="{align}"/></w:pPr>'
            f'<w:rPr><w:rFonts w:eastAsia="{cn_font}" w:ascii="Times New Roman" '
            f'w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'
            f'{b}<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr>'
            f'</w:style>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
        + "\n".join(items)
        + "\n</w:styles>"
    )


def _xml_document(parts: list[tuple]) -> str:
    h1 = h2 = h3 = 0
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">',
        "  <w:body>",
    ]
    for entry in parts:
        if not entry:
            continue
        if entry[0] == "sign":
            lines.extend(_make_sign(entry))
            continue
        if entry[0] == "table":
            rows = entry[1] if len(entry) > 1 else []
            lines.extend(_xml_table(rows))
            continue

        sid = str(entry[0])
        text = _esc(entry[1] if len(entry) > 1 else "")
        indent = bool(entry[2]) if len(entry) > 2 else False
        align = entry[3] if len(entry) > 3 else None

        if sid == "14":
            h1 += 1
            h2 = h3 = 0
            text = f"{_h1_num(h1)}、{text}"
        elif sid == "15":
            h2 += 1
            h3 = 0
            text = f"（{_h2_num(h2)}）{text}"
        elif sid == "16":
            h3 += 1
            text = f"{h3}．{text}"
        elif sid == "19" and ART_RE.match(text.lstrip()):
            # 制度类"第X条"作为一级结构边界，重置二级/三级计数器。
            # 用 match + lstrip 而非 search：仅段落起始的条文才是边界，
            # 正文中引用"《XX办法》第七条"不应触发重置。
            h2 = h3 = 0

        need_indent = indent or sid in INDENTED_HEADS
        ind = f'<w:ind w:firstLine="{FIRST_INDENT}"/>' if need_indent else ""
        sp = (
            f'<w:spacing w:line="{LINE_SPACING}" w:lineRule="exact" w:after="{TITLE_AFTER}"/>'
            if sid == "13"
            else f'<w:spacing w:line="{LINE_SPACING}" w:lineRule="exact"/>'
        )
        jc = f'<w:jc w:val="{align}"/>' if align else ""
        t = f'<w:t xml:space="preserve">{text}</w:t>' if text else ""
        lines.append(
            f'    <w:p><w:pPr><w:pStyle w:val="{sid}"/>{jc}{ind}{sp}</w:pPr><w:r>{t}</w:r></w:p>'
        )

    pg = PAGE
    lines.append(
        f'    <w:sectPr><w:pgSz w:w="{pg["width"]}" w:h="{pg["height"]}"/>'
        f'<w:pgMar w:top="{pg["top"]}" w:bottom="{pg["bottom"]}" '
        f'w:left="{pg["left"]}" w:right="{pg["right"]}"/>'
        '<w:docGrid w:type="lines" w:linePitch="312"/></w:sectPr>'
    )
    lines.append("  </w:body>")
    lines.append("</w:document>")
    return "\n".join(lines)


def _make_sign(entry: tuple) -> list[str]:
    name = str(entry[1]) if len(entry) > 1 else ""
    date = str(entry[2]) if len(entry) > 2 else ""
    lines = []
    for _ in range(2):
        lines.append(
            f'    <w:p><w:pPr><w:pStyle w:val="19"/><w:spacing w:line="{LINE_SPACING}" '
            f'w:lineRule="exact"/></w:pPr></w:p>'
        )

    body_w = PAGE["width"] - PAGE["left"] - PAGE["right"]
    left_indent = body_w - max(_measure_text_twips(name), _measure_text_twips(date)) - 2 * SIGN_INDENT
    left_indent = max(0, int(left_indent))

    lines.append(
        f'    <w:p>'
        f'<w:pPr><w:pStyle w:val="19"/><w:jc w:val="center"/><w:ind w:left="{left_indent}"/>'
        f'<w:spacing w:line="{LINE_SPACING}" w:lineRule="exact"/></w:pPr>'
        f'<w:r><w:t xml:space="preserve">{_esc(name)}</w:t><w:br/><w:t xml:space="preserve">{_esc(date)}</w:t></w:r>'
        f'</w:p>'
    )
    return lines


def _measure_text_twips(text: str) -> int:
    """估算/测量落款宽度。"""
    try:
        from PIL import ImageFont

        font_path = "C:/Windows/Fonts/simfang.ttf"
        if Path(font_path).exists():
            font = ImageFont.truetype(font_path, 16)
            ref = font.getlength("一二三四五六七八九十") or 1
            scale = 3200 / ref
            return int(font.getlength(text) * scale)
    except Exception:
        pass
    width = 0
    for ch in text:
        width += 160 if ord(ch) < 128 else 320
    return width


def _xml_content_types() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
  <Override PartName="/word/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""


def _xml_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""


def _xml_doc_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
</Relationships>"""


def _xml_core(parts: list[tuple], *, author: str = "") -> str:
    title = ""
    for entry in parts:
        if entry and entry[0] == "13":
            title = str(entry[1])
            break
    creator = _esc(author) if author else "公文排版引擎"
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f'<dc:title>{_esc(title)}</dc:title><dc:creator>{creator}</dc:creator>'
        f'<cp:lastModifiedBy>{creator}</cp:lastModifiedBy></cp:coreProperties>'
    )


def _xml_app(*, author: str = "") -> str:
    app = _esc(author) if author else "公文排版引擎"
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>{app}</Application>
</Properties>"""


# ═══════════════════ settings.xml / theme1.xml（防日文字体回退） ═══════════════════
#
# 背景（真实事故）：不写 settings.xml / theme1.xml 时，Word 打开后会用隐式
# Office 主题补全；而早期经由日文模板底子（或 WPS 兼容路径）补出的主题里：
#   ① majorFont/minorFont 的 <a:ea typeface=""/> 东亚字体槽位为空；
#   ② 脚本回退表中 Jpan（日文）槽位为「ＭＳ 明朝」；
#   ③ settings.xml 出现 <w:themeFontLang w:eastAsia="ja-JP"/>，把东亚语言
#      钉成日文。三者叠加，导致整篇（含原文件既有段，不只新增段）被
#      渲染成 MS 明朝。故必须显式输出这两个部件，且 ea 槽位不得为空。

def _xml_settings() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        # 东亚语言钉为简体中文，杜绝 ja-JP 回退到 MS 明朝
        '<w:themeFontLang w:val="en-US" w:eastAsia="zh-CN"/>'
        '<w:clrSchemeMapping w:bg1="light1" w:t1="dark1" w:bg2="light2" '
        'w:t2="dark2" w:accent1="accent1" w:accent2="accent2" w:accent3="accent3" '
        'w:accent4="accent4" w:accent5="accent5" w:accent6="accent6" '
        'w:hyperlink="hyperlink" w:followedHyperlink="followedHyperlink"/>'
        '<w:compat>'
        '<w:doNotExpandShiftReturn/><w:useFELayout/>'
        '<w:compatSetting w:name="compatibilityMode" '
        'w:uri="http://schemas.microsoft.com/office/word" w:val="12"/>'
        '</w:compat>'
        '</w:settings>'
    )


def _xml_theme() -> str:
    # majorFont（标题）/minorFont（正文）的东亚槽位显式给中文字体，
    # Jpan 槽也钉成同一中文字体，任何语言路径都不会落到「ＭＳ 明朝」。
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office">'
        '<a:themeElements>'
        '<a:clrScheme name="Office">'
        '<a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>'
        '<a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>'
        '<a:dk2><a:srgbClr val="1F497D"/></a:dk2>'
        '<a:lt2><a:srgbClr val="EEECE1"/></a:lt2>'
        '<a:accent1><a:srgbClr val="4F81BD"/></a:accent1>'
        '<a:accent2><a:srgbClr val="C0504D"/></a:accent2>'
        '<a:accent3><a:srgbClr val="9BBB59"/></a:accent3>'
        '<a:accent4><a:srgbClr val="8064A2"/></a:accent4>'
        '<a:accent5><a:srgbClr val="4BACC6"/></a:accent5>'
        '<a:accent6><a:srgbClr val="F79646"/></a:accent6>'
        '<a:hlink><a:srgbClr val="0000FF"/></a:hlink>'
        '<a:folHlink><a:srgbClr val="800080"/></a:folHlink>'
        '</a:clrScheme>'
        '<a:fontScheme name="Office">'
        '<a:majorFont>'
        '<a:latin typeface="Times New Roman"/>'
        '<a:ea typeface="方正小标宋简体"/><a:cs typeface="Times New Roman"/>'
        '<a:font script="Jpan" typeface="黑体"/>'
        '<a:font script="Hang" typeface="黑体"/>'
        '<a:font script="Hans" typeface="黑体"/>'
        '<a:font script="Hant" typeface="黑体"/>'
        '</a:majorFont>'
        '<a:minorFont>'
        '<a:latin typeface="Times New Roman"/>'
        '<a:ea typeface="仿宋_GB2312"/><a:cs typeface="Times New Roman"/>'
        '<a:font script="Jpan" typeface="仿宋_GB2312"/>'
        '<a:font script="Hang" typeface="仿宋_GB2312"/>'
        '<a:font script="Hans" typeface="仿宋_GB2312"/>'
        '<a:font script="Hant" typeface="仿宋_GB2312"/>'
        '</a:minorFont>'
        '</a:fontScheme>'
        '<a:fmtScheme name="Office">'
        '<a:fillStyleLst>'
        '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
        '<a:gradFill rotWithShape="1"><a:gsLst>'
        '<a:gs pos="0"><a:schemeClr val="phClr"><a:tint val="50000"/>'
        '<a:satMod val="300000"/></a:schemeClr></a:gs>'
        '<a:gs pos="100000"><a:schemeClr val="phClr"><a:tint val="15000"/>'
        '<a:satMod val="300000"/></a:schemeClr></a:gs>'
        '</a:gsLst><a:lin ang="16200000" scaled="1"/></a:gradFill>'
        '</a:fillStyleLst>'
        '<a:lnStyleLst>'
        '<a:ln w="9525" cap="flat" cmpd="sng" algn="ctr">'
        '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
        '<a:prstDash val="solid"/></a:ln>'
        '<a:ln w="25400" cap="flat" cmpd="sng" algn="ctr">'
        '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
        '<a:prstDash val="solid"/></a:ln>'
        '<a:ln w="38100" cap="flat" cmpd="sng" algn="ctr">'
        '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
        '<a:prstDash val="solid"/></a:ln>'
        '</a:lnStyleLst>'
        '<a:effectStyleLst>'
        '<a:effectStyle><a:effectLst/></a:effectStyle>'
        '<a:effectStyle><a:effectLst/></a:effectStyle>'
        '<a:effectStyle><a:effectLst/></a:effectStyle>'
        '</a:effectStyleLst>'
        '<a:bgFillStyleLst>'
        '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
        '<a:gradFill rotWithShape="1"><a:gsLst>'
        '<a:gs pos="0"><a:schemeClr val="phClr"><a:tint val="40000"/>'
        '<a:satMod val="350000"/></a:schemeClr></a:gs>'
        '<a:gs pos="100000"><a:schemeClr val="phClr"><a:tint val="15000"/>'
        '<a:satMod val="350000"/></a:schemeClr></a:gs>'
        '</a:gsLst><a:lin ang="16200000" scaled="1"/></a:gradFill>'
        '</a:bgFillStyleLst>'
        '</a:fmtScheme>'
        '</a:themeElements>'
        '<a:objectDefaults/>'
        '</a:theme>'
    )


def _strip_markdown_inline(text: str) -> str:
    """Remove Markdown inline formatting.  """
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'^\s*---+$', '', text, flags=re.MULTILINE)
    return text


def markdown_to_parts(text: str, title: str | None = None, author: str | None = None, date: str | None = None) -> list[tuple]:
    text = _strip_markdown_inline(text)

    lines = [ln.strip() for ln in text.replace("\r\n", "\n").split("\n")]
    lines = [ln for ln in lines if ln]
    if not lines and not title:
        raise ValueError("输入为空，且未指定 --title")

    doc_title = title or lines[0].strip("# ").strip()
    if title and lines and lines[0].startswith("#"):
        body_lines = lines[1:]
    else:
        body_lines = lines if title else lines[1:]
    parts: list[tuple] = [("13", doc_title)]

    i = 0
    while i < len(body_lines):
        raw = body_lines[i]
        line = raw.strip().strip("# ").strip()
        if not line or line.startswith("!["):
            i += 1
            continue

        stripped = raw.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            table_rows = []
            while i < len(body_lines):
                s = body_lines[i].strip()
                if not (s.startswith("|") and s.endswith("|")):
                    break
                table_rows.append(_parse_table_row(s))
                i += 1
            # 跳过表头分隔行 (|:---:|:---:| ...)
            if len(table_rows) >= 2:
                sep_line = ''.join(table_rows[1])
                if re.search(r'^[\s\-:]+$', sep_line):
                    table_rows.pop(1)
            if table_rows:
                parts.append(("table", table_rows))
            continue

        m1 = H1_RE.match(line)
        m2 = H2_RE.match(line)
        m3 = H3_RE.match(line)
        if m1:
            parts.append(("14", m1.group(2).strip()))
        elif m2:
            parts.append(("15", m2.group(2).strip()))
        elif m3:
            parts.append(("16", m3.group(2).strip()))
        else:
            parts.append(("19", line, True))
        i += 1

    if author or date:
        parts.append(("sign", author or "", date or ""))
    return parts


def main() -> int:
    parser = argparse.ArgumentParser(description="GB/T 9704 公文 docx 排版引擎")
    parser.add_argument("input", nargs="?", help="输入 Markdown/文本文件；省略则生成内置测试样例")
    parser.add_argument("output", nargs="?", help="输出 .docx 路径")
    parser.add_argument("--title", help="标题；默认取输入第一行")
    parser.add_argument("--author", default="", help="落款/发文机关署名；提供后会生成落款")
    parser.add_argument("--date", default="", help="成文日期；提供后会生成落款")
    args = parser.parse_args()

    if args.input and args.output:
        inpath = Path(args.input)
        if not inpath.exists():
            print(f"error: 输入文件不存在: {args.input}", file=sys.stderr)
            return 1
        text = inpath.read_text(encoding="utf-8-sig")
        if not text.strip():
            print(f"error: 输入文件为空: {args.input}", file=sys.stderr)
            return 1
        try:
            parts = markdown_to_parts(text, args.title, args.author, args.date)
            generate(parts, args.output, author=args.author)
            print(f"created: {args.output}")
            return 0
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1

    demo = [
        ("13", "关于子公司经营管理情况的报告"),
        ("19", "根据年度工作安排，现将各子公司经营管理有关情况报告如下。", True),
        ("14", "经营指标完成情况"),
        ("19", "截至2026年5月末，各控股子公司累计实现营业收入128.6亿元，同比增长12.3%；净利润9.2亿元，同比增长8.7%。", True),
        ("15", "重点子公司分析"),
        ("19", "A公司经营指标完成情况较好，B公司新业务板块增长较快。", True),
        ("16", "制度建设方面"),
        ("19", "已推动各子公司完成内部控制手册修订工作。", True),
        ("14", "下一步工作安排"),
        ("19", "一是持续加强经营调度。二是加快推进重点项目落地。三是深化风险防控。", True),
        ("19", "以上报告如无不妥，请审阅。", True),
        ("sign", "富泽人寿保险股份有限公司", "2026年6月16日"),
    ]
    out = Path("公文排版样例.docx")
    generate(demo, out)
    print(f"OK: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
