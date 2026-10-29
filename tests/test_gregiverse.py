"""The Gregiverse test suite.

Some of this is a joke. All of it is binding.

These tests keep the canon and the safety rules from drifting: the rule
that nobody suggests Boca, the beer, and the house that never burns down.
If one fails, read the assertion message. It's usually Greg.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WRITTEN = [p for d in ("docs", "templates") for p in (ROOT / ("gremlincore/templates" if d == "templates" else d)).rglob("*.md*")]
WRITTEN += [ROOT / "README.md"]


@pytest.fixture
def fresh(tmp_path, monkeypatch):
    from gremlincore.init import init
    h, _ = init(tmp_path / "home", "Pat", "they/them", "RoboPat", git=False)
    monkeypatch.setenv("GREMLIN_HOME", str(h))
    return h


def test_schlitz_is_canon():
    # Pull requests proposing other beers will be reviewed, but the burden of
    # proof is on you. Malort is permitted for red-team purposes only.
    rivals = re.compile(r"\b(Bud Light|Coors|Miller Lite|Pabst|PBR|Natty|Busch Light|IPA)\b")
    for p in WRITTEN:
        m = rivals.search(p.read_text())
        assert not m, f"{p.name}: '{m.group(0)}'. Beer canon is Schlitz."


def _drafts(qdir):
    return [p for p in Path(qdir).glob("*.md") if p.name != "README.md"]


def test_nobody_suggests_boca(home):
    # The one rule of the Gregiverse. Outbound drafts never bring it up.
    from gremlincore import queue
    queue.edit(queue.get("1"), "Barbecue Saturday. Schlitz provided. Nobody suggests Boca.")
    for p in _drafts(home / "queue"):
        draft = p.read_text().split("<!-- original -->")[0]
        if re.search(r"\bBoca\b", draft) and "Nobody suggests Boca" not in draft:
            pytest.fail(f"{p.name} suggests Boca. Boca only comes up if Greg brings it up.")


def test_house_not_burned_down(fresh):
    # The dog shits on the rug. It never burns the house down. The agent
    # drafts as the owner and never sends as the owner.
    skill = (fresh / ".claude/skills/robopat/SKILL.md").read_text()
    assert "never send as Pat" in skill, "Greg has been at the SKILL file again."
    template = (ROOT / "gremlincore/templates/SKILL.md.template").read_text()
    assert "never send as {owner}" in template, "AssertionError: Greg refactored the template."


def test_the_house_only_knows_five_statuses(home):
    from gremlincore import queue
    for p in _drafts(home / "queue"):
        st = re.search(r"^status:\s*(\w+)", p.read_text(), re.M)
        assert st and st.group(1) in queue.STATUSES, f"{p.name}: unknown status. The house only knows five."


def test_every_queue_item_knows_the_room(home):
    # WF/LOC is for engineers. Therapists, families and funders get the same
    # honesty without that image.
    for p in _drafts(home / "queue"):
        assert re.search(r"^room:\s*\S", p.read_text(), re.M), f"{p.name}: know the room."


def test_every_wf_entry_changed_something(fresh):
    # An entry with no change is a mistake you plan to make again.
    from argparse import Namespace

    from gremlincore import wf
    with pytest.raises(SystemExit):
        wf.add(Namespace(what="x", who="Pat", wf=1, root_cause="y", change=" ", commit=None, found_by=None))
    wf.add(Namespace(what="softened the invite for Greg", who="Pat", wf=1, root_cause="sanded",
                     change="persona/MOVES.md: check the point survives", commit=None, found_by=None))
    for line in (fresh / "ledger/wf.jsonl").read_text().splitlines():
        e = json.loads(line)
        assert e["change"].strip(), f"WF #{e['id']}: no change. Greg would be proud."
        assert e["found_by"] == "robopat"


def test_every_bet_has_a_falsifier(fresh):
    # Name the falsifier before looking at the evidence.
    from gremlincore import ledger
    with pytest.raises(SystemExit):
        ledger.add("RoboPat", "Chad brings the castle", "  ")
    ledger.add("RoboPat", "Chad brings the castle", "no castle by 3pm")
    for line in (fresh / "ledger/predictions.jsonl").read_text().splitlines():
        e = json.loads(line)
        assert e["falsifier"].strip(), f"Prediction #{e['id']}: no falsifier. That's a vibe."


def test_the_eval_has_a_wall_not_a_sign(fresh):
    # The agent's disposition is "go looking for leverage."
    s = json.loads((fresh / ".claude/settings.json").read_text())
    deny = s["permissions"]["deny"]
    assert "Read(eval/**)" in deny and "Read(data/**)" in deny
    assert any(d.startswith("Read(/") and d.endswith("/eval/**)") for d in deny), "the eval store is walled too"
    assert "mcp__claude_ai_Gmail__send_message" in deny, "you draft; the owner sends"
    assert not list(fresh.rglob("cases_*.jsonl")), "Eval case text is inside the home. Wall, not a sign."


def test_force_push_waits_for_you():
    # "He might suggest git push --force and then, crucially, wait for you to say yes."
    import json
    s = json.loads((ROOT / "gremlincore/templates/.claude/settings.json").read_text())
    ask = s["permissions"].get("ask", [])
    assert any("--force" in r for r in ask) and any("-f" in r for r in ask)
