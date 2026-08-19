"""Turn transcript events into short preview lines."""

from __future__ import annotations

import os
from dataclasses import dataclass

from .records import STATUS_IDLE, STATUS_WAITING, SessionRecord

#: Preview lines kept per box.
MAX_LINES = 5
#: Events searched back from the tail for the line a waiting session shows.
PENDING_LOOKBACK = 40
#: Characters kept on one preview line before the ellipsis.
LINE_WIDTH = 72

#: Transcript record types that never carry a preview line.
_SKIPPED_TYPES = frozenset(
    {
        "attachment",
        "ai-title",
        "atis-latch",
        "file-history-delta",
        "file-history-snapshot",
        "last-prompt",
        "mode",
        "permission-mode",
        "queue-operation",
        "relocated",
        "summary",
        "system",
        "worktree-state",
    }
)

#: Tool input keys searched, in order, for the argument shown in a label.
_ARG_KEYS = (
    "description",
    "command",
    "file_path",
    "path",
    "pattern",
    "query",
    "skill",
    "url",
    "prompt",
    "notebook_path",
)


@dataclass(frozen=True)
class Label:
    """Hold one preview line and the kind of event behind it."""

    kind: str
    text: str

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return self.text


def clip(text: str, width: int = LINE_WIDTH) -> str:
    """Flatten text to one line and cut it to the preview width."""
    flat = " ".join(str(text).split())
    if len(flat) <= width:
        return flat
    return flat[: width - 1].rstrip() + "…"


def tail(text: str, width: int = LINE_WIDTH) -> str:
    """Flatten text to one line and keep its ending."""
    flat = " ".join(str(text).split())
    if len(flat) <= width:
        return flat
    return "…" + flat[-(width - 1) :].lstrip()


def _blocks(event: dict) -> list[dict]:
    """List the content blocks of a user or assistant event."""
    message = event.get("message")
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return [b for b in content if isinstance(b, dict)]
    return []


def _tool_arg(name: str, tool_input: dict) -> str:
    """Pick the one input value worth showing for a tool call."""
    if not isinstance(tool_input, dict):
        return ""
    if name in ("Read", "Edit", "Write", "NotebookEdit"):
        for key in ("file_path", "notebook_path", "path"):
            value = tool_input.get(key)
            if isinstance(value, str) and value:
                return os.path.basename(value.rstrip("/")) or value
    for key in _ARG_KEYS:
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value
    for value in tool_input.values():
        if isinstance(value, (str, int, float)) and str(value).strip():
            return str(value)
    return ""


def tool_label(name: str, tool_input: dict) -> str:
    """Name a tool call the way the preview box shows it."""
    arg = _tool_arg(name, tool_input)
    if name in ("Edit", "Write", "NotebookEdit"):
        return clip(f"Editing {arg}…" if arg else "Editing…")
    if name == "Read":
        return clip(f"Reading {arg}" if arg else "Reading")
    if not arg:
        return clip(name)
    return clip(f"{name}({arg})")


def _is_user_prompt(event: dict) -> bool:
    """Say whether a user event is something the human typed."""
    if event.get("isMeta"):
        return False
    source = event.get("promptSource")
    if source and source != "typed":
        return False
    return not (event.get("sourceToolUseID") or event.get("sourceToolAssistantUUID"))


def event_label(event: dict) -> Label | None:
    """Turn one transcript event into a preview line, or nothing."""
    kind = event.get("type")
    if kind in _SKIPPED_TYPES:
        return None
    if kind == "assistant":
        for block in reversed(_blocks(event)):
            btype = block.get("type")
            if btype == "tool_use":
                return Label("tool", tool_label(block.get("name") or "tool", block.get("input") or {}))
            if btype == "text":
                text = block.get("text") or ""
                if text.strip():
                    return Label("text", clip(text))
        return None
    if kind == "user":
        blocks = _blocks(event)
        if any(b.get("type") == "tool_result" for b in blocks):
            return None
        if not _is_user_prompt(event):
            return None
        for block in blocks:
            if block.get("type") == "text":
                text = block.get("text") or ""
                if text.strip():
                    return Label("prompt", "› " + tail(text, LINE_WIDTH - 2))
        return None
    return None


def last_label(events: list[dict]) -> Label | None:
    """Give the newest preview line in a transcript, or nothing."""
    for event in reversed(events):
        label = event_label(event)
        if label is not None:
            return label
    return None


def pending_tool_use(events: list[dict]) -> dict | None:
    """Find the tool call at the tail that has no result yet."""
    resolved: set[str] = set()
    for event in events:
        if event.get("type") != "user":
            continue
        for block in _blocks(event):
            if block.get("type") == "tool_result":
                tool_id = block.get("tool_use_id")
                if isinstance(tool_id, str):
                    resolved.add(tool_id)
    for event in reversed(events):
        if event.get("type") != "assistant":
            continue
        for block in reversed(_blocks(event)):
            if block.get("type") != "tool_use":
                continue
            tool_id = block.get("id")
            if isinstance(tool_id, str) and tool_id not in resolved:
                return block
            return None
    return None


def pending_line(record: SessionRecord, events: list[dict]) -> str:
    """Say in one line what a waiting session waits for."""
    block = pending_tool_use(events)
    if block is not None:
        call = tool_label(block.get("name") or "tool", block.get("input") or {})
        return clip(f"Approve: {call}?")
    for event in reversed(events[-PENDING_LOOKBACK:]):
        if event.get("type") != "assistant":
            continue
        for eblock in reversed(_blocks(event)):
            if eblock.get("type") == "text" and (eblock.get("text") or "").strip():
                return clip(tail(eblock["text"]))
    return clip(record.waiting_for or "input needed")


def preview_lines(
    record: SessionRecord,
    events: list[dict],
    max_lines: int = MAX_LINES,
) -> list[Label]:
    """Build the 3-5 preview lines for one session box."""
    labels: list[Label] = []
    for event in events:
        label = event_label(event)
        if label is None:
            continue
        if labels and labels[-1].text == label.text:
            continue
        labels.append(label)

    if record.display_status == STATUS_IDLE and labels and labels[-1].kind == "text":
        done = labels[-1]
        labels[-1] = Label("done", clip("Done: " + done.text))

    head: list[Label] = []
    if record.display_status == STATUS_WAITING:
        head.append(Label("pending", pending_line(record, events)))

    body = labels[-(max_lines - len(head)) :] if max_lines > len(head) else []
    out = head + body
    if not out:
        out = [Label("empty", "(no transcript yet)")]
    return out[-max_lines:]
