"""
模板B: 润色请求模板
========================================
脚本可直接调用的标准请求构建器。
MCP Server 内部使用，也可被外部 PowerShell/Python 脚本独立调用。

可插入变量:
  - chapter_characters: 本章出场角色状态摘要
  - chapter_mood_tone: 本章情绪基调
  - draft_text: 原始初稿全文
"""

POLISH_USER_TEMPLATE = """【本章角色状态】
{chapter_characters}

【本章情绪基调】
{chapter_mood_tone}

【草稿正文】
{draft_text}

【指令】
请润色以上草稿。严格遵守以下规则：
1. 不修改任何情节、对话核心内容、角色选择、伏笔点位
2. 可拆分长句、补充感官细节（声/嗅/触/视）、强化情绪张力
3. 可优化对话口语化程度、消除平铺流水账
4. 不增删事件顺序、不添加新情节
5. 仅输出润色后的完整章节文本"""


def build_polish_request(
    chapter_characters: str,
    draft_text: str,
    chapter_mood_tone: str = "中性",
) -> str:
    """
    构建润色请求的用户消息。

    Args:
        chapter_characters: 本章出场角色状态摘要
            格式示例: "主角名(角色定位/当前状态/情绪/当前目标); 反派名(定位/状态/行动目的)"
        draft_text: 初稿生成模型输出的原始初稿全文
        chapter_mood_tone: 本章情绪基调
            可选: "紧张" "爽快" "压抑" "热血" "温情" "悬疑" "中性"

    Returns:
        格式化的用户消息文本，可直接作为 API chat message 的 user content
    """
    return POLISH_USER_TEMPLATE.format(
        chapter_characters=chapter_characters,
        chapter_mood_tone=chapter_mood_tone,
        draft_text=draft_text,
    )


# ── 独立调用示例 ──────────────────────────────────────────
if __name__ == "__main__":
    import sys, json

    if len(sys.argv) >= 2:
        characters = sys.argv[1] if len(sys.argv) > 1 else "主角(当前状态)"
        draft = sys.argv[2] if len(sys.argv) > 2 else "（草稿文本）"
        mood = sys.argv[3] if len(sys.argv) > 3 else "中性"

        result = build_polish_request(characters, draft, mood)
        print(json.dumps({"user_message": result}, ensure_ascii=False))
    else:
        print("=" * 60)
        print("模板B: 润色请求构建器")
        print("=" * 60)
        sample = build_polish_request(
            chapter_characters="主角(主角/当前能力等级/情绪/当前目标); 敌对角色(定位/能力/行动目的)",
            draft_text="主角在修炼。突然有异常动静。一个神秘人出现。两人交手。主角击退对方。",
            chapter_mood_tone="紧张",
        )
        print(sample)
        print("=" * 60)
        print("模块可被 MCP Server import 或外部脚本独立调用")
