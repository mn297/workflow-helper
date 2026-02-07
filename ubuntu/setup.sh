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

sudo apt install ddcutil i2c-tools
sudo usermod -aG i2c $USER
ddcutil detect



git config --global user.email "mn297@users.noreply.github.com"
git config --global user.name "mn297"

# Install browsers via snap
echo "Installing browsers via snap..."
sudo snap install chromium opera brave spotify

# Install uv (Python package manager)
echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh



cd ~/Downloads
wget https://github.com/sezanzeb/input-remapper/releases/download/2.2.0/input-remapper-2.2.0.deb
sudo apt install -f ./input-remapper-2.2.0.deb


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

# Install CUDA
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda-toolkit-13-1
sudo apt install nvidia-cuda-toolkit

# Download Isaac Sim
# check if $HOME/isaacsim exists
if [ ! -d "$HOME/isaacsim" ]; then
	echo "Isaac Sim not found, downloading..."
	ISAACSIM_URL="https://download.isaacsim.omniverse.nvidia.com/isaac-sim-standalone-5.1.0-linux-x86_64.zip"
	ISAACSIM_ZIP="$HOME/isaacsim.zip"
	ISAACSIM_DIR="$HOME/isaacsim"
	wget -O "$ISAACSIM_ZIP" "$ISAACSIM_URL"
	mkdir -p "$ISAACSIM_DIR"
	unzip -o "$ISAACSIM_ZIP" -d "$ISAACSIM_DIR"
	echo "Isaac Sim downloaded and extracted to $ISAACSIM_DIR"
else
	echo "Isaac Sim already exists, skipping download..."
fi
