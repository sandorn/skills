#!/usr/bin/env python3
# SAFETY: READONLY — 只从 stdin 读事实变更 payload，输出对应的 novel_project MCP tool call 序列到 stdout。
#         本脚本不再写 .writer/state/*.json、不再落任何本地状态。
"""章末事实归档：把 Agent 从章节里提取的原子事实变更转换为 `novel_project` MCP tool call 序列。

接口（v8.4）：
  输入（stdin，JSON）：
    {
      "chapter_number": 12,
      "changes": {
        "characters": [
          {"name": "苏白", "cultivation": "练气四层", "current_location": "青云门",
           "recent_changes": ["突破练气四层", "遇到老周"]},
          ...
        ],
        "foreshadowing": {
          "new": [
            {"name": "老周身份", "description": "神秘老者身份存疑",
             "hints_placed": ["ch012结尾提及腰间玉佩"]}
          ],
          "resolved": [
            {"name": "神秘玉佩", "resolution": "揭示为主角外公遗物"}
          ]
        },
        "factions": [
          {"name": "血刃门", "type": "邪修势力", "note": "反派门派首次出场"}
        ],
        "power": {
          "realms": [{"name": "练气", "note": "1-9 层"}],
          "techniques": [{"name": "破空剑诀", "grade": "黄阶下品"}]
        },
        "relations": [
          {"source": "苏白", "target": "青云门", "type": "所属"},
          {"source": "苏白", "target": "老周", "type": "盟友"}
        ]
      }
    }

  输出（stdout，JSON）：
    {
      "chapter": 12,
      "tool_calls": [
        # 【先查】每个已存在人物：先取现有 observations，Agent 应合并后再写回
        {"phase": "read", "tool": "get_entity_with_relations",
         "args": {"name": "苏白"},
         "purpose": "合并旧观测再 create_entities，避免覆盖"},

        # 【后写】create_entities（Agent 需在此把 old_observations + new_observations 合并）
        {"phase": "write", "tool": "create_entities",
         "args": {
           "entities": [
             {"name": "苏白", "entityType": "人物",
              "observations": [
                # 占位：Agent 从上一步 read 结果取出 old obs，追加本条后写回
                "<merge_with_old>",
                "ch012: 突破练气四层",
                "ch012: 当前位置 青云门",
                "ch012: 突破练气四层",
                "ch012: 遇到老周"
              ]}
           ]
         }},

        # 关系
        {"phase": "write", "tool": "create_relations",
         "args": {"relations": [{"source": "苏白", "target": "青云门", "type": "所属"}]}}
      ],
      "instructions": "..."
    }

Agent 拿到输出后按 phase=read → phase=write 顺序逐条调 MCP；read 阶段拿到 old
observations 后替换 write payload 里的 <merge_with_old> 占位符。

不再写任何 JSON 文件。旧 `.writer/state/*.json` 已废弃，见 references/memory-mcp.md §8。

用法：
  echo '<payload>' | python archive_facts.py [--project-root <path>]
  cat payload.json | python archive_facts.py

由 writer 的 write.md Step 5 Reflect 阶段自动调用。用户不直接跑。
"""
from __future__ import annotations
import sys
import json
import argparse
from pathlib import Path


PROJECT_MARKERS = ("novel.json", "writer.json", "novel-pipeline.json")

# entityType 受控词表（与 references/memory-mcp.md §3.1 对齐）
ENTITY_TYPES = {
    "characters": "人物",
    "factions": "势力",
    "locations": "地点",
    "realms": "境界",
    "techniques": "功法",
    "equipment": "功法",  # 装备也归 功法（法宝/灵器）
    "foreshadowing_new": "伏笔",
    "foreshadowing_resolved": "伏笔",
    "world_rules": "世界规则",
    "plot": "剧情节点",
}


def find_project_root(start: Path | None = None) -> Path | None:
    """从 start (默认 CWD) 向上找项目根标记文件，最多 6 层。"""
    cur = (start or Path.cwd()).resolve()
    for p in [cur] + list(cur.parents)[:5]:
        for marker in PROJECT_MARKERS:
            if (p / marker).exists():
                return p
    return None


