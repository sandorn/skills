#!/usr/bin/env python3
"""
独立润色管线：直接调用 novel-doubao 润色
流程:
  1. 读文本
  2. novel-doubao 润色
  3. 完整性检查
  4. 完成输出
"""
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, Tuple, List

HOOKS_DIR = Path(__file__).parent
SKILL_ROOT = HOOKS_DIR.parent

# 从共享工具加载
sys.path.insert(0, str(HOOKS_DIR))
from utils import HERMES_PYTHON, DEFAULT_CHAPTERS_DIR, BaseMCPClient, chapter_filename, logger

# 指向 Skill 内的 MCP 目录
DOUBAO = SKILL_ROOT / "mcp" / "novel-doubao" / "doubao_server.py"
DOUBAO_CWD = SKILL_ROOT / "mcp" / "novel-doubao"


def doubao_polish(text: str) -> Dict[str, Any]:
    """
    调用 novel-doubao MCP 进行润色
    :param text: 要润色的原文
    :return: 包含 success/data 或 error 的结果字典
    """
    if not DOUBAO.exists():
        return {"success": False, "error": f"doubao server not found: {DOUBAO}"}

    python = str(HERMES_PYTHON) if HERMES_PYTHON.exists() else sys.executable

    with BaseMCPClient([python, str(DOUBAO)], timeout=300, cwd=DOUBAO_CWD) as client:
        return client.call_tool("polish_chapter", {
            "chapter_characters": "",
            "draft_text": text,
            "chapter_mood_tone": "中性"
        })


def check_integrity(original: str, polished: str) -> Tuple[bool, List[str]]:
    """
    完整性检查：检查润色后的内容是否符合预期
    :param original: 原文
    :param polished: 润色后的文本
    :return: (是否通过, 问题列表)
    """
    issues: List[str] = []

    # 检查结尾是否有终结标点（中英文标点通用）
    END_OK = re.compile(r'[。！？…"”」\)）】\]]\s*$')
    polished_stripped = polished.rstrip()
    if not END_OK.search(polished_stripped):
        issues.append("结尾无终结标点(可能截断)")

    # 检查篇幅变化比例
    ratio = len(polished) / len(original) if original else 0
    if ratio < 0.7:
        issues.append(f"篇幅缩水{(1-ratio)*100:.0f}%")
    elif ratio > 1.5:
        issues.append(f"篇幅暴涨{(ratio-1)*100:.0f}%")

    return len(issues) == 0, issues


def output(data: Dict[str, Any]) -> None:
    """输出 JSON 结果并退出"""
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(0)


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        output({"error": "stdin 为空"})

    # 解析输入
    try:
        inp = json.loads(raw) if raw.startswith("{") else {"text": raw}
    except json.JSONDecodeError:
        inp = {"text": raw}

    text = inp.get("text", inp.get("output", ""))
    ch = inp.get("chapter", inp.get("ch", 0))

    # 如果没有提供文本，尝试从文件读取
    if not text and ch:
        p = DEFAULT_CHAPTERS_DIR / chapter_filename(ch)
        if p.exists():
            text = p.read_text(encoding="utf-8")
        else:
            output({"error": f"章节不存在: {p}"})

    if len(text.strip()) < 500:
        output({"error": "正文字数不足"})

    report: Dict[str, Any] = {}
    issues: List[str] = []

    print("[1/3] 调用 novel-doubao 润色...", file=sys.stderr)
    result = doubao_polish(text)

    if result.get("success"):
        polished = result.get("data", "")
        if polished.startswith("ERROR_TRUNCATED:") or polished.startswith("ERROR:"):
            issues.append(f"doubao 返回错误: {polished[:100]}")
            report["doubao_result"] = "错误，保留原文"
            polished = text
        else:
            report["doubao_result"] = f"成功，{len(polished)}字"
    else:
        polished = text
        error_msg = result.get("error", "未知错误")
        issues.append(f"doubao 调用失败: {error_msg[:100]}")
        report["doubao_result"] = f"失败，保留原文: {error_msg[:100]}"

    # 完整性检查
    if polished != text:
        print("[2/3] 执行完整性检查...", file=sys.stderr)
        integrity_ok, integrity_issues = check_integrity(text, polished)
        if not integrity_ok:
            issues.extend(integrity_issues)
            report["integrity_check"] = "FAIL: " + "; ".join(integrity_issues)
            report["doubao_result"] += " [完整性检查失败，保留原文]"
            polished = text
        else:
            report["integrity_check"] = "PASS"

    print("[3/3] 完成", file=sys.stderr)

    output({
        "polished": polished,
        "report": report,
        "issues": issues,
        "passed": len(issues) == 0,
        "hook": "polish_independent"
    })


if __name__ == "__main__":
    main()
