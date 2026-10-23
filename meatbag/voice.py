"""Collect the owner's own writing for voice and humor, from sources listed
in gremlin.toml [voice]: GitHub issues and comments on chosen repos, RSS
feeds, and recent Claude Code sessions from chosen projects.

Every source defaults to empty, so by default this reads nothing.

  meatbag voice [--days 4]   -> data/voice/{github,sessions,rss}.jsonl

Only the owner's words are kept: issue bodies and comments authored by
the configured GitHub login, the owner's own prompts in sessions, and
posts from the listed feeds (list only feeds you wrote).
"""
import argparse
import html
import json
import re
import subprocess
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from gremlincore.home import config

from . import paths


def _gh(*args):
    return json.loads(subprocess.run(["gh", *args], check=True,
                                     capture_output=True, text=True).stdout)


def github(login, repos):
    rows = []
    if not login:
        return rows
    for repo in repos:
        issues = _gh("issue", "list", "-R", repo, "--state", "all", "--limit", "500",
                     "--json", "number,title,body,author,createdAt,comments")
        for i in issues:
            if i["author"]["login"] == login:
                rows.append({"source": "github", "ref": f"{repo}#{i['number']}",
                             "title": i["title"], "ts": i["createdAt"], "text": i["body"]})
            for c in i.get("comments") or []:
                if c["author"]["login"] == login:
                    rows.append({"source": "github", "ref": f"{repo}#{i['number']} comment",
                                 "title": i["title"], "ts": c["createdAt"], "text": c["body"]})
    return rows


_NOISE = re.compile(r"<(system-reminder|command-|local-command|task-notification|"
                    r"bash-|user-prompt-submit)", re.I)


def sessions(days, projects=None, base=None):
    """The owner's prompts from Claude Code sessions in the allowlisted
    project dirs. An empty allowlist (the default) reads nothing.

    Never list your day job's projects: work sessions must not land in a
    persona corpus, and the allowlist is the only thing that keeps them out."""
    projects = config()["voice"]["session_projects"] if projects is None else projects
    projects = [p.lower() for p in projects if p.strip()]
    if not projects:
        return []
    base = Path(base) if base else Path.home() / ".claude/projects"
    rows, cutoff = [], time.time() - days * 86400
    for f in base.glob("*/*.jsonl"):
        if f.stat().st_mtime < cutoff:
            continue
        if not any(k in f.parent.name.lower() for k in projects):
            continue
        for line in f.open():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") != "user" or e.get("isMeta") or e.get("isSidechain"):
                continue
            c = (e.get("message") or {}).get("content")
            if isinstance(c, list):
                c = "\n".join(b.get("text", "") for b in c
                              if isinstance(b, dict) and b.get("type") == "text")
            if not isinstance(c, str) or not c.strip() or _NOISE.search(c[:200]):
                continue
            if "This session is being continued from a previous conversation" in c:
                continue
            rows.append({"source": "session", "ref": f"{f.parent.name}/{f.stem}",
                         "ts": e.get("timestamp"), "text": c.strip()})
    return rows


def _strip_html(s):
    s = re.sub(r"<(br|/p|/h\d|/li)[^>]*>", "\n", s)
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def rss(feeds):
    rows = []
    ns = {"content": "http://purl.org/rss/1.0/modules/content/"}
    for url in feeds:
        req = urllib.request.Request(url, headers={"User-Agent": "gremlincore-meatbag/0.0"})
        root = ET.fromstring(urllib.request.urlopen(req, timeout=60).read())
        for it in root.iter("item"):
            body = it.findtext("content:encoded", default="", namespaces=ns) or it.findtext("description", default="")
            rows.append({"source": "rss", "ref": it.findtext("link"),
                         "title": it.findtext("title"), "ts": it.findtext("pubDate"),
                         "text": _strip_html(body)})
    return rows


def sources(days, cfg=None):
    v = (cfg or config())["voice"]
    return [("github", lambda: github(v["github_login"], v["github_repos"])),
            ("sessions", lambda: sessions(days, v["session_projects"])),
            ("rss", lambda: rss(v["rss_feeds"]))]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="meatbag voice")
    ap.add_argument("--days", type=float, default=4)
    a = ap.parse_args(argv)
    cfg = config()
    v = cfg["voice"]
    if not (v["github_login"] and v["github_repos"]) and not v["rss_feeds"] and not v["session_projects"]:
        print("No voice sources configured in gremlin.toml [voice]: reading nothing. That's the default.")
        return 0
    out = paths.data("voice")
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in sources(a.days, cfg):
        try:
            rows = fn()
        except Exception as e:
            print(f"{name}: failed: {e}")
            continue
        if not rows:
            continue
        with (out / f"{name}.jsonl").open("w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        words = sum(len(r["text"].split()) for r in rows)
        print(f"{name}: {len(rows)} pieces, {words} words")
    return 0


if __name__ == "__main__":
    from meatbag import refuse_work_home
    refuse_work_home()
    main()
