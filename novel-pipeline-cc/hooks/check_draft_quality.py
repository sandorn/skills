#!/usr/bin/env python3
"""
PostToolUse Hook: check_draft_quality
初稿生成后执行 3 轮自检（Layer 1 拦截）
触发: MCP:novel-deepseek.generate_draft 返回后

自检项:
  1. 基础结构检查: 字数、段落、格式
  2. 关键元素标记: 是否包含大纲中的关键剧情点关键词
  3. 禁区检测: 是否出现禁止内容（元叙事、分析语句）

注: 深度语义检查（OOC、设定冲突）由 Claude CLI 在 Layer 2 执行。
    Hook 负责可编程的结构性检查。
"""
import sys, json, os, re
from pathlib import Path

# 项目隔离：优先当前项目 state-files/，回退 Skill 模板
from utils import find_state_dir
STATE_DIR = find_state_dir()

# 禁止出现的元叙事关键词（表明模型在"分析"而非"写小说"）
META_BAN_LIST = [
    "本章展示了", "这章讲了", "以上是", "以下是",
    "总结一下", "需要注意的是", "值得关注的是",
    "本章小结", "本章重点", "这一章中",
    "this chapter", "summary", "in conclusion",
    "本章通过", "通过本章", "本章结尾",
    "（注：", "（注意：", "（提示：", "（说明：",
]


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return output(False, ["stdin 为空"], {"round1": False, "round2": False, "round3": False})

        data = json.loads(raw)

        # 提取参数
        call_input = data.get("input", data.get("arguments", {}))
        call_output = data.get("output", data.get("result", data.get("response", {})))

        # output 可能是字符串（工具直接返回值）或对象
        draft_text = ""
        if isinstance(call_output, str):
            draft_text = call_output
        elif isinstance(call_output, dict):
            draft_text = call_output.get("content", "") or call_output.get("text", "") or json.dumps(call_output, ensure_ascii=False)
        elif isinstance(call_output, list):
            # MCP 可能返回多部分
            for part in call_output:
                if isinstance(part, dict) and part.get("type") == "text":
                    draft_text += part.get("text", "")

        chapter_outline = call_input.get("chapter_outline", "")
        revision_instructions = call_input.get("revision_instructions", "")

        issues = []
        round1_pass, r1_issues = check_structure(draft_text)
        round2_pass, r2_issues = check_outline_coverage(draft_text, chapter_outline)
        round3_pass, r3_issues = check_banned_content(draft_text)

        all_issues = r1_issues + r2_issues + r3_issues
        all_pass = round1_pass and round2_pass and round3_pass

        # 如果是修订重试，降低标准
        if revision_instructions:
            all_pass = round1_pass and round2_pass  # 仅结构+大纲，放宽禁区

        return output(all_pass, all_issues, {
            "round1_structure": round1_pass,
            "round2_outline": round2_pass,
            "round3_banned": round3_pass,
            "draft_length": len(draft_text),
            "is_revision": bool(revision_instructions),
        })

    except json.JSONDecodeError as e:
        return output(False, [f"JSON 解析失败: {str(e)}"], {})
    except Exception as e:
        return output(False, [f"校验异常: {str(e)}"], {})


def check_structure(text: str) -> tuple[bool, list[str]]:
    """Round 1: 基础结构检查"""
    issues = []
    text_stripped = text.strip()

    # 字数检查：最低 2500 字，最高 4500 字
    if len(text_stripped) < 2500:
        issues.append(f"[结构] 正文字数不足 ({len(text_stripped)}字)，最低要求 2500 字")
    elif len(text_stripped) > 4500:
        issues.append(f"[结构] 正文字数超标 ({len(text_stripped)}字)，最高限制 4500 字")

    # 段落检查：至少 5 个段落
    paragraphs = [p for p in text_stripped.split("\n") if p.strip()]
    if len(paragraphs) < 5:
        issues.append(f"[结构] 段落数量过少 ({len(paragraphs)}段)，缺乏叙事层次")

    # 是否有章节标题标记
    if not any(kw in text_stripped[:200] for kw in ["第", "章"]):
        issues.append("[结构] 开头未找到章节标识（'第X章'）")

    return len(issues) == 0, issues


def check_outline_coverage(text: str, outline: str) -> tuple[bool, list[str]]:
    """Round 2: 大纲关键点覆盖检查（关键词级别）"""
    issues = []
    if not outline or not outline.strip():
        return True, []  # 无大纲则跳过

    # 从大纲中提取关键名词/动词短语（长度 >= 2 字的中文词）
    outline_keywords = extract_keywords(outline)

    missing = []
    text_lower = text
    for kw in outline_keywords[:10]:  # 最多检查前 10 个关键词
        if kw not in text_lower:
            missing.append(kw)

    if len(missing) >= len(outline_keywords) * 0.5:  # 缺失超过 50%
        issues.append(f"[大纲] 关键剧情点缺失率过高 ({len(missing)}/{len(outline_keywords)})，缺失: {missing[:5]}...")

    return len(issues) == 0, issues


def check_banned_content(text: str) -> tuple[bool, list[str]]:
    """Round 3: 禁区检测"""
    issues = []
    for banned in META_BAN_LIST:
        if banned in text:
            issues.append(f"[禁区] 发现元叙事: '{banned}'")

    # 检查是否以分析/总结开头（前 50 字）
    first_50 = text.strip()[:50]
    analysis_starts = ["好的", "根据", "以下是", "让我们", "我将会", "我会"]
    for s in analysis_starts:
        if first_50.startswith(s):
            issues.append(f"[禁区] 正文以分析语开头: '{s}'")
            break

    return len(issues) == 0, issues


def extract_keywords(text: str) -> list[str]:
    """从文本中提取中文关键词"""
    # 简单策略：提取引号内的内容 + 2-4字的连续中文片段
    keywords = []
    # 书名号/引号内容
    quoted = re.findall(r'[《「]([^》」]+)[》」]', text)
    keywords.extend(quoted)
    # 2-4 字中文片段（非停用词）
    words = re.findall(r'[一-鿿]{2,4}', text)
    # 去重，过滤停用词
    stopwords = {"需要", "注意", "这一章", "本章", "通过", "可以", "一个", "这个", "那个", "什么", "怎么", "为什么", "并且", "但是", "因此", "所以", "然后", "之后", "之前", "必须", "一定", "每个"}
    for w in words:
        if w not in stopwords and len(w) >= 2:
            keywords.append(w)
    return list(dict.fromkeys(keywords))  # 去重保序


def output(valid: bool, issues: list[str], details: dict) -> None:
    result = {
        "passed": valid,
        "issues": issues,
        "details": details,
        "hook": "check_draft_quality",
        "action_required": "retry" if not valid else "proceed",
    }
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
