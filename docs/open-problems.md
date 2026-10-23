# Open problems we've committed to solving

Two problems are unsolved today. Each one has a done-line, and each stays
in the README until it's met. Bonkers is fine. Bullshit is not: this page
says what doesn't work yet.

---

## 1. Keeping plates current

A plate is a snapshot of how someone thinks, taken on the day it was
built. People keep changing, and a plate that never changes becomes a
museum piece wearing your name.

**What "current" has to mean:**

- **Versioned, owner-approved by default.** Every plate has a version.
  By default, meatbag proposes a new version from new exports and only the
  owner can bump it.
- **Automatic, if you opt in.** An owner can switch on automatic updates:
  meatbag folds new exports into the plate as they arrive, and a
  **periodic assessment** (monthly by default, owner's choice) puts every
  change since the last one in front of the owner to confirm or revise.
  Automatic changes are marked provisional until an assessment confirms
  them. A skipped assessment pauses automatic updates; it doesn't wave
  them through. Off by default, one switch to turn it on or off.
- **Incremental.** Re-running meatbag on new exports proposes a *diff*
  to the persona (new convictions, retired ones, changed moves), each with
  its receipts, instead of rebuilding from scratch. An old belief the
  owner still holds stays; one they've dropped moves to history, the way
  eras work today.
- **A sync model the grabber can see.** Borrowed from Chapter House's
  lineage design:
  - *snapshot*: you grabbed v3, you keep v3;
  - *tethered*: new versions flow to you;
  - *pinned*: you choose when to update.

  A plate says which model it supports. Grabbers choose, and the default
  is pinned.
- **Revocable going forward.** `cookout pull` stops future versions. It
  can't unring copies already grabbed (copy, not cut), and the README says
  so before anyone runs `bring`.

**Done when:** an owner adds three months of new exports, meatbag proposes
a diff with receipts, the owner red-pens it into v2, and a tethered
grabber gets v2 while a pinned one stays on v1. And with automatic
updates on, the changes land provisionally, the assessment shows all of
them, and a revision there wins. All in tests on invented fixtures.

---

## 2. Who you are vs. very important super serious business stuff

The goal is a line between *the meatbag* and *the employer's property*
that you can hand to your IT security department, and that holds when
they check it. The design rule is that work data can't get into the
plate **by construction**. "The agent promised not to" is a policy, and
the security team is right not to trust it.

**The claims we owe them, each with the evidence that backs it.** The
status column says what's built today and which test backs it. Tests live
in `tests/test_work_homes.py` and `tests/test_no_network.py`; they run on
invented fixtures (`python -m pytest -q`).

| Claim | Evidence they can check themselves | Status |
| --- | --- | --- |
| The installed plate is exactly the published one | It's a read-only package. Its hash matches the public release, so a reproducible build gives the same bytes. | **Open.** Needs packaging. Today's piece: `gremlin plate export` writes the same bytes from the same home (no timestamps) plus a `MANIFEST.sha256`. Nothing publishes or installs a plate yet. |
| Nothing at work writes into the plate | The plate is installed read-only (root-owned, `0444`). Work state lives in a separate *work home*. A test proves a plate's hash is unchanged after a full work session. | **Partly built.** Work homes exist: `gremlin init --work` writes `work = true`, and `gremlin wake` opens with "WORK HOME: nothing here becomes a plate." (`test_init_work_writes_work_true_and_wake_says_so`). **Open:** the read-only install and the hash-after-a-work-session test, which need packaging. |
| The runtime doesn't phone home | gremlincore has no network code. A test fails the build if a network import ever appears. They can also watch it under a firewall. | **Built.** `test_runtime_has_no_network_imports` is a static (AST) scan of every module in `gremlincore/`. It flags imports of network libraries (asyncio included); `__import__` and `importlib.import_module` calls under any alias, whether the name is a network library or computed (only an f-string starting with `gremlincore.` is allowed); `exec`/`eval`/`compile`; and subprocess or `os.system`/`popen`/`exec*` calls whose string arguments name a network tool (curl, wget, nc, ssh, ...). `test_the_scanner_catches_a_planted_import` shows each of those can fail it. It doesn't catch `getattr` indirection, a tool name built at runtime, or code loaded from files, and it doesn't cover third-party dependencies (textual, rich) or `gremlin talk`, which execs Claude Code. The firewall check is theirs to run. |
| The only egress is the model | `gremlin talk` is Claude Code, under the employer's existing Claude Code policy (their account, their settings, their data terms). Nothing else leaves the machine. | **Stated, not tested.** The no-network test backs the runtime half. Nothing tests what Claude Code itself sends. |
| The extractor never runs at work | A work home sets `work = true`. meatbag refuses to run in one, and `bring` refuses to export from one. Tested. | **Built, for a home marked as work.** Every meatbag CLI command exits 4 in a work home before reading anything (`test_every_meatbag_command_refuses_in_a_work_home`). So does every module's entry point (each `main()`, plus the distill and select-cases stubs), whether it's reached through `python -m` (`test_meatbag_modules_refuse_when_run_directly`) or imported and called (`test_meatbag_entry_points_refuse_when_imported_and_called`), and a new `main()` without the guard fails `test_every_meatbag_main_is_guarded`. A cwd inside a work home is refused even when `GREMLIN_HOME` points elsewhere. The flag fails closed: a `Work` key, a value like `"maybe"`, or a gremlin.toml that won't parse all count as work (`test_work_flag_fails_closed`, `test_malformed_toml_fails_closed`). **Not guarded:** meatbag's library functions (say, `normalize.turns()`) called directly from Python. `bring` isn't built; `gremlin plate export`, which it will call, refuses a work home (`test_export_refuses_in_a_work_home`). The flag is the owner's to set: a home nobody marked is not protected, and nothing stops someone copying files by hand. |
| Work context stays at work | `gremlin context add <repo>` stores context in the work home, outside `persona/`, excluded from every export path. Tested: a plate exported after adding context is byte-identical to one exported before. | **Built, for the export path.** `gremlin context add/list/remove` keeps a list of paths plus metadata in `context/contexts.json` and copies nothing (`test_context_add_list_remove_keeps_pointers_only`). The export is an allowlist: persona/*.md, STATUS.md, plate.toml, the manifest. An export after `context add` is byte-identical to one before (`test_export_after_context_add_is_byte_identical`); it holds no file from context/, the queue, the ledgers or the lessons, and refuses symlinks and hardlinked files (`test_export_is_the_allowlist_and_nothing_else`, `test_export_refuses_a_symlink_on_the_allowlist`, `test_export_refuses_a_hardlink_on_the_allowlist`). **Still policy, not construction:** an agent that writes context into `persona/` or STATUS.md by hand would get it exported. The skill tells it not to; nothing enforces that yet. |
| It's all auditable | MIT license, open source, an SBOM, and an audit log of every agent action in the work home. | **Partly.** MIT and open source, yes. No SBOM and no audit log yet. |

**The leak path that isn't on the work box, and is the hard part:** your
*personal* AI chats about work. If you talked a work problem through with
a chatbot at home, that conversation is in your personal export, and
meatbag will read it. Nothing on the work box can stop that, so meatbag
needs:

- a **work-content filter** that flags, before distillation, any turns
  that look like an employer's code, internal names, or customer data,
  using names and patterns the owner configures;
- an **owner review** of what got flagged;
- a **default of exclude when unsure**.

This is the problem we can't fully solve with filesystem permissions,
and we won't claim we have. **Status: unsolved.** None of the three is
built.

**Done when:** a security reviewer who isn't us gets the claims table,
the tests, and a work home to poke at, and can't find a path for work
data into a plate other than the personal-chat path. That path has a
filter, an owner review step, and a stated false-negative rate measured
on invented fixtures.

---

*Both problems are tracked here until their done-lines pass. If you find a
hole, open an issue. The template's called "I was Greg" for a reason.*
