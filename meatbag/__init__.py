"""meatbag: your AI-chat exports in, a persona corpus out. Local passes on Ollama."""
import sys

WORK_EXIT = 4


def work_home():
    """The work home meatbag would be running in, or None. Checks the resolved
    home (GREMLIN_HOME, else the nearest gremlin.toml up from here), and the
    nearest one up from the current directory too, in case GREMLIN_HOME
    points somewhere else."""
    from pathlib import Path

    from gremlincore import home
    candidates = [home.root()]
    for d in (Path.cwd(), *Path.cwd().parents):
        if (d / home.CONFIG_NAME).exists():
            candidates.append(d)
            break
    for h in candidates:
        if (Path(h) / home.CONFIG_NAME).exists() and home.is_work(home=h):
            return Path(h)
    return None


def refuse_work_home():
    """Exit non-zero, before reading anything, when run in a work home."""
    h = work_home()
    if h is not None:
        print(f"meatbag refuses to run in a work home: {h} has work = true.\n"
              "meatbag is the part that reads, and nothing in a work home becomes a plate.\n"
              "Run it at home, on your own exports.", file=sys.stderr)
        raise SystemExit(WORK_EXIT)
