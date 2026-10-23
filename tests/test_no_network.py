"""The README says the runtime "phones nobody." This backs it for the code
in gremlincore/: no module there imports a network library, statically or
by a string passed to __import__ / importlib.import_module. meatbag is
allowed (local_llm talks to Ollama on localhost; voice reads feeds you list).

What this doesn't cover, said plainly: third-party dependencies (textual,
rich), and `gremlin talk`, which execs Claude Code, the one stated egress.
"""
import ast
from pathlib import Path

import pytest

RUNTIME = Path(__file__).resolve().parent.parent / "gremlincore"

NETWORK = {
    "urllib", "urllib3", "http", "socket", "socketserver", "ssl", "requests", "httpx",
    "aiohttp", "websocket", "websockets", "ftplib", "smtplib", "poplib", "imaplib",
    "telnetlib", "nntplib", "xmlrpc", "asyncssh", "paramiko", "grpc", "pycurl", "anthropic",
    "openai", "webbrowser",
}


def network_imports(src):
    """[(line, module)] for every network import in a module's source."""
    hits = []
    for node in ast.walk(ast.parse(src)):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names = [node.module]
        elif isinstance(node, ast.Call):
            f = node.func
            fname = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
            if fname in ("__import__", "import_module") and node.args \
                    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                names = [node.args[0].value]
        hits += [(node.lineno, n) for n in names if n.split(".")[0] in NETWORK]
    return hits


def test_runtime_has_no_network_imports():
    files = sorted(RUNTIME.rglob("*.py"))
    assert len(files) >= 10, "the runtime moved; point this test at it"
    found = {str(p.relative_to(RUNTIME.parent)): h for p in files if (h := network_imports(p.read_text()))}
    assert not found, f"network code in the runtime: {found}"


@pytest.mark.parametrize("src", [
    "import urllib.request",
    "from http import client",
    "import socket as s",
    "def f():\n    import requests",
    "__import__('httpx')",
    "import importlib\nimportlib.import_module('ssl')",
])
def test_the_scanner_catches_a_planted_import(src):
    assert network_imports(src), src


def test_the_scanner_ignores_relative_and_local_imports():
    assert not network_imports("from . import http\nimport subprocess\nfrom .home import root")
