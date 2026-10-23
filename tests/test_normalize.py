"""normalize on tiny synthetic exports (tests/fixtures; invented, Gregiverse)."""
import json
import zipfile
from pathlib import Path

from meatbag import normalize

FX = Path(__file__).parent / "fixtures"


def test_claude_export():
    ts = list(normalize.turns(FX / "claude_export.json"))
    assert [t["source"] for t in ts] == ["claude"] * 6
    c1 = [t for t in ts if t["conv_id"] == "c-0001"]
    assert [t["role"] for t in c1] == ["human", "assistant", "human", "assistant"]  # the blank turn is skipped
    assert [t["idx"] for t in c1] == [0, 1, 2, 3]
    assert c1[1]["text"].startswith("Great! A tiered RSVP")  # text from content blocks
    assert c1[2]["text"].endswith("nobody suggests Boca.")
    assert c1[0]["title"] == "Barbecue logistics" and c1[0]["summary"].startswith("Planning")


def test_chatgpt_export_follows_the_visible_branch():
    ts = list(normalize.turns(FX / "chatgpt_export.json"))
    assert [t["role"] for t in ts] == ["human", "assistant", "human", "assistant"]  # no system turn
    assert all(t["source"] == "gpt" and t["conv_id"] == "g-0001" for t in ts)
    assert "OLD BRANCH" not in " ".join(t["text"] for t in ts)
    assert ts[-1]["text"] == "Bounce first, minutes later. Got it."
    assert ts[0]["ts"].startswith("2024-12-24") and ts[0]["conv_created"].startswith("2024-12-24")


def test_zip_and_cli_write_turns_into_the_home(home, tmp_path):
    z = tmp_path / "export.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.write(FX / "claude_export.json", "data-2026/conversations.json")
    normalize.main([str(z), str(FX / "chatgpt_export.json")])
    rows = [json.loads(l) for l in (home / "data/turns.jsonl").read_text().splitlines()]
    assert len(rows) == 10 and {r["source"] for r in rows} == {"claude", "gpt"}
