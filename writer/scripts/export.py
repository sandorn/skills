#!/usr/bin/env python3
"""多平台格式导出 — 番茄/起点/飞卢 三种格式。

用法：
    python export.py <项目根>                       # 导出全部章节到三种格式
    python export.py <项目根> --platform fanqie      # 仅番茄
    python export.py <项目根> --platform qidian      # 仅起点
    python export.py <项目根> --platform feilu       # 仅飞卢
    python export.py <项目根> --ch 1 60              # 仅指定范围
    python export.py <项目根> --output-dir ./out     # 指定输出目录

输出格式：
    {output_dir}/
    ├── fanqie/       # 纯文本，无 Markdown 标记
    │   ├── 001.txt
    │   └── ...
    ├── qidian/       # 标准起点格式
    │   ├── 第一章 标题.txt
    │   └── ...
    └── feilu/        # 飞卢格式（章节号+标题）
        ├── 001-标题.txt
        └── ...
"""

import re, os, sys, argparse
from pathlib import Path

from lib import count_chinese, find_chapters_dir, scan_chapter_files


def parse_chapter(text: str) -> tuple[str, int, str]:
    """解析章节文本，返回 (title_line, body_start_idx, body_text)。

    返回:
      title_line: H1 标题行内容（去掉 '# ' 前缀）
      body_start_idx: 正文起始行号
      body_text: 正文纯文本
    """
    lines = text.split('\n')
    title_line = ''
    body_start = 0

    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('# '):
            title_line = s[2:].strip()
        if s == '' and i > 0 and lines[i - 1].startswith('#'):
            body_start = i + 1
            break

    body = '\n'.join(lines[body_start:]).strip()
    return title_line, body_start, body


def _export_base(text: str, ch_num: int, title_template: str,
                 strip_markdown: bool, strip_html: bool) -> str:
    """通用导出逻辑：标题格式化 + 正文清洗 + 空行压缩。

    参数:
      text: 原始 .md 文本
      ch_num: 章节号
      title_template: 标题格式，如 '第{ch}章 {title}' 或 '{ch:03d}-{title}'
      strip_markdown: 是否清除 **粗体** 和 *斜体*
      strip_html: 是否清除 HTML 标签
    """
    title, body_start, body = parse_chapter(text)
    lines = text.split('\n')

    result = []

    # 格式化标题
    clean_title = re.sub(r'^ch\d+\s*[—\-]\s*', '', title)
    formatted_title = title_template.format(ch=ch_num, title=clean_title)
    result.append(formatted_title)
    result.append('')

    # 处理正文
    for line in lines[body_start:]:
        stripped = line.rstrip()
        if not stripped.strip():
            result.append('')
            continue
        if strip_markdown:
            stripped = re.sub(r'\*\*(.*?)\*\*', r'\1', stripped)
            stripped = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'\1',
                              stripped)
        if strip_html:
            stripped = re.sub(r'<[^>]+>', '', stripped)
        # 分隔线
        if re.match(r'^[-*=_]{3,}$', stripped.strip()):
            continue
        result.append(stripped)

    # 清理连续空行
    result = _clean_blanks(result)
    return '\n'.join(result)


def to_fanqie(text: str, ch_num: int) -> str:
    """番茄格式：纯文本，去 Markdown + HTML。"""
    return _export_base(text, ch_num, '第{ch}章 {title}',
                        strip_markdown=True, strip_html=True)


def to_qidian(text: str, ch_num: int) -> str:
    """起点格式：保留 Markdown，去 HTML。"""
    return _export_base(text, ch_num, '第{ch}章 {title}',
                        strip_markdown=False, strip_html=True)


def to_feilu(text: str, ch_num: int) -> str:
    """飞卢格式：章节号-标题，去 Markdown + HTML。"""
    return _export_base(text, ch_num, '{ch:03d}-{title}',
                        strip_markdown=True, strip_html=True)


