# Export formats

`meatbag normalize` reads the export zip, or the `conversations.json`
inside it, and writes one turn per line to `data/turns.jsonl`:

```
{source, conv_id, title, summary, conv_created, idx, role, text, ts}
```

`role` is `human` or `assistant`. `idx` counts kept turns within a
conversation (empty turns are skipped). Format is detected by shape: if
the first conversation has a `mapping`, it's ChatGPT; otherwise Claude.
Synthetic examples of both live in `tests/fixtures/`.

## Claude (claude.ai: Settings, Privacy, Export data)

A list of conversations:

```json
[{"uuid": "c-0001", "name": "Barbecue logistics", "summary": "...",
  "created_at": "2025-05-02T14:00:00Z",
  "chat_messages": [
    {"sender": "human", "text": "Help me plan a barbecue for twelve.", "created_at": "..."},
    {"sender": "assistant", "text": "", "content": [{"type": "text", "text": "..."}], "created_at": "..."}]}]
```

`text` is used when present, else the `text` blocks in `content` are joined.

## ChatGPT (Settings, Data controls, Export)

A list of conversations, each a tree of nodes:

```json
[{"title": "HOA bounce castle", "conversation_id": "g-0001", "create_time": 1735000000.0,
  "current_node": "a2",
  "mapping": {"a2": {"parent": "u2", "message": {"author": {"role": "assistant"},
              "content": {"parts": ["..."]}, "create_time": 1735000040}}, "...": {}}}]
```

Only the visible branch is read: from `current_node` back through
`parent` to the root, so regenerated answers you abandoned don't count.
System and tool messages are dropped; string `parts` are joined.

## Other sources

Anything else you wrote yourself (issues, posts, Claude Code prompts)
comes in through `meatbag voice`, which reads nothing until you list
sources in `gremlin.toml` `[voice]`.

Other people are in your transcripts. Nothing here redacts them yet; see
the README.
