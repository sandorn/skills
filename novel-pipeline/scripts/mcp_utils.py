#!/usr/bin/env python3
"""
novel-pipeline 通用工具集：MCP自动注册、路径适配等
"""
import subprocess
import sys
import time
import os
import shutil
from pathlib import Path

# 全局 SKILL 根目录适配
SKILL_ROOT = Path(__file__).parent.parent


def has_hermes() -> bool:
    """检测当前环境是否有 hermes CLI（用于 MCP 自动注册）。"""
    return shutil.which("hermes") is not None


def _manual_register_hint(required_mcps) -> None:
    """打印手动注册引导（非 Hermes 环境使用）。"""
    print("\n⚠️  当前环境未检测到 hermes 命令，无法自动注册 MCP。", file=sys.stderr)
    print("请在你的 MCP 客户端配置文件中手动加入以下条目：\n", file=sys.stderr)
    for name, dir_name, script in required_mcps:
        server_path = SKILL_ROOT / "mcp" / dir_name / script
        print(f'  "{name}": {{', file=sys.stderr)
        print(f'    "command": "{sys.executable}",', file=sys.stderr)
        print(f'    "args": ["{server_path}"]', file=sys.stderr)
        print(f'  }}', file=sys.stderr)
    print("\n（Claude Desktop 位于 %APPDATA%\\Claude\\claude_desktop_config.json；Claude Code 使用 `.mcp.json`）", file=sys.stderr)


def load_env() -> dict[str, str]:
    """
    加载 Skill 根目录的 .env 文件
    优先级: skill本地.env → 系统环境变量
    与 hooks/utils.py 保持一致的加载逻辑
    """
    env: dict[str, str] = {}

    # 优先级 1: Skill 本地 .env
    env_path = SKILL_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip("\"'")

    # 优先级 2: 系统环境变量（只补充不覆盖）
    for k, v in os.environ.items():
        if k not in env:
            env[k] = v

    return env


def check_mcp_registered(mcp_name: str) -> bool:
    """检查 MCP 服务是否已在 Hermes 中注册"""
    try:
        res = subprocess.run(
            ["hermes", "mcp", "list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
        if res.returncode != 0:
            return False
        return mcp_name in res.stdout
    except Exception:
        return False


def register_mcp(mcp_name: str, server_dir: str, script_name: str) -> bool:
    """
    动态注册 MCP 服务到当前 Hermes 会话
    通过 env= 直接传递环境变量，避免 shell 拼接注入
    :return: 注册成功返回 True
    """
    server_path = SKILL_ROOT / "mcp" / server_dir / script_name

    if not server_path.exists():
        print(f"⚠️  MCP {mcp_name} 脚本不存在: {server_path}", file=sys.stderr)
        return False

    try:
        subprocess.run(
            [
                "hermes", "mcp", "add",
                mcp_name,
                "--command", sys.executable,
                "--args", str(server_path),
            ],
            check=True,
            capture_output=True,
            timeout=30,
            env=load_env(),  # 直接传环境变量，无 shell 拼接
        )
        # 等待 MCP 加载完成
        time.sleep(3)
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  MCP {mcp_name} 注册失败: {e}", file=sys.stderr)
        if e.stderr:
            err = e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else e.stderr
            print(f"错误详情: {err[:500]}", file=sys.stderr)
        if e.stdout:
            out = e.stdout.decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else e.stdout
            print(f"输出详情: {out[:500]}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"⚠️  MCP {mcp_name} 注册异常: {e}", file=sys.stderr)
        return False


def ensure_mcps_ready(required_mcps=None) -> bool:
    """
    确保所有依赖的 MCP 服务已注册并可用
    :param required_mcps: 要注册的 MCP 列表，默认注册 doubao 和 deepseek
    :return: 全部注册成功返回 True
    """
    if required_mcps is None:
        required_mcps = [
            ("novel-doubao", "novel-doubao", "doubao_server.py"),
            ("novel-deepseek", "novel-deepseek", "deepseek_server.py"),
        ]

    # 非 Hermes 环境：直接打印手动注册引导并放行
    if not has_hermes():
        _manual_register_hint(required_mcps)
        return True

    all_ready = True
    for name, dir_name, script in required_mcps:
        if not check_mcp_registered(name):
            print(f"🔧 自动注册依赖 MCP 服务：{name}")
            if not register_mcp(name, dir_name, script):
                print(f"❌ 依赖 MCP {name} 注册失败，无法继续执行", file=sys.stderr)
                all_ready = False
    return all_ready
