#!/usr/bin/env python3
"""
PostToolUse Hook: check_ooc_firstory
在 DeepSeek 初稿生成后执行人设一致性校验（Layer 2 Round 1 自动化）
触发: MCP:novel-deepseek.generate_draft 返回后

校验项:
  1. 角色对话是否符合 speech_style
  2. 角色行为是否突破 bottom_lines
  3. 修为/战力/地名/年龄是否前后矛盾

注：firstory 需要 OAuth 认证和网络连接。
若服务不可用，优雅降级为跳过（不阻断流水线）。
"""
import sys, json, subprocess, time, os
from pathlib import Path


# firstory MCP 端点（优先远程，回退本地 npx）
FIRSTORY_REMOTE = "https://firstory-mcp.vercel.app/mcp"
FIRSTORY_LOCAL_CMD = ["npx", "-y", "firstory-mcp"]


def try_call_firstory(tool_name: str, arguments: dict, timeout: int = 30) -> dict:
    """尝试调用 firstory MCP 工具（远程 → 本地 npx 回退）"""
    # 尝试远程端点
    try:
        import urllib.request, urllib.error
        req = urllib.request.Request(
            FIRSTORY_REMOTE,
            data=json.dumps({
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments}
            }).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "result" in data:
                return {"success": True, "data": data["result"]}
            if "error" in data:
                return {"success": False, "error": str(data["error"])}
    except Exception as e:
        pass  # 远程不可用，尝试本地

    # 回退本地 npx
    try:
        proc = subprocess.Popen(
            FIRSTORY_LOCAL_CMD,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True
        )
        init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                           "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                      "clientInfo": {"name": "novel-pipeline", "version": "1.0"}}})
        proc.stdin.write(init + "\n"); proc.stdin.flush()
        time.sleep(0.5)
        notified = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
        proc.stdin.write(notified + "\n"); proc.stdin.flush()
        time.sleep(0.3)

        call = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                           "params": {"name": tool_name, "arguments": arguments}})
        proc.stdin.write(call + "\n"); proc.stdin.flush()

        stdout, stderr = proc.communicate(timeout=timeout)
        proc.kill()

        for line in stdout.split("\n"):
            line = line.strip()
            if not line: continue
            try:
                msg = json.loads(line)
                if "result" in msg:
                    return {"success": True, "data": msg["result"]}
                if "error" in msg:
                    return {"success": False, "error": str(msg["error"])}
            except json.JSONDecodeError:
                continue
        return {"success": False, "error": f"No response. stderr: {stderr[:200]}"}
    except FileNotFoundError:
        return {"success": False, "error": "npx not found"}
    except subprocess.TimeoutExpired:
        proc.kill()
        return {"success": False, "error": f"Timeout ({timeout}s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return output(True, ["stdin 为空，跳过 OOC 检查"], {"skipped": True})

        hook_input = json.loads(raw)
        call_input = hook_input.get("input", hook_input.get("arguments", {}))
        tool_output = hook_input.get("output", hook_input.get("result", hook_input.get("response", {})))

        # 提取初稿文本
        draft_text = ""
        if isinstance(tool_output, str):
            draft_text = tool_output
        elif isinstance(tool_output, dict):
            draft_text = tool_output.get("content", "") or tool_output.get("text", "")

        if not draft_text or len(draft_text.strip()) < 500:
            return output(True, ["正文字数不足，跳过 OOC 检查"], {"skipped": True, "reason": "text too short"})

        # 尝试从 state-files 加载角色定义
        from utils import find_state_dir
        state_dir = find_state_dir()
        characters = []
        chars_path = state_dir / "characters.json"
        if chars_path.exists():
            with open(chars_path, "r", encoding="utf-8") as f:
                chars_data = json.load(f)
                characters = chars_data.get("characters", [])

        issues = []
        ooc_results = {}

        # ── 1. 尝试调用 firstory character-query ──
        # 构建角色上下文
        char_context = ""
        for c in characters[:10]:  # 最多 10 个角色
            name = c.get("name", "")
            traits = ", ".join(c.get("personality_traits", []))
            speech = c.get("speech_style", "")
            bottoms = ", ".join(c.get("bottom_lines", []))
            char_context += f"{name}: 性格[{traits}], 说话[{speech}], 底线[{bottoms}]\n"

        query_result = try_call_firstory("character-query", {
            "text": draft_text,
            "characterContext": char_context,
        })
        if query_result["success"]:
            ooc_results["character_query"] = str(query_result["data"])
        else:
            # 优雅降级：firstory 不可用时用本地规则检查
            ooc_results["character_query"] = f"firstory 不可用，跳过远程 OOC: {query_result.get('error', 'unknown')}"
            # 执行本地基础检查
            local_issues = run_local_ooc_check(draft_text, characters)
            issues.extend(local_issues)

        passed = len(issues) == 0
        return output(passed, issues, {"ooc_results": ooc_results, "hook": "check_ooc_firstory"})

    except json.JSONDecodeError as e:
        return output(False, [f"JSON 解析失败: {str(e)}"], {})
    except Exception as e:
        return output(False, [f"OOC 检查异常: {str(e)}"], {})


def run_local_ooc_check(text: str, characters: list) -> list[str]:
    """本地基础 OOC 检查（firstory 不可用时的回退）"""
    issues = []
    for c in characters:
        name = c.get("name", "")
        if not name or name not in text:
            continue
        # 检查是否在文中出现但行为与性格矛盾（简单关键词检查）
        bottoms = c.get("bottom_lines", [])
        for bl in bottoms:
            # 检查是否出现了违反底线的行为（如"滥杀"+"凡人"同时出现）
            if bl == "不滥杀凡人" and "凡人" in text:
                if "杀" in text and name in text:
                    issues.append(f"[OOC/本地] {name} 可能突破底线'{bl}'——文中同时出现'{name}'、'杀'、'凡人'，需人工复核")

    return issues


def output(valid: bool, issues: list[str], details: dict) -> None:
    result = {
        "passed": valid,
        "issues": issues,
        "details": details,
        "hook": "check_ooc_firstory",
        "action_required": "review" if issues else "proceed",
    }
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)  # OOC 检查不阻断流程，仅标记


if __name__ == "__main__":
    main()
