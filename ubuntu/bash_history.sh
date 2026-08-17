# Shared bash history so Ctrl+R sees commands from other terminals.
# Append this file to ~/.bashrc. Do not overwrite PROMPT_COMMAND with a
# bare string — that breaks VS Code / Cursor shell integration.
#
#   cat ~/workflow-helper/ubuntu/bash_history.sh >> ~/.bashrc
#   source ~/.bashrc
#
# Make sure that `declare -p PROMPT_COMMAND` lists both __vsc_prompt_cmd
# and __sync_bash_history. Then run `echo vscode-history-test` in one
# terminal. In another, press Enter once, then Ctrl+R and type that string.
#
# HISTCONTROL=ignoreboth skips leading-space commands and consecutive
# duplicates — intentional, not a bug.
# history -a / -n write and read the history file.
# history -c then history -w wipes the file — do not run that.

HISTFILE="$HOME/.bash_history"
HISTSIZE=100000
HISTFILESIZE=200000
shopt -s histappend

__sync_bash_history() {
	builtin history -a
	builtin history -n
}

if declare -p PROMPT_COMMAND 2>/dev/null | grep -q 'declare -a'; then
	PROMPT_COMMAND+=(__sync_bash_history)
elif [[ -n "${PROMPT_COMMAND:-}" ]]; then
	PROMPT_COMMAND=("$PROMPT_COMMAND" __sync_bash_history)
else
	PROMPT_COMMAND=(__sync_bash_history)
fi
