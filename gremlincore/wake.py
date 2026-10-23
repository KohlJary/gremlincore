"""One wake-up brief: STATUS freshness, WF count, bets due, the queue, lessons.

  gremlin wake

If anything the agent is made of (persona/, its skill, CLAUDE.md) changed
after STATUS's "Last updated" date, the brief says so first, in caps. A
stale STATUS doesn't make the agent cautious; it makes it wrong with
confidence.
"""
import re
import statistics
import subprocess

from . import home, ledger, lessons, queue, wf
from .home import root, today

MADE_OF = ["persona", ".claude/skills", "skills", "CLAUDE.md", "gremlin.toml"]


def status_date():
    p = root() / "STATUS.md"
    m = re.search(r"_Last updated: (\d{4}-\d{2}-\d{2})_", p.read_text()) if p.exists() else None
    return m.group(1) if m else None


def last_change():
    paths = [p for p in MADE_OF if (root() / p).exists()]
    if not paths:
        return None
    out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", *paths],
                         cwd=root(), capture_output=True, text=True).stdout.strip()
    return out or None


def brief(on=None):
    on = on or today()
    cfg = home.config()
    lines = []
    sd, lc = status_date(), last_change()
    if sd and lc and lc > sd:
        lines.append(f"!! STATUS IS STALE: last updated {sd}, but persona/skill changed {lc}. "
                     "Update STATUS before believing it.")
    lines.append(f"# Wake brief, {on}")
    lines.append(f"STATUS last updated {sd or '?'}")
    es = wf.entries()
    lines.append(f"WF to date: {sum(e.get('wf', 0) for e in es)} across {len(es)} incident(s). Target: zero.")
    for e in es[-3:]:
        lines.append(f"  - #{e['id']} {e['what'][:90]} -> changed: {e.get('change', '')[:70]}")
    d = ledger.due(on)
    lines.append(f"Bets open and due: {len(d)}")
    for e, why in d:
        lines.append(f"  - #{e['id']} [{why[:40]}] {e['prediction'][:80]}")
    rows = queue.table(on)
    pending = [r for r in rows if r[1] == "pending"]
    if pending:
        med = statistics.median(r[4] for r in pending)
        lines.append(f"Queue: {len(pending)} pending, median age {med:g}d")
    else:
        lines.append("Queue: nothing pending")
    for i, st, kind, to, age, stale in rows:
        if st in ("pending", "approved", "edited"):
            lines.append(f"  - {i} {st} {age}d {to[:50]}" + ("  STALE: make it smaller" if stale else ""))
    ls = lessons.lessons()
    lines.append(f"Lessons from {cfg['owner']['name']}'s red pen: {len(ls)}")
    for l in ls[-5:]:
        lines.append(f"  - {l['id']} {l['kind']} ({l['room']}): " +
                     (l.get("reason") or f"{l['changed']:.0%} rewritten"))
    lines.append("Then: " + cfg["wake"]["closing"])
    return "\n".join(lines)


def main():
    print(brief())


if __name__ == "__main__":
    main()
