"""Read the subagents a session spawned and say which still run."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from .records import SessionRecord

#: An unresolved agent whose transcript stopped growing this long ago is stalled.
STALLED_AFTER_SECONDS = 120.0

STATE_RUNNING = "running"
STATE_DONE = "done"
STATE_STALLED = "stalled"
STATE_STOPPED = "stopped"

#: Short model names, longest first so "sonnet" never loses to a shorter match.
MODEL_NAMES = ("sonnet", "haiku", "opus", "fable")

#: State -> the glyph the sidebar paints in front of an agent row.
STATE_GLYPH = {
    STATE_RUNNING: "⚙",
    STATE_DONE: "✓",
    STATE_STALLED: "…",
    STATE_STOPPED: "■",
}


def model_short_name(value: object) -> str:
    """Shorten a model id to opus, sonnet, haiku, or fable."""
    if not value:
        return ""
    lowered = str(value).lower()
    for name in MODEL_NAMES:
        if name in lowered:
            return name
    return ""


def subagents_dir(record: SessionRecord) -> Path:
    """Give the subagents folder of a session, whether or not it exists."""
    return record.transcript_path.with_suffix("") / "subagents"


@dataclass(frozen=True)
class AgentRecord:
    """Hold one subagent transcript and the state read from its parent."""

    agent_id: str
    path: Path
    description: str
    agent_type: str
    tool_use_id: str
    spawn_depth: int
    parent_agent_id: str
    model: str
    state: str
    mtime: float
    sort_stamp: float

    @property
    def glyph(self) -> str:
        """Give the state glyph for this agent."""
        return STATE_GLYPH.get(self.state, "?")

    @property
    def is_running(self) -> bool:
        """Say whether this agent is still working."""
        return self.state == STATE_RUNNING

    @property
    def indent(self) -> str:
        """Give the sidebar indent that shows how deep the agent was spawned."""
        return "  " * max(0, self.spawn_depth - 1)

    @property
    def title(self) -> str:
        """Give the center-view title for this agent's transcript."""
        model = f" · {self.model}" if self.model else ""
        return f"{self.description}{model}"


def parse_meta(data: dict) -> dict:
    """Pull the fields cc-mirror uses out of one agent meta file."""
    return {
        "description": str(data.get("description") or "").strip(),
        "agent_type": str(data.get("agentType") or ""),
        "tool_use_id": str(data.get("toolUseId") or ""),
        "spawn_depth": int(data.get("spawnDepth") or 1),
        "parent_agent_id": str(data.get("parentAgentId") or ""),
        "model": model_short_name(data.get("model")),
        "stopped_by_user": bool(data.get("stoppedByUser")),
    }


def read_resolved_tool_ids(path: Path) -> set[str]:
    """Collect every tool_use_id that already has a result in a transcript."""
    out: set[str] = set()
    try:
        with path.open("r", errors="replace") as handle:
            for line in handle:
                if '"tool_result"' not in line:
                    continue
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get("type") != "user":
                    continue
                content = event.get("message", {}).get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        tool_id = block.get("tool_use_id")
                        if isinstance(tool_id, str):
                            out.add(tool_id)
    except OSError:
        return out
    return out


def read_model_from_transcript(path: Path) -> str:
    """Read the model an agent ran on from the head of its transcript."""
    try:
        with path.open("r", errors="replace") as handle:
            for line in handle:
                if '"model"' not in line:
                    continue
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get("type") != "assistant":
                    continue
                name = model_short_name(event.get("message", {}).get("model"))
                if name:
                    return name
    except OSError:
        return ""
    return ""


