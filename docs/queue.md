# Queue spec

Drafts waiting for the owner, one file each: `<home>/queue/NNNN-slug.md`.
The agent drafts as the owner and never sends as the owner. Approved,
edited and vetoed items stay: the owner's edits and vetoes are the best
training data the agent will ever get.

```
---
status: pending        # pending | approved | edited | vetoed | sent
kind: email            # email | post | plan | dm | ask | other
to: Uncle Ray
room: families         # engineers | researchers | funders | families | press | public | ...
why: barbecue invite: the move, and what it buys
prediction: 1          # ledger id
created: 2026-10-01
edited_by: pat         # set by `gremlin queue edit`; only the owner's edits are lessons
---

Barbecue Saturday, 3pm, bring a chair.
```

- `gremlin queue list | show | approve | edit | veto | sent` (or `gremlin tui`).
- `approve` means the owner is willing. Nothing in gremlincore sends
  anything. `sent` records that the owner sent it, and dates the linked bet.
- `edit` keeps the first original below `<!-- original -->`, forever.
- `veto` needs a reason. A reason that says the draft missed, softened,
  overclaimed, or was "not <owner>" gets a proposed WF line from
  `gremlin lessons`.
- A pending item older than 5 days is marked stale: it should get smaller,
  not louder.
- Header comments survive every edit.
