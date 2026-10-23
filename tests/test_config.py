from pathlib import Path

from gremlincore import home as home_mod


def test_defaults_without_a_toml(tmp_path, monkeypatch):
    monkeypatch.setenv("GREMLIN_HOME", str(tmp_path))
    cfg = home_mod.config()
    assert cfg["voice"] == {"github_login": "", "github_repos": [], "rss_feeds": [], "session_projects": []}
    assert cfg["filters"]["do_not_generalize"] == [] and cfg["corpus"]["eras"] == []
    assert cfg["models"]["local"] == "qwen3:8b"
    assert cfg["paths"]["eval"] == str(Path.home() / ".local/share/gremlincore/gremlin/eval")


def test_toml_overrides_and_keeps_the_rest(home):
    (home / "gremlin.toml").write_text(
        (home / "gremlin.toml").read_text()
        + '\n[paths]\neval = "~/walled/eval"\n\n[filters]\ndo_not_generalize = ["landlord"]\n'
        '\n[corpus]\neras = [{name = "before-the-move", before = "2025-06"}]\nlast_era = "after"\n')
    cfg = home_mod.config()
    assert cfg["owner"] == {"name": "Pat", "pronouns": "they/them"}
    assert cfg["agent"]["name"] == "RoboPat"
    assert cfg["paths"]["eval"] == str(Path.home() / "walled/eval")
    assert cfg["paths"]["pipeline"].endswith(".local/share/gremlincore/robopat/pipeline")
    assert cfg["filters"]["do_not_generalize"] == ["landlord"]
    assert cfg["corpus"]["domains"][0] == "strategy"  # untouched keys survive
    from meatbag.distill_snapshot import era
    assert era("2025-01-01T00:00:00Z", cfg) == "before-the-move" and era("2026-01-01", cfg) == "after"


def test_home_is_found_by_walking_up(tmp_path, monkeypatch):
    (tmp_path / "gremlin.toml").write_text('[agent]\nname = "RoboRay"\n')
    (tmp_path / "queue").mkdir()
    monkeypatch.delenv("GREMLIN_HOME", raising=False)
    monkeypatch.chdir(tmp_path / "queue")
    assert home_mod.root() == tmp_path and home_mod.agent() == "RoboRay"
