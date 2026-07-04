"""
Hook 共享工具
项目隔离查找：优先使用当前项目目录下的 state-files，回退到 Skill 模板。
"""
import os, json, subprocess, time
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SKILL_STATE_DIR = SKILL_DIR / "state-files"


def find_state_dir() -> Path:
    """
    从当前工作目录向上查找 novel-pipeline.json 项目标记文件。
    找到 → 返回项目的 state-files/ 目录
    未找到 → 返回 Skill 模板目录（只读回退）
    """
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents)[:5]:
        marker = parent / "novel-pipeline.json"
        if marker.exists():
            proj_state = parent / "state-files"
            if proj_state.exists():
                return proj_state
            proj_state.mkdir(parents=True, exist_ok=True)
            return proj_state
    return SKILL_STATE_DIR


def load_dotenv(key: str) -> str:
    """读取环境变量优先级：系统环境变量 → 全局.env → skill本地.env"""
    val = os.environ.get(key, "")
    if val:
        return val
    global_dotenv = Path.home() / ".litellm" / "servers" / ".env"
    if global_dotenv.exists():
        for line in global_dotenv.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == key:
                    return v.strip().strip("\"'")
    skill_dotenv = SKILL_DIR / ".env"
    if skill_dotenv.exists():
        for line in skill_dotenv.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == key:
                    return v.strip().strip("\"'")
    return ""


# ── memory-novel MCP 调用封装 ─────────────────────────────────

NPX = r"C:\Program Files\nodejs\npx.cmd"
MEMORY_FILE_PATH = load_dotenv("MEMORY_FILE_PATH") or r"D:\Writer\novel-project\.memory\knowledge.jsonl"


def _start_memory_mcp():
    """启动 memory-novel MCP 子进程"""
    env = {**os.environ, "MEMORY_FILE_PATH": MEMORY_FILE_PATH}
    proc = subprocess.Popen(
        [NPX, "-y", "@modelcontextprotocol/server-memory"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1,
    )
    time.sleep(1.5)
    return proc


def _mcp_call(proc, method, params=None):
    """发送 MCP 请求并返回响应"""
    req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})
    proc.stdin.write(req + "\n")
    proc.stdin.flush()
    time.sleep(0.5)
    return proc


def _read_response(proc, timeout=5):
    """读取子进程所有 stdout"""
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate(timeout=3)
    for line in stdout.strip().split("\n"):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return {"error": f"No JSON response. stderr: {stderr[:200]}"}


def memory_search(query: str) -> list:
    """搜索 memory-novel 知识图谱"""
    try:
        proc = _start_memory_mcp()
        _mcp_call(proc, "initialize", {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "novel-pipeline", "version": "2.0"}
        })
        _mcp_call(proc, "notifications/initialized")
        time.sleep(0.3)

        # 发送 search_nodes 请求
        req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                          "params": {"name": "search_nodes", "arguments": {"query": query}}})
        proc.stdin.write(req + "\n")
        proc.stdin.flush()

        resp = _read_response(proc)
        result = resp.get("result", {})
        content = result.get("content", [])
        for c in content:
            if c.get("type") == "text":
                return json.loads(c["text"]) if isinstance(c["text"], str) else c["text"]
        return []
    except Exception as e:
        return []


def memory_store_entities(entities: list) -> bool:
    """存储实体到 memory-novel 知识图谱"""
    try:
        proc = _start_memory_mcp()
        _mcp_call(proc, "initialize", {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "novel-pipeline", "version": "2.0"}
        })
        _mcp_call(proc, "notifications/initialized")
        time.sleep(0.3)

        req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                          "params": {"name": "create_entities", "arguments": {"entities": entities}}})
        proc.stdin.write(req + "\n")
        proc.stdin.flush()

        resp = _read_response(proc)
        return "result" in resp
    except Exception as e:
        return False


def memory_store_relations(relations: list) -> bool:
    """存储关系到 memory-novel 知识图谱"""
    try:
        proc = _start_memory_mcp()
        _mcp_call(proc, "initialize", {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "novel-pipeline", "version": "2.0"}
        })
        _mcp_call(proc, "notifications/initialized")
        time.sleep(0.3)

        req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                          "params": {"name": "create_relations", "arguments": {"relations": relations}}})
        proc.stdin.write(req + "\n")
        proc.stdin.flush()

        resp = _read_response(proc)
        return "result" in resp
    except Exception as e:
        return False
