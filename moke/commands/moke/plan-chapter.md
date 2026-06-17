---
name: moke:plan-chapter
description: Plan chapter intent / 规划章节意图
---

<objective>
Generate the chapter intent including goals, conflicts, and constraints.
</objective>

<process>
1. 读取书籍设定和当前状态

2. 生成章节规划：
   - 本章目标
   - 必须保留的内容
   - 必须避免的内容
   - 冲突设计

3. 保存规划到 runtime/plan.md

4. 输出规划摘要
</process>
