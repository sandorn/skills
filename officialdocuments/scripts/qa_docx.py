#!/usr/bin/env python3
"""gb_gongwen.py 产物质检脚本。

对 gb_gongwen.py 生成的 .docx 进行自动化版式/残留/编号检查，
输出结构化报告。零外部依赖（zipfile + xml.etree.ElementTree）。

用法:
    python qa_docx.py 文件.docx                    # 终端彩色报告
    python qa_docx.py 文件.docx --format json       # JSON 输出
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

# ═══════════════════ 常量 ═══════════════════

# 页面标准（单位 twips，参照 gb_gongwen.py PAGE 常量）
PAGE_SPEC = {"top": "2098", "bottom": "1985", "left": "1588", "right": "1474"}

# 样式标准
# id 为 gb_gongwen.py 生成文档的固有 styleId；aliases 为跨模板的样式名候选
# （宏产物用「公文标题/公文1级/…」命名，ID 体系也不同，必须按名定位）。
STYLE_SPEC = {
    "13": {"name": "标题", "font": "方正小标宋简体", "sz": "44", "bold": False,
           "aliases": ("标题", "公文标题", "文件标题", "Title", "heading 1")},
    "14": {"name": "一级标题", "font": "黑体", "sz": "32", "bold": False,
           "aliases": ("一级标题", "公文1级", "一级标题（一）", "heading 2")},
    "15": {"name": "二级标题", "font": "楷体_GB2312", "sz": "32", "bold": False,
           "aliases": ("二级标题", "公文2级", "heading 3")},
    "16": {"name": "三级标题", "font": "仿宋_GB2312", "sz": "32", "bold": True,
           "aliases": ("三级标题", "公文3级", "heading 4")},
    "19": {"name": "正文", "font": "仿宋_GB2312", "sz": "32", "bold": False,
           "aliases": ("正文", "公文正文", "Normal", "Body Text")},
}

# 段落版式标准
PARA_SPEC = {"firstLine": "640", "line": "600", "lineRule": "exact"}

# Markdown 残留检测正则（完备覆盖）
MD_RESIDUE_CHECKS = [
    # (名称, 正则, 阻断级别)
    ("粗体 **", r"\*\*", "ERROR"),
    ("粗体 __", r"__", "ERROR"),
    ("斜体 *（非列表）", r"(?<!\n)\*(?!\s)[^*]*\*", "ERROR"),
    ("斜体 _（非列表）", r"(?<!\n)_(?!\s)[^_]*_", "ERROR"),
    ("行内代码 `", r"`[^`]+`", "ERROR"),
    ("删除线 ~~", r"~~", "ERROR"),
    ("链接 [text](url)", r"\]\(", "ERROR"),
    ("图片 ![alt](url)", r"!\[", "ERROR"),
    ("标题标记 #", r"^#{1,6}\s", "ERROR"),
    ("分隔线 ---/***/___", r"^[-*_]{3,}$", "ERROR"),
    ("引用块 >", r"^>\s", "ERROR"),
    ("HTML 标签", r"<[a-zA-Z/][^>]*>", "ERROR"),
    ("转义反斜杠 \\", r"\\[*_#~`]", "WARNING"),
]

# 中文数字
CN_DIGITS = "一二三四五六七八九十百千"

# 第X条 正则（用于编号连续性检查的一级边界）
# 锚定行首并要求后接分隔符，避免正文中"依据《XX办法》第七条"被误判为条文
ARTICLE_RE = re.compile(rf"^第[{CN_DIGITS}]+条(?=[\s　]|$)")

# 一级标题"一、xxx"——非制度类公文（报告/请示/建议书）的分节边界，
# 同样应重置二级/三级编号。缺此规则会把全文二级编号当作一条连续序列，
# 对每节从"（一）"重启的正确公文误报"编号不连续"。
H1_OUT_RE = re.compile(rf"^[{CN_DIGITS}]+、")

# 二级编号（一）（二）...
H2_OUT_RE = re.compile(rf"^（[{CN_DIGITS}]+）")

# 三级编号 1．2．...
# 要求编号后紧跟非数字字符，避免表格中的金额（如"112.84万元"、"1.5倍"）
# 被误判为三级编号
H3_OUT_RE = re.compile(r"^\d+[．.](?!\d)")

# 中文数字 → int 映射
_CN_NUM_MAP = dict(zip("一二三四五六七八九十", range(1, 11)))
_CN_NUM_MAP["百"] = 100
_CN_NUM_MAP["千"] = 1000

# XML 命名空间
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
ET.register_namespace("w", NS["w"])


# ═══════════════════ 主题/语言禁忌（日文模板底子的雷） ═══════════════════
#
# 真实事故：theme1.xml 若为日文模板底子——
#   ① majorFont/minorFont 的 <a:ea typeface=""/> 东亚槽位为空；
#   ② 回退表 Jpan 槽为「ＭＳ 明朝」；
#   ③ settings.xml 出现 <w:themeFontLang w:eastAsia="ja-JP"/>。
# 三者叠加会把整篇（含原文件既有段）渲染成 MS 明朝。以下正则逐项拦截。
THEME_BAD_FONTS = ("ＭＳ", "明朝", "MS Mincho", "MS Gothic", "ゴシック")
THEME_PARTS = ("word/theme/theme1.xml", "word/settings.xml")


# ═══════════════════ 工具函数 ═══════════════════

def _parse_cn_num(s: str) -> int:
    """将中文数字转换为 int，如 '十三' → 13。"""
    s = s.strip()
    if not s:
        return 0
    total = 0
    section = 0
    for ch in s:
        if ch in ("百", "千"):
            section = (section or 1) * _CN_NUM_MAP[ch]
            total += section
            section = 0
        elif ch == "十":
            section = (section or 1) * 10
        else:
            section += _CN_NUM_MAP.get(ch, 0)
    return total + section


def _extract_texts(docx_path: Path) -> list[str]:
    """解压 docx，提取 word/document.xml 中所有 <w:t> 文本。"""
    with zipfile.ZipFile(docx_path, "r") as z:
        with z.open("word/document.xml") as f:
            tree = ET.parse(f)
    return [t.text or "" for t in tree.iter(f"{{{NS['w']}}}t")]


def _extract_body_texts(docx_path: Path) -> list[str]:
    """提取正文段落文本，跳过表格（<w:tbl>）内的内容。

    编号连续性检查必须排除表格：单元格里的金额、比率、序号
    （如"112.84万元"、"1．"）会被误判为三级编号，产生假阳性。
    """
    with zipfile.ZipFile(docx_path, "r") as z:
        with z.open("word/document.xml") as f:
            tree = ET.parse(f)
    body = tree.find(f"{{{NS['w']}}}body")
    if body is None:
        return []
    texts = []
    # 仅遍历 body 的直接子元素：<w:p> 取文本，<w:tbl> 整体跳过
    for child in body:
        if child.tag == f"{{{NS['w']}}}p":
            texts.append("".join(t.text or "" for t in child.iter(f"{{{NS['w']}}}t")))
    return texts


def _local(attr: str) -> str:
    """去掉 XML 命名空间前缀，返回属性本地名。"""
    return attr.split("}")[-1] if "}" in attr else attr


def _ind_map(el) -> dict:
    return {_local(k): v for k, v in el.attrib.items()}


def _extract_styles(docx_path: Path) -> dict[str, dict]:
    """从 styles.xml 提取样式信息：名称、basedOn、字体/字号、段落属性。

    额外键 ``__docdefaults__`` 保存 docDefaults 的字体/字号兜底值。
    样式可整体为空（如「公文正文」只靠 basedOn 继承），调用方需用
    `_resolve_style()` 沿继承链补齐，不可直接读 rPr 就判失败。
    """
    result: dict[str, dict] = {}
    try:
        with zipfile.ZipFile(docx_path, "r") as z:
            with z.open("word/styles.xml") as f:
                tree = ET.parse(f)
        W = NS["w"]

        dd_info: dict = {}
        dd = tree.find("w:docDefaults", NS)
        if dd is not None:
            rpr = dd.find("w:rPrDefault/w:rPr", NS)
            if rpr is not None:
                rf = rpr.find("w:rFonts", NS)
                sz = rpr.find("w:sz", NS)
                dd_info["font"] = rf.get(f"{{{W}}}eastAsia", "") if rf is not None else ""
                dd_info["sz"] = sz.get(f"{{{W}}}val", "") if sz is not None else ""
        result["__docdefaults__"] = dd_info

        for style in tree.iter(f"{{{W}}}style"):
            sid = style.get(f"{{{W}}}styleId", "")
            if not sid:
                continue
            nm = style.find("w:name", NS)
            bo = style.find("w:basedOn", NS)
            info: dict = {
                "name": nm.get(f"{{{W}}}val", "") if nm is not None else "",
                "basedOn": bo.get(f"{{{W}}}val", "") if bo is not None else "",
                "default": style.get(f"{{{W}}}default", "") in ("1", "true"),
                "type": style.get(f"{{{W}}}type", ""),
                "font": "", "sz": "", "ind": {}, "spacing": {},
            }
            rpr = style.find("w:rPr", NS)
            if rpr is not None:
                rf = rpr.find("w:rFonts", NS)
                sz = rpr.find("w:sz", NS)
                info["font"] = rf.get(f"{{{W}}}eastAsia", "") if rf is not None else ""
                info["sz"] = sz.get(f"{{{W}}}val", "") if sz is not None else ""
            ppr = style.find("w:pPr", NS)
            if ppr is not None:
                ind = ppr.find("w:ind", NS)
                if ind is not None:
                    info["ind"] = _ind_map(ind)
                sp = ppr.find("w:spacing", NS)
                if sp is not None:
                    info["spacing"] = _ind_map(sp)
            result[sid] = info
    except Exception:
        pass
    return result


def _resolve_style(sid: str, styles: dict, depth: int = 0) -> dict:
    """沿 basedOn 链补齐 font/sz，最终兜底 docDefaults。

    宏产物中「公文正文」等样式 rPr 为空、靠 basedOn=Normal 继承，
    直接读 rPr 会得到空值并被误判为 N/A。
    """
    info = styles.get(sid)
    if not isinstance(info, dict) or depth > 10:
        return {"font": "", "sz": ""}
    out = {"font": info.get("font", ""), "sz": info.get("sz", "")}
    if (not out["font"] or not out["sz"]) and info.get("basedOn"):
        parent = _resolve_style(info["basedOn"], styles, depth + 1)
        out["font"] = out["font"] or parent.get("font", "")
        out["sz"] = out["sz"] or parent.get("sz", "")
    if not out["font"] or not out["sz"]:
        dd = styles.get("__docdefaults__") or {}
        out["font"] = out["font"] or dd.get("font", "")
        out["sz"] = out["sz"] or dd.get("sz", "")
    return out


def _check_page(docx_path: Path) -> dict:
    """检查 1: 页面尺寸。"""
    try:
        with zipfile.ZipFile(docx_path, "r") as z:
            with z.open("word/document.xml") as f:
                tree = ET.parse(f)
        pgmar = tree.find(".//w:pgMar", NS)
        if pgmar is None:
            return {"pass": False, "detail": "未找到 <w:pgMar>", "actual": {}}
        actual = {k: pgmar.get(f"{{{NS['w']}}}{k}", "") for k in PAGE_SPEC}
        ok = all(actual.get(k) == v for k, v in PAGE_SPEC.items())
        mismatches = [k for k in PAGE_SPEC if actual.get(k) != PAGE_SPEC[k]]
        return {
            "pass": ok,
            "detail": f"页边距{'正确' if ok else '不符合: ' + ', '.join(mismatches)}",
            "actual": actual,
            "mismatches": mismatches,
        }
    except Exception as e:
        return {"pass": False, "detail": f"检查异常: {e}", "actual": {}}


def _find_style_id(spec: dict, fallback: str, styles: dict) -> str:
    """按样式名/别名定位实际 styleId；找不到时回退硬编码 ID。

    跨模板兼容：gb_gongwen 产物用「标题/一级标题/…」+ 13/14/15/19，
    Normal.dotm 宏产物用「公文标题/公文1级/…」+ 18/13/15/16。
    """
    by_name: dict[str, str] = {}
    for sid, info in styles.items():
        if sid.startswith("__") or not isinstance(info, dict):
            continue
        nm = (info.get("name") or "").strip().lower()
        if nm:
            by_name.setdefault(nm, sid)
    for alias in spec.get("aliases", ()):
        hit = by_name.get(alias.lower())
        if hit:
            return hit
    return fallback


def _check_styles(docx_path: Path) -> list[dict]:
    """检查 2-5: 字体/样式（标题/一级/二级/正文）。

    按样式名（含别名）定位、沿 basedOn 继承链取字体字号，
    避免依赖特定模板的 styleId 编号而误报。
    """
    results = []
    actual_styles = _extract_styles(docx_path)
    for spec_key in ["13", "14", "15", "19"]:
        spec = STYLE_SPEC[spec_key]
        sid = _find_style_id(spec, spec_key, actual_styles)
        actual = _resolve_style(sid, actual_styles) if sid else {}
        font_ok = actual.get("font", "") == spec["font"]
        sz_ok = actual.get("sz", "") == spec["sz"]
        ok = font_ok and sz_ok
        detail_parts = []
        if not font_ok:
            detail_parts.append(f"字体期望'{spec['font']}' 实际'{actual.get('font') or 'N/A'}'")
        if not sz_ok:
            detail_parts.append(f"字号期望'{spec['sz']}' 实际'{actual.get('sz') or 'N/A'}'")
        results.append({
            "id": spec_key,
            "style_id": sid,
            "name": spec["name"],
            "pass": ok,
            "detail": "正确" if ok else "; ".join(detail_parts),
            "actual": {"styleId": sid, **actual},
        })
    # 检查一级标题编号存在性（公文"一、"或制度"第X条"任一存在即通过）
    texts = _extract_texts(docx_path)
    full_text = "".join(texts)
    style14_ok = any(s["id"] == "14" and s["pass"] for s in results)
    if style14_ok:
        has_gongwen = bool(re.search(r"一、", full_text))
        has_article = bool(re.search(rf"第[{CN_DIGITS}]+条", full_text))
        has_num = has_gongwen or has_article
        label = "一、" if has_gongwen else ("第X条" if has_article else "")
        results.append({
            "id": "14-num",
            "name": "一级标题编号",
            "pass": has_num,
            "detail": f"存在 ({label})" if has_num else "不存在 '一、' 或 '第X条' 编号",
            "actual": {},
        })
    else:
        results.append({
            "id": "14-num",
            "name": "一级标题编号",
            "pass": None,
            "detail": "样式 #14 未通过，跳过编号检查",
            "actual": {},
        })
    return results


def _check_paragraph_format(docx_path: Path) -> dict:
    """检查 6: 段落版式（首行缩进 + 行距）。

    正文段落常无 pPr（缩进/行距写在样式里），故按
    段落 pPr → pStyle → basedOn 链 → 默认段落样式 逐级取值；
    首行缩进允许 firstLineChars=200（2 字符）等价表达 640 twips。
    """
    try:
        with zipfile.ZipFile(docx_path, "r") as z:
            with z.open("word/document.xml") as f:
                tree = ET.parse(f)
        styles = _extract_styles(docx_path)
        default_sid = next(
            (sid for sid, i in styles.items()
             if isinstance(i, dict) and i.get("default") and i.get("type") == "paragraph"),
            "",
        )

        def style_props(sid: str, depth: int = 0) -> tuple[dict, dict]:
            """沿 basedOn 链取第一个非空 ind / spacing。"""
            info = styles.get(sid)
            if not isinstance(info, dict) or depth > 10:
                return {}, {}
            ind = dict(info.get("ind") or {})
            sp = dict(info.get("spacing") or {})
            if (not ind or not sp) and info.get("basedOn"):
                p_ind, p_sp = style_props(info["basedOn"], depth + 1)
                ind = ind or p_ind
                sp = sp or p_sp
            return ind, sp

        for p in tree.iter(f"{{{NS['w']}}}p"):
            ppr = p.find("w:pPr", NS)
            own_ind: dict = {}
            own_sp: dict = {}
            psid = ""
            if ppr is not None:
                ind_el = ppr.find("w:ind", NS)
                if ind_el is not None:
                    own_ind = _ind_map(ind_el)
                sp_el = ppr.find("w:spacing", NS)
                if sp_el is not None:
                    own_sp = _ind_map(sp_el)
                ps_el = ppr.find("w:pStyle", NS)
                if ps_el is not None:
                    psid = ps_el.get(f"{{{NS['w']}}}val", "")

            s_ind, s_sp = style_props(psid or default_sid)
            ind = own_ind or s_ind
            sp = own_sp or s_sp
            if not ind:
                continue

            # OOXML 语义：firstLineChars 存在时优先于 firstLine（Word 按字符数渲染，
            # firstLine 只是创建时的绝对快照，可能因字号变更而失配，如 880 残留）
            chars = ind.get("firstLineChars", "")
            if chars and chars != "0":
                try:
                    first_line = str(int(round(int(chars) / 100 * 320)))
                except ValueError:
                    first_line = ind.get("firstLine", "")
            else:
                first_line = ind.get("firstLine", "")
            # 只取「带首行缩进」的正文档（跳过标题/落款等 jc=center 或 firstLine=0 段）
            try:
                if not first_line or int(first_line) <= 0:
                    continue
            except ValueError:
                continue

            actual = {
                "firstLine": first_line,
                "line": sp.get("line", ""),
                "lineRule": sp.get("lineRule", ""),
            }
            ok = all(actual.get(k) == v for k, v in PARA_SPEC.items())
            mismatches = [k for k in PARA_SPEC if actual.get(k) != PARA_SPEC[k]]
            return {
                "pass": ok,
                "detail": f"段落版式{'正确' if ok else '不符合: ' + ', '.join(mismatches)}",
                "actual": actual,
                "mismatches": mismatches,
            }
        return {"pass": False, "detail": "未找到带缩进的正文段落", "actual": {}}
    except Exception as e:
        return {"pass": False, "detail": f"检查异常: {e}", "actual": {}}


def _check_content_integrity(docx_path: Path, keywords: list[str] | None = None) -> dict:
    """检查 7: 内容完整性。

    提取所有文本，检查传入的关键词是否都在文档中。
    如未传入 keywords，仅检查文件非空。
    """
    try:
        texts = _extract_texts(docx_path)
        full = "".join(texts)
        if not full.strip():
            return {"pass": False, "detail": "文档内容为空", "char_count": 0, "missing": []}
        if keywords:
            missing = [kw for kw in keywords if kw not in full]
            return {
                "pass": len(missing) == 0,
                "detail": "所有关键文本均在" if not missing else f"缺失: {', '.join(missing)}",
                "char_count": len(full),
                "missing": missing,
            }
        return {"pass": True, "detail": f"文档非空（{len(full)} 字符）", "char_count": len(full), "missing": []}
    except Exception as e:
        return {"pass": False, "detail": f"检查异常: {e}", "char_count": 0, "missing": []}


# ═══════════════════ 第二层: Markdown 残留 ═══════════════════

def _check_md_residue(docx_path: Path) -> list[dict]:
    """检查 9-21: Markdown 语法残留。"""
    texts = _extract_texts(docx_path)
    results = []
    for name, pattern, level in MD_RESIDUE_CHECKS:
        regex = re.compile(pattern, re.MULTILINE)
        full = "\n".join(texts)
        matches = regex.findall(full)
        # 对于行首模式（分隔线/引用/标题标记），逐行检查
        if pattern.startswith("^"):
            line_matches = []
            for i, line in enumerate(full.split("\n")):
                if regex.search(line):
                    line_matches.append(f"第{i+1}行: {line.strip()[:50]}")
            ok = len(line_matches) == 0
            results.append({
                "name": name,
                "pass": ok,
                "level": level,
                "detail": "未检出" if ok else f"检出 {len(line_matches)} 处",
                "samples": line_matches[:3] if not ok else [],
            })
        else:
            ok = len(matches) == 0
            results.append({
                "name": name,
                "pass": ok,
                "level": level,
                "detail": "未检出" if ok else f"检出 {len(matches)} 处",
                "samples": matches[:3] if not ok else [],
            })
    return results


# ═══════════════════ 第三层: 编号连续性 ═══════════════════

def _check_numbering_continuity(docx_path: Path) -> list[dict]:
    """检查 22-23: 二级/三级编号跨节重置。

    按段落提取正文（跳过表格），识别"第X条"和一级标题"一、"作为分节边界，
    在每个边界区间内检查（一）（二）... 和 1．2．... 是否从 1 开始递增。
    """
    # 按 <w:p> 取整段文本，天然对齐段落边界；同时跳过表格，
    # 避免单元格中的金额/序号被误判为编号
    merged = [t.strip() for t in _extract_body_texts(docx_path) if t.strip()]

    h2_errors = []
    h3_errors = []
    current_section = 0  # 当前分节计数（第X条 或 一级标题）
    h2_counter = 0
    h3_counter = 0

    for line in merged:
        art_m = ARTICLE_RE.match(line)
        if art_m:
            current_section += 1
            h2_counter = 0
            h3_counter = 0
            continue

        # 一级标题"一、xxx"同为分节边界（报告/请示等非制度文种）
        h1_m = H1_OUT_RE.match(line)
        if h1_m:
            current_section += 1
            h2_counter = 0
            h3_counter = 0
            continue

        h2_m = H2_OUT_RE.match(line)
        if h2_m:
            expected = h2_counter + 1
            actual_str = h2_m.group().strip("（）")
            try:
                actual = _parse_cn_num(actual_str)
            except Exception:
                actual = -1
            if actual != expected:
                h2_errors.append(
                    f"第{current_section}节区间: 期望（{_cn_to_str(expected)}） 实际{line[:30]}"
                )
            h2_counter = actual if actual > 0 else expected
            h3_counter = 0
            continue

        h3_m = H3_OUT_RE.match(line)
        if h3_m:
            expected = h3_counter + 1
            actual_str = h3_m.group().rstrip("．.")
            try:
                actual = int(actual_str)
            except Exception:
                actual = -1
            if actual != expected:
                h3_errors.append(
                    f"第{current_section}节区间: 期望 {expected}． 实际{line[:30]}"
                )
            h3_counter = actual if actual > 0 else expected

    results = [
        {
            "name": "二级编号跨节重置（一）（二）...",
            "pass": len(h2_errors) == 0,
            "level": "ERROR",
            "detail": "全部正确" if not h2_errors else f"{len(h2_errors)} 处错误",
            "samples": h2_errors[:5],
        },
        {
            "name": "三级编号跨节重置 1．2．...",
            "pass": len(h3_errors) == 0,
            "level": "ERROR",
            "detail": "全部正确" if not h3_errors else f"{len(h3_errors)} 处错误",
            "samples": h3_errors[:5],
        },
    ]
    return results


def _cn_to_str(n: int) -> str:
    """1 → 一, 10 → 十, 用最小表示。"""
    CN = "一二三四五六七八九十"
    if 1 <= n <= 10:
        return CN[n - 1]
    return str(n)


# ═══════════════════ 第三·五层: 主题字体/语言 ═══════════════════

def _read_part(docx_path: Path, part: str) -> str | None:
    """读取 docx 内指定部件文本；缺失返回 None。"""
    try:
        with zipfile.ZipFile(docx_path, "r") as z:
            try:
                with z.open(part) as f:
                    return f.read().decode("utf-8", errors="replace")
            except KeyError:
                return None
    except Exception:
        return None


def _theme_inert(docx_path: Path) -> tuple[bool, str]:
    """判断主题对渲染是否完全无效（用于豁免"日文底子"拦截）。

    豁免须同时满足：
      1) document.xml + styles.xml 中主题字体引用（w:*Theme=）计数为 0，
         即没有任何 run/style 依赖 theme1.xml 的字体方案；
      2) styles.xml 的 docDefaults 已显式指定非空 eastAsia 字体，
         正文兜底不落回主题。

    两者成立时，theme1.xml 的 a:ea 空槽与 Jpan 日文回退永远不会被触发，
    属"模板底子脏但零实际影响"，应降级为提示而非阻断。
    真实事故里的带雷文档（rFonts 缺 eastAsia、正文继承主题）refs>0 或
    docDefaults 无显式东亚字体，不会命中豁免，仍被拦截。
    """
    refs = 0
    for part in ("word/document.xml", "word/styles.xml"):
        xml = _read_part(docx_path, part) or ""
        refs += len(re.findall(r'w:(?:ascii|hAnsi|eastAsia|cs)Theme="', xml))

    styles = _read_part(docx_path, "word/styles.xml") or ""
    dd_m = re.search(r"<w:docDefaults>.*?</w:docDefaults>", styles, re.S)
    east = ""
    if dd_m:
        ea_m = re.search(r'w:eastAsia="([^"]*)"', dd_m.group(0))
        if ea_m:
            east = ea_m.group(1).strip()

    if refs == 0 and east:
        return True, (f"主题字体引用 0 处，docDefaults 已钉 eastAsia={east}，"
                      f"主题空槽/Jpan 回退不参与渲染")
    return False, (f"主题字体引用 {refs} 处，docDefaults eastAsia="
                   f"{'未钉' if not east else east}")


def _check_theme_fonts(docx_path: Path) -> list[dict]:
    """检查 theme1.xml / settings.xml：日文模板底子的三处雷。

    1) 部件必须存在（缺失时 Word 会用隐式主题补全，存在同样风险）；
    2) 不得出现 ＭＳ 明朝/MS Mincho/ゴシック 等日文回退字体；
    3) majorFont/minorFont 的 <a:ea typeface=""/> 东亚槽位不得为空；
    4) <w:themeFontLang w:eastAsia="..."/> 不得为 ja-JP，应为 zh-CN。

    豁免：当 `_theme_inert()` 成立（无主题字体引用且 docDefaults 已显式
    锁定东亚字体）时，上述 2)/3)/4) 一律降为 WARNING —— 脏底子不会被用到。
    """
    inert, inert_reason = _theme_inert(docx_path)
    # 惰性主题：不构成实际字形风险，降级为提示；否则阻断
    lvl = "WARNING" if inert else "ERROR"
    suffix = f"（豁免：{inert_reason}）" if inert else ""

    results: list[dict] = []
    for part in THEME_PARTS:
        xml = _read_part(docx_path, part)
        label = part.split("/")[-1]
        if xml is None:
            results.append({
                "name": f"{label} 存在性",
                "pass": False,
                "level": lvl,
                "detail": f"缺少 {part}，Word 将隐式补全主题（可能落入日文字体回退）{suffix}",
                "samples": [],
            })
            continue
        results.append({
            "name": f"{label} 存在性",
            "pass": True,
            "level": "INFO",
            "detail": "部件存在",
            "samples": [],
        })

        bad_hits = [tok for tok in THEME_BAD_FONTS if tok in xml]
        results.append({
            "name": f"{label} 日文回退字体（MS明朝等）",
            "pass": not bad_hits,
            "level": lvl,
            "detail": ("未检出日文回退字体" if not bad_hits
                       else f"检出禁忌字体标记: {', '.join(bad_hits)}{suffix}"),
            "samples": bad_hits,
        })

        if part.endswith("theme1.xml"):
            # 提取 majorFont/minorFont 两个槽内的 <a:ea typeface="..."/>
            empty_slots: list[str] = []
            for slot_name in ("majorFont", "minorFont"):
                slot_m = re.search(rf"<a:{slot_name}>(.*?)</a:{slot_name}>", xml, re.S)
                if not slot_m:
                    empty_slots.append(f"{slot_name}（槽位缺失）")
                    continue
                ea_m = re.search(r'<a:ea[^>]*typeface="([^"]*)"', slot_m.group(1))
                if ea_m is None:
                    empty_slots.append(f"{slot_name}（无 a:ea 节点）")
                elif not ea_m.group(1).strip():
                    empty_slots.append(f"{slot_name}（a:ea 为空）")
            results.append({
                "name": "theme1.xml 东亚字体槽位 a:ea",
                "pass": not empty_slots,
                "level": lvl,
                "detail": ("major/minor 东亚槽位均已显式指定中文字体" if not empty_slots
                           else "存在空东亚槽位，将回退 Jpan→MS 明朝: "
                                + ", ".join(empty_slots) + suffix),
                "samples": empty_slots,
            })
        else:
            lang_m = re.search(r'<w:themeFontLang[^>]*w:eastAsia="([^"]+)"', xml)
            if lang_m is None:
                # 无 themeFontLang 时 Word 可能按系统/主题推断，显式告警
                lang_ok = False
                detail = "未找到 <w:themeFontLang w:eastAsia=...>，东亚语言未钉为 zh-CN"
                samples = ["themeFontLang 缺失"]
            else:
                lang = lang_m.group(1)
                lang_ok = lang == "zh-CN"
                detail = ("东亚语言为 zh-CN" if lang_ok
                          else f"东亚语言被钉为 {lang}，应为 zh-CN（ja-JP 会触发 MS 明朝）")
                samples = [] if lang_ok else [f"eastAsia={lang}"]
            results.append({
                "name": "settings.xml 东亚语言 themeFontLang",
                "pass": lang_ok,
                "level": lvl,
                "detail": detail if lang_ok else detail + suffix,
                "samples": samples,
            })
    return results


# ═══════════════════ 第四层: 综合 ═══════════════════

def _check_file_size(docx_path: Path) -> dict:
    """检查 24: 文件大小合理性。"""
    size = docx_path.stat().st_size
    if size < 2500:
        return {"pass": False, "detail": f"文件过小 ({size} B)，疑似正文丢失", "level": "CRITICAL", "size": size}
    elif size > 500000:
        return {"pass": True, "detail": f"文件较大 ({size} B)，如有异常请检查图片嵌入", "level": "INFO", "size": size}
    return {"pass": True, "detail": f"正常 ({size // 1024} KB)", "level": "INFO", "size": size}


def _count_paragraphs(docx_path: Path) -> dict:
    """检查 25: 段落统计。"""
    try:
        with zipfile.ZipFile(docx_path, "r") as z:
            with z.open("word/document.xml") as f:
                tree = ET.parse(f)
        counts = {}
        total = 0
        for p in tree.iter(f"{{{NS['w']}}}p"):
            total += 1
            ppr = p.find("w:pPr", NS)
            if ppr is not None:
                pstyle = ppr.find("w:pStyle", NS)
                if pstyle is not None:
                    sid = pstyle.get(f"{{{NS['w']}}}val", "?")
                    counts[sid] = counts.get(sid, 0) + 1
                else:
                    counts["(无样式)"] = counts.get("(无样式)", 0) + 1
            else:
                counts["(无样式)"] = counts.get("(无样式)", 0) + 1
        return {"pass": True, "detail": f"共 {total} 段", "total": total, "by_style": counts, "level": "INFO"}
    except Exception as e:
        return {"pass": True, "detail": f"统计异常: {e}", "total": 0, "by_style": {}, "level": "INFO"}


# ═══════════════════ 报告输出 ═══════════════════

# ANSI 颜色
_G = "\033[32m"
_R = "\033[31m"
_Y = "\033[33m"
_B = "\033[36m"
_RESET = "\033[0m"


def _status_icon(passed: bool | None) -> str:
    if passed is True:
        return f"{_G}✅{_RESET}"
    elif passed is False:
        return f"{_R}❌{_RESET}"
    return f"{_Y}⚠️{_RESET}"


def terminal_report(docx_path: Path, all_results: list[dict]) -> int:
    """输出彩色终端报告，返回 exit code (0=通过, 1=不通过)。"""
    size = docx_path.stat().st_size
    print(f"{_B}══════════════════════════════════════════{_RESET}")
    print(f"{_B}  公文版式质检报告{_RESET}")
    print(f"{_B}══════════════════════════════════════════{_RESET}")
    print(f"  文件: {docx_path}")
    print(f"  大小: {size:,} B ({size // 1024} KB)")
    print()

    fail_count = 0
    warn_count = 0
    total_checks = 0

    layers = {
        "第一层: 版式结构": (range(0, 8), "#1-#8"),
        "第二层: Markdown 残留": (None, "#9-#21"),
        "第三层: 编号连续性": (None, "#22-#23"),
        "第三·五层: 主题字体/语言": (None, "#27-#32"),
        "第四层: 综合报告": (None, "#24-#26"),
    }

    layer_idx = 0
    for layer_name, (_, label) in layers.items():
        print(f"{_B}── {layer_name} ({label}) ──{_RESET}")
        # 第一层的 8 项是扁平的 list[dict]
        if layer_idx == 0:
            layer_items = []
            # 检查 1
            layer_items.append(("页面尺寸", all_results[0]))
            # 检查 2-5 + 编号
            for r in all_results[1]:  # style results list
                label_name = f"样式 #{r['id']} ({r['name']})"
                layer_items.append((label_name, r))
            # 检查 6
            layer_items.append(("段落版式", all_results[2]))
            # 检查 7
            layer_items.append(("内容完整性", all_results[3]))
            # 检查 8 就是本报告本身，不单独列出
        elif layer_idx == 1:
            layer_items = [(r["name"], r) for r in all_results[4]]
        elif layer_idx == 2:
            layer_items = [(r["name"], r) for r in all_results[5]]
        elif layer_idx == 3:
            # 主题字体/语言层，位置在 results[6]
            layer_items = [(r["name"], r) for r in all_results[6]]
        else:
            layer_items = [
                ("文件大小", all_results[7]),
                ("段落统计", all_results[8]),
            ]

        for name, r in layer_items:
            total_checks += 1
            level = r.get("level", "ERROR" if r.get("pass") is False else "INFO")
            # 未通过但已降级为 WARNING 的项显示告警图标，避免与阻断混淆
            if r["pass"] is False and level == "WARNING":
                icon = _status_icon(None)
            else:
                icon = _status_icon(r["pass"])
            detail = r.get("detail", "")
            actual = r.get("actual", {})
            actual_str = ""
            if actual and not r.get("pass", True):
                actual_str = f"  → 实际: {actual}"
            print(f"  {icon} {name}: {detail}{actual_str}")
            if not r.get("pass", False) and r.get("pass") is not None:
                if level == "CRITICAL" or level == "ERROR":
                    fail_count += 1
                elif level == "WARNING":
                    warn_count += 1
            # 输出样本
            samples = r.get("samples", [])
            for s in samples[:3]:
                print(f"      {_Y}{s}{_RESET}")
        layer_idx += 1
        print()

    # 综合判定
    print(f"{_B}──────────────────────────────────────────{_RESET}")
    print(f"  总检查项: {total_checks}")
    print(f"  通过: {total_checks - fail_count - warn_count}  |  阻断: {fail_count}  |  告警: {warn_count}")
    if fail_count > 0:
        print(f"  {_R}综合判定: 不通过{_RESET} (存在 {fail_count} 项阻断)")
        print(f"{_B}══════════════════════════════════════════{_RESET}")
        return 1
    elif warn_count > 0:
        print(f"  {_Y}综合判定: 通过（有 {warn_count} 项告警）{_RESET}")
        print(f"{_B}══════════════════════════════════════════{_RESET}")
        return 0
    else:
        print(f"  {_G}综合判定: 全部通过{_RESET}")
        print(f"{_B}══════════════════════════════════════════{_RESET}")
        return 0


def json_report(docx_path: Path, all_results: list[dict]) -> int:
    """输出 JSON 报告。"""
    output = {
        "file": str(docx_path),
        "size": docx_path.stat().st_size,
        "results": {
            "layer1_format": {
                "page": all_results[0],
                "styles": all_results[1],
                "paragraph_format": all_results[2],
                "content_integrity": all_results[3],
            },
            "layer2_md_residue": all_results[4],
            "layer3_numbering": all_results[5],
            "layer3_5_theme": all_results[6],
            "layer4_summary": {
                "file_size": all_results[7],
                "paragraph_stats": all_results[8],
            },
        },
    }
    # 统计
    all_checks = (
        [all_results[0]]
        + all_results[1]
        + [all_results[2]]
        + [all_results[3]]
        + all_results[4]
        + all_results[5]
        + all_results[6]
        + [all_results[7]]
        + [all_results[8]]
    )
    fail_count = sum(1 for r in all_checks if r.get("pass") is False and r.get("level") in ("ERROR", "CRITICAL"))
    output["summary"] = {
        "total_checks": len(all_checks),
        "failed": fail_count,
        "passed": sum(1 for r in all_checks if r.get("pass") is True),
        "verdict": "PASS" if fail_count == 0 else "FAIL",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 1 if fail_count > 0 else 0


# ═══════════════════ 主入口 ═══════════════════

def run(docx_path: Path, keywords: list[str] | None = None, fmt: str = "text") -> int:
    """执行全部检查，返回 exit code。"""
    if not docx_path.exists():
        print(f"error: 文件不存在: {docx_path}", file=sys.stderr)
        return 1
    if not docx_path.suffix.lower() in (".docx",):
        print(f"error: 仅支持 .docx 文件: {docx_path}", file=sys.stderr)
        return 1

    results = [
        _check_page(docx_path),            # 0: 页面尺寸
        _check_styles(docx_path),          # 1: 样式检查 (list)
        _check_paragraph_format(docx_path),  # 2: 段落版式
        _check_content_integrity(docx_path, keywords),  # 3: 内容完整性
        _check_md_residue(docx_path),      # 4: MD残留 (list)
        _check_numbering_continuity(docx_path),  # 5: 编号连续性 (list)
        _check_theme_fonts(docx_path),     # 6: 主题字体/语言 (list)
        _check_file_size(docx_path),       # 7: 文件大小
        _count_paragraphs(docx_path),      # 8: 段落统计
    ]

    if fmt == "json":
        return json_report(docx_path, results)
    return terminal_report(docx_path, results)


def main() -> int:
    parser = argparse.ArgumentParser(description="gb_gongwen.py 产物质检工具")
    parser.add_argument("docx", help="待检查的 .docx 文件路径")
    parser.add_argument("--keywords", nargs="*", help="内容完整性检查：需要在文档中出现的文本片段")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式 (默认 text)")
    args = parser.parse_args()
    return run(Path(args.docx), keywords=args.keywords, fmt=args.format)


if __name__ == "__main__":
    raise SystemExit(main())
