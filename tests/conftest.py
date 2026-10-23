"""A fixture home in the Gregiverse. Never a real queue, never a real corpus."""
import json
import subprocess

import pytest

DRAFT = """---
status: pending        # pending | approved | edited | vetoed | sent
kind: email
to: Uncle Ray
room: families
why: barbecue invite
prediction: 1
created: 2026-10-01
---

Barbecue Saturday, 3pm, bring a chair.
"""

TOML = """[owner]
name = "Pat"
pronouns = "they/them"

[agent]
name = "RoboPat"
symbol = "⊖"
"""


@pytest.fixture
def home(tmp_path, monkeypatch):
    for d in ("queue", "ledger", "persona"):
        (tmp_path / d).mkdir()
    (tmp_path / "gremlin.toml").write_text(TOML)
    (tmp_path / "queue/0001-bbq.md").write_text(DRAFT)
    (tmp_path / "ledger/predictions.jsonl").write_text(json.dumps(
        {"id": 1, "date": "2026-10-01", "by": "RoboPat", "prediction": "Ray RSVPs",
         "falsifier": "no RSVP", "check_when": "after send", "check_after_days": 7,
         "check_by": None, "outcome": None, "hit": None}) + "\n")
    (tmp_path / "ledger/wf.jsonl").write_text("")
    (tmp_path / "STATUS.md").write_text("_Last updated: 2026-10-01_\n")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path)
    monkeypatch.setenv("GREMLIN_HOME", str(tmp_path))
    monkeypatch.setenv("GREMLIN_TODAY", "2026-10-09")
    monkeypatch.delenv("GREMLIN_TALK", raising=False)
    return tmp_path
