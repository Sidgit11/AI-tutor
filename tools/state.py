#!/usr/bin/env python3
"""state.py - the only sanctioned way to mutate the AI-Tutor student model.

Every write is validated against SPEC section 4 before it lands; a violation is
refused and nothing is written. Timestamps are read from the system clock and
never accepted from the caller. Files are replaced atomically. Every successful
command prints the JSON it wrote.

Run `state.py <group> --help` for a group's flags.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone

KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PHASES = ["review", "teach", "rep", "build", "grade", "close"]
GATE_STATUS = ["pending", "locked", "passed"]


# --- Schemas: SPEC section 4, transcribed exactly. Objects are closed - every
# --- key listed is required, and no key outside the list is allowed at any depth.
def S(t, **kw):
    kw["t"] = t
    return kw


STR, NSTR, BOOL = S("str"), S("str", null=True), S("bool")

PASSFAIL = S("enum", values=["pass", "fail"])

VERDICT = S("obj", fields={
    "rubric": STR, "graded_at": STR, "model": STR,
    "criteria": S("arr", item=S("obj", fields={
        "id": STR, "verdict": PASSFAIL, "evidence": STR})),
    "overall": PASSFAIL,
    "highest_leverage_gap": STR,
    "regrade_of": NSTR,
})

MASTERY = S("obj", fields={
    "meta": S("obj", fields={
        "created": STR, "baseline": STR,
        "pace_hours_per_week": STR, "current_module": STR}),
    "concepts": S("map", value=S("obj", fields={
        "mastery": S("num", min=0.0, max=1.0),
        "last_touched": NSTR, "next_review": NSTR,
        "evidence": S("arr", item=STR), "misconceptions": S("arr", item=STR)})),
    "gates": S("map", value=S("obj", fields={
        "status": S("enum", values=GATE_STATUS),
        "verdicts": S("arr", item=VERDICT)})),
    "escalations": S("arr", item=S("obj", fields={
        "date": STR, "concept": S("str", kebab=True),
        "rung": S("int", min=1, max=4)})),
    "mode_counts": S("obj", fields={
        "reps_unassisted": S("int", min=0), "builds_assisted": S("int", min=0)}),
    "streak": S("obj", fields={
        "count": S("int", min=0), "frozen": BOOL, "last_session": NSTR}),
})

STATE = S("obj", fields={
    "session": S("obj", fields={
        "active": BOOL, "started_at": NSTR,
        "planned_minutes": S("int", min=1, null=True), "module": NSTR,
        "phase": S("enum", values=PHASES, null=True), "checkpoint": NSTR}),
    "parking_lot": S("arr", item=S("obj", fields={"item": STR, "added": STR})),
    "last_closed": NSTR,
})

BLANK_CONCEPT = {"mastery": 0.0, "last_touched": None, "next_review": None,
                 "evidence": [], "misconceptions": []}


# --- Validator ---
class Invalid(Exception):
    pass


class CliError(Exception):
    pass


def describe(n):
    t = n["t"]
    if t == "enum":
        s = "one of: " + ", ".join(n["values"])
    elif t == "obj":
        s = "object with exactly the keys: " + ", ".join(n["fields"])
    elif t == "arr":
        s = "array of " + describe(n["item"])
    elif t == "num":
        s = "number in [%s, %s]" % (n["min"], n["max"])
    elif t == "int":
        s = "integer in [%s, %s]" % (n.get("min", "-inf"), n.get("max", "inf"))
    else:
        s = {"str": "string", "bool": "boolean",
             "map": "object keyed by kebab-case id"}[t]
    return (s + ", or null") if n.get("null") else s


def typename(v):
    return {bool: "boolean", int: "integer", float: "number", str: "string",
            list: "array", dict: "object", type(None): "null"}.get(
                type(v), type(v).__name__)


def validate(node, v, path):
    """Raise Invalid naming the offending path and what was expected."""
    t = node["t"]

    def bad(got=None):
        raise Invalid("%s - expected %s, got %s" % (
            path, describe(node), got or "%s (%r)" % (typename(v), v)))

    if v is None:
        if not node.get("null"):
            bad("null")
        return
    if t == "obj":
        if not isinstance(v, dict):
            bad()
        for k in v:
            if k not in node["fields"]:
                raise Invalid(
                    "%s.%s - unknown key. The schema defines exactly: %s. SPEC section 4 "
                    "is the contract: no key may be added at any nesting level, for any "
                    "reason. Anything with no home in the schema goes in the journal."
                    % (path, k, ", ".join(node["fields"])))
        for k, sub in node["fields"].items():
            if k not in v:
                raise Invalid("%s.%s - missing required key (expected %s)"
                              % (path, k, describe(sub)))
            validate(sub, v[k], "%s.%s" % (path, k))
    elif t == "map":
        if not isinstance(v, dict):
            bad()
        for k, sub in v.items():
            if not KEBAB.match(k):
                raise Invalid("%s.%s - key must be kebab-case (lowercase letters, "
                              "digits, single hyphens), e.g. async-python" % (path, k))
            validate(node["value"], sub, "%s.%s" % (path, k))
    elif t == "arr":
        if not isinstance(v, list):
            bad()
        for i, item in enumerate(v):
            validate(node["item"], item, "%s[%d]" % (path, i))
    elif t == "enum":
        if v not in node["values"]:
            bad()
    elif t == "str":
        if not isinstance(v, str):
            bad()
        if node.get("kebab") and not KEBAB.match(v):
            raise Invalid("%s - %r must be kebab-case, e.g. tool-calling" % (path, v))
    elif t == "bool":
        if not isinstance(v, bool):
            bad()
    else:  # int, num
        ok = isinstance(v, int) if t == "int" else isinstance(v, (int, float))
        if isinstance(v, bool) or not ok:
            bad()
        if ("min" in node and v < node["min"]) or ("max" in node and v > node["max"]):
            raise Invalid("%s - %r is out of range; expected %s"
                          % (path, v, describe(node)))


# --- Clock and atomic IO ---
def now():
    """UTC ISO-8601 with explicit Z. The only source of timestamps."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        raise CliError("%s does not exist (wrong --root?)" % path)
    except ValueError as e:
        raise CliError("%s is not valid JSON: %s" % (path, e))


