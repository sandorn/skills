#!/usr/bin/env python3
"""
独立润色管线：直接调用 novel-doubao 润色
流程:
  1. 读文本
  2. 综合评估（默认配置）
  3. novel-doubao 润色
  4. 完整性检查
  5. 完成输出
关键实现: mcp_call 使用线程读取 stdout, 保持 stdin 开着直到收到目标响应,
        避免 communicate() 提前关闭 stdin 导致 MCP 服务器 anyio.ClosedResourceError
"""
import sys, json, subprocess, time, threading, queue, re
from pathlib import Path

HOOKS_DIR = Path(__file__).parent
SKILL_ROOT = HOOKS_DIR.parent
PYTHON = Path(r"C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe")
# 路径修正：指向Skill内的MCP目录
DOUBAO = SKILL_ROOT / "mcp" / "novel-doubao" / "doubao_server.py"
DOUBAO_CWD = SKILL_ROOT / "mcp" / "novel-doubao"
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
        p = CHAPTERS / f"ch{ch:02d}.md"
        if p.exists(): text = p.read_text(encoding="utf-8")
        else: return output({"error": f"章节不存在: {p}"})
    if len(text.strip()) < 500: return output({"error": "正文字数不足"})

    report = {}; issues = []

    print("[2/4] 综合评估...", file=sys.stderr)
    summary = {
        "publishready": {
            "ai_risk": "low",
            "suggestion": "",
        },
        "uno": {
            "scene_type": "mixed",
            "sensory_richness": "adequate",
        },
    }
    report["assessment"] = summary

    print("[3/4] novel-doubao 润色中...", file=sys.stderr)
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
        END_OK = re.compile(r'[。！？…\"\\u201d」\\)）】\\]]\\s*$')
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

    print("[4/4] 完成", file=sys.stderr)
    output({"polished": polished, "report": report, "issues": issues,
            "passed": len(issues) == 0, "hook": "polish_independent"})


def output(data):
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()