"""Run the cc-mirror dashboard over every live Claude Code session."""

from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.events import Click

from .messages import (
    AgentOpened,
    AgentsToggled,
    CenterClosed,
    JumpToWaiting,
    SessionFocused,
    SessionOpened,
)
from .model import Mirror, SessionState
from .widgets.center import CenterView
from .widgets.header import MirrorHeader
from .widgets.preview import PreviewStack
from .widgets.sidebar import AgentToggleRow, Sidebar

#: Seconds between record and transcript polls.
REFRESH_SECONDS = 1.0


class CCMirrorApp(App):
    """Show every Claude Code session and mirror one in the center view."""

    CSS_PATH = "app.tcss"
    TITLE = "cc-mirror"
    ENABLE_COMMAND_PALETTE = False
    # Textual's default "*" focuses the first focusable widget, which is the
    # hidden PaneMirror inside the closed center view -- and that swallows
    # every key. ensure_row_focus() puts the keyboard on a real row instead.
    AUTO_FOCUS = None

    BINDINGS = [
        Binding("q", "quit_dashboard", "Quit", show=True, priority=False),
        Binding("w", "next_waiting", "Next waiting", show=True),
        Binding("enter", "open_focused", "Open mirror", show=True),
        Binding("ctrl+backslash", "close_center", "Close mirror", show=True),
        # Overrides Textual's default priority ctrl+q quit. Ctrl+Q is the
        # second exit chord for the center view and does nothing elsewhere,
        # so `q` stays the only way to quit the dashboard.
        Binding("ctrl+q", "close_center", "Close mirror", show=False, priority=False),
        Binding("escape", "close_center", "Close mirror", show=False),
    ]

    def __init__(
        self,
        sessions_dir: Path | None = None,
        refresh_seconds: float = REFRESH_SECONDS,
        match_panes: bool = True,
        auto_poll: bool = True,
    ) -> None:
        super().__init__()
        self.mirror = Mirror(sessions_dir=sessions_dir, match_panes=match_panes)
        self.refresh_seconds = refresh_seconds
        self.auto_poll = auto_poll
        self.current_pid: int | None = None
        self.header_widget = MirrorHeader()
        self.sidebar = Sidebar()
        self.previews = PreviewStack()
        self.center = CenterView()
        self._waiting_cursor = -1

    def compose(self) -> ComposeResult:
        """Lay out the header, the sidebar, the preview stack, and the overlay."""
        yield self.header_widget
        with Horizontal(id="body"):
            yield self.sidebar
            yield self.previews
        yield self.center

    async def on_mount(self) -> None:
        """Load the first snapshot and start the 1 s refresh."""
        await self.refresh_sessions()
        if self.auto_poll:
            self.set_interval(self.refresh_seconds, self.refresh_sessions)

    async def refresh_sessions(self) -> None:
        """Re-read records and transcripts, then repaint the dashboard."""
        states = await asyncio.to_thread(self.mirror.poll)
        await self.apply(states)

    async def apply(self, states: list[SessionState]) -> None:
        """Push a fresh session list into every widget."""
        groups = self.mirror.grouped()
        await self.sidebar.sync(groups)
        await self.previews.sync(groups)
        self.header_widget.set_summary(
            self.mirror.header_text(), len(self.mirror.waiting)
        )
        pids = {state.record.pid for state in states}
        if self.current_pid not in pids:
            self.current_pid = states[0].record.pid if states else None
        self.sidebar.highlight(self.current_pid)
        self.ensure_row_focus()
        if self.center.is_open:
            if self.center_has_subject(pids):
                self.center.tick()
            else:
                self.center.close()

    def ensure_row_focus(self) -> None:
        """Put the keyboard on a row so the arrows work before any click."""
        if self.center.is_open:
            return
        focused = self.focused
        if focused is not None and focused not in (self.sidebar, self.previews):
            return
        box = self.previews.box_for(self.current_pid) if self.current_pid else None
        if box is not None:
            box.focus()

    def center_has_subject(self, pids: set[int]) -> bool:
        """Say whether the open center view still has something to show."""
        if self.center.agent_id is not None:
            # An agent view outlives its own pid; it ends with its session.
            return self.mirror.find_agent(self.center.agent_id) is not None
        return self.center.pid in pids

    # --- session focus and the center view -------------------------------

    def select(self, pid: int) -> None:
        """Make one session current and scroll it into view."""
        self.current_pid = pid
        self.sidebar.highlight(pid)
        box = self.previews.box_for(pid)
        if box is not None:
            self.previews.scroll_to_widget(box, animate=False)

    def open_center(self, pid: int) -> str | None:
        """Open the center view on one session."""
        state = self.mirror.find(pid)
        if state is None:
            return None
        self.select(pid)
        return self.center.open(state)

    def open_agent(self, agent_id: str) -> str | None:
        """Open the read-only transcript of one subagent."""
        agent = self.mirror.find_agent(agent_id)
        if agent is None:
            return None
        return self.center.open_agent(agent)

    def focused_pid(self) -> int | None:
        """Give the session the keyboard is on: focused widget, else current row."""
        focused = self.focused
        pid = getattr(focused, "pid", None)
        if isinstance(pid, int):
            return pid
        agent_id = getattr(focused, "agent_id", None)
        if isinstance(agent_id, str):
            owner = self.mirror.find_agent_session(agent_id)
            if owner is not None:
                return owner.record.pid
        return self.current_pid

    def nav_order(self) -> list:
        """List the focusable rows in the order the arrow keys walk them."""
        rows: list = []
        for _cwd, members in self.mirror.grouped():
            for state in members:
                box = self.previews.box_for(state.record.pid)
                if box is not None:
                    rows.append(box)
                if not (state.agents and self.sidebar.is_expanded(state.record.pid)):
                    continue
                for agent in state.agents:
                    row = self.sidebar.agent_row_for(agent.agent_id)
                    if row is not None:
                        rows.append(row)
        return rows

    def move_focus(self, delta: int) -> bool:
        """Step focus one row along the arrow-key sequence."""
        rows = self.nav_order()
        if not rows:
            return False
        focused = self.focused
        if focused in rows:
            index = rows.index(focused) + delta
        else:
            # Coming from a sidebar row or a toggle: anchor on that session.
            pid = self.focused_pid()
            anchor = self.previews.box_for(pid) if pid is not None else None
            index = rows.index(anchor) if anchor in rows else (
                0 if delta > 0 else len(rows) - 1
            )
        index = max(0, min(index, len(rows) - 1))
        target = rows[index]
        target.focus()
        target.scroll_visible(animate=False)
        pid = getattr(target, "pid", None)
        if isinstance(pid, int):
            self.select(pid)
        return True

    def on_session_focused(self, message: SessionFocused) -> None:
        """Handle a click on a preview box or a sidebar row."""
        message.stop()
        self.select(message.pid)

    def on_session_opened(self, message: SessionOpened) -> None:
        """Handle a double-click that opens the center view."""
        message.stop()
        self.open_center(message.pid)

    def on_agents_toggled(self, message: AgentsToggled) -> None:
        """Handle a click on an agent toggle row."""
        message.stop()
        self.toggle_agents(message.pid)

    def on_agent_opened(self, message: AgentOpened) -> None:
        """Handle a double-click on an agent row."""
        message.stop()
        self.open_agent(message.agent_id)

    def on_center_closed(self, message: CenterClosed) -> None:
        """Handle the exit chord sent from inside the mirror."""
        message.stop()
        self.action_close_center()

    def on_jump_to_waiting(self, message: JumpToWaiting) -> None:
        """Handle a header click."""
        message.stop()
        self.action_next_waiting()

    def on_click(self, event: Click) -> None:
        """Close the center view when a click lands outside its box."""
        if not self.center.is_open:
            return
        if self.center.region.contains(event.screen_x, event.screen_y):
            return
        self.action_close_center()

    # --- actions ----------------------------------------------------------

    def action_close_center(self) -> None:
        """Close the center view and give focus back to the preview stack."""
        if not self.center.is_open:
            return
        self.center.close()
        box = self.previews.box_for(self.current_pid) if self.current_pid else None
        if box is not None:
            box.focus()
        else:
            self.previews.focus()

    def action_open_focused(self) -> None:
        """Open whatever the keyboard is on: an agent, a tree, or a session."""
        if self.center.is_open:
            return
        focused = self.focused
        agent_id = getattr(focused, "agent_id", None)
        if isinstance(agent_id, str):
            self.open_agent(agent_id)
            return
        if isinstance(focused, AgentToggleRow):
            self.toggle_agents(focused.pid)
            return
        pid = self.focused_pid()
        if pid is None:
            return
        self.open_center(pid)

    def action_focus_next_row(self) -> None:
        """Move focus down one row."""
        self.move_focus(1)

    def action_focus_previous_row(self) -> None:
        """Move focus up one row."""
        self.move_focus(-1)

    def action_expand_agents(self) -> None:
        """Open the agent tree of the focused session."""
        pid = self.focused_pid()
        if pid is None:
            return
        state = self.mirror.find(pid)
        if state is None or not state.agents:
            return
        if not self.sidebar.is_expanded(pid):
            self.toggle_agents(pid)

    def action_collapse_agents(self) -> None:
        """Close the agent tree of the focused session, as a tree Left does."""
        pid = self.focused_pid()
        if pid is None:
            return
        if not self.sidebar.is_expanded(pid):
            return
        on_agent_row = isinstance(getattr(self.focused, "agent_id", None), str)
        self.toggle_agents(pid)
        if on_agent_row:
            # The row under the cursor is about to vanish; step up to its session.
            box = self.previews.box_for(pid)
            if box is not None:
                box.focus()
                self.select(pid)

    def toggle_agents(self, pid: int) -> None:
        """Expand or collapse one session's agent tree and repaint the sidebar."""
        self.sidebar.toggle(pid)
        self.call_next(self.refresh_sidebar)

    async def refresh_sidebar(self) -> None:
        """Rebuild the sidebar from the state already on screen."""
        await self.sidebar.sync(self.mirror.grouped())

    def action_next_waiting(self) -> None:
        """Move to the next session that needs a human."""
        waiting = self.mirror.waiting
        if not waiting:
            self.bell()
            return
        pids = [state.record.pid for state in waiting]
        if self.current_pid in pids:
            index = (pids.index(self.current_pid) + 1) % len(pids)
        else:
            index = 0
        self.select(pids[index])
        box = self.previews.box_for(pids[index])
        if box is not None:
            box.focus()

    def action_quit_dashboard(self) -> None:
        """Quit, but never while the center view is open."""
        if self.center.is_open:
            return
        self.exit()
