# Writer Skill 文件索引与依赖图

> SKILL.md 是权威入口。本文件仅补充 SKILL.md 未覆盖的**依赖关系**信息。

## 文件→脚本依赖

| 文件 | 依赖脚本 |
|------|---------|
| `quality.md` | audit.py, split_paragraphs.py |
| `review.md` | agents/ (4 templates) |
| `review-cycle.md` | audit.py, fact_db.py, report_panorama.py |
| `post-review-fix.md` | audit.py, split_paragraphs.py |
| `style-transfer.md` | polish.py, style-sop.md |
| `deploy.md` | audit.py, split_paragraphs.py |
| `write.md` | audit.py |
| `hard-bans.md` | audit.py (--dump-bans 校验) |
| `manual-polish.md` | 无（三零原则禁止脚本） |

## 文风预设

| 文件 | 说明 |
|------|------|
| `presets/fanqie-quick-anti.md` | 番茄爆款轻松逆袭风（polish.py --style 默认） |

## 已移除 (v7.8 激进精简)

- `pad_chapter.py` → 字数注入器已废弃，改为手工扩充
- `audit_5dim.py` → 功能已集成到 audit.py
- `backup.py` → 改用 git commit
- `publishable-check.md` → 被 review daily 吸收
- `memory.md` → 被 fact_db.py query 吸收
- `opening-craft.md` → 不可达，删除
- `project-knowledge-base.md` → 不可达，删除
- `corruption-fix-bu-shi.md` → 核心教训已写入硬禁令 B08
- `optimize.md` → 钩子分析用 analyze_hook.py，手工优化见 manual-polish.md
- `fix-template-cleanup.md` → 模板检测已集成到 audit.py
- `setting-audit-gaming-manifest.md` → 项目特定遗留
- `project-review-novel-gaming-manifest.md` → 项目特定遗留
