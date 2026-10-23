# Ledger spec

Two append-mostly JSONL files in `<home>/ledger/`.

## `predictions.jsonl`: bets, before they're checked

One line per bet:

```json
{"id": 1, "date": "2026-10-01", "by": "RoboPat", "prediction": "Uncle Ray RSVPs within a week",
 "why": "he never misses a grill", "falsifier": "no RSVP by the 8th",
 "check_when": "a week after the invite goes out", "check_by": null,
 "check_after_days": 7, "outcome": null, "hit": null}
```

- `falsifier` is required. No falsifier, no bet: that's a vibe with a timestamp.
- `check_by`: the ISO date to check by (null until known).
- `check_after_days`: days after a linked queue item is sent. When the
  owner marks the item sent, `check_by` is dated from the send. A list
  means several checkpoints.
- `awaiting`: who the bet is waiting on, if not a date (e.g. `owner-rating`).
- `outcome` and `hit` stay null until it's checked, then get filled in
  place (`gremlin ledger settle`). Never delete a row that turned out wrong.
- `gremlin ledger score` keeps the owner's bets and the agent's apart.

## `wf.jsonl`: the agent's mistake ledger

WF stands for "wives fucked," from WF/LOC: every decision either takes
something from the people it touches or doesn't. This is where the agent
counts the times it did, so it learns from them.

**What gets an entry:** any mistake the agent makes that cost someone
something. The owner rejected a draft because it missed the point. A draft
softened the point for the people it was aimed at. A stunt with no
payload. An overclaim. A prediction that was wrong *because the agent
reasoned badly* (bad luck goes in the prediction's outcome, not here). The
owner calling it out counts. The agent catching itself counts double, in
the good way: log it anyway.

**One line per incident:**

```json
{"id": 1, "date": "2026-10-23",
 "what": "Drafted the grant email for the reviewer's comfort, not the point",
 "who": "Pat (lost an evening to rewriting it)",
 "wf": 1,
 "root_cause": "Softened for the audience",
 "change": "persona/MOVES.md: added a check before any outbound draft",
 "commit": "abc1234",
 "found_by": "pat"}
```

- `wf` is the number of people who got fucked over: the owner counts as
  one. A bad email to 40 people is 40. An honest estimate beats a
  flattering one.
- `change` is required (`gremlin wf add` refuses without one). An entry
  with no change is a mistake the agent plans to make again. If nothing
  should change, say why in `change`.
- `found_by`: the owner, the agent, `eval`, or whoever filed the bug.

`gremlin wf` prints the running count and the recent incidents; the wake
brief shows it every time. The home's settings deny the Edit tool on
`ledger/wf.jsonl`, so entries go through `gremlin wf add`.

**Target: zero.**
