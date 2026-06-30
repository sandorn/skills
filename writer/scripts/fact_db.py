#!/usr/bin/env python3
# SAFETY: SAFE_WRITE — 仅写入 facts.db，不修改章节文件。自动 .bak 备份数据库。
"""SQLite 事实库 + 章节版本管理 — 写章管线自动调用，无需手动维护。

表结构 (9张):
  chapters             章节元数据 (ch, title, cjk_chars, status, hash)
  chapter_versions     章节版本快照 (draft → reviewed → polished → final)
  level_events         等级变化事件
  gold_events          金币变动事件
  hooks                伏笔池
  character_states     角色状态快照
  relationship_milestones  感情线里程碑
  writing_sessions     写作会话记录

用法:
  python fact_db.py init <project_root>             初始化数据库
  python fact_db.py status <project_root>           事实库概览
  python fact_db.py query <project_root> <subcmd>   查询
  python fact_db.py sync <project_root> <chapter.md>     自动提取+写入事实
  python fact_db.py mirror <project_root> <chapter.md>   镜像正文到数据库（始终最新）
  python fact_db.py version <project_root> <chapter.md> <status>  版本快照
"""

import sqlite3, os, sys, json, re, hashlib, argparse
from datetime import datetime
from pathlib import Path

# ── lib.py 在 scripts/ 同级目录 ──
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import count_chinese, load_character_names

SCHEMA = """
CREATE TABLE IF NOT EXISTS chapters (
    ch INTEGER PRIMARY KEY,
    title TEXT,
    cjk_chars INTEGER,
    content_hash TEXT,
    status TEXT DEFAULT 'draft',     -- draft / reviewed / polished / final
    written_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS chapter_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ch INTEGER NOT NULL,
    version TEXT NOT NULL,           -- 'draft', 'reviewed', 'polished', 'final'
    cjk_chars INTEGER,
    content_hash TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (ch) REFERENCES chapters(ch)
);

CREATE TABLE IF NOT EXISTS level_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ch INTEGER NOT NULL,
    character_name TEXT NOT NULL DEFAULT '主角',
    old_level INTEGER,
    new_level INTEGER,
    reason TEXT,
    FOREIGN KEY (ch) REFERENCES chapters(ch)
);

CREATE TABLE IF NOT EXISTS gold_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ch INTEGER NOT NULL,
    character_name TEXT NOT NULL DEFAULT '主角',
    change_amount INTEGER,
    balance INTEGER,
    reason TEXT,
    FOREIGN KEY (ch) REFERENCES chapters(ch)
);

CREATE TABLE IF NOT EXISTS hooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    planted_ch INTEGER,
    planned_recovery_ch INTEGER,
    recovered_ch INTEGER,
    status TEXT DEFAULT 'planted',
    category TEXT
);

CREATE TABLE IF NOT EXISTS character_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ch INTEGER NOT NULL,
    character_name TEXT NOT NULL,
    level INTEGER,
    permission TEXT,
    location TEXT,
    gold INTEGER,
    relationship TEXT,
    note TEXT,
    FOREIGN KEY (ch) REFERENCES chapters(ch)
);

CREATE TABLE IF NOT EXISTS relationship_milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ch INTEGER NOT NULL,
    character_a TEXT NOT NULL,
    character_b TEXT NOT NULL,
    event TEXT,
    stage TEXT,
    FOREIGN KEY (ch) REFERENCES chapters(ch)
);

CREATE TABLE IF NOT EXISTS chapter_content (
    ch INTEGER PRIMARY KEY,
    full_text TEXT,
    cjk_chars INTEGER,
    content_hash TEXT,
    updated_at TEXT,
    FOREIGN KEY (ch) REFERENCES chapters(ch)
);

CREATE TABLE IF NOT EXISTS writing_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ch INTEGER,
    mode TEXT,
    token_estimate INTEGER,
    note TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);
"""

# ── 自动提取的正则模式 ──

LEVEL_PATTERNS = [
    (r'升(?:到|至|为)\s*(\d+)\s*级', '升级'),
    (r'突破(?:到|至)?\s*(\d+)\s*级', '突破'),
    (r'达到(?:了)?\s*(\d+)\s*级', '达到'),
    (r'晋级\s*(\d+)\s*级', '晋级'),
    (r'跨入\s*(\d+)\s*级', '跨入'),
    (r'Lv\.?\s*(\d+)', '等级标记'),
    (r'等级[：:]\s*(\d+)', '等级标注'),
]

