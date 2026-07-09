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
    env_path = SKILL_ROOT / ".env"
    
    try:
        subprocess.run(
            [
                "hermes", "mcp", "add",
                "--name", mcp_name,
                "--command", sys.executable,
                "--args", str(server_path),
                "--cwd", str(cwd),
                "--env-file", str(env_path),
                "--session-only"
            ],
            check=True,
            capture_output=True,
            timeout=30
        )
        # 等待MCP加载完成
        time.sleep(2)
        return True
    except Exception as e:
        print(f"⚠️ MCP {mcp_name} 注册失败：{str(e)}", file=sys.stderr)
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