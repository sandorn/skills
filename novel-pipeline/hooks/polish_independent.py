#!/usr/bin/env python3
"""
独立润色管线：publishready 审计 + uno 修复 + publishready 复检

流程:
  1. 读取正文
  2. publishready: analyze + audit_ai + hotspots + suggest_revision
  3. uno: analyze_text
  4. 综合评估，确定修复方向
  5. uno: custom_enhance_text 按需修复
  6. publishready: compare_text_versions 复检
  7. 输出润色后文本 + 报告

用法:
  python hooks/polish_independent.py < chapter_text.json
  输入: {"text": "..."} 或 {"output": "..."} 或 {"chapter": 123}
  输出: {"polished": "...", "report": {...}}
"""
import sys, json, subprocess, time
from pathlib import Path

HOOKS_DIR = Path(__file__).parent
PYTHON = Path(r"C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe")
NPX = Path(r"C:\Program Files\nodejs\npx.cmd")
NODE = Path(r"C:\Program Files\nodejs\node.exe")
UNO = Path(r"C:\Users\Administrator\.litellm\servers\uno-mcp\dist\index.js")

CHAPTERS = Path("D:\\Writer\\novel-project\\chapters")


# ── MCP 调用工具 ──

def mcp_call(command: list, tool_name: str, arguments: dict, timeout: int = 60) -> dict:
    """通用 MCP 工具调用"""
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    try:
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                     "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                                "clientInfo": {"name": "novel-pipeline", "version": "2.5"}}}) + "\n")
        proc.stdin.flush(); time.sleep(0.4)
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        proc.stdin.flush(); time.sleep(0.3)
        req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                          "params": {"name": tool_name, "arguments": arguments}})
        proc.stdin.write(req + "\n"); proc.stdin.flush()
        stdout, stderr = proc.communicate(timeout=timeout)
        for line in stdout.split("\n"):
            line = line.strip()
            if not line: continue
            try:
                msg = json.loads(line)
                if "result" in msg and "content" in msg["result"]:
                    for c in msg["result"]["content"]:
                        if c.get("type") == "text": return {"ok": True, "data": c["text"]}
                if "error" in msg: return {"ok": False, "error": str(msg["error"])}
            except: continue
        return {"ok": False, "error": f"no valid response: {stderr[:200]}"}
    except subprocess.TimeoutExpired: proc.kill(); return {"ok": False, "error": f"timeout ({timeout}s)"}
    except Exception as e: return {"ok": False, "error": str(e)}
    finally:
        try: proc.kill()
        except: pass


def pr_tool(name: str, args: dict) -> dict:
    """调用 publishready"""
    npx = str(NPX) if NPX.exists() else "npx"
    return mcp_call([npx, "-y", "@veldica/publishready-mcp"], name, args)


def uno_tool(name: str, args: dict) -> dict:
    """调用 uno"""
    return mcp_call([str(NODE), str(UNO)], name, args)


# ── 主流程 ──

def main():
    raw = sys.stdin.read().strip()
    if not raw:
        return output({"error": "stdin 为空"})

    inp = json.loads(raw) if raw.startswith("{") else {"text": raw}
    
    # 支持按章节号读取
    text = inp.get("text", inp.get("output", ""))
    ch = inp.get("chapter", inp.get("ch", 0))
    if not text and ch:
        p = CHAPTERS / f"ch{ch}.md"
        if p.exists():
            text = p.read_text(encoding="utf-8")
        else:
            return output({"error": f"章节文件不存在: {p}"})

    if len(text.strip()) < 500:
        return output({"error": "正文字数不足500，跳过"})

    report = {}
    issues = []

    # ── Step 2: publishready 检查 ──
    print("[STEP 2/7] publishready 检查...", file=sys.stderr)
    r = pr_tool("analyze_text", {"text": text})
    report["pr_analyze"] = r.get("data", r.get("error", "失败")) if r["ok"] else f"失败: {r.get('error')}"
    if not r["ok"]: issues.append(f"publishready analyze_text: {r['error']}")

    r = pr_tool("audit_ai_sounding_prose", {"text": text})
    report["pr_ai_audit"] = r.get("data", r.get("error", "")) if r["ok"] else f"失败: {r.get('error')}"
    has_ai_issue = r["ok"] and ("marker" in (r.get("data", "")).lower() or "pattern" in (r.get("data", "")).lower())

    r = pr_tool("find_hotspots", {"text": text})
    report["pr_hotspots"] = r.get("data", "") if r["ok"] else f"失败: {r.get('error')}"

    r = pr_tool("suggest_revision_levers", {"text": text})
    report["pr_suggestions"] = r.get("data", "") if r["ok"] else f"失败: {r.get('error')}"

    # ── Step 3: uno 检查 ──
    print("[STEP 3/7] uno 检查...", file=sys.stderr)
    r = uno_tool("analyze_text", {"text": text})
    report["uno_analyze"] = r.get("data", "") if r["ok"] else f"失败: {r.get('error')}"
    has_environmental_issue = r["ok"] and "high" in r.get("data", "").lower() and ("environmental" in r.get("data", "").lower() or "prose" in r.get("data", "").lower())

    # ── Step 4: 综合评估 → 确定修复方向 ──
    print("[STEP 4/7] 综合评估...", file=sys.stderr)
    enable_flags = {
        "enableGoldenShadow": True,
        "enableEnvironmental": has_environmental_issue,
        "enableActionScene": True,
        "enableProseSmoother": has_ai_issue or has_environmental_issue,
        "enableRepetitionElimination": True,
    }
    report["assessment"] = {
        "ai_issue_detected": has_ai_issue,
        "environmental_weak": has_environmental_issue,
        "enabled_techniques": [k for k, v in enable_flags.items() if v],
    }

    # ── Step 5: uno 修复 ──
    print("[STEP 5/7] uno 修复中...", file=sys.stderr)
    r = uno_tool("custom_enhance_text", {
        "text": text,
        "expansionTarget": 120,  # 扩写 20%
        **enable_flags,
    })
    if r["ok"]:
        polished = r["data"]
        report["polished_length"] = len(polished)
    else:
        # 降级到普通 enhance_text
        r2 = uno_tool("enhance_text", {"text": text, "expansionTarget": 120})
        if r2["ok"]:
            polished = r2["data"]
            report["polished_length"] = len(polished)
            report["degraded"] = "custom_enhance 失败，使用 enhance"
        else:
            polished = text
            issues.append(f"uno 修复均失败: {r.get('error')} / {r2.get('error', '')}")

    # ── Step 6: publishready 复检 ──
    print("[STEP 6/7] publishready 复检...", file=sys.stderr)
    r = pr_tool("compare_text_versions", {"original_text": text, "revised_text": polished})
    report["pr_verification"] = r.get("data", "") if r["ok"] else f"复检失败: {r.get('error')}"

    # ── 输出 ──
    print("[STEP 7/7] 完成", file=sys.stderr)
    result = {
        "polished": polished,
        "report": report,
        "issues": issues,
        "passed": len(issues) == 0,
        "hook": "polish_independent",
    }
    output(result)


def output(data: dict):
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
