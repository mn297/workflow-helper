alias sros='source /opt/ros/noetic/setup.bash'

gsettings set org.gnome.desktop.interface enable-animations false

# pyenv
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"