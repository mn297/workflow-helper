#!/bin/bash
#
# Machine setup for Ubuntu 24.04: packages, dev tools, desktop apps, and the
# MX Master thumb-button scroll mapping.
#
# Best-effort: no `set -e`, so one broken install does not abort the rest, and
# every failure is listed at the end.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/mn297/workflow-helper/main/ubuntu/setup.sh | bash
#   ./setup.sh                          # everything
#   ./setup.sh apps                     # installs only
#   ./setup.sh scroll                   # thumb-scroll mapping only
#   SPEED=30 ./setup.sh scroll          # retune the scroll speed
#   DEVICE="Logitech MX Master 3S" ./setup.sh scroll
#
set -uo pipefail

# -E so failures inside functions reach the ERR trap too.
set -E
FAILED=()
trap 'FAILED+=("line $LINENO: $BASH_COMMAND")' ERR
trap 'printf "\nfailures: %s\n" "${#FAILED[@]}"; printf "  %s\n" "${FAILED[@]:-none}"' EXIT

# Supports `curl -fsSL .../ubuntu/setup.sh | bash`: piped means there is no file on
# disk, so install git, clone the repo, and re-run from the clone.
if [ ! -f "${BASH_SOURCE[0]:-}" ]; then
	REPO_DIR="${WORKFLOW_HELPER_DIR:-$HOME/workflow-helper}"
	sudo apt update
	sudo apt install -y git curl ca-certificates
	[ -d "$REPO_DIR/.git" ] || git clone https://github.com/mn297/workflow-helper.git "$REPO_DIR"
	git -C "$REPO_DIR" remote set-url --push origin git@github.com:mn297/workflow-helper.git
	exec bash "$REPO_DIR/ubuntu/setup.sh" "$@" </dev/null
fi
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SECTION="${1:-all}"
run_section() { [ "$SECTION" = all ] || [ "$SECTION" = "$1" ]; }

case "$SECTION" in
all | apps | scroll) ;;
*)
	echo "Usage: $0 [all|apps|scroll]" >&2
	exit 1
	;;
esac

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

[ "$(id -u)" -eq 0 ] && {
	echo "Run as your normal user, not root." >&2
	exit 1
}

