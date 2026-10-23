"""v1 plumbing: queue, ledger, lessons, wake. All against a fixture home
(tests/conftest.py), never a real queue."""
import subprocess

import pytest


def test_queue_lists_and_ages(home):
    from gremlincore import queue
    rows = queue.table()
    assert rows == [("0001", "pending", "email", "Uncle Ray", 8, True)]  # 8 days: stale, make it smaller


def test_veto_needs_a_reason(home):
    from gremlincore import queue
    with pytest.raises(SystemExit):
        queue.veto(queue.get("1"), "  ")
    it = queue.veto(queue.get("1"), "too Greg")
    assert it.meta["status"] == "vetoed" and it.meta["veto_reason"] == "too Greg"
    assert "# pending | approved" in (home / "queue/0001-bbq.md").read_text()  # comments survive


def test_edit_keeps_the_first_original_forever(home):
    from gremlincore import queue
    it = queue.edit(queue.get("1"), "Barbecue Saturday. Schlitz provided.", by="pat")
    it = queue.edit(it, "Barbecue Saturday. Schlitz provided. Nobody suggests Boca.", by="pat")
    assert it.meta["edited_by"] == "pat" and it.meta["status"] == "edited"
    assert it.draft.strip().endswith("Nobody suggests Boca.")
    assert it.original.strip() == "Barbecue Saturday, 3pm, bring a chair."


def test_approve_never_sends_and_sent_dates_the_bet(home):
    from gremlincore import ledger, queue
    queue.approve(queue.get("1"))
    assert ledger.entries()[0]["check_by"] is None
    queue.mark_sent(queue.get("1"))
    e = ledger.entries()[0]
    assert e["sent"] == "2026-10-09" and e["check_by"] == "2026-10-16"


def test_ledger_refuses_a_bet_without_a_falsifier(home):
    from gremlincore import ledger
    with pytest.raises(SystemExit):
        ledger.add("RoboPat", "it'll go great", "")


def test_ledger_due_settle_and_score_split_by_who(home):
    from gremlincore import ledger
    ledger.add("Pat", "RoboPat surprises me", "it doesn't", check_by="2026-10-05")
    assert [e["id"] for e, _ in ledger.due()] == [2]
    ledger.settle(2, "it did", True)
    s = ledger.score()
    assert s["Pat"] == {"bets": 1, "settled": 1, "hits": 1}
    assert s["RoboPat"]["settled"] == 0


def test_only_the_owners_edits_are_lessons(home):
    from gremlincore import lessons, queue
    queue.edit(queue.get("1"), "Pronoun fix only.", by="helper")
    assert lessons.lessons() == []
    queue.edit(queue.get("1"), "Pat's rewrite, with the point still in it.", by="pat")
    ls = lessons.lessons()
    assert len(ls) == 1 and ls[0]["room"] == "families" and ls[0]["changed"] > 0


def test_wf_worthy_veto_proposes_a_wf_line(home):
    from gremlincore import lessons, queue
    queue.veto(queue.get("1"), "you sanded the point down for Ray")
    assert "proposed_wf" in lessons.lessons()[0]


def test_wake_flags_a_stale_status(home):
    from gremlincore import wake
    (home / "persona/X.md").write_text("x")
    subprocess.run(["git", "add", "-A"], cwd=home)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"], cwd=home)
    b = wake.brief()
    if wake.last_change() > "2026-10-01":
        assert b.startswith("!! STATUS IS STALE")
    assert "Queue: 1 pending" in b and "STALE: make it smaller" in b


def test_wf_ledger_lives_in_the_home(home):
    from gremlincore import wf
    assert wf.ledger_path() == home / "ledger/wf.jsonl" and wf.entries() == []


def test_edits_default_to_the_configured_owner(home):
    from gremlincore import queue
    it = queue.edit(queue.get("1"), "Barbecue Saturday. Schlitz provided.")
    assert it.meta["edited_by"] == "pat"


def test_not_the_owner_is_a_wf_worthy_veto(home):
    from gremlincore import lessons, queue
    queue.veto(queue.get("1"), "this is not Pat at all")
    assert "proposed_wf" in lessons.lessons()[0]
    assert "--found-by pat" in lessons.lessons()[0]["proposed_wf"]


def test_wake_closes_with_the_configured_line(home):
    from gremlincore import wake
    assert wake.brief().endswith("What's stuck, and what can I move?")
    with (home / "gremlin.toml").open("a") as f:
        f.write('\n[wake]\nclosing = "Nobody suggests Boca. What else?"\n')
    assert wake.brief().endswith("Nobody suggests Boca. What else?")
