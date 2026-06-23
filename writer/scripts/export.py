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


def count_chinese(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def extract_chapter_info(text):
    """从章节正文提取章号、标题、正文"""
    lines = text.split('\n')
    title_line = ''
    body_start = 0

    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('# '):
            title_line = s[2:].strip()
        if s == '' and i > 0 and lines[i-1].startswith('#'):
            body_start = i + 1
            break

    # 从文件名猜测章号
    ch_num = 0

    body = '\n'.join(lines[body_start:]).strip()
    return ch_num, title_line, body


# ===========================
# 番茄格式（纯文本）
# ===========================
def to_fanqie(text, ch_num):
    """番茄：纯文本，去 Markdown，章节标题「第X章 标题」"""
    lines = text.split('\n')
    result = []

    # 处理标题
    title_line = ''
    body_start = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('# '):
            title_line = s[2:].strip()
            # 去掉 chXXX 前缀
            title_line = re.sub(r'^ch\d+\s*[—\-]\s*', '', title_line)
            if not title_line.startswith('第'):
                title_line = f'第{ch_num}章 {title_line}'
            result.append(title_line)
            result.append('')
        if s == '' and i > 0 and lines[i-1].startswith('#'):
            body_start = i + 1
            break

    for line in lines[body_start:]:
        stripped = line.rstrip()
        # 清除 Markdown 格式
        stripped = re.sub(r'\*\*(.*?)\*\*', r'\1', stripped)  # 粗体
        stripped = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'\1', stripped)  # 斜体
        # 清除 HTML
        stripped = re.sub(r'<[^>]+>', '', stripped)
        # 清除分隔线
        if re.match(r'^[-*=_]{3,}$', stripped.strip()):
            stripped = ''
        # 保留空行分段
        result.append(stripped)

    # 清理连续空行（最多2个）
    result = clean_blank_lines(result)
    return '\n'.join(result)


# ===========================
# 起点格式
# ===========================
def to_qidian(text, ch_num):
    """起点：保留 # 标题格式，保留基本 Markdown，对话可用「」"""
    lines = text.split('\n')
    result = []

    title_line = ''
    body_start = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('# '):
            title_line = s[2:].strip()
            if not title_line.startswith('第'):
                title_line = f'第{ch_num}章 {title_line}'
            result.append(title_line)
            result.append('')
        if s == '' and i > 0 and lines[i-1].startswith('#'):
            body_start = i + 1
            break

    for line in lines[body_start:]:
        stripped = line.rstrip()
        # 起点支持基本 Markdown，只清 HTML
        stripped = re.sub(r'<[^>]+>', '', stripped)
        if re.match(r'^[-*=_]{3,}$', stripped.strip()):
            continue
        result.append(stripped)

    result = clean_blank_lines(result)
    return '\n'.join(result)


# ===========================
# 飞卢格式
# ===========================
def to_feilu(text, ch_num):
    """飞卢：章节号短横标题，纯正文"""
    lines = text.split('\n')
    result = []

    title_line = ''
    body_start = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('# '):
            title_line = s[2:].strip()
            title_line = re.sub(r'^ch\d+\s*[—\-]\s*', '', title_line)
            result.append(f'{ch_num:03d}-{title_line}')
            result.append('')
        if s == '' and i > 0 and lines[i-1].startswith('#'):
            body_start = i + 1
            break

    for line in lines[body_start:]:
        stripped = line.rstrip()
        # 清除 Markdown
        stripped = re.sub(r'\*\*(.*?)\*\*', r'\1', stripped)
        stripped = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'\1', stripped)
        stripped = re.sub(r'<[^>]+>', '', stripped)
        if re.match(r'^[-*=_]{3,}$', stripped.strip()):
            continue
        result.append(stripped)

    result = clean_blank_lines(result)
    return '\n'.join(result)


def clean_blank_lines(lines):
    """清理连续空行，最多保留1个空行"""
    result = []
    prev_blank = False
    for line in lines:
        is_blank = line.strip() == ''
        if is_blank and prev_blank:
            continue
        result.append(line)
        prev_blank = is_blank
    return result


def scan_chapters(project_root, ch_start=None, ch_end=None):
    """扫描章节文件"""
    chapters_dir = None
    for d in [os.path.join(project_root, '正文'), os.path.join(project_root, 'chapters')]:
        if os.path.isdir(d):
            chapters_dir = d
            break
    if not chapters_dir:
        print("错误：未找到正文目录")
        sys.exit(1)

    files = sorted([f for f in os.listdir(chapters_dir) if f.endswith('.md')],
                   key=lambda x: int(re.search(r'(\d+)', x).group(1)) if re.search(r'(\d+)', x) else 0)

    if ch_start is not None:
        files = [f for f in files if
                 ch_start <= int(re.search(r'(\d+)', f).group(1)) <= (ch_end or ch_start + 999)]

    chapters = []
    for f in files:
        fp = os.path.join(chapters_dir, f)
        with open(fp, 'r', encoding='utf-8') as fh:
            text = fh.read()
        ch_num = int(re.search(r'(\d+)', f).group(1))
        chapters.append((ch_num, text, f))

    return chapters


def export_all(project_root, platforms, output_dir, ch_start=None, ch_end=None):
    """导出到所有指定平台格式"""
    chapters = scan_chapters(project_root, ch_start, ch_end)

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
                # 生成文件名
                if plat == 'qidian':
                    # 单文件名：从标题提取
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

        print(f"{'📕 番茄' if plat == 'fanqie' else ('📗 起点' if plat == 'qidian' else '📘 飞卢')}: "
              f"{out_path}/  ({exported}/{len(chapters)} 章)")


def main():
    parser = argparse.ArgumentParser(description='多平台格式导出')
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
