# GNOME session crash with the 4K monitor on the Legion 5 laptop

Machine: Lenovo Legion 5 16IRX9 (`83DG`), Ubuntu 24.04, GNOME Shell 46 with mutter `46.2-1ubuntu0.24.04.18` on Wayland, NVIDIA driver 580. The GPU and monitor tables are in [`gpu-laptop.md`](gpu-laptop.md). On Wayland, GNOME names the HDMI port `HDMI-5`. The kernel names it `card2-HDMI-A-5`.

## Symptom

On Wayland, the desktop session closes without a warning. All apps close and the login screen opens. The laptop does not reboot. The Xorg session does not have this crash.

The log shows these lines before each crash:

```text
gnome-shell: Failed to use stored monitor configuration: Invalid mode 3840x2160 (143.999) for monitor 'IOC 32M2V        '
gnome-shell: Failed to make current: EGL failed to allocate resources for the requested operation.
kernel: gnome-shell[...]: segfault at ffffffffffffffec ip ... error 5 in libmutter-14.so.0.0.0[1980b1,...]
kernel: nvidia-modeset: WARNING: GPU:0: Unable to read EDID for display device IOC 32M2V (HDMI-0)
kernel: nvidia-modeset: WARNING: GPU:0: HDMI FRL link training failed.
```

The crash report is `/var/crash/_usr_bin_gnome-shell.1000.crash`. It shows `Signal: 11` (`SIGSEGV`).

## Cause

Two faults work together. The HDMI link is the trigger. A bug in mutter turns the trigger into a crash.

The HDMI link to the monitor drops for a short time, about every 65 seconds. The kernel then cannot read the EDID. EDID is the data block in which a monitor lists its modes. The drop-outs also occur at the login screen, with no user session open.

4K at 144 Hz over HDMI needs FRL. FRL is the high-speed link mode of HDMI 2.1. FRL link training fails at each mode set. When the link comes back, the 144 Hz mode is sometimes missing. GNOME then builds the monitor layout again.

The HDMI port connects to the NVIDIA GPU, but the Intel iGPU is the primary GPU. The primary GPU is the GPU that draws the desktop. For each frame on the HDMI monitor, mutter copies the frame to the NVIDIA GPU. After a drop-out, this copy fails with `Failed to make current`, and `copy_shared_framebuffer_gpu()` returns NULL.

The function `meta_onscreen_native_swap_buffers_with_damage()` does not test the buffer for NULL. It gives the NULL buffer to `meta_drm_buffer_ensure_fb_id()`. That function reads from the NULL buffer, and gnome-shell stops with `SIGSEGV`. The code is in `src/backends/native/meta-onscreen-native.c`.

On Wayland, gnome-shell is also the display server. When it stops, every window loses its connection to the display, and all apps close. The Xorg session does not use this code. On Xorg, the X server does the copy, and the slow monitor problem in [`gpu-laptop.md`](gpu-laptop.md) applies instead.

