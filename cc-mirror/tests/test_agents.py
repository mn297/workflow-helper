"""Check subagent meta parsing, model naming, and running/done/stalled state."""

from __future__ import annotations

import json
import os

import pytest

from cc_mirror.agents import (
    STATE_DONE,
    STATE_RUNNING,
    STATE_STALLED,
    STATE_STOPPED,
    AgentStore,
    model_short_name,
    parse_meta,
    read_model_from_transcript,
    read_resolved_tool_ids,
    subagents_dir,
)
from cc_mirror.records import SessionRecord

from .conftest import (
    agent_assistant,
    assistant_text,
    assistant_tool,
    tool_result,
    write_agent,
    write_transcript,
)

SLUG = "-home-john-demo"
SID = "aaaaaaaa-1111-4111-8111-111111111111"


def make_record(projects_root, monkeypatch, cwd="/home/john/demo"):
    """Build a record whose transcript lives under a throwaway projects root."""
    from cc_mirror import records as records_mod

    monkeypatch.setattr(records_mod, "PROJECTS_DIR", projects_root)
    return SessionRecord(
        pid=1,
        session_id=SID,
        cwd=cwd,
        name="demo-aa",
        status="busy",
        started_at=0.0,
        updated_at=0.0,
    )


class TestModelShortName:
    """A model id shortens to opus, sonnet, haiku, or fable."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("claude-opus-5", "opus"),
            ("claude-opus-5[1m]", "opus"),
            ("claude-sonnet-5", "sonnet"),
            ("claude-haiku-4-5-20251001", "haiku"),
            ("claude-fable-5", "fable"),
            ("opus", "opus"),
            ("sonnet", "sonnet"),
            ("haiku", "haiku"),
            ("fable", "fable"),
            ("us.anthropic.claude-sonnet-5-v1:0", "sonnet"),
        ],
    )
    def test_known_models(self, value, expected):
        assert model_short_name(value) == expected

    @pytest.mark.parametrize("value", [None, "", "gpt-4o", "some-other-model", 0])
    def test_unknown_models_are_blank(self, value):
        assert model_short_name(value) == ""


class TestParseMeta:
    """Meta files carry the fields the tree shows, and tolerate missing ones."""

    def test_full_meta(self):
        parsed = parse_meta(
            {
                "agentType": "general-purpose",
                "description": "Graphics fundamentals explainer",
                "toolUseId": "toolu_01YPpc",
                "spawnDepth": 1,
                "model": "fable",
                "worktreeCleanlyRemoved": True,
            }
        )
        assert parsed["description"] == "Graphics fundamentals explainer"
        assert parsed["agent_type"] == "general-purpose"
        assert parsed["tool_use_id"] == "toolu_01YPpc"
        assert parsed["spawn_depth"] == 1
        assert parsed["model"] == "fable"
        assert parsed["parent_agent_id"] == ""
        assert parsed["stopped_by_user"] is False

    def test_nested_meta_names_its_parent(self):
        parsed = parse_meta({"spawnDepth": 3, "parentAgentId": "a123", "toolUseId": "t"})
        assert parsed["spawn_depth"] == 3
        assert parsed["parent_agent_id"] == "a123"

    def test_meta_without_a_model(self):
        assert parse_meta({"description": "x", "spawnDepth": 1})["model"] == ""

    def test_stopped_by_user(self):
        assert parse_meta({"stoppedByUser": True})["stopped_by_user"] is True

    def test_empty_meta_defaults_to_depth_one(self):
        assert parse_meta({})["spawn_depth"] == 1


class TestSubagentsDir:
    """The subagents folder sits beside the session transcript."""

    def test_path_shape(self, tmp_path, monkeypatch):
        record = make_record(tmp_path, monkeypatch)
        assert subagents_dir(record) == tmp_path / SLUG / SID / "subagents"


class TestResolvedToolIds:
    """A transcript reports which tool calls already came back."""

    def test_finds_result_ids(self, tmp_path):
        path = tmp_path / "t.jsonl"
        write_transcript(
            tmp_path,
            ".",
            "t",
            [
                assistant_tool("Agent", {"description": "go"}, "toolu_a"),
                tool_result("toolu_a"),
                assistant_tool("Agent", {"description": "wait"}, "toolu_b"),
            ],
        )
        path = tmp_path / "." / "t.jsonl"
        ids = read_resolved_tool_ids(path)
        assert ids == {"toolu_a"}

    def test_missing_file_is_empty(self, tmp_path):
        assert read_resolved_tool_ids(tmp_path / "nope.jsonl") == set()

    def test_torn_lines_are_skipped(self, tmp_path):
        path = tmp_path / "t.jsonl"
        path.write_text(json.dumps(tool_result("toolu_a")) + "\n{\"tool_result\"\n")
        assert read_resolved_tool_ids(path) == {"toolu_a"}


class TestModelFromTranscript:
    """A model id can be recovered from the agent transcript itself."""

    def test_reads_the_first_assistant_model(self, tmp_path):
        path = tmp_path / "a.jsonl"
        path.write_text(
            "\n".join(
                json.dumps(e)
                for e in [
                    {"type": "attachment", "attachment": {}},
                    agent_assistant("hi", "claude-sonnet-5"),
                ]
            )
            + "\n"
        )
        assert read_model_from_transcript(path) == "sonnet"

    def test_no_assistant_event(self, tmp_path):
        path = tmp_path / "a.jsonl"
        path.write_text(json.dumps({"type": "attachment"}) + "\n")
        assert read_model_from_transcript(path) == ""

    def test_missing_file(self, tmp_path):
        assert read_model_from_transcript(tmp_path / "nope.jsonl") == ""


class TestAgentStore:
    """The store derives each agent's state from its parent transcript."""

    def test_absent_subagents_dir_is_silent(self, tmp_path, monkeypatch):
        record = make_record(tmp_path, monkeypatch)
        write_transcript(tmp_path, SLUG, SID, [assistant_text("no agents here")])
        assert AgentStore().poll(record, now=1000.0) == []

    def test_empty_subagents_dir_is_silent(self, tmp_path, monkeypatch):
        record = make_record(tmp_path, monkeypatch)
        write_transcript(tmp_path, SLUG, SID, [assistant_text("hi")])
        (tmp_path / SLUG / SID / "subagents").mkdir(parents=True)
        assert AgentStore().poll(record, now=1000.0) == []

    def test_done_when_the_parent_holds_the_tool_result(self, tmp_path, monkeypatch):
        record = make_record(tmp_path, monkeypatch)
        write_transcript(
            tmp_path,
            SLUG,
            SID,
            [
                assistant_tool("Agent", {"description": "go"}, "toolu_a"),
                tool_result("toolu_a"),
            ],
        )
        write_agent(tmp_path, SLUG, SID, "a1", [agent_assistant("done")],
                    tool_use_id="toolu_a", jsonl_mtime=100.0)
        agents = AgentStore().poll(record, now=10_000.0)
        assert len(agents) == 1
        assert agents[0].state == STATE_DONE
        assert agents[0].glyph == "✓"
        assert agents[0].is_running is False

    def test_running_when_unresolved_and_fresh(self, tmp_path, monkeypatch):
        record = make_record(tmp_path, monkeypatch)
        write_transcript(tmp_path, SLUG, SID,
                         [assistant_tool("Agent", {"description": "go"}, "toolu_a")])
        write_agent(tmp_path, SLUG, SID, "a1", [agent_assistant("working")],
                    tool_use_id="toolu_a", jsonl_mtime=1000.0)
        agents = AgentStore().poll(record, now=1010.0)
        assert agents[0].state == STATE_RUNNING
        assert agents[0].is_running is True
        assert agents[0].glyph == "⚙"

    def test_stalled_when_unresolved_and_stale(self, tmp_path, monkeypatch):
        record = make_record(tmp_path, monkeypatch)
        write_transcript(tmp_path, SLUG, SID,
                         [assistant_tool("Agent", {"description": "go"}, "toolu_a")])
        write_agent(tmp_path, SLUG, SID, "a1", [agent_assistant("stuck")],
                    tool_use_id="toolu_a", jsonl_mtime=1000.0)
        agents = AgentStore().poll(record, now=1000.0 + 500)
        assert agents[0].state == STATE_STALLED
        assert agents[0].is_running is False

    def test_stopped_by_user(self, tmp_path, monkeypatch):
        record = make_record(tmp_path, monkeypatch)
        write_transcript(tmp_path, SLUG, SID,
                         [assistant_tool("Agent", {"description": "go"}, "toolu_a")])
        write_agent(tmp_path, SLUG, SID, "a1", [agent_assistant("halted")],
                    tool_use_id="toolu_a", stopped_by_user=True, jsonl_mtime=1000.0)
        assert AgentStore().poll(record, now=1010.0)[0].state == STATE_STOPPED

    def test_meta_without_a_tool_use_id_is_never_running(self, tmp_path, monkeypatch):
        record = make_record(tmp_path, monkeypatch)
        write_transcript(tmp_path, SLUG, SID, [assistant_text("hi")])
        write_agent(tmp_path, SLUG, SID, "a1", [agent_assistant("orphan")],
                    tool_use_id=None, jsonl_mtime=1000.0)
        assert AgentStore().poll(record, now=1001.0)[0].state == STATE_STALLED

    def test_running_flips_to_done_when_the_result_lands(self, tmp_path, monkeypatch):
        record = make_record(tmp_path, monkeypatch)
        events = [assistant_tool("Agent", {"description": "go"}, "toolu_a")]
        write_transcript(tmp_path, SLUG, SID, events)
        write_agent(tmp_path, SLUG, SID, "a1", [agent_assistant("working")],
                    tool_use_id="toolu_a", jsonl_mtime=1000.0)
        store = AgentStore()
        assert store.poll(record, now=1010.0)[0].state == STATE_RUNNING

        write_transcript(tmp_path, SLUG, SID, [*events, tool_result("toolu_a")])
        os.utime(record.transcript_path, (2000.0, 2000.0))
        assert store.poll(record, now=1020.0)[0].state == STATE_DONE

    def test_done_never_flips_back(self, tmp_path, monkeypatch):
        record = make_record(tmp_path, monkeypatch)
        write_transcript(tmp_path, SLUG, SID,
                         [assistant_tool("Agent", {"description": "go"}, "toolu_a"),
                          tool_result("toolu_a")])
        write_agent(tmp_path, SLUG, SID, "a1", [agent_assistant("done")],
                    tool_use_id="toolu_a", jsonl_mtime=1000.0)
        store = AgentStore()
        assert store.poll(record, now=1010.0)[0].state == STATE_DONE
        write_transcript(tmp_path, SLUG, SID,
                         [assistant_tool("Agent", {"description": "go"}, "toolu_a")])
        os.utime(record.transcript_path, (3000.0, 3000.0))
        assert store.poll(record, now=9999.0)[0].state == STATE_DONE

    def test_nested_agent_resolves_against_its_parent_agent(self, tmp_path, monkeypatch):
        record = make_record(tmp_path, monkeypatch)
        write_transcript(tmp_path, SLUG, SID,
                         [assistant_tool("Agent", {"description": "outer"}, "toolu_a")])
        # The parent agent spawned a child and already got its result back.
        write_agent(tmp_path, SLUG, SID, "a1",
                    [assistant_tool("Agent", {"description": "inner"}, "toolu_b"),
                     tool_result("toolu_b")],
                    tool_use_id="toolu_a", spawn_depth=1, jsonl_mtime=1000.0,
                    meta_mtime=10.0)
        write_agent(tmp_path, SLUG, SID, "a2", [agent_assistant("child work")],
                    tool_use_id="toolu_b", spawn_depth=2, parent_agent_id="a1",
                    jsonl_mtime=1000.0, meta_mtime=20.0)
        agents = AgentStore().poll(record, now=99_999.0)
        by_id = {a.agent_id: a for a in agents}
        # The outer agent is unresolved and stale; the inner one finished.
        assert by_id["a1"].state == STATE_STALLED
        assert by_id["a2"].state == STATE_DONE
        assert by_id["a2"].spawn_depth == 2
        assert by_id["a2"].indent == "  "

    def test_model_falls_back_to_the_transcript(self, tmp_path, monkeypatch):
        record = make_record(tmp_path, monkeypatch)
        write_transcript(tmp_path, SLUG, SID, [assistant_text("hi")])
        write_agent(tmp_path, SLUG, SID, "a1",
                    [agent_assistant("hi", "claude-haiku-4-5-20251001")],
                    tool_use_id="toolu_a", model=None, jsonl_mtime=1000.0)
        assert AgentStore().poll(record, now=1010.0)[0].model == "haiku"

    def test_order_follows_meta_mtime_and_is_stable(self, tmp_path, monkeypatch):
        record = make_record(tmp_path, monkeypatch)
        write_transcript(tmp_path, SLUG, SID, [assistant_text("hi")])
        write_agent(tmp_path, SLUG, SID, "third", [agent_assistant("c")],
                    tool_use_id="t3", meta_mtime=300.0, jsonl_mtime=1000.0)
        write_agent(tmp_path, SLUG, SID, "first", [agent_assistant("a")],
                    tool_use_id="t1", meta_mtime=100.0, jsonl_mtime=9000.0)
        write_agent(tmp_path, SLUG, SID, "second", [agent_assistant("b")],
                    tool_use_id="t2", meta_mtime=200.0, jsonl_mtime=5000.0)
        store = AgentStore()
        first = [a.agent_id for a in store.poll(record, now=1000.0)]
        assert first == ["first", "second", "third"]
        # A running agent's transcript keeps growing; the order must not move.
        os.utime(tmp_path / SLUG / SID / "subagents" / "agent-first.jsonl",
                 (99_999.0, 99_999.0))
        assert [a.agent_id for a in store.poll(record, now=1001.0)] == first

    def test_description_falls_back_to_the_agent_type(self, tmp_path, monkeypatch):
        record = make_record(tmp_path, monkeypatch)
        write_transcript(tmp_path, SLUG, SID, [assistant_text("hi")])
        write_agent(tmp_path, SLUG, SID, "a1", [agent_assistant("x")],
                    description="", agent_type="Explore", tool_use_id="t",
                    jsonl_mtime=1000.0)
        assert AgentStore().poll(record, now=1010.0)[0].description == "Explore"

    def test_a_broken_meta_file_is_skipped(self, tmp_path, monkeypatch):
        record = make_record(tmp_path, monkeypatch)
        write_transcript(tmp_path, SLUG, SID, [assistant_text("hi")])
        write_agent(tmp_path, SLUG, SID, "good", [agent_assistant("x")],
                    tool_use_id="t", meta_mtime=100.0, jsonl_mtime=1000.0)
        folder = tmp_path / SLUG / SID / "subagents"
        (folder / "agent-bad.meta.json").write_text("{not json")
        (folder / "agent-bad.jsonl").write_text("")
        agents = AgentStore().poll(record, now=1010.0)
        assert [a.agent_id for a in agents] == ["good"]