def _clean_blanks(lines: list[str]) -> list[str]:
    """清理连续空行，最多保留1个空行。"""
    result = []
    prev_blank = False
    for line in lines:
        is_blank = line.strip() == ''
        if is_blank and prev_blank:
            continue
        result.append(line)
        prev_blank = is_blank
    return result


def export_all(project_root, platforms, output_dir, ch_start=None, ch_end=None):
    """导出到所有指定平台格式"""
    chapters_dir = find_chapters_dir(project_root)
    if not chapters_dir:
        print("错误：未找到正文目录")
        sys.exit(1)

    files = scan_chapter_files(chapters_dir, ch_start, ch_end)
    if not files:
        print("错误：未找到章节文件")
        sys.exit(1)

    chapters = []
    for f in files:
        fp = os.path.join(chapters_dir, f)
        with open(fp, 'r', encoding='utf-8') as fh:
            text = fh.read()
        ch_num = int(re.search(r'(\d+)', f).group(1))
        chapters.append((ch_num, text, f))

    platform_funcs = {
        'fanqie': ('fanqie', to_fanqie, '.txt'),
        'qidian': ('qidian', to_qidian, '.txt'),
        'feilu': ('feilu', to_feilu, '.txt'),
    }

    for plat in platforms:
        plat_dir, func, ext = platform_funcs[plat]
        out_path = os.path.join(output_dir, plat_dir)
        os.makedirs(out_path, exist_ok=True)

        exported = 0
        for ch_num, text, fname in chapters:
            try:
                output = func(text, ch_num)
                if plat == 'qidian':
                    first_line = output.split('\n')[0] if output else f'第{ch_num}章'
                    safe_name = re.sub(r'[\\/:*?"<>|]', '_', first_line)[:50]
                elif plat == 'feilu':
                    safe_name = f'{ch_num:03d}-{fname.replace(".md", "")}'
                else:
                    safe_name = f'{ch_num:03d}'

                out_file = os.path.join(out_path, f'{safe_name}{ext}')
                with open(out_file, 'w', encoding='utf-8') as fh:
                    fh.write(output)
                exported += 1
            except Exception as e:
                print(f"  ⚠️  {fname}: 导出失败 - {e}")

        emoji = {'fanqie': '📕 番茄', 'qidian': '📗 起点', 'feilu': '📘 飞卢'}
        print(f"{emoji.get(plat, plat)}: {out_path}/  ({exported}/{len(chapters)} 章)")


def main():
    parser = argparse.ArgumentParser(
        description='多平台格式导出 — 番茄/起点/飞卢',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='示例:\n'
               '  python export.py .\n'
               '  python export.py . --platform fanqie\n'
               '  python export.py . --ch 1 60 --output-dir ./export',
    )
    parser.add_argument('project_root', help='项目根目录')
    parser.add_argument('--platform', choices=['fanqie', 'qidian', 'feilu', 'all'],
                        default='all', help='目标平台')
    parser.add_argument('--ch', type=int, nargs=2, metavar=('START', 'END'),
                        help='章节范围')
    parser.add_argument('--output-dir', default='./export', help='输出目录')
    args = parser.parse_args()

    if not os.path.isdir(args.project_root):
        print(f"错误：项目目录不存在 - {args.project_root}")
        sys.exit(2)

    platforms = ['fanqie', 'qidian', 'feilu'] if args.platform == 'all' else [args.platform]
    ch_start, ch_end = (args.ch[0], args.ch[1]) if args.ch else (None, None)

    output_dir = os.path.abspath(args.output_dir)
    print(f"📦 导出项目: {args.project_root}")
    print(f"📁 输出目录: {output_dir}")
    print(f"🎯 平台: {', '.join(platforms)}")
    if args.ch:
        print(f"📖 范围: ch{ch_start}-ch{ch_end}")
    print()

    export_all(args.project_root, platforms, output_dir, ch_start, ch_end)
    print()
    print("✅ 导出完成")


if __name__ == '__main__':
    main()
