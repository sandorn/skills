#!/bin/bash
# session-end.sh — 会话结束时按需记录最后状态
# 设计原则：默认静默且不写文件
set -euo pipefail

source "$(dirname "$0")/lib/common.sh"

if [ "${NOVELIZE_SESSION_LOG:-0}" != "1" ]; then
  exit 0
fi

BOOK_DIR=$(discover_active_book)
if [ -n "$BOOK_DIR" ] && [ -d "$BOOK_DIR/追踪" ]; then
  echo "[$(date '+%Y-%m-%dT%H:%M:%S%z')] session ended" >> "$BOOK_DIR/追踪/session-log.txt"
fi
