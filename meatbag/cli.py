"""meatbag: your AI-chat exports in, a persona corpus out.

Run from the agent's home (or set GREMLIN_HOME). In pipeline order:

  meatbag normalize EXPORT.zip ...   Claude / ChatGPT exports -> data/turns.jsonl
  meatbag mine tag                    one domain label per conversation (local model)
  meatbag mine moves                  overrides, convictions, gremlin flags (local model)
  meatbag sort                        sort gremlin flags: gremlin / out_there / funny / hurt
  meatbag holdout                     hold out whole conversations for the eval
  meatbag open-corpus                 corpus/ without them; full files leave the home
  meatbag hunt                        high-recall gremlin pass over corpus/ (coarse)
  meatbag snapshot                    data/distill/: what the distiller may read
  meatbag distill                     NOT BUILT: prints the manual steps, exits 3
  meatbag select-cases                NOT BUILT: prints the manual steps, exits 3
  meatbag quotecheck FILE [--mark]    are the persona's quotes really yours?
  meatbag voice [--days N]            your other writing (default: reads nothing)
  meatbag arms [--renormalize]        run the pre-registered eval arms (claude -p)
  meatbag report                      data/morning-report.md
"""
import importlib
import sys

COMMANDS = {
    "normalize": "normalize", "mine": "mine", "sort": "sort_gremlin", "hunt": "gremlin_hunt",
    "holdout": "holdout", "open-corpus": "open_corpus", "snapshot": "distill_snapshot",
    "quotecheck": "quotecheck", "voice": "voice", "arms": "arms", "report": "morning_report",
}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]
    from . import stubs
    if cmd == "distill":
        return stubs.distill(rest)
    if cmd == "select-cases":
        return stubs.select_cases(rest)
    if cmd not in COMMANDS:
        print(f"unknown command {cmd!r}\n" + __doc__, file=sys.stderr)
        return 2
    mod = importlib.import_module(f"meatbag.{COMMANDS[cmd]}")
    return mod.main(rest) or 0


if __name__ == "__main__":
    sys.exit(main())
