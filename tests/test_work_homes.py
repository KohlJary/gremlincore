"""Open problem 2, the parts a filesystem can back: work homes, meatbag's
refusal, work context kept as pointers, and a plate export that can't
carry it. Everything here is invented (Pat, Acme, Greg)."""
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

import meatbag
from gremlincore import context, home, plate, wake
from gremlincore.cli import main as gremlin
from gremlincore.init import init
from meatbag.cli import COMMANDS as MEATBAG_COMMANDS
from meatbag.cli import main as meatbag_main

SECRET = "ACME-INTERNAL-do-not-ship-7f3a"
ROOT = Path(__file__).resolve().parent.parent


def _home(tmp_path, monkeypatch, work=False, name="pat"):
    h, _ = init(tmp_path / name, "Pat", "they/them", "RoboPat", git=False, work=work)
    monkeypatch.setenv("GREMLIN_HOME", str(h))
    monkeypatch.setenv("GREMLIN_TODAY", "2026-10-09")
    monkeypatch.chdir(h)
    return h


def _employer_repo(tmp_path):
    """An invented employer repo, outside the home, with a marker in it."""
    r = tmp_path / "acme-billing"
    (r / "docs").mkdir(parents=True)
    (r / "README.md").write_text(f"# Acme billing\n{SECRET}\n")
    (r / "docs/oncall.md").write_text(f"Page Greg. {SECRET}\n")
    subprocess.run(["git", "init", "-q"], cwd=r)
    return r


def _tree(d):
    d = Path(d)
    return {str(p.relative_to(d)): p.read_bytes() for p in sorted(d.rglob("*")) if p.is_file()}


# --- work homes -------------------------------------------------------------

def test_init_work_writes_work_true_and_wake_says_so(tmp_path, monkeypatch):
    h = _home(tmp_path, monkeypatch, work=True)
    cfg = tomllib.loads((h / "gremlin.toml").read_text())
    assert cfg["work"] is True and home.is_work()
    assert wake.brief().splitlines()[0] == "WORK HOME: nothing here becomes a plate."


def test_init_personal_is_not_a_work_home(tmp_path, monkeypatch):
    h = _home(tmp_path, monkeypatch)
    assert tomllib.loads((h / "gremlin.toml").read_text())["work"] is False
    assert not home.is_work() and "WORK HOME" not in wake.brief()


def test_cli_init_work(tmp_path, capsys):
    gremlin(["init", str(tmp_path / "w"), "--owner", "Pat", "--pronouns", "they/them",
             "--agent", "RoboPat", "--no-git", "--work"])
    assert "WORK HOME" in capsys.readouterr().out
    assert home.is_work(home=tmp_path / "w")


@pytest.mark.parametrize("line", [
    "work = true", 'work = "true"', 'work = "yes"', 'work = "maybe"', 'work = ""', "work = 1",
    "work = 2.5", "work = [false]", "Work = true", "WORK = false\nwork = true",
    'Work = "maybe"', "[work]\nenabled = false"])
