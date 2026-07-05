#!/usr/bin/env python3
"""
PostToolUse Hook: audit_publishready
在润色完成后执行出版级文本审计（Layer 2 终检）
触发: 润色MCP polish_chapter 返回后
审计项:
  1. AI 腔检测 (audit_ai_sounding_prose)
  2. 可读性打分 + 热点定位 (find_hotspots)
  3. 与小说模板合规检查 (analyze_against_template)
  4. 链式调用 check_uno.py 做内容质量分析
所有处理在本地完成，不发送文本到第三方服务。
"""
import sys, json, subprocess, time
from pathlib import Path

TEMPLATE_FICTION = "fiction"
UNO_SCRIPT = Path(__file__).parent / "check_uno.py"
PYTHON = Path(r'C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe')
NPX = Path(r"C:\Program Files\nodejs\npx.cmd")


def call_publishready_tool(tool_name: str, arguments: dict, timeout: int = 60) -> dict:
    npx = str(NPX) if NPX.exists() else "npx"
    proc = subprocess.Popen(
        [npx, "-y", "@veldica/publishready-mcp"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1
    )
    try:
        init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                           "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                      "clientInfo": {"name": "novel-pipeline", "version": "2.0"}}})
        proc.stdin.write(init + "\n"); proc.stdin.flush(); time.sleep(0.5)
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"); proc.stdin.flush(); time.sleep(0.3)
        call = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                           "params": {"name": tool_name, "arguments": arguments}})
        proc.stdin.write(call + "\n"); proc.stdin.flush()
        stdout, stderr = proc.communicate(timeout=timeout)
        for line in stdout.split("\n"):
            line = line.strip()
            if not line: continue
            try:
                msg = json.loads(line)
                if "result" in msg and "content" in msg["result"]:
                    for c in msg["result"]["content"]:
                        if c.get("type") == "text": return {"success": True, "data": c["text"]}
                if "error" in msg: return {"success": False, "error": str(msg["error"])}
            except json.JSONDecodeError: continue
        return {"success": False, "error": f"No valid response. stderr: {stderr[:200]}"}
    except subprocess.TimeoutExpired: proc.kill(); return {"success": False, "error": f"Timeout ({timeout}s)"}
    except Exception as e: return {"success": False, "error": str(e)}
    finally:
        try: proc.kill()
        except: pass


def extract_text(data: str) -> str:
    if not data: return ""
    try: return json.dumps(json.loads(data), ensure_ascii=False, indent=2)
    except: return data


def call_uno(text: str) -> dict:
    if not UNO_SCRIPT.exists():
        return {"success": False, "error": f"check_uno.py not found: {UNO_SCRIPT}"}
    try:
        python = str(PYTHON) if PYTHON.exists() else sys.executable
        proc = subprocess.run(
            [python, str(UNO_SCRIPT)],
            input=json.dumps({"output": text}),
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return {"success": False, "error": proc.stderr[:200] or "no output"}
        return {"success": True, "data": json.loads(proc.stdout)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip(): return output(True, ["stdin 为空，跳过审计"], {"skipped": True})
        hook_input = json.loads(raw)
        tool_output = hook_input.get("output", hook_input.get("result", hook_input.get("response", {})))
        text = ""
        if isinstance(tool_output, str): text = tool_output
        elif isinstance(tool_output, dict): text = tool_output.get("content", "") or tool_output.get("text", "")
        if not text or len(text.strip()) < 500:
            return output(True, ["正文字数不足，跳过审计"], {"skipped": True})

        issues = []
        results = {}

        r = call_publishready_tool("audit_ai_sounding_prose", {"text": text})
        if r["success"]: results["ai_audit"] = extract_text(r["data"])
        else: issues.append(f"[publishready] AI腔检测失败: {r.get('error', '')}")

        r = call_publishready_tool("find_hotspots", {"text": text})
        if r["success"]: results["hotspots"] = extract_text(r["data"])
        else: issues.append(f"[publishready] 热点定位失败: {r.get('error', '')}")

        r = call_publishready_tool("analyze_against_template", {"text": text, "template_id": TEMPLATE_FICTION})
        if r["success"]: results["template_check"] = extract_text(r["data"])
        else: results["template_check"] = f"跳过: {r.get('error', '')}"

        r = call_uno(text)
        if r["success"]: results["uno_report"] = r["data"]
        else: issues.append(f"[uno] 跳过: {r.get('error', '')}")

        passed = len([i for i in issues if "[AI腔]" in i]) == 0
        return output(passed, issues, {"audit_results": results, "hook": "audit_publishready"})
    except json.JSONDecodeError as e: return output(False, [f"JSON 解析失败: {str(e)}"], {})
    except Exception as e: return output(False, [f"审计异常: {str(e)}"], {})


def output(valid: bool, issues: list, details: dict) -> None:
    print(json.dumps({"passed": valid, "issues": issues, "details": details,
                       "hook": "audit_publishready", "action_required": "review" if issues else "proceed"},
                      ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
