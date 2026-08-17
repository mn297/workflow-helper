# claude-auto-retry: fix missing colors under Cursor + tmux

## Symptom

Claude Code TUI launches via `claude-auto-retry` (tmux wrap) with **no colors**.
Shell prompt in the same pane still has colors.

## Cause

Cursor's agent shell exports `TERM=dumb`, `NO_COLOR=1`, `FORCE_COLOR=0`.
If that host is first to start the tmux server (or the wrapper forwards the
full env via `new-session -e`), those vars stick in tmux global/session env
and every later interactive Claude pane inherits them.

Related upstream: [PR #67](https://github.com/cheapestinference/claude-auto-retry/pull/67)
(whitelist helps secrets, but still forwards `TERM`).

## Fix (portable)

```bash
~/workflow-helper/claude/auto-retry-colors/apply.sh
```

Idempotent. Re-run after:

- `npm update -g claude-auto-retry`
- `claude-auto-retry install` (rewrites shell wrappers from package template)

Then start a **fresh** `claude` (old panes keep the polluted process env).

## Tmux resize (TUI stuck on an old pane width)

Copy [`ubuntu/tmux.conf`](../../ubuntu/tmux.conf) into `~/.tmux.conf`. Then run `tmux source-file ~/.tmux.conf`.

If the layout is still wrong, widen the panel. Then press `Ctrl+L`. Or bypass the wrap with `command claude`.

Optional live scrub without reinstall:

```bash
~/workflow-helper/claude/auto-retry-colors/scrub-tmux.sh
# or nuclear:
tmux kill-server   # only if you have no other sessions you care about
```

## What the patch does

1. **`src/launcher.js`**
   - `sanitizeInteractiveEnv()` drops `NO_COLOR` / `NODE_DISABLE_COLORS` /
     `CURSOR_AGENT` / `FORCE_COLOR=0` / `TERM=dumb`
   - `buildTmuxEnvArgs` never forwards `TERM` or `CLAUDE_AUTO_RETRY_ACTIVE`
   - inner tmux cmd `unset`s color killers before launching
   - interactive spawn uses sanitized env
   - after `new-session`, scrub those vars off tmux **global** env
2. **`src/wrapper.sh`** (+ reinstalled `~/.bashrc` / `~/.zshrc` block)
   - same `unset` at the top of the `claude()` function

## Files

| File | Role |
|------|------|
| `apply.sh` | find package, apply patches, reinstall shell wrapper, scrub tmux |
| `scrub-tmux.sh` | clear color-killers from live tmux global/session env |
| `launcher-colors.patch` | against `claude-auto-retry@0.6.2` `src/launcher.js` |
| `wrapper-colors.patch` | against `claude-auto-retry@0.6.2` `src/wrapper.sh` |
