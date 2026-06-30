#!/usr/bin/env python3
"""追读力分析脚本 — 钩子强度 + 爽点分布 + 节奏间隔

从正文文件中提取量化指标，输出逐章和聚合报告。

用法：
    python analyze_hook.py <chapters目录>                  # 全部章节
    python analyze_hook.py <chapters目录> 1 60             # ch01-ch60

输出维度：
  1. 钩子强度（章末500字）：悬念密度 / 未完成动作 / 情绪爆发 / 信息落差
  2. 爽点分布：每5章区间内的爽点密度和类型
  3. 钩子间隔：连续钩子之间的章节数
  4. 钩子退化检测：连续3章钩子强度下降 → 标记警
"""

import re, os, sys, json, argparse
from collections import Counter
from pathlib import Path


def count_chinese(text):
    return len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text))


# ===========================
# 钩子检测
# ===========================

HOOK_PATTERNS = {
    '突然揭示': [
        r'(?:原来|竟是|竟然|没想到|怎么可能|怎么会)(?:是|有|在|这)',
        r'(?:真相|秘密|底牌|身份|真面目)',
        r'他(?:看见|听到|发现|注意到|意识到)(?:了|到)',
    ],
    '紧急危机': [
        r'(?:糟了|不好|危险|出事了|大事不好|完了)',
        r'(?:冲进|破门|突然|猛地|骤然)(?:推|撞|闯)',
        r'(?:警报|尖叫|枪声|爆炸|惨叫)',
    ],
    '未完成动作': [
        r'(?:手停|脚步一顿|停了下来|停在半空)',
        r'(?:欲言又止|张了张嘴|到嘴边)(?:又|的话)',
        r'(?:然后|接下来|下一步|明天)(?:会|再|才)',
        r'\.{2,}(?:[。！？]?\s*)$',  # 省略号结尾
    ],
    '身份反转': [
        r'(?:你就是|你是|原来你是|没想到你是)(?:那个|那位)',
        r'(?:他|她)竟然是(?:.*?)('
        r'刘秋|林芷琪|季东海|赵天龙|周正阳|韩主任|魏之明|老周)',
    ],
    '两难抉择': [
        r'(?:要么|要么就|只能选|只能|必须)(?:一个|一样|其一|做出选择)',
        r'(?:选|保|救)(?:哪个|哪一个|谁|哪一个)',
        r'(?:两难|抉择|取舍|难以取舍)',
    ],
    '神秘线索': [
        r'(?:神秘|奇怪|古怪|异常|不对劲|诡异)',
        r'(?:线索|痕迹|痕迹|印记|暗号|标记)',
        r'(?:迷|疑|问题|疑问)(?:还|仍未|仍然)',
    ],
    '倒计时': [
        r'(?:只剩|还剩下|只有.{1,5}(?:时间|天|小时|分钟|秒))',
        r'(?:倒计时|计时|倒数的)',
        r'(?:必须在|必须赶在|赶在.{1,10}(?:之前|前))',
    ],
    '承诺/威胁': [
        r'(?:我会|我保证|我一定|我发誓)(?:.*?)(?:找到|回来|做到|搞定)',
        r'(?:你等着|走着瞧|你给我等着|这事没完)',
        r'(?:后果自负|你一定会后悔|会付出代价)',
    ],
    '离奇消失': [
        r'(?:不见了|消失了|凭空|不见了踪影|人间蒸发)',
        r'(?:空空如也|空荡荡|什么也没有|没有任何痕迹)',
    ],
    '意象钩子': [
        r'(?:风|雨|雪|月光|路灯|影子|暗)(?:.*?)(?:吹|下|落|拉长|晃动|移动)',
        r'(?:夜色|黄昏|黎明|黑暗|灯火)(?:.*?)(?:深|浓|降临|亮起|熄灭)',
    ],
    '留白钩子': [
        r'\.{3,}$',  # 省略号结尾
        r'(?:……|—{2,})$',  # 中文省略号或破折号结尾（虽然正文禁止破折号，但可能是被漏掉的）
        r'^(?:也许|或许|大概|可能)(?:.*?)$',  # 以模糊词开头的段落
    ],
}

