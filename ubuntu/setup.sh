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


git config --global user.email "mn297@users.noreply.github.com"
git config --global user.name "mn297"

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

# nvidia container toolkit
sudo apt-get update && sudo apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  gnupg2

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update

export NVIDIA_CONTAINER_TOOLKIT_VERSION=1.19.0-1
sudo apt-get install -y \
  nvidia-container-toolkit=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
  nvidia-container-toolkit-base=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
  libnvidia-container-tools=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
  libnvidia-container1=${NVIDIA_CONTAINER_TOOLKIT_VERSION}

sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker


# isaac ros
mkdir -p ~/workspaces/isaac_ros-dev/src
echo 'export ISAAC_ROS_WS="${ISAAC_ROS_WS:-${HOME}/workspaces/isaac_ros-dev/}"' >> ~/.bashrc
source ~/.bashrc

sudo apt update && sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

sudo apt update && sudo apt install -y curl gnupg software-properties-common
sudo add-apt-repository universe

k="/usr/share/keyrings/nvidia-isaac-ros.gpg"
curl -fsSL https://isaac.download.nvidia.com/isaac-ros/repos.key | sudo gpg --dearmor | sudo tee -a $k > /dev/null
f="/etc/apt/sources.list.d/nvidia-isaac-ros.list"
sudo touch $f
s="deb [signed-by=$k] https://isaac.download.nvidia.com/isaac-ros/release-4.3 noble main"
grep -qxF "$s" $f || echo "$s" | sudo tee -a $f
sudo apt-get update

sudo apt-get install -y isaac-ros-cli



# Install CUDA
# wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
# sudo dpkg -i cuda-keyring_1.1-1_all.deb
# sudo apt-get update
# sudo apt-get -y install cuda-toolkit-13-1
# sudo apt install -y nvidia-cuda-toolkit

# Download Isaac Sim
# check if $HOME/isaacsim exists
# if [ ! -d "$HOME/isaacsim" ]; then
# 	echo "Isaac Sim not found, downloading..."
# 	ISAACSIM_URL="https://download.isaacsim.omniverse.nvidia.com/isaac-sim-standalone-5.1.0-linux-x86_64.zip"
# 	ISAACSIM_ZIP="$HOME/isaacsim.zip"
# 	ISAACSIM_DIR="$HOME/isaacsim"
# 	wget -O "$ISAACSIM_ZIP" "$ISAACSIM_URL"
# 	mkdir -p "$ISAACSIM_DIR"
# 	unzip -o "$ISAACSIM_ZIP" -d "$ISAACSIM_DIR"
# 	echo "Isaac Sim downloaded and extracted to $ISAACSIM_DIR"
# else
# 	echo "Isaac Sim already exists, skipping download..."
# fi
