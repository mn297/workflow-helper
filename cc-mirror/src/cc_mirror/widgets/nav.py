"""Bind the arrow keys on every row the dashboard can focus."""

from __future__ import annotations

from textual.binding import Binding
from textual.css.query import NoMatches, WrongType

#: Arrow keys for a focusable row.
#:
#: These sit on the rows, not on the app. A key event reaches the focused
#: widget first, so a row binding beats the scroll bindings of the
#: VerticalScroll it lives in. App-level bindings would lose that race, and
#: priority bindings would steal the arrows from the live mirror.
NAV_BINDINGS = [
    Binding("up", "app.focus_previous_row", "Previous", show=False),
    Binding("down", "app.focus_next_row", "Next", show=False),
    Binding("left", "app.collapse_agents", "Collapse agents", show=False),
    Binding("right", "app.expand_agents", "Expand agents", show=False),
]


def focused_child_id(container) -> str | None:
    """Give the id of the container's own focused child, if it has one."""
    try:
        focused = container.app.focused
    except RuntimeError:  # NoActiveAppError: the container is not mounted yet
        return None
    if focused is None or focused.id is None:
        return None
    return focused.id if any(focused is child for child in container.children) else None


def restore_focus(container, widget_id: str | None) -> None:
    """Focus a rebuilt child by id, so a repaint never moves the keyboard."""
    if not widget_id:
        return
    try:
        # scroll_visible=False: the caller already restored the scroll offset,
        # and focusing must not drag the view somewhere else.
        container.query_one(f"#{widget_id}").focus(scroll_visible=False)
    except (NoMatches, WrongType):
        return