# 爽点关键词
SHUANG_KEYWORDS = {
    '升级': r'(?:升到|突破|晋级|进阶|达到了|跨入|踏入)(?:\d+)级',
    '打脸': r'(?:打脸|懵了|愣住|傻眼|不可置信|目瞪口呆|哑口无言)',
    '暴富': r'(?:赚了|挣了|进账|收益|利润|纯利|净赚|到手)(?:\d+)',
    '智谋': r'(?:早就|提前|早有预料|将计就计|反将一军|瓮中捉鳖)',
    '情感': r'(?:确定了关系|在一起|答应|表白|告白|承诺)',
    '装备': r'(?:获得了|得到了|爆出|掉落|拿到了|入手了)(?:.*?)(?:装备|武器|戒指|项链)',
    '势力': r'(?:加入|收编|收服|联盟|结盟|投靠|归顺)',
    '逆转': r'(?:反转|绝地|逆转|翻盘|起死回生|反败为胜)',
}


def detect_hooks(text, last_n_chars=500):
    """检测章末区域的钩子类型和强度"""
    ending = text[-last_n_chars:]
    hooks_found = {}
    total_strength = 0

    for htype, patterns in HOOK_PATTERNS.items():
        hits = 0
        for pat in patterns:
            matches = re.findall(pat, ending)
            hits += len(matches)
        if hits > 0:
            hooks_found[htype] = hits
            total_strength += hits

    # 归一化强度（0-10）
    strength = min(10, total_strength)
    return hooks_found, strength


def detect_shuang(text):
    """检测章节中的爽点"""
    shuang = {}
    total = 0
    for stype, pattern in SHUANG_KEYWORDS.items():
        matches = re.findall(pattern, text)
        if matches:
            shuang[stype] = len(matches)
            total += len(matches)
    return shuang, total


