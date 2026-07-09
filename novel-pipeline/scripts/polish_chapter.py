#!/usr/bin/env python3
"""
novel-pipeline Skill 官方逐章润色工具
触发词：逐章润色
功能：单章顺序润色，完成一章输出一章结果，无后台批量运行，全程进度透明
"""
import json
import subprocess
import sys
import time
from pathlib import Path

# 自动适配Skill路径
SKILL_ROOT = Path(__file__).parent.parent
POLISH_SCRIPT = SKILL_ROOT / "hooks" / "polish_independent.py"

def _check_mcp_registered(mcp_name: str) -> bool:
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

def _register_mcp(mcp_name: str, server_dir: str, script_name: str) -> bool:
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

# 启动前自动检查并注册依赖MCP
REQUIRED_MCPS = [
    ("novel-doubao", "novel-doubao", "doubao_server.py"),
    ("novel-deepseek", "novel-deepseek", "deepseek_server.py")
]

for name, dir_name, script in REQUIRED_MCPS:
    if not _check_mcp_registered(name):
        print(f"🔧 自动注册依赖MCP服务：{name}")
        if not _register_mcp(name, dir_name, script):
            print(f"❌ 依赖MCP {name} 注册失败，无法继续执行", file=sys.stderr)
            sys.exit(1)

def polish_single_chapter(chap_num, chapters_dir, python_path=None):
    """
    单章润色入口
    :param chap_num: 章节号
    :param chapters_dir: 章节目录路径
    :param python_path: Python解释器路径，默认使用当前运行的解释器
    :return: (是否成功, 结果信息)
    """
    if not python_path:
        python_path = sys.executable
    
    chap_path = Path(chapters_dir) / f"ch{chap_num}.md"
    if not chap_path.exists():
        return False, f"❌ ch{chap_num} 不存在"
    
    # 读取原文
    try:
        with open(chap_path, 'r', encoding='utf-8') as f:
            text = f.read()
        original_len = len(text)
    except Exception as e:
        return False, f"❌ ch{chap_num} 读取失败：{str(e)}"
    
    # 构造输入
    input_data = json.dumps({
        "text": text,
        "chapter": chap_num
    }, ensure_ascii=False)
    
    # 调用润色脚本
    try:
        proc = subprocess.Popen(
            [str(python_path), str(POLISH_SCRIPT)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        stdout, stderr = proc.communicate(input=input_data, timeout=600)
        
        if proc.returncode != 0:
            return False, f"❌ ch{chap_num} 润色失败：{stderr[:200]}"
        
        # 解析结果
        result = json.loads(stdout)
        polished_text = result.get("polished", "")
        issues = result.get("issues", [])
        
        # 保存结果
        with open(chap_path, 'w', encoding='utf-8') as f:
            f.write(polished_text)
        
        # 构造结果信息
        msg = f"✅ ch{chap_num} 润色完成 | 原字数：{original_len:,} → 润色后字数：{len(polished_text):,} | 问题数：{len(issues)}"
        if issues:
            msg += f"\n⚠️  遗留问题：{'、'.join(issues[:3])}{' 等' if len(issues) > 3 else ''}"
        return True, msg
    except Exception as e:
        return False, f"❌ ch{chap_num} 执行异常：{str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法：")
        print("  单章润色：python polish_chapter.py <章节号> <章节目录路径> [Python解释器路径]")
        print("  示例：python polish_chapter.py 101 D:\\Writer\\novel-project\\chapters")
        sys.exit(1)
    
    chap = int(sys.argv[1])
    chapters_dir = sys.argv[2]
    python_path = sys.argv[3] if len(sys.argv) >=4 else None
    
    success, msg = polish_single_chapter(chap, chapters_dir, python_path)
    print(msg)
    sys.exit(0 if success else 1)