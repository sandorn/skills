# -*- coding: utf-8 -*-
"""制度 docx 正文抽取器（段落 + 表格），供版本比对/审查使用。

用法：
    uv run --with python-docx python docx_text.py <file.docx> > out.txt
    diff -u old.txt new.txt

要点：
- 段落与表格按文档流顺序输出，表格行前缀【T】，单元格以 " | " 分隔；
- 纵向合并单元格在行内去重，避免同一段文字重复输出；
- 输出 UTF-8，Windows 下用 `sed 's/^[0-9]*\t//'` 去掉行号后再 diff。
"""
import sys

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph


def iter_block_items(parent):
    body = parent.element.body
    for child in body.iterchildren():
        if child.tag == qn('w:p'):
            yield Paragraph(child, parent)
        elif child.tag == qn('w:tbl'):
            yield Table(child, parent)


def dump(path):
    doc = Document(path)
    out = []
    for blk in iter_block_items(doc):
        if isinstance(blk, Paragraph):
            t = blk.text.strip()
            if t:
                out.append(t)
        else:
            for row in blk.rows:
                cells, seen = [], set()
                for c in row.cells:
                    if id(c._tc) in seen:
                        continue
                    seen.add(id(c._tc))
                    cells.append(c.text.strip().replace('\n', ' '))
                line = ' | '.join(cells)
                if line.strip(' |'):
                    out.append('【T】' + line)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    for i, line in enumerate(dump(sys.argv[1]), 1):
        print(f'{i}\t{line}')
