#!/usr/bin/env python3
# SAFETY: SAFE_WRITE — 从 .writer/state/*.json 派生 tracking/*.md；保留 <!-- user-edit --> 块。
"""tracking 渲染：把 .writer/state/*.json 转成人读的 tracking/*.md。

用户手写内容保护：
  用户在 tracking md 中用以下语法包裹自定义内容：

      <!-- user-edit -->
      我的额外规划：ch28-30 老周暴露用刘强作证
      <!-- /user-edit -->

  render_tracking 会：
    1. 读取现有 tracking/*.md（如存在），提取所有 user-edit 块
    2. 用最新 state 重新生成模板部分
    3. 把 user-edit 块**原样保留**在原来的锚点位置

  锚点定位：user-edit 块必须紧跟在某个 `##` 或 `###` 标题下方。
  render_tracking 用"块内容前的最近标题"作为锚点匹配。
  找不到锚点时，把 user-edit 块统一移到文末的"# 用户笔记"节。

用法：
  python render_tracking.py [--project-root <path>] [--only <name>]
    --only characters | hooks | ...   仅渲染指定文件
    --dry-run                          只打印，不写文件

一般由 write.md Step 5 Reflect 后自动调用，也可用户手动跑。
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path


PROJECT_MARKERS = ("novel.json", "writer.json", "novel-pipeline.json")
USER_EDIT_RE = re.compile(
    r"<!--\s*user-edit\s*-->(.*?)<!--\s*/user-edit\s*-->",
    re.DOTALL,
)


def find_project_root(start: Path | None = None) -> Path | None:
    cur = (start or Path.cwd()).resolve()
    for p in [cur] + list(cur.parents)[:5]:
        for m in PROJECT_MARKERS:
            if (p / m).exists():
                return p
    return None


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def extract_user_blocks(md_path: Path) -> list[tuple[str, str]]:
    """从现有 md 中提取所有 user-edit 块。
    返回 [(anchor_heading, block_content), ...]。
    anchor_heading 是 user-edit 块之前最近的 ## / ### 行文本；找不到则为空字符串。
    """
    if not md_path.exists():
        return []
    text = md_path.read_text(encoding="utf-8")
    blocks = []
    for m in USER_EDIT_RE.finditer(text):
        block_content = m.group(1).strip()
        # 找 block 前最近的 ## 或 ### 标题
        prefix = text[: m.start()]
        heading_matches = list(re.finditer(r"^(##+\s+.*)$", prefix, re.MULTILINE))
        anchor = heading_matches[-1].group(1).strip() if heading_matches else ""
        blocks.append((anchor, block_content))
    return blocks


def inject_user_blocks(rendered: str, user_blocks: list[tuple[str, str]]) -> str:
    """把 user-edit 块注入到 rendered 里对应锚点下。找不到锚点的堆到文末。"""
    if not user_blocks:
        return rendered

    lines = rendered.splitlines(keepends=False)
    # 建标题行 → 行号索引
    heading_line_idx = {}
    for i, line in enumerate(lines):
        if re.match(r"^##+\s+", line):
            heading_line_idx[line.strip()] = i

    orphans = []  # 匹配不到锚点的块
    # 从后往前插入，避免行号偏移
    insertions: dict[int, list[str]] = {}
    for anchor, block in user_blocks:
        if anchor and anchor in heading_line_idx:
            idx = heading_line_idx[anchor]
            insertions.setdefault(idx + 1, []).append(
                f"\n<!-- user-edit -->\n{block}\n<!-- /user-edit -->\n"
            )
        else:
            orphans.append(block)

    # 应用插入（从大到小，避免影响索引）
    for idx in sorted(insertions.keys(), reverse=True):
        for block_text in insertions[idx]:
            lines.insert(idx, block_text)

    out = "\n".join(lines).rstrip() + "\n"

    if orphans:
        out += "\n---\n\n## 用户笔记（未匹配锚点）\n\n"
        for block in orphans:
            out += f"<!-- user-edit -->\n{block}\n<!-- /user-edit -->\n\n"

    return out


# ==================== 各文件渲染器 ====================

def render_characters(state_dir: Path) -> str:
    data = _read_json(state_dir / "characters.json") or {"characters": []}
    chars = data.get("characters", [])
    lines = [
        "# 角色状态追踪",
        "",
        f"> 由 `.writer/state/characters.json` v{data.get('version', 1)} 渲染。用户可在任何 `##` 下方追加 `<!-- user-edit -->...<!-- /user-edit -->` 块。",
        "",
    ]
    for c in chars:
        name = c.get("name", "?")
        lines.append(f"## {name}")
        lines.append("")
        for k in [
            "role", "aliases", "cultivation", "cultivation_level", "level",
            "current_location", "emotional_state", "active_goals",
            "special_abilities", "personality_traits", "last_appearance_chapter",
        ]:
            v = c.get(k)
            if v is None or v == "" or v == []:
                continue
            if isinstance(v, list):
                lines.append(f"- **{k}**: {', '.join(str(x) for x in v)}")
            else:
                lines.append(f"- **{k}**: {v}")
        recent = c.get("recent_changes", [])
        if recent:
            lines.append("- **recent_changes**:")
            for r in recent[-5:]:
                lines.append(f"  - {r}")
        lines.append("")
    return "\n".join(lines)


def render_hooks(state_dir: Path) -> str:
    data = _read_json(state_dir / "foreshadowing.json") or {"active": [], "resolved": []}
    lines = [
        "# 伏笔池",
        "",
        f"> 由 `.writer/state/foreshadowing.json` v{data.get('version', 1)} 渲染。",
        "",
        "## 待回收（active）",
        "",
    ]
    active = data.get("active", [])
    if not active:
        lines.append("_（无）_")
    else:
        lines.append("| ID | 描述 | 埋设章 | 预期窗口 | 部分回收 |")
        lines.append("|---|---|---|---|---|")
        for f in active:
            partial = f.get("partial_resolution", [])
            partial_str = f"{len(partial)} 次" if partial else "-"
            lines.append(
                f"| {f.get('id', '?')} | {f.get('description', '?')} | "
                f"ch{f.get('planted_chapter', '?'):03d} | "
                f"{f.get('expected_payoff_window', '-')} | {partial_str} |"
            )
    lines.append("")
    lines.append("## 已回收（resolved）")
    lines.append("")
    resolved = data.get("resolved", [])
    if not resolved:
        lines.append("_（无）_")
    else:
        for f in resolved:
            lines.append(
                f"- **{f.get('id', '?')}**（ch{f.get('planted_chapter', '?')}→ch{f.get('resolved_chapter', '?')}）"
                f"：{f.get('description', '?')}"
            )
            if f.get("resolution"):
                lines.append(f"  - 回收方式：{f['resolution']}")
    lines.append("")
    stats = data.get("stats", {})
    if stats:
        lines.append("## 统计")
        lines.append("")
        for k, v in stats.items():
            lines.append(f"- {k}: {v}")
    lines.append("")
    return "\n".join(lines)


def render_current_state(state_dir: Path, project_root: Path) -> str:
    """current_state.md = 主角 + 关键配角当前值一览。"""
    data = _read_json(state_dir / "characters.json") or {"characters": []}
    chars = data.get("characters", [])
    lines = [
        "# 当前状态快照",
        "",
        f"> 由 `.writer/state/characters.json` v{data.get('version', 1)} 渲染。",
        "",
    ]

    # 主角优先
    protags = [c for c in chars if c.get("role") == "protagonist"]
    others = [c for c in chars if c.get("role") != "protagonist"]

    for group_name, group in [("主角", protags), ("重要角色", others)]:
        if not group:
            continue
        lines.append(f"## {group_name}")
        lines.append("")
        for c in group:
            name = c.get("name", "?")
            cul = c.get("cultivation") or c.get("cultivation_level") or c.get("level") or "-"
            loc = c.get("current_location", "-")
            last = c.get("last_appearance_chapter", "-")
            lines.append(f"### {name}")
            lines.append(f"- 修为/等级：{cul}")
            lines.append(f"- 当前位置：{loc}")
            lines.append(f"- 最近出现：ch{last if isinstance(last, str) else f'{last:03d}'}")
            lines.append("")
    return "\n".join(lines)


RENDERERS = {
    "characters.md": render_characters,
    "hooks.md": render_hooks,
    "current_state.md": lambda sd: render_current_state(sd, Path()),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Render tracking/*.md from .writer/state/*.json")
    parser.add_argument("--project-root", type=Path, help="项目根")
    parser.add_argument("--only", help="仅渲染某个文件（characters.md/hooks.md/current_state.md）")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不写")
    args = parser.parse_args()

    project_root = args.project_root or find_project_root()
    if project_root is None:
        print("ERROR: 未找到项目根", file=sys.stderr)
        return 1

    state_dir = project_root / ".writer" / "state"
    tracking_dir = project_root / "tracking"
    if not state_dir.exists():
        print(f"ERROR: {state_dir} 不存在（先跑 archive_facts.py）", file=sys.stderr)
        return 1
    tracking_dir.mkdir(parents=True, exist_ok=True)

    targets = [args.only] if args.only else list(RENDERERS.keys())
    for fname in targets:
        if fname not in RENDERERS:
            print(f"WARN: 未知目标 {fname}", file=sys.stderr)
            continue
        rendered = RENDERERS[fname](state_dir)
        md_path = tracking_dir / fname

        # 抽取现有 user-edit 块
        user_blocks = extract_user_blocks(md_path)
        final = inject_user_blocks(rendered, user_blocks)

        if args.dry_run:
            print(f"===== {fname} =====")
            print(final)
            print()
            continue

        # 备份 + 写入
        if md_path.exists():
            shutil.copyfile(md_path, md_path.with_suffix(".md.bak"))
        md_path.write_text(final, encoding="utf-8")
        n_blocks = len(user_blocks)
        print(f"✅ {fname} 已渲染（保留 {n_blocks} 个用户块）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
