#!/usr/bin/env bash
# Upgrade NVIDIA 535.288.01 -> 580.173.02 for Isaac Sim 6.0.1 RTX support.
#
# Why: omni.rtx enforces driver >= 550.90.07 on Linux and rejects 535.288.01
# ("R550 Omniverse RTX driver requirement"). Without this, HydraEngine rtx
# fails to create a scene renderer: no viewport, cameras, RTX sensors or SDG.
#
# NOTE: Isaac Sim's own compatibility_check reports 535 as "supported" against a
# stale 535.161 threshold. The renderer disagrees. Trust the renderer.
set -euo pipefail

KERNEL="$(uname -r)"
MODPKG="linux-modules-nvidia-580-${KERNEL}"

echo "==> Running kernel: ${KERNEL}"
echo "==> Matching module package: ${MODPKG}"

# This system uses PRECOMPILED SIGNED modules, not DKMS. The generic HWE
# metapackage (linux-modules-nvidia-580-generic-hwe-24.04) currently targets
# kernel 7.0.0-30-generic and would NOT provide a module for the running
# kernel. Pin to the running kernel explicitly.
if ! apt-cache show "${MODPKG}" >/dev/null 2>&1; then
    echo "ERROR: ${MODPKG} not available. Aborting rather than risk a" >&2
    echo "       reboot with no NVIDIA kernel module." >&2
    exit 1
fi

sudo apt-get update
sudo apt-get install -y nvidia-driver-580 "${MODPKG}"

echo
echo "==> Verification (must show 580 for BOTH before rebooting)"
dpkg -l | awk '/^ii/ && /nvidia-driver-580|linux-modules-nvidia-580/ {print "   ", $2, $3}'

echo
echo "==> Confirming a module exists for the running kernel:"
if find "/lib/modules/${KERNEL}" -name 'nvidia.ko*' 2>/dev/null | grep -q .; then
    find "/lib/modules/${KERNEL}" -name 'nvidia.ko*' | sed 's/^/    /'
else
    echo "    WARNING: no nvidia.ko found for ${KERNEL}. Do NOT reboot yet."
fi

cat <<'MSG'

=========================================================
REBOOT REQUIRED:   sudo reboot
After reboot:      nvidia-smi        # expect 580.173.02

If the desktop fails to come back:
  - At GRUB, pick a previous kernel, or add `nomodeset` to the kernel line.
  - Then roll back:  sudo apt-get install -y nvidia-driver-535
=========================================================
MSG