def analyze_chapter(filepath):
    """分析单章"""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # 跳过标题行
    lines = text.split('\n')
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip() == '' and i > 0 and lines[i-1].startswith('#'):
            body_start = i + 1
            break
    body = '\n'.join(lines[body_start:])
    cn = count_chinese(body)

    hooks, hook_strength = detect_hooks(body)
    shuang, shuang_count = detect_shuang(body)

    # 章末句完整性检测
    last_sentence = ''
    for line in reversed(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            last_sentence = stripped
            break

    is_truncated = False
    if last_sentence:
        # 末句不应以「了」「的」「是」结尾且无句号
        ends_incomplete = not re.search(r'[。！？」』\u2026]$', last_sentence)
        if ends_incomplete and len(last_sentence) < 20:
            is_truncated = True

    return {
        'cn_chars': cn,
        'hook_types': hooks,
        'hook_strength': hook_strength,
        'shuang_types': shuang,
        'shuang_count': shuang_count,
        'is_truncated': is_truncated,
        'last_sentence': last_sentence[:60],
    }


def main():
    parser = argparse.ArgumentParser(
        description='追读力分析脚本 — 钩子强度 + 爽点分布 + 节奏间隔',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('target', help='chapters目录')
    parser.add_argument('start', nargs='?', type=int, default=None, help='起始章节号')
    parser.add_argument('end', nargs='?', type=int, default=None, help='结束章节号')
    parser.add_argument('--ch', nargs=2, type=int, metavar=('START', 'END'), default=None,
                        help='章节范围 (替代位置参数)')
    args = parser.parse_args()

    target = args.target

    if not os.path.isdir(target):
        print(f"错误：{target} 不是目录")
        sys.exit(2)

    files = sorted([f for f in os.listdir(target) if f.endswith('.md')])

    # 范围过滤
    if args.ch is not None:
        ch_start, ch_end = args.ch
    else:
        ch_start = args.start
        ch_end = args.end

    if ch_start is not None:
        files = [f for f in files if
                 ch_start <= int(''.join(c for c in f if c.isdigit())) <= (ch_end or ch_start + 999)]

    results = []
    total_hook_strength = 0
    total_shuang = 0
    hook_strength_history = []
    shuang_history = []

    for f in files:
        fp = os.path.join(target, f)
        result = analyze_chapter(fp)
        results.append((f, result))
        total_hook_strength += result['hook_strength']
        total_shuang += result['shuang_count']
        hook_strength_history.append(result['hook_strength'])
        shuang_history.append(result['shuang_count'])

    n = len(results)
    if n == 0:
        print("无章节可分析")
        sys.exit(1)

    # ===== 输出 =====
    print("=" * 70)
    print(f"追读力分析报告 (共 {n} 章)")
    print("=" * 70)
    print()

    # 1. 逐章明细
    print(f"{'章节':<25} {'字数':>5} {'钩力':>3} {'爽点':>3} {'截断':>4} {'钩子类型'}")
    print("-" * 70)
    for f, r in results:
        ch_num = ''.join(c for c in f if c.isdigit())
        hook_types_str = ','.join(r['hook_types'].keys())[:30]
        trunc_sym = "⚠️" if r['is_truncated'] else "  "
        print(f"{f:<25} {r['cn_chars']:>5} {r['hook_strength']:>3} "
              f"{r['shuang_count']:>3} {trunc_sym:>4} {hook_types_str}")

    # 2. 聚合指标
    print()
    print("-" * 70)
    print("聚合指标")
    print("-" * 70)

    avg_hook = total_hook_strength / n
    avg_shuang = total_shuang / n
    print(f"平均钩子强度: {avg_hook:.2f}/10")
    print(f"平均爽点数: {avg_shuang:.2f}/章")
    print(f"截断末句: {sum(1 for _, r in results if r['is_truncated'])}/{n} 章")
    print()

    # 3. 钩子退化检测（连续3章钩子强度下降）
    print("-" * 70)
    print("钩力衰减预警")
    print("-" * 70)
    degradation_count = 0
    for i in range(2, n):
        if (hook_strength_history[i-2] > hook_strength_history[i-1] >
                hook_strength_history[i]):
            degradation_count += 1
            f = results[i][0]
            print(f"⚠️  {results[i-2][0]}→{results[i-1][0]}→{f}: "
                  f"{hook_strength_history[i-2]}→{hook_strength_history[i-1]}→{hook_strength_history[i]}")

    if degradation_count == 0:
        print(f"✅ 无连续3章钩力下降")

    # 4. 5章区间爽点分布
    print()
    print("-" * 70)
    print("5章区间爽点分布")
    print("-" * 70)
    interval = 5
    for i in range(0, n, interval):
        chunk = results[i:i+interval]
        total_s = sum(r[1]['shuang_count'] for r in chunk)
        avg_s = total_s / len(chunk) if chunk else 0
        f_start = ''.join(c for c in chunk[0][0] if c.isdigit())
        f_end = ''.join(c for c in chunk[-1][0] if c.isdigit())
        # 收集该区间的爽点类型分布
        type_counts = Counter()
        for _, r in chunk:
            for stype, count in r['shuang_types'].items():
                type_counts[stype] += count
        type_str = ', '.join(f"{k}({v})" for k, v in type_counts.most_common(3))
        bar = "█" * min(10, int(avg_s * 2))
        print(f"ch{f_start}-{f_end}: {bar} {avg_s:.1f}/章 [{type_str}]")

    # 5. 钩子类型分布
    print()
    print("-" * 70)
    print("钩子类型分布（出现章数）")
    print("-" * 70)
    type_freq = Counter()
    for _, r in results:
        for htype in r['hook_types']:
            type_freq[htype] += 1
    total_chapters_with_hooks = sum(1 for _, r in results if r['hook_types'])
    for htype, count in type_freq.most_common():
        pct = count / n * 100
        bar = "█" * min(20, int(pct / 5))
        print(f"{htype:<12} {bar} {count}/{n} ({pct:.0f}%)")

    print()
    print("=" * 70)
    print("总结")
    print("=" * 70)
    issues = []
    if avg_hook < 3:
        issues.append(f"❌ 钩子强度偏低 ({avg_hook:.1f}/10)。建议强化章末悬念或未完成事件。")
    elif avg_hook < 5:
        issues.append(f"⚠️ 钩子强度中等 ({avg_hook:.1f}/10)。注意保持章末悬念密度。")
    else:
        issues.append(f"✅ 钩子强度良好 ({avg_hook:.1f}/10)。")

    if avg_shuang < 0.5:
        issues.append(f"❌ 爽点密度偏低 ({avg_shuang:.2f}/章)。建议每章至少1个爽点。")
    elif avg_shuang < 1:
        issues.append(f"⚠️ 爽点密度一般 ({avg_shuang:.2f}/章)。近一半章节无爽点。")

    if sum(1 for _, r in results if r['is_truncated']) > n * 0.05:
        issues.append(f"❌ 截断末句比例偏高（>5%），需检查番茄投稿兼容性。")

    if degradation_count > 0:
        issues.append(f"⚠️ {degradation_count} 次连续3章钩力衰减，注意卷末节奏调整。")

    for issue in issues:
        print(f"  {issue}")

    return 0


if __name__ == '__main__':
    main()
