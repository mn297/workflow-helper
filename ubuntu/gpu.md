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
