---
name: human-maintainer-pass
description: >
  Rewrites code or markdown that an LLM generated so it reads like a person on
  the project wrote it: cuts one-use helpers, speculative error handling,
  planted comments, template headings, and padded prose, without changing
  behavior or meaning. Use when the user points at generated code, a README,
  docs, notes, or a skill and asks to make it look human made, or says
  "human-maintainer pass", "de-slop", "LLM smell", "AI smell", "sus
  comments", or "looks AI-generated".
compatibility: claude-code cursor codex gemini-cli opencode
metadata:
  tags: "Editing, Prose, Code, Readability"
  category: "writing"
---

# human-maintainer-pass

Take code or markdown an LLM wrote and make it look like a person on this project wrote it: someone who knows the codebase and wrote only what the job needed. Behavior and meaning stay the same. Most of the work is deleting.

Human made means fitted to the project, not sloppy. Do not add typos, slang, inconsistent formatting, or deliberate mistakes.

## Scope

Edit only what the model wrote. If the user names a file, that is the target. If they mean recent work ("what you just wrote", "this branch"), use `git status`, `git diff`, and `git diff --staged` to find the generated lines. Code and comments that people wrote stay as they are (check `git blame` when unsure). They are the style reference.

## Steps

1. Read two or three nearby files that people wrote. Note how they name things, how many comments and docstrings they have, how they handle errors, whether they use type hints, and how their docs read (heading case, length, tone). That is the target style. In a new repo with nothing to copy, default to short and plain.
2. Before editing, name the three to five smells that most give the artifact away. Fix those first. Small stuff can wait or be skipped.
3. Delete before rewriting. Inline one-use helpers, drop layers that only pass calls through, collapse sections. A tidier version of the generated outline is still the generated outline.
4. Keep behavior. If a cut would change what the code does (an exception type a caller catches, a log line someone greps for, a public name), leave it and mention it.
5. Check the work. `rg` every name you deleted or inlined to be sure nothing else uses it. Run the repo's tests, linter, or type checker if it has them. In markdown, check that every command, path, and link still matches the repo.
6. Read the diff as a maintainer reviewing a colleague's PR. Cut anything you would ask them to cut. Anything that makes you ask "why is this here?" either gets a reason or goes. Then stop. The next edit after that is taste.

If the artifact already reads as ordinary, say so and change nothing.

## Code

- a function, class, module, or config option used in one place
- a wrapper that adds nothing (`send()` calling `_send_impl()`)
- an abstract base class, protocol, factory, or registry with one implementation
- `utils.py`, `helpers.py`, `constants.py`, `types.py` split out of a small feature
- error handling for failures that cannot happen here: broad `except Exception` that logs and re-raises or returns `None`, retries around local calls, `isinstance` checks on typed arguments, `None` checks on values that are never `None`
- the same validation at every layer instead of once at the boundary
- names longer than the idea (`processed_user_data_list`, `is_valid_input_flag`)
- logging every step, emoji status lines, color-print helpers in a 30-line script
- `__main__` demo blocks, "example usage" at the bottom of a module, `to_dict`/`from_dict` or getters and setters nobody calls
- backward-compatibility shims and deprecated aliases for code that never shipped
- tests that only check that mocks were called, or near-copies of the same test

Keep error handling at real boundaries: user input, files the user supplies, network, subprocesses.

## Comments and docstrings

These are usually the fastest giveaway. Drop:

- comments that narrate the next line (`# Loop through the items`, `# Return the result`)
- section banners (`# ===== Helpers =====`) and step labels (`# Step 1: load data`)
- docstrings on small or private functions that restate the name, and `Args:`/`Returns:` blocks that repeat the signature
- tutorial voice: "we need to", "here we", "now we", "this ensures", "handle the edge case where"
- notes about the edit or the chat: "added for safety", "fixed bug", "updated as requested", "NEW:", "changed from X to Y"
- reassurance: "robust handling", "this should work"
- commented-out code, and TODOs the model left as placeholders

Keep a comment when it explains why and the why is not obvious from the code: a constraint, a workaround, a link to an issue. Match the docstring style the repo already uses.

## Markdown

Structure:

- headings on a doc that fits on one screen, or a heading every few lines
- stock sections: Overview, Introduction, Key Features, Best Practices, Conclusion, Summary, Next Steps, a TL;DR on a short doc
- Contributing, License, and badge sections in a personal repo
- bullets that start with a bold label and a colon (`- **Fast:** ...`), and bold **Note:** or **Important:** callouts
- emoji in headings and bullets
- a table with two rows, or table cells that hold paragraphs
- bullets where a sentence reads better, numbered lists where order does not matter, nesting past one level
- every section the same shape: intro line, three bullets, wrap-up line
- Title Case headings when the repo uses sentence case

Prose:

- em dashes as the default punctuation
- "not just X, it's Y", "whether you're X or Y", adjectives in threes
- delve, leverage, robust, seamless, comprehensive, streamline, powerful, crucial, utilize, facilitate, and similar
- signposting: "it's worth noting", "importantly", "keep in mind"
- "simply", "easily", "just" in front of a command
- an opener that restates the heading, and a closer that restates the doc ("By following these steps...", "Happy coding!", "Feel free to...")
- vague claims ("fast", "safe", "flexible") where the source has a concrete fact

Rewrite toward specific facts from the source: file names, commands, numbers, what actually happens. If a claim has no fact behind it, delete it. When removing em dashes, restructure the sentence. Swapping every dash for a semicolon or colon is the same tic in different punctuation, and swapping words while keeping the padded structure is the same mistake.

## Examples

Code, before:

```python
# ===== Helper Functions =====

def _validate_path(path: str) -> bool:
    """Validate that the given path is a non-empty string.

    Args:
        path: The path to validate.

    Returns:
        True if the path is valid, False otherwise.
    """
    return isinstance(path, str) and len(path) > 0


def load_config(path: str) -> dict:
    """Load configuration from a YAML file."""
    # Validate the input path
    if not _validate_path(path):
        raise ValueError("Invalid path provided")
    try:
        # Open the file and parse the YAML
        with open(path) as f:
            config = yaml.safe_load(f)
        # Ensure we always return a dict for robustness
        return config or {}
    except Exception as e:
        logger.error(f"❌ Failed to load config: {e}")
        raise
```

After:

```python
def load_config(path: str) -> dict:
    with open(path) as f:
        # an empty file loads as None
        return yaml.safe_load(f) or {}
```

The "for robustness" comment became the real reason. An empty path now raises `FileNotFoundError` instead of `ValueError`, which is fine only after `rg` shows no caller catches `ValueError`. Say so in the report.

Markdown, before:

````markdown
## 🚀 Overview

`sync.sh` is a powerful, flexible tool that streamlines syncing your dotfiles — making setup seamless across machines.

## ✨ Key Features

- **Fast:** Syncs everything in seconds.
- **Safe:** Backs up existing files before overwriting.
- **Simple:** One command to get started.

## 📦 Usage

Simply run the following command:

```bash
./sync.sh
```

## 🎯 Conclusion

By following these steps, you can easily keep your dotfiles in sync!
````

After:

````markdown
`sync.sh` symlinks the dotfiles in this repo into `$HOME`. A file that is already there is moved to `~/.dotfiles.bak/` first.

```bash
./sync.sh
```
````

"Symlinks" and the backup path come from reading `sync.sh`. "Fast" had nothing behind it, so it went.

## Report

Reply in a few sentences: the main cuts, anything left on purpose and why, any behavior change, and the checks you ran. Do not recap the lists above or declare the result "now human".
