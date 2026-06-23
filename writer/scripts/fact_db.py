#!/usr/bin/env python3
"""SQLite 事实库 — 网文项目的事实存储层。

设计原则：
  - 正文内容留在 .md 文件（人类可读、git diff 友好）
  - 结构化事实存入 SQLite（机器可查、增量更新、可聚合）
  - 写章/审章管线自动 INSERT，不手动维护
  - doctor 用此库替代 grep/search_files 做快速状态查询

用法：
    python fact_db.py init <project_root>             # 初始化数据库
    python fact_db.py status <project_root>           # 查看事实概览
    python fact_db.py insert <project_root>            # 插入事实（stdin JSON）
    python fact_db.py query <project_root> <subcmd>    # 查询事实
      subcmd: level-events | gold-events | hooks | char-states | relationship
      --ch-start N --ch-end M  或  --ch N M

示例：
    python fact_db.py init .
    python fact_db.py status .
    python fact_db.py query . level-events --ch 1 60
    echo '{"table":"level","record":{"ch":180,"new_level":45}}' | python fact_db.py insert .
"""

import sqlite3, os, sys, json, re, argparse
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS chapters (
    ch INTEGER PRIMARY KEY,
    title TEXT,
    cjk_chars INTEGER,
    total_chars INTEGER,
    status TEXT DEFAULT 'draft',     -- draft / reviewed / polished / final
    written_at TEXT,
    updated_at TEXT
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
    change_amount INTEGER,   -- 正=收入 负=支出
    balance INTEGER,         -- 变动后余额
    reason TEXT,
    FOREIGN KEY (ch) REFERENCES chapters(ch)
);

CREATE TABLE IF NOT EXISTS hooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    planted_ch INTEGER,
    planned_recovery_ch INTEGER,
    recovered_ch INTEGER,
    status TEXT DEFAULT 'planted',  -- planted / recovered / abandoned
    category TEXT                   -- power / relationship / plot / world
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
    stage TEXT,   -- met / friend / close / confession / relationship / married
    FOREIGN KEY (ch) REFERENCES chapters(ch)
);

CREATE TABLE IF NOT EXISTS writing_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ch INTEGER,
    mode TEXT,        -- single / batch / delegate / review / polish
    token_estimate INTEGER,
    note TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);
