#!/usr/bin/env python3
"""项目全景报告 — 结构化项目概览 + 统计数据 + 质量指标。

用法：
    python report_panorama.py <项目根>                          # 输出全景报告
    python report_panorama.py <项目根> --output report.md        # 写入文件

输出格式：Markdown，含项目信息、章节统计、角色统计、质量指标、结构健康。
"""

import re, os, sys, json, subprocess
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime


def count_chinese(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def run_script(script_path, args):
    """运行 writer 脚本并捕获输出"""
    try:
        result = subprocess.run(
            [sys.executable, script_path] + args,
            capture_output=True, text=True, timeout=30
        )
        return result.stdout
    except Exception as e:
        return f"[错误: {e}]"


def load_writer_json(project_root):
    """加载项目状态"""
    path = os.path.join(project_root, 'writer.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def load_fact_db_status(project_root):
    """从 facts.db 获取统计"""
    db_path = os.path.join(project_root, '.writer', 'facts.db')
    if not os.path.exists(db_path):
        return None
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        stats = {}
        for table in ['chapters', 'level_events', 'gold_events', 'hooks',
                       'character_states', 'relationship_milestones', 'writing_sessions']:
            count = cur.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            stats[table] = count
        # 最新等级
        latest_level = cur.execute(
            "SELECT ch, new_level FROM level_events ORDER BY ch DESC LIMIT 1"
        ).fetchone()
        if latest_level:
            stats['latest_level'] = f"ch{latest_level[0]}: {latest_level[1]}级"
        # 伏笔状态
        pending_hooks = cur.execute(
            "SELECT count(*) FROM hooks WHERE status='planted'"
        ).fetchone()[0]
        stats['pending_hooks'] = pending_hooks
        conn.close()
        return stats
    except Exception as e:
        return {'error': str(e)}


def scan_chapters(project_root):
    """扫描正文章节"""
    chapters_dir = None
    for d in [os.path.join(project_root, '正文'), os.path.join(project_root, 'chapters')]:
        if os.path.isdir(d):
            chapters_dir = d
            break
    if not chapters_dir:
        return None, []

    files = sorted([f for f in os.listdir(chapters_dir) if f.endswith('.md')])
    chapters = []

    total_cjk = 0
    total_bans = 0
    total_long_paras = 0
    below_threshold = 0
    ban_issues = Counter()

    for f in files:
        fp = os.path.join(chapters_dir, f)
        with open(fp, 'r', encoding='utf-8') as fh:
            text = fh.read()

        cn = count_chinese(text)
        total_cjk += cn

        # 禁令扫描（快速）
        dashes = len(re.findall('——', text))
        ai_phrases = len(re.findall(r'他知道|忽然|突然|不是.*而是', text))
        if dashes > 0:
            ban_issues['破折号'] += 1
            total_bans += 1
        if ai_phrases > 0:
            ban_issues['AI句式'] += 1
            total_bans += 1
        if cn < 2500:
            below_threshold += 1

        # 段落超长
        lines = text.split('\n')
        for line in lines:
            s = line.strip()
            if not s or s.startswith(('#', '「', '『')):
                continue
            if count_chinese(s) > 60:
                total_long_paras += 1

        ch_num = ''.join(c for c in f if c.isdigit()) or '?'
        chapters.append({
            'file': f,
            'ch': int(ch_num) if ch_num.isdigit() else 0,
            'cjk': cn,
            'bans': dashes + ai_phrases,
        })

    stats = {
        'total_chapters': len(files),
        'total_cjk': total_cjk,
        'avg_cjk': total_cjk / len(files) if files else 0,
        'below_threshold': below_threshold,
        'total_bans': total_bans,
        'total_long_paras': total_long_paras,
        'ban_issues': dict(ban_issues),
        'chapters_dir': chapters_dir,
    }
    return stats, chapters


def scan_setting(project_root):
    """扫描设定目录"""
    setting_counts = {}
    for setting_dir in [
        os.path.join(project_root, 'setting'),
        os.path.join(project_root, '设定'),
    ]:
        if os.path.isdir(setting_dir):
            for f in os.listdir(setting_dir):
                if f.endswith('.md'):
                    fp = os.path.join(setting_dir, f)
                    with open(fp, 'r', encoding='utf-8') as fh:
                        text = fh.read()
                    setting_counts[f] = count_chinese(text)
            break
    return setting_counts


def scan_tracking(project_root):
    """扫描追踪文件"""
    tracking = {}
    for tracking_dir in [
        os.path.join(project_root, 'tracking'),
        os.path.join(project_root, '追踪'),
    ]:
        if os.path.isdir(tracking_dir):
            for f in os.listdir(tracking_dir):
                if f.endswith('.md'):
                    fp = os.path.join(tracking_dir, f)
                    tracking[f] = os.path.getsize(fp)
            break
    return tracking


def check_codebase_memory(project_root):
    """检查 MCP codebase-memory 状态"""
    try:
        result = subprocess.run(
            ['index-tool', 'cli', 'index_status',
             json.dumps({'project': os.path.basename(project_root)})],
            capture_output=True, text=True, timeout=10
        )
        if result.stdout.strip():
            return result.stdout.strip()
        return '未响应'
    except Exception:
        return '未安装'


def generate_report(project_root, stats, chapters, setting, tracking, state, fact_stats):
    """生成全景报告"""
    lines = []

    # ===== 头部 =====
    lines.append(f'# 项目全景报告')
    lines.append(f'> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append(f'> 项目路径: {os.path.abspath(project_root)}')
    lines.append('')

    # ===== 基本信息 =====
    lines.append('## 📋 项目信息')
    lines.append('')
    if state:
        lines.append(f'| 字段 | 值 |')
        lines.append(f'|------|-----|')
        for key in ['project', 'author', 'stage', 'genre', 'platform',
                     'chapters_total', 'chapters_done', 'words_per_chapter',
                     'current_volume', 'current_chapter', 'last_action']:
            val = state.get(key, '-')
            labels = {
                'project': '书名', 'author': '作者', 'stage': '阶段',
                'genre': '题材', 'platform': '平台',
                'chapters_total': '计划总章', 'chapters_done': '已完成章',
                'words_per_chapter': '每章字数', 'current_volume': '当前卷',
                'current_chapter': '当前章', 'last_action': '上次操作',
            }
            lines.append(f'| {labels.get(key, key)} | {val} |')
    else:
        lines.append('> writer.json 未找到')
    lines.append('')

    # ===== 章节统计 =====
    lines.append('## 📊 章节统计')
    lines.append('')
    if stats:
        lines.append(f'| 指标 | 数值 |')
        lines.append(f'|------|------|')
        lines.append(f'| 总章数 | {stats["total_chapters"]} |')
        lines.append(f'| 总汉字数 | {stats["total_cjk"]:,} |')
        lines.append(f'| 平均每章 | {stats["avg_cjk"]:.0f} 汉字 |')
        lines.append(f'| 字数不足(<2500) | {stats["below_threshold"]} 章 ({(stats["below_threshold"]/stats["total_chapters"]*100) if stats["total_chapters"] else 0:.0f}%) |')
        lines.append(f'| 禁令命中 | {stats["total_bans"]} 处 |')
        lines.append(f'| 超长段落(>60字) | {stats["total_long_paras"]} 行 |')
        lines.append('')
        if stats.get('ban_issues'):
            lines.append('**禁令分布：**')
            for name, count in stats['ban_issues'].items():
                pct = count / stats['total_chapters'] * 100
                bar = '█' * min(20, int(pct / 5))
                lines.append(f'- {name}: {bar} {count}/{stats["total_chapters"]} ({pct:.0f}%)')
            lines.append('')

    # ===== 章节列表 =====
    lines.append('### 章节速览')
    lines.append('')
    lines.append(f'| 章节 | 汉字 | 禁令 | 状态 |')
    lines.append(f'|------|------|------|------|')
    for ch in chapters[-20:]:  # 最近20章
        status = '✅' if ch['cjk'] >= 2500 and ch['bans'] == 0 else '⚠️'
        lines.append(f'| {ch["file"]} | {ch["cjk"]} | {ch["bans"]} | {status} |')
    if len(chapters) > 20:
        lines.append(f'| ... (共 {len(chapters)} 章，仅显示最近20章) |')
    lines.append('')

    # ===== 设定统计 =====
    lines.append('## 📚 设定文件')
    lines.append('')
    if setting:
        lines.append(f'| 文件 | 汉字 |')
        lines.append(f'|------|------|')
        for name, cn in sorted(setting.items()):
            lines.append(f'| {name} | {cn} |')
    else:
        lines.append('> 设定目录未找到')
    lines.append('')

    # ===== 追踪文件 =====
    lines.append('## 📁 追踪文件')
    lines.append('')
    if tracking:
        lines.append(f'| 文件 | 大小 |')
        lines.append(f'|------|------|')
        for name, size in sorted(tracking.items()):
            lines.append(f'| {name} | {size/1024:.1f} KB |')
    else:
        lines.append('> 追踪目录未找到')
    lines.append('')

    # ===== 事实库状态 =====
    lines.append('## 🗄️ 事实库')
    lines.append('')
    if fact_stats:
        lines.append(f'| 表 | 记录数 |')
        lines.append(f'|----|--------|')
        for table, count in fact_stats.items():
            if table in ('latest_level', 'pending_hooks', 'error'):
                continue
            lines.append(f'| {table} | {count} |')
        if 'latest_level' in fact_stats:
            lines.append(f'')
            lines.append(f'最新等级: {fact_stats["latest_level"]}')
        if 'pending_hooks' in fact_stats:
            lines.append(f'待回收伏笔: {fact_stats["pending_hooks"]} 条')
    else:
        lines.append('> facts.db 未初始化 — 运行: `python3 scripts/fact_db.py init .`')
    lines.append('')

    # ===== MCP 代码库状态 =====
    lines.append('## 🔌 外部知识库状态')
    lines.append('')
    cbm_status = check_codebase_memory(project_root)
    lines.append(f'外部知识库: {cbm_status}')
    lines.append('')

    # ===== 健康评分 =====
    lines.append('## 🏥 健康评分')
    lines.append('')
    score = 100
    issues = []

    if stats:
        # 字数不足
        if stats['below_threshold'] > 0:
            penalty = min(20, stats['below_threshold'])
            score -= penalty
            issues.append(f'-{penalty} 字数不足 {stats["below_threshold"]} 章')
        # 禁令
        if stats['total_bans'] > 0:
            penalty = min(15, stats['total_bans'])
            score -= penalty
            issues.append(f'-{penalty} 禁令 {stats["total_bans"]} 处')
        # 超长段落
        if stats['total_long_paras'] > 10:
            penalty = min(10, stats['total_long_paras'] // 5)
            score -= penalty
            issues.append(f'-{penalty} 超长段落 {stats["total_long_paras"]} 行')
        # 追踪文件缺失
        if not tracking:
            score -= 10
            issues.append('-10 追踪文件缺失')

    score = max(0, score)
    score_bar = '🟢' if score >= 80 else ('🟡' if score >= 60 else '🔴')
    lines.append(f'**{score_bar} 总体健康: {score}/100**')
    if issues:
        lines.append('')
        lines.append('扣分项:')
        for issue in issues:
            lines.append(f'- {issue}')
    else:
        lines.append('- 无扣分项')
    lines.append('')

    # ===== 下一步建议 =====
    lines.append('## 💡 建议')
    lines.append('')
    suggestions = []
    if stats and stats['total_chapters'] > 10 and len(setting) < 3:
        suggestions.append('- 章节多但设定少，建议补充设定文件')
    if not os.path.exists(os.path.join(project_root, '.writer', 'facts.db')):
        suggestions.append('- 事实库未初始化: `python3 scripts/fact_db.py init .`')
    if stats and stats['below_threshold'] > stats['total_chapters'] * 0.1:
        suggestions.append(f'- 字数不足率偏高 ({stats["below_threshold"]}/{stats["total_chapters"]})，建议 safe_pad 批量追加')
    if stats and stats['total_bans'] > 0:
        suggestions.append('- 有禁令残留，建议执行批量禁令扫描+修复')
    if not suggestions:
        suggestions.append('- 项目状态良好，继续写作即可')
    for s in suggestions:
        lines.append(s)
    lines.append('')

    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    project_root = sys.argv[1]
    output_file = None
    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]

    if not os.path.isdir(project_root):
        print(f"错误：项目目录不存在 - {project_root}")
        sys.exit(2)

    # 采集数据
    state = load_writer_json(project_root)
    stats, chapters = scan_chapters(project_root)
    setting = scan_setting(project_root)
    tracking = scan_tracking(project_root)
    fact_stats = load_fact_db_status(project_root)

    # 生成报告
    report = generate_report(project_root, stats, chapters, setting,
                              tracking, state, fact_stats)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 全景报告已写入: {output_file}")
    else:
        print(report)


if __name__ == '__main__':
    main()
