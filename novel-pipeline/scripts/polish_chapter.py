#!/usr/bin/env python3
"""
novel-pipeline Skill 官方逐章润色工具
触发词：逐章润色 / 批量润色

功能：
  - 单章模式：`polish_chapter.py 101 <chapters_dir>` 处理单章
  - 批量模式：`polish_chapter.py --range 1-30 <chapters_dir>` 顺序处理，支持断点续传
  - 字数循环 + 文风覆盖 由 novel-doubao MCP 一次调用完成
  - 每次执行前对项目做 git 快照，避免无备份覆盖

前置钩子：
  1. ensure_mcps_ready()   — 检查/注册依赖 MCP
  2. ensure_git_snapshot() — 覆盖章节文件前 git 快照
     - 项目非 git repo   → 打印警告；除非 --force，否则拒绝执行
     - 有未提交变更     → 自动 commit "pre-polish snapshot"
     - 完全干净         → 跳过
"""
import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))
from mcp_utils import ensure_mcps_ready
from utils import chapter_filename

SKILL_ROOT = Path(__file__).parent.parent
POLISH_SCRIPT = SKILL_ROOT / "hooks" / "polish_independent.py"


# ==================== Git 快照前置钩子 ====================
def _run_git(args, cwd):
    r = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _find_git_root(start):
    start = Path(start).resolve()
    for p in [start, *start.parents][:6]:
        if (p / ".git").exists():
            return p
    return None


def ensure_git_snapshot(chapters_dir, force=False):
    chapters_dir = Path(chapters_dir).resolve()
    git_root = _find_git_root(chapters_dir)

    if git_root is None:
        print("⚠️  项目目录不是 git 仓库，无法自动快照。", file=sys.stderr)
        if force:
            print("   已指定 --force，跳过快照继续执行。", file=sys.stderr)
            return True
        print("   建议：先在项目根执行 `git init && git add . && git commit -m init`", file=sys.stderr)
        print("   或者使用 --force 明确接受无快照润色。", file=sys.stderr)
        return False

    code, out, err = _run_git(["status", "--porcelain"], git_root)
    if code != 0:
        print(f"⚠️  git status 失败: {err[:200]}", file=sys.stderr)
        return force

    if not out:
        print(f"✅ git 工作区干净（{git_root.name}），跳过快照")
        return True

    print("🗂️  发现未提交变更，创建润色前快照...")
    code, _, err = _run_git(["add", "-A"], git_root)
    if code != 0:
        print(f"⚠️  git add 失败: {err[:200]}", file=sys.stderr)
        return force
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"chore: pre-polish snapshot {stamp}"
    code, _, err = _run_git(["commit", "-m", msg], git_root)
    if code != 0:
        print(f"⚠️  git commit 失败（不阻断润色）: {err[:200]}", file=sys.stderr)
        return True
    print(f"✅ 快照已提交：{msg}")
    return True


