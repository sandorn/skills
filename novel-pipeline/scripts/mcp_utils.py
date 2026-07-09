#!/usr/bin/env python3
"""
novel-pipeline 通用工具集：MCP自动注册、路径适配等
"""
import subprocess
import sys
import time
from pathlib import Path

# 全局SKILL根目录适配
SKILL_ROOT = Path(__file__).parent.parent

def load_env():
    """加载Skill根目录的.env文件到环境变量"""
    env_path = SKILL_ROOT / ".env"
    env = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip(); v = v.strip().strip("\\\"'")
                env[k] = v
    return env

def check_mcp_registered(mcp_name: str) -> bool:
    """检查MCP服务是否已在Hermes中注册"""
    try:
        res = subprocess.run(
            ["hermes", "mcp", "list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10
        )
        if res.returncode != 0:
            return False
        return mcp_name in res.stdout
    except Exception:
        return False

def register_mcp(mcp_name: str, server_dir: str, script_name: str) -> bool:
    """动态注册MCP服务到当前Hermes会话"""
    server_path = SKILL_ROOT / "mcp" / server_dir / script_name
    cwd = SKILL_ROOT / "mcp" / server_dir
    # 加载.env环境变量
    env = load_env()
    # 拼接启动命令，带上环境变量
    env_str = " && ".join([f"set {k}={v}" for k, v in env.items()])
    start_cmd = f"{env_str} && \"{sys.executable}\" \"{server_path}\""
    
    try:
        subprocess.run(
            [
                "hermes", "mcp", "add",
                mcp_name,
                "--command", "cmd.exe",
                "--args", "/c", start_cmd
            ],
            check=True,
            capture_output=True,
            timeout=30
        )
        # 等待MCP加载完成
        time.sleep(3)
        return True
    except Exception as e:
        print(f"⚠️ MCP {mcp_name} 注册失败: {str(e)}", file=sys.stderr)
        # 打印详细错误
        if hasattr(e, "stderr"):
            print(f"错误详情: {e.stderr}", file=sys.stderr)
        if hasattr(e, "stdout"):
            print(f"输出详情: {e.stdout}", file=sys.stderr)
        return False

def ensure_mcps_ready(required_mcps=None) -> bool:
    """确保所有依赖的MCP服务已注册并可用"""
    if required_mcps is None:
        required_mcps = [
            ("novel-doubao", "novel-doubao", "doubao_server.py"),
            ("novel-deepseek", "novel-deepseek", "deepseek_server.py")
        ]
    
    all_ready = True
    for name, dir_name, script in required_mcps:
        if not check_mcp_registered(name):
            print(f"🔧 自动注册依赖MCP服务：{name}")
            if not register_mcp(name, dir_name, script):
                print(f"❌ 依赖MCP {name} 注册失败，无法继续执行", file=sys.stderr)
                all_ready = False
    return all_ready