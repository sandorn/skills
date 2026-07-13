#!/usr/bin/env python3
# SAFETY: READONLY — 读老项目 .writer/state/*.json，输出 novel_project MCP tool-call 序列到 stdout。
#         本脚本不修改任何文件，也不调 MCP；Agent 拿输出后依 phase 顺序调用。
"""一次性迁移：把老 writer 项目 `.writer/state/*.json` 里的角色/伏笔/势力/力量体系
导入 `novel_project` MCP。

用法：
  python import_state_to_mcp.py --project-root D:/OLD/wanjie [--project-prefix wanjie]

流程：
  1. 找 <root>/.writer/state/{characters,foreshadowing,world_setting,power_system}.json
  2. 每个已知字段生成对应的 create_entities / create_relations payload
  3. 用 chIMPORT: 前缀标注观测，避免与后续正常章节归档撞车
  4. 输出到 stdout，Agent 按 tool_calls 顺序调 MCP
  5. 完成后手动删除 .writer/state/ 与 tracking/

Agent 侧执行步骤：
  - 本脚本首次导入不需要 read 阶段（都是首次创建）
  - 直接按顺序调 create_entities 再调 create_relations
  - 完成后向用户确认：`read_graph` 返回的实体数量与本脚本报告的 `stats` 一致

选项：
  --project-prefix <str>   给所有实体名加前缀，如 `wanjie:苏白`，用于多本书共用同一个 MCP db
  --project-root <path>    项目根（自动查找 novel.json / writer.json 兜底）
"""
from __future__ import annotations
import sys
import json
import argparse
from pathlib import Path


PROJECT_MARKERS = ("novel.json", "writer.json", "novel-pipeline.json")


def find_project_root(start: Path | None = None) -> Path | None:
    cur = (start or Path.cwd()).resolve()
    for p in [cur] + list(cur.parents)[:5]:
        for marker in PROJECT_MARKERS:
            if (p / marker).exists():
                return p
    return None


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _prefix(name: str, prefix: str | None) -> str:
    if not prefix or not name:
        return name
    # 保留 伏笔:/剧情:/世界规则: 命名空间前缀
    for ns in ("伏笔:", "剧情:", "世界规则:"):
        if name.startswith(ns):
            return f"{ns}{prefix}:{name[len(ns):]}"
    return f"{prefix}:{name}"


def build_characters(data: dict, prefix: str | None) -> tuple[list, list, int]:
    """characters.json → (entities, relations, count)。"""
    entities, relations = [], []
    chars = data.get("characters", []) or []
    for c in chars:
        raw_name = c.get("name")
        if not raw_name:
            continue
        name = _prefix(raw_name, prefix)
        obs = ["chIMPORT: 从 .writer/state/characters.json 迁移"]
        for key, label in [
            ("role", "角色定位"),
            ("cultivation", "修为"),
            ("cultivation_level", "修为等级"),
            ("level", "等级"),
            ("current_location", "当前位置"),
            ("emotional_state", "情绪"),
        ]:
            if c.get(key):
                obs.append(f"chIMPORT: {label} {c[key]}")
        for g in c.get("active_goals", []) or []:
            obs.append(f"chIMPORT: 目标 {g}")
        for sk in c.get("special_abilities", []) or []:
            obs.append(f"chIMPORT: 掌握 {sk}")
        for tr in c.get("personality_traits", []) or []:
            obs.append(f"chIMPORT: 性格 {tr}")
        for rc in c.get("recent_changes", []) or []:
            obs.append(f"chIMPORT: 历史变更 {rc}")
        if c.get("last_appearance_chapter"):
            obs.append(f"chIMPORT: 最后登场 ch{int(c['last_appearance_chapter']):03d}")

        entities.append({"name": name, "entityType": "人物", "observations": obs})

        # 关系抽取
        for f in c.get("factions", []) or []:
            relations.append({"source": name, "target": _prefix(f, prefix), "type": "所属"})
        for m in c.get("masters", []) or []:
            relations.append({"source": name, "target": _prefix(m, prefix), "type": "师承"})
        for ally in c.get("allies", []) or []:
            relations.append({"source": name, "target": _prefix(ally, prefix), "type": "盟友"})
        for enemy in c.get("enemies", []) or []:
            relations.append({"source": name, "target": _prefix(enemy, prefix), "type": "敌对"})
        for tech in c.get("techniques", []) or c.get("special_abilities", []) or []:
            # techniques 优先当"修习"关系；如果只有 special_abilities，也一并连边
            relations.append({"source": name, "target": _prefix(tech, prefix), "type": "修习"})

    return entities, relations, len(entities)


