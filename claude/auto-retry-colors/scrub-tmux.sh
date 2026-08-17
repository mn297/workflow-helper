#!/usr/bin/env bash
# Clear color-killing env vars from a live tmux server polluted by Cursor agent.
# Does NOT rewrite process environ of already-running panes — restart claude after.
set -euo pipefail

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux not installed" >&2
  exit 0
fi

if ! tmux list-sessions >/dev/null 2>&1; then
  echo "no live tmux server"
  exit 0
fi

scrub_keys=(NO_COLOR FORCE_COLOR NODE_DISABLE_COLORS CURSOR_AGENT CLAUDE_AUTO_RETRY_ACTIVE)

echo "==> scrubbing tmux global env"
for k in "${scrub_keys[@]}"; do
  tmux set-environment -gu "$k" 2>/dev/null || true
done
term="$(tmux show-environment -g TERM 2>/dev/null || true)"
if [[ "$term" == "TERM=dumb" ]]; then
  tmux set-environment -gu TERM
fi

echo "==> scrubbing claude-retry-* session env"
while IFS= read -r s; do
  [[ -z "$s" ]] && continue
  for k in "${scrub_keys[@]}"; do
    tmux set-environment -t "$s" -u "$k" 2>/dev/null || true
  done
  term="$(tmux show-environment -t "$s" TERM 2>/dev/null || true)"
  if [[ "$term" == "TERM=dumb" ]]; then
    tmux set-environment -t "$s" -u TERM 2>/dev/null || true
  fi
  echo "  cleaned $s"
done < <(tmux list-sessions -F '#{session_name}' 2>/dev/null | grep '^claude-retry-' || true)

echo "==> remaining global killers:"
tmux show-environment -g 2>/dev/null | grep -E '^(NO_COLOR|FORCE_COLOR|TERM|CURSOR_AGENT)=' || echo "  (clean)"
echo "Restart \`claude\` in a fresh pane for colors to return."
