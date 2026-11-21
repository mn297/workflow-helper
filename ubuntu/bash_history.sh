# Per-terminal bash history: each open terminal keeps its own list, so Up
# never recalls a command typed in another open terminal. A new terminal
# starts with the commands of every terminal that has already closed.
# Append this file to ~/.bashrc:
#
#   cat ~/workflow-helper/ubuntu/bash_history.sh >> ~/.bashrc
#
# Each shell writes to ~/.bash_history_sessions/bash-<pid>.hist after every
# command. On exit that file moves into ~/.bash_history (the archive).
# Terminals that were killed (no exit trap) are archived by the next shell
# that starts. Do not overwrite PROMPT_COMMAND with a bare string: that
# breaks the VS Code / Cursor shell integration.

HIST_ARCHIVE="$HOME/.bash_history"
HIST_DIR="$HOME/.bash_history_sessions"
HISTSIZE=100000
HISTFILESIZE=200000
HISTCONTROL=ignoreboth
shopt -s histappend

# Move a closed terminal's history into the archive. mv claims the file
# first, so two shells starting together cannot both append it.
__hist_archive() {
	local claimed="$1.$$.archiving"
	mv -f -- "$1" "$claimed" 2>/dev/null || return
	cat -- "$claimed" >>"$HIST_ARCHIVE" && rm -f -- "$claimed"
}

__hist_on_exit() {
	# Non-interactive shells that inherit these functions must not archive
	# a terminal that is still open.
	[[ $HISTFILE == "$HIST_DIR/bash-$$.hist" ]] || return
	builtin history -a
	__hist_archive "$HISTFILE"
	# bash writes HISTFILE again after the EXIT trap; stop it recreating the file.
	unset HISTFILE
	if (($(wc -l <"$HIST_ARCHIVE") > HISTFILESIZE * 6 / 5)); then
		tail -n "$HISTFILESIZE" -- "$HIST_ARCHIVE" >"$HIST_ARCHIVE.$$" &&
			mv -f -- "$HIST_ARCHIVE.$$" "$HIST_ARCHIVE"
	fi
}

__hist_save() {
	builtin history -a
}

if [[ $- == *i* ]]; then
	mkdir -p -- "$HIST_DIR"
	for __hist_file in "$HIST_DIR"/bash-*.hist; do
		[[ -e $__hist_file ]] || continue
		__hist_pid="${__hist_file##*/bash-}"
		__hist_pid="${__hist_pid%.hist}"
		# A file named after this shell's PID belongs to a dead terminal whose PID was reused.
		if [[ $__hist_pid == "$$" ]] || ! kill -0 "$__hist_pid" 2>/dev/null; then
			__hist_archive "$__hist_file"
		fi
	done
	unset __hist_file __hist_pid

	HISTFILE="$HIST_DIR/bash-$$.hist"
	[[ -r $HIST_ARCHIVE ]] && builtin history -r "$HIST_ARCHIVE"
	trap __hist_on_exit EXIT

	if declare -p PROMPT_COMMAND 2>/dev/null | grep -q 'declare -a'; then
		PROMPT_COMMAND+=(__hist_save)
	elif [[ -n ${PROMPT_COMMAND:-} ]]; then
		PROMPT_COMMAND=("$PROMPT_COMMAND" __hist_save)
	else
		PROMPT_COMMAND=(__hist_save)
	fi
fi
