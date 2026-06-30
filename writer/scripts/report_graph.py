#!/usr/bin/env python3
"""实体关系图谱生成 — 从正文+追踪文件提取角色关系 → 输出Mermaid格式。

用法：
    python report_graph.py <项目根>                                 # 全量图谱
    python report_graph.py <项目根> --main-only                      # 仅主角关系圈
    python report_graph.py <项目根> --ch 1 60                        # 仅该范围章节
    python report_graph.py <项目根> --output <文件>                   # 写入文件

⚠️ 项目适配：MAIN_CHARACTERS 字典需按项目修改角色名/别名/派系。
   本脚本为通用框架，硬编码的角色数据来自示例项目，使用前替换为当前项目角色。
"""

import re, os, sys, json, argparse
from collections import defaultdict, Counter
from pathlib import Path

# ── 默认角色字典（空，由项目配置覆盖）──
# 项目使用前需填充：{角色名: {"type": "主角", "faction": "主角方", "aliases": []}}
MAIN_CHARACTERS: dict = {}

# ── 关系动词检测规则 ──
RELATION_VERBS: dict = {}

def extract_characters_from_text(text, known_chars=None):
    """从文本中提取出现的角色"""
    chars = known_chars or MAIN_CHARACTERS
    found = {}
    for name, info in chars.items():
        # 搜索本名
        count = len(re.findall(re.escape(name), text))
        if count > 0:
            found[name] = count
        # 搜索别名
        for alias in info['aliases']:
            if len(alias) >= 2:  # 避免单字误匹配
                alias_count = len(re.findall(re.escape(alias), text))
                if alias_count > 0:
                    found[name] = found.get(name, 0) + alias_count
    return found


def extract_relationships(text, chars_found):
    """从文本中提取角色间关系"""
    relations = []
    char_names = list(chars_found.keys())

    # 1. 关系动词检测
    for rel_type, pattern in RELATION_VERBS.items():
        for match in re.finditer(pattern, text):
            pos = match.start()
            context = text[max(0, pos-30):pos+30]
            # 看上下文中有哪些角色名
            context_chars = [c for c in char_names if c in context]
            if len(context_chars) >= 2:
                # 取最近的两个
                for i in range(len(context_chars)):
                    for j in range(i+1, len(context_chars)):
                        relations.append((context_chars[i], context_chars[j], rel_type, context[:40]))

    # 2. co-occurrence（同一段落内同时出现）
    paragraphs = text.split('\n\n')
    for para in paragraphs:
        para_chars = [c for c in char_names if c in para]
        if len(para_chars) >= 2:
            for i in range(len(para_chars)):
                for j in range(i+1, len(para_chars)):
                    # 只记录同段落共现，增加一个通用关系权重
                    pass  # 在 aggregator 中处理共现

    return relations


def load_tracking_states(project_root):
    """从追踪文件读取角色状态"""
    states = {}
    for path in [
        os.path.join(project_root, 'tracking', 'current_state.md'),
        os.path.join(project_root, '追踪', '角色状态.md'),
    ]:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            # 提取角色名和状态
            for name in MAIN_CHARACTERS:
                if name in text:
                    states[name] = True
    return states


def load_from_fact_db(project_root):
    """如果 facts.db 存在，从中提取角色关系"""
    db_path = os.path.join(project_root, '.writer', 'facts.db')
    if not os.path.exists(db_path):
        return [], []
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # 关系里程碑
        rels = cur.execute(
            "SELECT character_a, character_b, stage, ch FROM relationship_milestones ORDER BY ch"
        ).fetchall()
        # 所有出现的角色
        chars = cur.execute(
            "SELECT DISTINCT character_name FROM character_states"
        ).fetchall()
        chars = [r[0] for r in chars]
        conn.close()
        return rels, chars
    except Exception:
        return [], []


def build_entity_graph(project_root, main_only=False, ch_start=None, ch_end=None):
    """构建实体关系图谱"""
    # 1. 从 facts.db 加载
    fact_rels, fact_chars = load_from_fact_db(project_root)
    if fact_chars:
        print(f"📦 从 facts.db 加载了 {len(fact_chars)} 个角色, {len(fact_rels)} 个关系", file=sys.stderr)

    # 2. 从正文文件扫描共现关系
    chapters_dir = None
    for d in [os.path.join(project_root, '正文'), os.path.join(project_root, 'chapters')]:
        if os.path.isdir(d):
            chapters_dir = d
            break

    if not chapters_dir:
        print("错误：未找到正文目录", file=sys.stderr)
        sys.exit(1)

    files = sorted([f for f in os.listdir(chapters_dir) if f.endswith('.md')])

    # 范围过滤
    if ch_start is not None:
        files = [f for f in files if
                 ch_start <= int(''.join(c for c in f if c.isdigit())) <= (ch_end or ch_start + 999)]

    # 角色出现次数统计
    char_freq = Counter()
    # 角色共现图
    cooccur = defaultdict(lambda: defaultdict(int))
    # 关系列表
    relation_list = []

    for f in files:
        fp = os.path.join(chapters_dir, f)
        with open(fp, 'r', encoding='utf-8') as fh:
            text = fh.read()

        chars = extract_characters_from_text(text)
        for name, count in chars.items():
            char_freq[name] += 1

        # 同章共现
        char_names = list(chars.keys())
        for i in range(len(char_names)):
            for j in range(i+1, len(char_names)):
                a, b = char_names[i], char_names[j]
                cooccur[a][b] += 1
                cooccur[b][a] += 1

        # 关系动词检测
        rels = extract_relationships(text, chars)
        relation_list.extend(rels)

    # 合并 facts.db 的关系
    for a, b, stage, ch in fact_rels:
        if a in MAIN_CHARACTERS and b in MAIN_CHARACTERS:
            # 这已经是一个明确的关系，给高权重
            if stage in ('confession', 'relationship', 'married'):
                relation_list.append((a, b, '恋人', f'ch{ch}: {stage}'))
            elif stage in ('close',):
                relation_list.append((a, b, '合作', f'ch{ch}: {stage}'))

    return char_freq, cooccur, relation_list, files


