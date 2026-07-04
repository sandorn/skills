#!/usr/bin/env python3
"""
PostToolUse Hook: check_uno
在初稿生成后执行内容质量分析（uno MCP 引擎）
触发: generate_draft 返回后 / polish_chapter 返回后

用途:
  1. analyze_text 分析剧情节奏、行文密度、感官细节等
  2. 为 Agent 提供质量报告，辅助修订决策

uno 服务器路径: C:\\Users\\Administrator\\.litellm\\servers\\uno-mcp\\dist\\index.js
"""
import sys, json, subprocess, time
from pathlib import Path

UNO_SERVER = Path(r"C:\Users\Administrator\.litellm\servers\uno-mcp\dist\index.js")
NODE = Path(r"C:\Program Files\nodejs\node.exe")


def call_uno_tool(tool_name: str, arguments: dict, timeout: int = 30) -> dict:
    """通过 node 子进程调用 uno MCP 工具"""
    if not UNO_SERVER.exists():
        return {"success": False, "error": f"uno server not found: {UNO_SERVER}"}

    proc = subprocess.Popen(
        [str(NODE), str(UNO_SERVER)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1,
    )
    try:
        # MCP 初始化
        init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                           "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                      "clientInfo": {"name": "novel-pipeline", "version": "2.0"}}})
        proc.stdin.write(init + "\n"); proc.stdin.flush()
        time.sleep(0.3)

        notified = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
        proc.stdin.write(notified + "\n"); proc.stdin.flush()
        time.sleep(0.3)

        # 调用工具
        call = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                           "params": {"name": tool_name, "arguments": arguments}})
        proc.stdin.write(call + "\n"); proc.stdin.flush()

        stdout, stderr = proc.communicate(timeout=timeout)

        for line in stdout.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                # 只匹配 tools/call 的响应 (id=2)
                if msg.get("id") == 2 and "result" in msg:
                    content = msg["result"].get("content", [])
                    for c in content:
                        if c.get("type") == "text":
                            return {"success": True, "data": c["text"]}
                    return {"success": True, "data": msg["result"]}
                if msg.get("id") == 2 and "error" in msg:
                    return {"success": False, "error": str(msg["error"])}
            except json.JSONDecodeError:
                continue
        return {"success": False, "error": f"No valid response. stderr: {stderr[:200]}"}
    except subprocess.TimeoutExpired:
        proc.kill()
        return {"success": False, "error": f"Timeout ({timeout}s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        try:
            proc.kill()
        except:
            pass


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return output(True, ["stdin 为空，跳过分析"], {"skipped": True})

        hook_input = json.loads(raw)
        tool_output = hook_input.get("output", hook_input.get("result", hook_input.get("response", {})))

        # 提取正文文本
        text = ""
        if isinstance(tool_output, str):
            text = tool_output
        elif isinstance(tool_output, dict):
            text = tool_output.get("content", "") or tool_output.get("text", "")

        if not text or len(text.strip()) < 500:
            return output(True, ["正文字数不足，跳过分析"], {"skipped": True, "reason": "text too short"})

        issues = []
        analysis = {}

        # 调用 uno analyze_text
        result = call_uno_tool("analyze_text", {"text": text})
        if result["success"]:
            analysis["uno_report"] = result["data"]
        else:
            issues.append(f"[uno] analyze_text 失败: {result.get('error', 'unknown')}")

        # 汇总
        passed = len(issues) == 0
        return output(passed, issues, {"analysis": analysis, "hook": "check_uno"})

    except json.JSONDecodeError as e:
        return output(False, [f"JSON 解析失败: {str(e)}"], {})
    except Exception as e:
        return output(False, [f"uno 检查异常: {str(e)}"], {})


def output(valid: bool, issues: list[str], details: dict) -> None:
    result = {
        "passed": valid,
        "issues": issues,
        "details": details,
        "hook": "check_uno",
        "action_required": "review" if issues else "proceed",
    }
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
