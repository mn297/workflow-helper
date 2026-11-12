#!/bin/bash
# Reset an xHCI controller each time the kernel logs that it died, escalating when a reset does not hold.
#
# The first death gets a rebind. A death within RETRY_S of the last reset gets a PCI remove
# and rescan. After MAX_TRIES resets in a row that did not hold, it logs and waits; a death
# more than RETRY_S after the last reset starts the count again.
RETRY_S=60 # s; a rebound controller has died again 12 s after its reset
MAX_TRIES=5
last=0  # epoch s when the last reset finished
tries=0 # resets since the controller last stayed up for RETRY_S
journalctl -k -f -n 0 -o cat | while read -r line; do
	# The kernel logs "HC died" once per death; the "assume dead" line before it is not counted.
	[[ $line == *"HC died"* ]] || continue
	addr=$(grep -oE '[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]' <<<"$line" | head -1)
	(($(date +%s) - last < RETRY_S)) || tries=0
	if ((tries >= MAX_TRIES)); then
		logger -t xhci-watchdog "controller ${addr:-unknown} died after $tries resets in a row; not resetting again"
		continue
	fi
	tries=$((tries + 1))
	flag=
	((tries > 1)) && flag=--rescan
	logger -t xhci-watchdog "controller ${addr:-unknown} died; resetting (try $tries of $MAX_TRIES)"
	sleep 2
	/usr/local/sbin/xhci-reset $flag $addr
	last=$(date +%s)
done
