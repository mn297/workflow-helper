# ~/.config/fish/config.fish
eval "$(pyenv init -)"
function lazygit
    if test "$argv[1]" = "--amend"
        if test "$argv[2]" = "--message" -o "$argv[2]" = "-m"
            git add .
            git commit --amend -m "$argv[3]"
        else
            git add .
            git commit --amend
        end
        git push --force
    else
        git add .
        git commit -m "$argv[1]"
        git push
    end
end
