#!/usr/bin/env python3
"""
PostToolUse Hook: audit_publishready
在豆包润色完成后执行出版级文本审计（Layer 2 终检）
触发: MCP:novel-doubao.polish_chapter 返回后

审计项:
  1. AI 腔检测 (audit_ai_sounding_prose)
  2. 可读性打分 + 热点定位 (find_hotspots)
  3. 与小说模板合规检查 (analyze_against_template)

所有处理在本地完成，不发送文本到第三方服务。
"""
import sys, json, subprocess, time, re
from pathlib import Path

TEMPLATE_FICTION = "fiction"  # publishready 内建小说模板


def call_publishready_tool(tool_name: str, arguments: dict, timeout: int = 60) -> dict:
    """通过 npx 子进程调用 publishready MCP 工具"""
    proc = subprocess.Popen(
        ["npx", "-y", "@veldica/publishready-mcp"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1
    )
    try:
        # MCP 初始化
        init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                           "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                      "clientInfo": {"name": "novel-pipeline", "version": "1.0"}}})
        proc.stdin.write(init + "\n"); proc.stdin.flush()
        time.sleep(0.5)

        # 确认初始化
        notified = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
        proc.stdin.write(notified + "\n"); proc.stdin.flush()
        time.sleep(0.3)

        # 调用工具
        call = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                           "params": {"name": tool_name, "arguments": arguments}})
        proc.stdin.write(call + "\n"); proc.stdin.flush()

        # 读取响应
        stdout, stderr = proc.communicate(timeout=timeout)

        # 解析 JSON 行
        for line in stdout.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                if "result" in msg and "content" in msg["result"]:
                    for content in msg["result"]["content"]:
                        if content.get("type") == "text":
                            return {"success": True, "data": content["text"]}
                if "error" in msg:
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


def extract_text_from_output(data: str) -> str:
    """尝试从 publishready 返回中提取 JSON 结果"""
    # publishready 可能返回纯文本或 JSON
    if not data:
        return ""
    try:
        parsed = json.loads(data)
        return json.dumps(parsed, ensure_ascii=False, indent=2)
    except:
        return data


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return output(True, ["stdin 为空，跳过审计"], {"skipped": True})

        hook_input = json.loads(raw)
        tool_output = hook_input.get("output", hook_input.get("result", hook_input.get("response", {})))

        # 提取润色后的正文文本
        polished_text = ""
        if isinstance(tool_output, str):
            polished_text = tool_output
        elif isinstance(tool_output, dict):
            polished_text = tool_output.get("content", "") or tool_output.get("text", "")

        if not polished_text or len(polished_text.strip()) < 500:
            return output(True, ["正文字数不足，跳过审计"], {"skipped": True, "reason": "text too short"})

        issues = []
        audit_results = {}

        # ── 1. AI 腔检测 ──
        ai_result = call_publishready_tool("audit_ai_sounding_prose", {"text": polished_text})
        if ai_result["success"]:
            audit_results["ai_audit"] = extract_text_from_output(ai_result["data"])
            # 检查是否有 AI 腔标记
            ai_data = ai_result["data"]
            if "marker" in ai_data.lower() or "pattern" in ai_data.lower():
                issues.append("[AI腔] 检测到可能的 AI 写作痕迹，详见 audit_results.ai_audit")
        else:
            issues.append(f"[publishready] AI腔检测失败: {ai_result.get('error', 'unknown')}")

        # ── 2. 热点定位 ──
        hotspot_result = call_publishready_tool("find_hotspots", {"text": polished_text})
        if hotspot_result["success"]:
            audit_results["hotspots"] = extract_text_from_output(hotspot_result["data"])
        else:
            issues.append(f"[publishready] 热点定位失败: {hotspot_result.get('error', 'unknown')}")

        # ── 3. 小说模板合规 ──
        template_result = call_publishready_tool("analyze_against_template",
                                                  {"text": polished_text, "template_id": TEMPLATE_FICTION})
        if template_result["success"]:
            audit_results["template_check"] = extract_text_from_output(template_result["data"])
        else:
            # 模板检查失败不阻塞（模板可能不存在）
            audit_results["template_check"] = f"跳过: {template_result.get('error', 'unknown')}"

        # 汇总
        passed = len([i for i in issues if "[AI腔]" in i]) == 0  # 只有 AI 腔是硬伤
        return output(passed, issues, {"audit_results": audit_results, "hook": "audit_publishready"})

    except json.JSONDecodeError as e:
        return output(False, [f"JSON 解析失败: {str(e)}"], {})
    except Exception as e:
        return output(False, [f"审计异常: {str(e)}"], {})


def output(valid: bool, issues: list[str], details: dict) -> None:
    result = {
        "passed": valid,
        "issues": issues,
        "details": details,
        "hook": "audit_publishready",
        "action_required": "review" if issues else "proceed",
    }
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if valid else 0)  # 审计不阻断流程，只标记


if __name__ == "__main__":
    main()
