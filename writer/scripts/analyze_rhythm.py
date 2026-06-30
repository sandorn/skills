#!/usr/bin/env python3
"""节奏状态查询 — 等级/金币/感情线/钩力趋势 聚合分析。

从 facts.db + 最近 hook_strength 输出 + tracking 文件中提取数据，
回答「最近N章的节奏怎么样」「升级间隔是否合理」「感情线推进频率」等问题。

用法：
    python analyze_rhythm.py <项目根>                                          # 全量节奏报告
    python analyze_rhythm.py <项目根> --ch 1 60                                 # 指定范围
    python analyze_rhythm.py <项目根> --dim level                                # 仅等级维度
    python analyze_rhythm.py <项目根> --dim gold                                 # 仅金币维度
    python analyze_rhythm.py <项目根> --dim hook                                 # 仅钩力维度
    python analyze_rhythm.py <项目根> --dim love                                 # 仅感情线维度

输出格式：Markdown 报告，含每个维度的趋势表和评估。
"""

import re, os, sys, json, sqlite3, argparse
from collections import defaultdict
from datetime import datetime

from lib import count_chinese, find_chapters_dir


def open_fact_db(project_root):
    """连接 facts.db"""
    db_path = os.path.join(project_root, '.writer', 'facts.db')
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ===========================
# 等级节奏
# ===========================
def analyze_level_rhythm(conn, ch_start=0, ch_end=9999):
    """等级提升频率分析"""
    rows = conn.execute("""
        SELECT ch, old_level, new_level, reason
        FROM level_events
        WHERE ch BETWEEN ? AND ?
        ORDER BY ch
    """, (ch_start, ch_end)).fetchall()

    if not rows:
        return None

    results = []
    prev_level = None
    for r in rows:
        if prev_level is not None and r['new_level']:
            interval = r['ch'] - results[-1]['ch'] if results else 0
            results.append({
                'ch': r['ch'],
                'old': r['old_level'],
                'new': r['new_level'],
                'reason': r['reason'] or '',
                'interval': interval,
            })
        prev_level = r['new_level'] or prev_level

    total_interval = results[-1]['ch'] - results[0]['ch'] if len(results) >= 2 else 0
    avg_interval = total_interval / (len(results) - 1) if len(results) >= 2 else 0

    return {
        'events': results,
        'total_events': len(results),
        'avg_interval': avg_interval,
        'total_range': total_interval,
        'recommendation': (
            f"平均 {avg_interval:.1f} 章/级" if avg_interval > 0 else "仅1次升级事件"
        ),
    }


# ===========================
# 金币节奏
# ===========================
def analyze_gold_rhythm(conn, ch_start=0, ch_end=9999):
    """金币流动分析"""
    rows = conn.execute("""
        SELECT ch, change_amount, balance, reason
        FROM gold_events
        WHERE ch BETWEEN ? AND ?
        ORDER BY ch
    """, (ch_start, ch_end)).fetchall()

    if not rows:
        return None

    events = []
    total_income = 0
    total_expense = 0
    income_count = 0
    expense_count = 0

    for r in rows:
        amt = r['change_amount'] or 0
        events.append({
            'ch': r['ch'],
            'delta': amt,
            'balance': r['balance'],
            'reason': r['reason'] or '',
        })
        if amt > 0:
            total_income += amt
            income_count += 1
        elif amt < 0:
            total_expense += abs(amt)
            expense_count += 1

    return {
        'events': events,
        'total_events': len(events),
        'total_income': total_income,
        'total_expense': total_expense,
        'income_count': income_count,
        'expense_count': expense_count,
        'net': total_income - total_expense,
        'recommendation': (
            f"总收入 {total_income}, 总支出 {total_expense}, 净 {total_income - total_expense}"
        ),
    }


