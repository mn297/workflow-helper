"""List every session in the sidebar, grouped by working directory."""

from __future__ import annotations

from pathlib import Path

from rich.text import Text
from textual.containers import VerticalScroll
from textual.css.query import NoMatches, WrongType
from textual.events import Click
from textual.widgets import Static

from ..agents import (
    STATE_DONE,
    STATE_RUNNING,
    STATE_STALLED,
    STATE_STOPPED,
    AgentRecord,
)
from ..messages import AgentOpened, AgentsToggled, SessionFocused, SessionOpened
from ..model import CLASS_RO, SessionState
from ..records import STATUS_BUSY, STATUS_DEAD, STATUS_IDLE, STATUS_WAITING
from .nav import NAV_BINDINGS, focused_child_id, restore_focus

#: Status -> the word shown beside the dot in the sidebar.
ROW_LABEL = {
    STATUS_BUSY: "busy",
    STATUS_WAITING: "WAITING",
    STATUS_IDLE: "idle",
    STATUS_DEAD: "dead",
}

#: Status -> the dot color of the sidebar row.
ROW_STYLE = {
    STATUS_BUSY: "cyan",
    STATUS_WAITING: "bold orange1",
    STATUS_IDLE: "dim",
    STATUS_DEAD: "#555555",
}


#: Agent state -> the style of its sidebar row.
AGENT_STYLE = {
    STATE_RUNNING: "cyan",
    STATE_DONE: "dim",
    STATE_STALLED: "yellow",
    STATE_STOPPED: "#8a8a8a",
}


def row_id(pid: int) -> str:
    """Give the widget id used for one session's sidebar row."""
    return f"row-{pid}"


def toggle_id(pid: int) -> str:
    """Give the widget id used for one session's agent toggle row."""
    return f"agents-{pid}"


def agent_row_id(agent_id: str) -> str:
    """Give the widget id used for one subagent row."""
    return f"agent-{agent_id}"


class GroupHeading(Static):
    """Name one working directory above its sessions."""

    def __init__(self, cwd: str) -> None:
        label = Path(cwd).name or cwd
        super().__init__(Text(label, style="bold"), classes="group-heading")
        self.cwd = cwd
        self.label = label
        self.tooltip = cwd


class SessionRow(Static, can_focus=True):
    """Show one session line and select it on click."""

    BINDINGS = NAV_BINDINGS

    def __init__(self, state: SessionState) -> None:
        super().__init__(id=row_id(state.record.pid), classes="session-row")
        self.pid = state.record.pid
        self._signature: tuple | None = None
        self.sync(state)

    def sync(self, state: SessionState) -> None:
        """Repaint the row when its status or class changed."""
        status = state.record.display_status
        signature = (status, state.session_class, state.record.short_id)
        if signature == self._signature:
            return
        self._signature = signature
        self.set_class(status == STATUS_WAITING, "-waiting")
        self.set_class(status == STATUS_DEAD, "-dead")
        style = ROW_STYLE.get(status, "")
        text = Text()
        text.append(" ● ", style=style)
        text.append(f"{state.record.short_id:<4} ", style=style)
        text.append(ROW_LABEL.get(status, status), style=style)
        if state.session_class == CLASS_RO:
            text.append(" [ro]", style="dim")
        self.update(text)

    def on_click(self, event: Click) -> None:
        """Focus the session, or open it on a double-click."""
        event.stop()
        self.focus()
        if event.chain >= 2:
            self.post_message(SessionOpened(self.pid))
        else:
            self.post_message(SessionFocused(self.pid))


class AgentToggleRow(Static, can_focus=True):
    """Open and close one session's agent tree."""

    BINDINGS = NAV_BINDINGS

    def __init__(self, state: SessionState, expanded: bool) -> None:
        super().__init__(id=toggle_id(state.record.pid), classes="agent-toggle")
        self.pid = state.record.pid
        self._signature: tuple | None = None
        self.sync(state, expanded)

    def sync(self, state: SessionState, expanded: bool) -> None:
        """Repaint the toggle when the agent counts or the arrow changed."""
        summary = state.agent_summary
        signature = (summary, expanded)
        if signature == self._signature:
            return
        self._signature = signature
        self.expanded = expanded
        self.summary = summary
        self.set_class(expanded, "-expanded")
        text = Text()
        text.append(f" {'▾' if expanded else '▸'} ", style="dim")
        style = "cyan" if state.running_agents else "dim"
        text.append(summary, style=style)
        self.update(text)

    def on_click(self, event: Click) -> None:
        """Toggle the tree on a click."""
        event.stop()
        self.focus()
        self.post_message(AgentsToggled(self.pid))


