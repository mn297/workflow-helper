#!/usr/bin/env bash
#
# Map mouse thumb buttons 8/9 to continuous scroll up/down on Ubuntu 24.04.
#
#   button 8 (BTN_SIDE / "back")     -> hold to scroll UP
#   button 9 (BTN_EXTRA / "forward") -> hold to scroll DOWN
#
# Uses input-remapper, which rewrites events at the evdev layer. That means it
# works on both X11 and Wayland, unlike `xinput set-button-map` (X11 only, and
# one notch per click with no hold-to-repeat).
#
# The wheel() macro loops while the button is held and emits both REL_WHEEL and
# REL_WHEEL_HI_RES, so smooth-scrolling apps (GTK, Firefox, Chrome) behave.
#
# Usage:
#   ./setup.sh                          # default device + speed
#   DEVICE="Logitech MX Master 3S" ./setup.sh
#   SPEED=20 ./setup.sh                 # gentler
#
set -euo pipefail

DEVICE="${DEVICE:-Logitech MX Master 3S}"
PRESET="${PRESET:-thumb-scroll}"
SPEED="${SPEED:-120}"   # notches/sec ~= SPEED/2 (rel_rate is 60 Hz)

# Which evdev codes to map. 275/276 is what libinput reports as X11 buttons 8/9.
UP_CODE="${UP_CODE:-275}"     # BTN_SIDE
DOWN_CODE="${DOWN_CODE:-276}" # BTN_EXTRA

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

[ "$(id -u)" -eq 0 ] && { echo "Run as your normal user, not root." >&2; exit 1; }

# ---------------------------------------------------------------- 1. install
say "Installing input-remapper"
if ! command -v input-remapper-control >/dev/null; then
    sudo apt-get update
    sudo apt-get install -y input-remapper
else
    echo "already installed: $(dpkg-query -W -f'${Version}' input-remapper 2>/dev/null || echo present)"
fi

# The daemon does the injecting and must be up at boot. The package also ships
# /etc/xdg/autostart/input-remapper-autoload.desktop, which runs
# `input-remapper-control --command autoload` at login and applies the preset.
# Only escalate if something actually needs changing, so reruns need no sudo.
say "Enabling the daemon"
if [ "$(systemctl is-enabled input-remapper-daemon.service 2>/dev/null)" = enabled ] \
   && systemctl is-active --quiet input-remapper-daemon.service; then
    echo "already enabled and running"
else
    sudo systemctl enable --now input-remapper-daemon.service
    systemctl is-active input-remapper-daemon.service
fi

# ------------------------------------------------------- 2. write the preset
# input-remapper keys a preset to a device by an md5 of its capabilities+name,
# so compute it from the live device rather than hardcoding it.
say "Writing preset '$PRESET' for '$DEVICE'"
DEVICE="$DEVICE" PRESET="$PRESET" SPEED="$SPEED" \
UP_CODE="$UP_CODE" DOWN_CODE="$DOWN_CODE" python3 - <<'PY'
import os, sys, evdev
from inputremapper.utils import get_device_hash
from inputremapper.configs.preset import Preset
from inputremapper.configs.mapping import Mapping
from inputremapper.configs.input_config import InputCombination, InputConfig
from inputremapper.configs.paths import get_preset_path
from inputremapper.configs.global_config import GlobalConfig

name  = os.environ["DEVICE"]
preset_name = os.environ["PRESET"]
speed = int(os.environ["SPEED"])

dev = next((d for d in map(evdev.InputDevice, evdev.list_devices())
            if d.name == name and evdev.ecodes.EV_REL in d.capabilities()), None)
if dev is None:
    sys.exit(f"Device {name!r} not found. Plug it in, or list names with:\n"
             f"  python3 -c \"import evdev;[print(evdev.InputDevice(p).name) "
             f"for p in evdev.list_devices()]\"")

h = get_device_hash(dev)
print(f"{dev.path}  hash={h}")

preset = Preset(get_preset_path(name, preset_name))
for code, direction in ((int(os.environ["UP_CODE"]), "up"),
                        (int(os.environ["DOWN_CODE"]), "down")):
    preset.add(Mapping(
        input_combination=InputCombination(
            [InputConfig(type=evdev.ecodes.EV_KEY, code=code, origin_hash=h)]
        ),
        target_uinput="mouse",
        output_symbol=f"wheel({direction}, {speed})",
        mapping_type="key_macro",
        name=f"{evdev.ecodes.BTN[code]} -> scroll {direction}",
    ))
preset.save()

# autoload = re-apply this preset at every login
cfg = GlobalConfig()
cfg.load_config()
cfg.set_autoload_preset(name, preset_name)   # persists on its own
PY

# ------------------------------------------------------------- 3. apply now
say "Applying"
input-remapper-control --command stop --device "$DEVICE" >/dev/null 2>&1 || true
input-remapper-control --command start --device "$DEVICE" --preset "$PRESET"

sleep 2
if grep -q "input-remapper $DEVICE forwarded" /proc/bus/input/devices; then
    say "Active — hold button 8 to scroll up, button 9 to scroll down."
else
    echo "WARNING: injection did not come up. Check: journalctl -u input-remapper-daemon -n 40" >&2
    exit 1
fi

cat <<EOF

Speed        : $SPEED  (~$((SPEED / 2)) notches/sec)
Preset file  : ~/.config/input-remapper-2/presets/$DEVICE/$PRESET.json
Autoload     : ~/.config/input-remapper-2/config.json

Retune       : SPEED=30 ./setup.sh
Disable      : input-remapper-control --command stop-all
Re-enable    : input-remapper-control --command autoload
GUI          : input-remapper-gtk

If the wrong buttons respond, find your real codes with
  sudo evtest        # pick the mouse, press the thumb buttons
and rerun with e.g.  UP_CODE=278 DOWN_CODE=277 ./setup.sh
EOF
