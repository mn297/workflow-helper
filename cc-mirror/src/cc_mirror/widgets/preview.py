"""Stack one preview box per session and scroll through them."""

from __future__ import annotations

from pathlib import Path

from rich.text import Text
from textual.containers import VerticalScroll
from textual.css.query import NoMatches, WrongType
from textual.events import Click
from textual.widgets import Static

from ..messages import SessionFocused, SessionOpened
from ..model import CLASS_RO, SessionState
from ..records import STATUS_BUSY, STATUS_DEAD, STATUS_IDLE, STATUS_WAITING
from .nav import NAV_BINDINGS, focused_child_id, restore_focus

#: Status -> the word painted on the box border.
STATUS_LABEL = {
    STATUS_BUSY: "thinking",
    STATUS_WAITING: "HUMAN NEEDED",
    STATUS_IDLE: "idle",
    STATUS_DEAD: "dead",
}

#: Status -> the CSS class that colors the outline.
STATUS_CLASS = {
    STATUS_BUSY: "-busy",
    STATUS_WAITING: "-waiting",
    STATUS_IDLE: "-idle",
    STATUS_DEAD: "-dead",
}

#: Label kind -> Rich style for the preview line.
KIND_STYLE = {
    "pending": "bold orange1",
    "prompt": "bold",
    "tool": "",
    "text": "dim",
    "done": "green",
    "empty": "dim italic",
    "agent": "cyan",
}


def box_id(pid: int) -> str:
    """Give the widget id used for one session's preview box."""
    return f"preview-{pid}"


def shorten_path(cwd: str, home: str | None = None) -> str:
    """Write a working directory with ~ standing in for the home folder."""
    root = str(Path.home()) if home is None else home
    if cwd == root:
        return "~"
    if root and cwd.startswith(root + "/"):
        return "~" + cwd[len(root) :]
    return cwd


def fit_tail(text: str, width: int) -> str:
    """Cut a path from the left so its tail survives a narrow rule."""
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width == 1:
        return "…"
    return "…" + text[-(width - 1) :]


def rule_text(label: str, width: int, lead: int = 2) -> str:
    """Draw a horizontal rule with a folder path sitting at its left."""
    if width <= 0:
        return ""
    # Two dashes, a space either side of the label, then dashes to the edge.
    label = fit_tail(label, max(1, width - (lead + 2)))
    body = f"{'─' * lead} {label} "
    return (body + "─" * max(0, width - len(body)))[:width]


class GroupRule(Static):
    """Separate one folder's preview boxes from the next."""

    def __init__(self, cwd: str) -> None:
        super().__init__(classes="group-rule", markup=False)
        self.cwd = cwd
        self.label = shorten_path(cwd)

    def render(self) -> Text:
        """Redraw the rule at whatever width the stack currently has."""
        return Text(rule_text(self.label, self.size.width), style="dim")


class PreviewBox(Static, can_focus=True):
    """Show 3-5 semantic lines for one session and open it on double-click."""

    BINDINGS = NAV_BINDINGS

    def __init__(self, state: SessionState) -> None:
        super().__init__(id=box_id(state.record.pid))
        self.pid = state.record.pid
        self._signature: tuple | None = None
        self.sync(state)

    def sync(self, state: SessionState) -> None:
        """Repaint the box when its status, class, or lines changed."""
        status = state.record.display_status
        signature = (
            status,
            state.session_class,
            state.record.name,
            tuple((line.kind, line.text) for line in state.lines),
            tuple(line.text for line in state.agent_lines),
        )
        if signature == self._signature:
            return
        self._signature = signature
        self.status = status
        self.lines_text = [line.text for line in state.lines]
        self.agent_lines_text = [line.text for line in state.agent_lines]
        for css in STATUS_CLASS.values():
            self.remove_class(css)
        self.add_class(STATUS_CLASS.get(status, "-idle"))
        self.set_class(state.session_class == CLASS_RO, "-ro")
        self.border_title = state.title_markup
        self.border_subtitle = STATUS_LABEL.get(status, status)
        body = Text()
        for index, line in enumerate([*state.lines, *state.agent_lines]):
            if index:
                body.append("\n")
            body.append(line.text, style=KIND_STYLE.get(line.kind, ""))
        self.update(body)

    def on_click(self, event: Click) -> None:
        """Focus on a single click, open the center view on a double-click."""
        event.stop()
        self.focus()
        if event.chain >= 2:
            self.post_message(SessionOpened(self.pid))
        else:
            self.post_message(SessionFocused(self.pid))


class PreviewStack(VerticalScroll):
    """Stack every session preview box, grouped by folder like the sidebar."""

    # Focus belongs to the boxes, not the viewport; see Sidebar.can_focus.
    can_focus = False

    def __init__(self) -> None:
        super().__init__(id="previews")
        self._shape: tuple = ()

    async def sync(self, groups: list[tuple[str, list[SessionState]]]) -> None:
        """Add, drop, and refresh preview boxes to match the session list."""
        shape = tuple(
            (cwd, tuple(state.record.pid for state in members))
            for cwd, members in groups
        )
        if shape != self._shape:
            self._shape = shape
            scroll_y = self.scroll_offset.y
            keep_focus = focused_child_id(self)
            await self.remove_children()
            widgets: list[Static] = []
            for cwd, members in groups:
                widgets.append(GroupRule(cwd))
                widgets.extend(PreviewBox(state) for state in members)
            await self.mount_all(widgets)
            self.scroll_to(y=scroll_y, animate=False)
            restore_focus(self, keep_focus)
            return
        for _cwd, members in groups:
            for state in members:
                box = self.box_for(state.record.pid)
                if box is not None:
                    box.sync(state)

    def box_for(self, pid: int) -> PreviewBox | None:
        """Find the preview box of one session, if it is mounted."""
        try:
            return self.query_one(f"#{box_id(pid)}", PreviewBox)
        except (NoMatches, WrongType):
            return None
