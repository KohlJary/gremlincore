"""The TUI, driven by the pilot against a fixture home (never a real queue)."""
import pytest

pytest.importorskip("textual")

@pytest.mark.asyncio
async def test_tui_shows_queue_and_vetoes_with_a_reason(home):
    from gremlincore import queue
    from gremlincore.tui import GremlinApp
    app = GremlinApp()
    async with app.run_test() as pilot:
        t = app.query_one("#queue")
        assert t.row_count == 1
        await pilot.press("v")
        await pilot.press(*"too Greg")
        await pilot.press("enter")
        await pilot.pause()
    assert queue.get("1").meta["status"] == "vetoed"
    assert queue.get("1").meta["veto_reason"] == "too Greg"


@pytest.mark.asyncio
async def test_tui_approve_never_sends(home):
    from gremlincore import ledger, queue
    from gremlincore.tui import GremlinApp
    app = GremlinApp()
    async with app.run_test() as pilot:
        await pilot.press("a")
        await pilot.pause()
    assert queue.get("1").meta["status"] == "approved"
    assert ledger.entries()[0]["check_by"] is None  # approving isn't sending


@pytest.mark.asyncio
async def test_tui_escapes_markup_in_drafts(home):
    (home / "queue/0001-bbq.md").write_text((home / "queue/0001-bbq.md").read_text() + "\n[/b] [red]oops\n")
    from gremlincore.tui import GremlinApp
    app = GremlinApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.query_one("#draft") is not None  # renders without MarkupError


@pytest.mark.asyncio
async def test_tui_quit_asks_first(home):
    from gremlincore.tui import ConfirmModal, GremlinApp
    app = GremlinApp()
    async with app.run_test() as pilot:
        await pilot.press("q")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmModal)
        await pilot.press("n")
        await pilot.pause()
        assert not isinstance(app.screen, ConfirmModal)


def test_talk_opens_the_agent_and_can_bring_the_draft(home, monkeypatch):
    from gremlincore import queue
    from gremlincore.tui import GremlinApp
    app = GremlinApp()
    assert app.talk_cmd()[-2:] == ["gremlincore.cli", "talk"]
    monkeypatch.setenv("GREMLIN_TALK", "true")
    cmd = app.talk_cmd(queue.get("1"))
    assert cmd[0] == "true" and "queue item 0001" in cmd[1] and "0001-bbq.md" in cmd[1]


@pytest.mark.asyncio
async def test_talk_in_a_headless_terminal_says_so(home, monkeypatch):
    monkeypatch.setenv("GREMLIN_TALK", "true")
    from gremlincore.tui import GremlinApp
    app = GremlinApp()
    async with app.run_test() as pilot:
        await pilot.press("t")
        await pilot.pause()
        assert app.query_one("#queue").row_count == 1  # still alive, still refreshed


@pytest.mark.asyncio
async def test_tui_wears_the_agents_name(home):
    from gremlincore.tui import GremlinApp
    app = GremlinApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.title == "RoboPat" and app.by == "pat"
