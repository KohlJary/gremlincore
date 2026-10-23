"""Ollama's native chat endpoint (the OpenAI-compatible one ignores num_ctx).
OLLAMA_HOST overrides the server."""
import json
import os
import urllib.request

_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA = ("" if "://" in _HOST else "http://") + _HOST + "/api/chat"


def chat_json(model, system, user, num_ctx=8192, timeout=300):
    body = {
        "model": model, "stream": False, "think": False, "format": "json",
        "options": {"num_ctx": num_ctx, "temperature": 0.2},
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
    }
    req = urllib.request.Request(OLLAMA, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        content = json.loads(r.read())["message"]["content"]
    return json.loads(content)
