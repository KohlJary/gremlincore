"""Where your agent lives, what it's called, and the small frontmatter
format its files use.

The home is a directory with a `gremlin.toml` in it. It's found from
GREMLIN_HOME, else by walking up from the current directory to the first
`gremlin.toml`, else the current directory.
"""
import copy
import os
import re
import subprocess
import tomllib
from datetime import date
from pathlib import Path

CONFIG_NAME = "gremlin.toml"


def root():
    env = os.environ.get("GREMLIN_HOME")
    if env:
        return Path(env).expanduser()
    here = Path.cwd()
    for d in (here, *here.parents):
        if (d / CONFIG_NAME).exists():
            return d
    return here


def today():
    return os.environ.get("GREMLIN_TODAY") or date.today().isoformat()


# Everything a stranger's agent needs to not be somebody else's.
DEFAULTS = {
    # A work home (`gremlin init --work`) runs at work: nothing in it becomes
    # a plate. meatbag refuses to run in one and `gremlin plate export`
    # refuses to export from one.
    "work": False,
    "owner": {"name": "you", "pronouns": "they/them"},
    "agent": {"name": "gremlin", "symbol": "⊖"},
    "paths": {
        # Outside the home on purpose: the agent works in the home, and the
        # full pipeline and the eval answers must not be in reach.
        "pipeline": "",   # default ~/.local/share/gremlincore/<agent>/pipeline
        "eval": "",       # default ~/.local/share/gremlincore/<agent>/eval
    },
    "corpus": {
        "domains": ["strategy", "outreach", "ops", "research", "writing", "creative",
                    "engineering", "personal", "other"],
        # Read first by `meatbag mine moves`; engineering last, since frontier
        # models already write code and that's not where the scarcity is.
        "domain_order": ["strategy", "outreach", "ops", "research", "writing",
                         "personal", "creative", "other", "engineering"],
        "skip_in_distill": ["engineering"],
        "eval_domains": ["strategy", "outreach", "ops"],
        # Eras: [{name = "early", before = "2025-06"}, ...], oldest first.
        # Anything after the last cutoff gets `last_era`. Default: one era.
        "eras": [],
        "last_era": "all",
    },
    "filters": {
        # Topics where your pushback makes sense for you, in your life, and
        # is not a strategy move anyone should generalize. Example: if you
        # spent years arguing with doctors, your agent shouldn't learn
        # "always reject the expert" from it. Rows that match stay as
        # context and never become MOVES. Regex fragments, case-insensitive.
        "do_not_generalize": [],
    },
    "voice": {
        # Every source defaults to empty: read nothing until you say so.
        "github_login": "",
        "github_repos": [],
        "rss_feeds": [],
        # Claude Code project dirs (substring match) whose sessions count
        # as your voice. Leave your day job's projects OUT: work sessions
        # must never land in a persona corpus.
        "session_projects": [],
    },
    "models": {"local": "qwen3:8b", "eval": "claude-opus-5-5"},
    "gremlin": {
        # Your own confirmed examples for the gremlin passes. Empty means
        # the invented defaults in meatbag/sort_gremlin.py are used.
        "examples": [],
        "near_misses": [],
    },
    "wake": {"closing": "Okay, I'm in. What's stuck, and what can I move?"},
    "eval": {
        # STATUS.md sections to strip from the agent arm (arms.py), e.g. a
        # list of jobs the agent wrote for itself that would leak the answer.
        "strip_status_sections": [],
    },
}


def _merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def config(home=None):
    """gremlin.toml merged over DEFAULTS. A missing file means defaults."""
    p = Path(home or root()) / CONFIG_NAME
    data = tomllib.loads(p.read_text()) if p.exists() else {}
    cfg = _merge(DEFAULTS, data)
    slug_ = slug(cfg["agent"]["name"])
    base = Path.home() / ".local/share/gremlincore" / slug_
    cfg["paths"]["pipeline"] = str(Path(cfg["paths"]["pipeline"] or base / "pipeline").expanduser())
    cfg["paths"]["eval"] = str(Path(cfg["paths"]["eval"] or base / "eval").expanduser())
    return cfg


CLEARLY_FALSE = ("false", "no", "0", "off")


def is_work(cfg=None, home=None):
    """True unless the home clearly says it isn't a work home. Fails closed:
    a key spelled `Work` or `WORK`, a value like "maybe", a number other than
    0, a table, or a gremlin.toml that won't parse all count as work. A guard
    that a typo can switch off isn't one. No `work` key at all means a
    personal home (every home from before work homes existed)."""
    if cfg is None:
        p = Path(home or root()) / CONFIG_NAME
        try:
            cfg = tomllib.loads(p.read_text()) if p.exists() else {}
        except (tomllib.TOMLDecodeError, UnicodeDecodeError, OSError):
            return True
    vals = [v for k, v in cfg.items() if isinstance(k, str) and k.strip().lower() == "work"]
    return any(not _clearly_false(v) for v in vals)


def _clearly_false(v):
    if v is False or (type(v) is int and v == 0):
        return True
    return isinstance(v, str) and v.strip().lower() in CLEARLY_FALSE


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "gremlin"


def owner(cfg=None):
    return (cfg or config())["owner"]["name"]


def owner_id(cfg=None):
    """The owner as it's stamped in queue headers (edited_by, approved_by)."""
    return slug(owner(cfg))


def agent(cfg=None):
    return (cfg or config())["agent"]["name"]


def pipeline_dir():
    return Path(config()["paths"]["pipeline"])


def eval_dir():
    return Path(config()["paths"]["eval"])


_FM = re.compile(r"\A---\n(.*?)\n---\n?", re.S)


def split(text):
    """(meta dict, header text, body). Values lose trailing '# comments'."""
    m = _FM.match(text)
    if not m:
        return {}, "", text
    meta = {}
    for line in m.group(1).splitlines():
        k, sep, v = line.partition(":")
        if sep and re.fullmatch(r"[A-Za-z_][\w-]*", k.strip()):
            meta[k.strip()] = re.sub(r"\s+#.*$", "", v).strip()
    return meta, m.group(1), text[m.end():]


def set_field(text, key, value):
    """Set one header line, keeping every other line (and comments) as is."""
    m = _FM.match(text)
    head = m.group(1) if m else ""
    body = text[m.end():] if m else text
    lines = head.splitlines()
    pat = re.compile(rf"^{re.escape(key)}:")
    for i, line in enumerate(lines):
        if pat.match(line):
            comment = re.search(r"\s+#.*$", line)
            lines[i] = f"{key}: {value}" + (comment.group(0) if comment else "")
            break
    else:
        lines.append(f"{key}: {value}")
    rest = "\n" + body.lstrip("\n") if body.strip() else ""
    return "---\n" + "\n".join(lines) + "\n---\n" + rest


def git_date(path, first=False):
    """Date a file was first added (first=True) or last changed, by git."""
    try:
        args = ["git", "log", "--format=%cs", "--", str(path)]
        if first:
            args[2:2] = ["--diff-filter=A"]
        out = subprocess.run(args, cwd=root(), capture_output=True, text=True).stdout.split()
        return (out[-1] if first else out[0]) if out else None
    except (OSError, IndexError):
        return None
