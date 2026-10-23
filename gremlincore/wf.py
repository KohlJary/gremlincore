"""The WF ledger: the agent's mistakes, counted, so it learns from them.
(Spec: docs/ledger.md.)

  gremlin wf                    # running count + recent incidents
  gremlin wf add --what ... --who ... --wf N --root-cause ... \
      --change ... [--commit SHA] [--found-by NAME]
"""
import argparse
import json
from datetime import date
from . import home


def ledger_path():
    return home.root() / "ledger" / "wf.jsonl"


def entries():
    p = ledger_path()
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def show(recent=10):
    es = entries()
    total = sum(e.get("wf", 0) for e in es)
    print(f"WF to date: {total} across {len(es)} incident(s). Target: zero.")
    for e in es[-recent:]:
        print(f"- #{e['id']} {e['date']} [{e.get('wf', 0)} WF] {e['what']}")
        print(f"    root cause: {e.get('root_cause')}")
        print(f"    changed:    {e.get('change')}")


def add(a):
    if not a.change.strip():
        raise SystemExit("change is required: an entry with no change is a mistake you plan to make again")
    es = entries()
    e = {"id": (es[-1]["id"] + 1) if es else 1, "date": home.today(),
         "what": a.what, "who": a.who, "wf": a.wf, "root_cause": a.root_cause,
         "change": a.change, "commit": a.commit, "found_by": a.found_by or home.slug(home.agent())}
    with ledger_path().open("a") as f:
        f.write(json.dumps(e) + "\n")
    show(recent=1)


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("add")
    p.add_argument("--what", required=True)
    p.add_argument("--who", required=True)
    p.add_argument("--wf", type=int, required=True)
    p.add_argument("--root-cause", required=True)
    p.add_argument("--change", required=True)
    p.add_argument("--commit")
    p.add_argument("--found-by")
    a = ap.parse_args(argv)
    add(a) if a.cmd == "add" else show()


if __name__ == "__main__":
    main()
