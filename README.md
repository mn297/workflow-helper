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

Installs [SimpleEnglish](https://github.com/AminBlg/SimpleEnglish), [i-have-adhd](https://github.com/ayghri/i-have-adhd), and [Context7](https://github.com/upstash/context7) (`ctx7` CLI + MCP), then links the repo skills in [`skills/`](skills/) (docstring summaries, explaining new topics, plain paper notes, grounded primer, human maintainer pass, project docs layout, explainer films). [Caveman](https://github.com/JuliusBrussee/caveman) skills install for Cursor and Codex. Claude Code gets `caveman-commit` plus the local hook in [`ubuntu/claude/hooks/caveman.sh`](ubuntu/claude/hooks/caveman.sh), not the caveman plugin. It also installs the status line [`ubuntu/claude/statusline-command.sh`](ubuntu/claude/statusline-command.sh): `Opus | 45k/1.0M ctx | xhigh`. Claude plugins are simple-english, i-have-adhd, and mattpocock-skills. Context7 on Claude is MCP only. Set `CONTEXT7_API_KEY` or reuse the key already in `~/.cursor/mcp.json` / `~/.claude.json`. [RTK](https://github.com/rtk-ai/rtk) is optional.

```bash
./ubuntu/setup-llm.sh          # skills / plugins (default)
./ubuntu/setup-llm.sh rtk      # optional: binary + hooks
./ubuntu/setup-llm.sh all      # RTK + skills
```

| Topic | File |
|---|---|
| tmux config: resize repaint, mouse copy to clipboard | [`ubuntu/tmux.conf`](ubuntu/tmux.conf) |
| Cursor keybindings, `settings.json`, extensions, allowlist | [`ubuntu/cursor/`](ubuntu/cursor/) |
| Spec format for agent plus human: outline, EARS requirements, test and decision tables, Mermaid rules | [`spec-format.md`](spec-format.md) |

## Isaac Sim

See [`ubuntu/isaacsim.md`](ubuntu/isaacsim.md). Sysctl file: [`ubuntu/99-inotify.conf`](ubuntu/99-inotify.conf).

Building 6.x from source on Ubuntu 24.04:

| Topic | File |
|---|---|
| Repo-local GCC 11 + git-lfs (no system change) | [`ubuntu/isaacsim_toolchain.sh`](ubuntu/isaacsim_toolchain.sh) |
| NVIDIA 580 driver (RTX needs >= 550.90.07) | [`ubuntu/isaacsim_nvidia_driver.sh`](ubuntu/isaacsim_nvidia_driver.sh) |
| Headless physics smoke test | [`ubuntu/isaacsim_smoke.py`](ubuntu/isaacsim_smoke.py) |

## Adobe Acrobat Reader

[`ubuntu/acrobat-reader.sh`](ubuntu/acrobat-reader.sh) installs Adobe Acrobat Reader DC under Wine. It needs no sudo, because Wine comes from the WineHQ Flatpak, installed for the current user.

```bash
./ubuntu/acrobat-reader.sh                  # install; keeps a finished install
./ubuntu/acrobat-reader.sh --replace        # wipe the install and reinstall
./ubuntu/acrobat-reader.sh uninstall        # keeps the Wine Flatpak
LOGPIXELS=144 ./ubuntu/acrobat-reader.sh    # UI scale: 96 = 100 %, 192 = 200 %
```

Open a PDF with `acroread file.pdf`, with the "Adobe Acrobat Reader DC" menu entry, or with Open With in the file manager. To make Reader the default PDF app, run `xdg-mime default acroread.desktop application/pdf`.

The script pins Reader 2020.013.20074, because newer builds break under Wine. It follows the recipe of the community [acrordrdc snap](https://github.com/mmtrt/acrordrdc-snap). The Wine prefix, the folder that holds the Windows install, is `~/.var/app/org.winehq.Wine/data/acrordr` (1.2 GB). Without `LOGPIXELS`, the script reads the DPI of the primary screen. It picks 100 % below 192 dpi, 200 % from 192 dpi, and 300 % from 288 dpi.

> **Warning:** Reader 2020 gets no security updates. Its protected mode, the Windows sandbox for PDF code, is off, because it crashes under Wine. The Flatpak shows Reader only Documents, Desktop, Downloads, Music, Pictures, Videos and the files you open with it, but Reader still has network access. Open only PDFs you trust.

The launcher [`ubuntu/acrobat-reader/acroread`](ubuntu/acrobat-reader/acroread) opens a second PDF as a tab in the running Reader. A wineserver is the Wine process that holds one prefix together, and two wineservers on one prefix can corrupt it. Each `flatpak run` has its own `/tmp` and its own process IDs, so a plain second launch starts a second wineserver. The launcher shares the wineserver socket folder and joins the process ID namespace of the running Reader.

| Problem | Fix |
|---|---|
| `Reader or its wineserver runs on ...` | Close Reader, wait 3 seconds, and run the script again. |
| Reader hangs and does not close | `flatpak kill org.winehq.Wine`. This stops every app in the Wine Flatpak. |
| UI too small or too large | `LOGPIXELS=144 ./ubuntu/acrobat-reader.sh`, then restart Reader. |

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

If `KEYS` includes `fn`, the setup removes the brightness keys from the GNOME brightness control. If it does not, the setup gives them back. GNOME 46 (Ubuntu 24.04) keeps these keys in gsd-media-keys, the GNOME service for keyboard shortcuts. The setup restarts this service, because the service keeps its old shortcut until a restart. GNOME 49 and later (Ubuntu 26.04) keep the keys in GNOME Shell, which applies the change immediately.

Earlier versions used xbindkeys. When you typed on a different keyboard, the keymap changed, and xbindkeys lost its keys. The setup removes the old xbindkeys binding.

The feature works in X11 and Wayland sessions. On X11, the script gets the cursor position from xdotool. Wayland does not give the cursor position to other programs. For Wayland, the setup installs the GNOME Shell extension [`cursor-brightness@workflow-helper`](ubuntu/cursor-brightness@workflow-helper/). The extension tells the script the connector name of the monitor under the cursor, for example `DP-1`. The script then reads the EDID of that connector from `/sys/class/drm`.

After the first setup in a Wayland session, log out and log in again. GNOME Shell loads a new extension only at login.

The first press on an external monitor takes about 3 seconds. The script finds the i2c bus of the monitor from its EDID, the identity block that the monitor sends. It keeps the result until reboot, so later presses take about 0.3 seconds.

| Problem | Fix |
|---|---|
| External monitor does not change | Turn on DDC/CI in the menu of the monitor. Then run `ddcutil detect`. |
| Wayland: `no answer from the shell extension cursor-brightness@workflow-helper.` | Log out and log in again. If the error stays, run `gnome-extensions info cursor-brightness@workflow-helper` and make sure that the state is `ACTIVE`. |
| No key does anything | Make sure that the shortcuts exist in Settings > Keyboard > Custom Shortcuts. If they do not, run `./ubuntu/setup.sh brightness` again. |
| Fn keys change only the laptop panel, not the monitor under the cursor | The GNOME brightness control has the keys again. Run `./ubuntu/setup.sh brightness` again. It restarts gsd-media-keys. |
| Keys do nothing on the lock screen | This is expected. The GNOME lock screen takes all keys. |
| Disable | Delete the "Brightness ... (workflow-helper)" shortcuts in Settings > Keyboard > Custom Shortcuts. Then run `gnome-extensions disable cursor-brightness@workflow-helper`. |

### Red mouse cursor

This section makes the mouse cursor red with a black outline. The default size is 48 px. The GNOME default is 24 px.

```bash
./ubuntu/setup.sh cursor            # red cursor, 48 px
SIZE=64 ./ubuntu/setup.sh cursor    # 24, 32, 48, 64 or 96
```

The script [`ubuntu/red-cursor.py`](ubuntu/red-cursor.py) copies the Ubuntu Yaru cursors to `~/.icons/Yaru-Red`. It changes the black fill to red and the white outline to black. The shadow stays black.

Apps that are open keep the old cursor until you restart them. Some apps need a new login.

To go back to the Ubuntu cursor, run:

```bash
gsettings reset org.gnome.desktop.interface cursor-theme
gsettings reset org.gnome.desktop.interface cursor-size
```

| Topic | File |
|---|---|
| Desktop on the iGPU, CUDA on the 5070 Ti, VRAM in the top bar, `gpuclean` when the desktop turns slow | [`ubuntu/gpu.md`](ubuntu/gpu.md) |
| Slow second monitor on the Legion 5 laptop (HDMI on the RTX 4060) | [`ubuntu/gpu-laptop.md`](ubuntu/gpu-laptop.md) |
| GNOME session crash with the 4K HDMI monitor on the Legion 5 laptop (Wayland) | [`ubuntu/gnome-crash-laptop.md`](ubuntu/gnome-crash-laptop.md) |
| Power, wake, hibernate | [`ubuntu/power.md`](ubuntu/power.md) |
| mt7925e S3 resume | [`ubuntu/setup_mt7925e_unbind.sh`](ubuntu/setup_mt7925e_unbind.sh) |
| Shared bash history (`Ctrl+R`) | [`ubuntu/bash_history.sh`](ubuntu/bash_history.sh) |
