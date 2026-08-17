#!/usr/bin/env bash
# Re-apply the Cursor-agent / tmux color fix onto the installed claude-auto-retry.
# Idempotent. Safe to run after npm update or `claude-auto-retry install`.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

die() { echo "error: $*" >&2; exit 1; }
info() { echo "==> $*"; }

find_pkg_root() {
  local cand
  if [[ -n "${CLAUDE_AUTO_RETRY_ROOT:-}" && -f "${CLAUDE_AUTO_RETRY_ROOT}/src/launcher.js" ]]; then
    echo "$CLAUDE_AUTO_RETRY_ROOT"
    return
  fi
  # Prefer the launcher path baked into the shell wrapper, if present.
  if [[ -f "${HOME}/.bashrc" ]]; then
    cand=$(grep -oE '/[^"]+/claude-auto-retry/src/launcher\.js' "${HOME}/.bashrc" 2>/dev/null | head -1 || true)
    if [[ -n "$cand" && -f "$cand" ]]; then
      echo "$(cd "$(dirname "$cand")/.." && pwd)"
      return
    fi
  fi
  # npm global root (nvm / system)
  if command -v npm >/dev/null 2>&1; then
    cand="$(npm root -g 2>/dev/null)/claude-auto-retry"
    if [[ -f "$cand/src/launcher.js" ]]; then
      echo "$cand"
      return
    fi
  fi
  # Common nvm layout
  for cand in "${HOME}"/.nvm/versions/node/*/lib/node_modules/claude-auto-retry; do
    if [[ -f "$cand/src/launcher.js" ]]; then
      echo "$cand"
      return
    fi
  done
  return 1
}

apply_one() {
  local patch="$1" file="$2"
  if grep -q 'sanitizeInteractiveEnv\|Drop color-killers left by non-TTY' "$file" 2>/dev/null; then
    # Already patched — confirm reverse-apply would work, then skip.
    if patch -p1 --dry-run -R -i "$patch" --directory "$(dirname "$(dirname "$file")")" >/dev/null 2>&1 \
       || grep -q 'sanitizeInteractiveEnv\|Drop color-killers left by non-TTY' "$file"; then
      info "already patched: $file"
      return 0
    fi
  fi
  # Apply from package root with -p1
  local pkg_root
  pkg_root="$(cd "$(dirname "$file")/.." && pwd)"
  if patch -p1 --dry-run -i "$patch" --directory "$pkg_root" >/dev/null 2>&1; then
    patch -p1 -i "$patch" --directory "$pkg_root" >/dev/null
    info "patched: $file"
  elif patch -p1 --dry-run -R -i "$patch" --directory "$pkg_root" >/dev/null 2>&1; then
    info "already patched: $file"
  else
    die "patch failed for $file (upstream may have changed — inspect $patch)"
  fi
}

main() {
  local pkg
  pkg="$(find_pkg_root)" || die "claude-auto-retry not found (npm i -g claude-auto-retry first)"
  info "package: $pkg"

  [[ -f "$pkg/src/launcher.js" ]] || die "missing $pkg/src/launcher.js"
  [[ -f "$pkg/src/wrapper.sh" ]] || die "missing $pkg/src/wrapper.sh"

  apply_one "$ROOT/launcher-colors.patch" "$pkg/src/launcher.js"
  apply_one "$ROOT/wrapper-colors.patch" "$pkg/src/wrapper.sh"

  # Refresh shell wrappers from the (now patched) template.
  if command -v claude-auto-retry >/dev/null 2>&1; then
    info "reinstalling shell wrapper via claude-auto-retry install"
    claude-auto-retry install
  else
    info "claude-auto-retry CLI not on PATH — patching ~/.bashrc ~/.zshrc in place"
    for rc in "${HOME}/.bashrc" "${HOME}/.zshrc"; do
      [[ -f "$rc" ]] || continue
      if grep -q 'Drop color-killers left by non-TTY' "$rc" 2>/dev/null; then
        info "already patched: $rc"
        continue
      fi
      if grep -q '# >>> claude-auto-retry >>>' "$rc"; then
        # Insert the unset block right after the "orphaned wrapper" comment line.
        python3 - "$rc" <<'PY'
import pathlib, sys
path = pathlib.Path(sys.argv[1])
text = path.read_text()
needle = "  # uninstall` first) — an orphaned wrapper must never break the claude command.\n"
insert = needle + (
    "  # Drop color-killers left by non-TTY hosts (Cursor agent) that started the tmux server.\n"
    "  unset NO_COLOR NODE_DISABLE_COLORS CURSOR_AGENT\n"
    '  [ "${FORCE_COLOR-}" = "0" ] && unset FORCE_COLOR\n'
    '  [ "${TERM-}" = "dumb" ] && unset TERM\n'
)
if needle not in text:
    sys.exit(f"marker not found in {path}")
if "Drop color-killers left by non-TTY" in text:
    print(f"already patched: {path}")
else:
    path.write_text(text.replace(needle, insert, 1))
    print(f"patched: {path}")
PY
      fi
    done
  fi

  if [[ -x "$ROOT/scrub-tmux.sh" ]]; then
    info "scrubbing live tmux env"
    "$ROOT/scrub-tmux.sh" || true
  fi

  info "done. Start a fresh \`claude\` session (old panes keep polluted process env)."
}

main "$@"
