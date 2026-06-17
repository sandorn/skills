---
name: moke:revise
description: Revise chapter based on audit / 根据审计修订章节
---

<objective>
Fix issues identified in the audit while maintaining chapter quality.
</objective>

<process>
1. 读取审计报告和待修订章节
   - 章节路径：`books/<书名>/chapters/第N章-<标题>.md`

2. 生成修订版本

3. 保存修订后的章节（覆盖原文件）

4. 更新章节摘要
</process>
