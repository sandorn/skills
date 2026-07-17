#!/usr/bin/env python3
"""
novel-pipeline DeepSeek draft CLI.

Generates chapter drafts sequentially through the novel-deepseek MCP server.
This script only writes chapters/*.md and .draft_progress.json. It does not
read or write novel_project memory; writer remains responsible for archiving.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from mcp_utils import ensure_mcps_ready
from polish_chapter import ensure_git_snapshot
from utils import BaseMCPClient, PIPELINE_PYTHON, chapter_filename


SKILL_ROOT = Path(__file__).parent.parent
DEEPSEEK = SKILL_ROOT / "mcp" / "novel-deepseek" / "deepseek_server.py"
DEEPSEEK_CWD = SKILL_ROOT / "mcp" / "novel-deepseek"
PROJECT_MARKERS = ("novel.json", "writer.json", "novel-pipeline.json")


def parse_range(spec: str) -> tuple[int, int]:
    """Accept '5' or '5-30'."""
    if "-" in spec:
        a, b = spec.split("-", 1)
        start, end = int(a), int(b)
    else:
        start = end = int(spec)
    if start <= 0 or end <= 0 or end < start:
        raise argparse.ArgumentTypeError("range must be N or N-M with 1 <= N <= M")
    return start, end


def count_chinese(text: str) -> int:
    return len(re.findall(r"[一-鿿㐀-䶿]", text))


def find_project_root(start: Path) -> Path | None:
    cur = start.resolve()
    for p in [cur, *cur.parents][:8]:
        if any((p / marker).exists() for marker in PROJECT_MARKERS):
            return p
    return None


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def build_global_setting(project_root: Path | None, explicit_files: list[str]) -> str:
    """Build the global setting text passed to DeepSeek."""
    parts: list[str] = []
    for raw in explicit_files:
        p = Path(raw)
        if p.exists():
            parts.append(f"【{p.name}】\n{read_text_file(p)}")

    if project_root:
        setting_dir = project_root / "setting"
        if setting_dir.exists():
            for name in [
                "story_bible.md",
                "characters.md",
                "power_system.md",
                "factions.md",
                "writing_rules.md",
            ]:
                p = setting_dir / name
                if p.exists():
                    parts.append(f"【setting/{name}】\n{read_text_file(p)}")

    return "\n\n".join(part for part in parts if part.strip())


def find_outline_file(project_root: Path | None, outline_dir: Path | None, chapter: int) -> Path | None:
    candidates: list[Path] = []
    filename = chapter_filename(chapter)
    if outline_dir:
        candidates.extend([
            outline_dir / filename,
            outline_dir / f"ch{chapter:03d}.md",
            outline_dir / f"{chapter:03d}.md",
        ])
    if project_root:
        base = project_root / "outline" / "chapter_outline"
        candidates.extend([
            base / filename,
            base / f"ch{chapter:03d}.md",
            base / f"{chapter:03d}.md",
        ])
    for p in candidates:
        if p.exists():
            return p
    return None


class ProgressTracker:
    """Resume state stored next to chapters_dir."""

    def __init__(self, chapters_dir: Path):
        self.file = chapters_dir.parent / ".draft_progress.json"
        self.data = self._load()

    def _load(self) -> dict:
        if self.file.exists():
            try:
                return json.loads(self.file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        return {"completed": [], "failed": {}}

    def save(self) -> None:
        self.file.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def is_done(self, chapter: int) -> bool:
        return chapter in self.data["completed"]

    def mark_done(self, chapter: int) -> None:
        if chapter not in self.data["completed"]:
            self.data["completed"].append(chapter)
        self.data["failed"].pop(str(chapter), None)
        self.save()

    def mark_failed(self, chapter: int, reason: str) -> None:
        self.data["failed"][str(chapter)] = reason
        self.save()

    def reset(self) -> None:
        self.data = {"completed": [], "failed": {}}
        self.save()


def generate_draft(client: BaseMCPClient, chapter: int, global_setting: str, outline: str, revision: str) -> tuple[bool, str]:
    result = client.call_tool(
        "generate_draft",
        {
            "global_setting": global_setting,
            "chapter_outline": outline,
            "chapter_number": chapter,
            "revision_instructions": revision,
        },
    )
    if not result.get("success"):
        return False, result.get("error", "unknown MCP error")
    text = str(result.get("data", "")).strip()
    if not text:
        return False, "empty draft"
    if text.startswith("ERROR:"):
        return False, text[:500]
    return True, text


def write_chapter(chapters_dir: Path, chapter: int, text: str, overwrite: bool) -> tuple[bool, str]:
    path = chapters_dir / chapter_filename(chapter)
    if path.exists() and not overwrite:
        return False, f"{path.name} already exists; pass --overwrite to replace"
    if path.exists():
        old = path.read_text(encoding="utf-8")
        if old != text:
            path.with_suffix(path.suffix + ".bak").write_text(old, encoding="utf-8")
    path.write_text(text, encoding="utf-8")
    return True, str(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate chapter drafts through novel-deepseek MCP.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_draft_range.py --range 1-5 D:\\Book\\chapters
  python generate_draft_range.py --range 8 D:\\Book\\chapters --overwrite
  python generate_draft_range.py --range 1-3 chapters --outline-dir outline/chapter_outline --setting-file setting/story_bible.md
        """,
    )
    parser.add_argument("--range", dest="range_spec", required=True, help="chapter range, e.g. 1 or 1-30")
    parser.add_argument("chapters_dir", help="target chapters directory")
    parser.add_argument("--outline-dir", type=Path, help="chapter outline directory; defaults to <project>/outline/chapter_outline")
    parser.add_argument("--setting-file", action="append", default=[], help="extra setting file; can be repeated")
    parser.add_argument("--revision-file", type=Path, help="revision instructions applied to every generated chapter")
    parser.add_argument("--overwrite", action="store_true", help="replace existing ch_NNN.md files and create .bak")
    parser.add_argument("--force", action="store_true", help="allow writes without a git repo")
    parser.add_argument("--skip-snapshot", action="store_true", help="skip git snapshot when an outer workflow already did it")
    parser.add_argument("--reset", action="store_true", help="reset .draft_progress.json")
    parser.add_argument("--delay", type=int, default=2, help="seconds between chapters")
    parser.add_argument("--min-words", type=int, default=2500, help="minimum Chinese characters warning threshold")
    args = parser.parse_args()

    start, end = parse_range(args.range_spec)
    chapters_dir = Path(args.chapters_dir).resolve()
    chapters_dir.mkdir(parents=True, exist_ok=True)
    project_root = find_project_root(chapters_dir)

    global_setting = build_global_setting(project_root, args.setting_file)
    if not global_setting:
        print("⚠️  未找到设定文本，将只按章纲生成。", file=sys.stderr)
        global_setting = "无额外设定。严格遵循本章细纲。"

    revision = read_text_file(args.revision_file) if args.revision_file and args.revision_file.exists() else ""

    if not ensure_mcps_ready([("novel-deepseek", "novel-deepseek", "deepseek_server.py")]):
        return 1
    if not args.skip_snapshot and not ensure_git_snapshot(chapters_dir, force=args.force):
        return 2
    if not DEEPSEEK.exists():
        print(f"❌ DeepSeek MCP server not found: {DEEPSEEK}", file=sys.stderr)
        return 2

    progress = ProgressTracker(chapters_dir)
    if args.reset:
        progress.reset()
        print("进度已重置")

    python = str(PIPELINE_PYTHON) if PIPELINE_PYTHON.exists() else sys.executable
    ok = skip = fail = 0
    total = end - start + 1
    print(f"DeepSeek 出稿 ch_{start:03d} -> ch_{end:03d}（共 {total} 章）")
    print(f"章节目录：{chapters_dir}")
    print(f"进度文件：{progress.file}")

    with BaseMCPClient([python, str(DEEPSEEK)], timeout=300, cwd=DEEPSEEK_CWD) as client:
        for index, chapter in enumerate(range(start, end + 1), 1):
            if progress.is_done(chapter):
                print(f"[{index}/{total}] ch_{chapter:03d} 已完成，跳过")
                skip += 1
                continue

            outline_file = find_outline_file(project_root, args.outline_dir.resolve() if args.outline_dir else None, chapter)
            if not outline_file:
                msg = "missing chapter outline"
                print(f"[{index}/{total}] ch_{chapter:03d} 失败：{msg}")
                progress.mark_failed(chapter, msg)
                fail += 1
                continue

            outline = read_text_file(outline_file)
            print(f"[{index}/{total}] ch_{chapter:03d} 生成中：{outline_file.name}")
            success, draft = generate_draft(client, chapter, global_setting, outline, revision)
            if not success:
                print(f"  失败：{draft[:200]}")
                progress.mark_failed(chapter, draft)
                fail += 1
                continue

            written, message = write_chapter(chapters_dir, chapter, draft, overwrite=args.overwrite)
            if not written:
                print(f"  跳过：{message}")
                progress.mark_failed(chapter, message)
                skip += 1
                continue

            cn = count_chinese(draft)
            suffix = "" if cn >= args.min_words else f" ⚠️ 低于 {args.min_words}"
            print(f"  完成：{Path(message).name}，中文字数 {cn}{suffix}")
            progress.mark_done(chapter)
            ok += 1
            if index < total and args.delay > 0:
                time.sleep(args.delay)

    print(f"完成：OK={ok} 跳过={skip} 失败={fail}")
    if progress.data["failed"]:
        print("失败列表：")
        for key, reason in sorted(progress.data["failed"].items(), key=lambda item: int(item[0])):
            print(f"  ch_{int(key):03d}: {reason[:120]}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