def generate_mermaid(char_freq, cooccur, relation_list, main_only=False):
    """生成 Mermaid classDiagram"""
    lines = []
    lines.append('```mermaid')
    lines.append('classDiagram')

    # 角色分类
    by_type = defaultdict(list)
    for name in char_freq:
        if name in MAIN_CHARACTERS:
            by_type[MAIN_CHARACTERS[name]['type']].append(name)
        else:
            by_type['其他'].append(name)

    if main_only:
        # 只保留主角 + 直接相关角色
        core = {'刘秋', '林芷琪', '季东海', '赵天龙', '周正阳', '方远', '赵凯', '韩主任'}
        for t in by_type:
            by_type[t] = [n for n in by_type[t] if n in core or char_freq[n] > 5]

    # 渲染角色节点
    type_labels = {
        '主角': '主角',
        '女主': '女主',
        '重要配角': '重要配角',
        '对抗→盟友': '对抗→盟友',
        '师长': '师长',
        '长辈': '长辈',
        '配角': '配角',
        '对抗': '对抗',
        '中立': '中立',
        '其他': '其他',
    }

    # class 定义（按 faction 着色和分组）
    faction_colors = {
        '主角方': '#e1f5fe',
        '转化方': '#fff3e0',
        '中立': '#f5f5f5',
        '敌对': '#ffebee',
    }

    for t, names in by_type.items():
        label = type_labels.get(t, t)
        if not names:
            continue
        lines.append(f'  class {label} {{')
        for name in names:
            freq = char_freq[name]
            faction = MAIN_CHARACTERS.get(name, {}).get('faction', '其他')
            color = faction_colors.get(faction, '#f5f5f5')
            lines.append(f'    +{name}[{name}]')
        lines.append('  }')

    # 关系边
    drawn_pairs = set()
    for a, b, rel_type, context in relation_list:
        if a not in char_freq or b not in char_freq:
            continue
        if main_only and a not in core and b not in core:
            continue
        pair = tuple(sorted([a, b]))
        if pair in drawn_pairs:
            continue
        drawn_pairs.add(pair)

        # 边风格
        if rel_type == '恋人':
            label = '💕 恋人'
        elif rel_type == '敌对':
            label = '⚔️ 敌对'
        elif rel_type == '师徒':
            label = '📚 师徒'
        elif rel_type == '合作':
            label = '🤝 合作'
        elif rel_type == '家人':
            label = '👨‍👩‍👧 家人'
        elif rel_type == '同事':
            label = '👥 同事'
        else:
            label = '—'

        lines.append(f'  {a} --> {b} : {label}')

    # 共现权重高的加隐含关系（共现 > 10 且无明确关系）
    cooccur_threshold = 10 if not main_only else 5
    for a in cooccur:
        for b in cooccur[a]:
            if a >= b:
                continue
            pair = tuple(sorted([a, b]))
            if pair in drawn_pairs:
                continue
            if main_only and a not in core and b not in core:
                continue
            if cooccur[a][b] >= cooccur_threshold:
                drawn_pairs.add(pair)
                lines.append(f'  {a} .. {b} : 共现{cooccur[a][b]}次')

    lines.append('```')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='实体关系图谱生成 — 从正文+追踪文件提取角色关系 → 输出Mermaid格式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('project_root', help='项目根目录')
    parser.add_argument('--main-only', action='store_true', help='仅主角关系圈')
    parser.add_argument('--ch', nargs=2, type=int, metavar=('START', 'END'), default=None,
                        help='章节范围')
    parser.add_argument('--output', metavar='FILE', help='写入文件')
    args = parser.parse_args()

    project_root = args.project_root
    main_only = args.main_only
    output_file = args.output
    ch_start = None
    ch_end = None

    if args.ch is not None:
        ch_start, ch_end = args.ch

    char_freq, cooccur, relation_list, files = build_entity_graph(
        project_root, main_only, ch_start, ch_end)

    print(f"📊 扫描 {len(files)} 章，发现 {len(char_freq)} 个角色",
          file=sys.stderr)

    mermaid = generate_mermaid(char_freq, cooccur, relation_list, main_only)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(mermaid)
        print(f"✅ 已写入 {output_file}", file=sys.stderr)
    else:
        print(mermaid)


if __name__ == '__main__':
    main()
