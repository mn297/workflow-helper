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
# Caveman is not in this list. Claude Code loads one skill (caveman-commit)
# plus a local hook. The full pack is for Cursor and Codex only.
SKILL_PACKAGES=(
	AminBlg/SimpleEnglish
	ayghri/i-have-adhd
	upstash/context7
)
# Skills the caveman repo ships besides caveman-commit. Claude must not
# auto-load these; the plugin that did was replaced by ubuntu/claude/hooks.
CAVEMAN_SKILLS_NOT_FOR_CLAUDE=(
	caveman
	cavecrew
	caveman-compress
	caveman-discover
	caveman-evidence-review
	caveman-explore
	caveman-help
	caveman-learn
	caveman-manage
	caveman-optimize
	caveman-review
	caveman-setup
	caveman-stats
	compress
	investigate-first
	lean-build
	migration
	safe-refactor
	surgical-patch
	verify-and-stop
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

# Copy the local caveman hook, status line script, and user CLAUDE.md, and
# wire them into ~/.claude/settings.json without duplicating a hook entry.
install_claude_user_files() {
	local hook_dst="$HOME/.claude/hooks/caveman.sh"
	mkdir -p "$HOME/.claude/hooks"
	cp "$REPO/ubuntu/claude/hooks/caveman.sh" "$hook_dst"
	chmod +x "$hook_dst"
	cp "$REPO/ubuntu/claude/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
	cp "$REPO/ubuntu/claude/statusline-command.sh" "$HOME/.claude/statusline-command.sh"
	# The status line script parses its JSON input with jq.
	command -v jq >/dev/null || sudo apt install -y jq
	if [ ! -s "$HOME/.claude/.caveman-active" ]; then
		printf 'full\n' >"$HOME/.claude/.caveman-active"
	fi
	python3 - "$hook_dst" <<'PY'
import json
import sys
from pathlib import Path

hook = sys.argv[1]
settings_path = Path.home() / ".claude" / "settings.json"
settings = {}
if settings_path.exists() and settings_path.stat().st_size:
    settings = json.loads(settings_path.read_text())
hooks = settings.setdefault("hooks", {})


def command_block(arg, status):
    return {
        "type": "command",
        "command": f"bash {hook} {arg}",
        "timeout": 5,
        "statusMessage": status,
    }


def already(entries):
    return "hooks/caveman.sh" in json.dumps(entries)


session = hooks.setdefault("SessionStart", [])
if not already(session):
    session.append(
        {
            "matcher": "startup|resume|clear|compact",
            "hooks": [command_block("session", "Loading caveman mode")],
        }
    )
prompt = hooks.setdefault("UserPromptSubmit", [])
if not already(prompt):
    prompt.append({"hooks": [command_block("prompt", "caveman")]})
settings["statusLine"] = {
    "type": "command",
    "command": f"bash {Path.home() / '.claude' / 'statusline-command.sh'}",
}
settings_path.write_text(json.dumps(settings, indent=2) + "\n")
PY
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

		# Full caveman pack auto-loads dozens of skills into Claude Code.
		# Claude keeps caveman-commit only; terse mode is the local hook.
		say "Installing caveman skills for Cursor and Codex"
		npx -y skills add JuliusBrussee/caveman -g -y --agent cursor codex
		say "Installing caveman-commit for Claude Code"
		npx -y skills add JuliusBrussee/caveman -g -y --skill caveman-commit --agent claude-code
		for skill in "${CAVEMAN_SKILLS_NOT_FOR_CLAUDE[@]}"; do
			if [ -e "$HOME/.claude/skills/$skill" ]; then
				npx -y skills remove -g -y -a claude-code -s "$skill"
			fi
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
		# simple-english and i-have-adhd stay plugins. Caveman is a local
		# hook (the plugin loads the whole skill pack). Context7 is MCP,
		# wired above; the plugin would register a second server.
		run_maybe_tty claude plugin marketplace add AminBlg/SimpleEnglish
		run_maybe_tty claude plugin install simple-english@simple-english
		run_maybe_tty claude plugin marketplace add ayghri/i-have-adhd
		run_maybe_tty claude plugin install i-have-adhd@i-have-adhd
		run_maybe_tty claude plugin marketplace add anthropics/claude-plugins-official
		run_maybe_tty claude plugin install mattpocock-skills@claude-plugins-official

		say "Removing Claude plugins the local hook and Context7 MCP replace"
		for plugin in caveman@caveman context7@context7-marketplace; do
			if claude plugin list 2>/dev/null | grep -q "$plugin"; then
				run_maybe_tty claude plugin uninstall "$plugin" -y
			fi
		done

		say "Installing Claude caveman hook and user CLAUDE.md"
		install_claude_user_files
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
