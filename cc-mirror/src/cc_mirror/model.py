"""Join session records, transcript labels, and tmux panes."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from . import labels as labels_mod
from . import tmux as tmux_mod
from . import transcript as transcript_mod
from .agents import AgentRecord, AgentStore
from .records import STATUS_WAITING, RecordStore, SessionRecord
from .tmux import Pane

CLASS_TMUX = "tmux"
CLASS_RO = "ro"

#: Bytes read from the end of an agent transcript for its one preview line.
AGENT_TAIL_BYTES = 65_536


@dataclass
class SessionState:
    """Hold everything cc-mirror shows about one session."""

    record: SessionRecord
    lines: list[labels_mod.Label] = field(default_factory=list)
    pane: Pane | None = None
    agents: list[AgentRecord] = field(default_factory=list)
    agent_lines: list[labels_mod.Label] = field(default_factory=list)

    @property
    def running_agents(self) -> list[AgentRecord]:
        """List the subagents of this session that still work."""
        return [agent for agent in self.agents if agent.is_running]

    @property
    def agent_summary(self) -> str:
        """Give the sidebar toggle text, such as `2 agents · 1 running`."""
        total = len(self.agents)
        running = len(self.running_agents)
        noun = "agent" if total == 1 else "agents"
        if running:
            return f"{total} {noun} · {running} running"
        return f"{total} {noun}"

    @property
    def session_class(self) -> str:
        """Say whether the session is mirrorable ([tmux]) or read-only ([ro])."""
        return CLASS_TMUX if self.pane is not None else CLASS_RO

    @property
    def title(self) -> str:
        """Give the box title: session name plus its class tag."""
        return f"{self.record.name} [{self.session_class}]"

    @property
    def title_markup(self) -> str:
        """Give the box title with its class tag safe from Rich markup."""
        return f"{self.record.name} \\[{self.session_class}]"


class Mirror:
    """Poll records and transcripts and hand back current session state."""

    def __init__(
        self,
        sessions_dir: Path | None = None,
        grace_seconds: float = 60.0,
        match_panes: bool = True,
    ) -> None:
        self.store = RecordStore(sessions_dir, grace_seconds=grace_seconds)
        self.agent_store = AgentStore()
        self.match_panes = match_panes
        self._label_cache: dict[str, tuple[float, str, list[labels_mod.Label]]] = {}
        self._agent_line_cache: dict[str, tuple[float, labels_mod.Label]] = {}
        self.states: list[SessionState] = []

    def poll(self, now: float | None = None) -> list[SessionState]:
        """Re-read every record and rebuild the session state list."""
        now = time.time() if now is None else now
        records = self.store.poll(now)
        panes: dict[int, Pane] = {}
        if self.match_panes and records and tmux_mod.tmux_available():
            panes = tmux_mod.pane_map([r.pid for r in records if r.alive])
        states = []
        for record in records:
            agents = self.agent_store.poll(record, now)
            states.append(
                SessionState(
                    record=record,
                    lines=self._lines_for(record),
                    pane=panes.get(record.pid),
                    agents=agents,
                    agent_lines=[
                        self._agent_line(agent)
                        for agent in agents
                        if agent.is_running
                    ],
                )
            )
        self.states = states
        return states

    def _agent_line(self, agent: AgentRecord) -> labels_mod.Label:
        """Build the one preview line a running agent contributes."""
        mtime = transcript_mod.transcript_mtime(agent.path)
        cached = self._agent_line_cache.get(agent.agent_id)
        if cached is not None and cached[0] == mtime:
            return cached[1]
        events = transcript_mod.read_tail_lines(agent.path, AGENT_TAIL_BYTES)
        label = labels_mod.last_label(events)
        detail = label.text if label is not None else agent.description
        model = f"{agent.model}: " if agent.model else ""
        line = labels_mod.Label(
            "agent", labels_mod.clip(f"{agent.glyph} {model}{detail}")
        )
        self._agent_line_cache[agent.agent_id] = (mtime, line)
        return line

    def find_agent(self, agent_id: str) -> AgentRecord | None:
        """Find one subagent across every session on screen."""
        for state in self.states:
            for agent in state.agents:
                if agent.agent_id == agent_id:
                    return agent
        return None

    def find_agent_session(self, agent_id: str) -> SessionState | None:
        """Find the session that spawned one subagent."""
        for state in self.states:
            for agent in state.agents:
                if agent.agent_id == agent_id:
                    return state
        return None

    def _lines_for(self, record: SessionRecord) -> list[labels_mod.Label]:
        """Build the preview lines for a record, reusing the last result."""
        path = record.transcript_path
        mtime = transcript_mod.transcript_mtime(path)
        cached = self._label_cache.get(record.session_id)
        stamp = record.display_status
        if cached is not None and cached[0] == mtime and cached[1] == stamp:
            return cached[2]
        events = transcript_mod.read_tail_lines(path)
        lines = labels_mod.preview_lines(record, events)
        self._label_cache[record.session_id] = (mtime, stamp, lines)
        return lines

    def grouped(self) -> list[tuple[str, list[SessionState]]]:
        """Group current state by cwd: groups alphabetical, sessions by start."""
        groups: dict[str, list[SessionState]] = {}
        for state in self.states:
            groups.setdefault(state.record.cwd, []).append(state)
        out = []
        for cwd in sorted(groups):
            members = sorted(
                groups[cwd], key=lambda s: (s.record.started_at, s.record.pid)
            )
            out.append((cwd, members))
        return out

    @property
    def waiting(self) -> list[SessionState]:
        """List the sessions that need a human, in sidebar order."""
        return [s for s in self.states if s.record.display_status == STATUS_WAITING]

    def header_text(self) -> str:
        """Give the header summary: N sessions, M waiting."""
        total = len(self.states)
        waiting = len(self.waiting)
        noun = "session" if total == 1 else "sessions"
        return f"{total} {noun} · {waiting} waiting"

    def find(self, pid: int) -> SessionState | None:
        """Find current state by pid."""
        for state in self.states:
            if state.record.pid == pid:
                return state
        return None
