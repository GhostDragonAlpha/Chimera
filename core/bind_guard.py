"""bind_guard — refuse to commit a server that listens to the whole network.

WHY (2026-07-23). Three of this project's own servers were found bound to every network
interface: `view_renders.py` serving Saved/SplatEmit, `dashboard.py`'s Flask app, and an
ad-hoc `python -m http.server`. All three were reachable from the LAN at 192.168.3.169.

NONE OF IT WAS A DECISION. `("", PORT)` is the example in Python's own socketserver docs,
and `python -m http.server` binds 0.0.0.0 BY DEFAULT. A careful engineer copying the
official documentation produces the identical bug. So the three servers were not three
mistakes -- they were ONE MISSING CHECK, and this is that check.

    The operator: "I have to add at least minimal security because any idiot can
    fucking learn how to be a hacker now."

WHAT IT DOES NOT DO: it does not judge whether exposure is wrong. Sometimes you genuinely
want a server on the LAN. It requires you to SAY SO, on the line, with a reason -- so that
binding the world is a sentence someone wrote rather than a default nobody noticed.

    app.run(host='0.0.0.0')   # bind-public: staging box, firewalled, ticket CH-402

Run standalone over the whole tree, or let the pre-commit hook run it on staged files:

    python -m core.bind_guard              # everything tracked
    python -m core.bind_guard --staged     # what is about to be committed
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Each rule: (name, pattern, what to write instead). Patterns are deliberately narrow --
# a guard with false positives gets bypassed with --no-verify and then protects nothing.
RULES = [
    ('empty-host-tuple',
     re.compile(r'(?:TCPServer|HTTPServer|ThreadingHTTPServer|socket\w*)\s*\(\s*\(\s*["\']\s*["\']\s*,'),
     'an empty host string means EVERY interface; write "127.0.0.1" instead'),

    ('bind-empty',
     re.compile(r'\.bind\(\s*\(\s*["\']\s*["\']\s*,'),
     'an empty host string means EVERY interface; write "127.0.0.1" instead'),

    ('explicit-any-host',
     re.compile(r'(?:host\s*=\s*|--host[= ]|--bind[= ]|HOST\s*=\s*)["\']?(?:0\.0\.0\.0|::)\b'),
     '0.0.0.0 and :: mean EVERY interface; write 127.0.0.1 instead'),

    ('any-host-tuple',
     re.compile(r'\(\s*["\'](?:0\.0\.0\.0|::)["\']\s*,\s*\w*[Pp][Oo][Rr][Tt]'),
     '0.0.0.0 and :: mean EVERY interface; write 127.0.0.1 instead'),

    ('http-server-default',
     re.compile(r'python\s+-m\s+http\.server(?![^\n]*--bind)'),
     'python -m http.server binds EVERY interface by default; add --bind 127.0.0.1'),
]

# The escape hatch. Exposure is allowed -- it just has to be a sentence somebody wrote.
ALLOW = re.compile(r'#\s*bind-public\b|//\s*bind-public\b|REM\s+bind-public\b', re.I)

SCAN_SUFFIXES = {'.py', '.js', '.ts', '.tsx', '.cmd', '.bat', '.sh', '.ps1',
                 '.json', '.yml', '.yaml', '.toml', '.cfg', '.ini'}

SKIP_PARTS = {'node_modules', '.git', 'site-packages', 'dist', 'build', '__pycache__',
              '.venv', 'venv', 'WorldModel/training_data', 'Saved'}

# This file necessarily contains the patterns it looks for.
SELF = 'core/bind_guard.py'


def _skip(path: str) -> bool:
    p = path.replace('\\', '/')
    if p.endswith(SELF) or p == SELF:
        return True
    if Path(p).suffix.lower() not in SCAN_SUFFIXES:
        return True
    return any(part in p for part in SKIP_PARTS)


def scan_text(path: str, text: str) -> list:
    """Marker applies to its own line OR to the next code line.

    Both styles are normal and a guard that only accepts one of them just teaches people
    to reach for --no-verify:

        app.run(host='0.0.0.0')   # bind-public: reason

        # bind-public: a longer reason that needs
        #   more than one line to explain
        app.run(host='0.0.0.0')
    """
    hits = []
    armed = False
    for i, line in enumerate(text.splitlines(), 1):
        if ALLOW.search(line):
            armed = True
            continue
        stripped = line.strip()
        if armed and (not stripped or stripped.startswith(('#', '//', 'REM ', 'rem '))):
            continue                      # still inside the explaining comment block
        for name, pat, advice in RULES:
            if pat.search(line):
                if armed:
                    break
                hits.append({'file': path, 'line': i, 'rule': name,
                             'advice': advice, 'text': line.strip()[:110]})
                break
        if stripped:
            armed = False                 # the marker covers ONE statement, not a file
    return hits


def _staged_files() -> list:
    out = subprocess.run(['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
                         capture_output=True, text=True)
    return [f for f in out.stdout.splitlines() if f.strip()]


def _tracked_files() -> list:
    out = subprocess.run(['git', 'ls-files'], capture_output=True, text=True)
    return [f for f in out.stdout.splitlines() if f.strip()]


def check(paths: list, root: Path) -> list:
    hits = []
    for f in paths:
        if _skip(f):
            continue
        p = root / f
        try:
            hits += scan_text(f, p.read_text(encoding='utf-8', errors='replace'))
        except (OSError, UnicodeError):
            continue
    return hits


def main() -> int:
    root = Path(subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                               capture_output=True, text=True).stdout.strip() or '.')
    staged = '--staged' in sys.argv
    files = _staged_files() if staged else _tracked_files()
    hits = check(files, root)

    if not hits:
        print(f'[bind-guard] PASS: no server binds the whole network '
              f'({len(files)} file(s) considered)')
        return 0

    print('')
    print('[bind-guard] REFUSED: a server here would answer the ENTIRE network,')
    print('             not just this machine. Anyone on your LAN could reach it.')
    print('')
    for h in hits:
        print(f"  {h['file']}:{h['line']}  [{h['rule']}]")
        print(f"      {h['text']}")
        print(f"      -> {h['advice']}")
        print('')
    print('  127.0.0.1 (localhost) serves this machine only. The agent and the browser')
    print('  both run here, so it costs you nothing.')
    print('')
    print('  If you genuinely mean to expose it, say so on the line and why:')
    print("      app.run(host='0.0.0.0')   # bind-public: reason goes here")
    print('')
    print('  Full explanation: docs/LOCAL_SERVERS.md')
    print('')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
