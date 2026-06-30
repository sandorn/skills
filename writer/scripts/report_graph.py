#!/usr/bin/env python3
# SAFETY: READONLY — 只读分析+图谱生成，不修改任何源文件。安全。
"""实体关系图谱生成 — 从正文+追踪文件提取角色关系 → 输出Mermaid格式。

用法：
    python report_graph.py <项目根>                                 # 全量图谱
    python report_graph.py <项目根> --main-only                      # 仅主角关系圈
    python report_graph.py <项目根> --ch 1 60                        # 仅该范围章节
    python report_graph.py <项目根> --output <文件>                   # 写入文件

项目适配：角色名从 setting/characters.md 或 writer.json 自动加载。
若都未配置，脚本会从正文中自动检测高频人名（至少出现3次以上的角色）。
"""

import re, os, sys, json, argparse
from collections import defaultdict, Counter
from pathlib import Path

from lib import (count_chinese, find_chapters_dir, scan_chapter_files,
                 load_writer_json, load_character_names)


# ── 关系动词检测规则（通用，不绑定特定项目）──
RELATION_VERBS = {
    '师徒': r'(?:师父|徒弟|师傅|弟子|老师|学生|教导|传授|拜师)',
    '敌对': r'(?:敌人|死对头|不共戴天|势不两立|仇人|对手|针对|较量)',
    '恋人': r'(?:喜欢|爱|心动|心动|表白|在一起|确定关系|女朋友|男朋友)',
    '家人': r'(?:父亲|母亲|爸爸|妈妈|儿子|女儿|兄弟|姐妹|哥哥|弟弟|姐姐|妹妹|叔叔|阿姨)',
    '合作': r'(?:合作|联手|结盟|联盟|合伙|搭档|伙伴)',
    '同事': r'(?:同事|同僚|上下级|老板|下属|汇报)',
    '朋友': r'(?:朋友|兄弟|闺蜜|哥们|铁子|老铁|熟人)',
}


def extract_characters_from_text(text, known_chars=None):
    """从文本中提取出现的角色名及其出现次数。"""
    chars = known_chars or {}
    found = {}
    for name, info in chars.items():
        count = len(re.findall(re.escape(name), text))
        if count > 0:
            found[name] = count
        for alias in info.get('aliases', []):
            if len(alias) >= 2:
                alias_count = len(re.findall(re.escape(alias), text))
                if alias_count > 0:
                    found[name] = found.get(name, 0) + alias_count
    return found


def detect_characters_from_text(text, min_occurrences=3):
    """从文本中自动检测人名（2-3字高频词汇，启发式）。

    用于没有配置角色文件的项目。返回 {name: info} 格式的字典。
    """
    # 提取所有 2-3 字中文组合
    candidates_2 = re.findall(r'[一-鿿]{2}', text)
    candidates_3 = re.findall(r'[一-鿿]{3}', text)

    # 过滤常见非人名词汇
    stops = {'一个', '他们', '什么', '已经', '没有', '可以', '这个', '自己',
             '不是', '时候', '知道', '觉得', '因为', '所以', '如果', '虽然',
             '但是', '不过', '然后', '还是', '只是', '一定', '一样', '可能',
             '那些', '这些', '那个', '那个', '起来', '下来', '过来', '过去',
             '怎么', '为什么', '怎么办', '怎么样', '越来越', '是不是',
             '房间里', '办公室', '会议室', '看了看', '想了想', '笑了笑',
             '一瞬间', '突然', '忽然', '似乎', '仿佛'}

    freq = Counter()
    for w in candidates_2:
        if w not in stops:
            freq[w] += 1
    for w in candidates_3:
        if w not in stops:
            freq[w] += 0.5  # 三字词加权

    # 取出现次数 >= min_occurrences 的词作为候选角色名
    chars = {}
    for name, count in freq.most_common(30):
        if count < min_occurrences:
            break
        chars[name] = {'type': '自动检测', 'faction': '未知', 'aliases': []}

    return chars


