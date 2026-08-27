#!/bin/bash
# Best-effort setup: no `set -e`, so one broken install does not abort the rest.
set -uo pipefail

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
	exec bash "$REPO_DIR/ubuntu/setup.sh" </dev/null
fi
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Update package lists
echo "Updating package lists..."
sudo apt update

# Install essential build tools and utilities
echo "Installing essential build tools..."
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

# Install Claude Code
echo "Installing Claude Code..."
curl -fsSL https://claude.ai/install.sh | bash

# Install Cursor. The apt repo returns 403/GPG mismatches, so resolve the latest
# deb from the download API instead. Use cursor.com, not www (www 308-redirects).
echo "Installing Cursor..."
CURSOR_DEB_URL="$(curl -fsSL "https://cursor.com/api/download?platform=linux-x64&releaseTrack=stable" \
	| python3 -c 'import json,sys; print(json.load(sys.stdin)["debUrl"])')"
CURSOR_DEB="/tmp/cursor.deb"
curl -fL "$CURSOR_DEB_URL" -o "$CURSOR_DEB"
sudo apt install -y "$CURSOR_DEB"
rm -f "$CURSOR_DEB"
curl https://cursor.com/install -fsS | bash # cursor-agent CLI
mkdir -p "$HOME/.config/Cursor/User"
cp "$HERE/cursor/keybindings.json" "$HOME/.config/Cursor/User/keybindings.json"

# Install uv (Python package manager)
echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install pixi
echo "Installing pixi..."
curl -fsSL https://pixi.sh/install.sh | bash

# Install browsers via snap
echo "Installing browsers via snap..."
sudo snap install chromium opera brave

# Install Spotify via snap
echo "Installing Spotify via snap..."
sudo snap install spotify





sudo apt install -y ddcutil i2c-tools
sudo usermod -aG i2c $USER
ddcutil detect

sudo apt install -y xscreensaver xscreensaver-gl-extra xscreensaver-data-extra



sudo apt install -y flatpak
sudo apt install -y gnome-software-plugin-flatpak
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo

# Torrent client
sudo add-apt-repository -y ppa:qbittorrent-team/qbittorrent-stable
sudo apt-get update && sudo apt-get install -y qbittorrent



# Install input-remapper
# cd ~/Downloads
# wget https://github.com/sezanzeb/input-remapper/releases/download/2.2.0/input-remapper-2.2.0.deb
# sudo apt install -f ./input-remapper-2.2.0.deb
sudo apt install -y input-remapper

# Install OpenLogi (Logitech Options+ alternative)
echo "Installing OpenLogi..."
OPENLOGI_ARCH="$(dpkg --print-architecture)"
OPENLOGI_DEB_URL="$(curl -fsSL https://api.github.com/repos/AprilNEA/OpenLogi/releases/latest \
	| python3 -c "import json,sys; arch=sys.argv[1]; assets=json.load(sys.stdin)['assets']; print(next(a['browser_download_url'] for a in assets if a['name'].endswith(f'-linux-{arch}.deb')))" "$OPENLOGI_ARCH")"
OPENLOGI_DEB="/tmp/$(basename "$OPENLOGI_DEB_URL")"
curl -fL "$OPENLOGI_DEB_URL" -o "$OPENLOGI_DEB"
sudo apt install -y "$OPENLOGI_DEB"
rm -f "$OPENLOGI_DEB"
systemctl --user enable --now openlogi-agent.service

# Install keyd for capslock to enter
if [ ! -d "$HOME/keyd/.git" ]; then
	git clone https://github.com/rvaiya/keyd "$HOME/keyd"
fi
cd "$HOME/keyd"
make && sudo make install
sudo systemctl enable --now keyd

# Create keyd config directory if it doesn't exist
sudo mkdir -p /etc/keyd

# Write keyd configuration
sudo tee /etc/keyd/default.conf >/dev/null <<'EOF'
[ids]

*

[main]

capslock = enter

EOF

sudo keyd reload


# docker
sudo apt remove $(dpkg --get-selections docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc | cut -f1) || true

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
sudo snap install shfmt
sudo snap install blender --classic
