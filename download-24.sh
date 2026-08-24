#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Ubuntu 24.04 LTS recovery USB creator
# WARNING: TARGET IS COMPLETELY ERASED
# ============================================================

TARGET="/dev/sda"

VERSION="24.04.4"
ISO="ubuntu-${VERSION}-desktop-amd64.iso"
BASE_URL="https://releases.ubuntu.com/24.04"

# Store ISO on internal disk so download can be reused/resumed.
WORKDIR="/var/cache/ubuntu-recovery"
ISO_PATH="${WORKDIR}/${ISO}"

echo
echo "============================================"
echo " Ubuntu Recovery USB Creator"
echo "============================================"
echo "TARGET: $TARGET"
echo "ISO:    $ISO"
echo

# Must be root.
if [[ "$EUID" -ne 0 ]]; then
    echo "Re-running as root..."
    exec sudo "$0" "$@"
fi

# Recovery mode often mounts / read-only.
echo "[1/8] Making root filesystem writable if necessary..."
mount -o remount,rw / 2>/dev/null || true

# Make sure target exists.
if [[ ! -b "$TARGET" ]]; then
    echo "ERROR: $TARGET does not exist."
    echo
    lsblk -o NAME,SIZE,TYPE,MODEL,TRAN,MOUNTPOINTS
    exit 1
fi

# Must be a whole disk, not a partition.
TYPE="$(lsblk -ndo TYPE "$TARGET")"

if [[ "$TYPE" != "disk" ]]; then
    echo "ERROR: $TARGET is not a whole disk."
    exit 1
fi

echo
echo "[2/8] Disk information:"
lsblk -o NAME,SIZE,TYPE,MODEL,SERIAL,TRAN,MOUNTPOINTS "$TARGET"
echo

# ------------------------------------------------------------
# CRITICAL SAFETY CHECK
# Refuse if /dev/sda is an ancestor of the root filesystem.
# ------------------------------------------------------------

ROOT_SOURCE="$(findmnt -n -o SOURCE / 2>/dev/null || true)"

if [[ -n "$ROOT_SOURCE" ]]; then
    if lsblk -sno NAME "$ROOT_SOURCE" 2>/dev/null |
       grep -Fxq "$(basename "$TARGET")"; then

        echo
        echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        echo "REFUSING TO CONTINUE"
        echo "$TARGET appears to contain the running Ubuntu system."
        echo "Writing to it would destroy your installation."
        echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        exit 1
    fi
fi

# Require USB to be big enough.
SIZE_BYTES="$(blockdev --getsize64 "$TARGET")"
MIN_BYTES=$((7 * 1024 * 1024 * 1024))

if (( SIZE_BYTES < MIN_BYTES )); then
    echo "ERROR: USB is too small."
    echo "Use an 8 GB or larger USB stick."
    exit 1
fi

echo
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
echo "EVERYTHING ON $TARGET WILL BE DESTROYED."
echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
echo
read -r -p "Type exactly ERASE-SDA to continue: " CONFIRM

if [[ "$CONFIRM" != "ERASE-SDA" ]]; then
    echo "Cancelled."
    exit 1
fi

# Recovery mode may not have networking started.
echo
echo "[3/8] Starting networking if available..."

systemctl start NetworkManager 2>/dev/null || true
systemctl start systemd-resolved 2>/dev/null || true

mkdir -p "$WORKDIR"
cd "$WORKDIR"

# ------------------------------------------------------------
# Download helper
# ------------------------------------------------------------

download_iso()
{
    if command -v wget >/dev/null 2>&1; then
        wget -c \
            "${BASE_URL}/${ISO}" \
            -O "$ISO_PATH"

    elif command -v curl >/dev/null 2>&1; then
        curl -fL \
            --retry 3 \
            -C - \
            -o "$ISO_PATH" \
            "${BASE_URL}/${ISO}"

    else
        echo "ERROR: neither wget nor curl is installed."
        echo "Install one with:"
        echo "    apt update"
        echo "    apt install wget"
        exit 1
    fi
}

download_checksums()
{
    if command -v wget >/dev/null 2>&1; then
        wget -O SHA256SUMS \
            "${BASE_URL}/SHA256SUMS"
    else
        curl -fL \
            -o SHA256SUMS \
            "${BASE_URL}/SHA256SUMS"
    fi
}

echo
echo "[4/8] Downloading Ubuntu ${VERSION}..."

download_iso

echo
echo "[5/8] Downloading checksum..."

download_checksums

echo
echo "[6/8] Verifying ISO..."

grep -E \
    "^[0-9a-fA-F]{64} [ *]${ISO}$" \
    SHA256SUMS \
    > SHA256SUMS.one

if [[ ! -s SHA256SUMS.one ]]; then
    echo "ERROR: Could not find $ISO in SHA256SUMS."
    exit 1
fi

sha256sum -c SHA256SUMS.one

echo
echo "ISO checksum GOOD."
echo

# ------------------------------------------------------------
# Unmount every partition belonging to USB.
# Do NOT mount it before dd.
# ------------------------------------------------------------

echo "[7/8] Unmounting USB partitions..."

while read -r PART; do
    [[ -n "$PART" ]] || continue

    echo "Unmounting $PART ..."
    umount "$PART" 2>/dev/null || true

done < <(
    lsblk -lnpo NAME,TYPE "$TARGET" |
    awk '$2 == "part" {print $1}'
)

sync

echo
echo "============================================"
echo "WRITING UBUNTU TO $TARGET"
echo "DO NOT REMOVE THE USB."
echo "============================================"
echo

dd \
    if="$ISO_PATH" \
    of="$TARGET" \
    bs=4M \
    status=progress \
    conv=fsync

sync

echo
echo "[8/8] Finished."
echo

# Ask kernel to re-read partition table.
partprobe "$TARGET" 2>/dev/null || true

echo "Result:"
lsblk -f "$TARGET"

echo
echo "============================================"
echo " Ubuntu recovery USB successfully created."
echo "============================================"
echo
echo "You can now reboot and boot from $TARGET."
echo "Choose:"
echo "    Try or Install Ubuntu"
echo
echo "For file recovery, choose TRY UBUNTU first."
echo

eject "$TARGET" 2>/dev/null || true