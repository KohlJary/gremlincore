"""The TUI: the owner's send button, without a send button.

Review the queue, approve / edit / veto, record that something was sent
(after you sent it), and see the ledger, the WF count and the wake brief.
Nothing here sends anything.

  gremlin tui

Layout (docs/tui-lessons.md): StatusBar on top, QueueList left,
DraftDetail right, Footer. Vim keys at App level with priority, table
focused on mount, q confirms, every user/model string escaped, long edits
in a modal TextArea (ctrl+s saves, esc cancels), typed modals, design
tokens only.
"""
import os
import subprocess
import sys

from rich.markup import escape
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Input, Label, Static, TextArea

from . import home, ledger, queue, wake, wf


class EditModal(ModalScreen[str | None]):
    BINDINGS = [Binding("ctrl+s", "save", "Save"), Binding("escape", "cancel", "Cancel")]
    DEFAULT_CSS = """
    EditModal { align: center middle; }
    EditModal > Vertical { width: 90%; height: 85%; border: thick $primary; background: $surface; padding: 1; }
    EditModal TextArea { height: 1fr; }
    """

    def __init__(self, text):
        super().__init__()
        self.text = text

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Edit the draft. ctrl+s saves (the original is kept forever), esc cancels.")
            yield TextArea(self.text, id="editor")

    def action_save(self):
        self.dismiss(self.query_one("#editor", TextArea).text)

    def action_cancel(self):
        self.dismiss(None)


