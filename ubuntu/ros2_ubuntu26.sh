#!/usr/bin/env bash
set -euo pipefail

# ROS 2 Lyrical on Ubuntu 26.04 / Resolute
# Date note: as of early May 2026, Lyrical is still beta.
# The beta packages are in ros2-testing, not the normal ros2 repo.

ROS_DISTRO_NAME="lyrical"
ROS_DESKTOP_PKG="ros-${ROS_DISTRO_NAME}-desktop"
ROS_BASE_PKG="ros-${ROS_DISTRO_NAME}-ros-base"

echo "=== Checking Ubuntu version ==="
. /etc/os-release

if [ "${VERSION_CODENAME:-}" != "resolute" ]; then
  echo "ERROR: This script is for Ubuntu 26.04, codename resolute."
  echo "Detected: ${PRETTY_NAME:-unknown}, codename=${VERSION_CODENAME:-unknown}"
  exit 1
fi

echo "Detected Ubuntu codename: ${VERSION_CODENAME}"

echo "=== Setting locale ==="
sudo apt update
sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

echo "=== Installing basic tools and enabling universe ==="
sudo apt install -y software-properties-common curl ca-certificates gnupg lsb-release
sudo add-apt-repository -y universe
sudo apt update

echo "=== Installing ROS 2 normal apt source first ==="
DEB_CODENAME="$(
  . /etc/os-release
  echo "${UBUNTU_CODENAME:-${VERSION_CODENAME}}"
)"

ROS_API_TMP="$(mktemp /tmp/ros-apt-release.XXXXXX.json)"
trap 'rm -f "$ROS_API_TMP"' EXIT

curl -sSf -o "$ROS_API_TMP" \
  "https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest"

ROS_APT_SOURCE_VERSION="$(
  grep -Fm1 '"tag_name"' "$ROS_API_TMP" | awk -F'"' '{print $4}'
)"

if [ -z "$ROS_APT_SOURCE_VERSION" ]; then
  echo "ERROR: Could not read ros-apt-source release tag from GitHub API."
  exit 1
fi

echo "Latest ros-apt-source version: ${ROS_APT_SOURCE_VERSION}"

ROS2_APT_DEB_URL="https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.${DEB_CODENAME}_all.deb"

curl -fSL -o /tmp/ros2-apt-source.deb "$ROS2_APT_DEB_URL"
sudo apt install -y /tmp/ros2-apt-source.deb
sudo apt update

echo "=== Switching to ROS 2 testing apt source ==="
# The testing source package conflicts with ros2-apt-source and replaces it.
# Try apt first; if unavailable, download the .deb directly from the same release.
if ! sudo apt install -y ros2-testing-apt-source; then
  echo "apt could not install ros2-testing-apt-source directly; downloading .deb..."

  ROS2_TESTING_APT_DEB_URL="https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-testing-apt-source_${ROS_APT_SOURCE_VERSION}.${DEB_CODENAME}_all.deb"

  curl -fSL -o /tmp/ros2-testing-apt-source.deb "$ROS2_TESTING_APT_DEB_URL"
  sudo apt install -y /tmp/ros2-testing-apt-source.deb
fi

sudo apt update

echo "=== Confirming ROS testing repo is enabled ==="
grep -R "packages.ros.org/ros2-testing" /etc/apt/sources.list.d /etc/apt/sources.list || true

echo "=== Checking available Lyrical packages ==="
apt-cache policy "$ROS_DESKTOP_PKG" "$ROS_BASE_PKG" || true

echo "=== Upgrading system packages ==="
sudo apt upgrade -y

echo "=== Installing ROS 2 Lyrical ==="
if apt-cache show "$ROS_DESKTOP_PKG" >/dev/null 2>&1; then
  echo "Installing full desktop package: ${ROS_DESKTOP_PKG}"
  sudo apt install -y "$ROS_DESKTOP_PKG"
elif apt-cache show "$ROS_BASE_PKG" >/dev/null 2>&1; then
  echo "Desktop package not available yet."
  echo "Installing base package instead: ${ROS_BASE_PKG}"
  sudo apt install -y "$ROS_BASE_PKG"
else
  echo "ERROR: No ros-lyrical packages found."
  echo "Try:"
  echo "  sudo apt update"
  echo "  apt-cache search '^ros-lyrical-' | head -100"
  exit 1
fi

echo "=== Installing ROS development tools ==="
sudo apt install -y ros-dev-tools

echo "=== Optional useful ROS packages for Isaac Sim / robotics examples ==="
sudo apt install -y \
  ros-${ROS_DISTRO_NAME}-vision-msgs \
  ros-${ROS_DISTRO_NAME}-ackermann-msgs \
  ros-${ROS_DISTRO_NAME}-control-msgs \
  ros-${ROS_DISTRO_NAME}-xacro \
  ros-${ROS_DISTRO_NAME}-joint-state-publisher \
  ros-${ROS_DISTRO_NAME}-robot-state-publisher || true

echo "=== Adding ROS source line to ~/.bashrc ==="
SOURCE_LINE="source /opt/ros/${ROS_DISTRO_NAME}/setup.bash"

if [ ! -f "$HOME/.bashrc" ] || ! grep -qFx "$SOURCE_LINE" "$HOME/.bashrc"; then
  echo "$SOURCE_LINE" >> "$HOME/.bashrc"
fi

echo "=== Sourcing ROS for this shell ==="
# shellcheck source=/dev/null
source "/opt/ros/${ROS_DISTRO_NAME}/setup.bash"

echo "=== Verifying ROS 2 ==="
which ros2
ros2 --version || true
ros2 doctor || true

echo ""
echo "DONE."
echo "Open a new terminal, or run:"
echo "  source /opt/ros/${ROS_DISTRO_NAME}/setup.bash"
echo ""
echo "Test with:"
echo "  ros2 run demo_nodes_cpp talker"
echo "and in another terminal:"
echo "  ros2 run demo_nodes_py listener"