#!/bin/bash
# Rebind xHCI USB controllers: the given PCI addresses, or every xHCI controller.
#
#   xhci-reset [--rescan] [ADDR...]
#
# --rescan removes each controller from the PCI bus and rescans instead of rebinding.
# A failed bind falls back to the same remove and rescan. Exits 1 when a controller
# ends without the xhci_hcd driver bound.
# Accepts only PCI addresses of xHCI controllers, because sudoers lets the user
# pass it arguments without a password.
set -u
DRV=/sys/bus/pci/drivers/xhci_hcd

is_xhci() {
	[[ $1 =~ ^[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]$ ]] &&
		[ "$(cat "/sys/bus/pci/devices/$1/class" 2>/dev/null)" = "0x0c0330" ]
}

remove_rescan() {
	echo 1 >"/sys/bus/pci/devices/$1/remove"
	sleep 1
	echo 1 >/sys/bus/pci/rescan
	sleep 3
}

rescan=0
if [ "${1:-}" = --rescan ]; then
	rescan=1
	shift
fi
addrs=("$@")
if [ ${#addrs[@]} -eq 0 ]; then
	for d in /sys/bus/pci/devices/*; do
		is_xhci "$(basename "$d")" && addrs+=("$(basename "$d")")
	done
fi

rc=0
for a in "${addrs[@]}"; do
	is_xhci "$a" || {
		echo "not an xHCI controller: $a" >&2
		rc=1
		continue
	}
	if ((rescan)); then
		remove_rescan "$a"
	else
		[ -e "$DRV/$a" ] && echo -n "$a" >"$DRV/unbind"
		sleep 1
		echo -n "$a" >"$DRV/bind" 2>/dev/null
		sleep 3
		[ -e "$DRV/$a" ] || remove_rescan "$a"
	fi
	how=rebind
	((rescan)) && how=rescan
	if [ -e "$DRV/$a" ]; then
		logger -t xhci-reset "reset $a ($how)"
		echo "reset $a ($how)"
	else
		logger -t xhci-reset "reset $a ($how) failed: xhci_hcd not bound"
		echo "reset $a ($how) failed: xhci_hcd not bound" >&2
		rc=1
	fi
done
exit $rc
