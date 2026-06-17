---
name: moke:draft
description: Write a chapter draft with full truth files / 使用完整真相文件写章节草稿
---

<objective>
Generate a single chapter draft (3000 words) based on all 7 truth files from the story state.
</objective>

<process>
1. 读取所有 7 个真相文件（路径：`books/{bookName}/story/`）：
   - current_state.md - 当前状态卡（角色位置、关系、信息、冲突）
   - particle_ledger.md - 资源账本（物品/资源增减记录，如有数值系统）
   - pending_hooks.md - 伏笔池（已埋伏笔、推进状态、回收时机）
   - chapter_summaries.md - 章节摘要（每章压缩摘要）
   - subplot_board.md - 支线进度板（各支线当前进度）
   - emotional_arcs.md - 角色情感弧线（情感变化轨迹）
   - character_matrix.md - 角色交互矩阵（关系网络、信息边界）

2. 智能过滤上下文：
   - 识别本章相关角色（主角 + 在场角色）
   - 加载相关支线和伏笔
   - 获取当前位置和场景信息
   - 提取相关关系和情感状态

3. 生成章节草稿（3000±200字）

4. 保存到 `books/<书名>/chapters/第N章-<标题>.md`
   - 文件名格式：`第1章-废材觉醒.md`
   - 必须先确保 chapters/ 目录存在
   - 文件第一行必须是 `# 第N章 <标题>` 格式

5. 调用 Observer 提取事实（9类）
6. 调用 Reflector 更新真相文件
</process>
