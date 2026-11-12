#!/bin/bash
# Install guards so that a wedged USB device cannot leave the laptop without a keyboard.
#
# On 2026-10-23 a RealSense D455 stopped answering at driver start. A minute
# later the xHCI controller died ("HC died; cleaning up") and every USB device
# went with it, the keyboard included. Only a hard reboot recovered.
# See ubuntu/usb-guard.md. This installs, as root:
#
#   1. xhci-watchdog.service: follows the kernel log and resets a controller
#      that died, so the keyboard comes back with no input.
#   2. /usr/local/sbin/xhci-reset: rebinds the xHCI controllers. The user who
#      ran this script may run it without a password:
#      sudo -n /usr/local/sbin/xhci-reset
#   3. A udev rule that keeps the devices in QUIRKS out of USB autosuspend.
#   4. The usbcore quirk "k" (no USB3 link power management, U1/U2) for the
#      devices in QUIRKS: now, and on every boot through the kernel command
#      line. usbcore is built into the Ubuntu kernel, so modprobe.d cannot set it.
#
# Usage:
#   ./ubuntu/setup_usb_guard.sh            install (safe to run again)
#   ./ubuntu/setup_usb_guard.sh --remove   remove 1-3; prints how to undo 4
#
# After the install, unplug and replug the devices so the quirk applies.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
	exec sudo "$0" "$@"
fi

SRC="$(cd "$(dirname "$0")" && pwd)/usb-guard"
QUIRKS="8086:0b5c:k" # RealSense D455; add more as vid:pid:k, comma-separated
RESET=/usr/local/sbin/xhci-reset
WATCHDOG=/usr/local/sbin/xhci-watchdog
UNIT=/etc/systemd/system/xhci-watchdog.service
RULE=/etc/udev/rules.d/99-usb-guard-power.rules
SUDOERS=/etc/sudoers.d/xhci-reset
GRUB=/etc/default/grub
QPARAM=/sys/module/usbcore/parameters/quirks

if [ "${1:-}" = "--remove" ]; then
	systemctl disable --now xhci-watchdog.service 2>/dev/null || true
	rm -f "$UNIT" "$WATCHDOG" "$RESET" "$SUDOERS" "$RULE"
	systemctl daemon-reload
	udevadm control --reload
	echo "Removed. To drop the boot quirk, delete 'usbcore.quirks=$QUIRKS' from"
	echo "GRUB_CMDLINE_LINUX_DEFAULT in $GRUB, then run: sudo update-grub"
	exit 0
fi

# 1 and 2. The reset script and the watchdog.
install -m 755 -o root -g root "$SRC/xhci-reset.sh" "$RESET"
install -m 755 -o root -g root "$SRC/xhci-watchdog.sh" "$WATCHDOG"
install -m 644 "$SRC/xhci-watchdog.service" "$UNIT"
systemctl daemon-reload
systemctl enable --now xhci-watchdog.service

if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != root ]; then
	tmp=$(mktemp)
	echo "$SUDO_USER ALL=(root) NOPASSWD: $RESET, $RESET *" >"$tmp"
	if visudo -cf "$tmp" >/dev/null; then
		install -m 440 -o root -g root "$tmp" "$SUDOERS"
	else
		echo "The sudoers entry failed visudo, so it was skipped." >&2
	fi
	rm -f "$tmp"
fi

# 3. No autosuspend: the rule for the next plug-in, and the devices plugged in now.
install -m 644 "$SRC/99-usb-guard-power.rules" "$RULE"
rm -f /etc/udev/rules.d/99-d455-power.rules # the first version's name for the same rule
udevadm control --reload
IFS=, read -ra qs <<<"$QUIRKS"
for q in "${qs[@]}"; do
	vid=${q%%:*} rest=${q#*:} pid=${rest%%:*}
	for d in /sys/bus/usb/devices/*; do
		if [ -f "$d/idVendor" ] && [ "$(cat "$d/idVendor")" = "$vid" ] && [ "$(cat "$d/idProduct")" = "$pid" ]; then
			echo on >"$d/power/control"
		fi
	done
done

# 4. No USB3 link power management: now (from the next plug-in) and on every boot.
cur=$(cat "$QPARAM")
for q in "${qs[@]}"; do
	case ",$cur," in *",$q,"*) ;; *) cur="${cur:+$cur,}$q" ;; esac
done
echo "$cur" >"$QPARAM"
if ! grep -q "usbcore.quirks=$QUIRKS" "$GRUB"; then
	cp "$GRUB" "$GRUB.bak.usb-guard"
	if grep -q "^GRUB_CMDLINE_LINUX_DEFAULT=.*usbcore\.quirks=" "$GRUB"; then
		sed -i "/^GRUB_CMDLINE_LINUX_DEFAULT=/s/usbcore\.quirks=[^ \"]*/usbcore.quirks=$QUIRKS/" "$GRUB"
	else
		sed -i "s/^GRUB_CMDLINE_LINUX_DEFAULT=\"\(.*\)\"/GRUB_CMDLINE_LINUX_DEFAULT=\"\1 usbcore.quirks=$QUIRKS\"/" "$GRUB"
	fi
	if ! grep -q "usbcore.quirks=$QUIRKS" "$GRUB"; then
		cp "$GRUB.bak.usb-guard" "$GRUB"
		echo "Could not edit $GRUB, so it was restored. Add usbcore.quirks=$QUIRKS by hand." >&2
		exit 1
	fi
	update-grub
fi

echo "USB guard installed. Check: systemctl status xhci-watchdog; cat $QPARAM"
echo "Unplug and replug the guarded devices so the quirk applies."
