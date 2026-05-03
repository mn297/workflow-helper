#!/bin/bash
# Copy bundled input-remapper v2 presets into ~/.config/input-remapper-2
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/input-remapper-2"
DEST="${HOME}/.config/input-remapper-2"

if [ ! -d "$SRC/presets" ]; then
    echo "missing $SRC/presets — run from repo ubuntu/ tree" >&2
    exit 1
fi

mkdir -p "$DEST/presets"
cp "$SRC/config.json" "$DEST/config.json"

shopt -s nullglob
for d in "$SRC/presets"/*; do
    name="$(basename "$d")"
    mkdir -p "$DEST/presets/$name"
    for f in "$d"/*.json; do
        cp "$f" "$DEST/presets/$name/"
    done
done

echo "Installed input-remapper-2 configs to $DEST"
echo "Open Input Remapper to apply/reload if changes do not take effect."