def save(path, data, schema, name):
    """Validate, then write via temp file + rename so a crash cannot corrupt."""
    validate(schema, data, name)
    directory = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".%s." % name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def emit(name, what, fragment):
    print("wrote %s - %s" % (name, what))
    print(json.dumps(fragment, indent=2))
    return 0


class Ctx(object):
    """Where the two state files live, and how they are read and written."""

    def __init__(self, root):
        self.mastery = os.path.join(root, "student", "mastery.json")
        self.state = os.path.join(root, "student", "state.json")

    def load_mastery(self): return load(self.mastery)
    def load_state(self): return load(self.state)
    def save_mastery(self, m): save(self.mastery, m, MASTERY, "mastery.json")
    def save_state(self, s): save(self.state, s, STATE, "state.json")


def kebab_or_die(field, value):
    if not KEBAB.match(value):
        raise CliError("%s %r is not kebab-case. Use lowercase letters, digits and "
                       "single hyphens, e.g. async-python, tool-calling." % (field, value))
    return value


# --- Commands ---
def cmd_session(a, c):
    st = c.load_state()
    s = st["session"]
    if a.op == "open":
        s.update(active=True, started_at=now(), planned_minutes=a.minutes,
                 module=a.module, phase=a.phase, checkpoint=a.checkpoint)
        what = "session opened"
    elif a.op == "checkpoint":
        s["checkpoint"] = a.text
        what = "checkpoint updated"
    elif a.op == "phase":
        s["phase"] = a.name
        what = "phase set"
    else:  # close
        s.update(active=False, phase="close", checkpoint=a.checkpoint)
        st["last_closed"] = now()
        what = "session closed"
    c.save_state(st)
    return emit("state.json", what, {"session": s, "last_closed": st["last_closed"]})


