"""Share fixtures and screen helpers across the cc-mirror tests."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

SESSION_ID_WAIT = "11111111-1111-4111-8111-111111111111"
SESSION_ID_BUSY = "22222222-2222-4222-8222-222222222222"
SESSION_ID_IDLE = "33333333-3333-4333-8333-333333333333"


def screen_text(app) -> str:
    """Render the current app screen to plain text, one line per row."""
    strips = app.screen._compositor.render_strips()
    return "\n".join(strip.text.rstrip() for strip in strips)


def write_record(directory: Path, **fields) -> Path:
    """Write one fake ~/.claude/sessions record and return its path."""
    now_ms = int(time.time() * 1000)
    data = {
        "pid": fields.get("pid", 1),
        "sessionId": fields.get("session_id", SESSION_ID_BUSY),
        "cwd": fields.get("cwd", "/home/john/demo"),
        "startedAt": fields.get("started_at", now_ms - 60_000),
        "version": "2.1.235",
        "kind": "interactive",
        "entrypoint": "cli",
        "name": fields.get("name", "demo-aa"),
        "nameSource": "derived",
        "status": fields.get("status", "busy"),
        "updatedAt": fields.get("updated_at", now_ms),
        "messagingSocketPath": f"/run/user/1000/cc-socks/{fields.get('pid', 1)}.sock",
    }
    if "waiting_for" in fields:
        data["waitingFor"] = fields["waiting_for"]
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{data['pid']}.json"
    path.write_text(json.dumps(data))
    return path


def write_transcript(root: Path, slug: str, session_id: str, events: list[dict]) -> Path:
    """Write a fake transcript under a projects slug and return its path."""
    folder = root / slug
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{session_id}.jsonl"
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n")
    return path


def write_agent(
    root: Path,
    slug: str,
    session_id: str,
    agent_id: str,
    events: list[dict],
    *,
    description: str = "Do the thing",
    agent_type: str = "general-purpose",
    tool_use_id: str | None = "toolu_agent1",
    spawn_depth: int = 1,
    parent_agent_id: str | None = None,
    model: str | None = "opus",
    stopped_by_user: bool = False,
    meta_mtime: float | None = None,
    jsonl_mtime: float | None = None,
) -> Path:
    """Write one fake subagent transcript plus its meta file."""
    folder = root / slug / session_id / "subagents"
    folder.mkdir(parents=True, exist_ok=True)
    meta: dict = {
        "agentType": agent_type,
        "description": description,
        "spawnDepth": spawn_depth,
    }
    if tool_use_id is not None:
        meta["toolUseId"] = tool_use_id
    if parent_agent_id is not None:
        meta["parentAgentId"] = parent_agent_id
    if model is not None:
        meta["model"] = model
    if stopped_by_user:
        meta["stoppedByUser"] = True

    meta_path = folder / f"agent-{agent_id}.meta.json"
    meta_path.write_text(json.dumps(meta))
    path = folder / f"agent-{agent_id}.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n" if events else "")
    if meta_mtime is not None:
        os.utime(meta_path, (meta_mtime, meta_mtime))
    if jsonl_mtime is not None:
        os.utime(path, (jsonl_mtime, jsonl_mtime))
    return path


def agent_assistant(text: str, model: str = "claude-opus-5") -> dict:
    """Build an agent transcript event whose assistant message names its model."""
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "model": model,
            "content": [{"type": "text", "text": text}],
        },
        "uuid": f"ag-{abs(hash(text)) % 10**8}",
    }


def assistant_text(text: str) -> dict:
    """Build an assistant transcript event that holds one text block."""
    return {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
        "uuid": f"a-{abs(hash(text)) % 10**8}",
    }


def assistant_tool(name: str, tool_input: dict, tool_id: str) -> dict:
    """Build an assistant transcript event that holds one tool_use block."""
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": tool_id, "name": name, "input": tool_input}
            ],
        },
        "uuid": f"a-{tool_id}",
    }


def tool_result(tool_id: str, content: str = "ok") -> dict:
    """Build a user transcript event that holds one tool_result block."""
    return {
        "type": "user",
        "message": {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": tool_id, "content": content}
            ],
        },
        "toolUseResult": content,
        "uuid": f"r-{tool_id}",
    }


def user_prompt(text: str) -> dict:
    """Build a user transcript event for something the human typed."""
    return {
        "type": "user",
        "message": {"role": "user", "content": text},
        "promptSource": "typed",
        "uuid": f"u-{abs(hash(text)) % 10**8}",
    }


@pytest.fixture
def claude_home(tmp_path: Path, monkeypatch) -> Path:
    """Point the records and projects modules at a throwaway ~/.claude."""
    home = tmp_path / "claude"
    (home / "sessions").mkdir(parents=True)
    (home / "projects").mkdir(parents=True)
    from cc_mirror import records

    monkeypatch.setattr(records, "SESSIONS_DIR", home / "sessions")
    monkeypatch.setattr(records, "PROJECTS_DIR", home / "projects")
    return home
