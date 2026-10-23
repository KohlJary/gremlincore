import json

from meatbag import voice


def _session(base, project, text):
    d = base / project
    d.mkdir(parents=True)
    (d / "s1.jsonl").write_text(json.dumps(
        {"type": "user", "timestamp": "2026-10-20T10:00:00Z", "message": {"content": text}}) + "\n")


def test_reads_nothing_by_default(home, tmp_path, capsys):
    base = tmp_path / "projects"
    _session(base, "-home-pat-dayjob-billing", "the quarterly numbers are wrong")
    assert voice.sessions(30, base=base) == []
    cfg_v = voice.config()["voice"]
    assert not any(cfg_v.values())
    voice.main([])
    assert "reading nothing" in capsys.readouterr().out
    assert not (home / "data/voice").exists()


def test_allowlist_reads_only_listed_projects(home, tmp_path):
    base = tmp_path / "projects"
    _session(base, "-home-pat-dayjob-billing", "the quarterly numbers are wrong")
    _session(base, "-home-pat-cookout", "Schlitz, chairs, and nobody suggests Boca")
    rows = voice.sessions(30, projects=["cookout"], base=base)
    assert [r["text"] for r in rows] == ["Schlitz, chairs, and nobody suggests Boca"]


def test_github_without_a_login_reads_nothing():
    assert voice.github("", ["someone/repo"]) == []
    assert voice.rss([]) == []
