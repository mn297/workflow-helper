# claude-auto-retry: install and local patches

`claude-auto-retry` wraps each `claude` launch in its own tmux session and retries
after rate limits, overloads, and safeguard flags. The tmux session is also the
mirror channel: `tmux attach` from any terminal gives an exact second view of the
same Claude, with keys live in both directions.

The local patches correct two faults in the stock package. The patches target
`claude-auto-retry@0.7.3`.

## Install

```bash
npm install -g claude-auto-retry
~/workflow-helper/claude/auto-retry-colors/apply.sh
cp ~/workflow-helper/ubuntu/tmux.conf ~/.tmux.conf
```

Then start a fresh shell. Old panes keep the old process env.

Run `apply.sh` again after each of these commands:

- `npm update -g claude-auto-retry`
- `claude-auto-retry install`

`apply.sh` is idempotent. If upstream changes and a patch does not apply, the
script stops with an error. Then make new patches against the new source.

## Fault 1: no colors under Cursor

Cursor's agent shell exports `TERM=dumb`, `NO_COLOR=1`, and `FORCE_COLOR=0`.
In 0.7.3 the launcher serializes the full env to a snapshot file (upstream #68).
The pane loads that snapshot, so the color-killers reach claude and the TUI
renders without colors. `TERM=dumb` breaks the render completely.

The patch:

- The snapshot writer drops `NO_COLOR`, `NODE_DISABLE_COLORS`, `CURSOR_AGENT`,
  `FORCE_COLOR=0`, and `TERM=dumb`.
- `TERM` never crosses into the pane at all. The pane keeps the TERM that tmux
  sets (`tmux-256color`).
- The snapshot applier has the same guards, so old snapshots stay safe.
- The interactive spawn (inside an existing tmux) uses the same sanitized env.
- After `new-session`, the launcher removes the color-killers from the tmux
  global env. A server that a polluted host started gives them to every
  fallback shell.
- `src/wrapper.sh` (and the installed `~/.bashrc` / `~/.zshrc` block) unsets the
  same vars at the top of the `claude()` function.

## Fault 2: wrong-size first render

Stock 0.7.3 creates the session with `new-session -d` and no size. The session
is born 80x24, claude paints its first frame there, and the attach a moment
later resizes it mid-paint. The result is the stale-width artifact render.

The patch adds `-x <cols> -y <rows>` from the launching terminal, so the pane
has the correct size before claude starts.

## tmux config

[`ubuntu/tmux.conf`](../../ubuntu/tmux.conf) is the source of truth for
`~/.tmux.conf`. Reload into a running server with
`tmux source-file ~/.tmux.conf`. What it sets:

- **Resize**: `window-size latest`, `aggressive-resize on`, and a
  `client-resized` hook that sends `C-l`. Claude Code repaints its frame on
  `C-l`, so a resize leaves no artifacts. Readline and vim also treat `C-l` as
  redraw, so a shell pane is safe.
- **Copy**: drag-select pipes to `wl-copy` with `copy-pipe-no-clear`. The
  selection stays visible and the view does not jump. Double-click copies a
  word. Triple-click copies a line. `set-clipboard on` adds OSC 52 for remote
  attaches.
- **Colors**: `default-terminal tmux-256color` plus RGB (truecolor)
  passthrough.

## Verified facts (2026-08-19, claude-auto-retry 0.7.3, tmux 3.4, Claude Code 2.1.235)

| Fact | Value |
|---|---|
| Claude Code screen buffer in tmux | main buffer, `#{alternate_on}` = 0 |
| Claude Code mouse tracking | off, `#{mouse_any_flag}` = 0 |
| Pane TERM with this config | `tmux-256color` |
| Retry brakes (stock) | maxRetries 5, overload cap 120 min, safeguard cap 3 |
| Session name pattern | `claude-retry-<pid>-<timestamp>` |

Because `alternate_on` is 0 for claude, do not gate hooks on it. The transcript
lives in normal tmux scrollback, so wheel-up opens copy-mode with real history.

## Mirror a session

```bash
tmux ls                      # list running claude sessions
tmux attach -t <name>        # exact mirror, keys live from both terminals
```

Detach with `C-b d`. The session and claude continue.

## Files

| File | Role |
|---|---|
| `apply.sh` | find package, apply patches, reinstall shell wrapper, scrub tmux |
| `scrub-tmux.sh` | clear color-killers from live tmux global/session env |
| `launcher-colors.patch` | against `claude-auto-retry@0.7.3` `src/launcher.js` |
| `wrapper-colors.patch` | against `claude-auto-retry@0.7.3` `src/wrapper.sh` |
