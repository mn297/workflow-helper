# Slow second monitor on the Legion 5 laptop

Machine: Lenovo Legion 5 16IRX9 (`83DG`), Ubuntu 24.04, GNOME Shell 46 on Xorg, NVIDIA driver 580. `prime-select` is `on-demand`.

On the external monitor, all apps (Cursor, Chromium, Opera) feel slow. The laptop panel feels normal.

| GPU | PCI | Driver | DRM |
|---|---|---|---|
| Intel Raptor Lake-S UHD Graphics | `00:02.0` `[8086:a78b]` | `i915` | `card1` |
| NVIDIA GeForce RTX 4060 Laptop GPU | `01:00.0` `[10de:28e0]` | `nvidia` | `card2` |

| Monitor | Port | GPU of the port | Mode |
|---|---|---|---|
| Laptop panel | `eDP-1` | Intel | 2560×1600, 165 Hz |
| IOC 32M2V | `HDMI-1-0` | NVIDIA | 3840×2160, 144 Hz, primary |

## Cause

The HDMI port of this laptop connects to the NVIDIA GPU. In `on-demand` mode, the Intel iGPU draws the full desktop for both monitors (6400×2325). Xorg then copies each frame to the NVIDIA GPU, and the NVIDIA GPU sends it to the HDMI port. This copy is called reverse PRIME. The laptop panel does not need the copy, because it connects to the Intel iGPU.

With a mostly idle desktop, the Intel iGPU ran at 1600 MHz. This is its maximum clock. The 4K monitor at 144 Hz uses all of its capacity.

GNOME on Xorg uses one frame clock for all monitors. The panel runs at 165 Hz and the monitor runs at 144 Hz. This can add stutter on one of the two monitors.

## Make sure of the cause

```bash
xrandr --listproviders                     # NVIDIA-G0 is "Sink Output": it only shows frames
xrandr --query | grep -E ' connected|\*'   # HDMI-1-0 is an NVIDIA port
prime-select query                         # on-demand
cat /sys/class/drm/card1/gt_act_freq_mhz /sys/class/drm/card1/gt_RP0_freq_mhz
```

The last command shows the current clock and the maximum clock of the Intel iGPU. If the two values are equal while the desktop is idle, the iGPU is at its limit.

## Fixes

These fixes are not tested on this machine yet. Do the quick test first.

### Quick test at 60 Hz

```bash
xrandr --output HDMI-1-0 --mode 3840x2160 --rate 60
```

If the monitor feels faster at 60 Hz, the cause is correct. To set 144 Hz again, use Settings > Displays.

### Fix 1: the NVIDIA GPU draws the desktop

```bash
sudo prime-select nvidia
sudo reboot
```

The NVIDIA GPU then draws the full desktop. The Intel iGPU only shows the frames on the laptop panel. The NVIDIA GPU does not go to sleep, so the battery life is shorter.

To go back, run `sudo prime-select on-demand` and reboot.

### Fix 2: discrete GPU mode in the BIOS

This laptop has a MUX switch. A MUX switch is a hardware switch that connects the laptop panel to the NVIDIA GPU. The second path to the panel shows as `/sys/class/drm/card2-eDP-2`.

In discrete mode, the NVIDIA GPU drives both monitors and the copy step stops. This fix gives the best result. The battery life is the shortest of the three modes.

1. Run `sudo prime-select nvidia`, so that Xorg uses the NVIDIA GPU at the next boot.
2. Restart the laptop. At the Lenovo logo, press F2 to open the BIOS.
3. Find the GPU mode setting. On Legion laptops, it is usually `GPU Working Mode` on the `Configuration` tab.
4. Set it to the discrete GPU (dGPU only) mode. Save and restart.

To go back, set the BIOS setting to the hybrid mode again. Then run `sudo prime-select on-demand` and reboot.
