"""Hand an agent the docstring and comment rules at its first Python docstring or comment.

A Claude Code hook. On PostToolUse of Write or Edit on a ``.py`` file whose new text holds a
docstring or a comment, it returns the rule sections of SKILL.md as ``additionalContext``, once
per agent. The main session and each subagent count as separate agents, because a subagent
does not see the context of its parent. A main session whose transcript shows that the skill
was already invoked gets nothing. On SessionStart after a compaction, the markers of that
session are deleted, because the compaction summary drops the injected text.

Agents load a skill on an instruction only part of the time (about two in three, in a sample
of 83 agents that wrote docstrings). A hook fires every time.
"""

import json
import os
import re
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent / "SKILL.md"
MARKERS = Path(tempfile.gettempdir()) / f"claude-docstring-hook-{os.getuid()}"
SECTIONS = ("Pick the shape first", "Hard rules for line 1", "Comments on lines you write",
            "Describe the code, not its history", "Scope")
# A comment token, not a shebang or a linter pragma.
COMMENT = re.compile(r"(?m)(?:^|\s)#(?!!)(?!\s*(?:noqa|type:|pragma|fmt:))\s*\S")


def rules() -> str:
    """Cut the rule sections and the edit gate out of SKILL.md, without the examples."""
    text = SKILL.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^## ", text)
    keep = ["## " + p.strip() for p in parts if p.split("\n", 1)[0].strip() in SECTIONS]
    gate = re.search(r"(?ms)^Edit an existing summary.*?not a reason\.$", text)
    if gate:
        keep.insert(2, gate.group(0))
    return "\n\n".join(keep)


def new_text(tool_input: dict) -> str:
    if "content" in tool_input:
        return tool_input["content"] or ""
    edits = tool_input.get("edits") or [tool_input]
    return "\n".join(e.get("new_string") or "" for e in edits)


def skill_invoked(transcript: str) -> bool:
    try:
        with open(transcript, encoding="utf-8", errors="ignore") as f:
            return any('"writing-docstring-summaries"' in line and '"Skill"' in line for line in f)
    except OSError:
        return False


def main() -> None:
    event = json.load(sys.stdin)
    session = re.sub(r"[^\w-]", "", event.get("session_id", "nosession"))
    if event.get("hook_event_name") == "SessionStart":
        for m in MARKERS.glob(f"{session}*"):
            m.unlink(missing_ok=True)
        return

    tool_input = event.get("tool_input") or {}
    path = tool_input.get("file_path", "")
    if not path.endswith((".py", ".pyi")):
        return
    text = new_text(tool_input)
    if '"""' not in text and "'''" not in text and not COMMENT.search(text):
        return

    agent = re.sub(r"[^\w-]", "", event.get("agent_id") or "main")
    marker = MARKERS / f"{session}.{agent}"
    if marker.exists():
        return
    if agent == "main" and skill_invoked(event.get("transcript_path", "")):
        return
    MARKERS.mkdir(mode=0o700, exist_ok=True)
    marker.touch()

    context = (f"You just wrote docstrings or comments in {path}. These are the rules of the "
               "writing-docstring-summaries skill. Recheck the lines you wrote against them, and "
               "apply them to the rest of this task. Leave lines you did not change as they are."
               "\n\n" + rules())
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                             "additionalContext": context}}))


if __name__ == "__main__":
    main()
