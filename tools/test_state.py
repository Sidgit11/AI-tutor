"""Tests for tools/state.py.

Four of these reproduce real defects the tutor committed while hand-editing JSON,
which prose rules failed to prevent, and prove the tool now refuses them:
  1. an invented key under streak (`reset_note`, then `reset`)
  2. parking-lot entries written as bare strings
  3. gates.<module>.status set to "failed", which SPEC section 4 does not enumerate
  4. a concept entry created without the full schema shape

Run: uv run --with pytest pytest tools/ -q
"""
import io
import json
import os
import sys
from contextlib import redirect_stderr, redirect_stdout

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state  # noqa: E402

PRISTINE_MASTERY = {
    "meta": {"created": "2026-07-29", "baseline": "ships-with-ai-assistance",
             "pace_hours_per_week": "5-10", "current_module": "00-bootstrap"},
    "concepts": {},
    "gates": {"00-bootstrap": {"status": "pending", "verdicts": []},
              "01-floor": {"status": "locked", "verdicts": []}},
    "escalations": [],
    "mode_counts": {"reps_unassisted": 0, "builds_assisted": 0},
    "streak": {"count": 0, "frozen": False, "last_session": None},
}
PRISTINE_STATE = {
    "session": {"active": False, "started_at": None, "planned_minutes": None,
                "module": None, "phase": None, "checkpoint": None},
    "parking_lot": [], "last_closed": None,
}
GOOD_VERDICT = {
    "rubric": "00-bootstrap-gate", "graded_at": "ignored-and-replaced",
    "model": "claude-opus-4-x",
    "criteria": [{"id": "c1", "verdict": "fail", "evidence": "ran the defense, no answer"}],
    "overall": "fail", "highest_leverage_gap": "cannot explain state flow",
    "regrade_of": None,
}


@pytest.fixture
def campus(tmp_path):
    (tmp_path / "student").mkdir()
    write(tmp_path, "mastery.json", PRISTINE_MASTERY)
    write(tmp_path, "state.json", PRISTINE_STATE)
    return tmp_path


def write(root, name, data):
    with open(str(root / "student" / name), "w") as f:
        json.dump(data, f, indent=2)


def read(root, name):
    with open(str(root / "student" / name)) as f:
        return json.load(f)


