"""Model-agnostic HTTP adapter. Credentials are read from a session file, not arguments.

The trusted launcher provisions each agent's own session JSON:
{"endpoint":"http://127.0.0.1:8765/v1/action", "token":"session-secret"}.
Do not provide supervisor credentials to ordinary agent sessions.
"""
import argparse
import json
from pathlib import Path
import sys
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from urllib.parse import urlparse

def call(session,operation,arguments):
    endpoint=session['endpoint'];u=urlparse(endpoint)
    if u.scheme not in ('http','https') or u.username or u.password:
        raise ValueError('invalid_endpoint')
    if u.scheme=='http' and u.hostname not in ('127.0.0.1','localhost','::1'):
        raise ValueError('nonlocal_transport_requires_https_adapter')
    body=json.dumps({'operation':operation,'arguments':arguments}).encode()
    req=Request(endpoint,data=body,headers={'Authorization':'Bearer '+session['token'],'Content-Type':'application/json'})
    try:
        with urlopen(req,timeout=30) as r:return json.load(r)
    except HTTPError as e:
        raise ValueError(e.read().decode()) from e

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--session',type=Path,required=True)
    p.add_argument('operation')
    p.add_argument('--arguments',type=Path,help='JSON object file; omit for snapshot/events.')
    a=p.parse_args()
    if a.operation=='enroll':
        p.error('Enrollment must use the trusted launcher adapter so credentials are not lost or logged.')
    try:
        s=json.loads(a.session.read_text(encoding='utf-8'))
        args=json.loads(a.arguments.read_text(encoding='utf-8')) if a.arguments else {}
        result=call(s,a.operation,args)
        # Enrollment returns a secret: refuse printing it into model/tool logs.
        if isinstance(result.get('result'),dict) and 'session_token' in result['result']:
            print('Enrollment response contains credentials; use the trusted launcher adapter, not this logging CLI.',file=sys.stderr)
            return 2
        print(json.dumps(result,indent=2));return 0
    except (OSError,ValueError,KeyError,URLError) as e:
        print('REFUSED: '+str(e),file=sys.stderr);return 2

if __name__=='__main__':sys.exit(main())
