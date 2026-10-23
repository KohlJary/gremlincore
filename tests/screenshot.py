"""Regenerate docs/tui-screenshot.svg from an invented fixture home.

  python tests/screenshot.py

Never point this at a real home: the screenshot shows the queue.
"""
import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.conftest import DRAFT, TOML  # noqa: E402

SECOND = """---
status: edited
kind: post
to: the HOA newsletter
room: public
why: the bounce castle, framed as civic infrastructure
prediction: 2
created: 2026-10-07
edited_by: pat
---

Saturday the HOA gets a bounce castle. Waivers are how they win. We bounce
first and apologize in the minutes. Schlitz for adults; juice boxes for
Chad.

<!-- original -->

The HOA is invited to consider a bounce castle.
"""


async def main():
    with tempfile.TemporaryDirectory() as d:
        h = Path(d)
        for sub in ("queue", "ledger", "persona"):
            (h / sub).mkdir()
        (h / "gremlin.toml").write_text(TOML)
        (h / "queue/0001-bbq.md").write_text(DRAFT)
        (h / "queue/0002-castle.md").write_text(SECOND)
        (h / "ledger/predictions.jsonl").write_text(
            json.dumps({"id": 1, "date": "2026-10-01", "by": "RoboPat", "prediction": "Ray RSVPs",
                        "falsifier": "no RSVP", "check_after_days": 7, "check_by": None,
                        "outcome": None, "hit": None}) + "\n")
        (h / "ledger/wf.jsonl").write_text(json.dumps(
            {"id": 1, "date": "2026-10-05", "what": "Sanded the castle post down for the HOA",
             "who": "Pat", "wf": 1, "root_cause": "wrote for the room's comfort",
             "change": "persona/MOVES.md: the point survives the edit", "found_by": "pat"}) + "\n")
        (h / "STATUS.md").write_text("_Last updated: 2026-10-09_\n")
        subprocess.run(["git", "init", "-q"], cwd=h)
        os.environ["GREMLIN_HOME"] = str(h)
        os.environ["GREMLIN_TODAY"] = "2026-10-09"
        from gremlincore.tui import GremlinApp
        app = GremlinApp()
        async with app.run_test(size=(110, 30)) as pilot:
            await pilot.pause()
            app.save_screenshot(filename="tui-screenshot.svg", path=str(ROOT / "docs"))
    print("wrote docs/tui-screenshot.svg")


if __name__ == "__main__":
    asyncio.run(main())