def cmd_park(a, c):
    st = c.load_state()
    lot = st["parking_lot"]
    if a.op == "list":
        if not lot:
            print("parking_lot is empty")
        for i, e in enumerate(lot, 1):
            print("[%d] %s  (added %s)" % (i, e["item"], e["added"]))
        return 0
    if a.op == "add":
        lot.append({"item": a.item, "added": now()})
        what = "parked item %d" % len(lot)
    else:  # clear
        if not 1 <= a.index <= len(lot):
            raise CliError("park clear: index %d out of range; parking_lot has %d "
                           "entries (indices are 1-based, as shown by `park list`)"
                           % (a.index, len(lot)))
        removed = lot.pop(a.index - 1)
        what = "cleared parked item: %s" % removed["item"]
    c.save_state(st)
    return emit("state.json", what, {"parking_lot": lot})


def cmd_concept(a, c):
    if getattr(a, "next_review", None) is not None:
        raise CliError("next_review is the examiner's field (v0.2) and this tool "
                       "refuses to write it. Leave it null.")
    cid = kebab_or_die("concept id", a.id)
    m = c.load_mastery()
    created = cid not in m["concepts"]
    if created:
        m["concepts"][cid] = dict(BLANK_CONCEPT)
        m["concepts"][cid]["evidence"] = []
        m["concepts"][cid]["misconceptions"] = []
    entry = m["concepts"][cid]
    if a.op == "touch":
        entry["mastery"] = a.mastery
        entry["last_touched"] = today()
        entry["evidence"].extend(a.evidence or [])
        what = "concept %s %s" % (cid, "created and touched" if created else "touched")
    else:  # misconception
        entry["misconceptions"].append(a.text)
        entry["last_touched"] = today()
        what = "misconception logged on %s%s" % (cid, " (entry created)" if created else "")
    c.save_mastery(m)
    out = emit("mastery.json", what, {cid: entry})
    if a.op == "misconception":
        print("note: mirror recurring patterns into student/misconceptions.md by hand.")
    return out


def cmd_escalation(a, c):
    cid = kebab_or_die("concept id", a.concept)
    m = c.load_mastery()
    row = {"date": today(), "concept": cid, "rung": a.rung}
    m["escalations"].append(row)
    c.save_mastery(m)
    return emit("mastery.json", "escalation logged", row)


def cmd_streak(a, c):
    m = c.load_mastery()
    s = m["streak"]
    prior = s["count"]
    if a.op == "increment":
        s["count"] = prior + 1
        s["last_session"] = now()
        what = "streak incremented"
    elif a.op == "freeze":
        s["frozen"] = True
        what = "streak frozen"
    elif a.op == "unfreeze":
        s["frozen"] = False
        what = "streak unfrozen"
    else:  # clear
        s["count"] = 0
        what = "streak cleared"
    c.save_mastery(m)
    out = emit("mastery.json", what, {"streak": s})
    if a.op == "clear":
        print("ACTION REQUIRED: the schema has nowhere to record why a streak was "
              "cleared. Write to today's journal entry: prior count was %d; reason: %s"
              % (prior, a.reason))
    return out


def cmd_mode(a, c):
    key = "reps_unassisted" if a.op == "rep-unassisted" else "builds_assisted"
    m = c.load_mastery()
    m["mode_counts"][key] += 1
    c.save_mastery(m)
    return emit("mastery.json", "%s incremented" % key, {"mode_counts": m["mode_counts"]})