def _ch(n: int) -> str:
    """章节前缀（强制 chNNN: 格式，与 memory-mcp.md §3.2 对齐）。"""
    return f"ch{n:03d}"


def build_character_calls(chars: list, chapter: int) -> tuple[list, list]:
    """人物变更 → (read_calls, write_calls)。

    每个人物先 read 拿旧 obs，Agent 合并后写回；关系单独 emit。
    """
    reads, writes, relations = [], [], []
    entities = []
    for c in chars:
        name = c.get("name")
        if not name:
            continue

        # 收集本章观测（原子化，一句一条，强制章节前缀）
        obs = []
        for key in ["cultivation", "cultivation_level", "level"]:
            if key in c:
                obs.append(f"{_ch(chapter)}: 修为 {c[key]}")
                break
        if "current_location" in c:
            obs.append(f"{_ch(chapter)}: 位于 {c['current_location']}")
        if "emotional_state" in c:
            obs.append(f"{_ch(chapter)}: 情绪 {c['emotional_state']}")
        for goal in c.get("active_goals", []) or []:
            obs.append(f"{_ch(chapter)}: 目标 {goal}")
        for skill in c.get("special_abilities", []) or []:
            obs.append(f"{_ch(chapter)}: 掌握 {skill}")
        for trait in c.get("personality_traits", []) or []:
            obs.append(f"{_ch(chapter)}: 性格 {trait}")
        for change in c.get("recent_changes", []) or []:
            obs.append(f"{_ch(chapter)}: {change}")

        if not obs:
            continue

        reads.append({
            "phase": "read",
            "tool": "get_entity_with_relations",
            "args": {"name": name},
            "purpose": f"合并旧观测再写回（{name}）",
        })
        entities.append({
            "name": name,
            "entityType": "人物",
            "observations": ["<merge_with_old>"] + obs,
        })

        # 关系
        for f in c.get("factions", []) or []:
            relations.append({"source": name, "target": f, "type": "所属"})
        for master in c.get("masters", []) or []:
            relations.append({"source": name, "target": master, "type": "师承"})
        for ally in c.get("allies", []) or []:
            relations.append({"source": name, "target": ally, "type": "盟友"})
        for enemy in c.get("enemies", []) or []:
            relations.append({"source": name, "target": enemy, "type": "敌对"})
        for tech in c.get("techniques", []) or []:
            relations.append({"source": name, "target": tech, "type": "修习"})

    if entities:
        writes.append({
            "phase": "write",
            "tool": "create_entities",
            "args": {"entities": entities},
            "purpose": "写回人物观测（Agent 需先合并 read 阶段的旧 observations）",
        })
    return reads, writes + ([{
        "phase": "write",
        "tool": "create_relations",
        "args": {"relations": relations},
        "purpose": "建立人物关系边（幂等）",
    }] if relations else [])


