"""Second local pass: sort the turns the first pass flagged as gremlin into
gremlin (GREMLIN.md), out_there (OUT_THERE.md), funny, and hurt (HURT.md).

A first pass tends to lump together real gremlin, out-there strangeness,
plain jokes, and hurt (it reads swearing as humor). This pass sorts each
flagged turn against definitions and examples. The examples below are
invented (the Gregiverse); put your own confirmed ones in gremlin.toml
([gremlin] examples / near_misses) and they're used instead.

  meatbag sort   -> data/gremlin_sorted.jsonl
"""
import argparse
import json
import sys

from gremlincore.home import config

from . import paths
from .filters import is_paste
from .local_llm import chat_json

# Invented. Nobody said these; they show the shape.
GREMLIN_EXAMPLES = [
    "Greg wants OKRs for the barbecue. Fine. Key result one: Greg returns the chair he owes Uncle Ray.",
    "the vendor wants a three-year contract for a spreadsheet, so I will simply become the spreadsheet",
    "putting 'nobody suggests Boca' in the HOA bylaws, in a font Chad can't read",
    "the airline won't refund the delay, so I'm entering it in their in-flight film festival as a documentary",
]
OUT_THERE_EXAMPLES = [
    "a parking garage is a cathedral for cars that forgot how to pray",
    "Uncle Ray's grill has outlived three of his marriages; at some point it's the patriarch",
]
NEAR_MISSES = [
    "out there, a strange way of SEEING with no target: \"a parking garage is a cathedral for cars that forgot how to pray\"",
    "excitement: \"it ran. first try. I'm scared.\"",
    "hurt, even with swearing: \"I'm so fucking tired of carrying all of this by myself.\"",
    "a plain joke with no target: \"Chad named his boat Boatimus Prime.\"",
]


def _quoted(xs):
    return "; ".join(f"'{x}'" for x in xs)


def system(cfg=None):
    cfg = cfg or config()
    o = cfg["owner"]["name"]
    mine = cfg["gremlin"]["examples"]
    gremlin_ex = mine or GREMLIN_EXAMPLES
    return (
        f"You sort things {o} said into one category. Return JSON: "
        "{\"category\": one of [gremlin, out_there, funny, hurt, none], "
        "\"why\": a few words}.\n"
        "gremlin: mischief with a target and a payload. Irreverence aimed at "
        "power, a dumb system, or a respectable trap, that makes a real point "
        "or could actually work. Think Homestuck troll: the trolling is "
        "affectionate toward people and merciless toward the system. Examples: "
        + _quoted(gremlin_ex) + ".\n"
        "out_there: a strange, cosmic or lateral way of seeing something; taking "
        "an absurd premise seriously for a moment. Examples: "
        + _quoted(OUT_THERE_EXAMPLES) + ".\n"
        "funny: a joke or playful aside with no target and no strange angle.\n"
        f"hurt: {o} is in pain, frustrated, grieving, lonely, unseen or "
        "exhausted, even if they swear or laugh. Swearing alone never makes "
        "something a joke. Hurt is as important as the others; sort it carefully.\n"
        "none: none of these."
    )


def main(argv=None):
    ap = argparse.ArgumentParser(prog="meatbag sort")
    ap.add_argument("--model")
    a = ap.parse_args(argv)
    cfg = config()
    model, owner, sys_prompt = a.model or cfg["models"]["local"], cfg["owner"]["name"], system(cfg)
    turns = {}
    for l in paths.data("turns.jsonl").open():
        t = json.loads(l)
        turns[(t["conv_id"], t["idx"])] = t
    out = paths.data("gremlin_sorted.jsonl")
    done = {(json.loads(l)["conv_id"], json.loads(l)["idx"]) for l in out.open()} if out.exists() else set()
    rows = [json.loads(l) for l in paths.data("moves_raw.jsonl").open()]
    todo = [r for r in rows if r.get("gremlin") and (r["conv_id"], r["idx"]) not in done]
    print(f"{len(todo)} to sort", file=sys.stderr)
    with out.open("a") as f:
        for r in todo:
            t = turns[(r["conv_id"], r["idx"])]["text"]
            if is_paste(t, owner):
                continue
            try:
                res = chat_json(model, sys_prompt, f"Conversation: {r['title']}\n\n{owner} said:\n{t[:1500]}")
            except Exception as e:
                print("fail", e, file=sys.stderr)
                continue
            f.write(json.dumps({"conv_id": r["conv_id"], "idx": r["idx"], "ts": r["ts"],
                                "title": r["title"], **res}) + "\n")
            f.flush()


if __name__ == "__main__":
    main()
