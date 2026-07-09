#!/usr/bin/env python3
"""
Doubao Text Polisher MCP Server (stdio transport)
模块3: 豆包-2.1-turbo 锁定式润色
Tool Description = 模块3全部规则（RED LINE），Claude CLI 读取即加载规则
"""
import os, sys, json, asyncio
from pathlib import Path
import httpx
from mcp.server.fastmcp import FastMCP

# ── .env 加载 ──────────────────────────────────────────────
# 路径调整：读取Skill根目录的.env
SKILL_DIR = Path(__file__).resolve().parent.parent
DOTENV_PATH = SKILL_DIR / ".env"

# 先读取.env配置，优先级最高
if DOTENV_PATH.exists():
    for line in DOTENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k = k.strip(); v = v.strip().strip("\\\"'")
            os.environ[k] = v

# 再从环境变量读取
DOUBAO_API_KEY=os.env...Y", "")
DOUBAO_BASE_URL = os.environ.get("DOUBAO_BASE_URL", os.environ.get("DOUBAO_BASIC_URL", "https://ark.cn-beijing.volces.com/api/v3"))
DOUBAO_MODEL = os.environ.get("DOUBAO_MODEL", os.environ.get("DOUBAO_NODEL", "doubao-seed-evolving"))

# ── System Prompt（发给豆包 的 system message）──────────────
POLISH_SYSTEM_PROMPT = """你是网文润色师。你收到的正文剧情已锁定，你只能做文字层面的优化。

【最高优先级红线——违反即失败】
1. 绝对不能修改剧情、人设、伏笔、战力体系、世界观设定，所有修改仅针对文字表达、流畅度、节奏感、爽感
2. 不能增减剧情内容，原文的对话、动作、场景、情节必须100%保留
3. 不能修改原文的专有名词、人名、地名、功法名、物品名等
4. 绝对不能出现AI写作的生硬套话、空洞描写

【润色规则】
1. 保持原文的叙事风格、语气、节奏不变
2. 优化语句通顺度，修正错别字、语病、不通顺的句子
3. 拆分过长的句子和段落，适配手机阅读，每段控制在2-5行最佳
4. 优化对话的自然度，符合人物身份和性格
5. 适当增加细节描写提升代入感，但不能新增剧情
6. 提升爽点的感染力，强化情绪表达
7. 删除冗余的修饰词、重复的表述
8. 调整语序让读起来更流畅，符合中文阅读习惯

【输出要求】
1. 只输出润色后的完整正文，不需要任何解释、说明、标记
2. 保持原文的段落结构，不要合并或拆分大的段落
3. 原文的标点符号、换行、格式尽量保留，除非明显错误
"""

mcp = FastMCP("novel-doubao")

@mcp.tool()
def polish_chapter(draft_text: str, chapter_characters: str = "", chapter_mood_tone: str = "中性") -> str:
    """
    润色小说章节，严格遵守润色规则，不修改剧情
    Args:
        draft_text: 待润色的章节原文
        chapter_characters: 章节人物设定/上下文参考
        chapter_mood_tone: 章节情绪基调（默认中性）
    Returns:
        润色后的完整正文
    """
    try:
        headers = {
            "Authorization": f"Bearer {DOUBAO_API_KEY}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {"role": "system", "content": POLISH_SYSTEM_PROMPT},
        ]
        
        if chapter_characters:
            messages.append({"role": "user", "content": f"章节上下文参考：{chapter_characters}"})
        
        messages.append({"role": "user", "content": f"请严格遵守润色规则，润色以下章节正文，只输出润色后的内容：\n\n{draft_text}"})
        
        payload = {
            "model": DOUBAO_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 16000
        }
        
        response = httpx.post(
            f"{DOUBAO_BASE_URL.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            return f"ERROR: API请求失败，状态码：{response.status_code}，错误：{response.text[:500]}"
    
    except Exception as e:
        return f"ERROR: 润色过程出错：{str(e)}"

if __name__ == "__main__":
    mcp.run()