def build_foreshadowing_calls(fore: dict, chapter: int) -> tuple[list, list]:
    """伏笔变更 → (read_calls, write_calls)。新伏笔为 entity，回收伏笔加 `回收于` 边。"""
    reads, writes = [], []
    new_entities = []
    for item in fore.get("new", []) or []:
        raw_name = item.get("name") or item.get("id") or item.get("description", "")[:20]
        if not raw_name:
            continue
        name = raw_name if raw_name.startswith("伏笔:") else f"伏笔:{raw_name}"
        obs = [f"{_ch(chapter)}: 埋设"]
        if item.get("description"):
            obs.append(f"{_ch(chapter)}: {item['description']}")
        for hint in item.get("hints_placed", []) or []:
            obs.append(f"{_ch(chapter)}: 埋线 {hint}")
        new_entities.append({
            "name": name,
            "entityType": "伏笔",
            "observations": obs,
        })

    resolved_relations = []
    resolved_entities = []
    for item in fore.get("resolved", []) or []:
        raw_name = item.get("name") or item.get("id")
        if not raw_name:
            continue
        name = raw_name if raw_name.startswith("伏笔:") else f"伏笔:{raw_name}"
        resolution = item.get("resolution", "已回收")
        reads.append({
            "phase": "read",
            "tool": "get_entity_with_relations",
            "args": {"name": name},
            "purpose": f"合并伏笔旧观测（{name}）",
        })
        resolved_entities.append({
            "name": name,
            "entityType": "伏笔",
            "observations": [
                "<merge_with_old>",
                f"{_ch(chapter)}: 已回收 - {resolution}",
            ],
        })
        # 若章节里有对应 剧情节点 实体，可建 回收于 边；这里输出占位，Agent 视情况调整
        plot_node = item.get("resolved_plot")
        if plot_node:
            plot_name = plot_node if plot_node.startswith("剧情:") else f"剧情:{plot_node}"
            resolved_relations.append({
                "source": name, "target": plot_name, "type": "回收于",
            })

    if new_entities:
        writes.append({
            "phase": "write",
            "tool": "create_entities",
            "args": {"entities": new_entities},
            "purpose": "新伏笔实体（首次创建，无需 merge）",
        })
    if resolved_entities:
        writes.append({
            "phase": "write",
            "tool": "create_entities",
            "args": {"entities": resolved_entities},
            "purpose": "标记伏笔为已回收（需合并旧观测）",
        })
    if resolved_relations:
        writes.append({
            "phase": "write",
            "tool": "create_relations",
            "args": {"relations": resolved_relations},
            "purpose": "伏笔回收于剧情节点",
        })
    return reads, writes


def build_faction_calls(factions: list, chapter: int) -> list:
    """势力：一次性 create_entities，无需 read（新势力直接建）。"""
    entities = []
    for f in factions or []:
        name = f.get("name")
        if not name:
            continue
        obs = [f"{_ch(chapter)}: 首次登场"]
        if f.get("type"):
            obs.append(f"{_ch(chapter)}: 类型 {f['type']}")
        if f.get("note"):
            obs.append(f"{_ch(chapter)}: {f['note']}")
        entities.append({"name": name, "entityType": "势力", "observations": obs})
    if not entities:
        return []
    return [{
        "phase": "write",
        "tool": "create_entities",
        "args": {"entities": entities},
        "purpose": "新势力实体（若已存在需 Agent 手动合并观测）",
    }]


def build_power_calls(power: dict, chapter: int) -> list:
    """境界体系与功法。"""
    entities = []
    for r in power.get("realms", []) or []:
        name = r.get("name") if isinstance(r, dict) else str(r)
        if not name:
            continue
        obs = [f"{_ch(chapter)}: 出现在剧情中"]
        if isinstance(r, dict) and r.get("note"):
            obs.append(f"{_ch(chapter)}: {r['note']}")
        entities.append({"name": name, "entityType": "境界", "observations": obs})
    for t in (power.get("techniques", []) or []) + (power.get("equipment", []) or []):
        name = t.get("name") if isinstance(t, dict) else str(t)
        if not name:
            continue
        obs = [f"{_ch(chapter)}: 出现"]
        if isinstance(t, dict):
            if t.get("grade") or t.get("rank"):
                obs.append(f"{_ch(chapter)}: 品阶 {t.get('grade') or t.get('rank')}")
            if t.get("note"):
                obs.append(f"{_ch(chapter)}: {t['note']}")
        entities.append({"name": name, "entityType": "功法", "observations": obs})
    if not entities:
        return []
    return [{
        "phase": "write",
        "tool": "create_entities",
        "args": {"entities": entities},
        "purpose": "境界/功法实体",
    }]


