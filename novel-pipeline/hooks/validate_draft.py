#!/usr/bin/env python3
"""
PreToolUse Hook: validate_draft
校验初稿生成调用参数完整性（Layer 1 拦截）
触发: 初稿生成MCP generate_draft 调用前
"""
import sys, json

REQUIRED_PARAMS = ["global_setting", "chapter_outline", "chapter_number"]
OPTIONAL_PARAMS = ["revision_instructions"]

def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return output(False, ["stdin 为空，无法校验"])

        data = json.loads(raw)

        # 兼容多种输入格式
        args = data.get("arguments", data.get("params", data))

        errors = []
        for p in REQUIRED_PARAMS:
            val = args.get(p)
            if val is None:
                errors.append(f"缺少必填参数: {p}")
            elif p == "global_setting" and (not isinstance(val, str) or not val.strip()):
                errors.append(f"参数 {p} 为空字符串")
            elif p == "chapter_outline" and (not isinstance(val, str) or not val.strip()):
                errors.append(f"参数 {p} 为空字符串")
            elif p == "chapter_number" and not isinstance(val, (int, float)):
                errors.append(f"参数 {p} 不是数字类型，当前值: {val}")

        # 检查大纲最小长度（至少 10 字才可能有实质内容）
        outline = args.get("chapter_outline", "")
        if isinstance(outline, str) and len(outline.strip()) < 10:
            errors.append("chapter_outline 过短（<10字），内容不足以指导生成")

        return output(len(errors) == 0, errors)

    except json.JSONDecodeError as e:
        return output(False, [f"JSON 解析失败: {str(e)}"])
    except Exception as e:
        return output(False, [f"校验异常: {str(e)}"])


def output(valid: bool, errors: list[str]) -> None:
    result = {"valid": valid, "errors": errors, "hook": "validate_draft"}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