class ReasonModal(ModalScreen[str | None]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]
    DEFAULT_CSS = """
    ReasonModal { align: center middle; }
    ReasonModal > Vertical { width: 70%; height: auto; border: thick $error; background: $surface; padding: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Veto. One line on why: that's how the agent learns. (enter to veto, esc to cancel)")
            yield Input(placeholder="missed the point / sanded it down / too Greg / ...", id="reason")

    def on_mount(self):
        self.query_one("#reason", Input).focus()

    def on_input_submitted(self, event: Input.Submitted):
        if event.value.strip():
            self.dismiss(event.value.strip())

    def action_cancel(self):
        self.dismiss(None)


class ConfirmModal(ModalScreen[bool]):
    BINDINGS = [Binding("y", "yes", "Yes"), Binding("n,escape", "no", "No")]
    DEFAULT_CSS = """
    ConfirmModal { align: center middle; }
    ConfirmModal > Vertical { width: 60%; height: auto; border: thick $warning; background: $surface; padding: 1; }
    """

    def __init__(self, question):
        super().__init__()
        self.question = question

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(escape(self.question))
            with Horizontal():
                yield Button("yes (y)", id="yes", variant="warning")
                yield Button("no (n)", id="no")

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss(event.button.id == "yes")

    def action_yes(self):
        self.dismiss(True)

    def action_no(self):
        self.dismiss(False)


class TextModal(ModalScreen[None]):
    """Read-only view: the ledger or the wake brief."""
    BINDINGS = [Binding("escape,q", "close", "Close")]
    DEFAULT_CSS = """
    TextModal { align: center middle; }
    TextModal > VerticalScroll { width: 90%; height: 85%; border: thick $primary; background: $surface; padding: 1; }
    """

    def __init__(self, text):
        super().__init__()
        self.text = text

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(escape(self.text))

    def action_close(self):
        self.dismiss(None)


class GremlinApp(App):
    TITLE = "gremlin"
    CSS = """
    #status { height: 3; padding: 0 1; background: $panel; color: $text; }
    #queue { width: 40%; }
    #detail { width: 1fr; padding: 0 1; border-left: tall $primary; }
    """
    BINDINGS = [
        Binding("j", "cursor_down", "down", show=False, priority=True),
        Binding("k", "cursor_up", "up", show=False, priority=True),
        Binding("a", "approve", "approve"),
        Binding("e", "edit", "edit"),
        Binding("v", "veto", "veto"),
        Binding("S", "sent", "I sent it"),
        Binding("l", "ledger", "ledger"),
        Binding("w", "wake", "wake brief"),
        Binding("t", "talk", "talk"),
        Binding("T", "talk_draft", "talk about this"),
        Binding("r", "refresh", "refresh"),
        Binding("q", "quit_confirm", "quit"),
    ]

    def __init__(self, by=None):
        super().__init__()
        self.cfg = home.config()
        self.by = by or home.owner_id(self.cfg)
        self.agent = self.cfg["agent"]["name"]
        self.title = self.agent
        self._quitting = False

    def compose(self) -> ComposeResult:
        yield Static(id="status")
        with Horizontal():
            yield DataTable(id="queue", cursor_type="row", zebra_stripes=True)
            with VerticalScroll(id="detail"):
                yield Static(id="draft")
        yield Footer()

    def on_mount(self):
        t = self.query_one("#queue", DataTable)
        t.add_columns("id", "status", "age", "to")
        self.refresh_all()
        t.focus()

    # data

    def selected(self):
        t = self.query_one("#queue", DataTable)
        if t.row_count == 0:
            return None
        key = t.coordinate_to_cell_key(t.cursor_coordinate).row_key.value
        return queue.get(key)

    def refresh_all(self):
        es = wf.entries()
        due = ledger.due()
        sd, lc = wake.status_date(), wake.last_change()
        stale = " · STATUS STALE" if sd and lc and lc > sd else ""
        self.query_one("#status", Static).update(
            f"[b]{escape(self.agent)}[/b] · WF {sum(e.get('wf', 0) for e in es)} (target: zero) · "
            f"bets open {len(due)} · STATUS {sd or '?'}{stale}\n"
            "Nothing here sends anything. Approve means you're willing; 'I sent it' records that you did.")
        t = self.query_one("#queue", DataTable)
        cur = t.cursor_row
        t.clear()
        for i, st, kind, to, age, stale_item in queue.table():
            t.add_row(i, st + (" *" if stale_item else ""), f"{age}d", to[:40], key=i)
        if t.row_count:
            t.move_cursor(row=min(cur, t.row_count - 1))
        self.show_detail()

    def show_detail(self):
        it = self.selected()
        d = self.query_one("#draft", Static)
        if not it:
            d.update(f"Queue is empty. {escape(self.agent)} hasn't drafted anything yet.")
            return
        m = it.meta
        head = "\n".join(f"[b]{k}[/b]: {escape(m.get(k, ''))}" for k in
                         ("status", "to", "room", "why", "prediction", "edited_by", "veto_reason") if m.get(k))
        d.update(head + "\n\n" + escape(it.draft.strip()) +
                 ("\n\n[dim](original kept below the line)[/dim]" if it.original else ""))

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted):
        self.show_detail()

    # actions

    def action_cursor_down(self):
        self.query_one("#queue", DataTable).action_cursor_down()

    def action_cursor_up(self):
        self.query_one("#queue", DataTable).action_cursor_up()

    def action_refresh(self):
        self.refresh_all()

    def action_approve(self):
        it = self.selected()
        if it:
            queue.approve(it, self.by)
            self.notify(f"{it.id} approved. Nothing was sent; that's your finger.")
            self.refresh_all()

    def action_edit(self):
        it = self.selected()
        if not it:
            return

        def done(text):
            if text is not None:
                queue.edit(queue.get(it.id), text, self.by)
                self.notify(f"{it.id} edited; the original is kept.")
                self.refresh_all()
        self.push_screen(EditModal(it.draft.strip()), done)

    def action_veto(self):
        it = self.selected()
        if not it:
            return

        def done(reason):
            if reason:
                queue.veto(queue.get(it.id), reason, self.by)
                self.notify(f"{it.id} vetoed: {reason}")
                self.refresh_all()
        self.push_screen(ReasonModal(), done)

    def action_sent(self):
        it = self.selected()
        if not it:
            return

        def done(yes):
            if yes:
                queue.mark_sent(queue.get(it.id), self.by)
                self.notify(f"{it.id} recorded as sent; its bet is dated.")
                self.refresh_all()
        self.push_screen(ConfirmModal(f"Did you send {it.id} yourself? This only records it."), done)

    def action_ledger(self):
        lines = []
        for e in ledger.entries():
            state = "settled: " + str(e.get("outcome")) if e.get("outcome") is not None else (
                e.get("awaiting") or (f"check by {e['check_by']}" if e.get("check_by") else "open"))
            lines.append(f"#{e['id']} ({e['by'].split(' (')[0]}) [{state}]\n  {e['prediction']}\n")
        score = "  ".join(f"{w}: {s['hits']}/{s['settled']} of {s['bets']}" for w, s in ledger.score().items())
        self.push_screen(TextModal("Ledger\n\n" + "\n".join(lines) + "\nScore: " + score))

    def action_wake(self):
        self.push_screen(TextModal(wake.brief()))

    def talk_cmd(self, it=None):
        """The agent session, as a command. GREMLIN_TALK overrides it (tests)."""
        env = os.environ.get("GREMLIN_TALK")
        cmd = env.split() if env else [sys.executable, "-m", "gremlincore.cli", "talk"]
        if it:
            cmd.append(f"{self.cfg['owner']['name']} opened this from the TUI, on queue item {it.id} "
                       f"({it.path.name}). Wake up, read it, and let's talk about it.")
        return cmd

    def _talk(self, it=None):
        from textual.app import SuspendNotSupported
        try:
            with self.suspend():
                subprocess.run(self.talk_cmd(it))
        except SuspendNotSupported:
            self.notify("Can't hand the terminal over here; run `gremlin talk` instead.", severity="warning")
        self.refresh_all()  # a talk can change the queue

    def action_talk(self):
        self._talk()

    def action_talk_draft(self):
        self._talk(self.selected())

    def action_quit_confirm(self):
        if self._quitting:
            return
        self._quitting = True

        def done(yes):
            self._quitting = False
            if yes:
                self.exit()
        self.push_screen(ConfirmModal(f"Quit {self.agent}?"), done)


def main():
    GremlinApp().run()


if __name__ == "__main__":
    main()
