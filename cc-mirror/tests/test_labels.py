"""Check the transcript reader and the transcript-to-label mapping."""

from __future__ import annotations

import json

from cc_mirror.labels import (
    Label,
    clip,
    event_label,
    pending_line,
    pending_tool_use,
    preview_lines,
    tail,
    tool_label,
)
from cc_mirror.records import SessionRecord
from cc_mirror.transcript import read_all_lines, read_tail_lines

from .conftest import assistant_text, assistant_tool, tool_result, user_prompt


def make_record(status="busy", waiting_for="", cwd="/home/john/demo"):
    """Build a SessionRecord for label tests."""
    return SessionRecord(
        pid=42,
        session_id="s-42",
        cwd=cwd,
        name="demo-aa",
        status=status,
        started_at=0.0,
        updated_at=0.0,
        waiting_for=waiting_for,
    )


class TestClip:
    """Preview lines flatten to one line and fit the width."""

    def test_short_text_is_untouched(self):
        assert clip("hello") == "hello"

    def test_newlines_collapse(self):
        assert clip("a\nb\n  c") == "a b c"

    def test_long_text_is_cut_with_an_ellipsis(self):
        out = clip("x" * 100, width=10)
        assert len(out) == 10
        assert out.endswith("…")

    def test_tail_keeps_the_ending(self):
        out = tail("abcdefghij", width=5)
        assert out == "…ghij"
        assert len(out) == 5


class TestToolLabel:
    """Tool calls read as `Bash(...)`, `Editing file…`, and so on."""

    def test_bash_prefers_the_description(self):
        assert tool_label("Bash", {"command": "pytest -k fusion", "description": "Run tests"}) == "Bash(Run tests)"

    def test_bash_falls_back_to_the_command(self):
        assert tool_label("Bash", {"command": "git diff"}) == "Bash(git diff)"

    def test_edit_shows_the_basename(self):
        assert tool_label("Edit", {"file_path": "/a/b/auth.ts"}) == "Editing auth.ts…"

    def test_write_shows_the_basename(self):
        assert tool_label("Write", {"file_path": "/a/b/model.py", "content": "x"}) == "Editing model.py…"

    def test_read_shows_the_basename(self):
        assert tool_label("Read", {"file_path": "/a/b/spec.md"}) == "Reading spec.md"

    def test_grep_shows_the_pattern(self):
        assert tool_label("Grep", {"pattern": "send-keys"}) == "Grep(send-keys)"

    def test_skill_shows_the_skill_name(self):
        assert tool_label("Skill", {"skill": "superpowers:tdd"}) == "Skill(superpowers:tdd)"

    def test_agent_shows_the_description(self):
        label = tool_label("Agent", {"description": "Build the TUI", "prompt": "long..."})
        assert label == "Agent(Build the TUI)"

    def test_unknown_tool_with_no_string_input(self):
        assert tool_label("Mystery", {}) == "Mystery"


class TestEventLabel:
    """Every transcript record type maps to one line, or to nothing."""

    def test_assistant_text(self):
        label = event_label(assistant_text("Done refactoring."))
        assert label == Label("text", "Done refactoring.")

    def test_assistant_tool_use_wins_over_earlier_text(self):
        event = {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Now I run the tests."},
                    {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "pytest"}},
                ],
            },
        }
        assert event_label(event).text == "Bash(pytest)"

    def test_thinking_block_alone_gives_nothing(self):
        event = {
            "type": "assistant",
            "message": {"content": [{"type": "thinking", "thinking": "hmm", "signature": "x"}]},
        }
        assert event_label(event) is None

    def test_typed_user_prompt(self):
        label = event_label(user_prompt("commit then get subagent to do those"))
        assert label.kind == "prompt"
        assert label.text.startswith("› ")
        assert "commit then get subagent" in label.text

    def test_system_prompt_source_is_skipped(self):
        event = user_prompt("<task-notification>...</task-notification>")
        event["promptSource"] = "system"
        assert event_label(event) is None

    def test_meta_user_event_is_skipped(self):
        event = {
            "type": "user",
            "isMeta": True,
            "sourceToolUseID": "toolu_1",
            "message": {"content": [{"type": "text", "text": "Base directory for this skill: ..."}]},
        }
        assert event_label(event) is None

    def test_tool_result_gives_no_line(self):
        assert event_label(tool_result("t1", "1\tline one")) is None

    def test_bookkeeping_types_are_skipped(self):
        for kind in ("attachment", "ai-title", "mode", "permission-mode", "atis-latch",
                     "last-prompt", "queue-operation", "file-history-snapshot",
                     "file-history-delta", "system", "relocated", "worktree-state"):
            assert event_label({"type": kind, "sessionId": "s"}) is None, kind


