#!/usr/bin/env python3
"""
novel-pipeline 环境验证脚本
一键检查 Python 环境、依赖包、MCP 服务器、项目结构是否健康。
在项目根目录执行即可输出诊断报告。

用法:
  python <Skill路径>/scripts/verify_env.py                    # 自动检测当前目录项目
  python <Skill路径>/scripts/verify_env.py D:\\your-novel-project  # 指定项目根目录
"""
import sys, json, importlib, shutil
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
HOOKS_DIR = SKILL_DIR / "hooks"
STATE_TEMPLATE = SKILL_DIR / "state-files"

STDLIB_CHECKS = [
    ("json", None), ("os", None), ("re", None),
    ("asyncio", None), ("subprocess", None),
    ("urllib.request", None), ("difflib", None),
    ("pathlib", None), ("datetime", None),
]
EXTERNAL_CHECKS = [
    ("httpx", "pip install httpx"),
    ("mcp.server.fastmcp", "pip install mcp"),
]
DEFAULT_MCP_SERVERS = [
    ("novel-deepseek", "deepseek_server.py"),
    ("novel-doubao", "doubao_server.py"),
]
ENV_KEYS = ["DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL",
            "DOUBAO_API_KEY", "DOUBAO_BASE_URL", "DOUBAO_MODEL",
            "MCP_FIRSTORY_ENDPOINT", "MCP_UNO_ENDPOINT", "MCP_PUBLISHREADY_ENDPOINT", "MCP_MEMORY_NOVEL_ENDPOINT"]
HOOK_SCRIPTS = [
    "validate_draft.py", "validate_polish.py",
    "check_draft_quality.py", "check_ooc_firstory.py",
    "audit_polish.py", "audit_publishready.py",
    "load_state.py", "archive_state.py", "utils.py",
]

def check(label, ok, detail=""):
    return {"check": label, "ok": ok, "detail": detail}

def run():
    results = []

    # Python version
    v = sys.version_info
    ok = v.major == 3 and v.minor >= 10
    results.append(check("Python version", ok,
        "%s.%s.%s (need >=3.10)" % (v.major, v.minor, v.micro) if not ok else "%s.%s.%s" % (v.major, v.minor, v.micro)))

    # stdlib modules
    for mod, hint in STDLIB_CHECKS:
        try:
            importlib.import_module(mod)
            results.append(check("stdlib: " + mod, True))
        except ImportError:
            results.append(check("stdlib: " + mod, False, hint or ""))

    # External packages
    for mod, hint in EXTERNAL_CHECKS:
        try:
            importlib.import_module(mod)
            results.append(check("pkg: " + mod, True))
        except ImportError:
            results.append(check("pkg: " + mod, False, hint))

    # npx / Node
    npx = shutil.which("npx")
    node = shutil.which("node")
    results.append(check("node available", bool(node), shutil.which("node") or "not found"))
    results.append(check("npx available", bool(npx), shutil.which("npx") or "not found"))

    # Global .env
    global_env = Path.home() / ".litellm" / "servers" / ".env"
    env_found = global_env.exists()
    env_vars = {}
    if env_found:
        for line in global_env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip("\"'")
    results.append(check("Global .env exists", env_found, str(global_env)))
    for key in ENV_KEYS:
        if key.endswith("_KEY"):
            has = key in env_vars and len(env_vars[key]) > 4
            results.append(check(".env: " + key, has, "configured" if has else "missing or too short"))
        elif key.endswith("_ENDPOINT"):
            has = key in env_vars and env_vars[key].startswith("http")
            results.append(check(".env: " + key, has, env_vars.get(key, "not set")))
        else:
            has = key in env_vars
            results.append(check(".env: " + key, has, env_vars.get(key, "not set")))

    # MCP server files (check default locations, optional)
    servers_dir = Path.home() / ".litellm" / "servers"
    if servers_dir.exists():
        for sname, sfile in DEFAULT_MCP_SERVERS:
            spath = servers_dir / sname / sfile
            ok = spath.exists()
            results.append(check("MCP (optional): " + sname, ok, str(spath) if ok else "missing (you can use custom MCP servers)"))
    else:
        results.append(check("MCP servers dir", False, f"{servers_dir} not found, deploy MCP services if needed"))

    # Hook scripts
    for h in HOOK_SCRIPTS:
        hpath = HOOKS_DIR / h
        ok = hpath.exists()
        results.append(check("hook: " + h, ok, str(hpath) if ok else "missing"))

    # Project detection
    project_root = None
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
    else:
        cwd = Path.cwd()
        for p in [cwd] + list(cwd.parents)[:5]:
            if (p / "novel-pipeline.json").exists():
                project_root = p
                break
    if project_root and project_root.exists():
        marker = project_root / "novel-pipeline.json"
        results.append(check("Project marker", marker.exists(), str(marker)))
        state_dir = project_root / "state-files"
        results.append(check("Project state-files", state_dir.exists(), str(state_dir)))
        chapters_dir = project_root / "chapters"
        if chapters_dir.exists():
            count = len(list(chapters_dir.glob("*.md"))) + len(list(chapters_dir.glob("*.txt")))
            results.append(check("Chapters dir", True, "%d chapters in %s" % (count, chapters_dir)))
        else:
            results.append(check("Chapters dir", False, str(chapters_dir) + " (will be created on first write)"))
        try:
            cfg = json.loads(marker.read_text(encoding="utf-8"))
            results.append(check("Config parse", True,
                "Work: %s / Ch: %s" % (cfg.get("project_name","?"), cfg.get("current_chapter","?"))))
        except Exception as e:
            results.append(check("Config parse", False, str(e)))
    else:
        results.append(check("Project root", False, "novel-pipeline.json not found (searched CWD + 5 parents) — create a new project first"))

    # Template state JSON validity
    all_templates_valid = True
    for tf in STATE_TEMPLATE.glob("*.json"):
        try:
            json.loads(tf.read_text(encoding="utf-8"))
            results.append(check(f"Template: {tf.name}", True))
        except json.JSONDecodeError as e:
            results.append(check(f"Template: {tf.name}", False, str(e)))
            all_templates_valid = False

    # Summary
    # 核心必过项：Python版本、stdlib、hooks脚本、模板有效
    critical_checks = [r for r in results if r["check"].startswith(("Python version", "stdlib:", "hook:", "Template:"))]
    summary = {
        "ok": all(r["ok"] for r in critical_checks),
        "total": len(results),
        "passed": sum(1 for r in results if r["ok"]),
        "failed": sum(1 for r in results if not r["ok"]),
        "critical_failed": sum(1 for r in critical_checks if not r["ok"]),
    }
    print(json.dumps({"summary": summary, "checks": results}, ensure_ascii=False, indent=2))
    sys.exit(0 if summary["ok"] else 1)

if __name__ == "__main__":
    run()
