# Desktop on the iGPU, CUDA on the RTX 5070 Ti

Machine: ASUS TUF GAMING B650-E WIFI, Ryzen 9 9950X3D, Ubuntu 24.04, GNOME Shell 46, NVIDIA driver 580. `prime-select` is `on-demand`.

The desktop draws on the GPU that owns the monitor cables. CUDA still uses the RTX 5070 Ti when the cables are on the motherboard.

| GPU | PCI | DRM | Memory |
|---|---|---|---|
| NVIDIA GeForce RTX 5070 Ti | `01:00.0` `[10de:2c05]` | `card1`, `/dev/dri/renderD128` | 16 GB |
| Radeon in the 9950X3D | `0c:00.0` `[1002:13c0]` | `card2`, `/dev/dri/renderD129` | 2 GB |

The motherboard rear panel has one DisplayPort (`card2-DP-1`) and one HDMI (`card2-HDMI-A-1`). Put both monitors there.

| Monitor | Cable | Mode |
|---|---|---|
| Main panel | motherboard DisplayPort | 6144×3456, desktop 3072×1728, primary |
| Portrait panel | motherboard HDMI | 2560×1440, rotated to 1440×2560 |

`prime-select on-demand` sends extra 3D work to the NVIDIA card. It does not move the desktop. The Radeon is a 2-compute-unit part. This desktop runs on it, and it feels heavier than on the 5070 Ti.

## After you move the cables

Log out, then log in. The old session keeps its NVIDIA allocations. `gnome-shell`, Cursor, Chromium, and Discord stay on `renderD128` until they start again. Cursor and Discord pass `--render-node-override=/dev/dri/renderD128`.

A GL or Vulkan program that must use the 5070 Ti needs the offload variables. CUDA does not.

```bash
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia __VK_LAYER_NV_optimus=NVIDIA_only <app>
prime-run <app>
```

## Check which GPU owns the picture

`card1-*` is the 5070 Ti. `card2-*` is the Radeon.

```bash
for c in /sys/class/drm/card*-*; do
  [ -f "$c/status" ] || continue
  echo "$(basename "$c") status=$(cat "$c/status") enabled=$(cat "$c/enabled") mode=$(head -1 "$c/modes" 2>/dev/null)"
done

xrandr --query | awk '/ connected|Screen /'

echo -n "amdgpu busy "; cat /sys/class/drm/card2/device/gpu_busy_percent
awk '{printf "amdgpu vram_used_MiB %.1f\n", $1/1048576}' /sys/class/drm/card2/device/mem_info_vram_used

nvidia-smi
```

Both monitors are on the Radeon when `card1-*` is disconnected, `card2-DP-1` and `card2-HDMI-A-1` are connected, and `nvidia-smi` shows `Disp.A` Off. NVIDIA memory near zero means the session started after the cable move.

## VRAM in the top bar

Astra Monitor shows 5070 Ti memory in the top bar. It reads `nvidia-smi` every 2 seconds. Hover the GPU indicator for used and total GB.

Run this from a graphical login:

```bash
~/workflow-helper/ubuntu/setup.sh astra
```

The script is [`astra-monitor.sh`](astra-monitor.sh). It installs `monitor@astraext.github.io`, enables it, and points the GPU header at this card (`0000:01:00.0`, `10de:2c05`).

If the desktop hitches every few seconds, raise `gpu-update` (seconds, range 1 to 10) or set `gpu-header-show` to `false`. The schema is `org.gnome.shell.extensions.astra-monitor`.

## When the desktop turns slow

The Radeon draws both monitors and composites every window. It has one graphics queue. When one app keeps that queue full, every window waits, including apps that draw on the 5070 Ti: their frames cross to the Radeon before they reach a monitor. While Cursor kept the Radeon busy, a browser frame took 1 ms to draw and waited 34 ms (median) to reach the screen.

Run this in a terminal:

```bash
gpuclean
```

`gpuclean` runs [`gpu_clean.py`](gpu_clean.py). It does three things:

1. It finds orphan headless browsers: headless Chrome or Chromium whose test script died, so systemd adopted them. They use RAM, not the GPU. One prompt kills them all (default yes).
2. It measures for 3 seconds how much of the Radeon's graphics engine each app uses.
3. For each app at 10 % or more, it asks y/N (default no):

| Busy app | What `gpuclean` does |
|---|---|
| `cursor`, `Discord`, `opera`, `chrome` | Restarts only the GPU process of the app. The app starts a new one, and the windows flash and redraw. |
| `vlc`, `spotify`, `totem`, `mpv`, `celluloid` | Closes the player. VLC with one screencast open used 15 %. |
| `Xwayland` | Lists the X11 apps. Each frame of an X11 app is copied on the Radeon. Pause the app that animates: a WebGL tab, a video, a Rerun viewer. |
| `gnome-shell` | Nothing. Its share falls when the other apps stop drawing. |

Then it measures again and prints the available RAM before and after.

Chromium starts a new GPU process each time the old one gets SIGTERM. The test killed it 4 times in a row. Cursor and Discord are Electron apps on the same Chromium code, but the restart is untested on them. If a Cursor window stays black, restart Cursor. A Cursor restart ends every terminal in Cursor, and any Claude Code session in them.

To measure only, without prompts:

```bash
python3 ~/workflow-helper/ubuntu/gpu_load.py 3     # per-app share of every GPU engine, from /proc/<pid>/fdinfo
```

`./ubuntu/setup.sh apps` adds the alias to `~/.bashrc`. To add it by hand:

```bash
echo "alias gpuclean='python3 ~/workflow-helper/ubuntu/gpu_clean.py'" >> ~/.bashrc
```
