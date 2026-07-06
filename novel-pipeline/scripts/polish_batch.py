#!/usr/bin/env python3
"""
通用批量润色脚本 (支持自定义章节范围)
"""
import subprocess, json, sys, time, argparse
from pathlib import Path

# 动态获取路径（通用化，不写死）
SKILL_ROOT = Path(__file__).parent.parent
HOOKS_DIR = SKILL_ROOT / "hooks"
PYTHON = Path(sys.executable)  # 使用当前运行的Python解释器

def run_polish(chapter, chapters_dir, timeout=600):
    """执行单章独立润色"""
    print(f"\n{'='*60}")
    print(f"开始润色 ch{chapter:02d}")
    print(f"{'='*60}\n")

    # 读取原文
    path = Path(chapters_dir) / f"ch{chapter:02d}.md"
    if not path.exists():
        print(f"❌ 章节 {path} 不存在，跳过")
        return {"chapter": chapter, "status": "skipped", "error": "file_not_found"}

    text = path.read_text(encoding="utf-8")
    print(f"📖 原文字数: {len(text)} 字")

    # 构造输入 JSON
    inp = json.dumps({
        "text": text,
        "chapter": chapter
    }, ensure_ascii=False)

    # 执行 polish_independent.py
    script = HOOKS_DIR / "polish_independent.py"
    cmd = [str(PYTHON), str(script)]

    print(f"🚀 执行润色管线 (预计耗时 3-5 分钟)...\n")
    start = time.time()

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        stdout, stderr = proc.communicate(input=inp, timeout=timeout)
        elapsed = time.time() - start

        print(f"⏱️ 耗时: {elapsed:.1f} 秒\n")

        if proc.returncode != 0:
            print(f"❌ 脚本执行失败 (exit code: {proc.returncode})")
            print(f"STDERR:\n{stderr}")
            return {
                "chapter": chapter,
                "status": "failed",
                "error": f"script_failed: {stderr[:200]}"
            }

        # 解析输出
        result = json.loads(stdout)
        polished = result.get("polished", "")
        report = result.get("report", {})
        issues = result.get("issues", [])
        passed = result.get("passed", False)

        print(f"✅ 润色完成")
        print(f"   状态: {'通过' if passed else '有遗留问题'}")
        print(f"   字数: {len(text)} → {len(polished)} 字")
        print(f"   问题数: {len(issues)}")

        if issues:
            print(f"\n   遗留问题:")
            for i, issue in enumerate(issues[:5], 1):
                print(f"     {i}. {issue}")

        # 保存润色结果
        out_path = path
        out_path.write_text(polished, encoding="utf-8")

        print(f"\n💾 已保存到: {out_path}")

        return {
            "chapter": chapter,
            "status": "completed",
            "passed": passed,
            "original_len": len(text),
            "polished_len": len(polished),
            "issues_count": len(issues),
            "elapsed": elapsed,
            "issues": issues
        }

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        print(f"❌ 超时 ({elapsed:.1f}秒)")
        return {
            "chapter": chapter,
            "status": "timeout",
            "error": f"timeout after {elapsed:.1f}s"
        }
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ 异常: {e}")
        return {
            "chapter": chapter,
            "status": "error",
            "error": str(e),
            "elapsed": elapsed
        }

def main():
    parser = argparse.ArgumentParser(description="通用小说章节批量润色工具")
    parser.add_argument("--start", type=int, required=True, help="开始章节号 (如 1)")
    parser.add_argument("--end", type=int, required=True, help="结束章节号 (如 30)")
    parser.add_argument("--chapters-dir", type=str, default="./chapters", help="章节文件目录 (默认: ./chapters)")
    parser.add_argument("--output-report", type=str, default="./polish_batch_report.json", help="报告输出路径 (默认: ./polish_batch_report.json)")
    parser.add_argument("--timeout", type=int, default=600, help="单章润色超时时间(秒) (默认: 600)")
    parser.add_argument("--wait-interval", type=int, default=2, help="章节间等待时间(秒) (默认: 2)")
    
    args = parser.parse_args()

    print("="*60)
    print(f"批量润色任务 (ch{args.start:02d}-ch{args.end:02d})")
    print(f"章节目录: {Path(args.chapters_dir).resolve()}")
    print("="*60)

    results = []

    for ch in range(args.start, args.end + 1):
        result = run_polish(ch, args.chapters_dir, args.timeout)
        results.append(result)

        # 等待后处理下一章
        if ch < args.end:
            print(f"\n⏳ 等待 {args.wait_interval} 秒后处理下一章...\n")
            time.sleep(args.wait_interval)

    # 汇总报告
    print(f"\n{'='*60}")
    print("汇总报告")
    print(f"{'='*60}\n")

    total = len(results)
    completed = sum(1 for r in results if r["status"] == "completed")
    passed = sum(1 for r in results if r.get("passed", False))
    failed = sum(1 for r in results if r["status"] in ["failed", "timeout", "error"])
    skipped = sum(1 for r in results if r["status"] == "skipped")

    print(f"总计: {total} 章")
    print(f"✅ 完成: {completed} 章")
    print(f"   - 通过: {passed} 章")
    print(f"   - 遗留问题: {completed - passed} 章")
    print(f"❌ 失败: {failed} 章")
    print(f"⏭️ 跳过: {skipped} 章")

    # 统计字数变化
    total_orig = sum(r.get("original_len", 0) for r in results if r["status"] == "completed")
    total_polish = sum(r.get("polished_len", 0) for r in results if r["status"] == "completed")

    if total_orig > 0:
        avg_ratio = total_polish / total_orig * 100
        print(f"\n字数统计:")
        print(f"   原文总计: {total_orig:,} 字")
        print(f"   润色总计: {total_polish:,} 字")
        print(f"   平均变化: {avg_ratio:.1f}%")

    # 详细列表
    print(f"\n{'='*60}")
    print("详细结果")
    print(f"{'='*60}\n")

    for r in results:
        status_icon = {
            "completed": "✅",
            "passed": "✅",
            "failed": "❌",
            "timeout": "⏱️",
            "error": "💥",
            "skipped": "⏭️"
        }.get(r["status"], "❓")

        ch = r["chapter"]
        status = r["status"]
        elapsed = r.get("elapsed", 0)

        print(f"{status_icon} ch{ch:02d} | {status:10} | {elapsed:.1f}s", end="")

        if status == "completed":
            if r.get("issues_count", 0) > 0:
                print(f" | {r['issues_count']} 问题")
            else:
                print(f" | 无问题")

        elif status == "failed":
            print(f" | {r.get('error', '')[:50]}")

        else:
            print()

    # 导出 JSON
    output_path = Path(args.output_report).resolve()
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n📄 详细报告已保存: {output_path}")

if __name__ == "__main__":
    main()