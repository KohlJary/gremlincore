"""Pipeline steps that don't exist yet. Each prints what it will do and
exits non-zero, so a script that chains them stops instead of pretending.
"""
import sys

DISTILL = """meatbag distill: not built yet.

What it will do: read data/distill/{convictions,moves}.jsonl (from
`meatbag snapshot`) plus corpus/gremlin_hunt.jsonl, and write first drafts
into the "## Distilled from the corpus" sections of persona/*.md, each
entry marked "first draft" and each quote checked by `meatbag quotecheck`.

What to do today: it's manual. Hand the snapshot files to a strong model
(in a session that can't see data/ beyond data/distill/, and never eval/),
ask for persona entries in your own words with exact quotes, paste them
under the marker, run `meatbag quotecheck persona/<FILE>.md --mark`, then
edit them yourself. Your edits are what make them yours.
"""

SELECT = """meatbag select-cases: not built yet.

What it will do: read data/eval_candidates.jsonl (from `meatbag holdout`),
let you choose the eval cases, write their text to the eval store
(gremlin.toml [paths] eval, outside the home), write only ids and hashes
to eval/cases_index.json, then delete the candidates file.

What to do today: choose cases by hand, outside any agent session; put
their text in the eval store, not in the home; and write the frozen
persona_prompt.md, situation.md and prompts.md under eval/ledger/ before
any run (format in docs/eval.md).
"""


def distill(argv=None):
    print(DISTILL, file=sys.stderr)
    return 3


def select_cases(argv=None):
    print(SELECT, file=sys.stderr)
    return 3
