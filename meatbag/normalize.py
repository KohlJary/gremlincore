"""Read AI chat exports into one turn schema.

Each line of the output is one turn:
  {source, conv_id, title, summary, conv_created, idx, role, text, ts}
role is "human" or "assistant". Works on the export zip or the
conversations.json inside it. Claude and ChatGPT exports are told apart
by shape (docs/export-formats.md).

  meatbag normalize path/to/export.zip [more.zip ...]   -> data/turns.jsonl
"""
import argparse
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from gremlincore.home import root


def _load(path):
    path = Path(path).expanduser()
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as z:
            name = next(n for n in z.namelist() if n.endswith("conversations.json"))
            return json.loads(z.read(name))
    return json.loads(path.read_text())


def _claude_text(m):
    if m.get("text"):
        return m["text"]
    parts = [b.get("text", "") for b in m.get("content") or []
             if isinstance(b, dict) and b.get("type") == "text"]
    return "\n".join(p for p in parts if p)


def claude_turns(convs):
    for c in convs:
        idx = 0
        for m in c.get("chat_messages", []):
            text = _claude_text(m).strip()
            if not text:
                continue
            yield {
                "source": "claude", "conv_id": c["uuid"], "title": c.get("name") or "",
                "summary": c.get("summary") or "", "conv_created": c.get("created_at"),
                "idx": idx, "role": "human" if m["sender"] == "human" else "assistant",
                "text": text, "ts": m.get("created_at"),
            }
            idx += 1


def _gpt_path(c):
    """The visible branch: walk parents back from current_node."""
    mapping, node, path = c["mapping"], c.get("current_node"), []
    while node:
        path.append(mapping[node])
        node = mapping[node].get("parent")
    return reversed(path)


def gpt_turns(convs):
    for c in convs:
        created = c.get("create_time")
        conv_created = (datetime.fromtimestamp(created, timezone.utc).isoformat()
                        if created else None)
        idx = 0
        for n in _gpt_path(c):
            m = n.get("message")
            if not m:
                continue
            role = (m.get("author") or {}).get("role")
            if role not in ("user", "assistant"):
                continue
            parts = (m.get("content") or {}).get("parts") or []
            text = "\n".join(p for p in parts if isinstance(p, str)).strip()
            if not text:
                continue
            ts = m.get("create_time")
            yield {
                "source": "gpt", "conv_id": c.get("conversation_id") or c.get("id"),
                "title": c.get("title") or "", "summary": "", "conv_created": conv_created,
                "idx": idx, "role": "human" if role == "user" else "assistant",
                "text": text,
                "ts": datetime.fromtimestamp(ts, timezone.utc).isoformat() if ts else None,
            }
            idx += 1


def turns(path):
    convs = _load(path)
    if convs and "mapping" in convs[0]:
        return gpt_turns(convs)
    return claude_turns(convs)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="meatbag normalize")
    ap.add_argument("exports", nargs="+")
    ap.add_argument("-o", "--out", help="default: <home>/data/turns.jsonl")
    a = ap.parse_args(argv)
    out = Path(a.out) if a.out else root() / "data/turns.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out.open("w") as f:
        for p in a.exports:
            for t in turns(p):
                f.write(json.dumps(t) + "\n")
                n += 1
    print(f"{n} turns -> {out}", file=sys.stderr)


if __name__ == "__main__":
    from meatbag import refuse_work_home
    refuse_work_home()
    main()
