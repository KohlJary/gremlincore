"""What the distillation keeps, drops, and refuses to generalize.

Pastes: some of your turns are other people's words in your clipboard
(prompts, lyrics, docs, another model's output, game terminals). Long
pastes can hold a big share of a corpus's characters while being none of
your words. They're kept in the corpus and flagged, never distilled as
your convictions, moves or voice.

Do-not-generalize topics: some pushback makes sense for you, in your
life, and is not a strategy move to generalize to anyone else. Those
topics are yours to list in gremlin.toml ([filters] do_not_generalize).
Rows that match stay as context and never enter MOVES.md.
"""
import functools
import re

from gremlincore.home import config

_MD_HEAD = re.compile(r"(^|\n)#{1,3} ")
_FENCE = re.compile(r"^\s*```")
_VERBS = r"(is|was|calls|said|has|wants|believes|thinks)"


def third_person(owner=None):
    """'<owner> said...' inside the owner's own turn means it's a paste."""
    return _third_person(owner or config()["owner"]["name"])


@functools.lru_cache(maxsize=8)
def _third_person(owner):
    return re.compile(rf"\b{re.escape(owner)}('s)? {_VERBS}\b")


def do_not_generalize(topics=None):
    """The configured topics as one regex, or None if there are none."""
    topics = config()["filters"]["do_not_generalize"] if topics is None else topics
    topics = [t for t in topics if t.strip()]
    return re.compile("|".join(f"(?:{t})" for t in topics), re.I) if topics else None


def is_paste(text, owner=None):
    if len(text) > 3000:
        return True
    if len(text) > 800 and _MD_HEAD.search(text):
        return True
    if third_person(owner).search(text) or _FENCE.match(text):
        return True
    lines = [l for l in text.splitlines() if l.strip()]
    # lyrics, poems, terminals: many short lines
    if len(lines) >= 12 and sum(len(l) < 60 for l in lines) / len(lines) > 0.8:
        return True
    return False


def generalizable_move(row, topics=None):
    """A flagged override that may become a MOVES.md entry."""
    blob = " ".join(str(row.get(k) or "") for k in ("default_rejected", "move", "quote"))
    pat = do_not_generalize(topics)
    return bool(row.get("override")) and not (pat and pat.search(blob))
