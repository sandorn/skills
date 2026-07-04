#!/usr/bin/env python3
"""全章节批量审查脚本：OOC检查/违禁词检测/出版级审计
自动识别当前项目根目录，适配Windows/WSL双环境
用法：在小说项目根目录执行 python <Skill路径>/scripts/batch_audit.py
"""
import json
import asyncio
import sys
from pathlib import Path

# 自动识别路径
SKILL_DIR = Path(__file__).resolve().parent.parent
HOOK_DIR = SKILL_DIR / "hooks"
# 使用当前Python解释器，自动适配环境
PYTHON_PATH = sys.executable

# 自动向上查找项目根目录（包含novel-pipeline.json的目录）
PROJECT_ROOT = None
cwd = Path.cwd()
for p in [cwd] + list(cwd.parents)[:5]:
    if (p / "novel-pipeline.json").exists():
        PROJECT_ROOT = p
        break

if not PROJECT_ROOT:
    print("❌ 错误：未找到项目标记文件 novel-pipeline.json，请在小说项目根目录执行此脚本")
    sys.exit(1)

# 自动识别章节目录
config = json.loads((PROJECT_ROOT / "novel-pipeline.json").read_text(encoding="utf-8"))
CHAPTER_DIR = PROJECT_ROOT / config.get("chapter_dir", "./chapters/")
CHAPTER_DIR.mkdir(parents=True, exist_ok=True)

async def run_hook(script_name, input_data):
    """执行hook脚本并返回结果"""
    proc = await asyncio.create_subprocess_exec(
        str(PYTHON_PATH), 
        str(HOOK_DIR / script_name),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate(input=json.dumps(input_data).encode("utf-8"))
    if proc.returncode != 0:
        return {"passed": False, "error": stderr.decode("utf-8", errors="ignore")}
    try:
        return json.loads(stdout.decode("utf-8"))
    except json.JSONDecodeError:
        return {"passed": False, "error": "Invalid JSON output", "raw": stdout.decode("utf-8", errors="ignore")}

async def audit_chapter(chapter_path: Path):
    """单章节全维度审查"""
    # 自动识别章节编号
    stem = chapter_path.stem
    ch_num = 0
    # 匹配 ch1.md / 第1章.md / chapter1.md 等格式
    import re
    num_match = re.search(r'(\d+)', stem)
    if num_match:
        ch_num = int(num_match.group(1))
    
    text = chapter_path.read_text(encoding="utf-8")
    
    print(f"[审查] 第{ch_num}章({chapter_path.name}): {len(text)}字符")
    
    results = {
        "chapter": ch_num,
        "filename": chapter_path.name,
        "path": str(chapter_path),
        "length": len(text),
        "checks": {}
    }
    
    # 1. 出版级审计
    audit_res = await run_hook("audit_publishready.py", {"output": text})
    results["checks"]["publishready"] = audit_res
    
    # 2. OOC人设检查
    ooc_res = await run_hook("check_ooc_firstory.py", {
        "input": {"chapter_number": ch_num},
        "output": text
    })
    results["checks"]["ooc"] = ooc_res
    
    # 3. 红线内容检查
    redline_res = await run_hook("audit_polish.py", {
        "input": {"draft_text": text, "chapter_number": ch_num},
        "output": text
    })
    results["checks"]["redline"] = redline_res
    
    # 4. 基础质量检查
    quality_res = await run_hook("check_draft_quality.py", {
        "input": {"chapter_outline": "", "chapter_number": ch_num},
        "output": text
    })
    results["checks"]["quality"] = quality_res
    
    # 汇总结果
    results["all_passed"] = all(
        c.get("passed", False) for c in results["checks"].values()
    )
    
    if not results["all_passed"]:
        print(f"⚠ 第{ch_num}章 存在问题:")
        for name, res in results["checks"].items():
            if not res.get("passed", False):
                issues = res.get('issues', res.get('violations', res.get('error', '未知错误')))
                print(f"  - {name}: {issues}")
    
    return results

async def main():
    # 获取所有章节文件，支持.md/.txt格式
    chapters = []
    for ext in ["*.md", "*.txt"]:
        chapters.extend(CHAPTER_DIR.glob(ext))
    # 按章节编号排序
    def extract_num(p):
        import re
        m = re.search(r'(\d+)', p.stem)
        return int(m.group(1)) if m else 0
    chapters = sorted(chapters, key=extract_num)
    
    if not chapters:
        print(f"❌ 错误：在 {CHAPTER_DIR} 目录下未找到任何章节文件(.md/.txt)")
        sys.exit(1)
    
    print(f"=== 启动全章节审查 共{len(chapters)}章 ===")
    print(f"项目路径: {PROJECT_ROOT}")
    print(f"检查维度: 基础质量 | OOC人设合规 | 红线内容检测 | 出版级质量审计\n")
    
    all_results = []
    passed_count = 0
    failed_count = 0
    
    for chap in chapters:
        res = await audit_chapter(chap)
        all_results.append(res)
        if res["all_passed"]:
            passed_count += 1
        else:
            failed_count += 1
    
    # 生成汇总报告
    report = {
        "summary": {
            "total_chapters": len(all_results),
            "passed": passed_count,
            "failed": failed_count,
            "pass_rate": f"{passed_count/len(all_results)*100:.1f}%"
        },
        "failed_chapters": [
            {"chapter": r["chapter"], "filename": r["filename"], "issues": [
                f"{k}: {v.get('issues', v.get('violations', v.get('error', [])))}"
                for k, v in r["checks"].items() if not v.get("passed", False)
            ]}
            for r in all_results if not r["all_passed"]
        ]
    }
    
    # 保存报告到项目scripts/或根目录
    report_dir = PROJECT_ROOT / "scripts"
    report_dir.mkdir(exist_ok=True)
    report_path = report_dir / "audit_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print(f"\n{'='*60}")
    print(f"审查完成: 总{len(all_results)}章 | 通过{passed_count}章 | 失败{failed_count}章 | 通过率{passed_count/len(all_results)*100:.1f}%")
    print(f"详细报告已保存至: {report_path}")
    if failed_count > 0:
        print(f"问题章节清单: {[c['chapter'] for c in report['failed_chapters']]}")

if __name__ == "__main__":
    asyncio.run(main())
