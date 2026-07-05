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
SKILL_DIR = Path(__file__).resolve().parent.parent
DOTENV_PATH = SKILL_DIR / ".env"
DOUBAO_API_KEY = os.environ.get("DOUBAO_API_KEY", "")
DOUBAO_BASE_URL = os.environ.get("DOUBAO_BASE_URL", os.environ.get("DOUBAO_BASIC_URL", "https://ark.cn-beijing.volces.com/api/v3"))
DOUBAO_MODEL = os.environ.get("DOUBAO_MODEL", os.environ.get("DOUBAO_NODEL", "doubao-seed-evolving"))

if DOTENV_PATH.exists():
    for line in DOTENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k = k.strip(); v = v.strip().strip("\"'")
            if k == "DOUBAO_API_KEY" and not DOUBAO_API_KEY:
                DOUBAO_API_KEY = v
            elif k in ("DOUBAO_BASE_URL", "DOUBAO_BASIC_URL"):
                DOUBAO_BASE_URL = v
            elif k in ("DOUBAO_MODEL", "DOUBAO_NODEL"):
                DOUBAO_MODEL = v

# ── System Prompt（发给豆包 的 system message）──────────────
POLISH_SYSTEM_PROMPT = """你是网文润色师。你收到的正文剧情已锁定，你只能做文字层面的优化。

【最高优先级红线——违反即失败】
❌ 不得修改任何剧情事件、事件顺序
❌ 不得删除任何对话、人物选择、伏笔点位
❌ 不得新增任何情节、角色行为、剧情转折
❌ 不得调换段落顺序、事件先后
❌ 不得修改人物对话的核心内容、立场、态度

【仅开放的文字优化权限】
✅ 短句拆分：将超过42字的长句拆分为多句，增强阅读节奏
✅ 网文口语化对话：添加口语助词（嗯、啧、行吧、得嘞、靠），调整对话节奏
✅ 感官细节补充：每场景穿插1-2处环境音/气味/触感细节
✅ 情绪张力放大：通过人物微表情、身体反应强化情绪表达
✅ 爽点强化：打脸/突破/反转场景用更锋利的措辞
✅ 消除流水账：将"然后...然后..."的平铺直叙转为有节奏的叙事

【字数约束】
润色不得大幅改变正文字数。润色后字数波动不超过原文的 ±15%。
目标字数范围: 2800-3600 字（最低 2500，最高 4500）。

【轻量化设计】
你只接收本章相关的人设信息和情绪基调，不加载全书世界观。
这能降低 token 消耗，同时让你更聚焦于文字本身。

【输出要求】
直接返回完整润色后的章节文本。不附带任何说明、注释、修改建议。"""

# ── MCP Server ─────────────────────────────────────────────
server = FastMCP(
    name="novel-doubao",
    instructions="Doubao-2.1-turbo webnovel chapter polisher. RED LINE locked plot — text optimization only.",
)


@server.tool(
    name="polish_chapter",
    description="""[POLISHER — 豆包-2.1-turbo 锁定式润色]

## 模型定位
你是文字优化师，不是编辑。收到的正文剧情已最终锁定，你仅做文字层面的打磨。

## ⛔ 最高优先级红线（违反即退回重处理）
以下操作绝对禁止：
1. 不得修改、删除、新增、调换任何剧情事件
2. 不得修改人物对话的核心内容、立场、态度
3. 不得新增或删除角色选择、行为、伏笔点位
4. 不得调整事件顺序、段落结构
5. 不得增删任何情节线索

## ✅ 仅开放的文字优化权限
- 短句拆分：长句断短，增强阅读节奏
- 网文口语化对话：添加口语助词（嗯、啧、靠、行吧、得嘞）
- 感官细节补充：每场景1-2处环境音/气味/触感
- 情绪张力放大：通过微表情、身体反应强化情绪
- 爽点强化：打脸/突破/反转场景用更锋利的措辞
- 消除流水账：将平铺直叙转为有节奏的叙事

## 字数约束
润色后字数波动不超过原文的 ±15%。
目标范围: 2800-3600 字（最低 2500，最高 4500）。

## 轻量化设计
仅接收本章角色状态摘要、本章情绪基调、草稿文本。
不加载全书完整世界观，降低 token 消耗。

## 输出格式
直接返回完整润色后的章节文本，无任何附加说明、注释、建议。

## 输入参数
- chapter_characters: 本章出场角色的当前状态摘要（姓名/修为/情绪/目标）
- chapter_mood_tone: 本章情绪基调（如：紧张、爽快、压抑、热血、温情）
- draft_text: DeepSeek 生成的原始初稿全文""",
)
async def polish_chapter(
    chapter_characters: str,
    draft_text: str,
    chapter_mood_tone: str = "中性",
) -> str:
    """Polish a webnovel chapter using Doubao-2.1-turbo."""

    if not DOUBAO_API_KEY:
        return "ERROR: DOUBAO_API_KEY 未配置。请在 novel-pipeline/.env 中设置。"

    user_message = f"""【本章角色状态】
{chapter_characters}

【本章情绪基调】
{chapter_mood_tone}

【草稿正文】
{draft_text}

【指令】
请润色以上草稿。严格遵守：
- 不修改情节、对话内容、角色选择、伏笔
- 可拆分长句、增加感官细节、强化情绪张力
- 不增删事件顺序、不添加新情节
- 仅输出润色后的完整章节文本"""

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                f"{DOUBAO_BASE_URL}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {DOUBAO_API_KEY}",
                },
                json={
                    "model": DOUBAO_MODEL,
                    "messages": [
                        {"role": "system", "content": POLISH_SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.6,
                    "max_tokens": 8192,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return content

    except httpx.HTTPStatusError as e:
        return f"ERROR: 豆包 API 返回错误 {e.response.status_code}: {e.response.text[:500]}"
    except httpx.RequestError as e:
        return f"ERROR: 网络请求失败: {str(e)}"
    except Exception as e:
        return f"ERROR: 未知错误: {str(e)}"


if __name__ == "__main__":
    server.run(transport="stdio")
