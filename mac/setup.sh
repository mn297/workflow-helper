#!/bin/bash
#
# Machine setup for macOS.
#
# Usage:
#   ./setup.sh
#
set -uo pipefail

set -E
FAILED=()
trap 'FAILED+=("line $LINENO: $BASH_COMMAND")' ERR
trap 'printf "\nfailures: %s\n" "${#FAILED[@]}"; printf "  %s\n" "${FAILED[@]:-none}"' EXIT

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

[ "$(id -u)" -eq 0 ] && {
	echo "Run as your normal user, not root." >&2
	exit 1
}

if ! command -v brew >/dev/null; then
	if [ -x /opt/homebrew/bin/brew ]; then
		eval "$(/opt/homebrew/bin/brew shellenv)"
	elif [ -x /usr/local/bin/brew ]; then
		eval "$(/usr/local/bin/brew shellenv)"
	else
		echo "Homebrew is required: https://brew.sh/" >&2
		exit 1
	fi
fi

# Official cask: https://karabiner-elements.pqrs.org/
say "Installing Karabiner-Elements"
brew install --cask karabiner-elements

say "Installing Karabiner config"
mkdir -p "$HOME/.config/karabiner"
cp "$HERE/karabiner.json" "$HOME/.config/karabiner/karabiner.json"

echo "Grant Accessibility, Input Monitoring, and DriverKit permissions in System Settings."
echo "See https://karabiner-elements.pqrs.org/docs/getting-started/installation/"

say "Installing Spotify"
brew install --cask spotify

# Official cask: https://www.videolan.org/vlc/
say "Installing VLC"
brew install --cask vlc

# Official cask: https://rectangleapp.com/
say "Installing Rectangle"
brew install --cask rectangle

# Official cask: https://www.cursor.com/ — also links `cursor` onto PATH
say "Installing Cursor"
brew install --cask cursor

say "Installing Cursor keybindings"
mkdir -p "$HOME/Library/Application Support/Cursor/User"
cp "$HERE/cursor/keybindings.json" "$HOME/Library/Application Support/Cursor/User/keybindings.json"