GOLD_PATTERNS = [
    (r'(?:赚了|挣了|进账|收益|利润|纯利|净赚|到手)\s*(\d[\d,万百千亿]*)', 'income'),
    (r'(?:花了|支出|消费|付款|付了|转账)\s*(\d[\d,万百千亿]*)', 'expense'),
    (r'(?:余额|剩余|还有)\s*(\d[\d,万百千亿]*)', 'balance'),
    (r'(\d+)\s*(?:万|百万|千万|亿)?\s*(?:元|块|金币)', 'amount'),
]

RELATIONSHIP_PATTERNS = [
    (r'(?:表白|告白|确定关系|在一起)', 'confession'),
    (r'(?:结婚|婚礼|求婚)', 'relationship'),
    (r'(?:初遇|第一次见面|认识)', 'met'),
    (r'(?:成为朋友|交朋友|结拜)', 'friend'),
    (r'(?:同居|搬.*一起住)', 'relationship'),
]

HOOK_PATTERNS = [
    (r'(?:伏笔|悬念|暗线)', 'plot'),
    (r'(?:秘密|真相|底牌).*(?:揭晓|暴露|发现)', 'plot'),
    (r'(?:约定|承诺|发誓).*(?:将来|以后|下次)', 'plot'),
]


def get_db_path(project_root):
    return os.path.join(project_root, '.writer', 'facts.db')


def connect(project_root):
    db_path = get_db_path(project_root)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def extract_chapter_number(filepath):
    """从文件路径提取章节号"""
    name = os.path.basename(filepath)
    digits = ''.join(c for c in name if c.isdigit())
    return int(digits) if digits else 0


def extract_title(text):
    """从章节文本提取标题"""
    for line in text.split('\n'):
        s = line.strip()
        if s.startswith('# '):
            return s[2:].strip()
    return ''


def extract_level_events(text, ch):
    """自动提取等级变化"""
    events = []
    for pattern, label in LEVEL_PATTERNS:
        for m in re.finditer(pattern, text):
            events.append({
                'ch': ch,
                'character_name': '主角',
                'new_level': int(m.group(1)),
                'reason': f'{label}: {m.group(0)[:40]}',
            })
    return events


def extract_gold_events(text, ch):
    """自动提取金币变动"""
    events = []
    for pattern, etype in GOLD_PATTERNS:
        for m in re.finditer(pattern, text):
            raw = m.group(1).replace(',', '').replace('万', '0000').replace('百万', '000000').replace('千万', '0000000').replace('亿', '00000000').replace('百', '00').replace('千', '000')
            try:
                amount = int(re.sub(r'[^\d]', '', raw))
            except ValueError:
                continue
            if etype == 'expense':
                amount = -amount
            events.append({
                'ch': ch,
                'character_name': '主角',
                'change_amount': amount,
                'reason': f'{etype}: {m.group(0)[:40]}',
            })
    return events


def extract_character_appearances(text, ch, char_names):
    """检测已知角色在章节中的出现"""
    states = []
    for name, info in char_names.items():
        if name in text:
            states.append({
                'ch': ch,
                'character_name': name,
                'note': f'出现于 ch{ch:03d}',
            })
    return states


def extract_relationship_events(text, ch, char_names):
    """自动提取感情线里程碑"""
    events = []
    char_list = list(char_names.keys())
    for pattern, stage in RELATIONSHIP_PATTERNS:
        for m in re.finditer(pattern, text):
            # 找到最近的已知角色
            pos = m.start()
            context = text[max(0, pos-50):pos+50]
            nearby = [c for c in char_list if c in context]
            if len(nearby) >= 1:
                a, b = nearby[0], (nearby[1] if len(nearby) > 1 else '主角')
                events.append({
                    'ch': ch,
                    'character_a': a,
                    'character_b': b,
                    'event': m.group(0)[:60],
                    'stage': stage,
                })
    return events


def content_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def cmd_init(args):
    conn = connect(args.project_root)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"facts.db 已创建: {get_db_path(args.project_root)}")
    print(f"  8 表: chapters, chapter_versions, level_events, gold_events, hooks, character_states, relationship_milestones, writing_sessions")


