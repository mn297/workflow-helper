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

fflazy() {
  if [ -z "$1" ]; then
    echo "Usage: fflazy <file.ts>"
    return 1
  fi
  input_file=$1
  output_file="${input_file%.ts}.mkv"
  ffmpeg -i "$input_file" -c copy "$output_file"
}
# ffmpeg -i bansheechapter.ts -map 0 -c:v libx264 -crf 18 -preset fast -c:a aac -b:a 128k bansheechapter_fixed.mkv
# ffmpeg -i bansheechapter.ts -map 0:v -map 0:a -c:v libx264 -crf 18 -preset fast -c:a aac -b:a 128k bansheechapter_fixed.mkv


# alias scon='source "$HOME/miniconda3/Scripts/activate"'
# scon() {
#     cmd.exe /C "C:\Users\john\miniconda3\Scripts\activate.bat C:\Users\john\miniconda3 && bash"
# }

# scon() {
#   source "$HOME/miniconda3/Scripts/activate" "$HOME/miniconda3"
# }
scon() {
  # Unset other Python paths if necessary
  unset PYENV_ROOT
  unset PYENV_HOME
  unset PYENV
  unset PYTHONHOME
  unset PYTHONPATH

  source "$HOME/anaconda3/Scripts/activate" "$HOME/anaconda3"
  # source "$HOME/miniconda3/Scripts/activate" "$HOME/miniconda3"

  if [ -n "$1" ]; then
    conda activate "$1"
  else
    echo "No environment specified. Activating the base environment."
  fi
}

sros() {
  # Unset other Python paths if necessary
  unset PYTHONHOME
  unset PYTHONPATH
  unset PYENV

  # Activate base Conda environment
  source "$HOME/miniconda3/Scripts/activate" "$HOME/miniconda3"
  # Activate the ros_env environment
  conda activate ros_env

  # Modify PATH to use the Python from the ros_env environment
  export PATH="$HOME/miniconda3/envs/ros_env:$PATH"
  export PYTHONPATH="$HOME/miniconda3/envs/ros_env/Lib/site-packages:$PYTHONPATH"

}

senv() {
  # Unset other Python paths if necessary
  unset PYTHONHOME
  unset PYTHONPATH
  unset PYENV

  source "./venv/Scripts/activate" "./venv"
}

# Load pyenv automatically by adding
# export PYENV_ROOT="$HOME/.pyenv"
# [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
# eval "$(pyenv init --path)"
# eval "$(pyenv init -)"
# eval "$(pyenv virtualenv-init -)"

# export PYENV_ROOT="$HOME/.pyenv"
# export PATH="$PYENV_ROOT/bin:$PATH"
# echo $PYENV_ROOT
# echo $PATH
# eval "$(pyenv init --path)"
# eval "$(pyenv init -)"
# eval "$(pyenv virtualenv-init -)"

# Load Angular CLI autocompletion.
source <(ng completion script)

# WSL
codewsl() {
  local pwd_clip="code /mnt$(pwd | sed 's/^\/mnt//')"
  echo $pwd_clip | clip.exe
  code --remote wsl+Ubuntu
}

getwsl() {
  local pwd_clip="/mnt$(pwd | sed 's/^\/mnt//')"
  echo $pwd_clip
  echo $pwd_clip | clip.exe
}

alias pio_run='"/c/Users/john/.platformio/penv/Scripts/platformio.exe" run --environment teensy40'

alias penv='source ./venv/Scripts/activate'
alias gclon='git clone'