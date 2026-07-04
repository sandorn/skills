#!/usr/bin/env python3
"""
PreToolUse Hook: validate_polish
校验润色调用参数完整性（Layer 1 拦截）
触发: 润色MCP polish_chapter 调用前
"""
import sys, json

REQUIRED_PARAMS = ["chapter_characters", "draft_text"]
OPTIONAL_PARAMS = ["chapter_mood_tone"]

def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return output(False, ["stdin 为空，无法校验"])

        data = json.loads(raw)
        args = data.get("arguments", data.get("params", data))

        errors = []
        for p in REQUIRED_PARAMS:
            val = args.get(p)
            if val is None:
                errors.append(f"缺少必填参数: {p}")
            elif not isinstance(val, str) or not val.strip():
                errors.append(f"参数 {p} 为空字符串")

        # draft_text 最小长度检查（至少 200 字才值得润色）
        draft = args.get("draft_text", "")
        if isinstance(draft, str) and len(draft.strip()) < 200:
            errors.append(f"draft_text 过短（{len(draft.strip())}字），可能内容不完整")

        return output(len(errors) == 0, errors)

    except json.JSONDecodeError as e:
        return output(False, [f"JSON 解析失败: {str(e)}"])
    except Exception as e:
        return output(False, [f"校验异常: {str(e)}"])


def output(valid: bool, errors: list[str]) -> None:
    result = {"valid": valid, "errors": errors, "hook": "validate_polish"}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