def cmd_gate(a, c):
    m = c.load_mastery()
    if a.module not in m["gates"]:
        raise CliError("no gate %r in mastery.json. Known gates: %s. This tool does not "
                       "create gates." % (a.module, ", ".join(m["gates"])))
    gate = m["gates"][a.module]
    if a.op == "status":
        if a.status not in GATE_STATUS:
            raise CliError(
                "gates.%s.status - %r is not a valid status. SPEC section 4 enumerates "
                "exactly: %s. There is no 'failed' status: a failing verdict is recorded "
                "in gates.%s.verdicts[] with overall='fail', and the gate stays 'pending'."
                % (a.module, a.status, ", ".join(GATE_STATUS), a.module))
        gate["status"] = a.status
        c.save_mastery(m)
        return emit("mastery.json", "gate %s status set" % a.module,
                    {a.module: {"status": gate["status"],
                                "verdicts": "<%d unchanged>" % len(gate["verdicts"])}})
    # verdict
    verdict = load(a.file)
    if not isinstance(verdict, dict):
        raise CliError("%s - expected a single verdict object, got %s"
                       % (a.file, typename(verdict)))
    verdict = dict(verdict)
    verdict["graded_at"] = now()          # stamped here, never taken from the file
    validate(VERDICT, verdict, "verdict(%s)" % a.file)
    verdict = dict((k, verdict[k]) for k in VERDICT["fields"])  # canonical key order
    gate["verdicts"].append(verdict)
    c.save_mastery(m)
    out = emit("mastery.json", "verdict appended to gates.%s.verdicts[%d]"
               % (a.module, len(gate["verdicts"]) - 1), verdict)
    if verdict["overall"] == "pass":
        print("note: gate status is unchanged. Clear it with `gate status %s passed` "
              "only once the portfolio write-up is also done." % a.module)
    else:
        print("note: gate status unchanged (a fail never changes status).")
    return out


def cmd_meta(a, c):
    m = c.load_mastery()
    if a.module not in m["gates"]:
        raise CliError("no gate %r in mastery.json; current_module must name a gate. "
                       "Known: %s" % (a.module, ", ".join(m["gates"])))
    m["meta"]["current_module"] = a.module
    c.save_mastery(m)
    return emit("mastery.json", "current_module set", {"meta": m["meta"]})


def cmd_verify(a, c):
    bad = []
    for path, schema, name in ((c.mastery, MASTERY, "mastery.json"),
                               (c.state, STATE, "state.json")):
        try:
            validate(schema, load(path), name)
            print("ok   %s" % path)
        except (Invalid, CliError) as e:
            bad.append(str(e))
            print("FAIL %s" % path)
    for e in bad:
        sys.stderr.write("schema violation: %s\n" % e)
    return 1 if bad else 0


# --- CLI ---
EPILOG = """\
groups:
  session open|checkpoint|phase|close    session lifecycle in state.json
  park <text> | add | list | clear       parking lot (always {item, added})
  concept touch|misconception            concepts in mastery.json
  escalation log                         escalation ladder rungs
  streak increment|freeze|unfreeze|clear
  mode rep-unassisted|build-assisted     mode_counts
  gate status|verdict                    gates.<module>
  meta current-module                    meta.current_module
  verify                                 validate both files; run at open and close

rules this tool enforces (SPEC section 4):
  * no key that the schema does not define, at any nesting level
  * every enum value checked; gate status is pending|locked|passed only
  * arrays of objects keep their shape (parking_lot, escalations, verdicts)
  * concept ids are kebab-case; next_review is examiner-owned and unwritable
  * all timestamps are generated here (UTC ISO-8601, Z); none are accepted
  * writes are atomic and print what landed
"""


