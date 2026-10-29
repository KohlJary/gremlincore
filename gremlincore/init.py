"""Scaffold a new home: the place an agent lives.

  gremlin init ~/greg-bot --owner Greg --pronouns he/him --agent RoboGreg [--symbol ⊖] [--work]

--work makes a work home: `work = true` in gremlin.toml. Nothing in a work
home becomes a plate. meatbag refuses to run in one, `gremlin plate export`
refuses to export from one, and work context (`gremlin context add`) stays
a list of paths in context/.

Writes gremlin.toml, the persona/ skeleton, STATUS.md, empty ledgers, the
queue, .claude/settings.json (the walls), CLAUDE.md and the skill. It
refuses to touch a directory that already has a gremlin.toml, or any file
it would overwrite.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from .home import CONFIG_NAME, DEFAULTS, config, slug, today


def templates_dir():
    """A checkout's templates/, or where a package put them (the AUR package:
    /usr/share/gremlincore/templates). GREMLINCORE_TEMPLATES overrides both."""
    here = Path(__file__).resolve().parent
    env = os.environ.get("GREMLINCORE_TEMPLATES")
    cands = [Path(env)] if env else []
    cands += [here / "templates", here.parent / "templates",
              Path(sys.prefix) / "share/gremlincore/templates", Path("/usr/share/gremlincore/templates")]
    for d in cands:
        if (d / "SKILL.md.template").exists():
            return d
    raise SystemExit("gremlincore templates not found (install from a checkout: pip install -e ., "
                     "or set GREMLINCORE_TEMPLATES)")


def render(text, values):
    for k, v in values.items():
        text = text.replace("{" + k + "}", v)
    return text


def plan(home, values):
    """{relative path: content} for every file init writes."""
    t = templates_dir()
    files = {
        CONFIG_NAME: render((t / "gremlin.toml.template").read_text(), values),
        "STATUS.md": render((t / "STATUS.md.template").read_text(), values),
        "CLAUDE.md": render((t / "CLAUDE.md.template").read_text(), values),
        f".claude/skills/{values['slug']}/SKILL.md": render((t / "SKILL.md.template").read_text(), values),
        "queue/README.md": render((t / "queue/README.md").read_text(), values),
        "ledger/README.md": render((t / "ledger/README.md").read_text(), values),
        "ledger/predictions.jsonl": "",
        "ledger/wf.jsonl": "",
        ".gitignore": ("# Derived from transcripts: never committed.\ndata/\ncorpus/\neval/cases*\n"
                       "# Where work context lives on this machine: not for a public remote.\ncontext/\n"),
    }
    for p in sorted((t / "persona").glob("*.md")):
        files[f"persona/{p.name}"] = render(p.read_text(), values)
    files[".claude/settings.json"] = render((t / ".claude/settings.json").read_text(), values)
    json.loads(files[".claude/settings.json"])  # a broken wall is worse than none
    return files


WORK_LINE = ("# WORK HOME: nothing here becomes a plate. meatbag refuses to run here,\n"
             "# and `gremlin plate export` refuses to export from here.\n"
             "work = true")
PERSONAL_LINE = ("# A personal home. `gremlin init --work` makes a work home instead, one\n"
                 "# that meatbag and `gremlin plate export` refuse to touch.\n"
                 "work = false")


def init(home, owner, pronouns, agent, symbol=None, git=True, work=False):
    home = Path(home).expanduser()
    if (home / CONFIG_NAME).exists():
        raise SystemExit(f"{home} already has a {CONFIG_NAME}: that's somebody's home. Not touching it.")
    for v in (owner, pronouns, agent, symbol or ""):
        if any(c in v for c in '"\\\n'):
            raise SystemExit(f"no quotes, backslashes or newlines in names: {v!r}")
    values = {"owner": owner, "pronouns": pronouns, "agent": agent,
              "symbol": symbol or DEFAULTS["agent"]["symbol"], "slug": slug(agent),
              "owner_id": slug(owner), "today": today(),
              "closing": DEFAULTS["wake"]["closing"],
              "work_line": WORK_LINE if work else PERSONAL_LINE}
    base = Path.home() / ".local/share/gremlincore" / values["slug"]
    values["eval_store"] = str(base / "eval")
    values["pipeline_store"] = str(base / "pipeline")
    files = plan(home, values)
    clash = [p for p in files if (home / p).exists()]
    if clash:
        raise SystemExit(f"refusing to overwrite: {', '.join(clash)}")
    for rel, content in files.items():
        p = home / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    for d in ("corpus", "eval"):
        (home / d).mkdir(exist_ok=True)
    if git and not (home / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=home)
    cfg = config(home)
    return home, cfg


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gremlin init", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir")
    ap.add_argument("--owner", required=True)
    ap.add_argument("--pronouns", required=True)
    ap.add_argument("--agent", required=True)
    ap.add_argument("--symbol")
    ap.add_argument("--no-git", action="store_true")
    ap.add_argument("--work", action="store_true",
                    help="a work home: nothing here becomes a plate")
    a = ap.parse_args(argv)
    home, cfg = init(a.dir, a.owner, a.pronouns, a.agent, a.symbol, git=not a.no_git, work=a.work)
    print(f"{cfg['agent']['name']} has a home: {home}")
    if a.work:
        print("WORK HOME: nothing here becomes a plate. meatbag won't run here.")
        print("Add work context with `gremlin context add <repo>`; it stays a list of paths.")
        print(f"Talk to it: `cd {home} && gremlin talk`.")
        return 0
    print(f"  pipeline store: {cfg['paths']['pipeline']}")
    print(f"  eval store:     {cfg['paths']['eval']}")
    print("Next: export your AI chats, then `meatbag normalize <export.zip>` from the home.")
    print(f"Talk to it: `cd {home} && gremlin talk`.")


if __name__ == "__main__":
    sys.exit(main())
