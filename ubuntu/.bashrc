lazygit() {
  if [ "$1" = "--amend" ]; then
    if [ "$2" = "--message" ] || [ "$2" = "-m" ]; then
      git add .
      git commit --amend -m "$3"
    else
      git add .
      git commit --amend
    fi
    git push --force
  elif [ "$1" = "--fixup" ]; then
    git add .
    git commit --fixup HEAD
    git push
  else
    git add .
    git commit -m "$1"
    git push
  fi
}

# alias sros='source /opt/ros/noetic/setup.bash'
alias sros='source /opt/ros/noetic/setup.bash && [ -f devel/setup.bash ] && source devel/setup.bash'
alias kros='killall -9 roscore rosmaster rosout roslaunch rosmaster; rosnode cleanup ; rosnode kill -a ; killall -9
gzclient ; killall -9 gzserver ;'

gsettings set org.gnome.desktop.interface enable-animations false

# pyenv
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
