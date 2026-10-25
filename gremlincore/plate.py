"""The plate: what leaves a home when someone brings it (cookout's `bring`
will call this; cookout isn't built).

  gremlin plate export OUT

Writes an allowlist and nothing else:

  persona/*.md    regular files directly in persona/, no symlinks
  STATUS.md
  plate.toml      owner name, pronouns, agent name and symbol, from gremlin.toml
  MANIFEST.sha256 one line per file above, sorted

Everything else in the home is left behind because it isn't on the list:
context/, the queue, both ledgers (so the lessons, which are read from the
queue), corpus/, data/, eval/, .claude/. The output has no timestamps, so
the same home exports to the same bytes.

It refuses to run in a work home (anything but a clearly false `work`), and refuses a symlink
or a hardlinked file (link count above 1) anywhere on the allowlist, since
a link is how a file outside it would ride along.
"""
import argparse
import hashlib
import sys
from pathlib import Path

from . import home
from .home import root

PERSONA = "persona"
STATUS = "STATUS.md"


def _toml_str(v):
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _no_hardlink(p):
    if p.stat().st_nlink > 1:
        raise SystemExit(f"{p} has {p.stat().st_nlink} hard links. Refusing: another name for "
                         "the same bytes could be a file outside the allowlist. Copy it instead.")


def allowlist(h):
    """[(relative path in the plate, source path)] for every file that goes."""
    h = Path(h)
    pd = h / PERSONA
    if pd.is_symlink():
        raise SystemExit(f"{pd} is a symlink. A plate is built from the home's own persona/, not a link.")
    out = []
    if pd.is_dir():
        for p in sorted(pd.iterdir()):
            if p.suffix != ".md":
                continue
            if p.is_symlink():
                raise SystemExit(f"{p} is a symlink. Refusing: a link is how something outside "
                                 "the allowlist would ride along.")
            if p.is_file():
                _no_hardlink(p)
                out.append((f"{PERSONA}/{p.name}", p))
    st = h / STATUS
    if st.is_symlink():
        raise SystemExit(f"{st} is a symlink. Refusing.")
    if st.is_file():
        _no_hardlink(st)
        out.append((STATUS, st))
    return out


def plate_toml(cfg):
    o, a = cfg["owner"], cfg["agent"]
    return ("# A plate's identity, from the home's gremlin.toml. Nothing else from it travels.\n"
            "[owner]\n"
            f"name = {_toml_str(o['name'])}\n"
            f"pronouns = {_toml_str(o['pronouns'])}\n\n"
            "[agent]\n"
            f"name = {_toml_str(a['name'])}\n"
            f"symbol = {_toml_str(a['symbol'])}\n")


def export(out, h=None):
    h = Path(h or root())
    if home.is_work(home=h):  # before config(): a gremlin.toml that won't parse is work too
        raise SystemExit(f"{h} is a WORK HOME (work = true): nothing here becomes a plate. "
                         "Export from your personal home.")
    out = Path(out).expanduser()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise SystemExit(f"{out} exists and isn't an empty directory. Not writing over it.")
    if (h / PERSONA).resolve() in (out.resolve(), *out.resolve().parents):
        raise SystemExit(f"{out} is inside persona/. Export somewhere else.")
    cfg = home.config(h)
    files = {rel: src.read_bytes() for rel, src in allowlist(h)}
    files["plate.toml"] = plate_toml(cfg).encode()
    manifest = "".join(f"{hashlib.sha256(b).hexdigest()}  {rel}\n" for rel, b in sorted(files.items()))
    files["MANIFEST.sha256"] = manifest.encode()
    for rel, b in files.items():
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b)
    return out, sorted(files)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gremlin plate", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("out")
    a = ap.parse_args(argv)
    out, rels = export(a.out)
    print(f"plate written to {out}: {len(rels)} files")
    for r in rels:
        print(f"  {r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
