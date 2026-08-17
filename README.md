# workflow-helper

git config --global alias.lol "log --oneline --graph --decorate --all"

### Claude / Cursor

Agent skills — docstring summary lines (was `verb-analog-cadence`). Two
variants, same subject:

| Skill | Use for |
|---|---|
| `writing-docstring-summaries` | writing a summary line; shape table by artifact kind |
| `writing-docstring-summaries-strict` | auditing or rewriting existing ones; edit gate first, truth rule, evidence tags |

```bash
mkdir -p ~/.agents/skills ~/.cursor/skills ~/.claude/skills
for s in writing-docstring-summaries writing-docstring-summaries-strict; do
  for d in ~/.agents/skills ~/.cursor/skills ~/.claude/skills; do
    ln -sfn ~/workflow-helper/skills/"$s" "$d/$s"
  done
done
```

`claude-auto-retry` loses TUI colors when a Cursor agent starts the tmux server
(`TERM=dumb` / `NO_COLOR=1`). Portable fix:

```bash
~/workflow-helper/claude/auto-retry-colors/apply.sh
```

See [`claude/auto-retry-colors/README.md`](claude/auto-retry-colors/README.md).

`claude-auto-retry` wraps Claude in tmux; resizing a Cursor terminal often
mangles the TUI (layout sticks to an old/narrow pane width). Add to
`~/.tmux.conf`:

```tmux
setw -g aggressive-resize on
setw -g window-size latest
```

Reload live sessions: `tmux source-file ~/.tmux.conf`. If still mangled, widen
the panel and `Ctrl+L`, or bypass the wrap with `command claude`.

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

Cursor keybindings (Linux): [`ubuntu/cursor/keybindings.json`](ubuntu/cursor/keybindings.json)

```
Ctrl+I      chat panel (toggle; also works in terminal)
Ctrl+L      chat (focus / add)
Ctrl+B      explorer / left sidebar (toggle; also works in terminal)
Ctrl+Alt+S  agent sidebar (toggle)
Ctrl+1      editor 1
Ctrl+2      editor 2
Ctrl+3      terminal (focus)
Ctrl+`      terminal (toggle)
```

Restore:

```bash
mkdir -p ~/.config/Cursor/User
cp ~/workflow-helper/ubuntu/cursor/keybindings.json ~/.config/Cursor/User/keybindings.json
```

Merge [`ubuntu/cursor/settings.json`](ubuntu/cursor/settings.json) into `~/.config/Cursor/User/settings.json`. `commandsToSkipShell` must include `toggleSidebarVisibility` (Ctrl+B) and `toggleAuxiliaryBar` (Ctrl+I). Without that, the terminal eats both keys. Ctrl+I is ASCII Tab. Also set `vim.handleKeys` `"<C-i>"`, `"<C-`>"`, `"<C-b>"` to `false` (see [`vim_vsc.json`](vim_vsc.json)).

Cursor allowlist
```
ls, grep, cat, find, cd, colcon, diff, head, tail, less, wc, file, tree, realpath, dirname, basename, stat, which, whereis, locate, rg, echo, printf, pwd, env, printenv, whoami, date, uname, git status, git log, git diff, git branch, git show, git remote, cmake, make, cargo, npm, pip, python, node, rustc, gcc, ps, top, htop, free, df, du, lsblk, nvidia-smi
```

Fixes for the Black Screen on Wake
https://forums.developer.nvidia.com/t/590-48-01-no-display-after-wake-from-suspend-pageflip-timed-out-this-is-a-bug-in-the-nvidia-drm-kernel-driver/359173

You can sometimes recover the display by pressing Ctrl+Alt+F1 then Ctrl+Alt+F7 this forces the display to reinitialize without rebooting.

mt7925e S3 resume timeout (`pci_pm_resume returns -110`)
The Wi-Fi 7 card (`14c3:7925`, driver `mt7925e`) fails to resume from S3. Unbind it. Leave MT7922 (`14c3:0616`, driver `mt7921e`) bound.

```bash
~/workflow-helper/ubuntu/setup_mt7925e_unbind.sh
```

Check: `lspci -nnk -d 14c3:7925` must show no "Kernel driver in use". `lspci -nnk -d 14c3:0616` must still show `mt7921e`.


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
| Suspend/wake hang, `mt7925e ... pci_pm_resume returns -110` | Run `ubuntu/setup_mt7925e_unbind.sh`. Do not unbind MT7922. |
| Hibernate fails silently | Check swap size ≥ RAM, verify resume= param |
| No hibernate option in UI | Check polkit rule (step 7), reboot |
| Slow hibernate | Normal — writing full RAM to disk takes time |
| Resume drops to login | Working as intended — re-enter password |



# VS Code Terminal `Ctrl+R` Bash History Fix

`Ctrl+R` is Bash history, not VS Code. By default each terminal only sees its own in-memory history, so commands from other/previous terminals don't show up.

**Fix:** append this to the end of `~/.bashrc` (do not overwrite `PROMPT_COMMAND` with a bare string — that breaks VS Code shell integration):

```bash
HISTFILE="$HOME/.bash_history"
HISTSIZE=100000
HISTFILESIZE=200000
shopt -s histappend

__sync_bash_history() {
    builtin history -a
    builtin history -n
}

if declare -p PROMPT_COMMAND 2>/dev/null | grep -q 'declare -a'; then
    PROMPT_COMMAND+=(__sync_bash_history)
elif [[ -n "${PROMPT_COMMAND:-}" ]]; then
    PROMPT_COMMAND=("$PROMPT_COMMAND" __sync_bash_history)
else
    PROMPT_COMMAND=(__sync_bash_history)
fi
```

Open a new terminal (or `source ~/.bashrc`). `declare -p PROMPT_COMMAND` should list both `__vsc_prompt_cmd` and `__sync_bash_history`.

**Verify:** run `echo vscode-history-test` in one terminal; in another, press Enter once, then `Ctrl+R` and type `vscode-history-test`.

**Notes:**
- `HISTCONTROL=ignoreboth` skips leading-space commands and consecutive duplicates — intentional, not the bug.
- `history -a` / `-n` write/read the history file; `history -c` then `history -w` wipes the file — avoid that.
