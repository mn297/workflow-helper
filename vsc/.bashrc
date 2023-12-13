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

lazyffm() {
    if [ -z "$1" ]; then
        echo "Usage: lazyffm <file.ts>"
        return 1
    fi
    input_file=$1
    output_file="${input_file%.ts}.mkv"
    ffmpeg -i "$input_file" -c copy "$output_file"
}

