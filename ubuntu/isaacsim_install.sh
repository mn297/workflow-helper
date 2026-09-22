#!/usr/bin/env bash
# Standalone Isaac Sim 6.1.0 into ~/isaacsim.
#
# This is the NVIDIA quick-install zip, not the GitHub source tree that
# isaacsim_toolchain.sh builds under ~/IsaacSim. Mixing the two in one
# directory leaves a half-source, half-binary tree that neither launch
# path can use.
#
#   ~/workflow-helper/ubuntu/isaacsim_install.sh
#   ~/workflow-helper/ubuntu/isaacsim_install.sh --replace
#   ~/workflow-helper/ubuntu/isaacsim_install.sh launch
#
# Docs: https://docs.isaacsim.omniverse.nvidia.com/latest/installation/quick-install.html
set -euo pipefail

VERSION="6.1.0"
ARCH="linux-x86_64"
ZIP_NAME="isaac-sim-standalone-${VERSION}-${ARCH}.zip"
ZIP_URL="https://downloads.isaacsim.nvidia.com/${ZIP_NAME}"
ZIP_MD5="b471383a51f259e0af22541f05c34b0e"

ISAACSIM_DIR="${ISAACSIM_DIR:-$HOME/isaacsim}"
DOWNLOADS_DIR="${DOWNLOADS_DIR:-$HOME/Downloads}"
ZIP_PATH="${DOWNLOADS_DIR}/${ZIP_NAME}"

REPLACE=0
LAUNCH=0
for arg in "$@"; do
	case "$arg" in
	--replace) REPLACE=1 ;;
	launch) LAUNCH=1 ;;
	-h | --help)
		echo "usage: $0 [--replace] [launch]"
		echo "  standalone Isaac Sim ${VERSION} -> ${ISAACSIM_DIR:-$HOME/isaacsim}"
		exit 0
		;;
	*)
		echo "usage: $0 [--replace] [launch]" >&2
		exit 1
		;;
	esac
done

need() { command -v "$1" >/dev/null || { echo "ERROR: missing $1" >&2; exit 1; }; }
need wget
need unzip
need md5sum

free_gb=$(df -BG --output=avail "$HOME" | tail -1 | tr -dc '0-9')
if [ "${free_gb:-0}" -lt 50 ]; then
	echo "ERROR: ${free_gb} GB free under $HOME; NVIDIA asks for 50 GB." >&2
	exit 1
fi

if [ -e "$ISAACSIM_DIR" ] && [ "$REPLACE" -ne 1 ]; then
	echo "ERROR: ${ISAACSIM_DIR} already exists. Pass --replace to wipe it." >&2
	exit 1
fi

mkdir -p "$DOWNLOADS_DIR"
if [ -f "$ZIP_PATH" ]; then
	got=$(md5sum "$ZIP_PATH" | awk '{print $1}')
	if [ "$got" != "$ZIP_MD5" ]; then
		echo "zip MD5 ${got} != ${ZIP_MD5}; re-downloading"
		rm -f "$ZIP_PATH"
	fi
fi
if [ ! -f "$ZIP_PATH" ]; then
	wget -c --progress=dot:giga -O "$ZIP_PATH" "$ZIP_URL"
fi
got=$(md5sum "$ZIP_PATH" | awk '{print $1}')
if [ "$got" != "$ZIP_MD5" ]; then
	echo "ERROR: downloaded zip MD5 ${got}, expected ${ZIP_MD5}" >&2
	exit 1
fi

if [ -e "$ISAACSIM_DIR" ]; then
	rm -rf "$ISAACSIM_DIR"
fi
mkdir -p "$ISAACSIM_DIR"
unzip -o "$ZIP_PATH" -d "$ISAACSIM_DIR"
( cd "$ISAACSIM_DIR" && ./post_install.sh )

echo
echo "Installed $(cat "$ISAACSIM_DIR/VERSION") at ${ISAACSIM_DIR}"
echo "Launch:  ${ISAACSIM_DIR}/isaac-sim.sh"

if [ "$LAUNCH" -eq 1 ]; then
	cd "$ISAACSIM_DIR"
	exec ./isaac-sim.sh
fi