def cmd_status(args):
    conn = connect(args.project_root)
    cur = conn.cursor()
    tables = ['chapters', 'chapter_versions', 'level_events', 'gold_events', 'hooks',
              'character_states', 'relationship_milestones', 'writing_sessions']
    print(f"{'表名':<28} {'记录数':>6}")
    print("-" * 37)
    for t in tables:
        try:
            count = cur.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        except Exception:
            count = '?'
        print(f"{t:<28} {count:>6}")
    ch = cur.execute("SELECT ch, title, cjk_chars, status FROM chapters ORDER BY ch DESC LIMIT 1").fetchone()
    if ch:
        versions = cur.execute("SELECT count(*) FROM chapter_versions WHERE ch=?", (ch['ch'],)).fetchone()[0]
        print(f"\n最新章节: ch{ch['ch']:03d} \"{ch['title'] or '?'}\" ({ch['cjk_chars']}字, {ch['status']}, {versions}个版本)")
    conn.close()


def cmd_query(args):
    conn = connect(args.project_root)
    cur = conn.cursor()
    q = args.subcmd.lower()
    cs, ce = args.ch_start or 0, args.ch_end or 9999

    if q in ('level', 'levels', 'level-events'):
        rows = cur.execute("SELECT ch, old_level, new_level, reason FROM level_events WHERE ch BETWEEN ? AND ? ORDER BY ch", (cs, ce)).fetchall()
        print(f"{'章':>4} {'旧等级':>6} {'新等级':>6} {'原因'}")
        print("-" * 55)
        for r in rows:
            print(f"ch{r['ch']:03d} {r['old_level'] or '?':>6} -> {r['new_level'] or '?':>6}  {r['reason'] or ''}")
    elif q in ('gold', 'gold-events'):
        rows = cur.execute("SELECT ch, change_amount, balance, reason FROM gold_events WHERE ch BETWEEN ? AND ? ORDER BY ch", (cs, ce)).fetchall()
        for r in rows:
            sign = "+" if (r['change_amount'] or 0) >= 0 else ""
            print(f"ch{r['ch']:03d} {sign}{r['change_amount'] or 0:>8}  {r['reason'] or ''}")
    elif q in ('hook', 'hooks'):
        rows = cur.execute("SELECT id, content, planted_ch, status, category FROM hooks WHERE (planted_ch BETWEEN ? AND ? OR recovered_ch BETWEEN ? AND ?) ORDER BY planted_ch", (cs, ce, cs, ce)).fetchall()
        for r in rows:
            sym = {"planted": "v", "recovered": "ok", "abandoned": "x"}.get(r['status'], "?")
            print(f"{r['id']:>3} ch{r['planted_ch'] or '?':>4} {sym} {r['status']:<10} {r['category'] or '':<12} {(r['content'] or '')[:40]}")
    elif q in ('chars', 'characters', 'char-states'):
        rows = cur.execute("SELECT ch, character_name, level, permission, location FROM character_states WHERE ch BETWEEN ? AND ? ORDER BY ch, character_name", (cs, ce)).fetchall()
        for r in rows:
            print(f"ch{r['ch']:03d} {r['character_name']:<10} L{r['level'] or '?':>4} {r['permission'] or '':<4} {r['location'] or ''[:20]}")
    elif q in ('love', 'relationship'):
        rows = cur.execute("SELECT ch, character_a, character_b, event, stage FROM relationship_milestones WHERE ch BETWEEN ? AND ? ORDER BY ch", (cs, ce)).fetchall()
        for r in rows:
            print(f"ch{r['ch']:03d} {r['character_a']:<10} + {r['character_b']:<10} {r['stage'] or '':<14} {(r['event'] or '')[:30]}")
    elif q in ('versions', 'version'):
        rows = cur.execute("SELECT ch, version, cjk_chars, content_hash, created_at FROM chapter_versions WHERE ch BETWEEN ? AND ? ORDER BY ch, id", (cs, ce)).fetchall()
        print(f"{'章':>4} {'版本':<10} {'字数':>5} {'哈希':<12} {'时间'}")
        for r in rows:
            print(f"ch{r['ch']:03d} {r['version']:<10} {r['cjk_chars'] or '?':>5} {(r['content_hash'] or '')[:10]:<12} {r['created_at'] or ''}")
    elif q in ('content', 'text', 'body'):
        rows = cur.execute("SELECT ch, cjk_chars, content_hash, full_text FROM chapter_content WHERE ch BETWEEN ? AND ? ORDER BY ch", (cs, ce)).fetchall()
        for r in rows:
            print(f"\n=== ch{r['ch']:03d} ({r['cjk_chars']}字, {r['content_hash'][:8] if r['content_hash'] else '?'}) ===\n")
            print(r['full_text'] or '(空)')
    else:
        print(f"未知查询: {q}")
        print("支持: level-events, gold-events, hooks, char-states, relationship, versions, content")
    conn.close()


