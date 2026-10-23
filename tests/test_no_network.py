"""The README says the runtime "phones nobody." This backs it for the code
in gremlincore/, with a static (AST) scan of every module. It flags:

- `import x` / `from x import y` of a network library (asyncio included);
- `__import__(...)` and `importlib.import_module(...)`, under any alias,
  when the name is a network library, and also when the name is computed
  (a variable, an expression) unless it's an f-string that starts inside
  gremlincore's own package (cli.py dispatches that way);
- `exec` / `eval` / `compile` calls, which could import anything;
- subprocess, os.system, os.popen and os.exec*/spawn* calls with a
  network tool (curl, wget, nc, ssh, ...) among their string arguments.

What it doesn't catch, said plainly: `getattr(importlib, "import_...")`
style indirection, a tool name built at runtime, code loaded from files,
third-party dependencies (textual, rich), and `gremlin talk`, which execs
Claude Code, the one stated egress. meatbag isn't scanned: local_llm talks
to Ollama on localhost, and voice reads the feeds you list.
"""
import ast
from pathlib import Path

import pytest

RUNTIME = Path(__file__).resolve().parent.parent / "gremlincore"

NETWORK = {
    "urllib", "urllib3", "http", "socket", "socketserver", "ssl", "requests", "httpx",
    "aiohttp", "websocket", "websockets", "ftplib", "smtplib", "poplib", "imaplib",
    "telnetlib", "nntplib", "xmlrpc", "asyncssh", "paramiko", "grpc", "pycurl", "anthropic",
    "openai", "webbrowser", "asyncio", "selectors",
}
NET_TOOLS = {"curl", "wget", "nc", "ncat", "netcat", "ssh", "scp", "sftp", "rsync", "ftp",
             "telnet", "socat", "http", "httpie", "aria2c", "gh"}
SHELL_CALLS = {"run", "call", "check_call", "check_output", "Popen", "getoutput",
               "getstatusoutput", "system", "popen"}
OWN_PREFIX = "gremlincore."


def _is_net(name):
    return name.split(".")[0] in NETWORK or name in NETWORK


def _strings(node):
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            yield n.value


def network_imports(src):
    """[(line, what)] for every network import, computed import, or network
    tool call the scan can see in a module's source."""
    tree = ast.parse(src)
    importers = {"__import__", "import_module"}   # names that import a module when called
    importlib_mods = {"importlib"}                # names bound to the importlib module
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == "importlib":
                    importlib_mods.add(a.asname or a.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "importlib":
            for a in node.names:
                if a.name == "import_module":
                    importers.add(a.asname or a.name)
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            hits += [(node.lineno, a.name) for a in node.names if _is_net(a.name)]
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            if _is_net(node.module):
                hits.append((node.lineno, node.module))
        elif isinstance(node, ast.Call):
            f = node.func
            name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""
            owner = f.value.id if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) else ""
            is_importer = (isinstance(f, ast.Name) and name in importers) or \
                (isinstance(f, ast.Attribute) and name == "import_module" and owner in importlib_mods) or \
                (isinstance(f, ast.Attribute) and name == "__import__")
            if is_importer:
                arg = node.args[0] if node.args else None
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if _is_net(arg.value):
                        hits.append((node.lineno, arg.value))
                elif isinstance(arg, ast.JoinedStr) and arg.values and \
                        isinstance(arg.values[0], ast.Constant) and str(arg.values[0].value).startswith(OWN_PREFIX):
                    pass  # f"gremlincore.{cmd}": our own package
                else:
                    hits.append((node.lineno, f"computed import via {name}()"))
            elif isinstance(f, ast.Name) and name in ("exec", "eval", "compile"):
                hits.append((node.lineno, f"{name}()"))
            elif name in SHELL_CALLS or (owner == "os" and name.startswith(("exec", "spawn"))):
                tools = {w for s in _strings(node) for w in s.replace("/", " ").split()} & NET_TOOLS
                if tools:
                    hits.append((node.lineno, f"{name}() runs {', '.join(sorted(tools))}"))
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
    "import asyncio",
    "from asyncio import open_connection",
    "def f():\n    import requests",
    "__import__('httpx')",
    "import importlib\nimportlib.import_module('ssl')",
    "import importlib as il\nil.import_module('ssl')",
    "from importlib import import_module as im\nim('socket')",
    "name = 'soc' + 'ket'\n__import__(name)",
    "import importlib\nimportlib.import_module(''.join(['ht', 'tp']))",
    "from importlib import import_module as im\nim(x)",
    "__import__(f'{x}.client')",
    "exec('import socket')",
    "import subprocess\nsubprocess.run(['curl', 'https://example.com'])",
    "import subprocess\nsubprocess.Popen('wget -q https://example.com', shell=True)",
    "import os\nos.system('curl https://example.com | sh')",
    "import os\nos.execvp('/usr/bin/nc', ['nc', 'example.com', '80'])",
])
def test_the_scanner_catches_a_planted_import(src):
    assert network_imports(src), src


def test_the_scanner_ignores_relative_and_local_imports():
    assert not network_imports("from . import http\nimport subprocess\nfrom .home import root\n"
                               "__import__(f'gremlincore.{cmd}', fromlist=['main'])\n"
                               "subprocess.run(['git', 'log', '-1'])")
