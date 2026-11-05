# -*- coding: utf-8 -*-
"""由 WPS/Word 的 Normal.dotm 派生无宏公文模板 .dotx。

用途：WPS 新建文档的主题硬编码为日文底子（游明朝/游ゴシック），且默认
Normal.dotm 的 theme1.xml 不被继承；用本脚本产出的 .dotx 新建文档可正确
继承干净主题，再去跑 word.bas 公文宏即得完全合规产物。

保留：styles.xml（公文样式体系）、settings.xml（主题语言 zh-CN）、
theme1.xml（干净中文字体方案）、sectPr（页边距/文档网格）、fontTable。
剥离：vbaProject.bin / vbaData.xml 及其关系项，主文档类型改为模板。

用法：
    python make_gongwen_dotx.py [--src Normal.dotm] [--dst 公文模板.dotx]
默认源按 WPS → Microsoft 顺序探测。
"""
import argparse
import os
import re
import sys
import zipfile
from pathlib import Path

TEMPLATE_CT = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.template.main+xml"
)
DROP = {
    "word/vbaProject.bin",
    "word/vbaData.xml",
    "word/_rels/vbaProject.bin.rels",
}
CANDIDATES = [
    Path(os.path.expandvars(r"%APPDATA%/kingsoft/office6/templates/wps/zh_CN/Normal.dotm")),
    Path(os.path.expandvars(r"%APPDATA%/Microsoft/Templates/Normal.dotm")),
]


def clean_content_types(xml: str) -> str:
    xml = re.sub(r'<Override[^>]*PartName="/word/vbaProject\.bin"[^>]*/>', "", xml)
    xml = re.sub(r'<Override[^>]*PartName="/word/vbaData\.xml"[^>]*/>', "", xml)
    xml = re.sub(r'<Default[^>]*Extension="bin"[^>]*/>', "", xml)
    return re.sub(
        r'(<Override[^>]*PartName="/word/document\.xml"[^>]*ContentType=")[^"]*(")',
        lambda m: m.group(1) + TEMPLATE_CT + m.group(2),
        xml,
    )


def clean_rels(xml: str) -> str:
    """删除指向 vba 部件的 Relationship 元素。"""
    return re.sub(
        r'<Relationship[^>]*Target="(?:vbaProject\.bin|vbaData\.xml)"[^>]*/>', "", xml
    )


def clean_document(xml: str) -> str:
    """清空正文，仅保留 sectPr（页边距/纸张/文档网格），得到空白模板。"""
    m = re.search(r"<w:sectPr\b.*?</w:sectPr>", xml, re.S)
    sect = m.group(0) if m else ""
    head = re.search(r"<w:document\b[^>]*>", xml)
    if head is None:
        raise ValueError("word/document.xml 结构异常，找不到 w:document 根元素")
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        + head.group(0)
        + "<w:body>"
        + sect
        + "</w:body></w:document>"
    )


def pick_source(given: str | None) -> Path:
    if given:
        p = Path(given)
        if not p.exists():
            sys.exit(f"源模板不存在: {p}")
        return p
    for p in CANDIDATES:
        if p.exists():
            return p
    sys.exit("未找到 Normal.dotm，请用 --src 显式指定")


def main() -> int:
    ap = argparse.ArgumentParser(description="由 Normal.dotm 派生无宏公文模板 .dotx")
    ap.add_argument("--src", help="源 Normal.dotm 路径（默认自动探测 WPS/Microsoft）")
    ap.add_argument("--dst", help="输出 .dotx 路径")
    args = ap.parse_args()

    src = pick_source(args.src)
    dst = Path(args.dst) if args.dst else (
        Path(os.path.expandvars(r"%APPDATA%/kingsoft/office6/templates")) / "中言公文模板.dotx"
    )
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        bak = dst.with_suffix(dst.suffix + ".bak")
        bak.write_bytes(dst.read_bytes())
        print(f"已备份旧模板 → {bak}")

    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            name = info.filename
            if name in DROP or name.endswith("/"):
                continue
            data = zin.read(name)
            if name == "[Content_Types].xml":
                data = clean_content_types(data.decode("utf-8")).encode("utf-8")
            elif name == "word/_rels/document.xml.rels":
                data = clean_rels(data.decode("utf-8")).encode("utf-8")
            elif name == "word/document.xml":
                data = clean_document(data.decode("utf-8")).encode("utf-8")
            zout.writestr(info, data)

    # 自检：无 VBA 部件、主文档类型为模板、主题无日文字体
    with zipfile.ZipFile(dst) as z:
        names = z.namelist()
        assert not [n for n in names if "vba" in n.lower()], "仍残留 vba 部件"
        ct = z.read("[Content_Types].xml").decode("utf-8")
        assert TEMPLATE_CT in ct, "主文档类型未改为模板"
        theme = z.read("word/theme/theme1.xml").decode("utf-8")
        for bad in ("游明", "游ゴシック"):
            assert bad not in theme, f"主题仍含日文字体 {bad}"
    print(f"OK: {dst}  ({dst.stat().st_size} B)")
    print("用法：用它新建文档后再运行公文宏，产物主题即为干净中文字体。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
