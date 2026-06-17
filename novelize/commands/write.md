---
name: novelize-write
description: 正文写作 — 长/短篇自动判定，支持流水线模式
skill: novelize
---

# /novelize-write — 正文写作

统一正文写作入口，长/短篇自动判定，支持流水线一键调度。

## 基本用法

```bash
/novelize-write           # 续写下一章
/novelize-write 3         # 连续写 3 章
/novelize-write --pipeline "简介"    # 全流程：选题→设定→大纲→ch01
/novelize-write --continue           # 续写模式
/novelize-write --stage review       # 跳到审查期
/novelize-write --status             # 查询项目状态
```

## 长/短篇判定
- 项目目录中存在 `追踪/` → 长篇模式
- 项目目录中存在 `正文.md`（单文件）→ 短篇模式

## 长篇写作流程（Phase 1-5）

### Phase 1：选题定位
- Agent(architect) 确认/优化题材定位
- 输出/更新 `设定/题材定位.md`

### Phase 2：设定构建
- Agent(architect) 构建世界观
- Agent(designer) 设计核心角色
- 输出 `设定/世界观/`、`设定/角色/`

### Phase 3：大纲排布
- Agent(architect) 排布大纲
- 输出 `大纲/`

### Phase 4：逐章写作（循环）
- Step 1：Agent(explorer) → context_load 加载上下文
- Step 2：Agent(writer) → 正文写作
- Step 3（按需）：Agent(designer) → 对话质量优化
- Step 4（按需）：Agent(researcher) → 外部资料研究
- Step 5：Agent(writer) → 格式合规 + 更新 `追踪/上下文.md`

### Phase 5：质检
- Agent(checker) → 一致性检查
- Agent(writer) → 去AI味（6 Gate）
- 硬性禁令扫描

## 短篇写作流程（Phase 1-4）

### Phase 1：选题+设定
- Agent(architect) → 题材定位 + 设定
- Agent(designer) → 角色设计

### Phase 2：大纲
- Agent(architect) → 小节大纲

### Phase 3：逐节写作
- Agent(writer) → 正文写作
- 每节 800+ 字，50-65 行

### Phase 4：质检
- Agent(checker) → 一致性检查
- Agent(writer) → 去AI味
- 禁令扫描

## 流水线模式（--pipeline）

`/novelize-write --pipeline "简介"` 自动串联：
1. 提取书名+题材从简介
2. Agent(architect) → 题材定位
3. Agent(architect) → 世界观
4. Agent(designer) → 角色设计
5. Agent(architect) → 大纲
6. Agent(explorer) → context_load
7. Agent(writer) → ch01 正文
8. Auto-review quick mode

中间产出即时写入文件，支持断点续传。
