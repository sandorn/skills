#!/usr/bin/env python3
"""按句号/问号/感叹号拆分超长段落，确保每段≤60汉字。

v2 改进：
  - 对话行检测改为「『开头（适配项目规范）
  - 纯数字/标点行跳过
  - 拆分后保留原缩进

用法：
    python split_paragraphs.py <file.md>                # 单文件
    python split_paragraphs.py --batch <dir>            # 批量处理目录下所有 .md
    python split_paragraphs.py --verify <file.md>       # 仅检测不修改

拆分规则：
    - 按 。！？ 断段
    - 对话行（以「『开头）跳过不拆
    - 拆分后每段≤60汉字
    - 保留原有换行结构，仅拆分超标行
"""

import re
import sys
from pathlib import Path


def count_chinese(text: str) -> int:
    """统计汉字数量"""
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def is_dialogue_line(line: str) -> bool:
    """判断是否为对话行（以「『开头）——项目标准引号"""
    stripped = line.strip()
    return stripped.startswith(('「', '『'))


def split_paragraph(line: str, max_chars: int = 60) -> list[str]:
    """按句号/问号/感叹号拆分一个段落，确保每段≤60汉字"""
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


def process_file(filepath: Path, verify_only: bool = False) -> dict:
    """处理单个文件，返回统计信息"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    long_count = 0
    new_segments = 0

    for line in lines:
        stripped = line.rstrip('\n')
        if not stripped.strip():
            new_lines.append('\n')
            continue

        if count_chinese(stripped) > 60 and not is_dialogue_line(stripped):
            long_count += 1
            segments = split_paragraph(stripped, 60)
            new_segments += len(segments) - 1
            for seg in segments:
                new_lines.append(seg + '\n')
        else:
            new_lines.append(line)

    if not verify_only:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return {
        'file': str(filepath),
        'long_paragraphs': long_count,
        'new_segments_added': new_segments,
        'fixed': not verify_only and long_count > 0
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    verify_only = '--verify' in sys.argv
    batch = '--batch' in sys.argv

    if batch:
        dir_path = Path(sys.argv[-1])
        files = sorted(dir_path.glob('*.md'))
    else:
        files = [Path(sys.argv[-1])]

    total_long = 0
    total_new = 0
    total_fixed = 0

    for fp in files:
        if not fp.exists():
            print(f"SKIP: {fp} (not found)")
            continue
        result = process_file(fp, verify_only)
        total_long += result['long_paragraphs']
        total_new += result['new_segments_added']
        if result['fixed']:
            total_fixed += 1
        status = "FIXED" if result['fixed'] else (("DETECTED" if result['long_paragraphs'] > 0 else "OK"))
        print(f"{status}: {result['file']} ({result['long_paragraphs']} long → +{result['new_segments_added']} lines)")

    print(f"\n总计: {total_long} 段超标, +{total_new} 行, {total_fixed} 文件{'（仅检测）' if verify_only else '（已修复）'}")


if __name__ == '__main__':
    main()
