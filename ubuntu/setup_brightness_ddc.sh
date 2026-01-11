sudo apt update && sudo apt install -y ddcutil xbindkeys && \
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
sudo usermod -aG i2c "$USER" && \
[ -f ~/.xbindkeysrc ] || xbindkeys --defaults > ~/.xbindkeysrc && \
awk 'BEGIN{p=1} /# >>> DDCUTIL KEYS BEGIN >>>/{p=0} {if(p)print} END{}' ~/.xbindkeysrc > ~/.xbindkeysrc.tmp && mv ~/.xbindkeysrc.tmp ~/.xbindkeysrc && \
cat >> ~/.xbindkeysrc << 'EOF'
# >>> DDCUTIL KEYS BEGIN >>>
# Numpad 8 → brightness up
"~/bin/brightness-up.sh"
  KP_8

# Numpad 5 → brightness down
"~/bin/brightness-down.sh"
  KP_5
# >>> DDCUTIL KEYS END >>>
EOF
pkill -x xbindkeys 2>/dev/null; xbindkeys
