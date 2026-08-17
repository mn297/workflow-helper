#!/bin/sh
# Unbind MediaTek mt7925e (Wi-Fi 7, PCI 14c3:7925).
# Workaround for pci_pm_resume -110 (ETIMEDOUT) on S3.
# Does not touch mt7921e / MT7922 (14c3:0616).

UNBIND=/sys/bus/pci/drivers/mt7925e/unbind
[ -w "$UNBIND" ] || exit 0

for dev in /sys/bus/pci/devices/*; do
	[ -f "$dev/vendor" ] && [ -f "$dev/device" ] || continue
	vendor=$(cat "$dev/vendor" 2>/dev/null || true)
	device=$(cat "$dev/device" 2>/dev/null || true)
	[ "$vendor" = "0x14c3" ] && [ "$device" = "0x7925" ] || continue
	[ -e "$dev/driver" ] || continue
	echo "$(basename "$dev")" > "$UNBIND"
done
