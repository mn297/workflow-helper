# Ubuntu power, wake, hibernate

Machine notes: 62Gi RAM, swap file `/swap.img` on `/dev/nvme0n1p5`, Nvidia dGPU (Lenovo laptop).

## Black screen on wake

Forum: https://forums.developer.nvidia.com/t/590-48-01-no-display-after-wake-from-suspend-pageflip-timed-out-this-is-a-bug-in-the-nvidia-drm-kernel-driver/359173

You can recover the display without a reboot. Press Ctrl+Alt+F1. Then press Ctrl+Alt+F7. This forces the display to reinitialize.

If that fails, restart the display manager (GDM on Ubuntu):

```bash
sudo systemctl restart gdm
# or
sudo systemctl restart display-manager
```

## mt7925e S3 resume timeout (`pci_pm_resume returns -110`)

The Wi-Fi 7 card (`14c3:7925`, driver `mt7925e`) fails to resume from S3. Unbind it. Leave MT7922 (`14c3:0616`, driver `mt7921e`) bound.

```bash
~/workflow-helper/ubuntu/setup_mt7925e_unbind.sh
```

`lspci -nnk -d 14c3:7925` must show no "Kernel driver in use". `lspci -nnk -d 14c3:0616` must still show `mt7921e`.

## Nvidia suspend services and GRUB

```bash
sudo systemctl enable nvidia-suspend.service
sudo systemctl enable nvidia-resume.service
sudo systemctl enable nvidia-hibernate.service
```

Add `NVreg_PreserveVideoMemoryAllocations=1` to `GRUB_CMDLINE_LINUX_DEFAULT` in `/etc/default/grub`:

```
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash NVreg_PreserveVideoMemoryAllocations=1"
```

## GNOME idle and suspend

```bash
# Disable automatic suspend
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'

# Disable screen blank / timeout (dim only; do not turn off GPU output)
gsettings set org.gnome.desktop.session idle-delay 0

# Disable screen lock
gsettings set org.gnome.desktop.screensaver lock-enabled false
gsettings set org.gnome.desktop.screensaver idle-activation-enabled false
```

## Hibernate

### 1. Current swap

```bash
swapon --show
free -h
```

If swap is smaller than RAM, continue to step 2. Otherwise skip to step 3.

### 2. Resize the swap file to match RAM

```bash
sudo swapoff /swap.img
sudo fallocate -l 64G /swap.img
sudo chmod 600 /swap.img
sudo mkswap /swap.img
sudo swapon /swap.img
```

Make sure that `swapon --show` and `free -h` show the new size.

### 3. Resume offset

```bash
sudo filefrag -v /swap.img | head -4
# Note the first number under "physical_offset"
```

### 4. GRUB

```bash
sudo nano /etc/default/grub
```

Replace `XXXXX` with the offset from step 3:

```
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash resume=/dev/nvme0n1p5 resume_offset=XXXXX NVreg_PreserveVideoMemoryAllocations=1"
```

```bash
sudo update-grub
sudo update-initramfs -u
```

### 5. Nvidia hibernate services

```bash
sudo systemctl enable nvidia-suspend.service
sudo systemctl enable nvidia-resume.service
sudo systemctl enable nvidia-hibernate.service
```

```bash
echo 'options nvidia NVreg_PreserveVideoMemoryAllocations=1' | sudo tee /etc/modprobe.d/nvidia-power-mgmt.conf
sudo update-initramfs -u
```

### 6. Test hibernate

```bash
sudo systemctl hibernate
```

If the system powers off and resumes from swap, it works.

### 7. Hibernate in the UI

```bash
sudo nano /etc/polkit-1/localauthority/50-local.d/enable-hibernate.pkla
```

```ini
[Enable Hibernate]
Identity=unix-user:*
Action=org.freedesktop.login1.hibernate;org.freedesktop.login1.handle-hibernate-key
ResultActive=yes
```

Reboot. Hibernate must appear in the power menu.

Optional GNOME button:

```bash
sudo apt install gnome-shell-extension-prefs
# Then search for "Hibernate Status Button" in GNOME Extensions
```

### 8. (Optional) Lid close hibernates

If you want the lid close / power button to hibernate instead of suspend:

```bash
sudo nano /etc/systemd/logind.conf
```

Uncomment and set:

```ini
HandleLidSwitch=hibernate
HandleLidSwitchExternalPower=hibernate
```

```bash
sudo systemctl restart systemd-logind
```

## Troubleshooting

| Problem | Fix |
|---|---|
| Black screen after resume | Make sure that Nvidia services are enabled (step 5) |
| Suspend/wake hang, `mt7925e ... pci_pm_resume returns -110` | Run `ubuntu/setup_mt7925e_unbind.sh`. Do not unbind MT7922. |
| Hibernate fails silently | Make sure that swap size is ≥ RAM, and that `resume=` is set |
| No hibernate option in UI | Make sure that the polkit rule exists (step 7), then reboot |
| Slow hibernate | Normal — writing full RAM to disk takes time |
| Resume drops to login | Working as intended — re-enter the password |
