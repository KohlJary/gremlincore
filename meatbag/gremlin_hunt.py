"""Gremlin hunt, stage A: a high-recall local pass over every owner turn in
the open corpus (held-out conversations are already gone).

Be honest about what this is: a small local model (qwen3:8b by default)
is a coarse recall filter. It will flag plenty that isn't gremlin and miss
some that is; sorting from adjectives alone gets most labels wrong. So it
calibrates on example pairs rather than definitions, asks for the target
and the payload (gremlin has both), and only narrows the pile. A stronger
judge reading what this pass scores 2 or 3 (stage B, not in this repo
yet) does the real work, and the owner's red pen does the rest.

The examples are invented (the Gregiverse). Put your own confirmed lines
in gremlin.toml ([gremlin] examples / near_misses) and they're used
instead.

  meatbag hunt   -> corpus/gremlin_hunt.jsonl
"""
import argparse
import json
import sys

from gremlincore.home import config

from . import paths
from .filters import is_paste
from .local_llm import chat_json
from .sort_gremlin import GREMLIN_EXAMPLES, NEAR_MISSES
from meatbag import work_guard


def system(cfg=None):
    cfg = cfg or config()
    o = cfg["owner"]["name"]
    ex = cfg["gremlin"]["examples"] or GREMLIN_EXAMPLES
    near = cfg["gremlin"]["near_misses"] or NEAR_MISSES
    label = f"{o}'s own, confirmed" if cfg["gremlin"]["examples"] else "invented examples"
    return (
        f"You spot gremlin energy in things {o} said. Gremlin is Homestuck-troll\n"
        "mischief: affectionate to people, merciless to a system, an institution,\n"
        "a billionaire, or Greg (the type who runs the mean game). It has a TARGET\n"
        "and a PAYLOAD: a real point, or a ridiculous plan that might actually work.\n\n"
        f"GREMLIN ({label}):\n" + "\n".join(f'- "{x}"' for x in ex) + "\n\n"
        "NOT GREMLIN (near misses):\n" + "\n".join(f"- {x}" for x in near) + "\n"
        "- plain tech talk, plain anger with no bit.\n\n"
        'Return JSON: {"score": 0-3, "target": "who/what it\'s aimed at, or empty",\n'
        '"payload": "the point or the plan, or empty"}.\n'
        "3 = unmistakable gremlin. 2 = probably. 1 = has a flicker. 0 = no.\n"
        "No target or no payload means 1 at most."
    )


@work_guard
def main(argv=None):
    ap = argparse.ArgumentParser(prog="meatbag hunt")
    ap.add_argument("--model")
    a = ap.parse_args(argv)
    cfg = config()
    model, owner, sys_prompt = a.model or cfg["models"]["local"], cfg["owner"]["name"], system(cfg)
    out = paths.corpus("gremlin_hunt.jsonl")
    done = set()
    if out.exists():
        done = {(r["conv_id"], r["idx"]) for r in map(json.loads, out.open())}
    todo = [t for t in map(json.loads, paths.corpus("turns.jsonl").open())
            if t["role"] == "human" and len(t["text"]) > 25 and not is_paste(t["text"], owner)
            and (t["conv_id"], t["idx"]) not in done]
    print(f"{len(todo)} to score", file=sys.stderr)
    with out.open("a") as f:
        for i, t in enumerate(todo):
            try:
                r = chat_json(model, sys_prompt, f"Conversation: {t.get('title', '')}\n\n{owner} said:\n{t['text'][:1500]}")
                s = int(r.get("score", 0))
            except Exception as e:
                print("fail", t["conv_id"], t["idx"], e, file=sys.stderr)
                continue
            f.write(json.dumps({"conv_id": t["conv_id"], "idx": t["idx"], "ts": t.get("ts"),
                                "title": t.get("title"), "score": s,
                                "target": r.get("target", ""), "payload": r.get("payload", "")}) + "\n")
            f.flush()
            if i % 500 == 0:
                print(f"{i}/{len(todo)}", file=sys.stderr)


if __name__ == "__main__":
    main()
