"""Check the cursor overlay drawn on a rendered tmux capture."""

from __future__ import annotations

import pytest
from rich.text import Text

from cc_mirror.screen import CURSOR_STYLE, prepare_text, render_capture, with_cursor
from cc_mirror.tmux import Cursor, parse_cursor, split_capture
from cc_mirror.tmux import CURSOR_SENTINEL


def styled_at(text: Text, offset: int) -> bool:
    """Say whether the cursor style covers one character offset."""
    for span in text.spans:
        if span.start <= offset < span.end and CURSOR_STYLE in str(span.style):
            return True
    return False


class TestCursorOffset:
    """The cursor cell maps to the right plain-text offset."""

    def test_first_cell(self):
        _text, offset = prepare_text("abc\ndef", Cursor(0, 0))
        assert offset == 0

    def test_mid_first_line(self):
        _text, offset = prepare_text("abc\ndef", Cursor(2, 0))
        assert offset == 2

    def test_second_line(self):
        _text, offset = prepare_text("abc\ndef", Cursor(1, 1))
        assert offset == 5  # "abc\n" is 4 chars

    def test_third_line(self):
        _text, offset = prepare_text("ab\ncd\nef", Cursor(0, 2))
        assert offset == 6

    def test_offset_ignores_sgr_escapes(self):
        capture = "\x1b[36mabc\x1b[0m\ndef"
        text, offset = prepare_text(capture, Cursor(1, 1))
        assert text.plain.split("\n")[0] == "abc"
        assert offset == 5
        assert text.plain[offset] == "e"

    def test_no_cursor_gives_no_offset(self):
        text, offset = prepare_text("abc", None)
        assert offset is None
        assert text.plain == "abc"


class TestPastLineEnd:
    """A cursor past the end of its line gets a padded space to sit on."""

    def test_one_cell_past_the_end(self):
        text, offset = prepare_text("abc\ndef", Cursor(3, 0))
        assert offset == 3
        assert text.plain.split("\n")[0] == "abc "
        assert text.plain[offset] == " "

    def test_far_past_the_end(self):
        text, offset = prepare_text("ab", Cursor(6, 0))
        assert text.plain == "ab" + " " * 5
        assert offset == 6
        assert text.plain[offset] == " "

    def test_empty_line(self):
        text, offset = prepare_text("first\n\nthird", Cursor(2, 1))
        lines = text.plain.split("\n")
        assert lines[1] == "   "
        assert text.plain[offset] == " "

    def test_row_past_the_last_captured_line(self):
        text, offset = prepare_text("only one line", Cursor(2, 3))
        lines = text.plain.split("\n")
        assert len(lines) == 4
        assert text.plain[offset] == " "

    def test_padding_does_not_inherit_the_previous_colour(self):
        text, _offset = prepare_text("\x1b[41mred", Cursor(6, 0))
        # The reset before the padding keeps the red background off the spaces.
        assert text.plain == "red    "


class TestRenderCapture:
    """The rendered capture carries the cursor style on exactly one cell."""

    def test_cursor_cell_is_styled(self):
        text = render_capture("abc\ndef", Cursor(1, 1), show_cursor=True)
        assert styled_at(text, 5) is True
        assert styled_at(text, 4) is False
        assert styled_at(text, 6) is False

    def test_hidden_cursor_is_not_drawn(self):
        text = render_capture("abc", Cursor(1, 0, visible=False), show_cursor=True)
        assert styled_at(text, 1) is False

    def test_unfocused_view_draws_no_cursor(self):
        text = render_capture("abc", Cursor(1, 0), show_cursor=False)
        assert styled_at(text, 1) is False

    def test_no_cursor_reported(self):
        text = render_capture("abc", None, show_cursor=True)
        assert text.plain == "abc"
        assert not any(CURSOR_STYLE in str(s.style) for s in text.spans)

    def test_sgr_colours_survive_the_overlay(self):
        text = render_capture("\x1b[36mcyan text\x1b[0m", Cursor(0, 0))
        assert text.plain == "cyan text"
        assert styled_at(text, 0) is True


class TestWithCursor:
    """Blinking reuses the parsed capture instead of re-parsing it."""

    def test_on_phase_paints_the_cell(self):
        base, offset = prepare_text("abc", Cursor(1, 0))
        lit = with_cursor(base, offset)
        assert styled_at(lit, 1) is True

    def test_off_phase_returns_the_bare_capture(self):
        base, offset = prepare_text("abc", Cursor(1, 0))
        dark = with_cursor(base, None)
        assert styled_at(dark, 1) is False
        assert dark.plain == base.plain

    def test_the_base_text_is_never_mutated(self):
        base, offset = prepare_text("abc", Cursor(1, 0))
        before = len(base.spans)
        with_cursor(base, offset)
        with_cursor(base, offset)
        assert len(base.spans) == before


class TestCursorReport:
    """tmux cursor reports parse, and batched replies split cleanly."""

    def test_parse(self):
        assert parse_cursor("5,1,1") == Cursor(5, 1, True)
        assert parse_cursor("0,0,0") == Cursor(0, 0, False)
        assert parse_cursor(" 8,2,1 \n") == Cursor(8, 2, True)

    @pytest.mark.parametrize("bad", ["", "x,y,z", "1,2", "1,2,3,4", "-1,0,1"])
    def test_bad_reports(self, bad):
        assert parse_cursor(bad) is None

    def test_split_a_batched_reply(self):
        stdout = "line one\nline two\n" + CURSOR_SENTINEL + "8,1,1\n"
        capture, cursor = split_capture(stdout)
        assert capture == "line one\nline two"
        assert cursor == Cursor(8, 1, True)

    def test_split_keeps_blank_screen_lines(self):
        stdout = "a\n\n\n" + CURSOR_SENTINEL + "0,2,1\n"
        capture, cursor = split_capture(stdout)
        assert capture == "a\n\n"
        assert cursor.y == 2

    def test_split_without_a_sentinel(self):
        capture, cursor = split_capture("just a capture\n")
        assert capture == "just a capture\n"
        assert cursor is None
