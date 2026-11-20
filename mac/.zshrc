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

PATH="$HOME/perl5/bin${PATH:+:${PATH}}"; export PATH;
PERL5LIB="$HOME/perl5/lib/perl5${PERL5LIB:+:${PERL5LIB}}"; export PERL5LIB;
PERL_LOCAL_LIB_ROOT="$HOME/perl5${PERL_LOCAL_LIB_ROOT:+:${PERL_LOCAL_LIB_ROOT}}"; export PERL_LOCAL_LIB_ROOT;
PERL_MB_OPT="--install_base \"$HOME/perl5\""; export PERL_MB_OPT;
PERL_MM_OPT="INSTALL_BASE=$HOME/perl5"; export PERL_MM_OPT;

# bun completions
[ -s "$HOME/.bun/_bun" ] && source "$HOME/.bun/_bun"

# bun
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

# Jax MPS
export JAX_ENABLE_X64=True
export ENABLE_PJRT_COMPATIBILITY=1

export TURTLEBOT3_MODEL=burger

# sros

# list in MB and full path
export CLICOLOR=1
export LSCOLORS=ExFxBxDxCxegedabagacad
alias ls='ls -G'
alias ll='ls -alhF'
export HOST="localhost"

# History: each open terminal keeps its own list, so Up never recalls a
# command typed in another open terminal. A new terminal starts with the
# commands of every terminal that has already closed.
typeset -g HIST_ARCHIVE="${HOME}/.zsh_history"
typeset -g HIST_DIR="${HOME}/.zsh_history_sessions"
HISTSIZE=50000
SAVEHIST=50000
setopt APPEND_HISTORY INC_APPEND_HISTORY
setopt HIST_IGNORE_SPACE HIST_REDUCE_BLANKS HIST_FCNTL_LOCK HIST_SAVE_BY_COPY
unsetopt SHARE_HISTORY

# Move a closed terminal's history into the archive. mv claims the file
# first, so two shells starting together cannot both append it.
_hist_archive() {
  local claimed="$1.$$.archiving"
  mv -f -- "$1" "$claimed" 2>/dev/null || return
  cat -- "$claimed" >> "$HIST_ARCHIVE" && rm -f -- "$claimed"
}

_hist_on_exit() {
  # Non-interactive shells that inherit these functions (e.g. tool
  # snapshots) must not archive a terminal that is still open.
  [[ $HISTFILE == "${HIST_DIR}/zsh-$$.hist" ]] || return
  _hist_archive "$HISTFILE"
  if (( $(wc -l < "$HIST_ARCHIVE") > SAVEHIST * 6 / 5 )); then
    tail -n $SAVEHIST -- "$HIST_ARCHIVE" > "$HIST_ARCHIVE.$$" &&
      mv -f -- "$HIST_ARCHIVE.$$" "$HIST_ARCHIVE"
  fi
}

if [[ -o interactive ]]; then
  [[ -d $HIST_DIR ]] || mkdir -p -- "$HIST_DIR"
  # Terminals that were killed never ran their exit hook.
  for _hist_file in "$HIST_DIR"/zsh-*.hist(N); do
    _hist_pid="${${_hist_file:t}#zsh-}"
    _hist_pid="${_hist_pid%.hist}"
    # A file named after this shell's PID belongs to a dead terminal whose PID was reused.
    if [[ $_hist_pid == $$ ]] || ! kill -0 "$_hist_pid" 2>/dev/null; then
      _hist_archive "$_hist_file"
    fi
  done
  unset _hist_file _hist_pid

  HISTFILE="${HIST_DIR}/zsh-$$.hist"
  [[ -r $HIST_ARCHIVE ]] && fc -R "$HIST_ARCHIVE"
  autoload -Uz add-zsh-hook
  add-zsh-hook zshexit _hist_on_exit
fi

# macOS binds Up/Down to up-line-or-search. Cursor's shell integration
# adds prompt lines, so that widget never reaches command history.
bindkey '^[[A' history-beginning-search-backward
bindkey '^[[B' history-beginning-search-forward
bindkey '^[OA' history-beginning-search-backward
bindkey '^[OB' history-beginning-search-forward

# Pasted "# ... ~12 ..." must stay a comment. Otherwise ~12 is a directory-stack entry.
setopt INTERACTIVE_COMMENTS

# Must be last: command colors as you type
source ~/.zsh/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
