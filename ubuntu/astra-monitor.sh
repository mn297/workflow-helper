#!/bin/bash
#
# Install Astra Monitor and show RTX 5070 Ti memory in the GNOME top bar.
#
#   ./astra-monitor.sh
#   ./setup.sh astra
#
# Needs a graphical session (session bus). The extension reads nvidia-smi
# every 2 seconds. Hover the GPU indicator for used and total GB.
#
# GPU identity is this machine: 0000:01:00.0, vendor 10de, product 2c05.
set -euo pipefail

UUID="monitor@astraext.github.io"
SCHEMA="org.gnome.shell.extensions.astra-monitor"
EXT_DIR="${HOME}/.local/share/gnome-shell/extensions/${UUID}"
SCHEMA_DIR="${EXT_DIR}/schemas"
GPU='{"domain":"0000:01","bus":"00","slot":"0","vendorId":"10de","productId":"2c05"}'
DATA='[{"domain":"0000:01","bus":"00","slot":"0","vendorId":"10de","productId":"2c05","monitor":true}]'

if [ "$(id -u)" -eq 0 ]; then
	echo "Run as your normal user, not root." >&2
	exit 1
fi
if [ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
	echo "No session bus. Run this from a graphical login, not ssh." >&2
	exit 1
fi
if ! command -v busctl >/dev/null || ! command -v gsettings >/dev/null; then
	echo "busctl and gsettings are required." >&2
	exit 1
fi

if gnome-extensions info "$UUID" >/dev/null 2>&1; then
	echo "already installed: $UUID"
else
	result="$(busctl --user call org.gnome.Shell.Extensions /org/gnome/Shell/Extensions \
		org.gnome.Shell.Extensions InstallRemoteExtension s "$UUID")"
	echo "install: $result"
fi

enabled="$(busctl --user call org.gnome.Shell.Extensions /org/gnome/Shell/Extensions \
	org.gnome.Shell.Extensions EnableExtension s "$UUID")"
echo "enable: $enabled"

if [ ! -d "$SCHEMA_DIR" ]; then
	echo "Schema dir missing: $SCHEMA_DIR" >&2
	exit 1
fi

gsettings --schemadir "$SCHEMA_DIR" set "$SCHEMA" gpu-main "$GPU"
gsettings --schemadir "$SCHEMA_DIR" set "$SCHEMA" gpu-data "$DATA"
gsettings --schemadir "$SCHEMA_DIR" set "$SCHEMA" gpu-header-show true
gsettings --schemadir "$SCHEMA_DIR" set "$SCHEMA" gpu-header-memory-percentage true
gsettings --schemadir "$SCHEMA_DIR" set "$SCHEMA" gpu-header-memory-bar true

gnome-extensions info "$UUID"
echo "GPU header on. 5070 Ti memory is in the top bar."
