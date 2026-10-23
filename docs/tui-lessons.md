# TUI lessons

What the TUI is built on, and what to keep if you build another one.
Lessons from earlier Textual apps, kept because each one cost an evening.

## Draw it first

Sketch the layout as a box diagram before writing widgets: proportions
from character widths, one sub-diagram per component. It's not faster,
but it's right the first time, and a drawn component that never got wired
in is easy to spot.

## Ten Textual lessons

1. App-level vim keys (j/k/g/G/H/L) with `priority=True`, so they work in
   modals too.
2. Focus the main table in `on_mount`, or buttons eat j/k.
3. `q` asks first (a confirm modal), guarded against stacking.
4. `rich.markup.escape` every user or model string before a `Static`.
   `[/b]` in a body blanks the pane.
5. Long text edits in a modal `TextArea`: ctrl+s submits, Esc cancels;
   Tab leaves a TextArea.
6. Typed `ModalScreen[T]` + `dismiss(value)` + `push_screen(modal, cb)`.
7. Re-mounting races (`DuplicateIds`): use an exclusive `@work` that awaits
   removal, and skip re-rendering what's already shown.
8. Workers for I/O; `set_interval` refreshes at staggered rates; long-lived
   state on the App, not the screen.
9. Design tokens only (`$primary`, `$surface`, `$panel`); `1fr` layouts;
   compose everything, hide with `display: none`; `TabbedContent` for
   dense dashboards.
10. Tests: `async with app.run_test() as pilot`, `pilot.press`,
    `query_one` asserts, `asyncio_mode = "auto"`; a constructor flag to
    skip startup modals; build against fake data first, then flip a flag
    to live data.

Markdown widget only where needed; otherwise escaped text in a
`VerticalScroll`, capped with a truncation note.

## Stack

`textual>=8.0`, `rich`, `pytest>=8`, `pytest-asyncio>=0.24`, Python
>=3.11. Inline `DEFAULT_CSS` first; a `.tcss` file once two screens share
styles; `Footer` before a help screen.

## Avoid

- `Select.value` type drift (accept only `str`).
- `query_one` before mount.
- Mega-screens: split early.
- Unbounded sync file reads on refresh ticks.
- Asserting on `str(label.renderable)` across Textual versions.

## The layout (`gremlin tui`)

```
┌──────────────────────────────────────────────────────────┐
│ StatusBar  (agent · WF count · bets open · STATUS date)  │
├──────────────────┬───────────────────────────────────────┤
│ QueueList        │ DraftDetail                           │
│                  │   to · room · why · prediction        │
│                  │   ─────────────────────────────────   │
│                  │   body (VerticalScroll, escaped)      │
├──────────────────┴───────────────────────────────────────┤
│ Footer  a approve · e edit · v veto · S I sent it ·      │
│         l ledger · w wake · t talk · q quit              │
└──────────────────────────────────────────────────────────┘
```

![The TUI on the Gregiverse fixture home](tui-screenshot.svg)
