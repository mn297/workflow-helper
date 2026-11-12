#!/bin/bash
# kros: stop every ROS 2 and RealSense process of this user, then show who still holds the D455.
#
# It matches what a process is, not a loose name:
#   - ROS 2 nodes: every process started with --ros-args (all launched nodes)
#   - the ros2 command line and ros2 launch: an argument that ends in bin/ros2
#   - the ros2 daemon (ros2cli.daemon) and the Zenoh router (rmw_zenohd)
#   - RealSense programs: realsense2_camera_node, realsense-viewer and the rs-* tools
# It sends SIGINT, waits up to 5 s, sends SIGTERM, waits up to 3 s, then sends SIGKILL.
# A process stuck in the kernel (state D) survives even SIGKILL: unplug the camera then.
#
# Usage: kros        stop them
#        kros -n     list them and stop nothing
set -u

dry=0
[ "${1:-}" = "-n" ] && dry=1
RS_TOOLS=" realsense2_camera_node realsense-viewer rs-enumerate-devices rs-record rs-convert rs-embed rs-fw-update rs-fw-logger rs-terminal "

# kros and the shells that started it: their command lines can name ROS (bash -c "... ros2 ...").
ancestors=" "
a=$$
while [ "$a" -gt 1 ] 2>/dev/null; do
	ancestors+="$a "
	a=$(awk '{print $4}' "/proc/$a/stat" 2>/dev/null) || break
done

targets() {
	local p pid cmd exe
	for p in /proc/[0-9]*; do
		pid=${p#/proc/}
		case "$ancestors" in *" $pid "*) continue ;; esac
		[ -O "$p" ] || continue
		cmd=$(tr '\0' ' ' <"$p/cmdline" 2>/dev/null) || continue
		[ -n "$cmd" ] || continue
		exe=$(basename "$(readlink "$p/exe" 2>/dev/null)" 2>/dev/null)
		case "$cmd" in
		*--ros-args* | */bin/ros2\ * | *ros2cli.daemon* | *_ros2_daemon* | *rmw_zenohd*)
			echo "$pid"
			continue
			;;
		esac
		case "$RS_TOOLS" in *" $exe "*) echo "$pid" ;; esac
	done
}

show() {
	local pid
	for pid in "$@"; do
		[ -d "/proc/$pid" ] || continue
		printf '  %-7s %-2s %s\n' "$pid" "$(awk '{print $3}' "/proc/$pid/stat" 2>/dev/null)" \
			"$(tr '\0' ' ' <"/proc/$pid/cmdline" 2>/dev/null | cut -c1-150)"
	done
}

alive() {
	local pid out=()
	for pid in "$@"; do [ -d "/proc/$pid" ] && out+=("$pid"); done
	echo "${out[@]}"
}

wait_gone() { # wait_gone SECONDS PID...
	local t=$(($1 * 10))
	shift
	while [ "$t" -gt 0 ] && [ -n "$(alive "$@")" ]; do
		sleep 0.1
		t=$((t - 1))
	done
}

mapfile -t pids < <(targets)
if [ ${#pids[@]} -eq 0 ]; then
	echo "kros: no ROS 2 or RealSense process"
else
	echo "kros: ${#pids[@]} process(es):"
	show "${pids[@]}"
	[ "$dry" -eq 1 ] && echo "kros: -n given, stopped nothing"
	[ "$dry" -eq 1 ] || for sig in INT TERM KILL; do
		left=$(alive "${pids[@]}")
		[ -z "$left" ] && break
		# shellcheck disable=SC2086
		kill -s "$sig" $left 2>/dev/null
		case $sig in INT) wait_gone 5 $left ;; TERM) wait_gone 3 $left ;; KILL) wait_gone 2 $left ;; esac
	done
	left=$(alive "${pids[@]}")
	if [ "$dry" -eq 1 ]; then
		:
	elif [ -n "$left" ]; then
		echo "kros: still alive (state D = stuck in the kernel; unplug the camera):"
		# shellcheck disable=SC2086
		show $left
	else
		echo "kros: all stopped"
	fi
fi

# Who holds the D455 now, and is it on the bus?
for d in /sys/bus/usb/devices/*; do
	[ -f "$d/idProduct" ] && [ "$(cat "$d/idProduct")" = "0b5c" ] && [ "$(cat "$d/idVendor")" = "8086" ] || continue
	node=$(printf '/dev/bus/usb/%03d/%03d' "$(cat "$d/busnum")" "$(cat "$d/devnum")")
	holders=$(fuser "$node" 2>/dev/null)
	echo "D455: $(basename "$d") at $(cat "$d/speed") Mb/s, $node, held by: ${holders:-nobody}"
	exit 0
done
echo "D455: not on the USB bus"
