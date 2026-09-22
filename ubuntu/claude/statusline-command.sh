#!/bin/bash
# Concise status line: model, context tokens used / window size, effort level.
input=$(cat)

model=$(echo "$input" | jq -r '.model.display_name // "model"')
used=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
size=$(echo "$input" | jq -r '.context_window.context_window_size // 0')
effort=$(echo "$input" | jq -r '.effort.level // empty')

fmt() {
  awk -v n="$1" 'BEGIN {
    if (n >= 1000000) printf "%.1fM", n / 1000000
    else if (n >= 1000) printf "%.0fk", n / 1000
    else printf "%d", n
  }'
}

used_fmt=$(fmt "$used")
size_fmt=$(fmt "$size")

out="$model | $used_fmt/$size_fmt ctx"
[ -n "$effort" ] && out="$out | $effort"

printf '%s' "$out"
