import json
import re

import pytest

from gremlincore.init import init


def test_init_scaffolds_a_working_home(tmp_path, monkeypatch):
    h, cfg = init(tmp_path / "pat", "Pat", "they/them", "RoboPat", symbol="◎")
    monkeypatch.setenv("GREMLIN_HOME", str(h))
    for rel in ("gremlin.toml", "STATUS.md", "CLAUDE.md", ".claude/settings.json",
                ".claude/skills/robopat/SKILL.md", "queue/README.md", "ledger/README.md",
                "ledger/predictions.jsonl", "ledger/wf.jsonl", ".git"):
        assert (h / rel).exists(), rel
    for name in ("CONVICTIONS", "MOVES", "GREMLIN", "OUT_THERE", "HURT", "IDOLS", "MUSIC"):
        assert "## Distilled from the corpus" in (h / f"persona/{name}.md").read_text()
    for p in [*h.rglob("*.md"), h / "gremlin.toml", h / ".claude/settings.json"]:
        left = re.findall(r"\{(owner|agent|pronouns|symbol|slug|owner_id|today|closing|eval_store|pipeline_store)\}",
                          p.read_text())
        assert not left, f"{p}: unrendered {left}"
    assert cfg["owner"]["name"] == "Pat" and cfg["agent"]["symbol"] == "◎"
    json.loads((h / ".claude/settings.json").read_text())

    from gremlincore import ledger, queue, wake
    assert queue.items() == [] and ledger.entries() == []
    b = wake.brief()
    assert "Queue: nothing pending" in b and "Lessons from Pat's red pen: 0" in b
    assert "You are RoboPat ◎" in (h / "CLAUDE.md").read_text()


def test_init_refuses_to_clobber(tmp_path):
    h, _ = init(tmp_path / "pat", "Pat", "they/them", "RoboPat", git=False)
    (h / "STATUS.md").write_text("Pat's real status. Do not touch.")
    with pytest.raises(SystemExit, match="somebody's home"):
        init(h, "Greg", "he/him", "RoboGreg", git=False)
    assert (h / "STATUS.md").read_text() == "Pat's real status. Do not touch."


def test_init_refuses_to_overwrite_loose_files(tmp_path):
    d = tmp_path / "half"
    d.mkdir()
    (d / "CLAUDE.md").write_text("mine")
    with pytest.raises(SystemExit, match="refusing to overwrite"):
        init(d, "Pat", "they/them", "RoboPat", git=False)
    assert (d / "CLAUDE.md").read_text() == "mine" and not (d / "gremlin.toml").exists()


def test_cli_init(tmp_path, capsys):
    from gremlincore.cli import main
    main(["init", str(tmp_path / "ray"), "--owner", "Uncle Ray", "--pronouns", "he/him", "--agent", "RoboRay", "--no-git"])
    assert "RoboRay has a home" in capsys.readouterr().out
    assert (tmp_path / "ray/.claude/skills/roboray/SKILL.md").exists()