########################################################################## apps
if run_section apps; then

	say "Updating package lists"
	sudo apt update

	say "Installing essential build tools"
	sudo apt install -y \
		build-essential \
		cmake \
		git \
		gnupg \
		lsb-release \
		wget \
		ninja-build \
		ubuntu-drivers-common \
		pciutils \
		openjdk-17-jdk \
		xbindkeys \
		xdotool curl

	say "Installing Claude Code"
	curl -fsSL https://claude.ai/install.sh | bash

	# The apt repo returns 403/GPG mismatches, so resolve the latest deb from the
	# download API instead. Use cursor.com, not www (www 308-redirects).
	say "Installing Cursor"
	CURSOR_DEB_URL="$(curl -fsSL "https://cursor.com/api/download?platform=linux-x64&releaseTrack=stable" |
		python3 -c 'import json,sys; print(json.load(sys.stdin)["debUrl"])')"
	CURSOR_DEB="/tmp/cursor.deb"
	curl -fL "$CURSOR_DEB_URL" -o "$CURSOR_DEB"
	sudo apt install -y "$CURSOR_DEB"
	rm -f "$CURSOR_DEB"
	curl https://cursor.com/install -fsS | bash # cursor-agent CLI
	mkdir -p "$HOME/.config/Cursor/User"
	cp "$HERE/cursor/keybindings.json" "$HOME/.config/Cursor/User/keybindings.json"

	# Shared bash history so Ctrl+R sees commands from other terminals
	# (including Cursor). Idempotent: the snippet is a no-op if already present.
	say "Installing shared bash history"
	if grep -q '__sync_bash_history' "$HOME/.bashrc" 2>/dev/null; then
		echo "already in ~/.bashrc"
	else
		printf '\n' >>"$HOME/.bashrc"
		cat "$HERE/bash_history.sh" >>"$HOME/.bashrc"
	fi

	say "Installing uv"
	curl -LsSf https://astral.sh/uv/install.sh | sh

	say "Installing pixi"
	curl -fsSL https://pixi.sh/install.sh | bash

	say "Installing browsers via snap"
	sudo snap install chromium opera brave

	say "Installing Spotify via snap"
	sudo snap install spotify

	# Obsidian ships a deb, but the GitHub "latest release" is the Android APK,
	# so take the desktop version from desktop-releases.json and build the asset
	# URL from it. Snap is the fallback (official publisher, classic confinement).
	say "Installing Obsidian"
	OBSIDIAN_VERSION="$(curl -fsSL https://raw.githubusercontent.com/obsidianmd/obsidian-releases/master/desktop-releases.json |
		python3 -c 'import json,sys; print(json.load(sys.stdin)["latestVersion"])')"
	if [ "$(dpkg-query -W -f='${Version}' obsidian 2>/dev/null)" = "${OBSIDIAN_VERSION:-}" ]; then
		echo "already installed: obsidian $OBSIDIAN_VERSION"
	elif [ -n "${OBSIDIAN_VERSION:-}" ] &&
		curl -fL "https://github.com/obsidianmd/obsidian-releases/releases/download/v${OBSIDIAN_VERSION}/obsidian_${OBSIDIAN_VERSION}_amd64.deb" \
			-o /tmp/obsidian.deb; then
		sudo apt install -y /tmp/obsidian.deb
		rm -f /tmp/obsidian.deb
	else
		echo "deb unavailable, falling back to snap"
		sudo snap install obsidian --classic
	fi

	say "Installing ddcutil (external monitor brightness)"
	sudo apt install -y ddcutil i2c-tools
	sudo usermod -aG i2c "$USER"
	ddcutil detect

	say "Installing xscreensaver"
	sudo apt install -y xscreensaver xscreensaver-gl-extra xscreensaver-data-extra

	# Windows-style screen snip: region select, copied to the clipboard and saved
	# to ~/Pictures/Screenshots. Uses GNOME's own screenshot UI rather than
	# flameshot/gnome-screenshot, so it also works under Wayland.
	say "Binding Super+Shift+S to the screenshot UI"
	if [ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ] && command -v gsettings >/dev/null; then
		gsettings set org.gnome.shell.keybindings show-screenshot-ui "['Print', '<Shift><Super>s']"
		gsettings get org.gnome.shell.keybindings show-screenshot-ui
	else
		echo "no session bus (ssh/tty?), skipping; run it later from a desktop session:"
		echo "  gsettings set org.gnome.shell.keybindings show-screenshot-ui \"['Print', '<Shift><Super>s']\""
	fi

	say "Installing flatpak + flathub"
	sudo apt install -y flatpak
	sudo apt install -y gnome-software-plugin-flatpak
	flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo

	say "Installing qBittorrent"
	sudo add-apt-repository -y ppa:qbittorrent-team/qbittorrent-stable
	sudo apt-get update && sudo apt-get install -y qbittorrent

	# Install OpenLogi (Logitech Options+ alternative)
	say "Installing OpenLogi"
	OPENLOGI_ARCH="$(dpkg --print-architecture)"
	OPENLOGI_DEB_URL="$(curl -fsSL https://api.github.com/repos/AprilNEA/OpenLogi/releases/latest |
		python3 -c "import json,sys; arch=sys.argv[1]; assets=json.load(sys.stdin)['assets']; print(next(a['browser_download_url'] for a in assets if a['name'].endswith(f'-linux-{arch}.deb')))" "$OPENLOGI_ARCH")"
	OPENLOGI_DEB="/tmp/$(basename "$OPENLOGI_DEB_URL")"
	curl -fL "$OPENLOGI_DEB_URL" -o "$OPENLOGI_DEB"
	sudo apt install -y "$OPENLOGI_DEB"
	rm -f "$OPENLOGI_DEB"
	systemctl --user enable --now openlogi-agent.service

	# keyd, for capslock -> enter
	say "Installing keyd"
	if [ ! -d "$HOME/keyd/.git" ]; then
		git clone https://github.com/rvaiya/keyd "$HOME/keyd"
	fi
	(cd "$HOME/keyd" && make && sudo make install)
	sudo systemctl enable --now keyd

	sudo mkdir -p /etc/keyd
	sudo tee /etc/keyd/default.conf >/dev/null <<'EOF'
[ids]

*

[main]

capslock = enter

EOF

	sudo keyd reload

	say "Installing Docker"
	sudo apt remove -y $(dpkg --get-selections docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc | cut -f1) || true

	sudo apt update
	sudo apt install -y ca-certificates curl
	sudo install -m 0755 -d /etc/apt/keyrings
	sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
	sudo chmod a+r /etc/apt/keyrings/docker.asc

	sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

	sudo apt update
	sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

	# Low priority
	say "Installing shfmt and blender"
	sudo snap install shfmt
	sudo snap install blender --classic

fi

