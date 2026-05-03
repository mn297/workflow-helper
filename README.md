# workflow-helper

git config --global alias.lol "log --oneline --graph --decorate --all"

###  Isaac Sim
```
sudo tee /etc/sysctl.d/99-inotify.conf <<EOF
fs.inotify.max_user_watches=524288
fs.inotify.max_user_instances=1024
EOF
sudo sysctl --system
```

Verify
```
sysctl fs.inotify.max_user_watches fs.inotify.max_user_instances
```

Nuke Isaac Sim
```
# The install itself
rm -rf ~/isaacsim

# User config + cache (these can cause "internal conflicts" between versions, per NVIDIA docs)
rm -rf ~/.local/share/ov
rm -rf ~/.cache/ov
rm -rf ~/.nvidia-omniverse
rm -rf ~/Documents/Kit  # only if you don't have other Kit-based apps
```

IsaacLab
```
uv pip uninstall --python env_isaaclab/bin/python torch torchvision torchaudio triton

uv pip install --python env_isaaclab/bin/python \
  torch torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/cu130

uv pip uninstall --python env_isaaclab/bin/python torch torchvision torchaudio triton

```

### Ubuntu

Cursor allowlist
```
ls, grep, cat, find, cd, colcon, diff, head, tail, less, wc, file, tree, realpath, dirname, basename, stat, which, whereis, locate, rg, echo, printf, pwd, env, printenv, whoami, date, uname, git status, git log, git diff, git branch, git show, git remote, cmake, make, cargo, npm, pip, python, node, rustc, gcc, ps, top, htop, free, df, du, lsblk, nvidia-smi
```

Fixes for the Black Screen on Wake
https://forums.developer.nvidia.com/t/590-48-01-no-display-after-wake-from-suspend-pageflip-timed-out-this-is-a-bug-in-the-nvidia-drm-kernel-driver/359173

You can sometimes recover the display by pressing Ctrl+Alt+F1 then Ctrl+Alt+F7 this forces the display to reinitialize without rebooting.


```
sudo systemctl enable nvidia-suspend.service
sudo systemctl enable nvidia-resume.service
sudo systemctl enable nvidia-hibernate.service
```

sudo nano /etc/default/grub
```

Add `NVreg_PreserveVideoMemoryAllocations=1` to `GRUB_CMDLINE_LINUX_DEFAULT`, so it looks something like:
```
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash NVreg_PreserveVideoMemoryAllocations=1"


# Disable automatic suspend
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'

# Set screen blank to just dim, not turn off GPU output
gsettings set org.gnome.desktop.session idle-delay 0


# Disable screen blank/timeout
gsettings set org.gnome.desktop.session idle-delay 0

# Disable automatic suspend
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'

# Disable screen lock
gsettings set org.gnome.desktop.screensaver lock-enabled false
gsettings set org.gnome.desktop.screensaver idle-activation-enabled false


# Nuclear option — restart the display manager (GDM for Ubuntu)
sudo systemctl restart gdm

# If that doesn't work, try:
sudo systemctl restart display-manager


# Ubuntu Hibernate Setup Guide

## System Info

- **RAM:** 62Gi
- **Swap file:** `/swap.img` on `/dev/nvme0n1p5`
- **GPU:** Nvidia dGPU (Lenovo laptop)

---

## 1. Check Current Swap

```bash
swapon --show
free -h
```

If swap is smaller than RAM, continue to step 2. Otherwise skip to step 3.

## 2. Resize Swap File to Match RAM

```bash
sudo swapoff /swap.img
sudo fallocate -l 64G /swap.img
sudo chmod 600 /swap.img
sudo mkswap /swap.img
sudo swapon /swap.img
```

Verify:

```bash
swapon --show
free -h
```

## 3. Get Resume Offset

```bash
sudo filefrag -v /swap.img | head -4
# Note the first number under "physical_offset"
```

## 4. Configure GRUB

```bash
sudo nano /etc/default/grub
```

Update the line to (replace `XXXXX` with your offset from step 3):

```
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash resume=/dev/nvme0n1p5 resume_offset=XXXXX NVreg_PreserveVideoMemoryAllocations=1"
```

Apply changes:

```bash
sudo update-grub
sudo update-initramfs -u
```

## 5. Enable Nvidia Hibernate Services

```bash
sudo systemctl enable nvidia-suspend.service
sudo systemctl enable nvidia-resume.service
sudo systemctl enable nvidia-hibernate.service
```

Create modprobe config:

```bash
echo 'options nvidia NVreg_PreserveVideoMemoryAllocations=1' | sudo tee /etc/modprobe.d/nvidia-power-mgmt.conf
sudo update-initramfs -u
```

## 6. Test Hibernate

```bash
sudo systemctl hibernate
```

If the system powers off and resumes correctly from swap, it works.

## 7. Enable Hibernate in the UI

Create a PolicyKit rule:

```bash
sudo nano /etc/polkit-1/localauthority/50-local.d/enable-hibernate.pkla
```

Paste this:

```ini
[Enable Hibernate]
Identity=unix-user:*
Action=org.freedesktop.login1.hibernate;org.freedesktop.login1.handle-hibernate-key
ResultActive=yes
```

Reboot. Hibernate should now appear in the power menu.

Optionally install a GNOME extension for a hibernate button:

```bash
sudo apt install gnome-shell-extension-prefs
# Then search for "Hibernate Status Button" in GNOME Extensions
```

## 8. (Optional) Replace Suspend with Hibernate

If you want the lid close / power button to hibernate instead of suspend:

```bash
sudo nano /etc/systemd/logind.conf
```

Uncomment and set:

```ini
HandleLidSwitch=hibernate
HandleLidSwitchExternalPower=hibernate
```

Restart the service:

```bash
sudo systemctl restart systemd-logind
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Black screen after resume | Ensure nvidia services are enabled (step 5) |
| Hibernate fails silently | Check swap size ≥ RAM, verify resume= param |
| No hibernate option in UI | Check polkit rule (step 7), reboot |
| Slow hibernate | Normal — writing full RAM to disk takes time |
| Resume drops to login | Working as intended — re-enter password |