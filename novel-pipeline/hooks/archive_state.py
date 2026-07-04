#!/usr/bin/env python3
"""
Hook: archive_state
每章完成时自动归档状态变更（Layer 1 自动化）
触发: 章节生成完成后

从 stdin 接收 Agent 汇总的本章变更，更新 state-files/ 下的 JSON 文件，
并同步写入 memory-novel 知识图谱。
"""
import sys, json, os
from pathlib import Path
from datetime import datetime

# 项目隔离：优先当前项目 state-files/，回退 Skill 模板
from utils import find_state_dir, memory_store_entities, memory_store_relations
STATE_DIR = find_state_dir()


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return output(True, "无变更输入，跳过归档")

        data = json.loads(raw)
        changes = data.get("changes", data)

        if not changes:
            return output(True, "变更列表为空，跳过归档")

        applied = []

        # 1. 伏笔变更
        foreshadowing_changes = changes.get("foreshadowing", {})
        if foreshadowing_changes:
            _update_foreshadowing(foreshadowing_changes)
            applied.append("foreshadowing")

        # 2. 人物变更
        character_changes = changes.get("characters", [])
        if character_changes:
            _update_characters(character_changes)
            applied.append("characters")

        # 3. 世界观变更
        world_changes = changes.get("world_setting", {})
        if world_changes:
            _update_world_setting(world_changes)
            applied.append("world_setting")

        # 4. 战力/体系变更
        power_changes = changes.get("power_system", {})
        if power_changes:
            _update_power_system(power_changes)
            applied.append("power_system")

        return output(True, f"已归档: {', '.join(applied)}" if applied else "无匹配变更类型")

    except json.JSONDecodeError as e:
        return output(False, f"JSON 解析失败: {str(e)}")
    except Exception as e:
        return output(False, f"归档异常: {str(e)}")


def _update_foreshadowing(changes: dict) -> None:
    fpath = STATE_DIR / "foreshadowing.json"
    data = _read_json(fpath, {"version": 1, "active": [], "resolved": []})

    new_items = changes.get("new", [])
    for item in new_items:
        item.setdefault("id", f"f-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(data['active'])}")
        item.setdefault("status", "unresolved")
        item.setdefault("planted_chapter", changes.get("chapter_number", 0))
        data["active"].append(item)

    resolved_ids = changes.get("resolved_ids", [])
    for rid in resolved_ids:
        for item in data["active"]:
            if item.get("id") == rid:
                item["status"] = "resolved"
                item["resolved_chapter"] = changes.get("chapter_number", 0)
                data["resolved"].append(item)
                data["active"].remove(item)
                break

    data["version"] = data.get("version", 1) + 1
    _write_json(fpath, data)


def _update_characters(changes: list) -> None:
    fpath = STATE_DIR / "characters.json"
    data = _read_json(fpath, {"version": 1, "characters": []})

    memory_entities = []

    for change in changes:
        name = change.get("name")
        if not name:
            continue
        existing = next((c for c in data["characters"] if c["name"] == name), None)
        if existing:
            for key in ["cultivation_level", "level", "current_location", "emotional_state", "active_goals"]:
                if key in change:
                    existing[key] = change[key]
            if "recent_changes" in change:
                existing.setdefault("recent_changes", [])
                existing["recent_changes"].extend(change["recent_changes"])
            existing["last_appearance_chapter"] = change.get("chapter_number", existing.get("last_appearance_chapter", 0))
        else:
            change.setdefault("role", "supporting")
            change.setdefault("last_appearance_chapter", change.get("chapter_number", 0))
            data["characters"].append(change)

        # 同步到 memory-novel
        memory_entities.append({
            "name": name,
            "entityType": "character",
            "observations": [
                f"角色定位: {change.get('role', 'unknown')}",
                f"等级: {change.get('cultivation_level', change.get('level', 'unknown'))}",
                f"位置: {change.get('current_location', 'unknown')}",
                f"最近章节: 第{change.get('chapter_number', 0)}章",
            ]
        })

    data["version"] = data.get("version", 1) + 1
    _write_json(fpath, data)

    # memory-novel 同步（无视失败）
    if memory_entities:
        try:
            memory_store_entities(memory_entities)
        except Exception:
            pass


def _update_world_setting(changes: dict) -> None:
    fpath = STATE_DIR / "world_setting.json"
    data = _read_json(fpath, {"version": 1, "factions": [], "geography": [], "special_rules": []})

    memory_entities = []
    memory_relations = []

    for key in ["factions", "geography", "special_rules", "world_layers"]:
        if key in changes:
            existing = data.get(key, [])
            if isinstance(changes[key], list):
                for item in changes[key]:
                    if isinstance(item, dict) and "name" in item:
                        memory_entities.append({
                            "name": item["name"],
                            "entityType": key.rstrip("s"),  # factions -> faction
                            "observations": [f"{k}: {v}" for k, v in item.items() if k != "name"],
                        })
                existing.extend(changes[key])
            data[key] = existing

    data["version"] = data.get("version", 1) + 1
    _write_json(fpath, data)

    if memory_entities:
        try:
            memory_store_entities(memory_entities)
        except Exception:
            pass

    if memory_relations:
        try:
            memory_store_relations(memory_relations)
        except Exception:
            pass


def _update_power_system(changes: dict) -> None:
    fpath = STATE_DIR / "power_system.json"
    data = _read_json(fpath, {"version": 1, "power_levels": [], "equipment": [], "combat_rules": []})

    for key in ["power_levels", "realms", "equipment", "combat_rules"]:
        if key in changes:
            existing = data.get(key, [])
            if isinstance(changes[key], list):
                existing.extend(changes[key])
            data[key] = existing

    data["version"] = data.get("version", 1) + 1
    _write_json(fpath, data)


def _read_json(fpath: Path, default: dict) -> dict:
    if fpath.exists():
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return default


def _write_json(fpath: Path, data: dict) -> None:
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def output(success: bool, message: str) -> None:
    result = {
        "archived": success,
        "message": message,
        "hook": "archive_state",
    }
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
