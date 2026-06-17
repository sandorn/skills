#!/bin/bash
# detect-gaps.sh — 检测写作项目中的 8 项缺口
# 设计原则：无缺口时完全静默，不输出任何内容，避免污染 context
set -euo pipefail

source "$(dirname "$0")/lib/common.sh"

ROOT=$(project_root)
OUTPUT=""
HAS_WARNINGS=false

declare -a BOOK_DIRS=()
while IFS= read -r dir; do
  [ -n "$dir" ] && BOOK_DIRS+=("$dir")
done < <(discover_all_books)

if [ "${#BOOK_DIRS[@]}" -eq 0 ]; then
  exit 0
fi

for BOOK_DIR in "${BOOK_DIRS[@]}"; do
  BOOK_NAME=$(basename "$BOOK_DIR")
  BOOK_OUTPUT=""

  # 1. 正文多但设定少
  CHAPTER_COUNT=0
  SETTING_COUNT=0
  if [ -d "$BOOK_DIR/正文" ]; then
    CHAPTER_COUNT=$(find "$BOOK_DIR/正文" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
  elif [ -f "$BOOK_DIR/正文.md" ]; then
    CHAPTER_COUNT=1
  fi
  if [ -d "$BOOK_DIR/设定" ]; then
    SETTING_COUNT=$(find "$BOOK_DIR/设定" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
  fi
  if [ "$CHAPTER_COUNT" -gt 10 ] && [ "$SETTING_COUNT" -lt 3 ]; then
    BOOK_OUTPUT+="[WARN] $BOOK_NAME: $CHAPTER_COUNT chapters but only $SETTING_COUNT setting files.\n"
  fi

  # 2. AI味密度扫描
  if [ -d "$BOOK_DIR/正文" ]; then
    DASH_COUNT=$(grep -c '——' "$BOOK_DIR/正文/"*.md 2>/dev/null || echo "0")
    AI_PATTERN_COUNT=$(grep -c '不是.*而是' "$BOOK_DIR/正文/"*.md 2>/dev/null || echo "0")
    if [ "$DASH_COUNT" -gt 0 ] || [ "$AI_PATTERN_COUNT" -gt 0 ]; then
      BOOK_OUTPUT+="[WARN] $BOOK_NAME: 破折号 $DASH_COUNT / AI句式 $AI_PATTERN_COUNT detected. Run /novelize-deslop.\n"
    fi
  fi

  # 3. 过期或异常伏笔
  if [ -f "$BOOK_DIR/追踪/伏笔.md" ]; then
    ABNORMAL_FORESHADOW=$(awk -F'|' '
      function trim(s) { gsub(/^[[:space:]]+|[[:space:]]+$/, "", s); return s }
      /^\|/ && $0 !~ /^\|[-[:space:]|]+$/ {
        status=trim($6)
        if (status == "" || status == "状态" || status ~ /^状态\{/) next
        if (status == "已过期" || (status != "未埋" && status != "已埋" && status != "已回收")) print
      }
    ' "$BOOK_DIR/追踪/伏笔.md" 2>/dev/null || true)
    if [ -n "$ABNORMAL_FORESHADOW" ]; then
      BOOK_OUTPUT+="[WARN] $BOOK_NAME: Overdue/abnormal foreshadowing entries detected.\n"
    fi
  fi

  # 4. 大纲缺失
  if [ -d "$BOOK_DIR/正文" ] || [ -f "$BOOK_DIR/正文.md" ]; then
    if [ -d "$BOOK_DIR/追踪" ] && [ ! -d "$BOOK_DIR/大纲" ]; then
      BOOK_OUTPUT+="[WARN] $BOOK_NAME: 正文/ exists but 大纲/ is missing.\n"
    elif [ ! -d "$BOOK_DIR/追踪" ] && [ ! -f "$BOOK_DIR/小节大纲.md" ]; then
      BOOK_OUTPUT+="[WARN] $BOOK_NAME: 正文 exists but 小节大纲.md is missing.\n"
    fi
  fi

  if [ -n "$BOOK_OUTPUT" ]; then
    OUTPUT+="Checking: $BOOK_NAME\n$BOOK_OUTPUT"
    HAS_WARNINGS=true
  fi
done

# 5. 全局拆文未完成
if [ -d "$ROOT/拆文库" ]; then
  while IFS= read -r -d '' progress_file; do
    OUTPUT+="[WARN] Incomplete analysis: ${progress_file#$ROOT/}. Run /novelize-analyze.\n"
  done < <(find "$ROOT/拆文库" -name "_progress.md" -print0 2>/dev/null || true)
fi

if [ "$HAS_WARNINGS" = true ]; then
  printf '%b' "=== Novelize Gap Detection ===\n$OUTPUT\n"
fi
