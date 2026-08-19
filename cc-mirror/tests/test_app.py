"""Drive the Textual dashboard with Pilot and check what it shows."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from cc_mirror import tmux as tmux_mod
from cc_mirror.app import CCMirrorApp
from cc_mirror.model import CLASS_RO, CLASS_TMUX
from cc_mirror.tmux import Cursor, Pane
from cc_mirror.widgets.center import BLINK_TICKS, PaneMirror, TranscriptView
from cc_mirror.widgets.preview import (
    GroupRule,
    PreviewBox,
    fit_tail,
    rule_text,
    shorten_path,
)
from cc_mirror.widgets.sidebar import AgentRow, AgentToggleRow, GroupHeading, SessionRow

from .conftest import (
    SESSION_ID_BUSY,
    SESSION_ID_IDLE,
    SESSION_ID_WAIT,
    agent_assistant,
    assistant_text,
    assistant_tool,
    screen_text,
    tool_result,
    user_prompt,
    write_agent,
    write_record,
    write_transcript,
)

ALIVE = os.getpid()

CWD_ALPHA = "/home/john/alpha"
CWD_ZETA = "/home/john/zeta_proj"


@pytest.fixture
def fixture_home(claude_home: Path) -> Path:
    """Write three fake sessions: one waiting, one busy, one idle."""
    sessions = claude_home / "sessions"
    projects = claude_home / "projects"

    write_record(sessions, pid=ALIVE, name="alpha-c3", cwd=CWD_ALPHA,
                 status="waiting", session_id=SESSION_ID_WAIT,
                 started_at=1_000_000, waiting_for="input needed")
    write_record(sessions, pid=1, name="zeta-e3", cwd=CWD_ZETA,
                 status="busy", session_id=SESSION_ID_BUSY, started_at=1_000_100)
    write_record(sessions, pid=2, name="zeta-fb", cwd=CWD_ZETA,
                 status="idle", session_id=SESSION_ID_IDLE, started_at=1_000_200)

    write_transcript(projects, "-home-john-alpha", SESSION_ID_WAIT, [
        user_prompt("run the suite"),
        assistant_text("Running the suite."),
        assistant_tool("Bash", {"command": "pytest"}, "t1"),
    ])
    write_transcript(projects, "-home-john-zeta-proj", SESSION_ID_BUSY, [
        user_prompt("fix the fusion bug"),
        assistant_tool("Edit", {"file_path": "/a/model.py"}, "t2"),
        tool_result("t2"),
        assistant_tool("Bash", {"command": "pytest -k fusion"}, "t3"),
    ])
    write_transcript(projects, "-home-john-zeta-proj", SESSION_ID_IDLE, [
        assistant_tool("Bash", {"command": "git status"}, "t4"),
        tool_result("t4"),
        assistant_text("refactor complete"),
    ])
    return claude_home


def make_app(home: Path, **kwargs) -> CCMirrorApp:
    """Build a dashboard bound to the fixture home, with polling off."""
    kwargs.setdefault("match_panes", False)
    kwargs.setdefault("auto_poll", False)
    return CCMirrorApp(sessions_dir=home / "sessions", **kwargs)


class TestSidebar:
    """The sidebar groups sessions by folder in a stable order."""

    async def test_groups_and_rows_render(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            headings = [h.label for h in app.query(GroupHeading)]
            assert headings == ["alpha", "zeta_proj"]
            rows = [r.pid for r in app.query(SessionRow)]
            assert rows == [ALIVE, 1, 2]

    async def test_group_labels_appear_on_screen(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            text = screen_text(app)
            assert "alpha" in text
            assert "zeta_proj" in text
            assert "WAITING" in text

    async def test_order_holds_when_status_changes(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            before = [r.pid for r in app.query(SessionRow)]
            write_record(fixture_home / "sessions", pid=2, name="zeta-fb",
                         cwd=CWD_ZETA, status="waiting",
                         session_id=SESSION_ID_IDLE, started_at=1_000_200)
            await app.refresh_sessions()
            await pilot.pause()
            assert [r.pid for r in app.query(SessionRow)] == before


class TestPreviewStack:
    """Every session gets one preview box with its semantic lines."""

    async def test_one_box_per_session(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            boxes = list(app.query(PreviewBox))
            assert [b.pid for b in boxes] == [ALIVE, 1, 2]

    async def test_boxes_hold_semantic_lines(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            busy = app.previews.box_for(1)
            assert "Editing model.py…" in busy.lines_text
            assert "Bash(pytest -k fusion)" in busy.lines_text
            idle = app.previews.box_for(2)
            assert idle.lines_text[-1] == "Done: refactor complete"

    async def test_lines_reach_the_screen(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            text = screen_text(app)
            assert "Approve: Bash(pytest)?" in text
            assert "Editing model.py" in text

    async def test_line_count_stays_in_range(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            for box in app.query(PreviewBox):
                assert 1 <= len(box.lines_text) <= 5


class TestGroupRuleText:
    """The delimiter shortens the home folder and keeps the path tail."""

    def test_home_becomes_a_tilde(self):
        assert shorten_path("/home/john/tree_perception", "/home/john") == "~/tree_perception"
        assert shorten_path("/home/john", "/home/john") == "~"

    def test_a_path_outside_home_is_untouched(self):
        assert shorten_path("/opt/work/proj", "/home/john") == "/opt/work/proj"
        assert shorten_path("/home/johnny/proj", "/home/john") == "/home/johnny/proj"

    def test_fit_tail_keeps_the_end(self):
        assert fit_tail("~/a/b/c", 20) == "~/a/b/c"
        assert fit_tail("~/very/long/path/here", 10) == "…path/here"
        assert len(fit_tail("~/very/long/path/here", 10)) == 10
        assert fit_tail("abc", 1) == "…"
        assert fit_tail("abc", 0) == ""

    def test_rule_fills_the_width(self):
        rule = rule_text("~/proj", 30)
        assert len(rule) == 30
        assert rule.startswith("── ~/proj ")
        assert rule.endswith("─")

    def test_rule_shrinks_and_the_path_wins(self):
        rule = rule_text("~/very/long/project/path", 16)
        assert len(rule) == 16
        assert "…" in rule
        assert rule.rstrip("─").endswith("path ")

    def test_rule_at_a_silly_width(self):
        assert rule_text("~/proj", 0) == ""
        assert len(rule_text("~/proj", 3)) == 3


class TestPreviewGrouping:
    """The preview stack groups by folder exactly like the sidebar."""

    async def test_one_rule_per_group_in_sidebar_order(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            rules = list(app.query(GroupRule))
            assert [r.cwd for r in rules] == [CWD_ALPHA, CWD_ZETA]
            headings = [h.cwd for h in app.query(GroupHeading)]
            assert [r.cwd for r in rules] == headings

    async def test_boxes_sit_under_their_own_rule(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            kinds = [
                (type(w).__name__, getattr(w, "cwd", getattr(w, "pid", None)))
                for w in app.previews.children
            ]
            assert kinds == [
                ("GroupRule", CWD_ALPHA),
                ("PreviewBox", ALIVE),
                ("GroupRule", CWD_ZETA),
                ("PreviewBox", 1),
                ("PreviewBox", 2),
            ]

    async def test_the_rule_shows_the_shortened_path(self, fixture_home, monkeypatch):
        monkeypatch.setenv("HOME", "/home/john")
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            text = screen_text(app)
            assert "── ~/alpha ─" in text
            assert "── ~/zeta_proj ─" in text

    async def test_delimiters_are_not_focusable(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            rules = list(app.query(GroupRule))
            assert rules
            assert all(r.can_focus is False for r in rules)
            seen = []
            for _ in range(12):
                app.screen.focus_next()
                await pilot.pause()
                seen.append(app.focused)
            assert not any(isinstance(w, GroupRule) for w in seen)
            assert any(isinstance(w, PreviewBox) for w in seen)

    async def test_a_click_on_a_delimiter_selects_nothing(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.select(2)
            rule = next(iter(app.query(GroupRule)))
            await pilot.click(rule)
            await pilot.pause()
            assert app.current_pid == 2
            assert app.center.is_open is False

    async def test_a_new_group_appears_in_order(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            write_record(fixture_home / "sessions", pid=3, name="beta-11",
                         cwd="/home/john/beta", status="busy",
                         session_id="55555555-5555-4555-8555-555555555555",
                         started_at=1_000_400)
            await app.refresh_sessions()
            await pilot.pause()
            rules = [r.cwd for r in app.query(GroupRule)]
            assert rules == [CWD_ALPHA, "/home/john/beta", CWD_ZETA]
            assert rules == [h.cwd for h in app.query(GroupHeading)]

    async def test_scroll_position_survives_a_rebuild(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(90, 16)) as pilot:
            await pilot.pause()
            app.previews.scroll_to(y=4, animate=False)
            await pilot.pause()
            before = app.previews.scroll_offset.y
            assert before > 0
            write_record(fixture_home / "sessions", pid=3, name="zeta-99",
                         cwd=CWD_ZETA, status="busy",
                         session_id="66666666-6666-4666-8666-666666666666",
                         started_at=1_000_500)
            await app.refresh_sessions()
            await pilot.pause()
            assert app.previews.scroll_offset.y == before

    async def test_rules_survive_quiet_refresh_ticks(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            first = [id(r) for r in app.query(GroupRule)]
            for _ in range(3):
                await app.refresh_sessions()
                await pilot.pause()
            # No rebuild happened, so the same widgets are still mounted.
            assert [id(r) for r in app.query(GroupRule)] == first


class TestArrowNavigation:
    """Up and Down walk the rows; Left and Right work the agent tree."""

    @pytest.fixture
    def tree_home(self, fixture_home):
        """Give the busy session two agents so the tree has rows to walk."""
        projects = fixture_home / "projects"
        write_transcript(projects, "-home-john-zeta-proj", SESSION_ID_BUSY, [
            assistant_tool("Agent", {"description": "one"}, "toolu_1"),
        ])
        now = time.time()
        for index, agent_id in enumerate(("ag1", "ag2")):
            write_agent(projects, "-home-john-zeta-proj", SESSION_ID_BUSY, agent_id,
                        [agent_assistant("working")], description=f"agent {index}",
                        tool_use_id=f"toolu_{index}", meta_mtime=now - 100 + index,
                        jsonl_mtime=now)
        return fixture_home

    async def test_the_keyboard_starts_on_a_row_not_the_hidden_mirror(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            # A hidden PaneMirror holding focus would swallow every key.
            assert not isinstance(app.focused, PaneMirror)
            assert app.focused is app.previews.box_for(ALIVE)

    async def test_the_scroll_viewports_never_take_focus(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            assert app.sidebar.can_focus is False
            assert app.previews.can_focus is False
            seen = []
            for _ in range(14):
                app.screen.focus_next()
                await pilot.pause()
                seen.append(app.focused)
            assert app.sidebar not in seen
            assert app.previews not in seen

    async def test_arrows_work_without_a_click_first(self, tree_home):
        app = make_app(tree_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            # No click, no explicit focus() -- straight to the keyboard.
            await pilot.press("down")
            await pilot.pause()
            assert app.focused.id == "preview-1"
            await pilot.press("right")
            await pilot.pause()
            assert app.sidebar.is_expanded(1) is True
            await pilot.press("down")
            await pilot.pause()
            assert app.focused.id == "agent-ag1"

    async def test_enter_works_without_a_click_first(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            assert app.center.is_open is True
            assert app.center.pid == ALIVE

    async def test_down_walks_the_preview_boxes(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.previews.box_for(ALIVE).focus()
            await pilot.pause()
            seen = [app.focused.id]
            for _ in range(2):
                await pilot.press("down")
                await pilot.pause()
                seen.append(app.focused.id)
            assert seen == [f"preview-{ALIVE}", "preview-1", "preview-2"]

    async def test_up_walks_back(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.previews.box_for(2).focus()
            await pilot.pause()
            await pilot.press("up")
            await pilot.pause()
            assert app.focused.id == "preview-1"
            await pilot.press("up")
            await pilot.pause()
            assert app.focused.id == f"preview-{ALIVE}"

    async def test_the_ends_clamp(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.previews.box_for(ALIVE).focus()
            await pilot.pause()
            for _ in range(3):
                await pilot.press("up")
                await pilot.pause()
            assert app.focused.id == f"preview-{ALIVE}"
            for _ in range(6):
                await pilot.press("down")
                await pilot.pause()
            assert app.focused.id == "preview-2"

    async def test_delimiters_are_skipped(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            assert not any(isinstance(w, GroupRule) for w in app.nav_order())
            # preview-ALIVE and preview-1 sit in different groups, so a rule
            # is mounted between them; Down must step straight over it.
            children = list(app.previews.children)
            first = children.index(app.previews.box_for(ALIVE))
            second = children.index(app.previews.box_for(1))
            assert any(isinstance(w, GroupRule) for w in children[first + 1 : second])
            app.previews.box_for(ALIVE).focus()
            await pilot.pause()
            seen = []
            for _ in range(2):
                await pilot.press("down")
                await pilot.pause()
                seen.append(app.focused)
            assert not any(isinstance(w, GroupRule) for w in seen)
            assert seen[0].id == "preview-1"

    async def test_agent_rows_join_the_sequence_when_expanded(self, tree_home):
        app = make_app(tree_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            assert [w.id for w in app.nav_order()] == [
                f"preview-{ALIVE}", "preview-1", "preview-2"
            ]
            await pilot.click("#agents-1")
            await pilot.pause()
            assert [w.id for w in app.nav_order()] == [
                f"preview-{ALIVE}", "preview-1", "agent-ag1", "agent-ag2", "preview-2"
            ]
            app.previews.box_for(1).focus()
            await pilot.pause()
            seen = []
            for _ in range(3):
                await pilot.press("down")
                await pilot.pause()
                seen.append(app.focused.id)
            assert seen == ["agent-ag1", "agent-ag2", "preview-2"]

    async def test_right_expands_and_left_collapses(self, tree_home):
        app = make_app(tree_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.previews.box_for(1).focus()
            await pilot.pause()
            assert app.sidebar.is_expanded(1) is False
            await pilot.press("right")
            await pilot.pause()
            assert app.sidebar.is_expanded(1) is True
            assert len(list(app.query(AgentRow))) == 2
            await pilot.press("left")
            await pilot.pause()
            assert app.sidebar.is_expanded(1) is False
            assert list(app.query(AgentRow)) == []

    async def test_right_twice_does_not_collapse(self, tree_home):
        app = make_app(tree_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.previews.box_for(1).focus()
            await pilot.pause()
            for _ in range(2):
                await pilot.press("right")
                await pilot.pause()
            assert app.sidebar.is_expanded(1) is True

    async def test_left_on_an_agent_row_collapses_and_steps_up(self, tree_home):
        app = make_app(tree_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#agents-1")
            await pilot.pause()
            app.sidebar.agent_row_for("ag2").focus()
            await pilot.pause()
            await pilot.press("left")
            await pilot.pause()
            assert app.sidebar.is_expanded(1) is False
            assert app.focused.id == "preview-1"
            assert app.current_pid == 1

    async def test_arrows_work_from_a_sidebar_row(self, tree_home):
        app = make_app(tree_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#row-1")
            await pilot.pause()
            await pilot.press("right")
            await pilot.pause()
            assert app.sidebar.is_expanded(1) is True
            await pilot.press("down")
            await pilot.pause()
            # From the sidebar row, Down anchors on that session's own box.
            assert app.focused.id == "preview-1"

    async def test_a_session_without_agents_ignores_right(self, tree_home):
        app = make_app(tree_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.previews.box_for(2).focus()
            await pilot.pause()
            await pilot.press("right")
            await pilot.pause()
            assert app.sidebar.is_expanded(2) is False
            assert app.focused.id == "preview-2"

    async def test_focus_scrolls_the_stack_below_the_fold(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(90, 14)) as pilot:
            await pilot.pause()
            app.previews.box_for(ALIVE).focus()
            await pilot.pause()
            app.previews.scroll_to(y=0, animate=False)
            await pilot.pause()
            assert app.previews.scroll_offset.y == 0
            last = app.previews.box_for(2)
            assert last.region.bottom > app.previews.region.bottom, "not below the fold"
            for _ in range(2):
                await pilot.press("down")
                await pilot.pause()
            assert app.focused.id == "preview-2"
            assert app.previews.scroll_offset.y > 0

    async def test_selection_follows_the_arrow_keys(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.previews.box_for(ALIVE).focus()
            await pilot.pause()
            await pilot.press("down")
            await pilot.pause()
            assert app.current_pid == 1
            await pilot.press("down")
            await pilot.pause()
            assert app.current_pid == 2

    async def test_focus_survives_a_refresh_tick(self, tree_home):
        app = make_app(tree_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.previews.box_for(1).focus()
            await pilot.press("right")
            await pilot.pause()
            app.sidebar.agent_row_for("ag2").focus()
            await pilot.pause()
            assert app.focused.id == "agent-ag2"
            for _ in range(4):
                await app.refresh_sessions()
                await pilot.pause()
                assert app.focused.id == "agent-ag2"

    async def test_focus_survives_a_rebuild_that_adds_a_session(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.previews.box_for(2).focus()
            await pilot.pause()
            write_record(fixture_home / "sessions", pid=9, name="alpha-99",
                         cwd=CWD_ALPHA, status="busy",
                         session_id="77777777-7777-4777-8777-777777777777",
                         started_at=1_000_900)
            await app.refresh_sessions()
            await pilot.pause()
            assert app.previews.box_for(9) is not None
            assert app.focused.id == "preview-2", "a rebuild moved the keyboard"

    async def test_enter_still_opens_the_arrowed_row(self, tree_home):
        app = make_app(tree_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.previews.box_for(1).focus()
            await pilot.pause()
            await pilot.press("right")
            await pilot.pause()
            await pilot.press("down")
            await pilot.pause()
            assert app.focused.id == "agent-ag1"
            await pilot.press("enter")
            await pilot.pause()
            assert app.center.mode == "agent"
            assert app.center.agent_id == "ag1"


class TestStateOutlines:
    """Status drives the outline color, the border type, and the label."""

    async def test_waiting_box_shouts_human_needed(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            box = app.previews.box_for(ALIVE)
            assert box.has_class("-waiting")
            assert box.border_subtitle == "HUMAN NEEDED"
            assert box.lines_text[0] == "Approve: Bash(pytest)?"
            top_type, top_color = box.styles.border_top
            assert top_type == "dashed"  # [ro] variant of the waiting outline
            assert top_color.hex.lower() == "#ffa500"
            assert "HUMAN NEEDED" in screen_text(app)

    async def test_busy_box_is_cyan_and_says_thinking(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            box = app.previews.box_for(1)
            assert box.has_class("-busy")
            assert box.border_subtitle == "thinking"
            assert box.styles.border_top[1].hex.lower() == "#00ffff"

    async def test_idle_box_is_dim_gray(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            box = app.previews.box_for(2)
            assert box.has_class("-idle")
            assert box.border_subtitle == "idle"
            assert box.styles.border_top[1].hex.lower() == "#8a8a8a"

    async def test_ro_sessions_get_the_dashed_variant(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            for box in app.query(PreviewBox):
                assert box.has_class("-ro")
                assert box.styles.border_top[0] == "dashed"

    async def test_tmux_sessions_get_the_solid_variant(self, fixture_home, monkeypatch):
        pane = Pane("claude-retry-1-2", "0", "0", "%7", ALIVE)
        monkeypatch.setattr(tmux_mod, "pane_map", lambda pids: {ALIVE: pane})
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            box = app.previews.box_for(ALIVE)
            assert not box.has_class("-ro")
            assert box.styles.border_top[0] == "double"
            assert app.mirror.find(ALIVE).session_class == CLASS_TMUX
            assert app.mirror.find(1).session_class == CLASS_RO

    async def test_dead_record_is_marked_then_dropped(self, claude_home):
        sessions = claude_home / "sessions"
        write_record(sessions, pid=ALIVE, name="alive-aa", cwd=CWD_ALPHA)
        write_record(sessions, pid=4_194_303, name="ghost-bb", cwd=CWD_ALPHA)
        app = make_app(claude_home)
        async with app.run_test(size=(140, 40)) as pilot:
            # on_mount already polled, so the dead stamp is real wall-clock time.
            now = time.time()
            await app.apply(app.mirror.poll(now=now))
            await pilot.pause()
            ghost = app.previews.box_for(4_194_303)
            assert ghost is not None
            assert ghost.has_class("-dead")
            assert ghost.border_subtitle == "dead"
            assert ghost.lines_text  # a dead session still shows its last lines

            await app.apply(app.mirror.poll(now=now + 61.0))
            await pilot.pause()
            assert app.previews.box_for(4_194_303) is None
            assert app.previews.box_for(ALIVE) is not None


class TestHeader:
    """The header counts sessions and jumps to the next waiting one."""

    async def test_counts(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            assert app.mirror.header_text() == "3 sessions · 1 waiting"
            assert "3 sessions · 1 waiting" in screen_text(app)

    async def test_w_jumps_to_the_waiting_session(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.select(2)
            assert app.current_pid == 2
            await pilot.press("w")
            await pilot.pause()
            assert app.current_pid == ALIVE

    async def test_header_click_jumps_too(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.select(2)
            await pilot.click("#header")
            await pilot.pause()
            assert app.current_pid == ALIVE


class TestSelection:
    """Clicks focus a session; double-clicks open the center view."""

    async def test_single_click_focuses(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#preview-1")
            await pilot.pause()
            assert app.current_pid == 1
            assert app.center.is_open is False

    async def test_sidebar_row_click_focuses(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#row-2")
            await pilot.pause()
            assert app.current_pid == 2


class TestEnterOpens:
    """Enter opens the center view on whichever session holds the keyboard."""

    async def test_enter_on_a_focused_preview_box_opens_it(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.previews.box_for(1).focus()
            await pilot.pause()
            assert app.center.is_open is False
            await pilot.press("enter")
            await pilot.pause()
            assert app.center.is_open is True
            assert app.center.pid == 1
            assert app.current_pid == 1

    async def test_enter_on_a_selected_sidebar_row_opens_it(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#row-2")
            await pilot.pause()
            assert isinstance(app.focused, SessionRow)
            assert app.focused.pid == 2
            await pilot.press("enter")
            await pilot.pause()
            assert app.center.is_open is True
            assert app.center.pid == 2

    async def test_enter_follows_the_highlighted_row_without_widget_focus(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.select(2)
            app.set_focus(None)
            await pilot.pause()
            assert app.focused is None
            await pilot.press("enter")
            await pilot.pause()
            assert app.center.is_open is True
            assert app.center.pid == 2

    async def test_enter_matches_a_double_click(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click("#preview-1")
            await pilot.pause()
            clicked_mode, clicked_pid = app.center.mode, app.center.pid
            app.center.close()
            await pilot.pause()
            app.previews.box_for(1).focus()
            await pilot.press("enter")
            await pilot.pause()
            assert (app.center.mode, app.center.pid) == (clicked_mode, clicked_pid)

    async def test_enter_does_nothing_with_no_sessions(self, claude_home):
        app = make_app(claude_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            assert app.current_pid is None
            assert app.focused_pid() is None
            await pilot.press("enter")
            await pilot.pause()
            assert app.center.is_open is False
            assert app.is_running is True


class TestAgentTree:
    """The sidebar shows each session's subagents as an expandable tree."""

    @pytest.fixture
    def with_agents(self, fixture_home):
        """Give the busy session two agents: one running, one done."""
        projects = fixture_home / "projects"
        write_transcript(projects, "-home-john-zeta-proj", SESSION_ID_BUSY, [
            user_prompt("fix the fusion bug"),
            assistant_tool("Agent", {"description": "Port the parser"}, "toolu_done"),
            tool_result("toolu_done"),
            assistant_tool("Agent", {"description": "Write the docs"}, "toolu_live"),
        ])
        now = time.time()
        write_agent(projects, "-home-john-zeta-proj", SESSION_ID_BUSY, "adone",
                    [agent_assistant("finished", "claude-sonnet-5")],
                    description="Port the parser", tool_use_id="toolu_done",
                    model="sonnet", meta_mtime=now - 500, jsonl_mtime=now - 400)
        write_agent(projects, "-home-john-zeta-proj", SESSION_ID_BUSY, "alive",
                    [assistant_tool("Edit", {"file_path": "/a/app.py"}, "t1")],
                    description="Write the docs", tool_use_id="toolu_live",
                    model="opus", meta_mtime=now - 100, jsonl_mtime=now)
        return fixture_home

    async def test_no_toggle_for_a_session_without_agents(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            assert list(app.query(AgentToggleRow)) == []
            assert list(app.query(AgentRow)) == []

    async def test_toggle_appears_and_starts_collapsed(self, with_agents):
        app = make_app(with_agents)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            toggles = list(app.query(AgentToggleRow))
            assert [t.pid for t in toggles] == [1]
            assert toggles[0].expanded is False
            assert toggles[0].summary == "2 agents · 1 running"
            assert list(app.query(AgentRow)) == []
            assert "▸ 2 agents · 1 running" in screen_text(app)

    async def test_clicking_the_toggle_expands_the_tree(self, with_agents):
        app = make_app(with_agents)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#agents-1")
            await pilot.pause()
            rows = list(app.query(AgentRow))
            assert [r.agent_id for r in rows] == ["adone", "alive"]
            assert [r.state for r in rows] == ["done", "running"]
            assert [r.model for r in rows] == ["sonnet", "opus"]
            text = screen_text(app)
            assert "▾ 2 agents" in text
            assert "Port the parser" in text
            assert "Write the docs" in text

    async def test_enter_on_the_toggle_expands_and_collapses(self, with_agents):
        app = make_app(with_agents)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            app.sidebar.toggle_for(1).focus()
            await pilot.press("enter")
            await pilot.pause()
            assert len(list(app.query(AgentRow))) == 2
            assert app.center.is_open is False
            app.sidebar.toggle_for(1).focus()
            await pilot.press("enter")
            await pilot.pause()
            assert list(app.query(AgentRow)) == []

    async def test_expanded_state_survives_a_refresh_tick(self, with_agents):
        app = make_app(with_agents)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#agents-1")
            await pilot.pause()
            assert len(list(app.query(AgentRow))) == 2
            for _ in range(3):
                await app.refresh_sessions()
                await pilot.pause()
            assert len(list(app.query(AgentRow))) == 2
            assert app.sidebar.is_expanded(1) is True

    async def test_running_flips_to_done_on_the_next_tick(self, with_agents):
        app = make_app(with_agents)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#agents-1")
            await pilot.pause()
            assert app.sidebar.agent_row_for("alive").state == "running"
            # The parent transcript gets the tool_result that ends the agent.
            write_transcript(with_agents / "projects", "-home-john-zeta-proj",
                             SESSION_ID_BUSY, [
                                 user_prompt("fix the fusion bug"),
                                 assistant_tool("Agent", {"description": "Port the parser"}, "toolu_done"),
                                 tool_result("toolu_done"),
                                 assistant_tool("Agent", {"description": "Write the docs"}, "toolu_live"),
                                 tool_result("toolu_live"),
                             ])
            await app.refresh_sessions()
            await pilot.pause()
            assert app.sidebar.agent_row_for("alive").state == "done"
            assert app.sidebar.toggle_for(1).summary == "2 agents"

    async def test_only_running_agents_reach_the_preview_box(self, with_agents):
        app = make_app(with_agents)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            box = app.previews.box_for(1)
            assert box.agent_lines_text == ["⚙ opus: Editing app.py…"]
            assert "⚙ opus: Editing app.py…" in screen_text(app)
            assert app.previews.box_for(2).agent_lines_text == []

    async def test_enter_on_an_agent_row_opens_its_transcript(self, with_agents):
        app = make_app(with_agents)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#agents-1")
            await pilot.pause()
            app.sidebar.agent_row_for("adone").focus()
            await pilot.press("enter")
            await pilot.pause()
            assert app.center.is_open is True
            assert app.center.mode == "agent"
            assert app.center.agent_id == "adone"
            assert app.center.pid is None
            # Read-only is inherent: no pane, no sender, no typing.
            assert app.query_one(PaneMirror).target is None
            assert app.query_one(PaneMirror).sender is None
            assert app.query_one(TranscriptView).display is True
            assert "finished" in screen_text(app)

    async def test_double_click_on_an_agent_row_opens_its_transcript(self, with_agents):
        app = make_app(with_agents)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#agents-1")
            await pilot.pause()
            await pilot.double_click("#agent-alive")
            await pilot.pause()
            assert app.center.mode == "agent"
            assert app.center.agent_id == "alive"
            assert "Editing app.py…" in screen_text(app)

    async def test_the_exit_chord_closes_an_agent_transcript(self, with_agents):
        app = make_app(with_agents)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#agents-1")
            await pilot.pause()
            app.sidebar.agent_row_for("adone").focus()
            await pilot.press("enter")
            await pilot.pause()
            assert app.center.is_open is True
            await pilot.press("ctrl+backslash")
            await pilot.pause()
            assert app.center.is_open is False
            assert app.center.agent_id is None

    async def test_the_agent_view_survives_many_refresh_ticks(self, with_agents):
        app = make_app(with_agents)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#agents-1")
            await pilot.pause()
            app.sidebar.agent_row_for("adone").focus()
            await pilot.press("enter")
            await pilot.pause()
            assert app.center.is_open is True
            assert app.center.mode == "agent"

            # Four seconds of the 1 s refresh must not disturb either surface.
            for _ in range(4):
                await app.refresh_sessions()
                await pilot.pause()
                assert app.center.is_open is True, "the agent view closed under a tick"
                assert app.center.mode == "agent"
                assert app.center.agent_id == "adone"
                assert app.sidebar.is_expanded(1) is True
                assert len(list(app.query(AgentRow))) == 2
            assert "finished" in screen_text(app)

    async def test_the_agent_view_keeps_updating_its_content(self, with_agents):
        app = make_app(with_agents)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#agents-1")
            await pilot.pause()
            app.sidebar.agent_row_for("alive").focus()
            await pilot.press("enter")
            await pilot.pause()
            assert app.center.mode == "agent"
            assert "Editing app.py…" in screen_text(app)

            # The agent appends to its transcript; the open view must follow.
            write_agent(with_agents / "projects", "-home-john-zeta-proj",
                        SESSION_ID_BUSY, "alive",
                        [assistant_tool("Edit", {"file_path": "/a/app.py"}, "t1"),
                         assistant_tool("Bash", {"command": "pytest -q"}, "t2")],
                        description="Write the docs", tool_use_id="toolu_live",
                        model="opus")
            await app.refresh_sessions()
            await pilot.pause()
            assert app.center.is_open is True
            assert "Bash(pytest -q)" in screen_text(app)

    async def test_a_live_mirror_still_closes_when_its_session_dies(self, with_agents):
        app = make_app(with_agents)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click("#preview-2")
            await pilot.pause()
            assert app.center.is_open is True
            assert app.center.pid == 2
            (with_agents / "sessions" / "2.json").unlink()
            await app.refresh_sessions()
            await pilot.pause()
            assert app.center.is_open is False

    async def test_the_agent_view_closes_when_its_session_dies(self, with_agents):
        app = make_app(with_agents)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#agents-1")
            await pilot.pause()
            app.sidebar.agent_row_for("adone").focus()
            await pilot.press("enter")
            await pilot.pause()
            assert app.center.is_open is True
            (with_agents / "sessions" / "1.json").unlink()
            await app.refresh_sessions()
            await pilot.pause()
            assert app.center.is_open is False

    async def test_ctrl_q_closes_an_agent_transcript(self, with_agents):
        app = make_app(with_agents)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#agents-1")
            await pilot.pause()
            app.sidebar.agent_row_for("adone").focus()
            await pilot.press("enter")
            await pilot.pause()
            assert app.center.mode == "agent"
            await pilot.press("ctrl+q")
            await pilot.pause()
            assert app.center.is_open is False
            assert app.center.agent_id is None
            assert app.is_running is True
            # Closing the view must leave the tree exactly as it was.
            assert app.sidebar.is_expanded(1) is True

    async def test_nested_agents_are_indented_by_spawn_depth(self, fixture_home):
        projects = fixture_home / "projects"
        write_transcript(projects, "-home-john-zeta-proj", SESSION_ID_BUSY, [
            assistant_tool("Agent", {"description": "outer"}, "toolu_out"),
        ])
        now = time.time()
        write_agent(projects, "-home-john-zeta-proj", SESSION_ID_BUSY, "outer",
                    [assistant_tool("Agent", {"description": "inner"}, "toolu_in")],
                    description="Outer agent", tool_use_id="toolu_out",
                    meta_mtime=now - 200, jsonl_mtime=now)
        write_agent(projects, "-home-john-zeta-proj", SESSION_ID_BUSY, "inner",
                    [agent_assistant("deep")], description="Inner agent",
                    tool_use_id="toolu_in", spawn_depth=2, parent_agent_id="outer",
                    meta_mtime=now - 100, jsonl_mtime=now)
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.click("#agents-1")
            await pilot.pause()
            agents = {a.agent_id: a for a in app.mirror.find(1).agents}
            assert agents["outer"].indent == ""
            assert agents["inner"].indent == "  "
            assert agents["inner"].spawn_depth == 2


class TestCenterView:
    """The center view opens over the previews and leaves the sidebar up."""

    @pytest.fixture
    def fake_pane(self, monkeypatch):
        """Give the waiting session a pane, a canned capture, and a cursor."""
        pane = Pane("claude-retry-1-2", "0", "0", "%7", ALIVE)
        monkeypatch.setattr(tmux_mod, "pane_map", lambda pids: {ALIVE: pane})
        captures = ["\x1b[36m> claude screen one\x1b[0m", "\x1b[36m> claude screen two\x1b[0m"]
        state = {"index": 0, "cursor": Cursor(2, 0, True)}

        def capture(target, escapes=True):
            return captures[min(state["index"], len(captures) - 1)]

        def capture_with_cursor(target):
            return capture(target), state["cursor"]

        monkeypatch.setattr(tmux_mod, "capture_pane", capture)
        monkeypatch.setattr(tmux_mod, "capture_with_cursor", capture_with_cursor)
        return pane, state

    async def test_double_click_opens_the_live_mirror(self, fixture_home, fake_pane):
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            assert app.center.is_open is True
            assert app.center.mode == "live"
            assert app.center.pid == ALIVE
            assert "claude screen one" in screen_text(app)

    async def test_the_sidebar_stays_visible(self, fixture_home, fake_pane):
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            assert app.sidebar.display is True
            assert app.sidebar.region.width > 0
            assert app.center.region.x > app.sidebar.region.right - 1
            assert "zeta_proj" in screen_text(app)

    async def test_ctrl_backslash_closes(self, fixture_home, fake_pane):
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            assert app.center.is_open is True
            await pilot.press("ctrl+backslash")
            await pilot.pause()
            assert app.center.is_open is False

    async def test_click_outside_closes(self, fixture_home, fake_pane):
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            assert app.center.is_open is True
            await pilot.click("#sidebar", offset=(1, 12))
            await pilot.pause()
            assert app.center.is_open is False

    async def test_hash_diff_repaints_only_on_change(self, fixture_home, fake_pane):
        _pane, state = fake_pane
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            mirror = app.query_one(PaneMirror)
            mirror.stop()  # freeze the blink so only content drives the diff
            mirror.paint(*tmux_mod.capture_with_cursor("%7"))
            first = mirror.repaint_count
            assert mirror.paint(*tmux_mod.capture_with_cursor("%7")) is False
            assert mirror.repaint_count == first
            state["index"] = 1
            assert mirror.paint(*tmux_mod.capture_with_cursor("%7")) is True
            assert mirror.repaint_count == first + 1
            assert "claude screen two" in screen_text(app)

    async def test_the_cursor_cell_is_painted_in_the_mirror(self, fixture_home, fake_pane):
        _pane, state = fake_pane
        state["cursor"] = Cursor(5, 0, True)
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            mirror = app.query_one(PaneMirror)
            mirror.pause_polling()
            mirror.tick = 0
            mirror.paint("> claude screen one", Cursor(5, 0, True))
            assert mirror.shows_cursor is True
            assert mirror.cursor_spans == [(5, 6)]
            assert mirror.painted.plain[5] == "u"  # "> cla|ude screen one"

    async def test_blink_toggles_without_re_parsing_the_capture(self, fixture_home, fake_pane):
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            mirror = app.query_one(PaneMirror)
            mirror.pause_polling()
            capture = "> claude screen one"
            cursor = Cursor(3, 0, True)

            mirror.tick = 0
            assert mirror.blink_on is True
            mirror.paint(capture, cursor)
            digest = mirror.content_digest(capture)
            parses = mirror.parse_count
            repaints = mirror.repaint_count

            # Blink off: the cell changes, the content hash and parse do not.
            mirror.tick = BLINK_TICKS
            assert mirror.blink_on is False
            assert mirror.paint(capture, cursor) is True
            assert mirror.content_digest(capture) == digest
            assert mirror.parse_count == parses
            assert mirror.repaint_count == repaints + 1

            # Blink on again: still no re-parse.
            mirror.tick = BLINK_TICKS * 2
            assert mirror.blink_on is True
            assert mirror.paint(capture, cursor) is True
            assert mirror.parse_count == parses

    async def test_the_content_hash_ignores_the_blink_phase(self, fixture_home, fake_pane):
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            mirror = app.query_one(PaneMirror)
            mirror.pause_polling()
            capture = "unchanged screen"
            parses = mirror.parse_count
            seen = set()
            for tick in range(0, BLINK_TICKS * 4):
                mirror.tick = tick
                mirror.paint(capture, Cursor(1, 0, True))
                seen.add(mirror.content_digest(capture))
            assert len(seen) == 1
            assert mirror.parse_count == parses + 1

    async def test_a_still_screen_repaints_only_on_blink_edges(self, fixture_home, fake_pane):
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            mirror = app.query_one(PaneMirror)
            mirror.pause_polling()
            capture = "still screen"
            cursor = Cursor(0, 0, True)
            mirror.tick = 0
            mirror.paint(capture, cursor)
            repaints = mirror.repaint_count
            # Ten ticks span exactly two blink edges.
            for tick in range(1, BLINK_TICKS * 2 + 1):
                mirror.tick = tick
                mirror.paint(capture, cursor)
            assert mirror.repaint_count == repaints + 2

    async def test_a_hidden_cursor_is_not_painted(self, fixture_home, fake_pane):
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            mirror = app.query_one(PaneMirror)
            mirror.pause_polling()
            mirror.tick = 0
            mirror.paint("screen text", Cursor(2, 0, visible=False))
            assert mirror.cursor_spans == []

    async def test_an_unfocused_mirror_paints_no_cursor(self, fixture_home, fake_pane):
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            mirror = app.query_one(PaneMirror)
            mirror.stop()
            app.previews.box_for(ALIVE).focus()
            await pilot.pause()
            assert mirror.has_focus is False
            assert mirror.shows_cursor is False
            mirror.tick = 0
            mirror.paint("screen text", Cursor(2, 0, True))
            assert mirror.cursor_spans == []

    async def test_the_ro_transcript_view_has_no_cursor(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click("#preview-1")
            await pilot.pause()
            assert app.center.mode == "transcript"
            mirror = app.query_one(PaneMirror)
            assert mirror.target is None
            assert mirror.cursor is None
            assert mirror.shows_cursor is False

    async def test_keys_are_forwarded_to_the_pane(self, fixture_home, fake_pane, monkeypatch):
        sent: list[tuple] = []
        monkeypatch.setattr(tmux_mod, "send_text", lambda t, s: sent.append(("text", t, s)) or True)
        monkeypatch.setattr(tmux_mod, "send_key", lambda t, k: sent.append(("key", t, k)) or True)
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            mirror = app.query_one(PaneMirror)
            await pilot.press("h", "i", "enter", "ctrl+r", "up")
            await pilot.pause()
            mirror.sender.stop(timeout=2.0)
        assert sent == [
            ("text", "%7", "h"),
            ("text", "%7", "i"),
            ("key", "%7", "Enter"),
            ("key", "%7", "C-r"),
            ("key", "%7", "Up"),
        ]

    async def test_q_never_quits_from_the_center_view(self, fixture_home, fake_pane, monkeypatch):
        sent: list[tuple] = []
        monkeypatch.setattr(tmux_mod, "send_text", lambda t, s: sent.append(s) or True)
        monkeypatch.setattr(tmux_mod, "send_key", lambda t, k: sent.append(k) or True)
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            await pilot.press("q")
            await pilot.pause()
            assert app.center.is_open is True
            assert app.is_running is True
            app.query_one(PaneMirror).sender.stop(timeout=2.0)
        assert "q" in sent

    async def test_every_other_key_belongs_to_claude(self, fixture_home, fake_pane, monkeypatch):
        sent: list[str] = []
        monkeypatch.setattr(tmux_mod, "send_text", lambda t, s: sent.append(s) or True)
        monkeypatch.setattr(tmux_mod, "send_key", lambda t, k: sent.append(k) or True)
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            # Ctrl+Q is an exit chord now, so it is not in this set.
            keys = ("ctrl+c", "ctrl+p", "w", "escape", "f5", "tab",
                    "up", "down", "left", "right")
            for key in keys:
                await pilot.press(key)
                await pilot.pause()
                assert app.is_running is True, f"{key} must not quit the app"
                assert app.center.is_open is True, f"{key} must not close the mirror"
            app.query_one(PaneMirror).sender.stop(timeout=2.0)
        assert sent == ["C-c", "C-p", "w", "Escape", "F5", "Tab",
                        "Up", "Down", "Left", "Right"]

    async def test_ctrl_q_closes_the_mirror_and_sends_nothing(
        self, fixture_home, fake_pane, monkeypatch
    ):
        sent: list[str] = []
        monkeypatch.setattr(tmux_mod, "send_text", lambda t, s: sent.append(s) or True)
        monkeypatch.setattr(tmux_mod, "send_key", lambda t, k: sent.append(k) or True)
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            assert app.center.is_open is True
            mirror = app.query_one(PaneMirror)
            await pilot.press("ctrl+q")
            await pilot.pause()
            assert app.center.is_open is False, "ctrl+q must close the mirror"
            assert app.is_running is True, "ctrl+q must not quit the app"
            assert mirror.target is None
        # The chord is stolen before the sender: Claude never sees it.
        assert sent == [], f"ctrl+q reached the pane: {sent}"

    async def test_ctrl_q_closes_the_ro_transcript_view(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click("#preview-1")
            await pilot.pause()
            assert app.center.mode == "transcript"
            await pilot.press("ctrl+q")
            await pilot.pause()
            assert app.center.is_open is False
            assert app.is_running is True

    async def test_enter_inside_the_mirror_reaches_the_pane(self, fixture_home, fake_pane, monkeypatch):
        sent: list[str] = []
        monkeypatch.setattr(tmux_mod, "send_text", lambda t, s: sent.append(s) or True)
        monkeypatch.setattr(tmux_mod, "send_key", lambda t, k: sent.append(k) or True)
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            opened = (app.center.mode, app.center.pid)
            await pilot.press(*"hi", "enter")
            await pilot.pause()
            # Enter must type into Claude, never re-trigger the open action.
            assert app.center.is_open is True
            assert (app.center.mode, app.center.pid) == opened
            app.query_one(PaneMirror).sender.stop(timeout=2.0)
        assert sent == ["h", "i", "Enter"]

    async def test_enter_inside_the_ro_transcript_view_is_inert(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click("#preview-1")
            await pilot.pause()
            opened = (app.center.mode, app.center.pid)
            await pilot.press("enter")
            await pilot.pause()
            assert app.center.is_open is True
            assert (app.center.mode, app.center.pid) == opened

    async def test_arrows_inside_the_mirror_never_move_dashboard_focus(
        self, fixture_home, fake_pane, monkeypatch
    ):
        sent: list[str] = []
        monkeypatch.setattr(tmux_mod, "send_text", lambda t, s: sent.append(s) or True)
        monkeypatch.setattr(tmux_mod, "send_key", lambda t, k: sent.append(k) or True)
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            mirror = app.query_one(PaneMirror)
            assert app.focused is mirror
            before = app.current_pid
            for key in ("down", "down", "up", "left", "right"):
                await pilot.press(key)
                await pilot.pause()
            assert app.focused is mirror, "an arrow escaped the mirror"
            assert app.current_pid == before
            assert app.sidebar.is_expanded(ALIVE) is False
            mirror.sender.stop(timeout=2.0)
        assert sent == ["Down", "Down", "Up", "Left", "Right"]

    async def test_a_dead_pane_closes_the_mirror(self, fixture_home, fake_pane, monkeypatch):
        monkeypatch.setattr(tmux_mod, "capture_with_cursor", lambda t: ("", None))
        monkeypatch.setattr(tmux_mod, "pane_exists", lambda t: False)
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            deadline = time.time() + 3.0
            while time.time() < deadline and app.center.is_open:
                await pilot.pause()
                time.sleep(0.05)
            assert app.center.is_open is False

    async def test_the_mirror_survives_a_blank_but_live_pane(self, fixture_home, fake_pane, monkeypatch):
        monkeypatch.setattr(tmux_mod, "capture_with_cursor", lambda t: ("", None))
        monkeypatch.setattr(tmux_mod, "pane_exists", lambda t: True)
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            for _ in range(6):
                await pilot.pause()
                time.sleep(0.05)
            assert app.center.is_open is True
            app.query_one(PaneMirror).stop()

    async def test_a_vanished_session_closes_the_mirror(self, fixture_home, fake_pane):
        app = make_app(fixture_home, match_panes=True)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click(f"#preview-{ALIVE}")
            await pilot.pause()
            assert app.center.is_open is True
            (fixture_home / "sessions" / f"{ALIVE}.json").unlink()
            await app.refresh_sessions()
            await pilot.pause()
            assert app.center.is_open is False

    async def test_ro_session_opens_a_read_only_transcript(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click("#preview-1")
            await pilot.pause()
            assert app.center.is_open is True
            assert app.center.mode == "transcript"
            view = app.query_one(TranscriptView)
            assert view.display is True
            assert app.query_one(PaneMirror).display is False
            assert app.query_one(PaneMirror).target is None
            assert "fix the fusion bug" in screen_text(app)

    async def test_q_never_quits_from_the_ro_transcript_view(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click("#preview-1")
            await pilot.pause()
            await pilot.press("q")
            await pilot.pause()
            assert app.is_running is True
            assert app.center.is_open is True

    async def test_the_exit_chord_closes_the_ro_transcript_view(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click("#preview-1")
            await pilot.pause()
            await pilot.press("ctrl+backslash")
            await pilot.pause()
            assert app.center.is_open is False
            assert app.query_one(TranscriptView).display is False


class TestLiveUpdates:
    """A poll picks up new records and new transcript lines."""

    async def test_a_new_session_appears(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            assert len(list(app.query(PreviewBox))) == 3
            write_record(fixture_home / "sessions", pid=3, name="alpha-99",
                         cwd=CWD_ALPHA, status="busy",
                         session_id="44444444-4444-4444-8444-444444444444",
                         started_at=1_000_300)
            await app.refresh_sessions()
            await pilot.pause()
            assert len(list(app.query(PreviewBox))) == 4
            assert app.mirror.header_text() == "4 sessions · 1 waiting"

    async def test_new_transcript_lines_reach_the_box(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            box = app.previews.box_for(1)
            assert "Bash(npm run build)" not in box.lines_text
            write_transcript(fixture_home / "projects", "-home-john-zeta-proj",
                             SESSION_ID_BUSY, [
                                 user_prompt("fix the fusion bug"),
                                 assistant_tool("Edit", {"file_path": "/a/model.py"}, "t2"),
                                 tool_result("t2"),
                                 assistant_tool("Bash", {"command": "npm run build"}, "t5"),
                             ])
            await app.refresh_sessions()
            await pilot.pause()
            assert "Bash(npm run build)" in app.previews.box_for(1).lines_text

    async def test_status_change_repaints_the_outline(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            assert app.previews.box_for(1).has_class("-busy")
            write_record(fixture_home / "sessions", pid=1, name="zeta-e3", cwd=CWD_ZETA,
                         status="waiting", session_id=SESSION_ID_BUSY,
                         started_at=1_000_100, waiting_for="input needed")
            await app.refresh_sessions()
            await pilot.pause()
            box = app.previews.box_for(1)
            assert box.has_class("-waiting")
            assert box.border_subtitle == "HUMAN NEEDED"
            assert app.mirror.header_text() == "3 sessions · 2 waiting"


class TestQuit:
    """`q` is the only way to quit; ctrl+q only ever closes the center view."""

    async def test_q_quits_the_dashboard(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.press("q")
            await pilot.pause()
        assert app.is_running is False

    async def test_ctrl_q_on_the_dashboard_does_nothing(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            assert app.center.is_open is False
            focused_before = app.focused
            current_before = app.current_pid
            for _ in range(3):
                await pilot.press("ctrl+q")
                await pilot.pause()
                assert app.is_running is True, "ctrl+q must not quit the dashboard"
                assert app.center.is_open is False, "ctrl+q must not open anything"
            assert app.focused is focused_before
            assert app.current_pid == current_before

    async def test_ctrl_q_does_not_quit_after_closing_a_view(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            await pilot.double_click("#preview-1")
            await pilot.pause()
            await pilot.press("ctrl+q")
            await pilot.pause()
            assert app.center.is_open is False
            # A second press lands on the dashboard and must be inert.
            await pilot.press("ctrl+q")
            await pilot.pause()
            assert app.is_running is True
            assert app.center.is_open is False

    async def test_the_header_names_the_close_chord(self, fixture_home):
        app = make_app(fixture_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            header = screen_text(app).splitlines()[0]
            assert "Ctrl+Q closes" in header
            assert "q quits" in header


class TestEmptyState:
    """No records means no boxes and a zero header."""

    async def test_no_sessions(self, claude_home):
        app = make_app(claude_home)
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            assert list(app.query(PreviewBox)) == []
            assert app.mirror.header_text() == "0 sessions · 0 waiting"
            assert app.current_pid is None
