#!/bin/bash
# session-start.sh — 显示项目状态和写作上下文摘要
# 设计原则：无可用信息时完全静默，不输出任何内容，避免污染 context
set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT=""
HAS_CONTENT=false

if [ ! -f "$HOOK_DIR/lib/common.sh" ] || [ ! -f "$HOOK_DIR/lib/sentinel.sh" ]; then
  printf '%b' "[WARN] novelize hook libraries are missing. Re-run /novelize-init to restore.\n"
  exit 0
fi

source "$HOOK_DIR/lib/common.sh"
source "$HOOK_DIR/lib/sentinel.sh"

ROOT=$(project_root)

# 部署自检
if sentinel_exists "$ROOT/.novelize-deployed"; then
  MISSING_HOOKS=""
  for hook in session-start.sh session-end.sh detect-gaps.sh pre-compact.sh post-compact.sh validate-commit.sh lib/common.sh lib/sentinel.sh; do
    if [ ! -f "$ROOT/.claude/hooks/$hook" ]; then
      MISSING_HOOKS+="$hook "
    fi
  done
  if [ -n "$MISSING_HOOKS" ]; then
    OUTPUT+="[WARN] .novelize-deployed exists but hooks are missing: $MISSING_HOOKS\n"
    OUTPUT+="  Fix: re-run /novelize-init to restore missing hooks.\n\n"
    HAS_CONTENT=true
  fi
else
  OUTPUT+="[WARN] Writing infrastructure not deployed. Run /novelize-init to initialize.\n\n"
  HAS_CONTENT=true
fi

# 显示分支和最近 commit
BRANCH=$(git -C "$ROOT" branch --show-current 2>/dev/null || echo "")
if [ -n "$BRANCH" ]; then
  OUTPUT+="=== Novelize Writing ===\n"
  OUTPUT+="Branch: $BRANCH\n"
  RECENT=$(git -C "$ROOT" log --oneline -5 2>/dev/null || true)
  if [ -n "$RECENT" ]; then
    OUTPUT+="$RECENT\n"
  fi
  OUTPUT+="\n"
  HAS_CONTENT=true
fi

# 上下文.md 摘要
BOOK_DIR=$(discover_active_book)
if [ -n "$BOOK_DIR" ] && [ -f "$BOOK_DIR/追踪/上下文.md" ]; then
  OUTPUT+="--- 当前位置 ---\n"
  SNAPSHOT=$(head -10 "$BOOK_DIR/追踪/上下文.md")
  OUTPUT+="${SNAPSHOT}\n---\n\n"
  HAS_CONTENT=true
fi

# 未完成拆文
if [ -d "$ROOT/拆文库" ]; then
  PROGRESS_COUNT=$(find "$ROOT/拆文库" -name "_progress.md" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$PROGRESS_COUNT" -gt 0 ]; then
    OUTPUT+="[INFO] $PROGRESS_COUNT incomplete analysis in 拆文库/. Run /novelize-analyze.\n"
    HAS_CONTENT=true
  fi
fi

if [ "$HAS_CONTENT" = true ]; then
  printf '%b' "$OUTPUT"
fi
