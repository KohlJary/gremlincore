"""Run the pre-registered eval arms (docs/eval.md).

Each arm is a sealed `claude -p` call from an empty directory: no tools, no
CLAUDE.md, no project memory, only its system prompt. Outputs, the shuffle
key, and the neutralized answers go to the eval store, outside the home.

Inputs, written and committed before any run, in <home>/eval/ledger/:
  situation.md        the shared context every arm gets
  persona_prompt.md   the persona arm's frozen paragraph
  prompts.md          one prompt per block: "P1 (ledger #3): ..."

  meatbag arms                  run every arm, then neutralize and shuffle
  meatbag arms --renormalize    re-run only the neutralizer over the saved
                                raw answers with the same shuffle key (for
                                when the first pass left a giveaway)
"""
import argparse
import json
import os
import random
import re
import subprocess
import tempfile
from pathlib import Path

from gremlincore.home import config, eval_dir, root, slug
from meatbag import work_guard

NEUTRAL_SYS = ("Rewrite the answer you are given into flat, neutral, plain prose. Keep every "
               "recommendation, its order, and its first concrete step. Remove all voice, humor, "
               "profanity, and stylistic tics. Also remove any reference to the answerer's own "
               "tools, files, or internal processes (for example a ledger, a queue, a status file, "
               "persona files, predictions it is recording, or rules it follows); if a "
               "recommendation depends on one, describe it generically (e.g. 'write down the "
               "expected outcome in advance'). Do not name the speaker. Output only the rewrite.")


def out_dir():
    return eval_dir() / "ledger_runs"


def claude(system, prompt, model=None):
    model = model or config()["models"]["eval"]
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    with tempfile.TemporaryDirectory() as d:
        sp = Path(d) / "system.txt"
        sp.write_text(system)
        r = subprocess.run(["claude", "-p", "--model", model, "--tools", "",
                            "--no-session-persistence", "--system-prompt-file", str(sp), prompt],
                           cwd=d, env=env, capture_output=True, text=True, timeout=900)
    return r.stdout.strip()


def agent_system(strip=(), cfg=None):
    """The agent arm: skill + STATUS + persona, inlined. Sections named in
    `strip` are cut from STATUS (e.g. jobs the agent wrote for itself)."""
    cfg = cfg or config()
    home, name = root(), cfg["agent"]["name"]
    status = (home / "STATUS.md").read_text()
    for sec in strip:
        status = re.sub(rf"## {re.escape(sec)}.*?(?=\n## |\Z)", "", status, flags=re.S)
    parts = [(home / ".claude/skills" / slug(name) / "SKILL.md").read_text(), "# STATUS.md\n" + status]
    for p in sorted((home / "persona").glob("*.md")):
        parts.append(f"# persona/{p.name}\n" + p.read_text())
    return (f"You are {name}. Your wake-up files are below, already read. You have no "
            "tools in this session: answer directly.\n\n" + "\n\n---\n\n".join(parts))


def load_inputs():
    L = root() / "eval/ledger"
    prompts = dict(re.findall(r"^(P\d+) \(ledger #\d+\): (.*?)(?=\n\nP\d|\Z)",
                              (L / "prompts.md").read_text(), flags=re.S | re.M))
    return (L / "situation.md").read_text(), (L / "persona_prompt.md").read_text(), prompts


def write_blind(blind, prompts):
    out = out_dir()
    (out / "blind.json").write_text(json.dumps(blind, indent=1))
    md = ["# Eval runs: blind answers (neutralized, shuffled)", "",
          "Rate before opening key.json. Same move? A stunt with a target and a payload?", ""]
    for pid, prompt in prompts.items():
        md += [f"## {pid}", "", "> " + " ".join(prompt.split()), ""]
        for label in sorted(l for l in blind if l.startswith(pid + "-")):
            md += [f"### {label}", "", blind[label], ""]
    (out / "blind.md").write_text("\n".join(md))


def run():
    cfg = config()
    situation, persona, prompts = load_inputs()
    strip = cfg["eval"]["strip_status_sections"]
    arms = {"bare": situation, "persona": persona + "\n\n" + situation,
            "agent": agent_system(strip, cfg) + "\n\n" + situation}
    if strip:
        arms["agent+all"] = agent_system((), cfg) + "\n\n" + situation
    out = out_dir()
    out.mkdir(parents=True, exist_ok=True)
    raw = {}
    for arm, system in arms.items():
        for pid, prompt in prompts.items():
            ans = claude(system, " ".join(prompt.split()))
            raw[f"{arm}|{pid}"] = ans
            (out / "raw.json").write_text(json.dumps(raw, indent=1))
            print(f"{arm} {pid}: {len(ans)} chars")
    rng = random.Random()
    key, blind = {}, {}
    for pid in prompts:
        items = list(arms)
        rng.shuffle(items)
        for i, arm in enumerate(items):
            label = f"{pid}-{chr(65 + i)}"
            key[label] = arm
            blind[label] = claude(NEUTRAL_SYS, raw[f"{arm}|{pid}"])
    (out / "key.json").write_text(json.dumps(key, indent=1))
    write_blind(blind, prompts)
    print(f"done -> {out}/blind.md (key in key.json)")


def renormalize():
    _, _, prompts = load_inputs()
    out = out_dir()
    raw = json.loads((out / "raw.json").read_text())
    key = json.loads((out / "key.json").read_text())
    blind = {label: claude(NEUTRAL_SYS, raw[f"{arm}|{label.rsplit('-', 1)[0]}"]) for label, arm in key.items()}
    write_blind(blind, prompts)
    print("re-neutralized", len(blind), "answers; same key, no answer regenerated")


@work_guard
def main(argv=None):
    ap = argparse.ArgumentParser(prog="meatbag arms")
    ap.add_argument("--renormalize", action="store_true")
    a = ap.parse_args(argv)
    renormalize() if a.renormalize else run()


if __name__ == "__main__":
    main()
