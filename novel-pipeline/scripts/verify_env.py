#!/usr/bin/env python3
"""
novel-pipeline 环境验证脚本
一键检查 Python 环境、依赖包、Skill 结构、项目结构是否健康。
在项目根目录执行即可输出诊断报告。

用法:
  python <Skill路径>/scripts/verify_env.py                    # 自动检测当前目录项目
  python <Skill路径>/scripts/verify_env.py D:\\your-novel-project  # 指定项目根目录
"""
import sys, json, importlib, shutil
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
HOOKS_DIR = SKILL_DIR / "hooks"
MCP_DIR = SKILL_DIR / "mcp"
STATE_TEMPLATE = SKILL_DIR / "state-files"

STDLIB_CHECKS = [
    "json", "os", "re", "asyncio", "subprocess",
    "difflib", "pathlib", "datetime",
]
EXTERNAL_CHECKS = [
    ("httpx", "pip install httpx"),
    ("mcp.server.fastmcp", "pip install mcp"),
]
MCP_SERVERS = [
    ("novel-deepseek", "deepseek_server.py"),
    ("novel-doubao", "doubao_server.py"),
]
ENV_KEYS_REQUIRED = [
    "DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL",
    "DOUBAO_API_KEY", "DOUBAO_BASE_URL", "DOUBAO_MODEL",
]
HOOK_SCRIPTS = [
    "validate_draft.py", "validate_polish.py",
    "check_draft_quality.py", "audit_polish.py",
    "load_state.py", "archive_state.py",
    "polish_independent.py", "utils.py",
]


def check(label, ok, detail=""):
    return {"check": label, "ok": ok, "detail": detail}


def run():
    results = []

    # Python 版本
    v = sys.version_info
    ok = v.major == 3 and v.minor >= 10
    results.append(check("Python version", ok, f"{v.major}.{v.minor}.{v.micro} (need >=3.10)"))

    # stdlib
    for mod in STDLIB_CHECKS:
        try:
            importlib.import_module(mod)
            results.append(check("stdlib: " + mod, True))
        except ImportError:
            results.append(check("stdlib: " + mod, False))

    # 外部包
    for mod, hint in EXTERNAL_CHECKS:
        try:
            importlib.import_module(mod)
            results.append(check("pkg: " + mod, True))
        except ImportError:
            results.append(check("pkg: " + mod, False, hint))

    # Skill 本地 .env（必需）
    skill_env = SKILL_DIR / ".env"
    env_found = skill_env.exists()
    env_vars = {}
    if env_found:
        for line in skill_env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip("\"'")
    results.append(check("Skill .env exists", env_found, str(skill_env)))
    for key in ENV_KEYS_REQUIRED:
        val = env_vars.get(key, "")
        if key.endswith("_KEY"):
            has = bool(val) and len(val) > 4
        else:
            has = bool(val)
        results.append(check(".env: " + key, has, "configured" if has else "missing (放 skill .env 或系统环境变量)"))

    # MCP server 文件
    for sname, sfile in MCP_SERVERS:
        spath = MCP_DIR / sname / sfile
        results.append(check("MCP server: " + sname, spath.exists(), str(spath)))

    # Hook 脚本
    for h in HOOK_SCRIPTS:
        hpath = HOOKS_DIR / h
        results.append(check("hook: " + h, hpath.exists(), str(hpath) if hpath.exists() else "missing"))

    # 项目检测（识别 novel.json / writer.json / novel-pipeline.json 任一）
    project_root = None
    project_marker = None
    marker_names = ("novel.json", "writer.json", "novel-pipeline.json")
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        for name in marker_names:
            if (project_root / name).exists():
                project_marker = project_root / name
                break
    else:
        cwd = Path.cwd()
        for p in [cwd] + list(cwd.parents)[:5]:
            for name in marker_names:
                if (p / name).exists():
                    project_root = p
                    project_marker = p / name
                    break
            if project_marker:
                break
    if project_root and project_marker:
        results.append(check("Project marker", True, str(project_marker)))
        state_dir = project_root / "state-files"
        results.append(check("Project state-files", state_dir.exists(), str(state_dir)))
        chapters_dir = project_root / "chapters"
        if chapters_dir.exists():
            count = len(list(chapters_dir.glob("*.md"))) + len(list(chapters_dir.glob("*.txt")))
            results.append(check("Chapters dir", True, f"{count} chapters in {chapters_dir}"))
        else:
            results.append(check("Chapters dir", False, f"{chapters_dir} (will be created on first write)"))
        try:
            cfg = json.loads(project_marker.read_text(encoding="utf-8"))
            name = cfg.get("project_name") or cfg.get("project") or "?"
            ch = cfg.get("current_chapter") or cfg.get("chapters_done") or "?"
            results.append(check("Config parse", True, f"Work: {name} / Ch: {ch}"))
        except Exception as e:
            results.append(check("Config parse", False, str(e)))
    else:
        results.append(check("Project root", False, "no marker found (looked for novel.json / writer.json / novel-pipeline.json in CWD + 5 parents)"))

    # 模板 JSON 合法性
    for tf in STATE_TEMPLATE.glob("*.json"):
        try:
            json.loads(tf.read_text(encoding="utf-8"))
            results.append(check(f"Template: {tf.name}", True))
        except json.JSONDecodeError as e:
            results.append(check(f"Template: {tf.name}", False, str(e)))

    # 汇总
    # 关键项：Python 版本、stdlib、hook 脚本、MCP server、状态模板、Skill .env 存在、6 个必需环境变量
    critical = [
        r for r in results
        if r["check"].startswith((
            "Python version", "stdlib:", "hook:", "MCP server:",
            "Template:", "Skill .env", ".env: ",
        ))
    ]
    summary = {
        "ok": all(r["ok"] for r in critical),
        "total": len(results),
        "passed": sum(1 for r in results if r["ok"]),
        "failed": sum(1 for r in results if not r["ok"]),
        "critical_failed": sum(1 for r in critical if not r["ok"]),
    }
    print(json.dumps({"summary": summary, "checks": results}, ensure_ascii=False, indent=2))
    sys.exit(0 if summary["ok"] else 1)


if __name__ == "__main__":
    run()
