#!/bin/bash
#
# Step the brightness of whichever monitor the mouse cursor is on, 10% per key press.
#
#   cursor-brightness.sh up|down
#   STEP=5 cursor-brightness.sh up
#
# Laptop panel (eDP/LVDS/DSI): no DDC/CI, so write the kernel backlight through
# logind's SetBrightness, which needs no root. GNOME's slider follows the udev
# change event. External monitor: DDC/CI VCP 0x10 (brightness) via ddcutil.
#
# X11 only: the cursor comes from xdotool and output geometry from xrandr.
#
# Values snap to multiples of STEP: 73 goes up to 80, down to 70.
#
# A DDC write takes ~0.3 s, slower than key autorepeat. So a press only records
# a new target, and one writer per monitor applies the latest target while the
# others exit. Holding the key never queues a backlog.
set -uo pipefail

DIR="${1:-}"
STEP="${STEP:-10}"
case "$DIR" in
up | down) ;;
*)
	echo "usage: $0 up|down" >&2
	exit 2
	;;
esac
if ! [[ "$STEP" =~ ^[1-9][0-9]*$ ]]; then
	echo "STEP must be a positive integer, got '$STEP'" >&2
	exit 2
fi

STATE="${XDG_RUNTIME_DIR:-/tmp}/cursor-brightness"
mkdir -p "$STATE"

# Next multiple of STEP from percent $1 in $DIR, clamped to 0..100.
next_pct() {
	local p=$1 n
	if [ "$DIR" = up ]; then
		n=$(((p / STEP + 1) * STEP))
	else
		n=$((((p + STEP - 1) / STEP - 1) * STEP))
	fi
	((n > 100)) && n=100
	((n < 0)) && n=0
	echo "$n"
}

# ------------------------------------------------------ output under cursor
# Prints "<output> <first 128 EDID bytes as hex>" for the connected output
# whose geometry contains the cursor.
eval "$(xdotool getmouselocation --shell)"
read -r OUTPUT EDID < <(xrandr --current --verbose | awk -v x="$X" -v y="$Y" '
	function flush() { if (hit) { print name, substr(edid, 1, 256); done = 1; exit } }
	/^[^ \t]/ {
		flush(); hit = 0; inedid = 0; edid = ""
		if ($2 == "connected" && match($0, /[0-9]+x[0-9]+\+[0-9]+\+[0-9]+/)) {
			split(substr($0, RSTART, RLENGTH), g, /[x+]/)
			hit = x + 0 >= g[3] + 0 && x + 0 < g[3] + g[1] && y + 0 >= g[4] + 0 && y + 0 < g[4] + g[2]
			name = $1
		}
		next
	}
	hit && /^\tEDID:/ { inedid = 1; next }
	hit && inedid && /^\t\t[0-9a-f]+$/ { gsub(/[ \t]/, ""); edid = edid $0; next }
	{ inedid = 0 }
	END { if (!done) flush() }')
if [ -z "${OUTPUT:-}" ]; then
	echo "no connected output under the cursor at $X,$Y" >&2
	exit 1
fi

# ------------------------------------------------------------ laptop panel
case "$OUTPUT" in
eDP* | LVDS* | DSI*)
	# Same preference order as GNOME: firmware, then platform, then raw.
	BL=
	for type in firmware platform raw; do
		for d in /sys/class/backlight/*; do
			[ "$(cat "$d/type" 2>/dev/null)" = "$type" ] && BL=$d && break 2
		done
	done
	if [ -z "$BL" ]; then
		echo "$OUTPUT: no backlight in /sys/class/backlight" >&2
		exit 1
	fi
	exec 9>"$STATE/panel.lock"
	flock 9
	max=$(<"$BL/max_brightness")
	cur=$(<"$BL/brightness")
	pct=$(next_pct $(((cur * 100 + max / 2) / max)))
	raw=$((pct * max / 100))
	# 0 turns some panels fully off. Keep 1 so the screen stays readable.
	((raw < 1)) && raw=1
	busctl call org.freedesktop.login1 /org/freedesktop/login1/session/auto \
		org.freedesktop.login1.Session SetBrightness ssu backlight "${BL##*/}" "$raw"
	exit
	;;