class TestPendingDetection:
    """A tool_use with no result means the session waits for approval."""

    def test_unresolved_tool_use_is_found(self):
        events = [
            assistant_tool("Bash", {"command": "git status"}, "t1"),
            tool_result("t1"),
            assistant_tool("Bash", {"command": "pytest"}, "t2"),
        ]
        block = pending_tool_use(events)
        assert block is not None and block["id"] == "t2"

    def test_resolved_tool_use_is_not_pending(self):
        events = [
            assistant_tool("Bash", {"command": "pytest"}, "t2"),
            tool_result("t2"),
        ]
        assert pending_tool_use(events) is None

    def test_no_tool_calls_at_all(self):
        assert pending_tool_use([assistant_text("hello")]) is None

    def test_pending_line_reads_as_an_approval(self):
        events = [assistant_tool("Bash", {"command": "pytest"}, "t2")]
        assert pending_line(make_record("waiting"), events) == "Approve: Bash(pytest)?"

    def test_pending_line_falls_back_to_the_last_assistant_text(self):
        events = [
            assistant_tool("Bash", {"command": "pytest"}, "t1"),
            tool_result("t1"),
            assistant_text("Which branch should I merge into?"),
        ]
        assert pending_line(make_record("waiting"), events) == "Which branch should I merge into?"

    def test_pending_line_falls_back_to_waiting_for(self):
        events = [
            assistant_tool("Bash", {"command": "pytest"}, "t1"),
            tool_result("t1"),
        ]
        record = make_record("waiting", waiting_for="input needed")
        assert pending_line(record, events) == "input needed"


class TestPreviewLines:
    """A preview box gets at most five lines, status first when waiting."""

    def test_busy_session_shows_the_recent_activity(self):
        events = [
            user_prompt("fix the fusion bug"),
            assistant_text("Reading the model."),
            assistant_tool("Read", {"file_path": "/a/model.py"}, "t1"),
            tool_result("t1"),
            assistant_tool("Edit", {"file_path": "/a/model.py"}, "t2"),
            tool_result("t2"),
            assistant_tool("Bash", {"command": "pytest -k fusion"}, "t3"),
            tool_result("t3"),
        ]
        lines = preview_lines(make_record("busy"), events)
        assert len(lines) == 5
        assert lines[-1].text == "Bash(pytest -k fusion)"
        assert lines[-2].text == "Editing model.py…"

    def test_waiting_session_leads_with_the_pending_approval(self):
        events = [
            assistant_text("Running the suite."),
            assistant_tool("Bash", {"command": "pytest"}, "t9"),
        ]
        lines = preview_lines(make_record("waiting"), events)
        assert lines[0].kind == "pending"
        assert lines[0].text == "Approve: Bash(pytest)?"

    def test_idle_session_marks_the_last_text_as_done(self):
        events = [
            assistant_tool("Bash", {"command": "pytest"}, "t1"),
            tool_result("t1"),
            assistant_text("refactor complete"),
        ]
        lines = preview_lines(make_record("idle"), events)
        assert lines[-1].kind == "done"
        assert lines[-1].text == "Done: refactor complete"

    def test_empty_transcript(self):
        lines = preview_lines(make_record("busy"), [])
        assert [line.text for line in lines] == ["(no transcript yet)"]

    def test_repeated_lines_collapse(self):
        events = [assistant_text("same"), assistant_text("same"), assistant_text("other")]
        lines = preview_lines(make_record("busy"), events)
        assert [line.text for line in lines] == ["same", "other"]


class TestTranscriptReader:
    """The reader takes the tail of the file and skips torn lines."""

    def test_reads_whole_lines_only(self, tmp_path):
        path = tmp_path / "t.jsonl"
        events = [assistant_text(f"line {i} " + "x" * 500) for i in range(60)]
        path.write_text("\n".join(json.dumps(e) for e in events) + "\n")
        tailed = read_tail_lines(path, tail_bytes=4096)
        assert 0 < len(tailed) < 60
        assert all(isinstance(e, dict) for e in tailed)
        assert tailed[-1]["message"]["content"][0]["text"].startswith("line 59")

    def test_small_file_is_read_whole(self, tmp_path):
        path = tmp_path / "t.jsonl"
        path.write_text(json.dumps(assistant_text("only")) + "\n")
        assert len(read_tail_lines(path)) == 1

    def test_bad_json_lines_are_skipped(self, tmp_path):
        path = tmp_path / "t.jsonl"
        path.write_text(json.dumps(assistant_text("good")) + "\n{oops\n")
        assert len(read_tail_lines(path)) == 1

    def test_missing_file_is_empty(self, tmp_path):
        assert read_tail_lines(tmp_path / "nope.jsonl") == []
        assert read_all_lines(tmp_path / "nope.jsonl") == []


class TestWorktreeSlugCase:
    """The worktree slug resolves to the real transcript path."""

    def test_worktree_record_finds_its_transcript(self, tmp_path, monkeypatch):
        from cc_mirror import records as records_mod

        monkeypatch.setattr(records_mod, "PROJECTS_DIR", tmp_path)
        cwd = "/home/john/pdf-grinder/.claude/worktrees/stage-1-engine-module"
        record = SessionRecord(
            pid=1,
            session_id="abc",
            cwd=cwd,
            name="pdf-grinder-c3",
            status="waiting",
            started_at=0.0,
            updated_at=0.0,
        )
        folder = tmp_path / "-home-john-pdf-grinder--claude-worktrees-stage-1-engine-module"
        folder.mkdir()
        (folder / "abc.jsonl").write_text(
            json.dumps(assistant_tool("Bash", {"command": "pytest"}, "t1")) + "\n"
        )
        assert record.transcript_path.exists()
        events = read_tail_lines(record.transcript_path)
        lines = preview_lines(record, events)
        assert lines[0].text == "Approve: Bash(pytest)?"
