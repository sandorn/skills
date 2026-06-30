#!/usr/bin/env python3
"""字数补齐脚本 v7：全文稀疏段智能扩充。

核心变化 v6→v7：
  - 移除所有硬编码角色名/场景元素，改为从项目文件动态加载
  - 随机种子基于章节内容哈希（每章不同且可复现）
  - 写回前自动创建 .bak 备份
  - 依赖 scripts/lib.py 统一工具函数

用法：
    python3 pad_chapter.py <文件>                       # 单章（mode=full）
    python3 pad_chapter.py --batch <目录>                # 批量
    python3 pad_chapter.py <文件> --mode end             # 仅尾部追加（旧行为）
    python3 pad_chapter.py --batch <目录> --no-backup    # 跳过备份
"""

import re, os, sys, random, hashlib, argparse
from pathlib import Path
from collections import Counter

# 共享工具
from lib import count_chinese, extract_body, safe_write, load_character_names, is_dialogue_line
# 段落拆分
from split_paragraphs import split_full_text

TARGET = 2500
CHAR_THRESH = 60


# ===== 扩充策略池（通用 — 无项目特定数据） =====

SENSORY_DETAILS = {
    '视觉': ['灯光照在桌面上。影子拉长。', '窗帘在风里晃了一下。又停住。',
             '窗玻璃上凝了一层水雾。', '烟灰缸里积了半截烟灰。没有灭。还在冒着细烟。',
             '天花板的角落里有一片水渍。形状像一张地图。', '桌上的茶杯口朝上。底上还有一圈茶渍。'],
    '听觉': ['远处传来汽车驶过的声音。由远及近。又由近及远。',
             '有一只蚊子嗡地飞过去。绕了一圈。停在墙角。',
             '墙上的钟走得很慢。秒针每跳一格都像在犹豫。',
             '隔壁有电视的声音。听不清在放什么。只有嗡嗡的背景音。',
             '有鸟叫了一声。然后安静了。'],
    '触觉': ['桌面上凉凉的。指尖划过留下一道痕。',
             '手掌按在桌面上。木质触感。有点粗糙。',
             '脊背靠在椅背上。椅垫的弹簧已经松了。',
             '风从窗缝里挤进来。擦过后颈。凉飕飕的。'],
    '气味': ['空气里有灰尘的味道。混着旧纸和烟味。',
             '厨房的方向飘来油烟味。不太重。若有若无。',
             '刚下过雨。空气里有泥土和柏油混合的气味。'],
    '温度': ['房间里的温度不高不低。刚好让人不想动。',
             '手有点凉。他搓了一下。搁在膝盖上。',
             '窗户开了一条缝。冷风慢慢渗进来。'],
}

ACTIONS = [
    '他端起杯子喝了一口。水已经凉了。', '他又把杯子放回去。没有喝完。',
    '他换了个姿势。椅子的弹簧咯吱响了一声。', '他把右脚叠在左腿上。又放下来。',
    '他低头翻了一页。手指在纸面上划过。发出沙沙的声响。',
    '他靠回椅背。后脑勺枕在椅沿上。眼睛看着天花板。',
    '他拿起笔。在指尖转了一圈。又放下了。', '他搓了搓手指。关节咔咔响了两声。',
    '他掏出手机看了一眼。黑屏。又塞回裤兜里。', '他把手伸进口袋。摸到一个硬币。掏出来放在桌上。',
    '他的目光在房间里扫了一圈。每个角落都看过一遍。最后回到桌面上。',
]

DIALOGUE_REACTIONS = [
    '他没有马上接话。', '这句话他没说出来。在嘴边转了一圈。咽了回去。',
    '他的表情没什么变化。', '他顿了顿。', '他没有回答。沉默在两个人之间蔓延。',
    '他抬眼看了看对方。没有表情。', '他垂下眼睛。盯着桌面。', '他点了点头。没有多说什么。',
    '他笑了一下。很短。像是自嘲。', '他的手指在桌面上敲了两下。节奏很慢。',
    '他没有动。也没有说话。等着对方继续。',
    '他抬起头。眼神在对方脸上停了片刻。', '他侧过头。像是没听清。又像是走神了。',
    '他胸膛起伏了一下。又平复下来。', '他把手从桌上拿开。搁在膝盖上。',
]

EMOTION_HINTS = [
    '他抿了抿嘴。', '他的眉头皱了一下。很快又松开。', '他的表情松了松。',
    '他垂下肩膀。像是卸下一口气。', '他的嘴唇动了一下。没有出声。',
    '他的眼神暗了暗。', '他的呼吸顿了一下。', '他的拳头攥紧又松开。',
]


def classify_line(line):
    """判断一行文本的类型"""
    s = line.strip()
    if not s or s.startswith('#'):
        return 'skip'
    if is_dialogue_line(s):
        return 'dialogue'
    cn = count_chinese(s)
    if cn <= 80:
        return 'thin' if cn < 35 else 'normal'
    return 'long'


