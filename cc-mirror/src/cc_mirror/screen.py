"""Render a tmux capture and mark the cell the cursor sits on."""

from __future__ import annotations

from rich.text import Text

from .tmux import Cursor

#: Style painted over the cursor cell.
CURSOR_STYLE = "reverse"

#: Ends any colour still open before padding spaces onto a short line.
_RESET = "\x1b[0m"


def prepare_text(capture: str, cursor: Cursor | None) -> tuple[Text, int | None]:
    """Parse a capture and give the plain-text offset of the cursor cell."""
    if cursor is None:
        return Text.from_ansi(capture), None

    raw_lines = capture.split("\n")
    plain_lines = Text.from_ansi(capture).plain.split("\n")
    # A capture can be shorter than the pane, so the cursor row may not exist.
    while len(plain_lines) <= cursor.y:
        plain_lines.append("")
    while len(raw_lines) <= cursor.y:
        raw_lines.append("")

    # The cursor often sits one cell past the end of its line.
    missing = cursor.x + 1 - len(plain_lines[cursor.y])
    if missing > 0:
        raw_lines[cursor.y] = raw_lines[cursor.y] + _RESET + " " * missing
        plain_lines[cursor.y] = plain_lines[cursor.y] + " " * missing

    offset = sum(len(line) + 1 for line in plain_lines[: cursor.y]) + cursor.x
    return Text.from_ansi("\n".join(raw_lines)), offset


def render_capture(
    capture: str,
    cursor: Cursor | None = None,
    show_cursor: bool = True,
) -> Text:
    """Render a capture, painting the cursor cell when it should show."""
    wanted = cursor if (cursor is not None and cursor.visible and show_cursor) else None
    text, offset = prepare_text(capture, wanted)
    if offset is not None:
        text.stylize(CURSOR_STYLE, offset, offset + 1)
    return text


def with_cursor(base: Text, offset: int | None) -> Text:
    """Copy an already parsed capture and paint the cursor cell on it."""
    if offset is None:
        return base
    text = base.copy()
    text.stylize(CURSOR_STYLE, offset, offset + 1)
    return text
