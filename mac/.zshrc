# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

alias brew='env PATH="${PATH//$(pyenv root)\/shims:/}" brew'
alias brew="env PATH=(string replace (pyenv root)/shims '' \"\$PATH\") brew"
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
# fish;

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/opt/miniconda3/bin/conda' 'shell.zsh' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/opt/miniconda3/etc/profile.d/conda.sh" ]; then
        . "/opt/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="/opt/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

source /opt/powerlevel10k/powerlevel10k.zsh-theme
source ~/powerlevel10k/powerlevel10k.zsh-theme

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

alias scon='unset PYENV_VERSION; export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/miniconda3/bin:$PATH"'
# alias sros='unset PYENV_VERSION; export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/miniconda3/bin:$PATH"; conda activate ros_env; cd devel; source setup.bash; cd ..'
sros() {
    unset PYENV_VERSION
    export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/miniconda3/bin:$PATH"
    conda activate ros_env
    if cd devel; then
        source setup.bash
        cd ..
    fi
}
# alias sros='conda activate ros_env; cd devel; source setup.bash; cd ..'

source ~/.zsh/zsh-autosuggestions/zsh-autosuggestions.zsh


# pyenv settings
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"