#!/usr/bin/env python3
"""
novel-pipeline Skill 官方逐章润色工具
触发词：逐章润色
功能：单章顺序润色，完成一章输出一章结果，无后台批量运行，全程进度透明
"""
import json
import subprocess
import sys
from pathlib import Path

# 导入新版MCP工具
sys.path.insert(0, str(Path(__file__).parent))
from mcp_utils import ensure_mcps_ready

# 自动适配Skill路径
SKILL_ROOT = Path(__file__).parent.parent
POLISH_SCRIPT = SKILL_ROOT / "hooks" / "polish_independent.py"

# 启动前自动检查并注册依赖MCP
if not ensure_mcps_ready():
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
    
    # 适配两位数字文件名格式 ch01.md
    chap_path = Path(chapters_dir) / f"ch{int(chap_num):02d}.md"
    if not chap_path.exists():
        return False, f"❌ 章节文件不存在：{chap_path.name}"
    
    # 读取原文
    try:
        with open(chap_path, 'r', encoding='utf-8') as f:
            text = f.read()
        original_len = len(text)
    except Exception as e:
        return False, f"❌ 章节读取失败：{str(e)}"
    
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
            return False, f"❌ 润色失败：{stderr[:300]}"
        
        # 解析结果
        result = json.loads(stdout)
        polished_text = result.get("polished", "")
        issues = result.get("issues", [])
        
        # 保存结果
        with open(chap_path, 'w', encoding='utf-8') as f:
            f.write(polished_text)
        
        # 构造结果信息
        msg = f"✅ 第{chap_num}章润色完成 | 原字数：{original_len:,} → 润色后字数：{len(polished_text):,} | 问题数：{len(issues)}"
        if issues:
            msg += f"\n⚠️  遗留问题：{'、'.join(issues[:3])}{' 等' if len(issues) > 3 else ''}"
        return True, msg
    except Exception as e:
        return False, f"❌ 执行异常：{str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法：")
        print("  单章润色：python polish_chapter.py <章节号> <章节目录路径> [Python解释器路径]")
        print("  示例：python polish_chapter.py 1 D:\\Writer\\novel-project\\chapters")
        sys.exit(1)
    
    chap = int(sys.argv[1])
    chapters_dir = sys.argv[2]
    python_path = sys.argv[3] if len(sys.argv) >=4 else None
    
    success, msg = polish_single_chapter(chap, chapters_dir, python_path)
    print(msg)
    sys.exit(0 if success else 1)