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

Installs [SimpleEnglish](https://github.com/AminBlg/SimpleEnglish), [i-have-adhd](https://github.com/ayghri/i-have-adhd), and [Context7](https://github.com/upstash/context7) (`ctx7` CLI + MCP), then links the repo docstring skills. [Caveman](https://github.com/JuliusBrussee/caveman) skills install for Cursor and Codex. Claude Code gets `caveman-commit` plus the local hook in [`ubuntu/claude/hooks/caveman.sh`](ubuntu/claude/hooks/caveman.sh), not the caveman plugin. It also installs the status line [`ubuntu/claude/statusline-command.sh`](ubuntu/claude/statusline-command.sh): `Opus | 45k/1.0M ctx | xhigh`. Claude plugins are simple-english, i-have-adhd, and mattpocock-skills. Context7 on Claude is MCP only. Set `CONTEXT7_API_KEY` or reuse the key already in `~/.cursor/mcp.json` / `~/.claude.json`. [RTK](https://github.com/rtk-ai/rtk) is optional.

```bash
./ubuntu/setup-llm.sh          # skills / plugins (default)
./ubuntu/setup-llm.sh rtk      # optional: binary + hooks
./ubuntu/setup-llm.sh all      # RTK + skills
```

| Topic | File |
|---|---|
| tmux config: resize repaint, mouse copy to clipboard | [`ubuntu/tmux.conf`](ubuntu/tmux.conf) |
| Cursor keybindings, `settings.json`, extensions, allowlist | [`ubuntu/cursor/`](ubuntu/cursor/) |

## Isaac Sim

See [`ubuntu/isaacsim.md`](ubuntu/isaacsim.md). Sysctl file: [`ubuntu/99-inotify.conf`](ubuntu/99-inotify.conf).

Building 6.x from source on Ubuntu 24.04:

| Topic | File |
|---|---|
| Repo-local GCC 11 + git-lfs (no system change) | [`ubuntu/isaacsim_toolchain.sh`](ubuntu/isaacsim_toolchain.sh) |
| NVIDIA 580 driver (RTX needs >= 550.90.07) | [`ubuntu/isaacsim_nvidia_driver.sh`](ubuntu/isaacsim_nvidia_driver.sh) |
| Headless physics smoke test | [`ubuntu/isaacsim_smoke.py`](ubuntu/isaacsim_smoke.py) |

## Ubuntu

On a fresh machine, one command installs git, clones this repo to `~/workflow-helper`, and then runs
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
| Slow | `20` to `40` |
| Default | `120` |
| Fast | `180` to `240` |

The mouse must be plugged in. If the script picks the wrong device, set the name with `DEVICE="Logitech MX Master 3S"`.

No other program must hold an exclusive grab on the mouse. HID++ daemons
(OpenLogi, Solaar rules, logiops) grab the same device, and the first one to
start wins. If you install one, the scroll mapping stops without an error. The
buttons still work as back/forward, but the hold-to-scroll never fires. To find
the conflict, run:

```bash
journalctl -u input-remapper-daemon -n 40 | grep -i grab   # "Device or resource busy" = conflict
systemctl --user mask --now openlogi-agent.service         # then rerun ./ubuntu/setup.sh scroll
```

```bash
input-remapper-control --command stop-all     # disable
input-remapper-control --command autoload     # re-enable
input-remapper-gtk                            # GUI
```

### Brightness keys follow the cursor

[`ubuntu/cursor-brightness.sh`](ubuntu/cursor-brightness.sh) changes the brightness of the monitor under the mouse cursor. Each key press moves the brightness 10% up or down. The laptop panel changes through logind. An external monitor changes through DDC/CI, a protocol that lets the computer set monitor controls over the video cable.

```bash
./ubuntu/setup.sh brightness                # Fn brightness keys and numpad +/-
KEYS=numpad ./ubuntu/setup.sh brightness    # numpad 8 = up, numpad 5 = down
KEYS=fn ./ubuntu/setup.sh brightness        # Fn brightness keys only
STEP=5 ./ubuntu/setup.sh brightness         # 5% per press
```

`KEYS` takes one or more of `fn`, `plusminus` and `numpad`, separated by commas. The numpad keys work with NumLock on or off. While a numpad key is bound, it does not type its character.

The keys are GNOME custom shortcuts. You can see them in Settings > Keyboard > Custom Shortcuts, as "Brightness up (workflow-helper)" and "Brightness down (workflow-helper)". GNOME keeps them after a reboot.

If `KEYS` includes `fn`, the setup removes the brightness keys from the GNOME brightness control. If it does not, the setup gives them back. In both cases, the setup restarts gsd-media-keys, the GNOME service for keyboard shortcuts. Without the restart, the service keeps its old brightness shortcut, and the new shortcut cannot use the key.

Earlier versions used xbindkeys. xbindkeys lost its keys after each keymap change, for example when you typed on a different keyboard. The setup removes the old xbindkeys binding.

The feature works only in an X11 session ("Ubuntu on Xorg"). Wayland does not give the cursor position to other programs.

The first press on an external monitor takes about 3 seconds. The script finds the i2c bus of the monitor from its EDID, the identity block that the monitor sends. It keeps the result until reboot, so later presses take about 0.3 seconds.

| Problem | Fix |
|---|---|
| External monitor does not change | Turn on DDC/CI in the menu of the monitor. Then run `ddcutil detect`. |
| No key does anything | Make sure that the shortcuts exist in Settings > Keyboard > Custom Shortcuts. If they do not, run `./ubuntu/setup.sh brightness` again. |
| Fn keys change only the laptop panel, not the monitor under the cursor | The GNOME brightness control has the keys again. Run `./ubuntu/setup.sh brightness` again. It restarts gsd-media-keys. |
| Keys do nothing on the lock screen | This is expected. The GNOME lock screen takes all keys. |
| Disable | Delete the "Brightness ... (workflow-helper)" shortcuts in Settings > Keyboard > Custom Shortcuts. |

| Topic | File |
|---|---|
| Power, wake, hibernate | [`ubuntu/power.md`](ubuntu/power.md) |
| mt7925e S3 resume | [`ubuntu/setup_mt7925e_unbind.sh`](ubuntu/setup_mt7925e_unbind.sh) |
| Shared bash history (`Ctrl+R`) | [`ubuntu/bash_history.sh`](ubuntu/bash_history.sh) |
