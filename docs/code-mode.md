# Code mode: the gremlin goes to work

**Status: idea, with a design. There is no code.** Everything below is
what it would be, not what it is.

## The pitch

Senior engineers who actually loved the puzzle get to do the puzzle,
with a little guy in the computer.

Every AI coding tool on the market is pitched at velocity, and velocity
is a manager's number. The tools work. That's the problem: they took the
part of the job people chose the job for, and handed back a review queue.
A lot of senior devs now spend their day code-reviewing a robot and
missing the 2 AM bug they used to find themselves.

Code mode is the same gremlin, pointed at the day job, with one rule it
doesn't break: **it eats the bullshit and saves the puzzles for you.**

## Not for everyone

Plenty of seniors love vibe coding, and they should keep doing it. This
is for the ones who'd rather solve the thing than watch it get solved.
If that's not you, Daedalus-style full generation is right there and
nobody's judging.

## The rule

Every ticket gets a read before you open a file:

- **Plumbing.** Add a field to the DTO, bump a config, rename across 40
  files, wire up DI for the fourteenth time. The gremlin offers to take
  it. "This one's beneath you. Want me?" You say yes, it drafts the diff,
  the diff goes in the queue, you click.
- **Mixed.** It preps the plumbing around the edges and leaves a marked
  hole where the interesting part lives. Sous-chef rules: everything's
  chopped, you make the one cut that matters.
- **Puzzle.** It goes quiet and gets sharper. Context on demand, questions
  when you're stuck, a hint ladder you climb yourself (nudge, direction,
  sketch, answer). It never volunteers code on a puzzle ticket. You have
  to ask, one rung at a time.

It says its read out loud and you overrule it in one word. "Reads like
plumbing." "Nah, mine." Your taste wins, every time, and it learns from
losing.

**Rescaling mid-ticket.** A puzzle that turns into a swamp of boilerplate
halfway through: it offers to take just the swamp. A plumbing ticket
that turns out to hide a race condition: it hands the wheel back. "Hey.
This one got interesting. You want it?" That second move is the whole
product. Clippy interrupted to help. This one interrupts to give you
something.

## How it uses what's already here

Code mode adds almost no new machinery. It's the runtime, aimed at code.

- **Work homes.** Code mode only runs in a home made with
  `gremlin init --work`. meatbag already refuses to run there, and
  nothing exports from one. The persona is built at home and arrives as
  a plate. **meatbag lives at home. The gremlin goes to work.**
- **Context.** `gremlin context add <repo>` already keeps the work repo
  as pointers, outside `persona/`. Code mode reads through those
  pointers and writes nothing back into the plate.
- **The queue.** A new `kind: diff`. Drafted patches wait for your click
  like every other draft. The gremlin never applies a change you didn't
  approve, on any ticket, ever. On a puzzle ticket the queue stays empty
  unless you climb to the last rung.
- **The ledger.** Every ticket read is a bet, made before you start:

  ```json
  {"id": 41, "date": "2026-11-03", "by": "gremlin",
   "prediction": "PROJ-1182 is plumbing",
   "why": "three-file DTO change, prior art in OrderService",
   "falsifier": "owner says 'mine', or hand-writes the core change",
   "check_when": "ticket closed", "outcome": null, "hit": null}
  ```

  Your veto settles it. Over a few months that's a scored record of how
  well it knows what you find fun, which is the only metric this mode
  cares about.
- **The WF ledger.** Taking a puzzle from you is a fuckup, and it gets an
  entry with a change attached, same as a bad email. So is sandbagging:
  making you hand-write plumbing it should have taken.

  ```json
  {"id": 12, "date": "2026-11-05",
   "what": "Drafted the retry logic on PROJ-1190 unasked; that was the fun part",
   "who": "owner (lost the puzzle)", "wf": 1,
   "root_cause": "Read 'touches the HTTP client' as plumbing",
   "change": "persona/MOVES.md: error-handling design is a puzzle unless the owner says otherwise",
   "found_by": "owner"}
  ```
- **The wake brief.** Morning triage. "Three tickets. Two are bullshit
  and I've prepped them in the queue. One's a real one. I saved it for
  you."
- **The TUI.** Where he lives. Editors are cramped and hostile to
  personality, so the companion window is his body: his read on the
  current ticket, the hint ladder, the veto button, the sprint ratio.

## The sprint ratio

The ledger can say what share of a sprint was plumbing and what share
was puzzle. That's the first number a senior dev can take to a manager
that isn't about speed: "40% of my sprint was work a robot should do,
and the robot did it. Here's what I did with the rest." It's also the
number that says whether the job is still worth having.

## Structure

- **The editor talks to the home through files.** The runtime has no
  network code, and a test fails the build if any appears. Code mode
  keeps that. An editor client writes what it sees (cursor, open buffer,
  diagnostics, the current diff) to `<home>/code/now.json`, and reads the
  gremlin's notes back from `<home>/code/notes/`. Margin comments, ghost
  text for approved plumbing, a "he wants a word" marker. No sockets, no
  daemon port. The pieces are files and JSON on purpose, and this keeps
  them that way.
- **Clients, in order:** Neovim first (dogfood), then VS Code (reach),
  then Visual Studio and Rider (the C# day-job crowd). Emacs when someone
  wants it badly enough to write it, which someone will.
- **Model calls and tickets go through `gremlin talk`.** That's Claude
  Code under the employer's own policy. Ticket systems (Jira, Azure
  DevOps, GitHub Issues) come in as MCP servers there, not as network
  code in the runtime. The only egress stays the model and what the
  owner plugs in.
- **Code lives in `gremlincore/code/`, and it never imports meatbag.**
  A test enforces it, the same way the no-network test does. If the
  day-job audience ever needs its own install, the folder lifts out
  and already stands alone.

## What it reads to decide

The read on a ticket comes from: the ticket text; how many files it
touches; whether the repo has prior art for it; whether it's new logic or
pattern repetition; and the owner's past vetoes on tickets like it. The
persona supplies the taste ("I like writing parsers," "error handling is
mine"). The ledger supplies the correction. A global model of what's
"interesting" is exactly what this mode is against. Fun is per-person.

## What it won't do

- Apply a change you didn't click.
- Volunteer code on a puzzle ticket.
- Teach you what a dictionary is. You're senior. It spars, it doesn't
  tutor.
- Put anything from work into the plate.
- Optimize for accepted suggestions. Most tools are scored on how often
  you take their code. This one is partly scored on the code it *didn't*
  write.

## Open questions

- **The classifier is the product.** If it misreads puzzle vs. plumbing,
  it's either Copilot or useless. How many vetoes until it's good enough
  to trust? Unknown.
- **The hint ladder could be condescending.** Rungs have to be earned
  by being right, not by being cute. Needs real use to tune.
- **Does saving the puzzle actually make the job better,** or does it
  just make a bad job slower? That's measurable: self-reported
  satisfaction and veto rate, before and after, on the owner's own
  sprints. Until it's measured it's a bet, and it goes in the ledger.

## Done when

On a work home with an invented fixture repo and five invented tickets:
the gremlin records a bet on each ticket before anything opens; drafts a
diff into the queue for the plumbing ones and nothing for the puzzle
one; climbs the hint ladder only on request; settles its bets from the
owner's vetoes; files a WF entry with a change when it takes a puzzle;
and the no-network and no-meatbag-import tests still pass. All in
`python -m pytest -q`.
