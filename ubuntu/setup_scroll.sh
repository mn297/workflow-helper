#!/bin/bash
# Install dependencies
sudo apt update && sudo apt install -y xbindkeys xdotool x11-utils

mkdir -p ~/bin

# Create a generic "repeat-while-held" helper script
cat > ~/bin/scroll-while-held.sh << 'EOF'
#!/bin/bash
# Usage: ./scroll-while-held.sh <xdotool-key> <lock-file-id>
KEY=$1
LOCK_ID=$2
LOCKfile="/tmp/scroll_${LOCK_ID}.lock"

# If already running for this button, do nothing (debounce)
if [ -f "$LOCKfile" ]; then exit 0; fi

touch "$LOCKfile"

# Loop while the specific button is still held (check via xinput/xquerykeys is hard, 
# so we rely on xbindkeys "Release" event to kill this script's PID or remove lock).
# BUT simpler: xbindkeys triggers this on PRESS. We loop until killed.
# The "Release" binding in .xbindkeysrc will kill this specific instance/loop.

while [ -f "$LOCKfile" ]; do
    xdotool click "$KEY"
    sleep 0.05  # Speed of scroll (lower = faster)
done
EOF
chmod +x ~/bin/scroll-while-held.sh

# Stop any existing xbindkeys to safely update
pkill -x xbindkeys 2>/dev/null

# Backup & Prepare config
[ -f ~/.xbindkeysrc ] || xbindkeys --defaults > ~/.xbindkeysrc
cp ~/.xbindkeysrc ~/.xbindkeysrc.bak

# Remove old custom block if exists (idempotent)
sed -i '/# >>> MOUSE SCROLL BEGIN >>>/,/# >>> MOUSE SCROLL END >>>/d' ~/.xbindkeysrc

# Append new bindings
cat >> ~/.xbindkeysrc << 'EOF'
# >>> MOUSE SCROLL BEGIN >>>
# Button 9 Press -> Start scrolling DOWN (mouse button 5)
"touch /tmp/scroll_b9.lock; while [ -f /tmp/scroll_b9.lock ]; do xdotool click 5; sleep 0.05; done"
  b:9

# Button 9 Release -> Stop scrolling
"rm -f /tmp/scroll_b9.lock"
  release + b:9

# Button 8 Press -> Start scrolling UP (mouse button 4)
"touch /tmp/scroll_b8.lock; while [ -f /tmp/scroll_b8.lock ]; do xdotool click 4; sleep 0.05; done"
  b:8

# Button 8 Release -> Stop scrolling
"rm -f /tmp/scroll_b8.lock"
  release + b:8
# >>> MOUSE SCROLL END >>>
EOF

# Restart
xbindkeys
echo "Done. Button 9 holds Scroll Down, Button 8 holds Scroll Up."
