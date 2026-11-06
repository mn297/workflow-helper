
## Docs writing

When writing docs (README, runbook, spec, report, agent prompt): short sentences, active voice, simple tenses.
Put the answer or result first. Define a term at its first use. Cut filler words.
Keep hedges that carry meaning ("may", "likely", "untested"): never turn a guess into a flat claim.

## Specs for a fresh session

A plan for big-bang work is one self-contained spec in `docs/specs/`, in the format of
`~/workflow-helper/spec-format-steps.md`: read that file before writing or recutting a spec. The owner
sends the one spec file to a fresh session, so it carries everything: "Done when" checks first, a
change-at-a-glance and a step map, one chapter per step (goal, files, requirements, design, tests,
gate), one decisions table, and a closing "How to run this" section. Write no separate prompt or
handoff file. Run the builder check, commit the spec and stop; do not launch implementers from the
planning session. The older `~/workflow-helper/spec-format.md` stays only for reading specs already
written in it.

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

codebase-memory-mcp is opt-in: use its graph only for big-picture questions (architecture, change impact across a large package), and check `index_status` first. Its index goes stale after moves and misses uncommitted files.

## Python environments

Set up every Python environment with pixi (`pixi.toml`, `pixi install`, `pixi run`). When a repo ships conda instructions (`environment.yml`), translate them into a `pixi.toml`: take python, CUDA and pytorch from conda-forge, then add the remaining pip wheels and source builds as pypi dependencies. The user never uses conda.