class AgentRow(Static, can_focus=True):
    """Show one subagent, indented by how deep it was spawned."""

    BINDINGS = NAV_BINDINGS

    def __init__(self, agent: AgentRecord) -> None:
        super().__init__(id=agent_row_id(agent.agent_id), classes="agent-row")
        self.agent_id = agent.agent_id
        self._signature: tuple | None = None
        self.sync(agent)

    def sync(self, agent: AgentRecord) -> None:
        """Repaint the row when the agent's state or model changed."""
        signature = (agent.state, agent.model, agent.description, agent.spawn_depth)
        if signature == self._signature:
            return
        self._signature = signature
        self.state = agent.state
        self.model = agent.model
        for name in ("-running", "-done", "-stalled", "-stopped"):
            self.remove_class(name)
        self.add_class(f"-{agent.state}")
        style = AGENT_STYLE.get(agent.state, "")
        text = Text()
        text.append(f" {agent.indent}{agent.glyph} ", style=style)
        if agent.model:
            text.append(f"{agent.model} ", style="magenta" if agent.is_running else "dim")
        text.append(agent.description, style=style)
        self.update(text)

    def on_click(self, event: Click) -> None:
        """Focus the agent, or open its transcript on a double-click."""
        event.stop()
        self.focus()
        if event.chain >= 2:
            self.post_message(AgentOpened(self.agent_id))


class Sidebar(VerticalScroll):
    """Group every session row by working directory, in stable order."""

    # The viewport itself must never hold focus, or it would swallow the
    # arrow keys with its own scroll bindings before a row could see them.
    can_focus = False

    def __init__(self) -> None:
        super().__init__(id="sidebar")
        self._shape: tuple = ()
        #: Pids whose agent tree the user opened. Survives every rebuild.
        self.expanded: set[int] = set()

    def is_expanded(self, pid: int) -> bool:
        """Say whether one session's agent tree is open."""
        return pid in self.expanded

    def toggle(self, pid: int) -> bool:
        """Open or close one session's agent tree and report the new state."""
        if pid in self.expanded:
            self.expanded.discard(pid)
            return False
        self.expanded.add(pid)
        return True

    def _shape_of(self, groups: list[tuple[str, list[SessionState]]]) -> tuple:
        """Describe the rows the sidebar needs, so a rebuild happens only then."""
        return tuple(
            (
                cwd,
                tuple(
                    (
                        state.record.pid,
                        bool(state.agents),
                        self.is_expanded(state.record.pid),
                        tuple(a.agent_id for a in state.agents)
                        if self.is_expanded(state.record.pid)
                        else (),
                    )
                    for state in members
                ),
            )
            for cwd, members in groups
        )

    def _build(self, groups: list[tuple[str, list[SessionState]]]) -> list[Static]:
        """Build every sidebar row, agent trees included."""
        widgets: list[Static] = []
        for cwd, members in groups:
            widgets.append(GroupHeading(cwd))
            for state in members:
                widgets.append(SessionRow(state))
                if not state.agents:
                    continue
                expanded = self.is_expanded(state.record.pid)
                widgets.append(AgentToggleRow(state, expanded))
                if expanded:
                    widgets.extend(AgentRow(agent) for agent in state.agents)
        return widgets

    async def sync(self, groups: list[tuple[str, list[SessionState]]]) -> None:
        """Rebuild the rows only when the set of sessions or agents changed."""
        shape = self._shape_of(groups)
        if shape != self._shape:
            self._shape = shape
            scroll_y = self.scroll_offset.y
            keep_focus = focused_child_id(self)
            await self.remove_children()
            await self.mount_all(self._build(groups))
            self.scroll_to(y=scroll_y, animate=False)
            restore_focus(self, keep_focus)
            return
        for _cwd, members in groups:
            for state in members:
                row = self.row_for(state.record.pid)
                if row is not None:
                    row.sync(state)
                toggle = self.toggle_for(state.record.pid)
                if toggle is not None:
                    toggle.sync(state, self.is_expanded(state.record.pid))
                for agent in state.agents:
                    agent_row = self.agent_row_for(agent.agent_id)
                    if agent_row is not None:
                        agent_row.sync(agent)

    def row_for(self, pid: int) -> SessionRow | None:
        """Find the sidebar row of one session, if it is mounted."""
        try:
            return self.query_one(f"#{row_id(pid)}", SessionRow)
        except (NoMatches, WrongType):
            return None

    def toggle_for(self, pid: int) -> AgentToggleRow | None:
        """Find the agent toggle of one session, if it is mounted."""
        try:
            return self.query_one(f"#{toggle_id(pid)}", AgentToggleRow)
        except (NoMatches, WrongType):
            return None

    def agent_row_for(self, agent_id: str) -> AgentRow | None:
        """Find one subagent row, if it is mounted."""
        try:
            return self.query_one(f"#{agent_row_id(agent_id)}", AgentRow)
        except (NoMatches, WrongType):
            return None

    def highlight(self, pid: int | None) -> None:
        """Mark one row as the current session."""
        for row in self.query(SessionRow):
            row.set_class(row.pid == pid, "-current")