def extract_relationships(text, chars_found):
    """从文本中提取角色间关系。"""
    relations = []
    char_names = list(chars_found.keys())

    for rel_type, pattern in RELATION_VERBS.items():
        for match in re.finditer(pattern, text):
            pos = match.start()
            context = text[max(0, pos - 30):pos + 80]
            context_chars = [c for c in char_names if c in context]
            if len(context_chars) >= 1:
                for i in range(len(context_chars)):
                    for j in range(i + 1, len(context_chars)):
                        relations.append(
                            (context_chars[i], context_chars[j], rel_type,
                             context[:60]))

    return relations


def load_tracking_states(project_root, char_dict):
    """从追踪文件读取角色状态。"""
    states = {}
    for path in [
        os.path.join(project_root, 'tracking', 'current_state.md'),
        os.path.join(project_root, '追踪', '角色状态.md'),
    ]:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            for name in char_dict:
                if name in text:
                    states[name] = True
    return states


def load_from_fact_db(project_root):
    """如果 facts.db 存在，从中提取角色关系。"""
    db_path = os.path.join(project_root, '.writer', 'facts.db')
    if not os.path.exists(db_path):
        return [], []
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        rels = cur.execute(
            "SELECT character_a, character_b, stage, ch FROM relationship_milestones ORDER BY ch"
        ).fetchall()
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
    # 1. 加载角色字典
    char_dict = load_character_names(project_root)

    # 2. 从 facts.db 加载
    fact_rels, fact_chars = load_from_fact_db(project_root)

    # 3. 从正文扫描
    chapters_dir = find_chapters_dir(project_root)
    if not chapters_dir:
        print("错误：未找到正文目录", file=sys.stderr)
        sys.exit(1)

    files = scan_chapter_files(chapters_dir, ch_start, ch_end)

    # 如果没有配置角色名，先扫描全部文本自动检测
    if not char_dict:
        print("ℹ️  未检测到项目角色配置，从正文中自动检测高频人名...", file=sys.stderr)
        sample_text = ''
        for f in files[:20]:  # 采样前20章
            fp = os.path.join(chapters_dir, f)
            try:
                with open(fp, 'r', encoding='utf-8') as fh:
                    sample_text += fh.read()[:5000]
            except Exception:
                pass
        char_dict = detect_characters_from_text(sample_text, min_occurrences=3)
        if char_dict:
            print(f"   自动检测到 {len(char_dict)} 个候选角色", file=sys.stderr)
        else:
            print("   未检测到足够高频的人名，图谱可能为空", file=sys.stderr)

    # 4. 更新：合并 facts.db 中的角色
    for name in fact_chars:
        if name not in char_dict and len(name) >= 2:
            char_dict[name] = {'type': '其他', 'faction': '未知', 'aliases': []}

    # 5. 逐章扫描
    char_freq = Counter()
    cooccur = defaultdict(lambda: defaultdict(int))
    relation_list = []

    for f in files:
        fp = os.path.join(chapters_dir, f)
        try:
            with open(fp, 'r', encoding='utf-8') as fh:
                text = fh.read()
        except Exception:
            continue

        chars = extract_characters_from_text(text, char_dict)
        for name, count in chars.items():
            char_freq[name] += 1

        char_names = list(chars.keys())
        for i in range(len(char_names)):
            for j in range(i + 1, len(char_names)):
                a, b = char_names[i], char_names[j]
                cooccur[a][b] += 1
                cooccur[b][a] += 1

        rels = extract_relationships(text, chars)
        relation_list.extend(rels)

    # 6. 合并 facts.db 的关系
    for a, b, stage, ch in fact_rels:
        if a in char_dict or b in char_dict:
            # 确保双方都在 char_dict 中
            for name in (a, b):
                if name not in char_dict and len(name) >= 2:
                    char_dict[name] = {'type': '其他', 'faction': '未知', 'aliases': []}
            if stage in ('confession', 'relationship', 'married'):
                relation_list.append((a, b, '恋人', f'ch{ch}: {stage}'))
            elif stage in ('close',):
                relation_list.append((a, b, '合作', f'ch{ch}: {stage}'))

    return char_freq, cooccur, relation_list, files, char_dict


