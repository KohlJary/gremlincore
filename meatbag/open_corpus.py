"""Build corpus/: the corpus the agent may read, with held-out
conversations removed. Then move the full pipeline files out of the home
(to gremlin.toml [paths] pipeline), so the only copy of a held-out
conversation inside the home is none.

  meatbag open-corpus   (after the local passes finish)
"""
import json
import shutil

from gremlincore.home import pipeline_dir

from . import paths

FULL = ["turns.jsonl", "moves_raw.jsonl", "conv_tags.jsonl", "gremlin_sorted.jsonl"]


def main(argv=None):
    held = set(json.loads(paths.evaldir("holdout_convs.json").read_text())["conv_ids"])
    out = paths.corpus()
    out.mkdir(parents=True, exist_ok=True)
    pipe = pipeline_dir()
    for name in FULL:
        src = paths.data(name)
        if not src.exists():
            continue
        kept = dropped = 0
        with src.open() as f, (out / name).open("w") as g:
            for line in f:
                if json.loads(line).get("conv_id") in held:
                    dropped += 1
                    continue
                g.write(line)
                kept += 1
        pipe.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), pipe / name)
        print(f"{name}: {kept} kept in corpus, {dropped} held out; full copy -> {pipe}")


if __name__ == "__main__":
    main()
