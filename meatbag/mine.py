"""Local-model passes over data/turns.jsonl.

  tag:   one domain label per conversation  -> data/conv_tags.jsonl
  moves: for each of the owner's turns, did they override the assistant
         (and with what move), state a conviction (value, belief, mission),
         or go gremlin? Read in the configured domain order, engineering
         last.                              -> data/moves_raw.jsonl

Both append and skip what is already done, so they can be stopped and rerun.
The owner's name and the domain list come from gremlin.toml.

  meatbag mine tag
  meatbag mine moves
"""
import argparse
import json
import sys
import time
from collections import defaultdict

from gremlincore.home import config

from . import paths
from .local_llm import chat_json

GLOSS = {
    "strategy": "planning the mission, priorities, positioning, what to do next",
    "outreach": "contacting people, pitches, posts, getting attention, publishing",
    "ops": "logistics, deadlines, money, admin",
    "research": "ideas, theory, papers",
    "writing": "drafting essays or prose",
    "creative": "games, fiction, art, play",
    "engineering": "writing or debugging code",
    "personal": "health, feelings, relationships, life",
    "other": "anything else",
}


def tag_system(owner, domains):
    gloss = " ".join(f"{d} = {GLOSS[d]}." for d in domains if d in GLOSS)
    return (f"You label conversations between a person ({owner}) and an AI assistant. "
            "Return JSON: {\"domain\": one of " + json.dumps(domains) + ", "
            "\"secondary\": one of the same or null}. " + gloss)


def move_system(o):
    return (
        f"You study how {o} thinks: their values, convictions, mission, and the moves "
        f"they make. You see what an AI assistant said and {o}'s reply. Answer three "
        "separate questions.\n"
        f"1. OVERRIDE: does {o}'s reply reject the assistant's framing, correct it, "
        "redirect it, raise the ambition, cut through caution, or say the "
        "conventional approach is wrong? Most replies are NOT overrides. Agreement, "
        "thanks, new questions, changing the subject, adding a new idea, or pasted "
        "material are not overrides; there must be something the assistant said "
        f"or assumed that {o} pushes against.\n"
        f"2. CONVICTION: does {o} state a belief, value, ethical commitment, piece "
        "of their mission, or a principle about how to work or live? Only what "
        f"{o} asserts, not what the assistant said.\n"
        f"3. GREMLIN: is {o} being funny, irreverent, absurd, profane for effect, "
        "or proposing something ridiculous that might actually work?\n"
        "Return JSON: {\"override\": true|false, "
        "\"move\": if override, one sentence naming the move in general reusable "
        "form, in your own words, without naming this conversation's topic, else null, "
        f"\"default_rejected\": if override, the assistant default {o} rejected, in a "
        "few words, else null, "
        "\"kind\": if override, one of [premise, ambition, framing, ethics, tactics, "
        "tone, scope, factual, other], else null, "
        f"\"conviction\": if {o} states one, the conviction as a general statement in "
        f"the first person, faithful to what {o} said, else null, "
        "\"theme\": if conviction, one of [mission, ethics, ai-personhood, method, "
        "strategy, craft, politics, self, relationships, other], else null, "
        "\"gremlin\": true|false, "
        "\"gremlin_style\": if gremlin, a few words naming the kind of humor "
        "(e.g. absurd escalation, deadpan, profane emphasis, self-deprecation, "
        "load-bearing bit), else null, "
        f"\"quote\": if override, conviction or gremlin, {o}'s most telling words, copied "
        "exactly, at most 30 words, else null}."
    )


def _convs():
    convs = defaultdict(list)
    with paths.data("turns.jsonl").open() as f:
        for line in f:
            t = json.loads(line)
            convs[t["conv_id"]].append(t)
    return convs


def _done(path, key):
    if not path.exists():
        return set()
    return {tuple(json.loads(l)[k] for k in key) for l in path.open()}


def tag(model, cfg=None):
    cfg = cfg or config()
    owner, domains = cfg["owner"]["name"], cfg["corpus"]["domains"]
    system = tag_system(owner, domains)
    out = paths.data("conv_tags.jsonl")
    done = _done(out, ["conv_id"])
    convs = _convs()
    with out.open("a") as f:
        for cid, ts in convs.items():
            if (cid,) in done:
                continue
            first = [t["text"][:400] for t in ts if t["role"] == "human"][:3]
            user = (f"Title: {ts[0]['title']}\nSummary: {ts[0]['summary'][:1500]}\n"
                    f"{owner}'s first messages:\n" + "\n---\n".join(first))
            try:
                r = chat_json(model, system, user)
            except Exception as e:
                print("tag fail", cid, e, file=sys.stderr)
                continue
            f.write(json.dumps({"conv_id": cid, "title": ts[0]["title"],
                                "domain": r.get("domain"),
                                "secondary": r.get("secondary"),
                                "human_turns": sum(t["role"] == "human" for t in ts)}) + "\n")
            f.flush()


def moves(model, cfg=None, skip_domains=()):
    cfg = cfg or config()
    owner = cfg["owner"]["name"]
    system = move_system(owner)
    tags = {json.loads(l)["conv_id"]: json.loads(l) for l in paths.data("conv_tags.jsonl").open()}
    out = paths.data("moves_raw.jsonl")
    done = _done(out, ["conv_id", "idx"])
    convs = _convs()
    todo = []
    for cid, ts in convs.items():
        tg = tags.get(cid)
        if not tg or tg["domain"] in skip_domains:
            continue
        for prev, cur in zip(ts, ts[1:]):
            if prev["role"] == "assistant" and cur["role"] == "human" and (cid, cur["idx"]) not in done:
                todo.append((tg, prev, cur))
    order = cfg["corpus"].get("domain_order") or cfg["corpus"]["domains"]
    rank = {d: i for i, d in enumerate(order)}
    todo.sort(key=lambda x: rank.get(x[0]["domain"], len(rank)))
    print(f"{len(todo)} turns to read", file=sys.stderr)
    t0 = time.time()
    with out.open("a") as f:
        for i, (tg, prev, cur) in enumerate(todo):
            a = prev["text"]
            a = a if len(a) < 1800 else a[:900] + "\n[...]\n" + a[-900:]
            user = (f"Conversation: {tg['title']} ({tg['domain']})\n\n"
                    f"ASSISTANT SAID:\n{a}\n\n{owner.upper()} REPLIED:\n{cur['text'][:2000]}")
            try:
                r = chat_json(model, system, user)
            except Exception as e:
                print("move fail", cur["conv_id"], cur["idx"], e, file=sys.stderr)
                continue
            f.write(json.dumps({"conv_id": cur["conv_id"], "idx": cur["idx"],
                                "title": tg["title"], "domain": tg["domain"],
                                "ts": cur["ts"], **r}) + "\n")
            f.flush()
            if i % 100 == 0:
                print(f"{i}/{len(todo)} {time.time()-t0:.0f}s", file=sys.stderr)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="meatbag mine")
    ap.add_argument("stage", choices=["tag", "moves"])
    ap.add_argument("--model", help="default: [models] local in gremlin.toml")
    a = ap.parse_args(argv)
    cfg = config()
    {"tag": tag, "moves": moves}[a.stage](a.model or cfg["models"]["local"], cfg)


if __name__ == "__main__":
    main()
