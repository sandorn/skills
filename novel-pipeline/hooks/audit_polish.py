#!/usr/bin/env python3
"""
PostToolUse Hook: audit_polish
润色结果审计——检查是否违反 RED LINE（Layer 1 拦截）
触发: 润色MCP polish_chapter 返回后

RED LINE 检查:
  1. 关键剧情节点是否仍存在于润色文本中
  2. 对话行数是否一致（防止删改对话）
  3. 伏笔标记是否未被删除
  4. 段落数量是否合理变化（润色不应大幅增删段落）

注: 本 Hook 做结构性比对。深层语义篡改由 Agent Layer 2 语义检查执行。
"""
import sys, json, re
from difflib import SequenceMatcher


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return output(False, ["stdin 为空"], {})

        data = json.loads(raw)

        call_input = data.get("input", data.get("arguments", {}))
        call_output = data.get("output", data.get("result", data.get("response", {})))

        draft_text = call_input.get("draft_text", "")
        if not draft_text:
            return output(False, ["未找到原始草稿 draft_text"], {})

        polished_text = ""
        if isinstance(call_output, str):
            polished_text = call_output
        elif isinstance(call_output, dict):
            polished_text = call_output.get("content", "") or call_output.get("text", "")
        elif isinstance(call_output, list):
            for part in call_output:
                if isinstance(part, dict) and part.get("type") == "text":
                    polished_text += part.get("text", "")

        if not polished_text:
            return output(False, ["润色结果为空"], {})

        violations = []
        checks = {}

        # 检查 1: 整体相似度（润色不应导致文本完全不同）
        sim = SequenceMatcher(None, draft_text, polished_text).ratio()
        checks["similarity"] = round(sim, 3)
        if sim < 0.3:
            violations.append(f"[RED LINE] 润色后文本与原文相似度过低 ({sim:.1%})，疑似内容被改写")

        # 检查 2: 对话行数比对（支持中英文引号）
        draft_dialogue_count = count_dialogue_lines(draft_text)
        polished_dialogue_count = count_dialogue_lines(polished_text)
        checks["dialogue_count"] = {"original": draft_dialogue_count, "polished": polished_dialogue_count}
        if draft_dialogue_count > 0:
            ratio = polished_dialogue_count / draft_dialogue_count
            if ratio < 0.5 or ratio > 2.0:
                violations.append(f"[RED LINE] 对话行数异常变化 ({draft_dialogue_count}→{polished_dialogue_count})，疑似增删对话")

        # 检查 3: 伏笔标记保留
        foreshadowing_marks = extract_foreshadowing_marks(draft_text)
        checks["foreshadowing_marks_found"] = len(foreshadowing_marks)
        if foreshadowing_marks:
            missing = [m for m in foreshadowing_marks if m not in polished_text]
            if missing:
                violations.append(f"[RED LINE] 伏笔标记丢失 ({len(missing)}处): {missing[:3]}...")

        # 检查 4: 段落数量合理范围
        draft_paras = len([p for p in draft_text.split("\n") if p.strip()])
        polished_paras = len([p for p in polished_text.split("\n") if p.strip()])
        checks["paragraph_count"] = {"original": draft_paras, "polished": polished_paras}
        if draft_paras > 5:
            ratio = polished_paras / draft_paras
            if ratio < 0.3 or ratio > 3.0:
                violations.append(f"[RED LINE] 段落数量异常变化 ({draft_paras}→{polished_paras})")

        passed = len(violations) == 0
        return output(passed, violations, checks)

    except json.JSONDecodeError as e:
        return output(False, [f"JSON 解析失败: {str(e)}"], {})
    except Exception as e:
        return output(False, [f"审计异常: {str(e)}"], {})


def count_dialogue_lines(text: str) -> int:
    """统计对话行数，支持中文「」和英文""引号"""
    count = len(re.findall(r'[「"].+?[」"]', text))
    return count


def extract_foreshadowing_marks(text: str) -> list[str]:
    """
    提取伏笔标记。
    伏笔通常以特殊标记识别:
    - 【伏笔】/【埋伏笔】标记
    - 特殊物品/人物描述中的暗示性句子
    - 包含"似乎"/"隐约"/"莫名"等伏笔关键词的句子
    """
    marks = []
    # 显式标记
    for m in re.findall(r'【[伏埋].*?】', text):
        marks.append(m)
    # 伏笔关键词句子（取前 30 字作为标识）
    for m in re.findall(r'[^。！？\n]{0,15}(?:似乎|隐约|莫名|不对劲|诡异|古怪)[^。！？\n]{0,15}', text):
        marks.append(m[:40])
    return marks[:20]  # 最多 20 个标记


def output(passed: bool, issues: list[str], checks: dict) -> None:
    result = {
        "passed": passed,
        "violations": issues,
        "checks": checks,
        "hook": "audit_polish",
        "action_required": "retry" if not passed else "proceed",
    }
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
