"""Where the pipeline reads and writes, relative to the agent's home.

  data/     the full pipeline output (walled from the agent)
  corpus/   what the agent may read: held-out conversations removed
  eval/     held-out conversation ids only (walled)
"""
from gremlincore.home import root


def data(*parts):
    return root().joinpath("data", *parts)


def corpus(*parts):
    return root().joinpath("corpus", *parts)


def evaldir(*parts):
    return root().joinpath("eval", *parts)


def full(name):
    """A full pipeline file: data/<name>, or the pipeline store once
    `meatbag open-corpus` has moved it out of the home."""
    from gremlincore.home import pipeline_dir
    p = data(name)
    return p if p.exists() else pipeline_dir() / name