def cmd_sync(args):
    """自动从章节文件提取事实并写入 facts.db — 写章管线 Step 3 自动调用"""
    chapter_file = args.chapter_file
    if not os.path.exists(chapter_file):
        print(f"文件不存在: {chapter_file}")
        return 1

    with open(chapter_file, 'r', encoding='utf-8') as f:
        text = f.read()

    ch = extract_chapter_number(chapter_file)
    title = extract_title(text)
    cn = count_chinese(text)
    h = content_hash(text)

    project_root = args.project_root
    char_names = load_character_names(project_root)

    conn = connect(project_root)
    cur = conn.cursor()

    # 1. Upsert chapter metadata
    cur.execute("""
        INSERT INTO chapters (ch, title, cjk_chars, content_hash, status, written_at, updated_at)
        VALUES (?, ?, ?, ?, 'draft', ?, ?)
        ON CONFLICT(ch) DO UPDATE SET
            title=excluded.title, cjk_chars=excluded.cjk_chars,
            content_hash=excluded.content_hash, updated_at=excluded.updated_at
    """, (ch, title, cn, h, datetime.now().isoformat(), datetime.now().isoformat()))

    inserts = {'level': 0, 'gold': 0, 'char': 0, 'relation': 0}

    # 2. Extract level events
    prev_level = None
    prev = cur.execute("SELECT new_level FROM level_events WHERE ch < ? ORDER BY ch DESC LIMIT 1", (ch,)).fetchone()
    if prev:
        prev_level = prev[0]

    for ev in extract_level_events(text, ch):
        ev['old_level'] = prev_level
        cur.execute("""
            INSERT INTO level_events (ch, character_name, old_level, new_level, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (ev['ch'], ev['character_name'], ev.get('old_level'), ev['new_level'], ev['reason']))
        prev_level = ev['new_level']
        inserts['level'] += 1

    # 3. Extract gold events
    prev_balance = None
    prev_b = cur.execute("SELECT balance FROM gold_events WHERE ch < ? ORDER BY ch DESC LIMIT 1", (ch,)).fetchone()
    if prev_b:
        prev_balance = prev_b[0]

    for ev in extract_gold_events(text, ch):
        if prev_balance is not None:
            prev_balance += ev['change_amount']
            ev['balance'] = prev_balance
        cur.execute("""
            INSERT INTO gold_events (ch, character_name, change_amount, balance, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (ev['ch'], ev['character_name'], ev['change_amount'], ev.get('balance'), ev['reason']))
        inserts['gold'] += 1

    # 4. Extract character appearances
    for ev in extract_character_appearances(text, ch, char_names):
        cur.execute("""
            INSERT INTO character_states (ch, character_name, note)
            VALUES (?, ?, ?)
        """, (ev['ch'], ev['character_name'], ev['note']))
        inserts['char'] += 1

    # 5. Extract relationship milestones
    for ev in extract_relationship_events(text, ch, char_names):
        cur.execute("""
            INSERT INTO relationship_milestones (ch, character_a, character_b, event, stage)
            VALUES (?, ?, ?, ?, ?)
        """, (ev['ch'], ev['character_a'], ev['character_b'], ev['event'], ev['stage']))
        inserts['relation'] += 1

    conn.commit()
    conn.close()

    print(f"ch{ch:03d} sync: chapter=1 level={inserts['level']} gold={inserts['gold']} char={inserts['char']} relation={inserts['relation']}")
    return 0


def cmd_version(args):
    """保存章节版本快照"""
    chapter_file = args.chapter_file
    version = args.version
    if version not in ('draft', 'reviewed', 'polished', 'final'):
        print(f"无效版本: {version} (应为 draft/reviewed/polished/final)")
        return 1

    with open(chapter_file, 'r', encoding='utf-8') as f:
        text = f.read()

    ch = extract_chapter_number(chapter_file)
    cn = count_chinese(text)
    h = content_hash(text)

    conn = connect(args.project_root)
    cur = conn.cursor()

    # Check for duplicate (same hash)
    existing = cur.execute(
        "SELECT id FROM chapter_versions WHERE ch=? AND content_hash=? AND version=?",
        (ch, h, version)).fetchone()
    if existing:
        conn.close()
        print(f"ch{ch:03d} {version}: skip (same hash)")
        return 0

    cur.execute("""
        INSERT INTO chapter_versions (ch, version, cjk_chars, content_hash)
        VALUES (?, ?, ?, ?)
    """, (ch, version, cn, h))

    # Update chapter status
    cur.execute("UPDATE chapters SET status=?, updated_at=? WHERE ch=?",
                (version, datetime.now().isoformat(), ch))

    conn.commit()
    conn.close()
    print(f"ch{ch:03d} version: {version} ({cn}字, {h[:8]})")
    return 0


def cmd_mirror(args):
    """将章节正文镜像到 chapter_content 表 — 永远存储最新版本"""
    chapter_file = args.chapter_file
    if not os.path.exists(chapter_file):
        print(f"文件不存在: {chapter_file}")
        return 1

    with open(chapter_file, 'r', encoding='utf-8') as f:
        text = f.read()

    ch = extract_chapter_number(chapter_file)
    cn = count_chinese(text)
    h = content_hash(text)

    # 去标题行，只存正文
    lines = text.split('\n')
    body_start = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('#') and i == 0:
            body_start = i + 1
            while body_start < len(lines) and lines[body_start].strip() == '':
                body_start += 1
            break
        elif s == '' and i > 0 and lines[i - 1].strip().startswith('#'):
            body_start = i + 1
            break
    body = '\n'.join(lines[body_start:])

    conn = connect(args.project_root)
    cur = conn.cursor()

    # Check if content changed
    prev = cur.execute("SELECT content_hash FROM chapter_content WHERE ch=?", (ch,)).fetchone()
    if prev and prev['content_hash'] == h:
        conn.close()
        print(f"ch{ch:03d} mirror: skip (unchanged, {cn}字)")
        return 0

    cur.execute("""
        INSERT INTO chapter_content (ch, full_text, cjk_chars, content_hash, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(ch) DO UPDATE SET
            full_text=excluded.full_text, cjk_chars=excluded.cjk_chars,
            content_hash=excluded.content_hash, updated_at=excluded.updated_at
    """, (ch, body, cn, h, datetime.now().isoformat()))

    conn.commit()
    conn.close()
    print(f"ch{ch:03d} mirror: {cn}字 -> chapter_content ({h[:8]})")
    return 0


def main():
    parser = argparse.ArgumentParser(description='Writer 事实库 + 版本管理')
    sub = parser.add_subparsers(dest='command', help='命令')

    p_init = sub.add_parser('init', help='初始化数据库')
    p_init.add_argument('project_root', nargs='?', default='.')

    p_status = sub.add_parser('status', help='事实库概览')
    p_status.add_argument('project_root', nargs='?', default='.')

    p_query = sub.add_parser('query', help='查询事实')
    p_query.add_argument('project_root', nargs='?', default='.')
    p_query.add_argument('subcmd', nargs='?', help='level-events|gold-events|hooks|char-states|relationship|versions|content')
    p_query.add_argument('--ch-start', type=int)
    p_query.add_argument('--ch-end', type=int)

    p_sync = sub.add_parser('sync', help='从章节自动提取事实')
    p_sync.add_argument('project_root', nargs='?', default='.')
    p_sync.add_argument('chapter_file', help='章节 .md 文件路径')

    p_ver = sub.add_parser('version', help='保存章节版本快照')
    p_ver.add_argument('project_root', nargs='?', default='.')
    p_ver.add_argument('chapter_file', help='章节 .md 文件路径')
    p_ver.add_argument('version', help='draft|reviewed|polished|final')

    p_mir = sub.add_parser('mirror', help='镜像章节正文到数据库（始终存储最新版）')
    p_mir.add_argument('project_root', nargs='?', default='.')
    p_mir.add_argument('chapter_file', help='章节 .md 文件路径')

    args = parser.parse_args()

    if args.command == 'init':
        return cmd_init(args)
    elif args.command == 'status':
        return cmd_status(args)
    elif args.command == 'query':
        return cmd_query(args)
    elif args.command == 'sync':
        return cmd_sync(args)
    elif args.command == 'version':
        return cmd_version(args)
    elif args.command == 'mirror':
        return cmd_mirror(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