def build_foreshadowing(data: dict, prefix: str | None) -> tuple[list, int]:
    entities = []
    for item in data.get("active", []) or []:
        raw = item.get("name") or item.get("id") or item.get("description", "")[:20]
        if not raw:
            continue
        name = _prefix(raw if raw.startswith("伏笔:") else f"伏笔:{raw}", prefix)
        obs = ["chIMPORT: 从 .writer/state/foreshadowing.json 迁移 (状态: unresolved)"]
        if item.get("description"):
            obs.append(f"chIMPORT: 描述 {item['description']}")
        if item.get("planted_chapter"):
            obs.append(f"chIMPORT: 埋设章 ch{int(item['planted_chapter']):03d}")
        for hint in item.get("hints_placed", []) or []:
            obs.append(f"chIMPORT: 埋线 {hint}")
        entities.append({"name": name, "entityType": "伏笔", "observations": obs})

    for item in data.get("resolved", []) or []:
        raw = item.get("name") or item.get("id") or item.get("description", "")[:20]
        if not raw:
            continue
        name = _prefix(raw if raw.startswith("伏笔:") else f"伏笔:{raw}", prefix)
        obs = ["chIMPORT: 从 .writer/state/foreshadowing.json 迁移 (状态: resolved)"]
        if item.get("description"):
            obs.append(f"chIMPORT: 描述 {item['description']}")
        if item.get("planted_chapter"):
            obs.append(f"chIMPORT: 埋设章 ch{int(item['planted_chapter']):03d}")
        if item.get("resolved_chapter"):
            obs.append(f"chIMPORT: 回收章 ch{int(item['resolved_chapter']):03d}")
        entities.append({"name": name, "entityType": "伏笔", "observations": obs})

    return entities, len(entities)


def build_world(data: dict, prefix: str | None) -> tuple[list, int]:
    entities = []
    for f in data.get("factions", []) or []:
        raw = f.get("name") if isinstance(f, dict) else str(f)
        if not raw:
            continue
        obs = ["chIMPORT: 从 world_setting.json 迁移"]
        if isinstance(f, dict) and f.get("type"):
            obs.append(f"chIMPORT: 类型 {f['type']}")
        if isinstance(f, dict) and f.get("description"):
            obs.append(f"chIMPORT: {f['description']}")
        entities.append({"name": _prefix(raw, prefix), "entityType": "势力", "observations": obs})

    for g in data.get("geography", []) or []:
        raw = g.get("name") if isinstance(g, dict) else str(g)
        if not raw:
            continue
        obs = ["chIMPORT: 从 world_setting.json 迁移"]
        if isinstance(g, dict) and g.get("description"):
            obs.append(f"chIMPORT: {g['description']}")
        entities.append({"name": _prefix(raw, prefix), "entityType": "地点", "observations": obs})

    for r in data.get("special_rules", []) or []:
        raw = r.get("name") if isinstance(r, dict) else str(r)
        if not raw:
            continue
        canonical = raw if raw.startswith("世界规则:") else f"世界规则:{raw}"
        obs = ["chIMPORT: 从 world_setting.json 迁移"]
        if isinstance(r, dict) and r.get("description"):
            obs.append(f"chIMPORT: {r['description']}")
        entities.append({"name": _prefix(canonical, prefix), "entityType": "世界规则", "observations": obs})

    return entities, len(entities)


