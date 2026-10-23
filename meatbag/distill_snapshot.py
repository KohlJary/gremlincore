"""Snapshot for the distiller: only what it may read.

Held-out conversations removed, pastes dropped, do-not-generalize topics
kept out of the moves file, each row joined with the owner's turn text,
the assistant default it answered, and its era (gremlin.toml [corpus] eras).

  meatbag snapshot   -> data/distill/{convictions,moves}.jsonl
"""
import json

from gremlincore.home import config

from . import paths
from .filters import generalizable_move, is_paste
from meatbag import work_guard


def era(ts, cfg=None):
    """The era name for an ISO timestamp. Eras are [{name, before}], oldest
    first; anything after the last cutoff is last_era."""
    cfg = cfg or config()
    ts = ts or ""
    for e in cfg["corpus"]["eras"]:
        if ts < e["before"]:
            return e["name"]
    return cfg["corpus"]["last_era"]


@work_guard
def main(argv=None):
    cfg = config()
    owner, skip = cfg["owner"]["name"], set(cfg["corpus"]["skip_in_distill"])
    topics = cfg["filters"]["do_not_generalize"]
    held = set(json.loads(paths.evaldir("holdout_convs.json").read_text())["conv_ids"])
    turns = {}
    for l in paths.full("turns.jsonl").open():
        t = json.loads(l)
        turns[(t["conv_id"], t["idx"])] = t
    out = paths.data("distill"); out.mkdir(parents=True, exist_ok=True)
    nc = nm = 0
    with (out / "convictions.jsonl").open("w") as fc, (out / "moves.jsonl").open("w") as fm:
        for l in paths.full("moves_raw.jsonl").open():
            r = json.loads(l)
            if r["conv_id"] in held or r.get("domain") in skip:
                continue
            t = turns.get((r["conv_id"], r["idx"]))
            if not t or is_paste(t["text"], owner):
                continue
            base = {"era": era(r["ts"], cfg), "ts": (r["ts"] or "")[:10], "title": r["title"],
                    "domain": r["domain"], "subject": t["text"][:900]}
            if r.get("conviction"):
                fc.write(json.dumps({**base, "conviction_local": r["conviction"],
                                     "theme": r.get("theme"), "quote": r.get("quote")}) + "\n"); nc += 1
            if r.get("override") and generalizable_move(r, topics):
                prev = turns.get((r["conv_id"], r["idx"] - 1))
                a = prev["text"] if prev else ""
                a = a if len(a) < 600 else a[:300] + " [...] " + a[-300:]
                fm.write(json.dumps({**base, "assistant_before": a, "move_local": r.get("move"),
                                     "rejected_local": r.get("default_rejected"), "kind": r.get("kind")}) + "\n"); nm += 1
    print(f"convictions {nc}, moves {nm} -> {out}")


if __name__ == "__main__":
    main()
