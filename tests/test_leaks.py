"""Nothing of the first owner, or their world, rides along.

Greps every tracked-or-trackable file in the repo for names, handles and
secrets that belong to somebody's private build. The patterns are built
from pieces so this file doesn't match itself. The author's name is
allowed in exactly three places: LICENSE, the README's credit lines, and
pyproject's authors. The AUR PKGBUILD's Maintainer and url lines are the one
exception to every pattern: the AUR requires a maintainer, and the author chose to
publish the address (2026-10-23).
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

J = "".join
FORBIDDEN = [re.compile(p, re.I) for p in (
    J(["ja", "ryk"]), J(["ko", "hlbern"]), J(["@g", "mail"]), J(["hearth", "weave"]),
    J(["sub", "stack"]), J([r"\bca", r"ss\b"]), J(["daed", "alus"]), J(["sk-", "ant"]),
)]
AUTHOR = re.compile(J(["ko", "hl"]), re.I)
README_CREDITS = ("## the first plate", "## credits")
SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache"}


def files():
    try:
        out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
        ps = [ROOT / p for p in out if p]
    except (OSError, subprocess.CalledProcessError):
        ps = [p for p in ROOT.rglob("*") if p.is_file()]
    return [p for p in ps if p.is_file() and not SKIP_DIRS & set(p.relative_to(ROOT).parts)]


def allowed_author_lines(p):
    """Line numbers where the author's name may appear in this file."""
    rel = p.relative_to(ROOT).as_posix()
    lines = p.read_text(errors="replace").splitlines()
    if rel == "LICENSE":
        return set(range(len(lines)))
    if rel == "pyproject.toml":
        return {i for i, l in enumerate(lines) if l.startswith("authors")}
    if rel == "README.md":
        ok, inside = set(), False
        for i, l in enumerate(lines):
            if l.startswith("## "):
                inside = l.lower().startswith(README_CREDITS)
            if inside:
                ok.add(i)
        return ok
    return set()


PKGBUILD_PUBLIC = ("# Maintainer: ", "url=")


def test_no_leaks():
    hits = []
    for p in files():
        text = p.read_text(errors="replace")
        allowed = allowed_author_lines(p)
        for i, line in enumerate(text.splitlines()):
            if p.relative_to(ROOT).as_posix() == "pkg/aur/PKGBUILD" and line.startswith(PKGBUILD_PUBLIC):
                continue
            for pat in FORBIDDEN:
                if pat.search(line):
                    hits.append(f"{p.relative_to(ROOT)}:{i + 1}: {pat.pattern!r}")
            if AUTHOR.search(line) and i not in allowed:
                hits.append(f"{p.relative_to(ROOT)}:{i + 1}: author name outside the credits")
    assert not hits, "leaks:\n" + "\n".join(hits)


def test_the_leak_test_can_see():
    # If files() found nothing, the test above passes for the wrong reason.
    names = {p.relative_to(ROOT).as_posix() for p in files()}
    assert {"LICENSE", "pyproject.toml", "gremlincore/home.py", "meatbag/voice.py"} <= names
