#!/usr/bin/env python3
# SAFETY: SAFE_WRITE — 压缩正文段落间空行，自动 .bak 备份。⚠️ 不涉及文本替换。
"""压缩章节正文中的段落间空行：段间统一为单换行，禁止连续换行。

【背景】番茄/起点等网文平台的富文本编辑器把回车当作段落分隔符，
       正文若段间保留空行（\\n\\n），粘贴后会出现双倍换行/空段，
       需要人工删除。因此源文件段间统一使用单换行。

【保留的空行】章节首行标题（以 `# ` 开头，形如 `# 第X章 XX`）与正文之间的那一个空行。
             无 `# ` 前缀的老稿也兼容（回退按「第X章」中文标题识别）。

用法：
    python collapse_blanks.py <file.md>                # 单文件
    python collapse_blanks.py --batch <dir>            # 批量处理目录
    python collapse_blanks.py --verify <file.md>       # 仅检测不修改
    python collapse_blanks.py --batch <dir> --no-backup  # 跳过 .bak
"""

from __future__ import annotations

import sys
import argparse
from pathlib import Path

# 与其他脚本一致，从同目录 lib.py 导入
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import safe_write  # noqa: E402


def collapse_text(text: str) -> tuple[str, int]:
    """压缩空行。返回 (new_text, blank_lines_removed)。

    规则：
      - 保留首行标题后的第一个空行（若存在）
      - 正文中任何连续换行统一压缩为单换行
      - 尾部空行去除
    """
    lines = text.split('\n')
    if not lines:
        return text, 0

    result: list[str] = []
    n = len(lines)
    i = 0
    removed = 0

    # 首行按原样保留（章节标题）
    first = lines[0]
    result.append(first)
    i = 1

    # 首行是章节标题（`第X章` / `# 第X章` / `## ...`）时，跳过标题后的空行并保留一个
    first_stripped = first.strip()
    is_title = (
        first_stripped.startswith('#')
        or (first_stripped.startswith('第') and '章' in first_stripped[:12])
    )
    if is_title:
        # 吞掉紧跟标题的所有空行，只保留一个
        saw_blank = False
        while i < n and lines[i].strip() == '':
            if not saw_blank:
                result.append('')
                saw_blank = True
            else:
                removed += 1
            i += 1

    # 处理正文剩余部分：段间任何空行都压缩掉
    prev_blank = False  # 前一行是否为空
    while i < n:
        cur = lines[i].rstrip('\r')
        if cur.strip() == '':
            # 正文中间的空行——一律丢弃
            if not prev_blank:
                removed += 0  # 首次遇到空行也算一次要压掉的
            removed += 1
            prev_blank = True
        else:
            result.append(cur)
            prev_blank = False
        i += 1

    # 去掉末尾多余空行（result 尾）
    while len(result) > 1 and result[-1].strip() == '':
        result.pop()

    new_text = '\n'.join(result)
    # 保留文件末换行
    if text.endswith('\n') and not new_text.endswith('\n'):
        new_text += '\n'

    return new_text, removed


def process_file(filepath: Path, verify_only: bool = False,
                 backup: bool = True) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content, removed = collapse_text(content)
    changed = (new_content != content)

    result = {
        'file': str(filepath),
        'blanks_removed': removed,
        'changed': changed,
        'modified': False,
    }

    if changed and not verify_only:
        safe_write(str(filepath), new_content, backup=backup)
        result['modified'] = True

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?', help='单个 .md 文件路径')
    parser.add_argument('--batch', metavar='DIR', help='批量处理目录下所有 ch_*.md')
    parser.add_argument('--verify', action='store_true', help='只检测不修改')
    parser.add_argument('--no-backup', action='store_true', help='跳过 .bak 备份')
    args = parser.parse_args()

    if not args.path and not args.batch:
        parser.print_help()
        return 1

    files: list[Path] = []
    if args.batch:
        d = Path(args.batch)
        if not d.is_dir():
            print(f'错误：目录不存在 {d}', file=sys.stderr)
            return 1
        files = sorted(d.glob('ch_*.md'))
    elif args.path:
        p = Path(args.path)
        if not p.is_file():
            print(f'错误：文件不存在 {p}', file=sys.stderr)
            return 1
        files = [p]

    total_removed = 0
    modified_files = 0
    for fp in files:
        r = process_file(fp, verify_only=args.verify, backup=not args.no_backup)
        if r['changed']:
            tag = '将改' if args.verify else ('已改' if r['modified'] else '未改')
            print(f"[{tag}] {fp.name}  空行 -{r['blanks_removed']}")
            total_removed += r['blanks_removed']
            if r['modified']:
                modified_files += 1
        else:
            print(f"[跳过] {fp.name}  无空行")

    print(f'\n总计：处理 {len(files)} 文件，修改 {modified_files}，共去除 {total_removed} 处空行')
    return 0


if __name__ == '__main__':
    sys.exit(main())