def generate_mermaid(char_freq, cooccur, relation_list, char_dict,
                     main_only=False):
    """生成 Mermaid classDiagram"""
    lines = []
    lines.append('```mermaid')
    lines.append('classDiagram')

    if not char_freq:
        lines.append('  %% 无角色数据 — 请配置 setting/characters.md')
        lines.append('```')
        return '\n'.join(lines)

    # 角色分类
    by_type = defaultdict(list)
    for name in char_freq:
        info = char_dict.get(name, {})
        by_type[info.get('type', '其他')].append(name)

    if main_only:
        core = {n for n in char_freq if char_freq[n] > 3}

    type_labels = {
        '主角': '主角', '女主': '女主',
        '重要配角': '重要配角', '对抗→盟友': '对抗→盟友',
        '师长': '师长', '长辈': '长辈',
        '配角': '配角', '对抗': '对抗', '中立': '中立',
        '其他': '其他', '自动检测': '自动检测',
    }

    faction_colors = {
        '主角方': '#e1f5fe', '转化方': '#fff3e0',
        '中立': '#f5f5f5', '敌对': '#ffebee',
        '未知': '#fafafa',
    }

    for t, names in by_type.items():
        label = type_labels.get(t, t)
        if not names:
            continue
        lines.append(f'  class {label} {{')
        for name in names:
            freq = char_freq[name]
            faction = char_dict.get(name, {}).get('faction', '未知')
            color = faction_colors.get(faction, '#f5f5f5')
            lines.append(f'    +{name}[{name}]')
        lines.append('  }')

    # 关系边
    drawn_pairs = set()
    for a, b, rel_type, context in relation_list:
        if a not in char_freq or b not in char_freq:
            continue
        pair = tuple(sorted([a, b]))
        if pair in drawn_pairs:
            continue
        drawn_pairs.add(pair)

        edge_styles = {
            '恋人': '💕 恋人', '敌对': '⚔️ 敌对',
            '师徒': '📚 师徒', '合作': '🤝 合作',
            '家人': '👨‍👩‍👧 家人', '同事': '👥 同事',
            '朋友': '👤 朋友',
        }
        label = edge_styles.get(rel_type, '—')
        lines.append(f'  {a} --> {b} : {label}')

    # 共现权重高的加隐含关系
    cooccur_threshold = 10 if not main_only else 5
    for a in cooccur:
        for b in cooccur[a]:
            if a >= b:
                continue
            pair = tuple(sorted([a, b]))
            if pair in drawn_pairs:
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
        epilog='示例:\n'
               '  python report_graph.py .\n'
               '  python report_graph.py . --main-only\n'
               '  python report_graph.py . --ch 1 60 --output graph.md',
    )
    parser.add_argument('project_root', help='项目根目录')
    parser.add_argument('--main-only', action='store_true', help='仅主角关系圈')
    parser.add_argument('--ch', nargs=2, type=int, metavar=('START', 'END'),
                        default=None, help='章节范围')
    parser.add_argument('--output', metavar='FILE', help='写入文件')
    args = parser.parse_args()

    project_root = args.project_root
    main_only = args.main_only
    output_file = args.output
    ch_start, ch_end = args.ch if args.ch else (None, None)

    char_freq, cooccur, relation_list, files, char_dict = build_entity_graph(
        project_root, main_only, ch_start, ch_end)

    print(f"📊 扫描 {len(files)} 章，发现 {len(char_freq)} 个角色",
          file=sys.stderr)

    mermaid = generate_mermaid(char_freq, cooccur, relation_list, char_dict,
                               main_only)

    if output_file:
        safe_write(output_file, mermaid, backup=False)
        print(f"✅ 已写入 {output_file}", file=sys.stderr)
    else:
        print(mermaid)


if __name__ == '__main__':
    main()