"""


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


def cmd_init(args):
    """初始化数据库（建表）"""
    conn = connect(args.project_root)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"✅ facts.db 已创建: {get_db_path(args.project_root)}")
    print(f"   表: chapters, level_events, gold_events, hooks, character_states, relationship_milestones, writing_sessions")


def cmd_status(args):
    """事实库概览"""
    conn = connect(args.project_root)
    cur = conn.cursor()

    tables = ['chapters', 'level_events', 'gold_events', 'hooks',
              'character_states', 'relationship_milestones', 'writing_sessions']
    print(f"{'表名':<25} {'记录数':>8}")
    print("-" * 35)
    for t in tables:
        count = cur.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"{t:<25} {count:>8}")

    # 最近一个章节的记录
    ch = cur.execute("SELECT ch, title, cjk_chars, status FROM chapters ORDER BY ch DESC LIMIT 1").fetchone()
    if ch:
        print(f"\n最新章节: ch{ch['ch']:03d} \"{ch['title'] or '?'}\" "
              f"({ch['cjk_chars']}汉字, {ch['status']})")

    conn.close()


def cmd_query(args):
    """查询事实"""
    conn = connect(args.project_root)
    cur = conn.cursor()

    q_lower = args.subcmd.lower()

    if q_lower in ('level', 'levels', 'level-events'):
        rows = cur.execute("""
            SELECT ch, old_level, new_level, reason
            FROM level_events
            WHERE ch BETWEEN ? AND ?
            ORDER BY ch
        """, (args.ch_start or 0, args.ch_end or 9999)).fetchall()
        print(f"{'章':>4} {'旧等级':>6} {'新等级':>6} {'原因'}")
        print("-" * 55)
        for r in rows:
            print(f"ch{r['ch']:03d} {r['old_level'] or '?':>6} → {r['new_level'] or '?':>6}  {r['reason'] or ''}")

    elif q_lower in ('gold', 'gold-events'):
        rows = cur.execute("""
            SELECT ch, change_amount, balance, reason
            FROM gold_events
            WHERE ch BETWEEN ? AND ?
            ORDER BY ch
        """, (args.ch_start or 0, args.ch_end or 9999)).fetchall()
        print(f"{'章':>4} {'变动':>8} {'余额':>8} {'原因'}")
        print("-" * 50)
        for r in rows:
            sign = "+" if (r['change_amount'] or 0) >= 0 else ""
            print(f"ch{r['ch']:03d} {sign}{r['change_amount'] or 0:>8} {r['balance'] or '?':>8}  {r['reason'] or ''}")

    elif q_lower in ('hook', 'hooks'):
        rows = cur.execute("""
            SELECT id, content, planted_ch, status, category
            FROM hooks
            WHERE (planted_ch BETWEEN ? AND ? OR recovered_ch BETWEEN ? AND ?)
            ORDER BY planted_ch
        """, (args.ch_start or 0, args.ch_end or 9999, args.ch_start or 0, args.ch_end or 9999)).fetchall()
        print(f"{'ID':>3} {'埋入':>4} {'状态':<10} {'类别':<12} {'内容'}")
        print("-" * 70)
        for r in rows:
            status_sym = {"planted": "🌱", "recovered": "✅", "abandoned": "💀"}.get(r['status'], "?")
            print(f"{r['id']:>3} ch{r['planted_ch'] or '?':>4} {status_sym} {r['status']:<10} {r['category'] or '':<12} {r['content'] or ''[:40]}")

    elif q_lower in ('chars', 'characters', 'char-states'):
        rows = cur.execute("""
            SELECT ch, character_name, level, permission, location
            FROM character_states
            WHERE ch BETWEEN ? AND ?
            ORDER BY ch, character_name
        """, (args.ch_start or 0, args.ch_end or 9999)).fetchall()
        print(f"{'章':>4} {'角色':<10} {'等级':>4} {'权限':<4} {'位置'}")
        print("-" * 45)
        for r in rows:
            print(f"ch{r['ch']:03d} {r['character_name']:<10} {r['level'] or '?':>4} "
                  f"{r['permission'] or '':<4} {r['location'] or ''[:20]}")

    elif q_lower in ('love', 'relationship', '情感', '感情'):
        rows = cur.execute("""
            SELECT ch, character_a, character_b, event, stage
            FROM relationship_milestones
            WHERE ch BETWEEN ? AND ?
            ORDER BY ch
        """, (args.ch_start or 0, args.ch_end or 9999)).fetchall()
        print(f"{'章':>4} {'角色A':<10} {'角色B':<10} {'阶段':<14} {'事件'}")
        print("-" * 65)
        for r in rows:
            print(f"ch{r['ch']:03d} {r['character_a']:<10} {r['character_b']:<10} "
                  f"{r['stage'] or '':<14} {r['event'] or ''[:30]}")

    else:
        print(f"未知查询: {args.subcmd}")
        print("支持: level-events, gold-events, hooks, char-states, relationship")

    conn.close()


def cmd_insert(args):
    """插入事实（由写章/审章管线调用）"""
    conn = connect(args.project_root)
    cur = conn.cursor()

    # 从 stdin 读取 JSON
    data = json.loads(sys.stdin.read())
    table = data.get('table')
    record = data.get('record')

    if table == 'chapter':
        cur.execute("""
            INSERT OR REPLACE INTO chapters (ch, title, cjk_chars, total_chars, status, written_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (record['ch'], record.get('title'), record.get('cjk_chars'),
              record.get('total_chars'), record.get('status', 'draft'),
              record.get('written_at', datetime.now().isoformat()),
              datetime.now().isoformat()))

    elif table == 'level':
        cur.execute("""
            INSERT INTO level_events (ch, character_name, old_level, new_level, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (record['ch'], record.get('character_name', '主角'),
              record.get('old_level'), record.get('new_level'), record.get('reason')))

    elif table == 'gold':
        cur.execute("""
            INSERT INTO gold_events (ch, character_name, change_amount, balance, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (record['ch'], record.get('character_name', '主角'),
              record.get('change_amount'), record.get('balance'), record.get('reason')))

    elif table == 'hook':
        cur.execute("""
            INSERT INTO hooks (content, planted_ch, planned_recovery_ch, recovered_ch, status, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (record['content'], record['planted_ch'],
              record.get('planned_recovery_ch'), record.get('recovered_ch'),
              record.get('status', 'planted'), record.get('category')))

    elif table == 'char_state':
        cur.execute("""
            INSERT INTO character_states (ch, character_name, level, permission, location, gold, relationship, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (record['ch'], record['character_name'],
              record.get('level'), record.get('permission'),
              record.get('location'), record.get('gold'),
              record.get('relationship'), record.get('note')))

    elif table == 'relationship':
        cur.execute("""
            INSERT INTO relationship_milestones (ch, character_a, character_b, event, stage)
            VALUES (?, ?, ?, ?, ?)
        """, (record['ch'], record['character_a'],
              record['character_b'], record.get('event'), record.get('stage')))

    elif table == 'session':
        cur.execute("""
            INSERT INTO writing_sessions (ch, mode, token_estimate, note)
            VALUES (?, ?, ?, ?)
        """, (record.get('ch'), record.get('mode'),
              record.get('token_estimate'), record.get('note')))

    else:
        print(f"未知表: {table}")
        conn.close()
        return 1

    conn.commit()
    conn.close()
    print(f"✅ INSERT {table} OK")
    return 0


def main():
    parser = argparse.ArgumentParser(description='Writer 事实库')
    parser.add_argument('command', choices=['init', 'status', 'query', 'insert'])
    parser.add_argument('project_root', nargs='?', default='.')
    parser.add_argument('subcmd', nargs='?', help='query 子命令: level-events/gold-events/hooks/char-states/relationship')
    parser.add_argument('--ch-start', type=int, help='起始章')
    parser.add_argument('--ch-end', type=int, help='结束章')
    args = parser.parse_args()

    if not args.project_root and args.command != 'init':
        print("请指定项目根目录")
        sys.exit(1)

    if args.command == 'init':
        return cmd_init(args)
    elif args.command == 'status':
        return cmd_status(args)
    elif args.command == 'query':
        return cmd_query(args)
    elif args.command == 'insert':
        return cmd_insert(args)


if __name__ == '__main__':
    main()
