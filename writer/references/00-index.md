# Writer Skill 文件索引与依赖图

> SKILL.md 是权威入口。本文件仅补充 SKILL.md 未覆盖的**依赖关系**信息。

## 文件→脚本依赖

| 文件 | 依赖脚本 |
|------|---------|
| `quality.md` | audit.py, split_paragraphs.py |
| `review.md` | agents/ (4 templates), audit.py |
| `review-cycle.md` | audit.py, report_panorama.py |
| `post-review-fix.md` | audit.py, split_paragraphs.py |
| `style-transfer.md` | **novel-pipeline** `polish_chapter.py`, style-sop.md, presets/ |
| `deploy.md` | audit.py, split_paragraphs.py |
| `write.md` | audit.py, archive_facts.py, render_tracking.py |
| `hard-bans.md` | audit.py (--dump-bans 校验) |
| `manual-polish.md` | 无（三零原则禁止脚本） |
| `project-init.md` | archive_facts.py（初始化空骨架时用）|

## 文风预设

| 文件 | 说明 |
|------|------|
| `presets/fanqie-quick-anti.md` | 番茄爆款轻松逆袭风（novel-pipeline `polish_chapter.py --style-file` 消费）|

## 状态归档链（v8.3 新增）

```
写章 → chapters/ch_NNN.md
     → archive_facts.py 读 stdin JSON → .writer/state/*.json 追加事实
     → render_tracking.py 读 .writer/state/*.json → tracking/*.md 渲染（保留 <!-- user-edit --> 块）
```

## 已移除

- `scripts/polish.py` (v8.3) → 迁至 novel-pipeline skill 的 `scripts/polish_chapter.py`
- `references/memory-novel-schema.md` (v8.3) → memory-novel MCP 已废弃，改用 `.writer/state/*.json`
- `pad_chapter.py` (v7.8) → 字数注入器已废弃，改为手工扩充
- `audit_5dim.py` (v7.8) → 功能已集成到 audit.py
- `backup.py` → 改用 git commit
- `publishable-check.md` → 被 review daily 吸收
- `memory.md` → v8.0 之前的旧记忆管理，被 memory-novel 短暂替代，v8.3 最终迁至 `.writer/state/*.json`
- `opening-craft.md` / `project-knowledge-base.md` / `corruption-fix-bu-shi.md` / `optimize.md` / `fix-template-cleanup.md` / 两个 gaming-manifest 项目遗留文件（v7.8 一并清理）
