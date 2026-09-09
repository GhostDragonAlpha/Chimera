"""Trusted enrollment launcher: creates one agent session file via HTTP.

Credentials stay in a private session file (0600-equivalent); nothing is
printed to stdout so tokens never enter model or tool logs. The enrollment
token is read from the environment (CHIMERA_FLEET_ENROLLMENT_TOKEN), never
from arguments.
"""
import argparse
import json
import os
import stat
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--endpoint', required=True, help='e.g. http://127.0.0.1:8765/v1/action')
    p.add_argument('--agent', required=True)
    p.add_argument('--label', required=True)
    p.add_argument('--out', required=True, type=Path, help='private session file to write')
    a = p.parse_args()

    token = os.environ.get('CHIMERA_FLEET_ENROLLMENT_TOKEN', '')
    if not token:
        print('REFUSED: CHIMERA_FLEET_ENROLLMENT_TOKEN not set', file=sys.stderr)
        return 2
    body = json.dumps({'operation': 'enroll',
                       'arguments': {'agent': a.agent, 'label': a.label}}).encode()
    req = Request(a.endpoint, data=body,
                  headers={'Authorization': 'Bearer ' + token,
                           'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=30) as r:
            result = json.load(r)
    except (HTTPError, URLError, OSError) as e:
        print('REFUSED: ' + str(e), file=sys.stderr)
        return 2
    inner = result.get('result') or {}
    secret = inner.get('session_token')
    if not secret:
        print('REFUSED: enrollment did not return a session token', file=sys.stderr)
        return 2
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({'endpoint': a.endpoint, 'token': secret}),
                     encoding='utf-8')
    try:
        a.out.chmod(a.out.stat().st_mode & ~(stat.S_IRWXG | stat.S_IRWXO))
    except OSError:
        pass
    print(json.dumps({'enrolled': a.agent, 'session_file': str(a.out)}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
