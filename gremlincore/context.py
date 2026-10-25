"""Work context: the repos and docs dirs the agent works on, kept as pointers.

  gremlin context add PATH [--note TEXT]   register a repo or docs dir
  gremlin context list
  gremlin context remove PATH|NAME

Context is *what you work on*, not *who you are*. It's stored in
`context/contexts.json` inside the home as a list of paths plus metadata
(name, kind, date added, a note). Nothing is copied: not into persona/,
not into context/, not anywhere. The content stays where it lives, and the
plate export (`gremlin plate export`) never reads context/ at all.
"""
import argparse
import json
import sys
from pathlib import Path

from . import home
from .home import root, today

DIRNAME = "context"
REGISTRY = "contexts.json"

README = """# context/

Work context for this home: a list of paths in `contexts.json`, managed by
`gremlin context add|list|remove`. Only the pointers live here. The content
stays where it is, and nothing in this directory is ever part of a plate:
`gremlin plate export` doesn't read it, and the agent never copies context
into persona/, STATUS.md or ideas.md.
"""


def registry_path(h=None):
    return Path(h or root()) / DIRNAME / REGISTRY


def entries(h=None):
    p = registry_path(h)
    if not p.exists():
        return []
    return json.loads(p.read_text() or "[]")


def _save(es, h=None):
    p = registry_path(h)
    p.parent.mkdir(parents=True, exist_ok=True)
    readme = p.parent / "README.md"
    if not readme.exists():
        readme.write_text(README)
    p.write_text(json.dumps(es, indent=2, ensure_ascii=False) + "\n")


def add(path, note="", h=None):
    h = Path(h or root()).resolve()
    p = Path(path).expanduser().resolve()
    if not p.is_dir():
        raise SystemExit(f"{p} isn't a directory. Context is a repo or a docs dir.")
    if p == h or h in p.parents:
        raise SystemExit(f"{p} is inside the home ({h}). Context lives where it lives; "
                         "the home only keeps the pointer.")
    if p in h.parents:
        raise SystemExit(f"{p} contains the home ({h}). Point at the repo or docs dir itself.")
    es = entries(h)
    if any(e["path"] == str(p) for e in es):
        raise SystemExit(f"{p} is already registered.")
    names = {e["name"] for e in es}
    name, n = p.name, 2
    while name in names:
        name, n = f"{p.name}-{n}", n + 1
    e = {"name": name, "path": str(p), "kind": "repo" if (p / ".git").exists() else "dir",
         "added": today(), "note": note}
    es.append(e)
    _save(es, h)
    return e


def remove(key, h=None):
    h = Path(h or root())
    es = entries(h)
    resolved = str(Path(key).expanduser().resolve())
    keep = [e for e in es if e["name"] != key and e["path"] != resolved]
    if len(keep) == len(es):
        raise SystemExit(f"no context named or at {key!r}. `gremlin context list` shows them.")
    _save(keep, h)
    return [e for e in es if e not in keep]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gremlin context", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a_add = sub.add_parser("add")
    a_add.add_argument("path")
    a_add.add_argument("--note", default="")
    sub.add_parser("list")
    a_rm = sub.add_parser("remove")
    a_rm.add_argument("key")
    a = ap.parse_args(argv)
    if a.cmd == "add":
        e = add(a.path, a.note)
        print(f"context {e['name']} ({e['kind']}): {e['path']}")
        print("Registered as a pointer. Nothing was copied, and it never goes into a plate.")
        if not home.is_work():
            print("Note: this isn't a work home. `gremlin init --work` makes one that "
                  "meatbag and `gremlin plate export` refuse to touch.")
    elif a.cmd == "list":
        es = entries()
        if not es:
            print("No work context registered.")
        for e in es:
            gone = "" if Path(e["path"]).is_dir() else "  (missing)"
            print(f"{e['name']:<20} {e['kind']:<5} {e['added']}  {e['path']}{gone}"
                  + (f"  # {e['note']}" if e.get("note") else ""))
    else:
        for e in remove(a.key):
            print(f"removed context {e['name']}: {e['path']} (the pointer; the content was never here)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