def build_parser():
    p = argparse.ArgumentParser(
        prog="state.py", formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Validated, atomic writer for student/mastery.json and "
                    "student/state.json. The only sanctioned way to mutate them.",
        epilog=EPILOG)
    p.add_argument("--root", metavar="DIR",
                   help="campus root containing student/ (default: this repo). "
                        "May appear anywhere on the command line.")
    sub = p.add_subparsers(dest="group")

    def group(name, fn, helptext):
        """Add a command group; return its sub-subcommand factory."""
        sp = sub.add_parser(name, help=helptext)
        sp.set_defaults(fn=fn)
        return sp.add_subparsers(dest="op").add_parser

    so = group("session", cmd_session, "open, checkpoint, re-phase or close a session")
    q = so("open", help="set active, stamp started_at from the clock")
    q.add_argument("--minutes", type=int, required=True, help="planned_minutes")
    q.add_argument("--module", required=True, help="e.g. 00-bootstrap")
    q.add_argument("--phase", required=True, choices=PHASES)
    q.add_argument("--checkpoint", required=True, help="one sentence resume point")
    q = so("checkpoint", help="update session.checkpoint")
    q.add_argument("text")
    q = so("phase", help="update session.phase")
    q.add_argument("name", choices=PHASES)
    q = so("close", help="set active false, stamp last_closed")
    q.add_argument("--checkpoint", required=True, help="closing summary line")

    so = group("park", cmd_park, 'park "<item text>" | list | clear <index>')
    q = so("add", help="append {item, added}; `park \"text\"` also works")
    q.add_argument("item")
    so("list", help="print the parking lot with 1-based indices")
    q = so("clear", help="remove one entry by 1-based index")
    q.add_argument("index", type=int)

    so = group("concept", cmd_concept, "touch a concept or log a misconception")
    q = so("touch", help="create if absent, set mastery, append evidence")
    q.add_argument("id", help="kebab-case, e.g. tool-calling")
    q.add_argument("--mastery", type=float, required=True, help="0.0-1.0")
    q.add_argument("--evidence", action="append", metavar="TEXT",
                   help="short factual string; repeatable")
    q.add_argument("--next-review", metavar="X",  # accepted only to refuse it loudly
                   help="REFUSED: examiner-owned (v0.2). Exists only to say so precisely.")
    q = so("misconception", help="append to a concept's misconceptions")
    q.add_argument("id")
    q.add_argument("text")

    so = group("escalation", cmd_escalation, "log an escalation-ladder rung")
    q = so("log", help="append {date, concept, rung}")
    q.add_argument("--concept", required=True)
    q.add_argument("--rung", type=int, required=True, choices=[1, 2, 3, 4])

    so = group("streak", cmd_streak, "increment, freeze, unfreeze or clear the streak")
    so("increment", help="count +1, stamp last_session")
    so("freeze", help="frozen = true (student declared a break)")
    so("unfreeze", help="frozen = false")
    q = so("clear", help="count = 0 (student's explicit request only)")
    q.add_argument("--reason", required=True)

    so = group("mode", cmd_mode, "increment mode_counts")
    so("rep-unassisted", help="mode_counts.reps_unassisted +1")
    so("build-assisted", help="mode_counts.builds_assisted +1")

    so = group("gate", cmd_gate, "set a gate's status or append a grader verdict")
    q = so("status", help="pending | locked | passed (no other value)")
    q.add_argument("module")
    q.add_argument("status", metavar="{pending,locked,passed}")
    q = so("verdict", help="validate a verdict file and append it")
    q.add_argument("module")
    q.add_argument("--file", required=True,
                   help="path to verdict.json; graded_at is stamped by this tool")

    so = group("meta", cmd_meta, "meta fields")
    q = so("current-module", help="advance meta.current_module")
    q.add_argument("module")

    sub.add_parser("verify", help="validate both files; non-zero if either is invalid"
                   ).set_defaults(fn=cmd_verify, op="verify")
    return p, sub


def _extract_root(argv):
    """Pull --root out of argv wherever it appears; return (root, rest)."""
    root, rest, i = None, [], 0
    while i < len(argv):
        a = argv[i]
        if a == "--root":
            if i + 1 >= len(argv):
                raise CliError("--root needs a directory")
            root, i = argv[i + 1], i + 2
        elif a.startswith("--root="):
            root, i = a.split("=", 1)[1], i + 1
        else:
            rest.append(a)
            i += 1
    return root, rest


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        root, argv = _extract_root(argv)
    except CliError as e:
        sys.stderr.write("error: %s\n" % e)
        return 1
    # `park "text"` is shorthand for `park add "text"`
    if len(argv) > 1 and argv[0] == "park" and argv[1] not in ("add", "list", "clear",
                                                               "-h", "--help"):
        argv = ["park", "add"] + argv[1:]

    parser, sub = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "fn", None):
        parser.print_help(sys.stderr)
        return 2
    if args.op is None:  # group given without a subcommand
        sub.choices[args.group].print_help(sys.stderr)
        return 2
    if root is None:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        return args.fn(args, Ctx(root))
    except Invalid as e:
        sys.stderr.write("REFUSED - schema violation, nothing was written.\n%s\n" % e)
        return 1
    except CliError as e:
        sys.stderr.write("REFUSED - %s\n" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
