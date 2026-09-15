#!/bin/bash
#
# Agent skills for Claude Code, Codex, and Cursor. RTK is optional.
#
# Best-effort: no `set -e`, so one broken install does not abort the rest, and
# every failure is listed at the end.
#
# Usage:
#   ./setup-llm.sh              # skills / plugins
#   ./setup-llm.sh skills       # same as default
#   ./setup-llm.sh rtk          # optional: binary + hooks
#   ./setup-llm.sh all          # RTK + skills
#
set -uo pipefail

set -E
FAILED=()
trap 'FAILED+=("line $LINENO: $BASH_COMMAND")' ERR
trap 'printf "\nfailures: %s\n" "${#FAILED[@]}"; printf "  %s\n" "${FAILED[@]:-none}"' EXIT

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"

SECTION="${1:-skills}"
run_section() { [ "$SECTION" = all ] || [ "$SECTION" = "$1" ]; }

case "$SECTION" in
all | rtk | skills) ;;
*)
	echo "Usage: $0 [skills|rtk|all]" >&2
	exit 1
	;;
esac

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

[ "$(id -u)" -eq 0 ] && {
	echo "Run as your normal user, not root." >&2
	exit 1
}

# Official agent slugs for `npx skills add --agent`.
SKILL_AGENTS="claude-code cursor codex"
SKILL_PACKAGES=(
	JuliusBrussee/caveman
	AminBlg/SimpleEnglish
	ayghri/i-have-adhd
	upstash/context7
)

# Reuse CONTEXT7_API_KEY or a key already in local MCP config. Never print it.
# Without a key, ctx7 setup --yes would start an OAuth device flow and hang.
context7_api_key() {
	python3 - <<'PY'
import json, os
from pathlib import Path

def pick(value):
    text = (value or "").strip()
    if text.lower().startswith("bearer "):
        text = text[7:].strip()
    return text if text.startswith("ctx7sk-") else ""

key = pick(os.environ.get("CONTEXT7_API_KEY"))
if key:
    print(key)
    raise SystemExit

def walk(obj):
    if isinstance(obj, dict):
        for name, value in obj.items():
            if name in ("CONTEXT7_API_KEY", "Authorization", "authorization") and isinstance(value, str):
                found = pick(value)
                if found:
                    return found
            found = walk(value)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = walk(item)
            if found:
                return found
    return ""

for path in (Path.home() / ".cursor/mcp.json", Path.home() / ".claude.json"):
    try:
        found = walk(json.loads(path.read_text()))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        continue
    if found:
        print(found)
        raise SystemExit
PY
}

# Fake a TTY when the Claude CLI refuses a non-interactive pipe.
run_maybe_tty() {
	if [ -t 0 ]; then
		"$@"
		return
	fi
	if command -v script >/dev/null; then
		script -qefc "$*" /dev/null
		return
	fi
	"$@"
}

########################################################################## rtk
if run_section rtk; then

	say "Installing or updating RTK"
	# Re-run of the official installer replaces ~/.local/bin/rtk in place.
	curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/master/install.sh | sh
	hash -r
	export PATH="$HOME/.local/bin:$PATH"
	rtk --version
	rtk gain >/dev/null

	# --auto-patch skips the settings.json / hooks.json prompt so this is safe
	# to run from setup.sh or a non-interactive shell.
	say "Wiring RTK into Claude Code"
	rtk init -g --auto-patch

	say "Wiring RTK into Codex"
	rtk init -g --codex

	say "Wiring RTK into Cursor"
	rtk init -g --agent cursor --auto-patch

	say "RTK hook status"
	rtk init --show

fi

####################################################################### skills
if run_section skills; then

	if ! command -v npx >/dev/null; then
		echo "npx is required for skills; install Node first." >&2
		false
	else
		# Global + explicit agents: without -g, skills land in $PWD/.agents.
		for pkg in "${SKILL_PACKAGES[@]}"; do
			say "Installing skill $pkg"
			npx -y skills add "$pkg" -g -y --agent $SKILL_AGENTS
		done

		say "Linking repo docstring skills"
		bash "$REPO/skills/install.sh"

		say "Installing ctx7 CLI"
		npm install --global ctx7@latest
		hash -r

		# MCP writes agent config; CLI+skills installs find-docs. Combined --mcp --cli
		# is CLI-only (--cli wins), so run both.
		CTX7_KEY="$(context7_api_key || true)"
		if [ -n "${CTX7_KEY:-}" ]; then
			say "Wiring Context7 MCP into Claude, Cursor, Codex"
			npx -y ctx7 setup --mcp --claude --cursor --codex -y --api-key "$CTX7_KEY"
			say "Wiring Context7 CLI skills"
			npx -y ctx7 setup --cli --claude --cursor --codex -y --api-key "$CTX7_KEY"
		else
			echo "No CONTEXT7_API_KEY (and none in ~/.cursor/mcp.json or ~/.claude.json)."
			echo "Installing CLI skills only. MCP stays unauthenticated until you set CONTEXT7_API_KEY."
			npx -y ctx7 setup --cli --claude --cursor --codex -y
		fi
		unset CTX7_KEY
	fi

	if command -v claude >/dev/null; then
		say "Installing Claude Code plugins"
		run_maybe_tty claude plugin marketplace add JuliusBrussee/caveman
		run_maybe_tty claude plugin install caveman@caveman
		run_maybe_tty claude plugin marketplace add AminBlg/SimpleEnglish
		run_maybe_tty claude plugin install simple-english@simple-english
		run_maybe_tty claude plugin marketplace add ayghri/i-have-adhd
		run_maybe_tty claude plugin install i-have-adhd@i-have-adhd
		run_maybe_tty claude plugin marketplace add upstash/context7
		run_maybe_tty claude plugin install context7@context7-marketplace
	else
		echo "claude CLI not on PATH, skipping Claude plugins"
	fi

	if command -v codex >/dev/null; then
		say "Installing Codex plugins"
		codex plugin marketplace add JuliusBrussee/caveman
		codex plugin add caveman@caveman
		codex plugin marketplace add AminBlg/SimpleEnglish
		codex plugin add simple-english@simple-english
		codex plugin marketplace add ayghri/i-have-adhd
		codex plugin add i-have-adhd@i-have-adhd
		codex plugin marketplace add upstash/context7
		codex plugin add context7@context7-marketplace
	else
		echo "codex CLI not on PATH, skipping Codex plugins"
	fi

fi
