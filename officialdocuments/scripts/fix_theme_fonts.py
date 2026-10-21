#!/usr/bin/env python3
"""修复存量 .docx 中「日文模板底子」导致的 MS 明朝字体问题。

问题部件（原文件自带，影响整篇，不只新增段）：
  1. word/theme/theme1.xml：majorFont/minorFont 的 <a:ea typeface=""/> 为空，
     且脚本回退表 Jpan 槽为「ＭＳ 明朝」；
  2. word/settings.xml：<w:themeFontLang w:eastAsia="ja-JP"/> 把东亚语言钉成日文。

策略（外科手术式，最小改动）：
  - theme1.xml：将 majorFont/minorFont 内的 <a:ea .../> 替换为显式中文字体；
    将 Jpan 槽字体替换为对应中文字体（不删表，保持其他脚本槽位不变）。
  - settings.xml：将 themeFontLang 的 w:eastAsia 值改为 zh-CN；
    若节点不存在则在 <w:settings> 开标签后插入。
  部件缺失时不新增（保持包结构不变）。

用法:
    python fix_theme_fonts.py 文件.docx                # 原地修复（自动留 .bak）
    python fix_theme_fonts.py 文件.docx -o 输出.docx
    python fix_theme_fonts.py 文件.docx --no-backup    # 不备份
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path

# 东亚字体槽位显式字体（与 gb_gongwen.py 保持一致）
MAJOR_EA = "方正小标宋简体"
MINOR_EA = "仿宋_GB2312"
# Jpan 槽替换字体（major/minor）
MAJOR_JPAN = "黑体"
MINOR_JPAN = "仿宋_GB2312"

# Courier 裸名（系统只有 Courier New）——fontTable 里虽登记 altName=Courier New，
# 但 Word 打开仍弹「缺失 Courier，是否替换为 Courier New」。修复时把
# styles.xml / fontTable.xml 中的裸 "Courier" 统一为 "Courier New"，消除弹窗。
LEGACY_FONT_MAP = {
    "Courier": "Courier New",
}

THEME_PART = "word/theme/theme1.xml"
SETTINGS_PART = "word/settings.xml"
FONT_STYLE_PARTS = ("word/styles.xml", "word/fontTable.xml")


def fix_theme_xml(xml: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    for slot, ea_font, jpan_font in (
        ("majorFont", MAJOR_EA, MAJOR_JPAN),
        ("minorFont", MINOR_EA, MINOR_JPAN),
    ):
        slot_re = re.compile(rf"(<a:{slot}>)(.*?)(</a:{slot}>)", re.S)
        m = slot_re.search(xml)
        if not m:
            notes.append(f"{slot}: 槽位缺失，跳过")
            continue
        head, body, tail = m.group(1), m.group(2), m.group(3)

        # ① 东亚字体槽 <a:ea typeface="..."/> → 显式中文字体
        def _ea_repl(match: re.Match) -> str:
            old = match.group(1)
            if old.strip() == ea_font:
                return match.group(0)
            notes.append(f"{slot}: a:ea '{old}' -> '{ea_font}'")
            return f'<a:ea typeface="{ea_font}"/>'

        new_body, n = re.subn(r'<a:ea[^>]*typeface="([^"]*)"\s*/?>', _ea_repl, body, count=1)
        if n == 0:
            # 无 a:ea 节点，在 latin 后补一个
            new_body = re.sub(
                r'(<a:latin[^>]*/>)',
                rf'\1<a:ea typeface="{ea_font}"/>',
                body, count=1,
            )
            notes.append(f"{slot}: 无 a:ea 节点，已补 '{ea_font}'")
        body = new_body

        # ② Jpan 槽 → 中文字体（只改 Jpan，不动 Hang/Hans/Hant 等）
        def _jpan_repl(match: re.Match) -> str:
            old = match.group(1)
            if old.strip() == jpan_font:
                return match.group(0)
            notes.append(f"{slot}: Jpan '{old}' -> '{jpan_font}'")
            return f'<a:font script="Jpan" typeface="{jpan_font}"/>'

        body = re.sub(
            r'<a:font script="Jpan"[^>]*typeface="([^"]*)"\s*/>',
            _jpan_repl, body, count=1,
        )
        xml = xml[: m.start()] + head + body + tail + xml[m.end():]
    return xml, notes


def fix_settings_xml(xml: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    lang_re = re.compile(r'(<w:themeFontLang[^>]*w:eastAsia=")([^"]+)("[^>]*/?>)')
    m = lang_re.search(xml)
    if m:
        if m.group(2) != "zh-CN":
            notes.append(f'themeFontLang eastAsia {m.group(2)} -> zh-CN')
            xml = xml[: m.start()] + m.group(1) + "zh-CN" + m.group(3) + xml[m.end():]
    else:
        # 节点缺失：在 <w:settings ...> 开标签后插入
        insert = '<w:themeFontLang w:val="en-US" w:eastAsia="zh-CN"/>'
        xml2, n = re.subn(r'(<w:settings[^>]*>)', rf'\1{insert}', xml, count=1)
        if n:
            notes.append("themeFontLang 缺失，已插入 eastAsia=zh-CN")
            xml = xml2
    return xml, notes


def fix_legacy_fonts(xml: str) -> tuple[str, list[str]]:
    """替换裸 legacy 字体名（Courier → Courier New），不影响 Courier New 本身。

    仅在字体属性值（w:ascii/w:hAnsi/w:cs/w:name/typeface 等）中精确匹配，
    用负向前瞻排除 "Courier New" 等更长名称。
    """
    notes: list[str] = []
    for old, new in LEGACY_FONT_MAP.items():
        # ("...="Courier") 且后面不是单词字符/空格+字母（即排除 Courier New）
        pat = re.compile(rf'((?:w:ascii|w:hAnsi|w:cs|w:name|typeface)="){re.escape(old)}(?![\w ])(")')
        def _r(m: re.Match) -> str:
            notes.append(f"'{old}' -> '{new}'")
            return m.group(1) + new + m.group(2)
        xml = pat.sub(_r, xml)
    return xml, notes


def fix_docx(src: Path, dst: Path) -> list[str]:
    """读取 src，修复后写 dst；返回变更说明列表。"""
    all_notes: list[str] = []
    with zipfile.ZipFile(src, "r") as zin:
        items = {info.filename: (info, zin.read(info.filename)) for info in zin.infolist()}

    targets = {
        THEME_PART: fix_theme_xml,
        SETTINGS_PART: fix_settings_xml,
    }
    for part, fixer in targets.items():
        if part not in items:
            all_notes.append(f"{part}: 部件缺失，跳过（不新增）")
            continue
        info, data = items[part]
        xml = data.decode("utf-8", errors="replace")
        new_xml, notes = fixer(xml)
        all_notes.extend(notes)
        items[part] = (info, new_xml.encode("utf-8"))

    # legacy 裸字体名（Courier → Courier New），消除 Word 缺字替换弹窗
    for part in FONT_STYLE_PARTS:
        if part not in items:
            continue
        info, data = items[part]
        xml = data.decode("utf-8", errors="replace")
        new_xml, notes = fix_legacy_fonts(xml)
        if notes:
            all_notes.append(f"{part}: " + "; ".join(notes))
            items[part] = (info, new_xml.encode("utf-8"))

    dst.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for filename, (info, data) in items.items():
            zout.writestr(info, data)
    return all_notes


def main() -> int:
    parser = argparse.ArgumentParser(description="修复 docx 中 MS 明朝（日文模板底子）问题")
    parser.add_argument("docx", help="待修复 .docx")
    parser.add_argument("-o", "--output", help="输出路径（默认原地修复）")
    parser.add_argument("--no-backup", action="store_true", help="原地修复时不生成 .bak 备份")
    args = parser.parse_args()

    src = Path(args.docx)
    if not src.exists():
        print(f"error: 文件不存在: {src}", file=sys.stderr)
        return 1

    in_place = not args.output
    dst = src if in_place else Path(args.output)

    if in_place and not args.no_backup:
        bak = src.with_suffix(src.suffix + ".bak")
        shutil.copy2(src, bak)
        print(f"已备份: {bak}")

    tmp_out = dst if not in_place else dst.with_suffix(".fixed.tmp")
    notes = fix_docx(src, tmp_out)
    if in_place:
        shutil.move(str(tmp_out), str(dst))

    if notes:
        print("修复项:")
        for n in notes:
            print(f"  - {n}")
    else:
        print("未发现需修复内容（已是干净状态）")
    print(f"完成: {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
