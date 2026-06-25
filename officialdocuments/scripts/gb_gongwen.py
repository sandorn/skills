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
    - "sign" = 落款，格式 ("sign", "署名", "日期")

Markdown 输入规则：
    - 第一行作为标题；也可用 --title 覆盖。
    - 已带编号的标题（如"一、总体情况""（一）问题"）会识别层级并去掉编号，
      再由脚本统一自动编号，避免重复编号。
    - 普通段落作为正文。
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

def _h1_num(n: int) -> str:
    """一级标题中文序号，>10 时兜底为阿拉伯数字。"""
    if n <= 10:
        return CN_NUM[n]
    return str(n)

def _h2_num(n: int) -> str:
    """二级标题中文序号。"""
    if n <= 10:
        return CN_NUM[n]
    return str(n)

H1_RE = re.compile(r"^([一二三四五六七八九十]+)、\s*(.*)$")
H2_RE = re.compile(r"^（([一二三四五六七八九十]+)）\s*(.*)$")
H3_RE = re.compile(r"^(\d+)[.．、]\s*(.*)$")


def _esc(s: object) -> str:
    return _xml_escape(str(s), {"\"": "&quot;"})


def generate(parts: list[tuple], output_path: str | os.PathLike[str], *, author: str = "") -> None:
    """生成 docx。

    Args:
        parts: 段落列表，格式见模块文档。
        output_path: 输出 .docx 路径。
        author: 起草单位/作者，写入文档属性。
    """
    _build_docx(parts, Path(output_path), author=author)


def _build_docx(parts: list[tuple], output_path: Path, *, author: str = "") -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="gb_gongwen_"))
    try:
        (tmp / "_rels").mkdir(parents=True, exist_ok=True)
        (tmp / "word" / "_rels").mkdir(parents=True, exist_ok=True)
        (tmp / "docProps").mkdir(parents=True, exist_ok=True)

        def w(rel: str, content: str) -> None:
            (tmp / rel).write_text(content, encoding="utf-8")

        w("[Content_Types].xml", _xml_content_types())
        w("_rels/.rels", _xml_rels())
        w("word/_rels/document.xml.rels", _xml_doc_rels())
        w("docProps/core.xml", _xml_core(parts, author=author))
        w("docProps/app.xml", _xml_app(author=author))
        w("word/styles.xml", _xml_styles())
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

        sid = str(entry[0])
        text = _esc(entry[1] if len(entry) > 1 else "")
        indent = bool(entry[2]) if len(entry) > 2 else False
        align = entry[3] if len(entry) > 3 else None

        # 自动编号。调用方传入标题正文即可，不要带"一、""（一）"。
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
    for _ in range(2):  # 正文后空两行
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
    """估算/测量落款宽度。

    有 Pillow 时用 simfang.ttf 测宽；无 Pillow 时按中文 320twips、半角 160twips 估算。
    """
    try:
        from PIL import ImageFont  # type: ignore

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


def markdown_to_parts(text: str, title: str | None = None, author: str | None = None, date: str | None = None) -> list[tuple]:
    lines = [ln.strip() for ln in text.replace("\r\n", "\n").split("\n")]
    lines = [ln for ln in lines if ln]
    if not lines and not title:
        raise ValueError("输入为空，且未指定 --title")

    doc_title = title or lines[0].strip("# ").strip()
    # 如外部指定标题，且第一行是 Markdown 标题行（以 # 开头），则跳过
    if title and lines and lines[0].startswith("#"):
        body_lines = lines[1:]
    else:
        body_lines = lines if title else lines[1:]
    parts: list[tuple] = [("13", doc_title)]

    for raw in body_lines:
        line = raw.strip().strip("# ").strip()
        if not line or line.startswith("!["):
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
