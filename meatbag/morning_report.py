"""Write data/morning-report.md after the overnight chain: counts, how the
gremlin sort split, sample quotes per category, and anything that broke.
No model calls.

  meatbag report
"""
import collections
import json
import random

from gremlincore.home import pipeline_dir, today

from . import paths

CATEGORIES = ("gremlin", "out_there", "hurt")  # follow sort_gremlin's categories


def rows(name):
    for p in (paths.corpus(name), paths.data(name), pipeline_dir() / name):
        if p.exists():
            return [json.loads(l) for l in p.open() if l.strip()]
    return []


def report():
    out = [f"# Morning report, {today()}", ""]
    log = paths.data("overnight.log")
    out += ["## Chain log", "", "```", log.read_text().strip() if log.exists() else "(no log)", "```", ""]
    m = rows("moves_raw.jsonl")
    out += ["## Main pass (open corpus)", "", f"- rows: {len(m)}",
            f"- overrides: {sum(bool(r.get('override')) for r in m)}",
            f"- convictions: {sum(bool(r.get('conviction')) for r in m)}",
            f"- gremlin flags (first pass): {sum(bool(r.get('gremlin')) for r in m)}", ""]
    g = rows("gremlin_sorted.jsonl")
    c = collections.Counter(r.get("category") for r in g)
    out += ["## Gremlin sort", "", f"- sorted: {len(g)}"] + [f"- {k}: {v}" for k, v in c.most_common()] + [""]
    turns = {(t["conv_id"], t["idx"]): t["text"] for t in rows("turns.jsonl")}
    rng = random.Random(23)
    for cat in CATEGORIES:
        picks = [r for r in g if r.get("category") == cat and 0 < len(turns.get((r["conv_id"], r["idx"]), "")) < 300]
        out += [f"### Sample: {cat}", ""]
        for r in rng.sample(picks, min(10, len(picks))):
            out.append(f"- {(r.get('ts') or '')[:7]}: {turns[(r['conv_id'], r['idx'])].replace(chr(10), ' ')}")
        out.append("")
    fails = []
    for name in ("moves_run.log", "moves_retry.log", "sort_gremlin.log"):
        p = paths.data(name)
        if p.exists():
            n = sum("fail" in l for l in p.open())
            fails.append(f"- {name}: {n} failed calls")
    out += ["## Failures", ""] + fails + [""]
    return "\n".join(out)


def main(argv=None):
    paths.data().mkdir(parents=True, exist_ok=True)
    paths.data("morning-report.md").write_text(report())
    print(f"wrote {paths.data('morning-report.md')}")


if __name__ == "__main__":
    main()
