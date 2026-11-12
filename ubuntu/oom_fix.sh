#!/bin/bash
#
# Keep the GNOME session alive through a kernel out-of-memory kill, and put memcap on PATH.
#
#   ./oom_fix.sh
#
# Undo:
#   rm ~/.config/systemd/user/org.gnome.Shell@.service.d/oom.conf ~/.local/bin/memcap
#   systemctl --user daemon-reload
#
# See oom.md for the crash this fixes.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

if [ "$(id -u)" -eq 0 ]; then
	echo "Run as your normal user, not root." >&2
	exit 1
fi

# The kernel never picks gnome-shell (OOMScoreAdjust=-1000), but it can pick an
# app that runs inside the shell's cgroup. systemd's default OOMPolicy=stop then
# stops the shell unit, and its OnFailure= ends the session. With continue,
# only the killed app dies.
dir="$HOME/.config/systemd/user/org.gnome.Shell@.service.d"
mkdir -p "$dir"
printf '[Service]\nOOMPolicy=continue\n' >"$dir/oom.conf"
systemctl --user daemon-reload
systemctl --user list-units --plain --no-legend 'org.gnome.Shell@*.service' | awk '{print $1}' |
	while read -r unit; do
		echo "$unit: OOMPolicy=$(systemctl --user show "$unit" -p OOMPolicy --value)"
	done

mkdir -p "$HOME/.local/bin"
ln -sf "$HERE/memcap" "$HOME/.local/bin/memcap"
echo "memcap -> $HERE/memcap"