def test_work_flag_fails_closed(tmp_path, monkeypatch, line, capsys):
    """Anything that isn't clearly false is a work home."""
    (tmp_path / "gremlin.toml").write_text(line + "\n")
    assert home.is_work(home=tmp_path)
    monkeypatch.setenv("GREMLIN_HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as e:
        meatbag_main(["sort"])
    assert e.value.code == meatbag.WORK_EXIT


@pytest.mark.parametrize("line", ["work = false", 'work = "false"', 'work = "No"', "work = 0",
                                  'work = "off"', "", "# work = true"])
def test_work_flag_clearly_false(tmp_path, line):
    (tmp_path / "gremlin.toml").write_text(line + "\n")
    assert not home.is_work(home=tmp_path)


def test_malformed_toml_fails_closed(tmp_path, monkeypatch):
    (tmp_path / "gremlin.toml").write_text("work = fals\n[owner\n")
    assert home.is_work(home=tmp_path)
    monkeypatch.setenv("GREMLIN_HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as e:
        meatbag_main(["normalize"])
    assert e.value.code != 0
    with pytest.raises(SystemExit):
        plate.export(tmp_path / "out")
    assert not (tmp_path / "out").exists()


# --- meatbag refuses in a work home -----------------------------------------

@pytest.mark.parametrize("cmd", sorted([*MEATBAG_COMMANDS, "distill", "select-cases"]))
def test_every_meatbag_command_refuses_in_a_work_home(cmd, tmp_path, monkeypatch, capsys):
    h = _home(tmp_path, monkeypatch, work=True)
    before = _tree(h)
    with pytest.raises(SystemExit) as e:
        meatbag_main([cmd])
    assert e.value.code == meatbag.WORK_EXIT != 0
    assert "refuses to run in a work home" in capsys.readouterr().err
    assert _tree(h) == before and not (h / "data").exists()


MODULES = sorted(p.stem for p in (ROOT / "meatbag").glob("*.py")
                 if 'if __name__ == "__main__":' in p.read_text() and p.stem != "cli")


@pytest.mark.parametrize("mod", MODULES)
def test_meatbag_modules_refuse_when_run_directly(mod, tmp_path, monkeypatch):
    h = _home(tmp_path, monkeypatch, work=True)
    r = subprocess.run([sys.executable, "-m", f"meatbag.{mod}"], cwd=h, capture_output=True,
                       text=True, env={**os.environ, "PYTHONPATH": str(ROOT)})
    assert r.returncode == meatbag.WORK_EXIT, r.stderr
    assert "refuses to run in a work home" in r.stderr


GUARDED = [(m, "main") for m in MODULES] + [("stubs", "distill"), ("stubs", "select_cases")]


@pytest.mark.parametrize("mod,fn", GUARDED)
def test_meatbag_entry_points_refuse_when_imported_and_called(mod, fn, tmp_path, monkeypatch, capsys):
    """`import meatbag.normalize; normalize.main([...])` is refused too, not only the CLI."""
    import importlib
    h = _home(tmp_path, monkeypatch, work=True)
    before = _tree(h)
    entry = getattr(importlib.import_module(f"meatbag.{mod}"), fn)
    assert getattr(entry, "work_guarded", False), f"meatbag.{mod}.{fn} isn't wrapped in work_guard"
    with pytest.raises(SystemExit) as e:
        entry(["anything"])
    assert e.value.code == meatbag.WORK_EXIT
    assert "refuses to run in a work home" in capsys.readouterr().err
    assert _tree(h) == before


def test_every_meatbag_main_is_guarded():
    """A new module with a main() has to be wrapped, or this fails."""
    import importlib
    for p in sorted((ROOT / "meatbag").glob("*.py")):
        m = importlib.import_module(f"meatbag.{p.stem}")
        if p.stem not in ("cli", "__init__") and hasattr(m, "main"):
            assert getattr(m.main, "work_guarded", False), p.name


def test_meatbag_refuses_when_cwd_is_a_work_home_but_env_points_elsewhere(tmp_path, monkeypatch, capsys):
    personal, _ = init(tmp_path / "personal", "Pat", "they/them", "RoboPat", git=False)
    work = _home(tmp_path, monkeypatch, work=True, name="work")
    monkeypatch.setenv("GREMLIN_HOME", str(personal))
    monkeypatch.chdir(work)
    with pytest.raises(SystemExit) as e:
        meatbag_main(["normalize"])
    assert e.value.code == meatbag.WORK_EXIT


def test_meatbag_still_runs_in_a_personal_home(tmp_path, monkeypatch):
    _home(tmp_path, monkeypatch)
    assert meatbag.work_home() is None
    assert meatbag_main(["distill"]) == 3  # the stub's own exit, not the guard's


# --- work context -----------------------------------------------------------

def test_context_add_list_remove_keeps_pointers_only(tmp_path, monkeypatch, capsys):
    h = _home(tmp_path, monkeypatch, work=True)
    repo = _employer_repo(tmp_path)
    gremlin(["context", "add", str(repo), "--note", "billing service"])
    es = json.loads((h / "context/contexts.json").read_text())
    assert es == [{"name": "acme-billing", "path": str(repo.resolve()), "kind": "repo",
                   "added": "2026-10-09", "note": "billing service"}]
    for p in h.rglob("*"):
        if p.is_file():
            assert SECRET.encode() not in p.read_bytes(), f"context content copied into {p}"
    assert not (h / "persona").joinpath("acme-billing").exists()

    capsys.readouterr()
    gremlin(["context", "list"])
    assert "acme-billing" in capsys.readouterr().out
    gremlin(["context", "remove", "acme-billing"])
    assert context.entries() == []
    assert (repo / "README.md").read_text().count(SECRET) == 1  # never touched


def test_context_add_refuses_the_home_itself_and_duplicates(tmp_path, monkeypatch):
    h = _home(tmp_path, monkeypatch, work=True)
    with pytest.raises(SystemExit, match="inside the home"):
        context.add(h / "persona")
    with pytest.raises(SystemExit, match="contains the home"):
        context.add(tmp_path)
    with pytest.raises(SystemExit, match="isn't a directory"):
        context.add(tmp_path / "nope")
    repo = _employer_repo(tmp_path)
    context.add(repo)
    with pytest.raises(SystemExit, match="already registered"):
        context.add(repo)


def test_skill_says_where_context_lives_and_where_it_never_goes(tmp_path, monkeypatch):
    h = _home(tmp_path, monkeypatch, work=True)
    skill = (h / ".claude/skills/robopat/SKILL.md").read_text()
    assert "context/contexts.json" in skill
    assert "Context never goes into `persona/`, `STATUS.md` or `ideas.md`" in skill
    assert "context/" in (h / ".gitignore").read_text()


# --- the export path --------------------------------------------------------

def _personal_with_everything(tmp_path, monkeypatch):
    """A personal home with persona written, a queue, both ledgers, a lesson."""
    h = _home(tmp_path, monkeypatch)
    (h / "persona/MOVES.md").write_text("# Moves\n\n- Ask what the barbecue is for.\n")
    (h / "queue/0001-bbq.md").write_text(
        "---\nstatus: vetoed\nkind: email\nto: Uncle Ray\nroom: families\nwhy: QUEUE-MARKER\n"
        "prediction: 1\ncreated: 2026-10-01\nveto_reason: too corporate LESSON-MARKER\n---\n\nhi\n")
    (h / "ledger/predictions.jsonl").write_text('{"id": 1, "prediction": "LEDGER-MARKER"}\n')
    (h / "ledger/wf.jsonl").write_text('{"id": 1, "wf": 1, "what": "WF-MARKER"}\n')
    return h


EXPECTED = {"STATUS.md", "plate.toml", "MANIFEST.sha256",
            *(f"persona/{p.name}" for p in (ROOT / "templates/persona").glob("*.md"))}


def test_export_after_context_add_is_byte_identical(tmp_path, monkeypatch):
    """The open-problems test: a plate exported after `context add` is
    byte-identical to one exported before."""
    _personal_with_everything(tmp_path, monkeypatch)
    plate.export(tmp_path / "before")
    gremlin(["context", "add", str(_employer_repo(tmp_path))])
    assert context.entries()
    plate.export(tmp_path / "after")
    assert _tree(tmp_path / "before") == _tree(tmp_path / "after")


def test_export_is_the_allowlist_and_nothing_else(tmp_path, monkeypatch):
    h = _personal_with_everything(tmp_path, monkeypatch)
    context.add(_employer_repo(tmp_path))
    (h / "corpus/turns.jsonl").write_text('{"text": "CORPUS-MARKER"}\n')
    (h / "persona/notes.txt").write_text("NOT-MD-MARKER")
    _, rels = plate.export(tmp_path / "out")
    tree = _tree(tmp_path / "out")
    assert set(rels) == set(tree) == EXPECTED
    assert not any(r.startswith(("context", "queue", "ledger", "corpus", "data", "eval", ".claude"))
                   for r in tree)
    blob = b"".join(tree.values())
    for marker in (SECRET, "QUEUE-MARKER", "LESSON-MARKER", "LEDGER-MARKER", "WF-MARKER",
                   "CORPUS-MARKER", "NOT-MD-MARKER", "contexts.json", "acme-billing"):
        assert marker.encode() not in blob, marker
    assert tree["persona/MOVES.md"] == (h / "persona/MOVES.md").read_bytes()
    assert tomllib.loads(tree["plate.toml"].decode()) == {
        "owner": {"name": "Pat", "pronouns": "they/them"},
        "agent": {"name": "RoboPat", "symbol": "⊖"}}
    import hashlib
    for line in tree["MANIFEST.sha256"].decode().splitlines():
        digest, rel = line.split("  ")
        assert hashlib.sha256(tree[rel]).hexdigest() == digest


def test_export_refuses_in_a_work_home(tmp_path, monkeypatch, capsys):
    _home(tmp_path, monkeypatch, work=True)
    with pytest.raises(SystemExit, match="WORK HOME"):
        gremlin(["plate", "export", str(tmp_path / "out")])
    assert not (tmp_path / "out").exists()


def test_export_refuses_a_symlink_on_the_allowlist(tmp_path, monkeypatch):
    h = _home(tmp_path, monkeypatch)
    repo = _employer_repo(tmp_path)
    (h / "persona/ACME.md").symlink_to(repo / "README.md")
    with pytest.raises(SystemExit, match="symlink"):
        plate.export(tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("target", ["persona/ACME.md", "STATUS.md"])
def test_export_refuses_a_hardlink_on_the_allowlist(target, tmp_path, monkeypatch):
    h = _home(tmp_path, monkeypatch)
    repo = _employer_repo(tmp_path)
    (h / target).unlink(missing_ok=True)
    os.link(repo / "README.md", h / target)
    with pytest.raises(SystemExit, match="hard links"):
        plate.export(tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_export_wont_write_over_something(tmp_path, monkeypatch):
    _home(tmp_path, monkeypatch)
    (tmp_path / "out").mkdir()
    (tmp_path / "out/keep").write_text("mine")
    with pytest.raises(SystemExit, match="isn't an empty directory"):
        plate.export(tmp_path / "out")
    assert (tmp_path / "out/keep").read_text() == "mine"
