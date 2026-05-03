#!/bin/bash
set -euo pipefail

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
sudo snap install shfmt
snap install blender --classic


sudo apt install -y ddcutil i2c-tools
sudo usermod -aG i2c $USER
ddcutil detect

sudo apt install -y xscreensaver xscreensaver-gl-extra xscreensaver-data-extra


# Install browsers via snap
echo "Installing browsers via snap..."
sudo snap install chromium opera brave spotify

sudo apt install -y flatpak
sudo apt install -y gnome-software-plugin-flatpak
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo

# Torrent client
sudo add-apt-repository ppa:qbittorrent-team/qbittorrent-stable
sudo apt-get update && sudo apt-get install -y qbittorrent


# Install uv (Python package manager)
echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install pixi
echo "Installing pixi..."
curl -fsSL https://pixi.sh/install.sh | bash

# Install input-remapper
# cd ~/Downloads
# wget https://github.com/sezanzeb/input-remapper/releases/download/2.2.0/input-remapper-2.2.0.deb
# sudo apt install -f ./input-remapper-2.2.0.deb
sudo apt install -y input-remapper

# Install keyd for capslock to enter
cd ~
git clone https://github.com/rvaiya/keyd
cd keyd
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

