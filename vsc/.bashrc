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

# alias scon='source "$HOME/miniconda3/Scripts/activate"'
# scon() {
#     cmd.exe /C "C:\Users\john\miniconda3\Scripts\activate.bat C:\Users\john\miniconda3 && bash"
# }

# scon() {
#   source "$HOME/miniconda3/Scripts/activate" "$HOME/miniconda3"
# }
scon() {
  # Unset other Python paths if necessary
  unset PYTHONHOME
  unset PYTHONPATH
  unset PYENV

  source "$HOME/anaconda3/Scripts/activate" "$HOME/anaconda3"
  source "$HOME/miniconda3/Scripts/activate" "$HOME/miniconda3"

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

# Load Angular CLI autocompletion.
source <(ng completion script)
