#!/usr/bin/env python3
# SAFETY: SAFE_WRITE — 追加事实到 .writer/state/*.json；每次写入前对目标 JSON 做 .bak。
"""事实归档：把 Agent 从章节里提取的原子事实变更写入 `.writer/state/*.json`。

接口设计：
  输入：从 stdin 读 JSON payload，格式：
    {
      "chapter_number": 12,
      "changes": {
        "characters": [
          {"name": "苏白", "cultivation": "练气四层", "current_location": "青云门"},
          ...
        ],
        "foreshadowing": {
          "new": [
            {"description": "神秘老者身份", "hints_placed": ["ch_012结尾"]}
          ],
          "resolved_ids": ["f-003"]
        },
        "world_setting": {
          "factions": [{"name": "血刃门", "type": "邪修"}],
          "geography": [...]
        },
        "power_system": {
          "equipment": [{"name": "破空剑", "rank": "灵器"}],
          ...
        }
      }
    }
  输出：stdout 打印 JSON 结果 {archived: bool, changes_applied: [], message: str}

用法：
  echo '<payload>' | python archive_facts.py [--project-root <path>]
  cat payload.json | python archive_facts.py

由 writer 的 write.md Step 5 Reflect 阶段自动调用。用户不直接跑。

写入位置（按优先级）：
  <project>/.writer/state/{characters,foreshadowing,power_system,world_setting}.json
"""
import sys
import json
import argparse
import shutil
from datetime import datetime
from pathlib import Path


PROJECT_MARKERS = ("novel.json", "writer.json", "novel-pipeline.json")


def find_project_root(start: Path | None = None) -> Path | None:
    """从 start (默认 CWD) 向上找项目根标记文件，最多 6 层。"""
    cur = (start or Path.cwd()).resolve()
    for p in [cur] + list(cur.parents)[:5]:
        for marker in PROJECT_MARKERS:
            if (p / marker).exists():
                return p
    return None