def build_power(data: dict, prefix: str | None) -> tuple[list, int]:
    entities = []
    for r in data.get("realms", []) or []:
        raw = r.get("name") if isinstance(r, dict) else str(r)
        if not raw:
            continue
        obs = ["chIMPORT: 从 power_system.json 迁移"]
        if isinstance(r, dict) and r.get("description"):
            obs.append(f"chIMPORT: {r['description']}")
        entities.append({"name": _prefix(raw, prefix), "entityType": "境界", "observations": obs})
    for t in (data.get("techniques", []) or []) + (data.get("equipment", []) or []) + (data.get("forbidden_techniques", []) or []):
        raw = t.get("name") if isinstance(t, dict) else str(t)
        if not raw:
            continue
        obs = ["chIMPORT: 从 power_system.json 迁移"]
        if isinstance(t, dict):
            if t.get("grade") or t.get("rank"):
                obs.append(f"chIMPORT: 品阶 {t.get('grade') or t.get('rank')}")
            if t.get("description"):
                obs.append(f"chIMPORT: {t['description']}")
        entities.append({"name": _prefix(raw, prefix), "entityType": "功法", "observations": obs})

    return entities, len(entities)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate legacy .writer/state/*.json to novel_project MCP")
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--project-prefix", type=str, default=None,
                        help="给所有实体名加前缀，用于多本书共用同一 MCP db")
    args = parser.parse_args()

    root = args.project_root or find_project_root()
    if root is None:
        print(json.dumps({"ok": False, "error": "未找到项目根（缺 novel.json / writer.json）"}, ensure_ascii=False))
        return 1

    state_dir = root / ".writer" / "state"
    if not state_dir.exists():
        print(json.dumps({
            "ok": True,
            "message": f"未发现 .writer/state/，无需迁移: {state_dir}",
            "tool_calls": [],
        }, ensure_ascii=False))
        return 0

    all_entities: list = []
    all_relations: list = []
    stats: dict = {}

    ch = _read_json(state_dir / "characters.json")
    if ch:
        ents, rels, n = build_characters(ch, args.project_prefix)
        all_entities.extend(ents); all_relations.extend(rels); stats["characters"] = n

    fore = _read_json(state_dir / "foreshadowing.json")
    if fore:
        ents, n = build_foreshadowing(fore, args.project_prefix)
        all_entities.extend(ents); stats["foreshadowing"] = n

    world = _read_json(state_dir / "world_setting.json")
    if world:
        ents, n = build_world(world, args.project_prefix)
        all_entities.extend(ents); stats["world_setting"] = n

    power = _read_json(state_dir / "power_system.json")
    if power:
        ents, n = build_power(power, args.project_prefix)
        all_entities.extend(ents); stats["power_system"] = n

    # 分批：每批 create_entities 不超过 40 个，避免超大 payload
    tool_calls: list = []
    BATCH = 40
    for i in range(0, len(all_entities), BATCH):
        tool_calls.append({
            "phase": "write",
            "tool": "create_entities",
            "args": {"entities": all_entities[i:i + BATCH]},
            "purpose": f"批量导入实体 {i}-{min(i + BATCH, len(all_entities)) - 1}",
        })
    for i in range(0, len(all_relations), BATCH):
        tool_calls.append({
            "phase": "write",
            "tool": "create_relations",
            "args": {"relations": all_relations[i:i + BATCH]},
            "purpose": f"批量导入关系 {i}-{min(i + BATCH, len(all_relations)) - 1}",
        })

    output = {
        "ok": True,
        "project_root": str(root),
        "project_prefix": args.project_prefix,
        "stats": {
            **stats,
            "total_entities": len(all_entities),
            "total_relations": len(all_relations),
            "tool_call_batches": len(tool_calls),
        },
        "tool_calls": tool_calls,
        "instructions": (
            "1. 首次导入，无需 read 阶段（都是新实体）\n"
            "2. 按顺序执行所有 tool_calls：先 create_entities 批次，再 create_relations 批次\n"
            "3. 完成后调 read_graph 检查实体数是否与 stats.total_entities 相符\n"
            "4. 一切正常后，手动删除 .writer/state/ 与 tracking/ 目录\n"
            "5. 迁移完成后无需再跑本脚本；日常写章走 archive_facts.py 增量归档\n"
            "详见 references/memory-mcp.md §8"
        ),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