######################################################################## scroll
# Map mouse thumb buttons 8/9 to continuous scroll up/down.
#
#   button 8 (BTN_SIDE / "back")     -> hold to scroll UP
#   button 9 (BTN_EXTRA / "forward") -> hold to scroll DOWN
#
# Uses input-remapper, which rewrites events at the evdev layer. That means it
# works on both X11 and Wayland, unlike `xinput set-button-map` (X11 only, and
# one notch per click with no hold-to-repeat).
#
# The wheel() macro loops while the button is held and emits both REL_WHEEL and
# REL_WHEEL_HI_RES, so smooth-scrolling apps (GTK, Firefox, Chrome) behave.
if run_section scroll; then

	DEVICE="${DEVICE:-Logitech MX Master 3S}"
	PRESET="${PRESET:-thumb-scroll}"
	SPEED="${SPEED:-120}" # notches/sec ~= SPEED/2 (rel_rate is 60 Hz)

	# Which evdev codes to map. 275/276 is what libinput reports as X11 buttons 8/9.
	UP_CODE="${UP_CODE:-275}"     # BTN_SIDE
	DOWN_CODE="${DOWN_CODE:-276}" # BTN_EXTRA

	# ------------------------------------------------------------- 1. install
	say "Installing input-remapper"
	if ! command -v input-remapper-control >/dev/null; then
		sudo apt-get update
		sudo apt-get install -y input-remapper
	else
		echo "already installed: $(dpkg-query -W -f'${Version}' input-remapper 2>/dev/null || echo present)"
	fi

	# The daemon does the injecting and must be up at boot. The package also ships
	# /etc/xdg/autostart/input-remapper-autoload.desktop, which runs
	# `input-remapper-control --command autoload` at login and applies the preset.
	# Only escalate if something actually needs changing, so reruns need no sudo.
	say "Enabling the daemon"
	if [ "$(systemctl is-enabled input-remapper-daemon.service 2>/dev/null)" = enabled ] &&
		systemctl is-active --quiet input-remapper-daemon.service; then
		echo "already enabled and running"
	else
		sudo systemctl enable --now input-remapper-daemon.service
		systemctl is-active input-remapper-daemon.service
	fi

	# ---------------------------------------------------- 2. write the preset
	# input-remapper keys a preset to a device by an md5 of its capabilities+name,
	# so compute it from the live device rather than hardcoding it.
	say "Writing preset '$PRESET' for '$DEVICE'"
	DEVICE="$DEVICE" PRESET="$PRESET" SPEED="$SPEED" \
		UP_CODE="$UP_CODE" DOWN_CODE="$DOWN_CODE" python3 - <<'PY'
import os, sys, evdev
from inputremapper.utils import get_device_hash
from inputremapper.configs.preset import Preset
from inputremapper.configs.mapping import Mapping
from inputremapper.configs.input_config import InputCombination, InputConfig
from inputremapper.configs.paths import get_preset_path
from inputremapper.configs.global_config import GlobalConfig

name  = os.environ["DEVICE"]
preset_name = os.environ["PRESET"]
speed = int(os.environ["SPEED"])

dev = next((d for d in map(evdev.InputDevice, evdev.list_devices())
            if d.name == name and evdev.ecodes.EV_REL in d.capabilities()), None)
if dev is None:
    sys.exit(f"Device {name!r} not found. Plug it in, or list names with:\n"
             f"  python3 -c \"import evdev;[print(evdev.InputDevice(p).name) "
             f"for p in evdev.list_devices()]\"")

h = get_device_hash(dev)
print(f"{dev.path}  hash={h}")

preset = Preset(get_preset_path(name, preset_name))
for code, direction in ((int(os.environ["UP_CODE"]), "up"),
                        (int(os.environ["DOWN_CODE"]), "down")):
    preset.add(Mapping(
        input_combination=InputCombination(
            [InputConfig(type=evdev.ecodes.EV_KEY, code=code, origin_hash=h)]
        ),
        target_uinput="mouse",
        output_symbol=f"wheel({direction}, {speed})",
        mapping_type="key_macro",
        name=f"{evdev.ecodes.BTN[code]} -> scroll {direction}",
    ))
preset.save()

# autoload = re-apply this preset at every login
cfg = GlobalConfig()
cfg.load_config()
cfg.set_autoload_preset(name, preset_name)   # persists on its own
PY

	# ------------------------------------------------------------ 3. apply now
	say "Applying"
	input-remapper-control --command stop --device "$DEVICE" >/dev/null 2>&1 || true
	input-remapper-control --command start --device "$DEVICE" --preset "$PRESET"

	sleep 2
	if grep -q "input-remapper $DEVICE forwarded" /proc/bus/input/devices; then
		say "Active — hold button 8 to scroll up, button 9 to scroll down."
	else
		# Not fatal here: the mouse may simply not be plugged into this machine.
		echo "WARNING: injection did not come up. Check: journalctl -u input-remapper-daemon -n 40" >&2
	fi

	cat <<EOF

Speed        : $SPEED  (~$((SPEED / 2)) notches/sec)
Preset file  : ~/.config/input-remapper-2/presets/$DEVICE/$PRESET.json
Autoload     : ~/.config/input-remapper-2/config.json

Retune       : SPEED=30 ./setup.sh scroll
Disable      : input-remapper-control --command stop-all
Re-enable    : input-remapper-control --command autoload
GUI          : input-remapper-gtk

If the wrong buttons respond, find your real codes with
  sudo evtest        # pick the mouse, press the thumb buttons
and rerun with e.g.  UP_CODE=278 DOWN_CODE=277 ./setup.sh scroll
EOF

fi
