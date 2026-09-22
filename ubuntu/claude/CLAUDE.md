
## Docs writing

When writing or rewriting technical docs (README, runbook, procedure, error message, release notes, incident report, API guide): invoke the `simple-english` skill (ASD-STE100). Default **pragmatic** mode. Skip for chat replies, marketing, and code unless asked.

## Docstrings

When writing or rewriting any module, class, or public-function docstring summary line: invoke the `writing-docstring-summaries` skill first. This is the default — no need to ask.

Skip for private helpers, inline comments, and test bodies unless asked.

## Subagent model

When the session model is Fable 5 and you dispatch a subagent that writes or edits code, pass `model: "opus"` to the Agent tool (or `opts.model` in a Workflow). Fable orchestrates, Opus implements. This is the default — no need to ask.

Let the subagent inherit the session model for read-only work (search, locate, summarize) and for one-line mechanical edits.

`subagent_type: "fork"` always runs on the parent model and ignores the override; dispatch a fresh agent when the work needs Opus.

## Python environments

Set up every Python environment with pixi (`pixi.toml`, `pixi install`, `pixi run`). When a repo ships conda instructions (`environment.yml`), translate them into a `pixi.toml`: take python, CUDA and pytorch from conda-forge, then add the remaining pip wheels and source builds as pypi dependencies. The user never uses conda.
