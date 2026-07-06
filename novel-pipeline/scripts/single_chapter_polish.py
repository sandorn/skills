#!/usr/bin/env python3
"""
通用单章润色脚本（顺序润色模式专用）
优势：实时反馈、无前端卡顿、风险可控、可随时中断
适用场景：用户偏好逐章处理、避免长时间后台进程、小范围润色验证
"""
import sys
import json
import subprocess
import argparse
from pathlib import Path

# 动态获取Skill根目录
SKILL_ROOT = Path(__file__).parent.parent
HOOKS_DIR = SKILL_ROOT / "hooks"
PYTHON_PATH = Path(sys.executable)
POLISH_SCRIPT = HOOKS_DIR / "polish_independent.py"

def main():
    parser = argparse.ArgumentParser(description="单章顺序润色工具")
    parser.add_argument("chapter", type=int, help="要润色的章节号，如 61")
    parser.add_argument("--chapters-dir", type=str, required=True, help="章节文件所在目录，如 D:\Writer\novel-project\chapters")
    parser.add_argument("--timeout", type=int, default=600, help="单章润色超时时间（秒），默认 600")
    args = parser.parse_args()

    # 构造章节路径
    chap_path = Path(args.chapters_dir) / f"ch{args.chapter}.md"
    if not chap_path.exists():
        print(f"❌ 章节文件不存在：{chap_path}")
        return 1

    # 读取原文
    with open(chap_path, 'r', encoding='utf-8') as f:
        text = f.read()
    original_len = len(text)
    print(f"📄 开始润色 ch{args.chapter}，原文字数：{original_len:,}")

    # 构造输入数据
    input_data = json.dumps({
        "text": text,
        "chapter": args.chapter
    }, ensure_ascii=False)

    # 调用润色核心脚本
    try:
        proc = subprocess.Popen(
            [str(PYTHON_PATH), str(POLISH_SCRIPT)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        stdout, stderr = proc.communicate(input=input_data, timeout=args.timeout)

        if proc.returncode != 0:
            print(f"❌ ch{args.chapter} 润色失败，错误信息：{stderr[:200]}")
            return 1

        # 解析结果
        result = json.loads(stdout)
        polished_text = result.get("polished", "")
        issues = result.get("issues", [])
        passed = result.get("passed", False)

        # 保存润色结果
        with open(chap_path, 'w', encoding='utf-8') as f:
            f.write(polished_text)

        # 输出结果
        status = "✅ 润色通过" if passed else "⚠️ 润色完成但有遗留问题"
        print(f"{status} | ch{args.chapter} | 润色后字数：{len(polished_text):,} | 问题数：{len(issues)}")
        if issues:
            issue_preview = "、".join(issues[:3]) + (" 等" if len(issues) > 3 else "")
            print(f"⚠️  遗留问题：{issue_preview}")
        return 0

    except subprocess.TimeoutExpired:
        print(f"⏱️  ch{args.chapter} 润色超时（超过{args.timeout}秒）")
        return 1
    except Exception as e:
        print(f"💥 ch{args.chapter} 执行异常：{str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
