# Clean up PATH for VSCODE
terminal_path=$(zsh -l -c 'echo $PATH')
export PATH="$terminal_path"

# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi


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

# alias scon='unset PYENV_VERSION; export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/miniconda3/bin:$PATH"'
# alias sros='unset PYENV_VERSION; export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/miniconda3/bin:$PATH"; conda activate ros_env; cd devel; source setup.bash; cd ..'
scon() {
    unset PYENV_VERSION
    export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/miniconda3/bin:$PATH"
    if [ -n "$1" ]; then
        conda activate "$1"
    else
        echo "No environment specified. Just setting PATH."
    fi
}

sros() {
    unset PYENV_VERSION
    export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/opt/miniconda3/bin:$PATH"
    conda activate ros_env
    if cd devel; then
        source setup.bash
        cd ..
    fi
}
alias kros='pkill -f rosmaster ; pkill -f roscore ; rosnode kill -a ; pkill -f ros ; pkill -f gzserver; pkill -f gzclient'

source ~/.zsh/zsh-autosuggestions/zsh-autosuggestions.zsh


# pyenv settings
export PYENV_ROOT="$HOME/.pyenv"

# Ensure pyenv bin directory is in PATH
if [[ -d "$PYENV_ROOT/bin" ]]; then
  export PATH="$PYENV_ROOT/bin:$PATH"
fi

# Initialize pyenv
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# autocomplete
zstyle ':completion:*' menu select
bindkey '^ ' autosuggest-accept


# Load Angular CLI autocompletion.
source <(ng completion script)
export PATH="/opt/homebrew/opt/ssh-copy-id/bin:$PATH"
export PATH="/opt/homebrew/opt/ssh-copy-id/bin:$PATH"

PATH="/Users/user2/perl5/bin${PATH:+:${PATH}}"; export PATH;
PERL5LIB="/Users/user2/perl5/lib/perl5${PERL5LIB:+:${PERL5LIB}}"; export PERL5LIB;
PERL_LOCAL_LIB_ROOT="/Users/user2/perl5${PERL_LOCAL_LIB_ROOT:+:${PERL_LOCAL_LIB_ROOT}}"; export PERL_LOCAL_LIB_ROOT;
PERL_MB_OPT="--install_base \"/Users/user2/perl5\""; export PERL_MB_OPT;
PERL_MM_OPT="INSTALL_BASE=/Users/user2/perl5"; export PERL_MM_OPT;

# bun completions
[ -s "/Users/user2/.bun/_bun" ] && source "/Users/user2/.bun/_bun"

# bun
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

# Jax MPS
export JAX_ENABLE_X64=True
export ENABLE_PJRT_COMPATIBILITY=1

export TURTLEBOT3_MODEL=burger

sros

# list in MB and full path
alias ll='ls -alhF'
export HOST="localhost"