# ==================== 单章润色 ====================
def polish_single_chapter(
    chap_num: int,
    chapters_dir: Path,
    python_path: str,
    style_prompt: str = "",
    min_words: int = 0,
    max_words: int = 0,
    max_wc_retries: int = 2,
    save_compare: bool = False,
    compare_dir: Path | None = None,
):
    """
    调用 hooks/polish_independent.py 执行单章润色。
    返回 (success, message, original_len, polished_len, issues)
    """
    chap_path = Path(chapters_dir) / chapter_filename(chap_num)
    if not chap_path.exists():
        return False, f"❌ 章节文件不存在：{chap_path.name}", 0, 0, []

    try:
        text = chap_path.read_text(encoding="utf-8")
        original_len = len(text)
    except Exception as e:
        return False, f"❌ 章节读取失败：{e}", 0, 0, []

    input_data = json.dumps(
        {
            "text": text,
            "chapter": chap_num,
            "style_prompt": style_prompt,
            "min_words": min_words,
            "max_words": max_words,
            "max_wc_retries": max_wc_retries,
        },
        ensure_ascii=False,
    )

    try:
        proc = subprocess.Popen(
            [str(python_path), str(POLISH_SCRIPT)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        stdout, stderr = proc.communicate(input=input_data, timeout=900)

        if proc.returncode != 0:
            return False, f"❌ 润色失败：{stderr[:300]}", original_len, 0, []

        result = json.loads(stdout)
        polished_text = result.get("polished", "")
        issues = result.get("issues", [])

        # 保存结果（原地覆盖）
        chap_path.write_text(polished_text, encoding="utf-8")

        # 对比报告（可选）
        if save_compare and compare_dir is not None:
            compare_dir.mkdir(parents=True, exist_ok=True)
            report = _build_compare_report(chap_num, text, polished_text, min_words, max_words)
            (compare_dir / f"{chap_path.stem}_compare.md").write_text(report, encoding="utf-8")

        msg = (
            f"✅ 第{chap_num}章润色完成 | 原字数：{original_len:,} → "
            f"润色后字数：{len(polished_text):,} | 问题数：{len(issues)}"
        )
        if issues:
            msg += f"\n⚠️  遗留问题：{'、'.join(issues[:3])}{' 等' if len(issues) > 3 else ''}"
        return True, msg, original_len, len(polished_text), issues
    except subprocess.TimeoutExpired:
        return False, f"⏱️  第{chap_num}章润色超时", original_len, 0, []
    except Exception as e:
        return False, f"❌ 执行异常：{e}", original_len, 0, []


def _count_chinese(text: str) -> int:
    return len(re.findall(r"[一-鿿㐀-䶿]", text))


def _build_compare_report(chap_num, original, polished, min_words, max_words):
    orig_wc = _count_chinese(original)
    polished_wc = _count_chinese(polished)
    delta = polished_wc - orig_wc
    pct = (delta / orig_wc * 100) if orig_wc else 0
    lines = [
        f"# 润色对比报告：第 {chap_num} 章",
        "",
        "| 指标 | 原文 | 润色后 |",
        "|------|------|--------|",
        f"| 中文字数 | {orig_wc} | {polished_wc} |",
        f"| 有效行数 | {len([l for l in original.splitlines() if l.strip()])} | {len([l for l in polished.splitlines() if l.strip()])} |",
    ]
    if min_words or max_words:
        target = f"{min_words}-{max_words}" if min_words and max_words else (f"≥{min_words}" if min_words else f"≤{max_words}")
        met = (not min_words or polished_wc >= min_words) and (not max_words or polished_wc <= max_words)
        lines.append(f"| 字数目标 | {target} | {'已达成' if met else '未达成'} |")
    lines += ["", "## 变更摘要", "", f"- 字数变化：{delta:+d} 字（{pct:+.1f}%）"]
    return "\n".join(lines)


# ==================== 进度追踪 ====================
class ProgressTracker:
    """断点续传：`.polish_progress.json` 落在 chapters_dir 平级。"""

    def __init__(self, chapters_dir: Path):
        self.file = chapters_dir.parent / ".polish_progress.json"
        self.data = self._load()

    def _load(self) -> dict:
        if self.file.exists():
            try:
                return json.loads(self.file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        return {"completed": [], "failed": {}}

    def save(self):
        self.file.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def is_done(self, chap_num: int) -> bool:
        return chap_num in self.data["completed"]

    def mark_done(self, chap_num: int):
        if chap_num not in self.data["completed"]:
            self.data["completed"].append(chap_num)
        self.data["failed"].pop(str(chap_num), None)
        self.save()

    def mark_failed(self, chap_num: int, reason: str):
        self.data["failed"][str(chap_num)] = reason
        self.save()

    def reset(self):
        self.data = {"completed": [], "failed": {}}
        self.save()


# ==================== 批量模式 ====================
def polish_range(
    start: int,
    end: int,
    chapters_dir: Path,
    python_path: str,
    style_prompt: str,
    min_words: int,
    max_words: int,
    max_wc_retries: int,
    save_compare: bool,
    reset_progress: bool,
    delay_seconds: int,
):
    progress = ProgressTracker(chapters_dir)
    if reset_progress:
        progress.reset()
        print("🔄 进度已重置")

    compare_dir = chapters_dir.parent / "polish_compare" if save_compare else None

    total = end - start + 1
    ok = skip = fail = 0
    stats = []

    print("=" * 60)
    print(f"批量润色 ch_{start:03d} → ch_{end:03d}（共 {total} 章）")
    print(f"章节目录：{chapters_dir}")
    print(f"进度文件：{progress.file}")
    print(f"字数范围：{min_words}-{max_words}（0 = 禁用循环）")
    print(f"文风覆盖：{'启用（' + str(len(style_prompt)) + ' 字符）' if style_prompt else '未启用（MCP 默认）'}")
    print("=" * 60)

    for i, ch in enumerate(range(start, end + 1), 1):
        if progress.is_done(ch):
            print(f"[{i}/{total}] ch_{ch:03d} 已完成，跳过")
            skip += 1
            continue

        print(f"[{i}/{total}] ch_{ch:03d} 处理中...")
        success, msg, orig_len, polished_len, issues = polish_single_chapter(
            ch,
            chapters_dir,
            python_path,
            style_prompt=style_prompt,
            min_words=min_words,
            max_words=max_words,
            max_wc_retries=max_wc_retries,
            save_compare=save_compare,
            compare_dir=compare_dir,
        )
        print(f"  {msg}")

        if success:
            progress.mark_done(ch)
            ok += 1
            stats.append({"chapter": ch, "orig": orig_len, "polished": polished_len, "issues": len(issues)})
        else:
            progress.mark_failed(ch, msg)
            fail += 1

        if i < total and delay_seconds > 0:
            time.sleep(delay_seconds)

    # 汇总
    print("\n" + "=" * 60)
    print(f"完成：OK={ok}  跳过={skip}  失败={fail}")
    if stats:
        total_orig = sum(s["orig"] for s in stats)
        total_pol = sum(s["polished"] for s in stats)
        avg = (total_pol / total_orig * 100) if total_orig else 0
        print(f"字数：原 {total_orig:,} → 润 {total_pol:,}（平均变化 {avg:.1f}%）")
    if progress.data["failed"]:
        print("失败列表：")
        for k, v in progress.data["failed"].items():
            print(f"  ch_{int(k):03d}: {v[:80]}")
    print("=" * 60)

    return 0 if fail == 0 else 1


# ==================== CLI ====================
def _parse_range(s: str) -> tuple[int, int]:
    """接受 '5' 或 '5-30' 两种格式"""
    if "-" in s:
        a, b = s.split("-", 1)
        return int(a), int(b)
    n = int(s)
    return n, n


def main():
    parser = argparse.ArgumentParser(
        description="novel-pipeline 官方逐章润色工具（前置 git 快照 + 断点续传 + 字数循环）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  单章：      python polish_chapter.py 101 D:\\Writer\\novel-project\\chapters
  范围批量：  python polish_chapter.py --range 1-30 D:\\Writer\\novel-project\\chapters
  带字数循环：python polish_chapter.py --range 1-30 chapters/ --min-words 2500 --max-words 3000
  带文风预设：python polish_chapter.py --range 1-30 chapters/ --style-file <writer>/references/presets/fanqie-quick-anti.md
        """,
    )
    parser.add_argument("chapter", nargs="?", help="单章模式：章节号（如 101）")
    parser.add_argument("chapters_dir", help="章节目录，如 D:\\Writer\\novel-project\\chapters")
    parser.add_argument("python_path", nargs="?", default=None, help="可选：MCP 子进程 Python 解释器")

    parser.add_argument("--range", dest="range_spec", help="批量模式：章节范围，如 1-30")
    parser.add_argument("--force", action="store_true", help="项目非 git repo 时也放行")
    parser.add_argument("--skip-snapshot", action="store_true", help="跳过 git 快照（仅在外层已保证时使用）")

    parser.add_argument("--style-file", help="加载文风预设文件作为 system prompt override")
    parser.add_argument("--min-words", type=int, default=0, help="字数下限（0 表示禁用循环）")
    parser.add_argument("--max-words", type=int, default=0, help="字数上限（0 表示禁用循环）")
    parser.add_argument("--max-wc-retries", type=int, default=2, help="字数不达标最多重试次数")

    parser.add_argument("--compare", action="store_true", help="输出润色前后对比报告到 polish_compare/")
    parser.add_argument("--reset", action="store_true", help="重置断点续传进度")
    parser.add_argument("--delay", type=int, default=2, help="章间延迟秒数（默认 2）")

    args = parser.parse_args()

    # 参数合法性
    if not args.range_spec and not args.chapter:
        parser.error("必须指定单章号或 --range 范围")

    chapters_dir = Path(args.chapters_dir).resolve()
    if not chapters_dir.exists():
        print(f"❌ 章节目录不存在：{chapters_dir}", file=sys.stderr)
        sys.exit(2)

    python_path = args.python_path or sys.executable

    # 加载文风预设
    style_prompt = ""
    if args.style_file:
        style_path = Path(args.style_file)
        if not style_path.exists():
            print(f"❌ 文风预设文件不存在：{style_path}", file=sys.stderr)
            sys.exit(2)
        style_prompt = style_path.read_text(encoding="utf-8").strip()
        print(f"📖 文风预设已加载：{style_path.name}（{len(style_prompt)} 字符）")

    # 前置 1：MCP 就绪
    if not ensure_mcps_ready():
        sys.exit(1)

    # 前置 2：git 快照
    if not args.skip_snapshot:
        if not ensure_git_snapshot(chapters_dir, force=args.force):
            sys.exit(2)

    # 分派模式
    if args.range_spec:
        start, end = _parse_range(args.range_spec)
        rc = polish_range(
            start, end, chapters_dir, python_path,
            style_prompt=style_prompt,
            min_words=args.min_words,
            max_words=args.max_words,
            max_wc_retries=args.max_wc_retries,
            save_compare=args.compare,
            reset_progress=args.reset,
            delay_seconds=args.delay,
        )
        sys.exit(rc)

    # 单章模式
    compare_dir = chapters_dir.parent / "polish_compare" if args.compare else None
    success, msg, *_ = polish_single_chapter(
        int(args.chapter),
        chapters_dir,
        python_path,
        style_prompt=style_prompt,
        min_words=args.min_words,
        max_words=args.max_words,
        max_wc_retries=args.max_wc_retries,
        save_compare=args.compare,
        compare_dir=compare_dir,
    )
    print(msg)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
