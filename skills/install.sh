#!/usr/bin/env bash
# Symlink every repo skill (each dir with a SKILL.md) into agent skill dirs.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p ~/.agents/skills ~/.cursor/skills ~/.claude/skills
linked=()
for skill_md in "$ROOT"/*/SKILL.md; do
	s="$(basename "$(dirname "$skill_md")")"
	for d in ~/.agents/skills ~/.cursor/skills ~/.claude/skills; do
		ln -sfn "$ROOT/$s" "$d/$s"
	done
	linked+=("$s")
done
echo "Linked ${linked[*]} into ~/.agents ~/.cursor ~/.claude"
