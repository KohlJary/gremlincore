"""The queue: drafts waiting for the owner. The agent's outbox, and the
owner's send button.

Nothing here sends anything. `approve` means the owner is willing; `sent`
is recorded when the owner says it went out. `by` defaults to the owner
named in gremlin.toml.

  gremlin queue list
  gremlin queue show 0002
  gremlin queue approve 0002
  gremlin queue edit 0002 [--by NAME] [--from-file new.md]
  gremlin queue veto 0002 --reason "missed the point"
  gremlin queue sent 0002
"""
import argparse
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from . import ledger
from .home import git_date, owner_id, root, set_field, split, today

ORIGINAL = "<!-- original -->"
STATUSES = ("pending", "approved", "edited", "vetoed", "sent")
STALE_AFTER_DAYS = 5


@dataclass
class Item:
    path: Path
    meta: dict
    body: str

    @property
    def id(self):
        return self.path.name.split("-", 1)[0]

    @property
    def draft(self):
        """The current draft, without the kept original or the notes after it."""
        return self.body.split(ORIGINAL)[0]

    @property
    def original(self):
        return self.body.split(ORIGINAL, 1)[1] if ORIGINAL in self.body else None

    @property
    def created(self):
        return self.meta.get("created") or git_date(self.path, first=True) or today()

    def age_days(self, on=None):
        return (date.fromisoformat(on or today()) - date.fromisoformat(self.created)).days


def qdir():
    return root() / "queue"


def items():
    out = []
    for p in sorted(qdir().glob("[0-9]*.md")):
        meta, _, body = split(p.read_text())
        out.append(Item(p, meta, body))
    return out


def get(item_id):
    for it in items():
        if it.id == item_id.zfill(4):
            return it
    raise SystemExit(f"no queue item {item_id}")


def _write(it, **fields):
    text = it.path.read_text()
    for k, v in fields.items():
        text = set_field(text, k, v)
    it.path.write_text(text)
    meta, _, body = split(text)
    return Item(it.path, meta, body)


def approve(it, by=None):
    by = by or owner_id()
    return _write(it, status="approved", approved=today(), approved_by=by)


def veto(it, reason, by=None):
    by = by or owner_id()
    if not reason.strip():
        raise SystemExit("a veto needs a reason: that's how the agent learns")
    return _write(it, status="vetoed", vetoed=today(), vetoed_by=by, veto_reason=reason.replace("\n", " "))


def edit(it, new_draft, by=None):
    """Replace the draft. The first original is kept below ORIGINAL, forever."""
    by = by or owner_id()
    if new_draft.strip() == it.draft.strip():
        return it
    meta_text = it.path.read_text()
    head_end = len(meta_text) - len(it.body)
    original = it.original if it.original is not None else "\n\n" + it.draft.strip() + "\n"
    new_body = "\n" + new_draft.strip() + "\n\n" + ORIGINAL + original
    it.path.write_text(meta_text[:head_end] + new_body)
    meta, _, body = split(it.path.read_text())
    return _write(Item(it.path, meta, body), status="edited", edited=today(), edited_by=by)


def mark_sent(it, by=None):
    by = by or owner_id()
    it = _write(it, status="sent", sent=today(), sent_by=by)
    pid = it.meta.get("prediction", "").split()[0] if it.meta.get("prediction") else ""
    if pid.isdigit():
        ledger.stamp_sent(int(pid), today())
    return it


def edit_interactive(it, by):
    with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False) as f:
        f.write(it.draft.strip() + "\n")
        name = f.name
    subprocess.run([os.environ.get("EDITOR", "nano"), name])
    new = Path(name).read_text()
    os.unlink(name)
    return edit(it, new, by)


def table(on=None):
    rows = []
    for it in items():
        stale = it.meta.get("status") == "pending" and it.age_days(on) >= STALE_AFTER_DAYS
        rows.append((it.id, it.meta.get("status", "?"), it.meta.get("kind", ""),
                     it.meta.get("to", ""), it.age_days(on), stale))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    for c in ("show", "approve", "sent"):
        sub.add_parser(c).add_argument("id")
    e = sub.add_parser("edit"); e.add_argument("id"); e.add_argument("--by")
    e.add_argument("--from-file")
    v = sub.add_parser("veto"); v.add_argument("id"); v.add_argument("--reason", required=True)
    v.add_argument("--by")
    a = ap.parse_args(argv)
    if a.cmd == "list":
        for i, st, kind, to, age, stale in table():
            print(f"{i}  {st:9} {kind:6} {age:3}d  {to}" + ("   (stale: make it smaller)" if stale else ""))
        return
    it = get(a.id)
    if a.cmd == "show":
        print(it.path.read_text())
    elif a.cmd == "approve":
        approve(it); print(f"{it.id} approved. Nothing was sent; that's your finger.")
    elif a.cmd == "veto":
        veto(it, a.reason, a.by); print(f"{it.id} vetoed: {a.reason}")
    elif a.cmd == "edit":
        it2 = edit(it, Path(a.from_file).read_text(), a.by) if a.from_file else edit_interactive(it, a.by)
        print(f"{it.id} {'edited' if it2 is not it else 'unchanged'}")
    elif a.cmd == "sent":
        mark_sent(it); print(f"{it.id} marked sent {today()}")


if __name__ == "__main__":
    sys.exit(main())