class AgentStore:
    """Track every session's subagents and keep their state across polls."""

    def __init__(self, stalled_after: float = STALLED_AFTER_SECONDS) -> None:
        self.stalled_after = stalled_after
        self._meta: dict[str, tuple[float, dict]] = {}
        self._resolved: dict[str, tuple[float, set[str]]] = {}
        self._model: dict[str, str] = {}
        self._sort_stamp: dict[str, float] = {}
        self._done: set[str] = set()

    def _meta_for(self, meta_path: Path) -> dict | None:
        """Read one agent meta file, reusing the last parse when unchanged."""
        key = str(meta_path)
        try:
            mtime = meta_path.stat().st_mtime
        except OSError:
            return None
        cached = self._meta.get(key)
        if cached is not None and cached[0] == mtime:
            return cached[1]
        try:
            data = json.loads(meta_path.read_text(errors="replace"))
        except (OSError, ValueError):
            return None
        if not isinstance(data, dict):
            return None
        parsed = parse_meta(data)
        self._meta[key] = (mtime, parsed)
        self._sort_stamp.setdefault(key, mtime)
        return parsed

    def _resolved_for(self, path: Path) -> set[str]:
        """Collect resolved tool ids from a transcript, cached on its mtime."""
        key = str(path)
        try:
            mtime = path.stat().st_mtime
        except OSError:
            return set()
        cached = self._resolved.get(key)
        if cached is not None and cached[0] == mtime:
            return cached[1]
        ids = read_resolved_tool_ids(path)
        self._resolved[key] = (mtime, ids)
        return ids

    def _model_for(self, agent_id: str, path: Path, from_meta: str) -> str:
        """Give the agent's model, falling back to its transcript once."""
        if from_meta:
            return from_meta
        if agent_id in self._model:
            return self._model[agent_id]
        name = read_model_from_transcript(path)
        self._model[agent_id] = name
        return name

    def poll(self, record: SessionRecord, now: float | None = None) -> list[AgentRecord]:
        """List a session's subagents in spawn order, with current state."""
        now = time.time() if now is None else now
        folder = subagents_dir(record)
        if not folder.is_dir():
            return []
        try:
            metas = sorted(folder.glob("agent-*.meta.json"))
        except OSError:
            return []
        if not metas:
            return []

        parent_ids = self._resolved_for(record.transcript_path)
        agents: list[AgentRecord] = []
        for meta_path in metas:
            parsed = self._meta_for(meta_path)
            if parsed is None:
                continue
            agent_id = meta_path.name[len("agent-") : -len(".meta.json")]
            path = meta_path.with_name(f"agent-{agent_id}.jsonl")
            try:
                mtime = path.stat().st_mtime
            except OSError:
                mtime = 0.0

            resolved = parent_ids
            if parsed["parent_agent_id"]:
                parent_path = meta_path.with_name(
                    f"agent-{parsed['parent_agent_id']}.jsonl"
                )
                resolved = self._resolved_for(parent_path)

            state = self._state_for(agent_id, parsed, resolved, mtime, now)
            agents.append(
                AgentRecord(
                    agent_id=agent_id,
                    path=path,
                    description=parsed["description"] or parsed["agent_type"] or agent_id,
                    agent_type=parsed["agent_type"],
                    tool_use_id=parsed["tool_use_id"],
                    spawn_depth=parsed["spawn_depth"],
                    parent_agent_id=parsed["parent_agent_id"],
                    model=self._model_for(agent_id, path, parsed["model"]),
                    state=state,
                    mtime=mtime,
                    sort_stamp=self._sort_stamp.get(str(meta_path), mtime),
                )
            )
        agents.sort(key=lambda a: (a.sort_stamp, a.agent_id))
        return agents

    def _state_for(
        self,
        agent_id: str,
        parsed: dict,
        resolved: set[str],
        mtime: float,
        now: float,
    ) -> str:
        """Decide whether an agent runs, finished, stalled, or was stopped."""
        tool_id = parsed["tool_use_id"]
        if agent_id in self._done or (tool_id and tool_id in resolved):
            self._done.add(agent_id)
            return STATE_DONE
        if parsed["stopped_by_user"]:
            return STATE_STOPPED
        if not tool_id:
            # No toolUseId means nothing can ever resolve it; never call it running.
            return STATE_STALLED
        if now - mtime <= self.stalled_after:
            return STATE_RUNNING
        return STATE_STALLED
