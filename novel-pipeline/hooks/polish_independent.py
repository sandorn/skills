#!/usr/bin/env python3
"""
独立润色管线：publishready + uno 分析 → novel-doubao 润色

流程:
  1. 读文本
  2. publishready 审计
  3. uno 分析
  4. 综合评估
  5. novel-doubao 润色（携带双报告作 context）
  6. publishready 复检
  7. 输出

关键实现: mcp_call 使用线程读取 stdout, 保持 stdin 开着直到收到目标响应,
        避免 communicate() 提前关闭 stdin 导致 MCP 服务器 anyio.ClosedResourceError
"""
import sys, json, subprocess, time, threading, queue, re
from pathlib import Path

HOOKS_DIR = Path(__file__).parent
PYTHON = Path(r"C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe")
NPX = Path(r"C:\Program Files\nodejs\npx.cmd")
NODE = Path(r"C:\Program Files\nodejs\node.exe")
UNO = Path(r"C:\Users\Administrator\.litellm\servers\uno-mcp\dist\index.js")
DOUBAO = Path(r"C:\Users\Administrator\.litellm\servers\novel-doubao\doubao_server.py")
DOUBAO_CWD = Path(r"C:\Users\Administrator\.litellm\servers\novel-doubao")
CHAPTERS = Path("D:\\Writer\\novel-project\\chapters")


