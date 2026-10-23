"""gremlin: the runtime.

  gremlin init DIR --owner NAME --pronouns P --agent NAME [--symbol S]
  gremlin queue|ledger|wf|lessons|wake|tui ...
  gremlin talk [claude args]   start a Claude Code session as the agent, from its home
"""
import os
import shutil
import sys

from . import home

COMMANDS = ("init", "queue", "ledger", "wf", "lessons", "wake", "tui", "talk")


def talk(argv):
    """Run Claude Code from the home. ANTHROPIC_API_KEY is unset so the
    session uses your Claude login, not an API key that bills per token
    (and isn't scoped to this agent). Same as bin/gremlin."""
    claude = shutil.which("claude")
    if not claude:
        raise SystemExit("`claude` (Claude Code) isn't on PATH. Today the agent runs on Claude Code; see README.")
    os.chdir(home.root())
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    os.execve(claude, [claude, *argv], env)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help") or argv[0] not in COMMANDS:
        print(__doc__)
        return 0 if argv and argv[0] in ("-h", "--help") else 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "talk":
        return talk(rest)
    if cmd == "init":
        from .init import main as m
        return m(rest)
    if cmd == "tui":
        from .tui import main as m
        return m()
    if cmd == "lessons":
        from .lessons import main as m
        return m()
    if cmd == "wake":
        from .wake import main as m
        return m()
    mod = __import__(f"gremlincore.{cmd}", fromlist=["main"])
    return mod.main(rest)


if __name__ == "__main__":
    sys.exit(main())