Upstream mutter fixed the bug in GNOME 47. The fix is commit [`e3891781`](https://gitlab.gnome.org/GNOME/mutter/-/commit/e3891781804dfda1896f9e286bc0f1a55ef39d63) from merge request [3817](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/3817). With the fix, a failed copy makes mutter skip the frame. For 24.04 (Noble), Ubuntu set the related bug [LP #2069565](https://bugs.launchpad.net/bugs/2069565) to `Won't Fix`. An update of the Ubuntu 24.04 packages will not remove the bug.

## Make sure of the cause

```bash
echo $XDG_SESSION_TYPE    # wayland
journalctl -b -o short | grep -E 'Failed to make current|segfault.*libmutter|Unable to read EDID|FRL link training'
journalctl -b -o cat | grep -E 'selected (as )?primary'
```

If `Failed to make current` comes directly before `segfault ... libmutter-14`, the crash is this bug. The last command names the primary GPU. Without a fix, it shows `GPU /dev/dri/card1 selected primary from builtin panel presence`. `card1` is the Intel iGPU.

To get the source line of the crash, run gdb with debuginfod. Debuginfod downloads the debug symbols for the installed package.

```bash
gdb -batch -iex 'set debuginfod enabled on' -ex 'info line *0x1980b1' /usr/lib/x86_64-linux-gnu/libmutter-14.so.0.0.0
```

The offset `0x1980b1` comes from the `segfault` line. It is correct only for this build of `libmutter-14-0`.

## Fixes

These fixes are not tested on this machine yet. Fix 1 is the selected fix.

| Fix | Stops the drop-outs | Removes the crash path | Cost |
|---|---|---|---|
| 1. NVIDIA is the primary GPU | No | Yes, for the HDMI monitor | The NVIDIA GPU stays on. Shorter battery life. |
| 2. Discrete GPU mode in the BIOS | No | Yes | Shortest battery life. BIOS change. |
| 3. Stop the drop-outs | Yes | No | New cable or port, or 60 Hz. |
| 4. Xorg session | No | Yes | Slow second monitor. |
| 5. Patch mutter | No | Yes | Own build. Repeat after each mutter update. |
| 6. Newer Ubuntu release | No | Yes | Breaks ROS 2 Jazzy. |
| 7. Report the bug to Ubuntu | No | No | None. |

### Fix 1: NVIDIA is the primary GPU

The udev rule [`61-mutter-primary-gpu.rules`](61-mutter-primary-gpu.rules) adds the tag `mutter-device-preferred-primary` to the NVIDIA GPU (`10de:28e0`). When the kernel adds a device, a udev rule can set properties on it. Mutter reads the tag at login and makes that GPU the primary GPU. The NVIDIA GPU then draws the desktop and sends the frames to the HDMI port directly.

Frames for the laptop panel then go to the Intel iGPU with a copy. The laptop panel does not drop out, so a failed copy is less likely. The NULL bug stays in the code. If the copy to the Intel iGPU fails, the session can still stop.

1. Install the rule:

   ```bash
   sudo cp ~/workflow-helper/ubuntu/61-mutter-primary-gpu.rules /etc/udev/rules.d/
   sudo udevadm control --reload
   sudo udevadm trigger --subsystem-match=drm
   ```

2. Make sure that the NVIDIA GPU has the tag. The command must print `mutter-device-preferred-primary`.

   ```bash
   udevadm info -q property -n /dev/dri/card2 | grep -o mutter-device-preferred-primary
   ```

3. Save your work and reboot.
4. After you log in, make sure that mutter uses the rule. The output must be `GPU /dev/dri/card2 selected primary given udev rule`.

   ```bash
   journalctl -b -o cat | grep 'selected primary given udev rule'
   ```

To undo the fix, delete `/etc/udev/rules.d/61-mutter-primary-gpu.rules` and reboot.

If the login screen does not come back after the reboot, press Ctrl+Alt+F3 and log in on the text console. Then run `sudo rm /etc/udev/rules.d/61-mutter-primary-gpu.rules` and `sudo reboot`.

The NVIDIA GPU stays on while you are logged in. On battery power, the battery life is shorter.

### Fix 2: discrete GPU mode in the BIOS

The laptop has a MUX switch. A MUX switch is a hardware switch that connects the laptop panel to the NVIDIA GPU. In discrete mode, the NVIDIA GPU drives both monitors and mutter copies no frames. The crash path is then not used for either monitor.

Follow the steps in Fix 2 of [`gpu-laptop.md`](gpu-laptop.md). The battery life is the shortest of all the fixes. Each change of the mode needs a restart into the BIOS.

### Fix 3: stop the drop-outs

These changes act on the trigger. The crash path stays in the code, but a crash needs a drop-out first.

- If the monitor has a DisplayPort or USB-C input, connect it to a USB-C port of the laptop. DisplayPort does not use FRL.
- If you stay on HDMI, use a certified Ultra High Speed HDMI cable. 4K at 144 Hz needs this cable class.
- Turn off the automatic input switch and the deep sleep mode in the monitor menu. Some monitors drop the connection on an inactive input about once a minute.
- Set the monitor to 3840×2160 at 60 Hz in Settings > Displays. At 60 Hz, HDMI uses TMDS, the older link mode, and not FRL. 120 Hz also needs FRL.

To find the GPU that drives each USB-C port, run this command with the monitor connected:

```bash
grep -H . /sys/class/drm/card*-DP-*/status
```

A port on `card1` connects to the Intel iGPU. The Intel iGPU then drives both monitors with no copy, but it can be at its limit (see [`gpu-laptop.md`](gpu-laptop.md)). A port on `card2` connects to the NVIDIA GPU, and the copy stays.

### Fix 4: Xorg session

At the login screen, click your user name. Click the gear icon at the bottom right and select "Ubuntu on Xorg". The Xorg session does not use the crash path. If gnome-shell stops on Xorg, it restarts and the apps stay open.

On Xorg, the Intel iGPU draws both monitors and the X server copies the frames to the NVIDIA GPU. The second monitor is then slow (see [`gpu-laptop.md`](gpu-laptop.md)).

### Fix 5: patch mutter

The patch [`mutter-46.2-skip-null-fb.patch`](mutter-46.2-skip-null-fb.patch) adds the missing NULL test to the Ubuntu mutter 46.2 source. If the copy fails, mutter skips the frame, as upstream commit `e3891781` does. The patch applies to `46.2-1ubuntu0.24.04.18`. It is not built or tested.

1. Enable the source packages and install the build tools:

   ```bash
   sudo sed -i 's/^Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/ubuntu.sources
   sudo apt update
   sudo apt build-dep mutter
   sudo apt install devscripts quilt
   ```

2. Get the source and add the patch:

   ```bash
   mkdir -p ~/src && cd ~/src
   apt source mutter=46.2-1ubuntu0.24.04.18
   cd mutter-46.2
   export QUILT_PATCHES=debian/patches
   quilt import ~/workflow-helper/ubuntu/mutter-46.2-skip-null-fb.patch
   quilt push
   dch --local nullfb "Skip the frame when the secondary GPU copy fails (LP: #2069565)"
   ```

3. Build the packages. `nocheck` skips the test suite.

   ```bash
   DEB_BUILD_OPTIONS=nocheck dpkg-buildpackage -us -uc -b
   ```

4. Install the four packages that are on this machine, and hold them:

   ```bash
   cd ~/src
   sudo apt install ./libmutter-14-0_*nullfb1_amd64.deb ./gir1.2-mutter-14_*nullfb1_amd64.deb \
     ./mutter-common_*nullfb1_all.deb ./mutter-common-bin_*nullfb1_amd64.deb
   sudo apt-mark hold libmutter-14-0 gir1.2-mutter-14 mutter-common mutter-common-bin
   ```

5. Log out and log in again.

The hold stops all mutter updates from Ubuntu, also security updates. When Ubuntu releases a new mutter, remove the hold, update, and do the steps again with the new version.

To undo the fix, remove the hold and install the Ubuntu packages again:

```bash
sudo apt-mark unhold libmutter-14-0 gir1.2-mutter-14 mutter-common mutter-common-bin
sudo apt install --allow-downgrades libmutter-14-0=46.2-1ubuntu0.24.04.18 gir1.2-mutter-14=46.2-1ubuntu0.24.04.18 \
  mutter-common=46.2-1ubuntu0.24.04.18 mutter-common-bin=46.2-1ubuntu0.24.04.18
```

### Fix 6: newer Ubuntu release

A newer Ubuntu release has GNOME 47 or later, which has the upstream fix. The ROS 2 Jazzy packages in `/opt/ros/jazzy` are for Ubuntu 24.04 only. An upgrade breaks the ROS 2 workspaces on this laptop. Do not use this fix while the robot work needs Jazzy.

### Fix 7: report the bug to Ubuntu

This fix does not change the laptop. It asks Ubuntu for an SRU. An SRU (stable release update) is a fix for a released Ubuntu version.

```bash
ubuntu-bug /var/crash/_usr_bin_gnome-shell.1000.crash
```

In the report, name LP #2069565 and upstream commit `e3891781`. For 24.04, Ubuntu set LP #2069565 to `Won't Fix`, so an SRU is not likely.
