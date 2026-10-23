"""Pick the held-out conversations and the candidate eval cases inside them.

Whole conversations are held out, so nothing distilled into persona/ can
come from a conversation an eval case was drawn from.

  meatbag holdout   -> eval/holdout_convs.json (ids only)
                       data/eval_candidates.jsonl

Chosen case text belongs in the eval store (gremlin.toml [paths] eval,
default ~/.local/share/gremlincore/<agent>/eval), outside the home: a
wall, not a sign. Choosing the cases is `meatbag select-cases`, which is
not built yet. Delete data/eval_candidates.jsonl once cases are chosen.
"""
import json
import random
from collections import defaultdict

from gremlincore.home import config

from . import paths
from meatbag import work_guard

SEED = 20261022
FRACTION = 0.25
KINDS = {"premise", "ambition", "framing", "ethics", "tactics", "scope"}


@work_guard
def main(argv=None):
    cfg = config()
    domains = set(cfg["corpus"]["eval_domains"]) & set(cfg["corpus"]["domains"])
    turns = {}
    for l in paths.full("turns.jsonl").open():
        t = json.loads(l)
        turns[(t["conv_id"], t["idx"])] = t
    rows = [json.loads(l) for l in paths.full("moves_raw.jsonl").open()]
    tags = [json.loads(l) for l in paths.full("conv_tags.jsonl").open()]
    convs = sorted(t["conv_id"] for t in tags if t["domain"] in domains)
    rng = random.Random(SEED)
    held = set(rng.sample(convs, round(len(convs) * FRACTION)))
    paths.evaldir().mkdir(exist_ok=True)
    paths.evaldir("holdout_convs.json").write_text(json.dumps(
        {"seed": SEED, "fraction": FRACTION, "conv_ids": sorted(held)}, indent=1))
    by_conv = defaultdict(list)
    for r in rows:
        if r["conv_id"] in held and r.get("override") and r.get("kind") in KINDS:
            if len(turns[(r["conv_id"], r["idx"])]["text"]) > 80:
                by_conv[r["conv_id"]].append(r)
    n = 0
    with paths.data("eval_candidates.jsonl").open("w") as f:
        for cid, rs in by_conv.items():
            for r in rs:
                prev = turns.get((cid, r["idx"] - 1))
                f.write(json.dumps({
                    "conv_id": cid, "idx": r["idx"], "title": r["title"],
                    "kind": r["kind"], "move_local": r.get("move"),
                    "assistant": prev["text"] if prev else "",
                    "subject": turns[(cid, r["idx"])]["text"]}) + "\n")
                n += 1
    print(f"{len(held)}/{len(convs)} conversations held out; {n} candidates in them")


if __name__ == "__main__":
    main()