esac

# ---------------------------------------------------------- DDC/CI monitor
if [ ${#EDID} -ne 256 ]; then
	echo "$OUTPUT: xrandr shows no EDID, cannot match it to a DDC bus" >&2
	exit 1
fi
KEY=$(printf '%s' "$EDID" | md5sum | cut -c1-12)
BUSFILE="$STATE/$KEY.bus"   # i2c bus number, cached until reboot
TARGET="$STATE/$KEY.target" # "<raw target> <raw max>" from the last press
BURST=5                     # seconds a target stays fresh enough to step from

# xrandr names outputs differently from DRM, and the NVIDIA driver links no
# DRM connector to its i2c buses. So match on EDID: find the bus whose EDID
# equals the output's (~1 s scan, only on a cache miss).
find_bus() {
	ddcutil detect --verbose 2>/dev/null | awk -v want="$EDID" '
		/^Display [0-9]/ { ok = 1; bus = ""; hex = ""; next }
		/^[^ ]/ { ok = 0 }
		ok && /I2C bus:/ { sub(/.*i2c-/, ""); bus = $0 }
		ok && /^ +\+00[0-7]0 / {
			for (i = 2; i <= 17; i++) hex = hex $i
			if ($1 == "+0070" && hex == want) { print bus; exit }
		}'
}

# Sets $bus. Pass "fresh" to skip the cache, after a replug renumbered buses.
resolve_bus() {
	if [ "${1:-}" != fresh ] && [ -s "$BUSFILE" ]; then
		bus=$(<"$BUSFILE")
		return 0
	fi
	bus=$(find_bus)
	if [ -z "$bus" ]; then
		rm -f "$BUSFILE"
		echo "$OUTPUT: no DDC/CI display matches its EDID (DDC/CI off in the monitor menu?)" >&2
		return 1
	fi
	echo "$bus" >"$BUSFILE"
}

# Sets $cur and $max from the monitor.
read_vcp() {
	local _
	read -r _ _ _ cur max < <(ddcutil --bus "$bus" getvcp 10 --brief 2>/dev/null)
	[[ "${cur:-}" =~ ^[0-9]+$ && "${max:-}" =~ ^[0-9]+$ ]] && ((max > 0))
}

exec 8>"$STATE/$KEY.lock"    # guards $TARGET read-modify-write
exec 7>"$STATE/$KEY.io.lock" # one ddcutil on this bus at a time

flock 8
resolve_bus || exit 1
if [ -s "$TARGET" ] && (($(date +%s) - $(stat -c %Y "$TARGET") < BURST)); then
	# Mid-burst: step from the pending target, not the not-yet-written monitor.
	read -r cur max <"$TARGET"
else
	# Idle: read the monitor, since its own buttons may have changed it.
	flock 7
	if ! read_vcp; then
		resolve_bus fresh && read_vcp || {
			echo "$OUTPUT: cannot read brightness on /dev/i2c-$bus" >&2
			exit 1
		}
	fi
	flock -u 7
fi
pct=$(next_pct $(((cur * 100 + max / 2) / max)))
echo "$((pct * max / 100)) $max" >"$TARGET"
flock -u 8

# Apply the latest target. If another writer holds the bus, exit: it re-reads
# $TARGET after each write and picks this press up.
applied=
while :; do
	flock -n 7 || exit 0
	read -r want _ <"$TARGET"
	if ! ddcutil --bus "$bus" --noverify setvcp 10 "$want" >/dev/null; then
		rm -f "$BUSFILE" "$TARGET"
		echo "$OUTPUT: setvcp failed on /dev/i2c-$bus" >&2
		exit 1
	fi
	applied=$want
	flock -u 7
	read -r want _ <"$TARGET"
	[ "$want" = "$applied" ] && exit 0
done