def build_world_calls(world: dict, chapter: int) -> list:
    """地理/世界规则。"""
    entities = []
    for g in world.get("geography", []) or []:
        name = g.get("name") if isinstance(g, dict) else str(g)
        if not name:
            continue
        obs = [f"{_ch(chapter)}: 首次出现"]
        if isinstance(g, dict) and g.get("note"):
            obs.append(f"{_ch(chapter)}: {g['note']}")
        entities.append({"name": name, "entityType": "地点", "observations": obs})
    for r in world.get("special_rules", []) or []:
        name = r.get("name") if isinstance(r, dict) else str(r)
        if not name:
            continue
        raw = name if name.startswith("世界规则:") else f"世界规则:{name}"
        obs = [f"{_ch(chapter)}: 揭示"]
        if isinstance(r, dict) and r.get("note"):
            obs.append(f"{_ch(chapter)}: {r['note']}")
        entities.append({"name": raw, "entityType": "世界规则", "observations": obs})
    if not entities:
        return []
    return [{
        "phase": "write",
        "tool": "create_entities",
        "args": {"entities": entities},
        "purpose": "地点/世界规则实体",
    }]


def build_extra_relations(rels: list) -> list:
    """用户显式声明的关系。"""
    valid = [r for r in (rels or []) if r.get("source") and r.get("target") and r.get("type")]
    if not valid:
        return []
    return [{
        "phase": "write",
        "tool": "create_relations",
        "args": {"relations": valid},
        "purpose": "显式关系边（用户 payload 传入）",
    }]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Archive per-chapter facts as novel_project MCP tool-call sequence "
                    "(v8.4: no local JSON write).",
    )
    parser.add_argument("--project-root", type=Path,
                        help="项目根目录（自动查找 novel.json / writer.json 兜底）")
    parser.add_argument("--dry-run", action="store_true", help="同 stdout 输出（保留向后兼容）")
    args = parser.parse_args()

    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"ok": False, "error": "stdin 为空"}, ensure_ascii=False))
        return 1

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"JSON 解析失败: {e}"}, ensure_ascii=False))
        return 1

    chapter = payload.get("chapter_number", 0)
    changes = payload.get("changes", {})
    if not changes:
        print(json.dumps({
            "ok": True, "chapter": chapter, "tool_calls": [],
            "message": "变更为空，跳过归档",
        }, ensure_ascii=False))
        return 0

    project_root = args.project_root or find_project_root()
    # 项目根仅用于 sanity check，不再写文件；缺失也允许（脱离 writer 项目时 novel-pipeline 可能没有 marker）

    reads: list = []
    writes: list = []

    if changes.get("characters"):
        r, w = build_character_calls(changes["characters"], chapter)
        reads.extend(r); writes.extend(w)
    if changes.get("foreshadowing"):
        r, w = build_foreshadowing_calls(changes["foreshadowing"], chapter)
        reads.extend(r); writes.extend(w)
    if changes.get("factions"):
        writes.extend(build_faction_calls(changes["factions"], chapter))
    if changes.get("power") or changes.get("power_system"):
        writes.extend(build_power_calls(changes.get("power") or changes.get("power_system"), chapter))
    if changes.get("world_setting") or changes.get("world"):
        writes.extend(build_world_calls(changes.get("world_setting") or changes.get("world"), chapter))
    if changes.get("relations"):
        writes.extend(build_extra_relations(changes["relations"]))

    output = {
        "ok": True,
        "chapter": chapter,
        "project_root": str(project_root) if project_root else None,
        "tool_calls": reads + writes,
        "instructions": (
            "按顺序调 novel_project MCP：\n"
            "1. 先执行所有 phase=read 的 get_entity_with_relations 调用，记录返回的 observations（记为 old_obs）\n"
            "2. 在 phase=write 的 create_entities 参数中，将占位符 '<merge_with_old>' 替换为对应实体的 old_obs 列表元素\n"
            "3. 最后执行所有 phase=write 的调用（顺序：create_entities → create_relations）\n"
            "4. 完成后无需回写任何本地 JSON（v8.4 起 .writer/state/*.json 已废弃）\n"
            "详见 references/memory-mcp.md §4.1"
        ),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
