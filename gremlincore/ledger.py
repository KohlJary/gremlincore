"""The prediction ledger: bets recorded before they're checked, and closed.

  gremlin ledger due
  gremlin ledger add --by AGENT --prediction ... --falsifier ... [--check-after-days 30]
  gremlin ledger settle 3 --hit yes --outcome "Uncle Ray RSVPed in 2 days, with a chair"
  gremlin ledger score

Fields beyond the original prose ones:
  check_by          ISO date the bet should be checked by (null until known)
  check_after_days  days after a linked queue item is sent; a list means
                    several checkpoints (check_by is the earliest unsettled)
  awaiting          who the bet is waiting on, if not a date (e.g. owner-rating)
  hit               true / false / null once settled
"""
import argparse
import json
from datetime import date, timedelta

from .home import agent, root, today


def path():
    return root() / "ledger" / "predictions.jsonl"


def entries():
    p = path()
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def _save(es):
    path().write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in es))


def add(by, prediction, falsifier, why="", check_when="", check_after_days=None, check_by=None):
    if not falsifier.strip():
        raise SystemExit("no falsifier, no bet: that's a vibe with a timestamp")
    es = entries()
    e = {"id": (max(x["id"] for x in es) + 1) if es else 1, "date": today(), "by": by,
         "prediction": prediction, "why": why, "falsifier": falsifier, "check_when": check_when,
         "check_by": check_by, "check_after_days": check_after_days, "outcome": None, "hit": None}
    es.append(e)
    _save(es)
    return e


def stamp_sent(bet_id, sent_date):
    """A linked queue item went out: date the bet's checkpoints from the send."""
    es = entries()
    for e in es:
        if e["id"] == bet_id:
            days = e.get("check_after_days") or 30
            first = min(days) if isinstance(days, list) else days
            e["sent"] = sent_date
            e["check_by"] = (date.fromisoformat(sent_date) + timedelta(days=first)).isoformat()
    _save(es)


def due(on=None):
    on = on or today()
    out = []
    for e in entries():
        if e.get("outcome") is not None:
            continue
        if e.get("awaiting"):
            out.append((e, f"waiting on {e['awaiting']}"))
        elif e.get("check_by") and e["check_by"] <= on:
            out.append((e, f"due {e['check_by']}"))
    return out


def settle(bet_id, outcome, hit):
    es = entries()
    for e in es:
        if e["id"] == bet_id:
            e["outcome"] = outcome
            e["hit"] = hit
            e["settled"] = today()
            e.pop("awaiting", None)
            _save(es)
            return e
    raise SystemExit(f"no bet #{bet_id}")


def score():
    """Hit rate by who made the bet. The owner's bets and the agent's stay apart."""
    me = agent()
    by = {}
    for e in entries():
        who = me if e["by"].startswith(me) else e["by"].split()[0]
        s = by.setdefault(who, {"bets": 0, "settled": 0, "hits": 0})
        s["bets"] += 1
        if e.get("hit") is not None:
            s["settled"] += 1
            s["hits"] += bool(e["hit"])
    return by


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("due"); sub.add_parser("score")
    a_ = sub.add_parser("add")
    for f in ("--by", "--prediction", "--falsifier"):
        a_.add_argument(f, required=True)
    a_.add_argument("--why", default=""); a_.add_argument("--check-when", default="")
    a_.add_argument("--check-after-days", type=int)
    s_ = sub.add_parser("settle"); s_.add_argument("id", type=int)
    s_.add_argument("--outcome", required=True); s_.add_argument("--hit", choices=["yes", "no", "unclear"], required=True)
    a = ap.parse_args(argv)
    if a.cmd == "due":
        for e, why in due():
            print(f"#{e['id']} [{why}] {e['prediction'][:100]}")
    elif a.cmd == "score":
        for who, s in score().items():
            rate = f"{s['hits']}/{s['settled']}" if s["settled"] else "none settled"
            print(f"{who}: {s['bets']} bets, hits {rate}")
    elif a.cmd == "add":
        e = add(a.by, a.prediction, a.falsifier, a.why, a.check_when, a.check_after_days)
        print(f"bet #{e['id']} recorded")
    elif a.cmd == "settle":
        hit = {"yes": True, "no": False, "unclear": None}[a.hit]
        settle(a.id, a.outcome, hit); print(f"#{a.id} settled")


if __name__ == "__main__":
    main()
