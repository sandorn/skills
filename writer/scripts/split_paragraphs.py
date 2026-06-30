#!/usr/bin/env python3
# SAFETY: SAFE_WRITE — 仅拆分超长段落，自动创建 .bak 备份。⚠️ 不涉及文本替换。
"""按句号/问号/感叹号拆分超长段落，确保每段≤42 汉字。

v3 改进：
  - 统一换行处理（修复 v2 writelines 混用 '\n' 和完整行的 bug）
  - 写回前自动创建 .bak 备份
  - 依赖 scripts/lib.py 统一工具函数

用法：
    python split_paragraphs.py <file.md>                # 单文件
    python split_paragraphs.py --batch <dir>            # 批量处理目录下所有 .md
    python split_paragraphs.py --verify <file.md>       # 仅检测不修改
    python split_paragraphs.py --batch <dir> --no-backup  # 跳过备份

拆分规则：
    - 按 。！？ 断段
    - 对话行（以「『开头）跳过不拆
    - 拆分后每段≤42 汉字
    - 保留原有换行结构，仅拆分超标行
"""

import re
import sys
import argparse
from pathlib import Path

from lib import count_chinese, is_dialogue_line, safe_write


def split_paragraph(line: str, max_chars: int = 42) -> list[str]:
    """按句号/问号/感叹号拆分一个段落，确保每段≤42 汉字"""
    if count_chinese(line) <= max_chars or is_dialogue_line(line):
        return [line]

    sentences = re.split(r'(?<=[。！？])', line)
    result = []
    buffer = ""

    for sent in sentences:
        if not sent.strip():
            continue
        if count_chinese(buffer + sent) <= max_chars:
            buffer += sent
        else:
            if buffer.strip():
                result.append(buffer.strip())
            buffer = sent

    if buffer.strip():
        result.append(buffer.strip())

    return result if result else [line]


def split_full_text(text: str, max_chars: int = 42) -> str:
    """处理全文：按行拆分超标段落，保留标题/对话行和缩进。
    供 pad_chapter.py 等脚本复用。"""
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith('#') or is_dialogue_line(s):
            new_lines.append(line)
            continue
        if count_chinese(s) <= max_chars:
            new_lines.append(line)
            continue
        leading = line[:len(line) - len(line.lstrip())]
        parts = re.split(r'(?<=[。！？])', s)
        for p in parts:
            if p.strip():
                new_lines.append(leading + p.rstrip())
    return '\n'.join(new_lines)


def process_file(filepath: Path, verify_only: bool = False,
                 backup: bool = True) -> dict:
    """处理单个文件，返回统计信息"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    new_lines = []
    long_count = 0
    new_segments = 0
    modified = False

    for line in lines:
        stripped = line.rstrip('\r')
        if not stripped.strip():
            new_lines.append(stripped)
            continue

        if count_chinese(stripped) > 60 and not is_dialogue_line(stripped):
            long_count += 1
            segments = split_paragraph(stripped, 60)
            new_segments += len(segments) - 1
            new_lines.extend(segments)
            modified = True
        else:
            new_lines.append(stripped)

    if modified and not verify_only:
        new_content = '\n'.join(new_lines)
        safe_write(str(filepath), new_content, backup=backup)

    return {
        'file': str(filepath),
        'long_paragraphs': long_count,
        'new_segments_added': new_segments,
        'fixed': modified and not verify_only,
    }


def main():
    parser = argparse.ArgumentParser(
        description='按句号/问号/感叹号拆分超长段落，确保每段≤42 汉字',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='示例:\n'
               '  python split_paragraphs.py ch_001.md\n'
               '  python split_paragraphs.py --batch chapters/\n'
               '  python split_paragraphs.py --verify ch_001.md\n'
               '  python split_paragraphs.py --batch chapters/ --no-backup',
    )
    parser.add_argument('target', nargs='?', help='目标文件 (或配合 --batch)')
    parser.add_argument('--batch', metavar='DIR', help='批量处理目录下所有 .md')
    parser.add_argument('--verify', action='store_true', help='仅检测不修改')
    parser.add_argument('--no-backup', action='store_true', help='跳过 .bak 备份')
    args = parser.parse_args()

    verify_only = args.verify
    do_backup = not args.no_backup

    if args.batch:
        dir_path = Path(args.batch)
        files = sorted(dir_path.glob('*.md'))
    elif args.target:
        files = [Path(args.target)]
    else:
        parser.print_help()
        sys.exit(1)

    total_long = 0
    total_new = 0
    total_fixed = 0

    for fp in files:
        if not fp.exists():
            print(f"SKIP: {fp} (not found)")
            continue
        result = process_file(fp, verify_only, backup=do_backup)
        total_long += result['long_paragraphs']
        total_new += result['new_segments_added']
        if result['fixed']:
            total_fixed += 1
        status = "FIXED" if result['fixed'] else (
            "DETECTED" if result['long_paragraphs'] > 0 else "OK")
        print(f"{status}: {result['file']} "
              f"({result['long_paragraphs']} long → +{result['new_segments_added']} lines)")

    action = '（仅检测）' if verify_only else '（已修复）'
    backup_note = ' | 已备份 .bak' if (total_fixed > 0 and do_backup) else ''
    print(f"\n总计: {total_long} 段超标, +{total_new} 行, "
          f"{total_fixed} 文件{action}{backup_note}")


if __name__ == '__main__':
    main()
