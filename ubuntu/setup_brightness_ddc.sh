sudo apt update && sudo apt install -y ddcutil xbindkeys i2c-tools && \
mkdir -p ~/bin && \
cat > ~/bin/brightness-up.sh << 'EOF'
#!/bin/bash
ddcutil setvcp 10 + 10
EOF
cat > ~/bin/brightness-down.sh << 'EOF'
#!/bin/bash
ddcutil setvcp 10 - 10
EOF
chmod +x ~/bin/brightness-*.sh && \
sudo usermod -aG i2c "$USER" 2>/dev/null || true && \
[ -f ~/.xbindkeysrc ] || xbindkeys --defaults > ~/.xbindkeysrc && \
awk 'BEGIN{p=1} /# >>> DDCUTIL KEYS BEGIN >>>/{p=0} {if(p)print} END{}' ~/.xbindkeysrc > ~/.xbindkeysrc.tmp && mv ~/.xbindkeysrc.tmp ~/.xbindkeysrc && \
cat >> ~/.xbindkeysrc << XBINDKEYS_EOF
# >>> DDCUTIL KEYS BEGIN >>>
# Numpad 8 → brightness up
"$HOME/bin/brightness-up.sh"
  KP_8

# Numpad 5 → brightness down
"$HOME/bin/brightness-down.sh"
  KP_5
# >>> DDCUTIL KEYS END >>>
XBINDKEYS_EOF
pkill -x xbindkeys 2>/dev/null; xbindkeys

echo ""
echo "Next steps:"
echo "  1. Run:  ddcutil detect   (check that your monitor is detected)"
echo "  2. If using i2c group: log out and back in (or reboot) for /dev/i2c access"
echo "  3. If ddcutil detect fails, try:  sudo ddcutil detect  (to confirm hardware works)"
