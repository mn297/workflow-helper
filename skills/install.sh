#!/usr/bin/env bash
# Symlink docstring-summary skills into agent skill dirs.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p ~/.agents/skills ~/.cursor/skills ~/.claude/skills
for s in writing-docstring-summaries writing-docstring-summaries-strict; do
	for d in ~/.agents/skills ~/.cursor/skills ~/.claude/skills; do
		ln -sfn "$ROOT/$s" "$d/$s"
	done
done
echo "Linked writing-docstring-summaries{,-strict} into ~/.agents ~/.cursor ~/.claude"