def mcp_call(command, tool_name, arguments, timeout=90, cwd=None):
    """长响应友好的 MCP 调用: 用队列 + 线程读, 收到 id=2 后再关 stdin"""
    proc = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, bufsize=1,
        cwd=str(cwd) if cwd else None,
        encoding='utf-8', errors='replace',
    )
    q = queue.Queue()

    def reader():
        try:
            for line in proc.stdout:
                q.put(line)
        except: pass

    t = threading.Thread(target=reader, daemon=True); t.start()

    try:
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                     "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                                "clientInfo": {"name": "novel-pipeline", "version": "2.5"}}}) + "\n")
        proc.stdin.flush()

        # 等 initialize 响应
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                line = q.get(timeout=1)
                if line.strip():
                    msg = json.loads(line)
                    if msg.get("id") == 1: break
            except queue.Empty: continue
            except: continue

        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        proc.stdin.flush()

        req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                          "params": {"name": tool_name, "arguments": arguments}})
        proc.stdin.write(req + "\n"); proc.stdin.flush()

        # 等 id=2 响应
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                line = q.get(timeout=1)
                if not line.strip(): continue
                try:
                    msg = json.loads(line)
                except: continue
                if msg.get("id") != 2: continue
                if "result" in msg and "content" in msg["result"]:
                    for c in msg["result"]["content"]:
                        if c.get("type") == "text":
                            return {"ok": True, "data": c["text"]}
                if "error" in msg: return {"ok": False, "error": str(msg["error"])}
            except queue.Empty: continue

        return {"ok": False, "error": f"timeout waiting id=2 ({timeout}s)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        try: proc.stdin.close()
        except: pass
        try: proc.kill()
        except: pass


def pr_tool(name, args):
    npx = str(NPX) if NPX.exists() else "npx"
    return mcp_call([npx, "-y", "@veldica/publishready-mcp"], name, args, timeout=60)


def uno_tool(name, args):
    return mcp_call([str(NODE), str(UNO)], name, args, timeout=60)


def doubao_polish(text, report_summary):
    if not DOUBAO.exists():
        return {"ok": False, "error": f"doubao not found: {DOUBAO}"}
    python = str(PYTHON) if PYTHON.exists() else sys.executable
    ctx = f"审计参考: {json.dumps(report_summary, ensure_ascii=False)}"
    return mcp_call(
        [python, str(DOUBAO)], "polish_chapter",
        {"chapter_characters": ctx, "draft_text": text, "chapter_mood_tone": "中性"},
        timeout=300, cwd=DOUBAO_CWD,
    )


def main():
    raw = sys.stdin.read().strip()
    if not raw: return output({"error": "stdin 为空"})

    inp = json.loads(raw) if raw.startswith("{") else {"text": raw}
    text = inp.get("text", inp.get("output", ""))
    ch = inp.get("chapter", inp.get("ch", 0))
    if not text and ch:
        p = CHAPTERS / f"ch{ch}.md"
        if p.exists(): text = p.read_text(encoding="utf-8")
        else: return output({"error": f"章节不存在: {p}"})
    if len(text.strip()) < 500: return output({"error": "正文字数不足"})

    report = {}; issues = []

    print("[2/7] publishready 审计...", file=sys.stderr)
    for tool, key in [("analyze_text", "pr_analyze"), ("audit_ai_sounding_prose", "pr_ai_audit"),
                      ("find_hotspots", "pr_hotspots"), ("suggest_revision_levers", "pr_suggestions")]:
        r = pr_tool(tool, {"text": text})
        report[key] = r.get("data", "") if r["ok"] else f"失败: {r.get('error')}"
        if not r["ok"]: issues.append(f"{tool}: {r['error']}")

    print("[3/7] uno 分析...", file=sys.stderr)
    r = uno_tool("analyze_text", {"text": text})
    report["uno_analyze"] = r.get("data", "") if r["ok"] else f"失败: {r.get('error')}"

    print("[4/7] 综合评估...", file=sys.stderr)
    summary = {
        "publishready": {
            "ai_risk": "low" if "low" in report.get("pr_ai_audit", "").lower() else "check",
            "suggestion": report.get("pr_suggestions", "")[:200],
        },
        "uno": {
            "scene_type": "exposition" if "exposition" in report.get("uno_analyze", "") else "mixed",
            "sensory_richness": "needs_improvement" if "Needs improvement" in report.get("uno_analyze", "") else "adequate",
        },
    }
    report["assessment"] = summary

    print("[5/7] novel-doubao 润色中...", file=sys.stderr)
    r = doubao_polish(text, summary)
    if r["ok"]:
        polished = r["data"]
        if polished.startswith("ERROR_TRUNCATED:") or polished.startswith("ERROR:"):
            issues.append(f"doubao 返回错误: {polished[:100]}")
            report["doubao_result"] = f"错误, 保留原文"
            polished = text
        else:
            report["doubao_result"] = f"成功, {len(polished)}字"
    else:
        polished = text
        issues.append(f"doubao 失败: {r.get('error', '')[:100]}")
        report["doubao_result"] = f"失败, 保留原文: {r.get('error', '')[:100]}"

    # 完整性检查: 字数、结尾、篇幅比
    if polished != text:
        END_OK = re.compile(r'[。！？…"\u201d」\)）】\]]\s*$')
        polished_stripped = polished.rstrip()
        integrity_issues = []
        if not END_OK.search(polished_stripped):
            integrity_issues.append(f"结尾无终结标点(可能截断): ...{polished_stripped[-30:]}")
        ratio = len(polished) / len(text)
        if ratio < 0.7:
            integrity_issues.append(f"篇幅缩水{(1-ratio)*100:.0f}% (原{len(text)}→润{len(polished)})")
        if ratio > 1.5:
            integrity_issues.append(f"篇幅暴涨{(ratio-1)*100:.0f}% (原{len(text)}→润{len(polished)})")
        if integrity_issues:
            issues.extend(integrity_issues)
            report["integrity_check"] = "FAIL: " + "; ".join(integrity_issues)
            report["doubao_result"] += " [完整性检查失败, 保留原文]"
            polished = text
        else:
            report["integrity_check"] = "PASS"

    print("[6/7] publishready 复检...", file=sys.stderr)
    r = pr_tool("compare_text_versions", {"original_text": text, "revised_text": polished})
    report["pr_verification"] = r.get("data", "") if r["ok"] else f"失败: {r.get('error')}"

    print("[7/7] 完成", file=sys.stderr)
    output({"polished": polished, "report": report, "issues": issues,
            "passed": len(issues) == 0, "hook": "polish_independent"})


def output(data):
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
