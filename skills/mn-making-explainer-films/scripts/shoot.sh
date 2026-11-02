#!/usr/bin/env bash
# Screenshot a film page at given frames with a headless Chromium, one PNG per frame.
#   bash shoot.sh <page.html> <outdir> <frame> [<frame> ...]
# Finds Playwright's Chromium under ~/.cache/ms-playwright, else google-chrome, else chromium.
# Each shot opens the page paused at ?f=<frame>; look at every PNG with the Read tool.
set -euo pipefail
page="$(realpath "$1")"; out="$2"; shift 2
mkdir -p "$out"
bin=""
for c in "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux64/chrome "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux/chrome; do
	[ -x "$c" ] && bin="$c"
done
[ -n "$bin" ] || bin="$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)"
[ -n "$bin" ] || { echo "no Chromium found; install one with: npx playwright install chromium" >&2; exit 1; }
for f in "$@"; do
	timeout 90 nice -n 19 "$bin" --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
		--window-size=1320,1000 --virtual-time-budget=5000 --screenshot="$out/f$f.png" \
		"file://$page?f=$f" >/dev/null 2>&1 || echo "frame $f: chromium exited $?" >&2
	echo "$out/f$f.png"
done