def _read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _write_json(path: Path, data: dict) -> None:
    """写入前先备份到 .bak，防止意外损坏。"""
    if path.exists():
        shutil.copyfile(path, path.with_suffix(path.suffix + ".bak"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def apply_character_changes(state_dir: Path, changes: list, chapter_number: int) -> int:
    """更新 characters.json。返回受影响条目数。"""
    fpath = state_dir / "characters.json"
    data = _read_json(fpath, {"version": 1, "characters": []})
    n_applied = 0

    for change in changes:
        name = change.get("name")
        if not name:
            continue
        existing = next((c for c in data["characters"] if c.get("name") == name), None)
        if existing:
            # 更新指定字段
            for key in [
                "cultivation", "cultivation_level", "level",
                "current_location", "emotional_state", "active_goals",
                "special_abilities", "personality_traits",
            ]:
                if key in change:
                    existing[key] = change[key]
            # 追加变更历史
            if "recent_changes" in change:
                existing.setdefault("recent_changes", [])
                for c in change["recent_changes"]:
                    existing["recent_changes"].append(f"ch{chapter_number:03d}: {c}")
            existing["last_appearance_chapter"] = chapter_number
        else:
            # 新角色
            new_char = dict(change)
            new_char.setdefault("role", "supporting")
            new_char["last_appearance_chapter"] = chapter_number
            data["characters"].append(new_char)
        n_applied += 1

    data["version"] = data.get("version", 1) + 1
    _write_json(fpath, data)
    return n_applied


def apply_foreshadowing_changes(state_dir: Path, changes: dict, chapter_number: int) -> int:
    """更新 foreshadowing.json。返回受影响条目数。"""
    fpath = state_dir / "foreshadowing.json"
    data = _read_json(fpath, {"version": 1, "active": [], "resolved": []})
    n = 0

    # 新伏笔
    for item in changes.get("new", []):
        item.setdefault("id", f"f-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(data['active'])}")
        item.setdefault("status", "unresolved")
        item.setdefault("planted_chapter", chapter_number)
        data["active"].append(item)
        n += 1

    # 已回收
    for rid in changes.get("resolved_ids", []):
        for item in data["active"][:]:  # copy 避免遍历时修改
            if item.get("id") == rid:
                item["status"] = "resolved"
                item["resolved_chapter"] = chapter_number
                data["resolved"].append(item)
                data["active"].remove(item)
                n += 1
                break

    # 部分回收
    for pr in changes.get("partial_resolved", []):
        rid = pr.get("id")
        for item in data["active"]:
            if item.get("id") == rid:
                item.setdefault("partial_resolution", [])
                item["partial_resolution"].append({
                    "chapter": chapter_number,
                    "note": pr.get("note", ""),
                })
                n += 1
                break

    data["version"] = data.get("version", 1) + 1
    # 统计
    data["stats"] = {
        "total_planted": len(data["active"]) + len(data["resolved"]),
        "total_resolved": len(data["resolved"]),
        "active": len(data["active"]),
    }
    _write_json(fpath, data)
    return n


def apply_world_changes(state_dir: Path, changes: dict, chapter_number: int) -> int:
    """更新 world_setting.json。"""
    fpath = state_dir / "world_setting.json"
    data = _read_json(fpath, {"version": 1, "factions": [], "geography": [], "special_rules": []})
    n = 0
    for key in ["factions", "geography", "special_rules", "world_layers"]:
        if key in changes and isinstance(changes[key], list):
            existing_names = {
                (e.get("name") if isinstance(e, dict) else str(e))
                for e in data.get(key, [])
            }
            for item in changes[key]:
                name = item.get("name") if isinstance(item, dict) else str(item)
                if name not in existing_names:
                    data.setdefault(key, []).append(item)
                    existing_names.add(name)
                    n += 1
    data["version"] = data.get("version", 1) + 1
    _write_json(fpath, data)
    return n


def apply_power_changes(state_dir: Path, changes: dict, chapter_number: int) -> int:
    """更新 power_system.json。"""
    fpath = state_dir / "power_system.json"
    data = _read_json(fpath, {
        "version": 1, "realms": [], "equipment": [],
        "combat_rules": [], "techniques": [],
    })
    n = 0
    for key in ["realms", "power_levels", "equipment_ranks", "equipment", "combat_rules", "techniques", "forbidden_techniques"]:
        if key in changes and isinstance(changes[key], list):
            existing_names = {
                (e.get("name") if isinstance(e, dict) else str(e))
                for e in data.get(key, [])
            }
            for item in changes[key]:
                name = item.get("name") if isinstance(item, dict) else str(item)
                if name not in existing_names:
                    data.setdefault(key, []).append(item)
                    existing_names.add(name)
                    n += 1
    data["version"] = data.get("version", 1) + 1
    _write_json(fpath, data)
    return n


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive per-chapter facts to .writer/state/*.json")
    parser.add_argument("--project-root", type=Path, help="项目根目录（自动查找 novel.json / writer.json 兜底）")
    parser.add_argument("--dry-run", action="store_true", help="只打印将写入的内容，不实际写")
    args = parser.parse_args()

    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"archived": False, "error": "stdin 为空"}, ensure_ascii=False))
        return 1

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"archived": False, "error": f"JSON 解析失败: {e}"}, ensure_ascii=False))
        return 1

    chapter_number = payload.get("chapter_number", 0)
    changes = payload.get("changes", {})
    if not changes:
        print(json.dumps({"archived": True, "changes_applied": [], "message": "变更为空，跳过归档"}, ensure_ascii=False))
        return 0

    project_root = args.project_root or find_project_root()
    if project_root is None:
        print(json.dumps({"archived": False, "error": "未找到项目根（缺 novel.json / writer.json）"}, ensure_ascii=False))
        return 1

    state_dir = project_root / ".writer" / "state"

    if args.dry_run:
        print(json.dumps({
            "archived": False,
            "dry_run": True,
            "state_dir": str(state_dir),
            "payload": payload,
        }, ensure_ascii=False, indent=2))
        return 0

    state_dir.mkdir(parents=True, exist_ok=True)
    applied = []
    counts = {}

    if changes.get("characters"):
        n = apply_character_changes(state_dir, changes["characters"], chapter_number)
        applied.append("characters"); counts["characters"] = n
    if changes.get("foreshadowing"):
        n = apply_foreshadowing_changes(state_dir, changes["foreshadowing"], chapter_number)
        applied.append("foreshadowing"); counts["foreshadowing"] = n
    if changes.get("world_setting"):
        n = apply_world_changes(state_dir, changes["world_setting"], chapter_number)
        applied.append("world_setting"); counts["world_setting"] = n
    if changes.get("power_system"):
        n = apply_power_changes(state_dir, changes["power_system"], chapter_number)
        applied.append("power_system"); counts["power_system"] = n

    print(json.dumps({
        "archived": True,
        "chapter": chapter_number,
        "state_dir": str(state_dir),
        "changes_applied": applied,
        "counts": counts,
        "message": f"章 {chapter_number} 事实已归档",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
