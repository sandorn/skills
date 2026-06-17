#!/bin/bash
# sentinel.sh — 读取 .novelize-deployed sentinel 字段的工具函数

sentinel_file() {
  if [ -n "${SENTINEL_FILE:-}" ]; then
    printf '%s\n' "$SENTINEL_FILE"
  elif command -v project_root >/dev/null 2>&1; then
    printf '%s/.novelize-deployed\n' "$(project_root)"
  else
    printf '%s\n' ".novelize-deployed"
  fi
}

read_sentinel_field() {
  local field="$1"
  local file="${2:-$(sentinel_file)}"
  [ -f "$file" ] || return 0
  awk -v key="${field}:" '
    { sub(/\r$/, "") }
    substr($0, 1, length(key)) == key {
      v = substr($0, length(key) + 1)
      sub(/^[[:space:]]+/, "", v)
      n = length(v)
      if (n >= 2 && substr(v, 1, 1) == "\"" && substr(v, n, 1) == "\"") {
        v = substr(v, 2, n - 2)
      } else if (n >= 2) {
        q = sprintf("%c", 39)
        if (substr(v, 1, 1) == q && substr(v, n, 1) == q) {
          v = substr(v, 2, n - 2)
        }
      }
      sub(/[[:space:]]+$/, "", v)
      print v
      exit
    }
  ' "$file" 2>/dev/null
  return 0
}

sentinel_exists() {
  [ -f "${1:-$(sentinel_file)}" ]
}
