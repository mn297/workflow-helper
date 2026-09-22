# workflow-helper

This repo holds scripts, config files, and notes for this machine.

## Git

```bash
git config --global alias.lol "log --oneline --graph --decorate --all"
```

## Claude / Codex / Cursor

```bash
~/workflow-helper/ubuntu/setup-llm.sh
```

Installs [caveman](https://github.com/JuliusBrussee/caveman), [SimpleEnglish](https://github.com/AminBlg/SimpleEnglish), [i-have-adhd](https://github.com/ayghri/i-have-adhd), and [Context7](https://github.com/upstash/context7) (`ctx7` CLI + MCP), then links the repo docstring skills. Set `CONTEXT7_API_KEY` or reuse the key already in `~/.cursor/mcp.json` / `~/.claude.json`. [RTK](https://github.com/rtk-ai/rtk) is optional.

```bash
./ubuntu/setup-llm.sh          # skills / plugins (default)
./ubuntu/setup-llm.sh rtk      # optional: binary + hooks
./ubuntu/setup-llm.sh all      # RTK + skills
```

| Topic | File |
|---|---|
| tmux config: resize repaint, mouse copy to clipboard | [`ubuntu/tmux.conf`](ubuntu/tmux.conf) |
| Cursor keys, settings, extensions, allowlist | [`ubuntu/cursor/`](ubuntu/cursor/) |

## Isaac Sim

See [`ubuntu/isaacsim.md`](ubuntu/isaacsim.md). Sysctl file: [`ubuntu/99-inotify.conf`](ubuntu/99-inotify.conf).

Building 6.x from source on Ubuntu 24.04:

| Topic | File |
|---|---|
| Repo-local GCC 11 + git-lfs (no system change) | [`ubuntu/isaacsim_toolchain.sh`](ubuntu/isaacsim_toolchain.sh) |
| NVIDIA 580 driver (RTX needs >= 550.90.07) | [`ubuntu/isaacsim_nvidia_driver.sh`](ubuntu/isaacsim_nvidia_driver.sh) |
| Headless physics smoke test | [`ubuntu/isaacsim_smoke.py`](ubuntu/isaacsim_smoke.py) |

## Ubuntu

Fresh machine, one command — installs git, clones this repo to `~/workflow-helper`, then runs
[`ubuntu/setup.sh`](ubuntu/setup.sh) from the clone:

```bash
curl -fsSL https://raw.githubusercontent.com/mn297/workflow-helper/main/ubuntu/setup.sh | bash
```

Steps are best-effort: a failed install does not stop the run, and every failure is listed at the end.

Partial reruns from the clone:

```bash
./ubuntu/setup.sh apps      # installs only
./ubuntu/setup.sh scroll    # MX Master thumb-button scroll only
```

### Thumb-button scroll speed

[`ubuntu/setup.sh`](ubuntu/setup.sh) maps MX Master side buttons (8/9) to hold-to-scroll via input-remapper. Default `SPEED` is `120` (~60 notches/sec). Higher is faster.

```bash
SPEED=80 ./ubuntu/setup.sh scroll
```

| Feel | `SPEED` |
|---|---|
| Slow | `20`–`40` |
| Default | `120` |
| Fast | `180`–`240` |

Mouse must be plugged in. Override the device name with `DEVICE="Logitech MX Master 3S"` if needed.

Nothing else may hold an exclusive grab on the mouse. HID++ daemons (OpenLogi,
Solaar rules, logiops) grab the same device and whoever starts first wins, so
installing one silently kills the scroll mapping — the buttons keep working as
back/forward, but the hold-to-scroll never fires. Diagnose with:

```bash
journalctl -u input-remapper-daemon -n 40 | grep -i grab   # "Device or resource busy" = conflict
systemctl --user mask --now openlogi-agent.service         # then rerun ./ubuntu/setup.sh scroll
```

```bash
input-remapper-control --command stop-all     # disable
input-remapper-control --command autoload     # re-enable
input-remapper-gtk                            # GUI
```

| Topic | File |
|---|---|
| Power, wake, hibernate | [`ubuntu/power.md`](ubuntu/power.md) |
| mt7925e S3 resume | [`ubuntu/setup_mt7925e_unbind.sh`](ubuntu/setup_mt7925e_unbind.sh) |
| Shared bash history (`Ctrl+R`) | [`ubuntu/bash_history.sh`](ubuntu/bash_history.sh) |
