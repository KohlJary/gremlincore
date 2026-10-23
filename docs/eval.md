# Eval protocol

Predict the move: decision points from the owner's past where we know what
the owner did. The answer is hidden; the arms answer; the owner rates blind.
If the persona prompt does as well as the architecture, that's the finding,
and it gets written down.

## The wall

Case text lives in the eval store (`gremlin.toml` `[paths] eval`, default
`~/.local/share/gremlincore/<agent>/eval/`), outside the home. The home's
`eval/` holds only ids and hashes (`cases_index.json`) and the held-out
conversation ids (`holdout_convs.json`). The corpus the agent reads
(`corpus/`) has those conversations removed. The agent's disposition is
"go looking for leverage," so the eval gets a wall, not a sign: the
home's `.claude/settings.json` denies `eval/`, `data/` and the eval store,
and `CLAUDE.md` says the same holds for Bash.

Whole conversations are held out (`meatbag holdout`), so nothing distilled
into `persona/` can come from a conversation an eval case was drawn from.

## The arms, and what separates them

1. **Bare**: the base model, the case context, no persona.
2. **Persona prompt**: the same model told "you are <owner>," plus a
   one-paragraph description of the owner (written once, frozen,
   committed before any run).
3. **Agent**: the same model with the wake-up skill, STATUS and `persona/`.

Be honest about what arm 3 is. Until `persona/` holds distilled moves and
convictions, arm 3 is a thicker persona prompt, not an architecture, and a
comparison mostly measures prompt length. Run it once there's something
in MOVES to test.

## Rating

- **Neutralize style first.** A model rewrites every arm's answer into
  flat, neutral prose before the owner sees it, keeping the move and
  dropping the voice, and stripping the answerer's references to its own
  tools and files (a ledger, a queue, a status file). Otherwise the arm
  that swears and mentions Greg is obvious in a sentence, and the owner is
  rating vibe, not moves.
- **Recent cases last.** Cases from the last month are marked; the owner
  may remember those decisions, so they're rated after the rest and
  reported separately.
- **Order is shuffled** per case, and the key stays outside the home until
  all ratings are in.

## What counts as "same move"

Score both levels and report both:

- **Direction**: the same kind of move (raise the ambition, question the
  premise, narrow the scope, reframe the audience).
- **Call**: the same specific decision.

## Pre-registered runs (`meatbag arms`)

For a bet in the ledger that an eval run will settle, write the protocol
down before the run, in `<home>/eval/ledger/`:

- `situation.md`: the shared context every arm gets.
- `persona_prompt.md`: the persona arm's paragraph, frozen.
- `prompts.md`: one block per prompt, `P1 (ledger #N): <the prompt>`.

Each arm is a sealed `claude -p` call from an empty directory with no
tools, no `CLAUDE.md`, no project memory, and only its system prompt. Each
arm answers every prompt. A separate neutralizer call rewrites every
answer; answers are shuffled per prompt; the key and raw outputs go to
`<eval store>/ledger_runs/`. The owner rates blind, against the falsifiers
recorded in `ledger/predictions.jsonl`. Whoever built the run doesn't score it.

`[eval] strip_status_sections` names STATUS sections to cut from the agent
arm (for example, a list of jobs the agent wrote for itself that would
hand it the answer). When it's set, a second agent arm runs with them left
in.

## Amendments

If something has to change after a run and before any rating, write it
down as a dated amendment here, in the home, and say what was and wasn't
regenerated. Worked example of the shape: *the first neutralizer pass left
a giveaway word in exactly the agent arms' answers, which would unblind
them. `meatbag arms --renormalize` re-ran only the neutralizer over the
same raw answers with the same shuffle key. No answer was regenerated.
The person who ran it checked only for giveaway words and did not read or
score the answers.*

## What isn't built

Choosing the cases into the eval store and writing `cases_index.json`
(`meatbag select-cases` is a stub that prints the manual steps).