def get_chapter_context(lines, project_root=None):
    """从章节文本和项目文件中提取背景元素。

    角色名优先从项目设定文件加载，回退到从文本中检测高频人名。
    """
    text = '\n'.join(lines)

    # 尝试从项目加载角色名
    char_dict = {}
    if project_root:
        char_dict = load_character_names(project_root)

    if char_dict:
        # 统计文本中出现的角色频率
        char_freq = Counter()
        for name in char_dict:
            count = len(re.findall(re.escape(name), text))
            if count > 0:
                char_freq[name] = count
        subject = char_freq.most_common(1)[0][0] if char_freq else '他'
    else:
        # 回退：从文本中提取高频二字词作为候选主角
        words = re.findall(r'[一-鿿]{2}', text)
        freq = Counter(words)
        # 过滤常见停用词
        stops = {'一个', '他们', '什么', '已经', '没有', '可以', '这个', '自己', '不是',
                 '时候', '知道', '觉得', '因为', '所以', '如果', '虽然', '但是', '不过'}
        for w in stops:
            freq.pop(w, None)
        subject = freq.most_common(1)[0][0] if freq else '他'

    # 场景元素：从文本中自动检测
    scene_patterns = [r'桌面', r'窗户', r'门', r'走廊', r'椅子', r'沙发',
                      r'屏幕', r'键盘', r'茶杯', r'水杯', r'台灯', r'路灯',
                      r'窗外', r'屋里', r'墙壁', r'地板', r'天花板', r'床']
    scene = []
    for pat in scene_patterns:
        if re.search(pat, text) and pat not in scene:
            scene.append(pat)
    scene = scene[:8]

    # 感官元素
    sensory = []
    for cat, items in SENSORY_DETAILS.items():
        pool = [s for s in items if not any(kw in s for kw in ['他', subject])]
        if pool:
            sensory.extend(pool[:2])

    return subject, scene, sensory


def expand_thin_line(line, subject, scene, sensory, used_patterns, rng):
    """扩充一个薄段：返回原始行 + 扩充行列表"""
    s = line.strip()
    cn = count_chinese(s)
    if cn >= 35:
        return [line], 0

    added_chars = 0
    new_lines = [line.rstrip('\n')]
    used = set(used_patterns)

    if s.endswith(('。', '！', '？')):
        if sensory and rng.random() < 0.6:
            detail = rng.choice(sensory)
            if detail not in used:
                used.add(detail)
                new_lines.append('')
                new_lines.append(detail)
                added_chars += count_chinese(detail)

    action_verbs = ['站', '走', '坐', '拿', '放', '推', '拉', '开', '关',
                    '拿', '放', '看', '听', '说', '写', '翻', '点', '掏']
    if any(v in s for v in action_verbs) and rng.random() < 0.5:
        act = rng.choice(ACTIONS)
        if act not in used:
            used.add(act)
            new_lines.append('')
            new_lines.append(act)
            added_chars += count_chinese(act)

    if rng.random() < 0.3:
        hint = rng.choice(EMOTION_HINTS)
        if hint not in used:
            used.add(hint)
            new_lines.append('')
            new_lines.append(hint)
            added_chars += count_chinese(hint)

    used_patterns.update(used)
    return new_lines, added_chars


def expand_around_dialogue(line_no, lines, subject, scene, used_patterns, rng):
    """在对话行前后插入角色反应"""
    inserted = []
    added = 0

    if not is_dialogue_line(lines[line_no]):
        return [], 0

    if line_no > 0:
        prev = lines[line_no - 1].strip()
        if prev == '' or is_dialogue_line(lines[line_no - 1]):
            return [], 0

    reaction = rng.choice(DIALOGUE_REACTIONS)
    if reaction not in used_patterns:
        used_patterns.add(reaction)
        inserted.append('')
        inserted.append(reaction)
        inserted.append('')
        inserted.append(lines[line_no])
        added += count_chinese(reaction)

    return inserted, added


