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

# ── 直接读取.env文件，完全绕开环境变量问题 ──────────────────────────────────────────────
SKILL_DIR = Path(__file__).resolve().parent.parent
DOTENV_PATH = SKILL_DIR / ".env"

config = {}
if DOTENV_PATH.exists():
    for line in DOTENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("\"'")
            config[k] = v

# 直接从config字典取值，不需要环境变量
DOUBAO_API_KEY = config.get("DOUBAO_API_KEY", "")
DOUBAO_BASE_URL = config.get("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
DOUBAO_MODEL = config.get("DOUBAO_MODEL", "doubao-seed-evolving")

# 直接校验
if not DOUBAO_API_KEY:
    print(json.dumps({
        "jsonrpc": "2.0",
        "id": None,
        "error": {"code": -32000, "message": f"ERROR: DOUBAO_API_KEY 未找到，已读取.env内容：{list(config.keys())}"}
    }))
    sys.exit(1)

# ── System Prompt ──────────────────────────────────────────────
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
    try:
        headers = {
            "Authorization": f"Bearer {DOUBAO_API_KEY}",
            "Content-Type": "application/json"
        }
        messages = [
            {"role": "system", "content": POLISH_SYSTEM_PROMPT},
            {"role": "user", "content": f"请严格遵守润色规则，润色以下章节正文，只输出润色后的内容：\n\n{draft_text}"}
        ]
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
            return f"ERROR: API返回错误，状态码：{response.status_code}，内容：{response.text[:300]}"
    except Exception as e:
        import traceback
        return f"ERROR: 异常：{str(e)}\n{traceback.format_exc()[:300]}"

if __name__ == "__main__":
    mcp.run()
