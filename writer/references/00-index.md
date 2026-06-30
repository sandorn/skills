# Writer Skill 文件索引与依赖图

> SKILL.md 是权威入口。本文件仅补充 SKILL.md 未覆盖的**依赖关系**信息。

## 文件→脚本依赖

| 文件 | 依赖脚本 |
|------|---------|
| `quality.md` | audit.py, pad_chapter.py, split_paragraphs.py |
| `review.md` | agents/ (4 templates) |
| `review-cycle.md` | audit.py, audit_5dim.py, fact_db.py, report_panorama.py |
| `post-review-fix.md` | audit.py, pad_chapter.py, split_paragraphs.py, audit_5dim.py |
| `optimize.md` | analyze_hook.py, audit.py, pad_chapter.py |
| `style-transfer.md` | polish.py, style-sop.md |
| `deploy.md` | audit.py, pad_chapter.py |
| `write.md` | audit.py |
| `project-knowledge-base.md` | fact_db.py, report_panorama.py |
| `hard-bans.md` | audit.py (--dump-bans 校验) |
| `manual-polish.md` | 无（三零原则禁止脚本） |

## 文风预设

| 文件 | 说明 |
|------|------|
| `presets/fanqie-quick-anti.md` | 番茄爆款轻松逆袭风（polish.py --style 默认） |

## 已移除文件

- `fix-template-cleanup.md` → 模板复制检测已集成到 `audit.py`，修复流程见 `write-pitfalls.md`
- `setting-audit-gaming-manifest.md` → 项目特定遗留文件
- `project-review-novel-gaming-manifest.md` → 项目特定遗留文件
