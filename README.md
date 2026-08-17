# workflow-helper

This repo holds scripts, config files, and notes for this machine.

## Git

```bash
git config --global alias.lol "log --oneline --graph --decorate --all"
```

## Claude / Cursor

```bash
~/workflow-helper/skills/install.sh
```

That command links `writing-docstring-summaries` and `writing-docstring-summaries-strict` into `~/.agents`, `~/.cursor`, and `~/.claude`.

| Topic | File |
|---|---|
| `claude-auto-retry` colors and tmux TUI | [`claude/auto-retry-colors/README.md`](claude/auto-retry-colors/README.md) |
| tmux pane resize | [`ubuntu/tmux.conf`](ubuntu/tmux.conf) |
| Cursor keys, restore, allowlist | [`ubuntu/cursor/`](ubuntu/cursor/) |

## Isaac Sim

See [`ubuntu/isaacsim.md`](ubuntu/isaacsim.md). Sysctl file: [`ubuntu/99-inotify.conf`](ubuntu/99-inotify.conf).

## Ubuntu

| Topic | File |
|---|---|
| Power, wake, hibernate | [`ubuntu/power.md`](ubuntu/power.md) |
| mt7925e S3 resume | [`ubuntu/setup_mt7925e_unbind.sh`](ubuntu/setup_mt7925e_unbind.sh) |
| Shared bash history (`Ctrl+R`) | [`ubuntu/bash_history.sh`](ubuntu/bash_history.sh) |
