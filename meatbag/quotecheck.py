"""Check that quotes in persona files are the owner's actual words.

Matches each quoted span (20+ chars) in the "## Distilled from the corpus"
section against the owner's turns in the open corpus by 4-word shingles.
With --mark, any quote under 50% gets "(not verbatim)" after it, so a
paraphrase is never mistaken for the owner. Local models paraphrase while
claiming to quote; this catches it.

  meatbag quotecheck persona/CONVICTIONS.md [--mark]
"""
import json
import re
import sys
from pathlib import Path

from . import paths

MARK = " *(not verbatim)*"


def _norm(s):
    s = (s.replace("’", "'").replace("‘", "'").replace("“", '"')
          .replace("”", '"').replace("*", "").replace("_", " "))
    s = re.sub(r"\.\.\.|…", " ", s)
    s = re.sub(r"[^\w' ]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def corpus():
    """Every source of the owner's own words: chat turns (held-out removed),
    every file `meatbag voice` wrote to data/voice/, and recent Claude Code
    prompts from the configured session projects (none by default)."""
    hp = paths.evaldir("holdout_convs.json")
    held = set(json.loads(hp.read_text())["conv_ids"]) if hp.exists() else set()
    T = []
    for base in (paths.corpus("turns.jsonl"), paths.data("turns.jsonl")):
        if base.exists():
            T = [_norm(t["text"]) for t in map(json.loads, base.open())
                 if t["role"] == "human" and t["conv_id"] not in held]
            break
    vdir = paths.data("voice")
    for p in sorted(vdir.glob("*.jsonl")) if vdir.exists() else []:
        T += [_norm(json.loads(l)["text"]) for l in p.open() if l.strip()]
    from .voice import sessions
    T += [_norm(r["text"]) for r in sessions(14)]
    if not T:
        raise SystemExit("no corpus found")
    return T


def score(q, T):
    w = _norm(q).split()
    if len(w) < 4:
        return 1.0
    sh = {" ".join(w[i:i + 4]) for i in range(len(w) - 3)}
    best = 0.0
    for t in T:
        best = max(best, sum(s in t for s in sh) / len(sh))
        if best == 1.0:
            break
    return best


QUOTE = re.compile(r'"([^"\n]{20,}(?:\n[^"\n]+){0,3})"')


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    if not a or a[0] in ("-h", "--help"):
        raise SystemExit(__doc__)
    path, mark = Path(a[0]), "--mark" in a
    T = corpus()
    full = path.read_text()
    marker = "## Distilled from the corpus"
    head, text = (full.split(marker, 1)[0] + marker, full.split(marker, 1)[1]) if marker in full else ("", full)
    out, n, bad = [head], 0, 0
    pos = 0
    for m in QUOTE.finditer(text):
        q = m.group(1)
        if q.lstrip().startswith((")", "(", ",", ":")) or "\n- " in q or "**" in q:
            continue  # spans between two quotes, not a quote
        n += 1
        s = score(q, T)
        tail = text[m.end():m.end() + len(MARK)]
        if s < 0.5:
            bad += 1
            if mark and tail != MARK:
                out.append(text[pos:m.end()] + MARK)
                pos = m.end()
    out.append(text[pos:])
    if mark:
        path.write_text("".join(out))
    # only the distilled section is checked: the rest quotes this session,
    # essays and other sources by design
    print(f"{path}: {n} quotes, {bad} not verbatim" + (" (marked)" if mark else ""))


if __name__ == "__main__":
    main()
