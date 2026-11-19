
## Personal email

Never write the owner's personal email address (the Outlook one) into a file, commit, git config,
package manifest, log or request. Use `mn297@users.noreply.github.com` for git identity and for every
author or maintainer field (`package.xml`, `setup.py`, `pyproject.toml`, `Cargo.toml`). Before a
commit, check that the staged diff and the commit's author and committer carry no personal address.

## Docs writing

When writing docs (README, runbook, spec, report, agent prompt): short sentences, active voice, simple tenses.
Put the answer or result first. Define a term at its first use. Cut filler words.
Keep hedges that carry meaning ("may", "likely", "untested"): never turn a guess into a flat claim.

## Specs for a fresh session

Write a spec only when the owner asks for one ("write the spec", "spec this", "recut the spec") or
asks for a file to hand to a fresh session. Then write one self-contained file in `docs/specs/`, in
the format of `~/workflow-helper/spec-format-steps.md`: read that file first. Write no separate prompt
or handoff file. Run the builder check, commit the spec and stop; do not launch implementers from the
planning session. The older `~/workflow-helper/spec-format.md` stays only for reading specs already
written in it.

Every other markdown file stays free-form: a brainstorm, a plan, design notes, research notes, an
options memo, a plan-mode plan. Choose the structure that fits the problem. Do not use the spec
format's sections, requirement IDs or test tables there, and do not put such a file in `docs/specs/`.
When the owner's wish is unclear, write free-form and offer the spec in one line.

## Owner checks

Run every check you can run yourself, and show the real output. Ask the owner to run a command only
when it needs their hands, eyes, hardware, keys or accounts. Then give one command that writes its
output to a file you can read, and state the result you expect before the owner runs it.

## Docstrings and comments

When writing or rewriting any module, class, or public-function docstring summary line, or writing comments on code you add or change: invoke the `writing-docstring-summaries` skill first. This is the default — no need to ask.

Skip for private helpers and test bodies unless asked. Leave comments on lines you did not change as they are.

## Subagent model

Pick each subagent's model by the difficulty of its task, not by a fixed split. Pass `model` to the Agent tool (or `opts.model` in a Workflow) when the default does not fit.

- Haiku or Sonnet: search, locate, summarize, smoke runs, ports and builds that repeat a known pattern, one-line mechanical edits.
- Opus: implementation from a clear spec, refactors that tests guard, docs edits with given numbers.
- Fable: subtle math or numerics, design choices a spec leaves open, hard debugging, unattended orchestration, and reviews where a missed bug costs most.

Move a task up a tier when it fails twice or its result looks wrong. `subagent_type: "fork"` always runs on the parent model and ignores the override.

When you orchestrate a spec as Opus (high or xhigh effort), ask a smarter model for help where complexity or uncertainty calls for it: a design choice the spec leaves open, a bug that resists two tries, a result you cannot explain. Send it to a Fable subagent with the full context, then act on its answer.

## Code search

For structural questions about Python code, use the `LSP` tool first (pyright, from the `pyright-lsp` plugin): `goToDefinition`, `findReferences`, `incomingCalls` and `outgoingCalls`, `workspaceSymbol`, `documentSymbol`. It reads the files as they are now, uncommitted work included. An import it reports as "could not be resolved" usually means the repo's `pyrightconfig.json` lacks that environment, not a code bug.

Use Grep or `rg` for literal strings, configs, logs, docs and non-Python files, and when the LSP finds nothing.

## Python environments

Set up every Python environment with pixi (`pixi.toml`, `pixi install`, `pixi run`). When a repo ships conda instructions (`environment.yml`), translate them into a `pixi.toml`: take python, CUDA and pytorch from conda-forge, then add the remaining pip wheels and source builds as pypi dependencies. The user never uses conda.
