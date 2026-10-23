"""Learn from the red pen: the owner's edits and vetoes, grouped by room.

Only the owner's edits count (edited_by: <owner>). A helper's or the
agent's own edits are not lessons from the owner. A veto whose reason says
the draft missed, softened or overclaimed gets a proposed WF line, so the
mistake ledger doesn't depend on the agent remembering.

  gremlin lessons
"""
import difflib
import re

from . import home, queue

_WF_WORDS = (r"miss|soft|sand|overclaim|wrong|not me|greg|corporate|"
             r"respectable|boring|cringe|lie|made up|fake")


def wf_worthy():
    """The veto words that mean the draft fucked up. "not <owner>" counts too."""
    return re.compile(_WF_WORDS + "|not " + re.escape(home.owner().lower()), re.I)


def changed_share(a, b):
    """How much of the draft the owner rewrote: 0 (nothing) to 1 (everything)."""
    return round(1 - difflib.SequenceMatcher(None, a, b).ratio(), 2)


def lessons():
    out, me, pat = [], home.owner_id(), wf_worthy()
    for it in queue.items():
        room = it.meta.get("room", "?").split("(")[0].strip()
        st = it.meta.get("status")
        if st in ("edited", "approved", "sent") and it.meta.get("edited_by") == me and it.original:
            orig, new = it.original.strip(), it.draft.strip()
            diff = [l for l in difflib.unified_diff(orig.splitlines(), new.splitlines(), lineterm="", n=0)
                    if l[:1] in "+-" and not l.startswith(("+++", "---"))]
            out.append({"id": it.id, "room": room, "kind": "edit",
                        "changed": changed_share(orig, new), "diff": diff[:12]})
        elif st == "vetoed":
            reason = it.meta.get("veto_reason", "")
            les = {"id": it.id, "room": room, "kind": "veto", "reason": reason}
            if pat.search(reason):
                les["proposed_wf"] = (f'gremlin wf add --what "queue {it.id} vetoed: {reason}" '
                                      f'--who "{home.owner()}" --wf 1 --root-cause "<why the draft did that>" '
                                      f'--change "<the persona/skill line that stops it>" --found-by {me}')
            out.append(les)
    return out


def by_room():
    rooms = {}
    for les in lessons():
        rooms.setdefault(les["room"], []).append(les)
    return rooms


def main():
    ls = lessons()
    if not ls:
        print(f"No lessons yet: {home.owner()} hasn't edited or vetoed anything. The red pen is the training data.")
        return
    for room, group in by_room().items():
        edits = [l["changed"] for l in group if l["kind"] == "edit"]
        avg = f", avg rewritten {sum(edits)/len(edits):.0%}" if edits else ""
        print(f"## {room}: {len(group)} lesson(s){avg}")
        for l in group:
            if l["kind"] == "edit":
                print(f"- {l['id']} edited, {l['changed']:.0%} rewritten")
                for d in l["diff"]:
                    print(f"    {d[:110]}")
            else:
                print(f"- {l['id']} vetoed: {l['reason']}")
                if "proposed_wf" in l:
                    print(f"    proposed: {l['proposed_wf']}")


if __name__ == "__main__":
    main()
