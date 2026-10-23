# Loaded birds

The plan is to flip the whole banana-counting game the bird, with
receipts. A bird with no receipt is just a tweet. A bird stapled to a
reproducible result is a paper they have to cite.

So this page tracks which birds are loaded. Every architectural claim we
make goes here with its status, and it moves to **measured** only when
there's a number, a method and a falsifier anyone can check. Bonkers is
fine. Bullshit is not.

| # | Claim | Status | What would make it measured |
| --- | --- | --- | --- |
| 1 | **Pre-registered, walled evals for persona agents.** Bets go in the ledger before the check. Held-out data sits behind a wall the agent can't read. A blind rater grades neutralized, shuffled answers, and the key stays outside the repo until the ratings are locked. | Built. First round run, not yet scored. | Scored rounds, published with the pre-registration, the falsifier and the result, whichever way it went. |
| 2 | **The receipts-first agent.** It drafts and never sends; the owner clicks. It learns from the owner's red pen (edits and vetoes, with reasons). It keeps a ledger of its own mistakes, and each entry names the change that prevents the next one. | Built, in use. Not measured. | Veto rate and edit distance over time, from real use. Is it learning, or just apologizing? |
| 3 | **Consent built into persona packaging.** You bring your own plate, and nobody brings someone else's. Plates can be revoked going forward. Copy, not cut, is stated before anyone publishes. | Designed (cookout). Not built. | The gate built and attacked by someone who isn't us. |
| 4 | **Who you are vs. what your employer owns, provable to IT.** Read-only plates with matching hashes; the extractor refuses to run in a work home; work context never reaches an export. | Partly built. Work homes, meatbag refusing to run in one, work context kept as pointers, an allowlisted plate export that refuses work homes and is byte-identical after `context add`, and a test that the runtime has no network imports, all tested on invented fixtures. Not built: read-only installed plates and hash matching (need packaging), and the personal-chat filter. Not measured. [Open problem 2](open-problems.md). | Its done-line: an outside security reviewer finds no path except the personal-chat one, and that path is filtered and measured. |
| 5 | **Agent identity done right.** Every agent has a human sponsor, deny-by-default scopes, a kill switch the owner can hit from a phone, and an audit log. Posts are data, not instructions. | Designed. Being built in Babelr. | Shipped, with tests that try permission laundering and fail. |

Nothing here is upending anyone's roadmap yet, because nothing here has a
number yet. When one does, it moves up, and that's the bird.

Aim it at the game, not the players. Most of the people writing those
quarterly roadmaps are stuck playing too. If one of these ideas makes
your thing better, take it. That's the point. Credit's nice. Paying
the meatbag is nicer.