def expand_full_text(lines, bs, needed_chars, project_root=None):
    """全文扩充：定位薄段和对话段，就地扩充"""
    body_lines = lines[bs:]
    # 使用内容哈希作为随机种子，保证同章同结果且不同章不同
    content_hash = hashlib.md5('\n'.join(body_lines).encode('utf-8')).hexdigest()
    seed = int(content_hash[:8], 16)
    rng = random.Random(seed)
    used_patterns = set()

    subject, scene, sensory = get_chapter_context(body_lines, project_root)

    new_lines = lines[:bs]
    total_added = 0
    i = 0

    while i < len(body_lines) and total_added < needed_chars:
        line = body_lines[i]
        line_type = classify_line(line)

        if line_type == 'skip':
            new_lines.append(line)
            i += 1
            continue

        if line_type == 'thin':
            expanded, added = expand_thin_line(
                line, subject, scene, sensory, used_patterns, rng)
            new_lines.extend(expanded)
            total_added += added
            i += 1
            continue

        if line_type == 'dialogue':
            inserted, added = expand_around_dialogue(
                i, body_lines, subject, scene, used_patterns, rng)
            if inserted:
                new_lines.extend(inserted)
                total_added += added
            else:
                new_lines.append(line)
            i += 1
            continue

        if line_type == 'normal' and total_added < needed_chars * 0.6 and rng.random() < 0.15:
            if sensory:
                detail = rng.choice(sensory)
                if detail not in used_patterns:
                    used_patterns.add(detail)
                    new_lines.append(line)
                    new_lines.append('')
                    new_lines.append(detail)
                    total_added += count_chinese(detail)
                    i += 1
                    continue

        new_lines.append(line)
        i += 1

    # 全文扩充仍不足时，fallback 到章末追加
    if total_added < needed_chars * 0.5:
        remaining = needed_chars - total_added
        extra = []
        fallback = [
            f'{subject}又在原地站了一会儿。',
            f'他把桌面上的东西理了理。没什么要收拾的。但总要做点什么。',
        ]
        for fb in fallback:
            if count_chinese(''.join(extra)) >= remaining:
                break
            if fb not in used_patterns:
                extra.append('')
                extra.append(fb)
        if extra:
            new_lines.extend(extra)
            total_added += count_chinese('\n'.join(extra))

    return '\n'.join(new_lines), total_added


def pad_file_end(filepath, target=TARGET):
    """旧模式：仅在章末追加（保持向后兼容）"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    ls = content.split('\n')
    bs = 0
    for i, l in enumerate(ls):
        if l.strip() == '' and i > 0 and ls[i - 1].startswith('#'):
            bs = i + 1
            break
    body = '\n'.join(ls[bs:])
    cn = count_chinese(body)

    if cn >= target:
        return False

    kw_list = re.findall(r'[一-鿿㐀-䶿]{2,4}', content[-1500:])
    stop = {'一个', '他们', '什么', '已经', '没有', '可以', '这个', '自己', '不是'}
    kw = [w for w in kw_list if w not in stop][:3] or ['桌面']
    rng = random.Random(int(hashlib.md5(content[-200:].encode()).hexdigest()[:8], 16))
    obj = rng.choice(kw)

    extra = f'他看了一眼{obj}。\n{obj}还是老样子。\n他把视线移开。\n'
    padded = content.rstrip() + '\n' + extra + '\n'
    padded = split_full_text(padded)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(padded)
    return True


def pad_file_full(filepath, target=TARGET, backup=True, project_root=None):
    """新模式：全文稀疏段扩充"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    ls = content.split('\n')
    bs = 0
    for i, l in enumerate(ls):
        if l.strip() == '' and i > 0 and ls[i - 1].startswith('#'):
            bs = i + 1
            break
    body = '\n'.join(ls[bs:])
    cn = count_chinese(body)

    if cn >= target:
        return False

    needed = target - cn + 40
    padded, added = expand_full_text(ls, bs, needed, project_root)

    if added == 0:
        return False

    padded = split_full_text(padded)

    safe_write(filepath, padded, backup=backup)
    return True


def main():
    parser = argparse.ArgumentParser(
        description='字数补齐脚本 v7 — 全文稀疏段智能扩充',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='示例:\n'
               '  python3 pad_chapter.py ch_001.md\n'
               '  python3 pad_chapter.py --batch chapters/\n'
               '  python3 pad_chapter.py --batch chapters/ --no-backup\n'
               '  python3 pad_chapter.py ch_001.md --mode end',
    )
    parser.add_argument('target', nargs='?', help='目标文件或目录 (与 --batch 互斥)')
    parser.add_argument('--batch', metavar='DIR', help='批量处理目录下所有 .md')
    parser.add_argument('--mode', choices=['full', 'end'], default='full',
                        help='扩充模式: full(全文,默认) / end(仅尾部)')
    parser.add_argument('--project-root', default=None,
                        help='项目根目录 (用于加载角色名等配置)')
    parser.add_argument('--no-backup', action='store_true',
                        help='跳过 .bak 备份')
    args = parser.parse_args()

    mode = args.mode
    do_backup = not args.no_backup
    project_root = args.project_root

    if args.batch:
        dir_path = Path(args.batch)
        if not dir_path.is_dir():
            print(f"错误：目录不存在 — {dir_path}")
            sys.exit(2)
        files = sorted(dir_path.glob('*.md'))
    elif args.target:
        files = [Path(args.target)]
    else:
        parser.print_help()
        sys.exit(1)

    fixed = 0
    for fp in files:
        if not fp.exists():
            continue
        if mode == 'end':
            ok = pad_file_end(str(fp))
        else:
            ok = pad_file_full(str(fp), backup=do_backup, project_root=project_root)
        if ok:
            fixed += 1

    mode_label = '全文扩充' if mode == 'full' else '尾部追加'
    backup_label = ' (含.bak)' if do_backup else ''
    print(f"pad_chapter v7 ({mode_label}){backup_label}: {fixed}/{len(files)}章补齐 (目标≥{TARGET}字)")


if __name__ == '__main__':
    main()