def run(root, *args):
    """Invoke the CLI in-process; return (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    argv = ["--root", str(root)] + list(args)
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = state.main(argv)
    except SystemExit as e:              # argparse-level rejection
        code = e.code if isinstance(e.code, int) else 1
    return code, out.getvalue(), err.getvalue()


# --------------------------------------------------------------------------- #
# Defect 1: an invented key under streak
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("bogus", ["reset_note", "reset", "cleared_because"])
def test_defect_invented_streak_key_is_rejected(campus, bogus):
    m = json.loads(json.dumps(PRISTINE_MASTERY))
    m["streak"][bogus] = "was 7 before the student asked to clear it"
    write(campus, "mastery.json", m)

    code, _, err = run(campus, "verify")
    assert code == 1
    assert "streak.%s" % bogus in err and "unknown key" in err
    assert "count, frozen, last_session" in err

    # and no mutating command will land on top of it either
    code, _, err = run(campus, "streak", "increment")
    assert code == 1 and "streak.%s" % bogus in err
    assert read(campus, "mastery.json")["streak"]["count"] == 0


def test_unknown_key_rejected_at_every_nesting_level(campus):
    m = json.loads(json.dumps(PRISTINE_MASTERY))
    m["concepts"]["tool-calling"] = dict(
        mastery=0.3, last_touched=None, next_review=None, evidence=[],
        misconceptions=[], confidence="high")
    write(campus, "mastery.json", m)
    code, _, err = run(campus, "verify")
    assert code == 1
    assert "mastery.json.concepts.tool-calling.confidence" in err


def test_streak_clear_prints_journal_instruction(campus):
    run(campus, "streak", "increment")
    run(campus, "streak", "increment")
    code, out, _ = run(campus, "streak", "clear", "--reason", "student asked")
    assert code == 0
    assert read(campus, "mastery.json")["streak"]["count"] == 0
    assert "journal" in out and "prior count was 2" in out
    assert "student asked" in out


# --------------------------------------------------------------------------- #
# Defect 2: bare-string parking-lot entries
# --------------------------------------------------------------------------- #
def test_defect_bare_string_parking_lot_is_rejected(campus):
    s = json.loads(json.dumps(PRISTINE_STATE))
    s["parking_lot"] = ["finish pass 3 of tool-calling", "pytest sandbox is blocked"]
    write(campus, "state.json", s)
    code, _, err = run(campus, "verify")
    assert code == 1
    assert "parking_lot[0]" in err
    assert "item, added" in err and "got string" in err


def test_park_always_writes_the_object_form(campus):
    code, out, _ = run(campus, "park", "pytest sandbox is blocked")
    assert code == 0
    lot = read(campus, "state.json")["parking_lot"]
    assert list(lot[0]) == ["item", "added"]
    assert lot[0]["item"] == "pytest sandbox is blocked"
    assert "pytest sandbox is blocked" in out          # proof-of-write in transcript

    run(campus, "park", "add", "second item")
    code, out, _ = run(campus, "park", "list")
    assert "[1]" in out and "[2]" in out
    code, _, _ = run(campus, "park", "clear", "1")
    lot = read(campus, "state.json")["parking_lot"]
    assert len(lot) == 1 and lot[0]["item"] == "second item"
    code, _, err = run(campus, "park", "clear", "9")
    assert code == 1 and "out of range" in err


def test_escalations_and_verdicts_also_keep_their_shape(campus):
    m = json.loads(json.dumps(PRISTINE_MASTERY))
    m["escalations"] = ["rung 3 on async-python"]
    write(campus, "mastery.json", m)
    code, _, err = run(campus, "verify")
    assert code == 1 and "escalations[0]" in err and "date, concept, rung" in err


# --------------------------------------------------------------------------- #
# Defect 3: gates.<module>.status = "failed"
# --------------------------------------------------------------------------- #
def test_defect_gate_status_failed_is_rejected(campus):
    before = read(campus, "mastery.json")
    code, _, err = run(campus, "gate", "status", "00-bootstrap", "failed")
    assert code == 1
    assert "pending, locked, passed" in err
    assert "no 'failed' status" in err
    assert read(campus, "mastery.json") == before          # nothing was written

    # and hand-written "failed" is caught by verify too
    m = json.loads(json.dumps(PRISTINE_MASTERY))
    m["gates"]["00-bootstrap"]["status"] = "failed"
    write(campus, "mastery.json", m)
    code, _, err = run(campus, "verify")
    assert code == 1 and "gates.00-bootstrap.status" in err


def test_gate_status_accepts_only_the_three_enumerated_values(campus):
    for good in ("pending", "locked", "passed"):
        assert run(campus, "gate", "status", "00-bootstrap", good)[0] == 0
        assert read(campus, "mastery.json")["gates"]["00-bootstrap"]["status"] == good
    assert run(campus, "gate", "status", "02-nonexistent", "passed")[0] == 1


def test_gate_verdict_validates_before_appending(campus, tmp_path):
    bad = json.loads(json.dumps(GOOD_VERDICT))
    bad["criteria"][0]["verdict"] = "partial"
    p = str(tmp_path / "verdict.json")
    with open(p, "w") as f:
        json.dump(bad, f)
    code, _, err = run(campus, "gate", "verdict", "00-bootstrap", "--file", p)
    assert code == 1 and "criteria[0].verdict" in err and "pass, fail" in err
    assert read(campus, "mastery.json")["gates"]["00-bootstrap"]["verdicts"] == []

    missing = json.loads(json.dumps(GOOD_VERDICT))
    del missing["highest_leverage_gap"]
    with open(p, "w") as f:
        json.dump(missing, f)
    code, _, err = run(campus, "gate", "verdict", "00-bootstrap", "--file", p)
    assert code == 1 and "highest_leverage_gap" in err and "missing required key" in err

    with open(p, "w") as f:
        json.dump(GOOD_VERDICT, f)
    code, out, _ = run(campus, "gate", "verdict", "00-bootstrap", "--file", p)
    assert code == 0
    v = read(campus, "mastery.json")["gates"]["00-bootstrap"]["verdicts"][0]
    assert v["overall"] == "fail"
    assert v["graded_at"] != GOOD_VERDICT["graded_at"]      # stamped by the tool
    assert v["graded_at"].endswith("Z")
    assert read(campus, "mastery.json")["gates"]["00-bootstrap"]["status"] == "pending"


# --------------------------------------------------------------------------- #
# Defect 4: a concept entry created without the full schema shape
# --------------------------------------------------------------------------- #
def test_defect_partial_concept_entry_is_rejected(campus):
    m = json.loads(json.dumps(PRISTINE_MASTERY))
    m["concepts"]["tool-calling"] = {"mastery": 0.3, "evidence": ["taught: pass 1"]}
    write(campus, "mastery.json", m)
    code, _, err = run(campus, "verify")
    assert code == 1
    assert "concepts.tool-calling." in err and "missing required key" in err


def test_concept_touch_creates_the_full_shape_on_first_pass(campus):
    assert read(campus, "mastery.json")["concepts"] == {}
    code, out, _ = run(campus, "concept", "touch", "tool-calling",
                       "--mastery", "0.2", "--evidence", "taught: pass 1 check-gated")
    assert code == 0
    entry = read(campus, "mastery.json")["concepts"]["tool-calling"]
    assert set(entry) == {"mastery", "last_touched", "next_review", "evidence",
                          "misconceptions"}
    assert entry["mastery"] == 0.2
    assert entry["evidence"] == ["taught: pass 1 check-gated"]
    assert entry["next_review"] is None
    assert "tool-calling" in out                            # proof-of-write

    run(campus, "concept", "touch", "tool-calling", "--mastery", "0.4",
        "--evidence", "taught: pass 2 check-gated")
    entry = read(campus, "mastery.json")["concepts"]["tool-calling"]
    assert entry["mastery"] == 0.4 and len(entry["evidence"]) == 2

    run(campus, "concept", "misconception", "async-python", "conflates await with parallel")
    entry = read(campus, "mastery.json")["concepts"]["async-python"]
    assert entry["misconceptions"] == ["conflates await with parallel"]
    assert set(entry) == {"mastery", "last_touched", "next_review", "evidence",
                          "misconceptions"}


def test_mastery_must_be_in_range(campus):
    code, _, err = run(campus, "concept", "touch", "x-y", "--mastery", "1.5")
    assert code == 1 and "out of range" in err and "[0.0, 1.0]" in err
    assert read(campus, "mastery.json")["concepts"] == {}


# --------------------------------------------------------------------------- #
# next_review ban, kebab-case, timestamps, atomicity
# --------------------------------------------------------------------------- #
def test_next_review_cannot_be_written(campus):
    code, _, err = run(campus, "concept", "touch", "tool-calling", "--mastery", "0.3",
                       "--next-review", "2026-08-05")
    assert code == 1 and "next_review" in err and "examiner" in err
    assert read(campus, "mastery.json")["concepts"] == {}
    run(campus, "concept", "touch", "tool-calling", "--mastery", "0.3")
    assert read(campus, "mastery.json")["concepts"]["tool-calling"]["next_review"] is None


@pytest.mark.parametrize("bad_id", ["Tool_Calling", "tool calling", "toolCalling",
                                    "tool--calling", "tool-", "tool_calling"])
def test_kebab_case_is_enforced(campus, bad_id):
    code, _, err = run(campus, "concept", "touch", bad_id, "--mastery", "0.3")
    assert code == 1 and "kebab-case" in err
    code, _, err = run(campus, "escalation", "log", "--concept", bad_id, "--rung", "3")
    assert code == 1 and "kebab-case" in err
    assert read(campus, "mastery.json")["escalations"] == []


def test_timestamps_are_generated_not_accepted(campus):
    run(campus, "session", "open", "--minutes", "90", "--module", "00-bootstrap",
        "--phase", "teach", "--checkpoint", "teach: tool-calling, pass 1 of 3")
    s = read(campus, "state.json")["session"]
    assert s["active"] is True
    assert state.re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", s["started_at"])
    assert s["phase"] == "teach" and s["planned_minutes"] == 90

    # there is no flag by which a caller could supply one
    for flag in ("--started-at", "--last-closed", "--added", "--graded-at", "--date"):
        code, _, _ = run(campus, "session", "open", "--minutes", "30", "--module", "m",
                         "--phase", "teach", "--checkpoint", "c", flag, "2020-01-01")
        assert code == 2, flag

    run(campus, "park", "an item")
    assert read(campus, "state.json")["parking_lot"][0]["added"].endswith("Z")
    run(campus, "escalation", "log", "--concept", "tool-calling", "--rung", "3")
    assert state.re.match(r"^\d{4}-\d{2}-\d{2}$",
                          read(campus, "mastery.json")["escalations"][0]["date"])
    run(campus, "session", "close", "--checkpoint", "closed out")
    st = read(campus, "state.json")
    assert st["session"]["active"] is False and st["last_closed"].endswith("Z")
    assert st["parking_lot"], "close must keep the parking lot"


def test_rejected_write_leaves_the_file_byte_identical_and_no_temp_files(campus):
    path = str(campus / "student" / "mastery.json")
    with open(path, "rb") as f:
        before = f.read()
    assert run(campus, "concept", "touch", "x-y", "--mastery", "3.0")[0] == 1
    with open(path, "rb") as f:
        assert f.read() == before
    assert [p for p in os.listdir(str(campus / "student")) if p.endswith(".tmp")] == []


def test_write_is_atomic_when_the_rename_fails(campus, monkeypatch):
    path = str(campus / "student" / "state.json")
    with open(path, "rb") as f:
        before = f.read()

    def boom(src, dst):
        raise OSError("simulated crash between write and rename")

    monkeypatch.setattr(state.os, "replace", boom)
    with pytest.raises(OSError):
        state.main(["--root", str(campus), "park", "an item"])
    with open(path, "rb") as f:
        assert f.read() == before                     # never a partial file
    assert [p for p in os.listdir(str(campus / "student")) if p.endswith(".tmp")] == []


# --------------------------------------------------------------------------- #
# Whole-loop smoke test
# --------------------------------------------------------------------------- #
def test_full_session_loop_stays_schema_valid(campus, tmp_path):
    p = str(tmp_path / "v.json")
    with open(p, "w") as f:
        json.dump(GOOD_VERDICT, f)
    for cmd in (
        ["session", "open", "--minutes", "90", "--module", "00-bootstrap",
         "--phase", "teach", "--checkpoint", "teach: tool-calling pass 1"],
        ["concept", "touch", "tool-calling", "--mastery", "0.2",
         "--evidence", "taught: pass 1 check-gated"],
        ["session", "phase", "rep"],
        ["session", "checkpoint", "rep 001: test failing on the retry case"],
        ["escalation", "log", "--concept", "tool-calling", "--rung", "3"],
        ["mode", "rep-unassisted"],
        ["concept", "misconception", "tool-calling", "thinks schemas are optional"],
        ["session", "phase", "grade"],
        ["gate", "verdict", "00-bootstrap", "--file", p],
        ["park", "finish pass 3 of tool-calling"],
        ["streak", "increment"],
        ["session", "close", "--checkpoint", "closed: pass 1 done, pass 2-3 parked"],
        ["verify"],
    ):
        code, out, err = run(campus, *cmd)
        assert code == 0, "%s -> %s %s" % (cmd, out, err)
        assert out.strip(), "%s printed nothing; every write must be visible" % cmd
    m = read(campus, "mastery.json")
    assert m["streak"]["count"] == 1 and m["streak"]["last_session"].endswith("Z")
    assert m["mode_counts"]["reps_unassisted"] == 1
    assert len(m["gates"]["00-bootstrap"]["verdicts"]) == 1