# ===========================
# 钩力趋势（从 analyze_hook.py 输出文件读取）
# ===========================
def analyze_hook_rhythm(project_root, ch_start=0, ch_end=9999):
    """从 analyze_hook.py 历史输出中提取钩力趋势"""
    # 尝试运行 analyze_hook.py 获取数据
    hook_script = os.path.join(os.path.dirname(__file__), 'analyze_hook.py')
    if not os.path.exists(hook_script):
        return None

    import subprocess
    try:
        chapters_dir = find_chapters_dir(project_root)
        if not chapters_dir:
            return None

        # 运行 hook_strength，只获取聚合数据
        result = subprocess.run(
            [sys.executable, hook_script, chapters_dir,
             str(ch_start), str(ch_end or 9999)],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout
    except Exception as e:
        return f"[无法运行: {e}]"


# ===========================
# 感情线节奏
# ===========================
def analyze_love_rhythm(conn, ch_start=0, ch_end=9999):
    """感情线推进频率分析"""
    rows = conn.execute("""
        SELECT ch, character_a, character_b, event, stage
        FROM relationship_milestones
        WHERE ch BETWEEN ? AND ?
        ORDER BY ch
    """, (ch_start, ch_end)).fetchall()

    if not rows:
        return None

    stages = []
    stage_order = {'met': 1, 'friend': 2, 'close': 3, 'confession': 4, 'relationship': 5, 'married': 6}
    current_stage = 0
    milestones = []

    for r in rows:
        stage = r['stage']
        stage_val = stage_order.get(stage, 0)
        if stage_val > current_stage:
            current_stage = stage_val
            milestones.append({
                'ch': r['ch'],
                'stage': stage,
                'event': r['event'] or '',
                'progress': f"{stage}/{len(stage_order)}"
            })

    # 感情线密度（每N章有一次事件）
    total_chs = ch_end - ch_start if ch_end > ch_start else 60
    density = total_chs / len(rows) if rows else 0

    return {
        'events': rows,
        'milestones': milestones,
        'total_events': len(rows),
        'current_stage': current_stage,
        'stage_name': {v: k for k, v in stage_order.items()}.get(current_stage, 'unknown'),
        'density': f"每 {density:.1f} 章有一次感情线事件" if rows else '无数据',
        'recommendation': _recommend_love(current_stage, len(rows), total_chs),
    }


def _recommend_love(current_stage, event_count, total_chs):
    if current_stage <= 2 and total_chs > 100:
        return "⚠️ 已写100+章但感情线停留在初级阶段，建议加速推进"
    elif current_stage >= 4 and event_count / max(1, total_chs) > 0.05:
        return "✅ 感情线推进节奏合理"
    elif event_count == 0:
        return "❌ 未有感情线事件记录（如需感情线，建议添加）"
    else:
        return f"当前阶段: {current_stage}/6"


# ===========================
# 综合报告
# ===========================
def generate_report(project_root, ch_start, ch_end, dims):
    """生成节奏报告"""
    conn = open_fact_db(project_root)

    lines = []
    lines.append(f'# 节奏状态报告')
    lines.append(f'> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append(f'> 范围: ch{ch_start}-{ch_end if ch_end != 9999 else "latest"}')
    lines.append('')

    if not conn:
        lines.append('> ⚠️ facts.db 未初始化。运行 `python3 scripts/fact_db.py init .` 后重新查询')
        lines.append('')
        skip_db = True
    else:
        skip_db = False

    # 维度：等级
    if not skip_db and (not dims or 'level' in dims):
        lines.append('## 📈 等级节奏')
        lines.append('')
        lr = analyze_level_rhythm(conn, ch_start, ch_end)
        if lr:
            lines.append(f'| 章 | 等级变化 | 间隔 | 原因 |')
            lines.append(f'|---|---------|------|------|')
            for e in lr['events']:
                gap = f"{e['interval']}章" if e['interval'] > 0 else "-"
                lines.append(f"| ch{e['ch']:03d} | {e['old'] or '?'} → {e['new'] or '?'} | {gap} | {e['reason'][:30]} |")
            lines.append('')
            lines.append(f'- 总事件: {lr["total_events"]} 次')
            lines.append(f'- {lr["recommendation"]}')
            if lr['avg_interval'] > 20:
                lines.append('- ⚠️ 升级间隔超过20章，建议检查升级节奏是否合理')
            elif lr['avg_interval'] < 3:
                lines.append('- ⚠️ 升级间隔过短（<3章），注意避免等级通货膨胀')
        else:
            lines.append('- 无等级事件记录')
        lines.append('')

    # 维度：金币
    if not skip_db and (not dims or 'gold' in dims):
        lines.append('## 💰 金币节奏')
        lines.append('')
        gr = analyze_gold_rhythm(conn, ch_start, ch_end)
        if gr:
            lines.append(f'| 章 | 变动 | 余额 | 原因 |')
            lines.append(f'|---|------|------|------|')
            for e in gr['events'][-10:]:
                sign = '+' if e['delta'] >= 0 else ''
                lines.append(f"| ch{e['ch']:03d} | {sign}{e['delta']:,} | {e['balance'] or '?'} | {e['reason'][:25]} |")
            if len(gr['events']) > 10:
                lines.append(f'| ... (共 {len(gr["events"])} 条，仅显示最近10条) |')
            lines.append('')
            lines.append(f'- {gr["recommendation"]}')
            lines.append(f'- 收入事件: {gr["income_count"]} 次 | 支出事件: {gr["expense_count"]} 次')
        else:
            lines.append('- 无金币事件记录')
        lines.append('')

    # 维度：钩力
    if not dims or 'hook' in dims:
        lines.append('## 🎣 钩力趋势')
        lines.append('')
        hook_data = analyze_hook_rhythm(project_root, ch_start, ch_end)
        if hook_data and '错误' not in hook_data[:10]:
            lines.append('```')
            lines.append(hook_data.strip())
            lines.append('```')
        else:
            lines.append(f'- {hook_data}')
        lines.append('')

    # 维度：感情线
    if not skip_db and (not dims or 'love' in dims):
        lines.append('## 💕 感情线')
        lines.append('')
        lr = analyze_love_rhythm(conn, ch_start, ch_end)
        if lr:
            lines.append(f'| 章 | 阶段 | 事件 |')
            lines.append(f'|---|------|------|')
            for e in lr['events'][-10:]:
                lines.append(f"| ch{e['ch']:03d} | {e['stage'] or ''} | {e['event'] or ''[:40]} |")
            if len(lr['events']) > 10:
                lines.append(f'| ... (共 {len(lr["events"])} 条，仅显示最近10条) |')
            lines.append('')
            lines.append(f'- 里程碑: {len(lr["milestones"])} 个')
            for m in lr['milestones']:
                lines.append(f'  - ch{m["ch"]:03d}: 进入 {m["stage"]} 阶段')
            lines.append(f'- 密度: {lr["density"]}')
            lines.append(f'- {lr["recommendation"]}')
        else:
            lines.append('- 无感情线事件记录')
        lines.append('')

    # 综合评估
    lines.append('## 📊 综合评估')
    lines.append('')
    if not skip_db:
        conn.close()

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='节奏状态查询 — 等级/金币/感情线/钩力趋势 聚合分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('project_root', help='项目根目录')
    parser.add_argument('--ch', nargs=2, type=int, metavar=('START', 'END'), default=None,
                        help='章节范围')
    parser.add_argument('--dim', choices=['level', 'gold', 'hook', 'love'], default=None,
                        help='仅查询指定维度')
    args = parser.parse_args()

    project_root = args.project_root
    ch_start = 0
    ch_end = 9999
    dims = None

    if args.ch is not None:
        ch_start, ch_end = args.ch
    if args.dim is not None:
        dims = [args.dim]
        ch_start = 0
        ch_end = 9999

    report = generate_report(project_root, ch_start, ch_end, dims)
    print(report)


if __name__ == '__main__':
    main()
