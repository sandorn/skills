#!/usr/bin/env python3
"""
SessionStart Hook: load_state
自动加载持久化存档文件（Layer 1 自动化）
触发: 会话启动，novel-pipeline skill 激活时

扫描 state-files/ 目录 + 查询 memory-novel 知识图谱，
输出摘要供 Agent 加载为会话上下文。
"""
import sys, json, os
from pathlib import Path
from datetime import datetime

# 项目隔离：优先当前项目 state-files/，回退 Skill 模板
from utils import find_state_dir, memory_search
STATE_DIR = find_state_dir()

STATE_FILES = [
    "world_setting.json",
    "characters.json",
    "foreshadowing.json",
    "power_system.json",
]


def main():
    try:
        loaded = {}
        summary_parts = []
        memory_notes = []
        total_entries = 0

        for fname in STATE_FILES:
            fpath = STATE_DIR / fname
            if not fpath.exists():
                continue
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                loaded[fname] = _summarize(fname, data)
                entries, desc = loaded[fname]
                total_entries += entries
                if desc:
                    summary_parts.append(desc)
            except (json.JSONDecodeError, IOError) as e:
                loaded[fname] = (0, f"读取失败: {str(e)}")

        # 补充 memory-novel 知识图谱查询
        try:
            for entity_type in ["主角", "反派", "势力", "世界观"]:
                nodes = memory_search(entity_type)
                if nodes:
                    memory_notes.append(f"[memory] {entity_type}: {len(nodes)} 条")
        except Exception:
            pass  # memory-novel 不可用时静默跳过

        summary = "\n".join(summary_parts) if summary_parts else "（状态文件为空或不存在——请先创建世界观设定）"

        result = {
            "loaded": True,
            "timestamp": datetime.now().isoformat(),
            "files_loaded": list(loaded.keys()),
            "total_entries": total_entries,
            "summary": summary,
            "memory_notes": memory_notes,
            "hook": "load_state",
            "instruction": "以上状态已加载至会话上下文。续写时自动携带最新人物/伏笔/世界观信息。",
        }

        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)

    except Exception as e:
        result = {
            "loaded": False,
            "error": str(e),
            "hook": "load_state",
        }
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)  # 不阻断启动


def _summarize(fname: str, data: dict) -> tuple[int, str]:
    """对每个状态文件生成摘要"""
    if fname == "world_setting.json":
        factions = data.get("factions", [])
        realms = data.get("realms", []) or data.get("world_layers", [])
        n = len(factions) + len(realms)
        names = [f.get("name", "?") for f in factions]
        return n, f"[世界观] {len(factions)}个势力({', '.join(names[:5])}), {len(realms)}个等级/世界层级"

    elif fname == "characters.json":
        chars = data.get("characters", [])
        summaries = []
        for c in chars[:10]:
            name = c.get("name", "?")
            role = c.get("role", "?")
            level = c.get("cultivation_level", "") or c.get("level", "")
            summaries.append(f"{name}({role}{'/'+level if level else ''})")
        return len(chars), f"[人物] ({len(chars)}): {', '.join(summaries)}"

    elif fname == "foreshadowing.json":
        active = data.get("active", [])
        resolved = data.get("resolved", [])
        open_items = [f"{f.get('id','?')}:{f.get('description','?')[:20]}" for f in active[:8]]
        return len(active), f"[伏笔] {len(active)}个未回收({'; '.join(open_items) if open_items else '无'}), {len(resolved)}个已回收"

    elif fname == "power_system.json":
        realms = data.get("realms", []) or data.get("power_levels", [])
        equip = data.get("equipment", [])
        rules = data.get("combat_rules", [])
        return len(realms) + len(equip) + len(rules), f"[战力/体系] {len(realms)}等级, {len(equip)}装备/物品, {len(rules)}战斗/能力规则"

    return 0, ""


if __name__ == "__main__":
    main()
