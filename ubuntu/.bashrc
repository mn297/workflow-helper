# alias sros='source /opt/ros/noetic/setup.bash'
alias sros='source /opt/ros/noetic/setup.bash && [ -f devel/setup.bash ] && source devel/setup.bash'

gsettings set org.gnome.desktop.interface enable-animations false

# pyenv
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
