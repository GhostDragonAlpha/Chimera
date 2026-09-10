"""Local authenticated control service. No model spawning, Git or engine execution."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sqlite3
import sys

from control import Refusal
from review_handoff import ReviewHandoffControl

MAX_BODY=65536  # Transport policy, not a physics constant.

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass  # Never echo tokens or request bodies.
    def reply(self,code,payload):
        raw=json.dumps(payload).encode()
        self.send_response(code); self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_POST(self):
        if self.path!='/v1/action': return self.reply(404,{'error':'unknown_path'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=MAX_BODY: raise Refusal('request_size')
            auth=self.headers.get('Authorization','')
            if not auth.startswith('Bearer '):raise Refusal('bearer_required')
            request=json.loads(self.rfile.read(size))
            if not isinstance(request,dict) or set(request)-{'operation','arguments'}:raise Refusal('invalid_envelope')
            args=request.get('arguments',{})
            if not isinstance(args,dict) or not isinstance(request.get('operation'),str):raise Refusal('invalid_envelope')
            result=self.server.control.call(request['operation'],auth[7:],**args)
            return self.reply(200,result)
        except (Refusal,ValueError,TypeError,KeyError) as e:
            return self.reply(409,{'error':str(e)})
        except sqlite3.Error:
            return self.reply(503,{'error':'control_store_unavailable_retry_read_state'})
    def do_GET(self):
        self.reply(405,{'error':'authenticated_post_required'})

class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,control):
        self.control=control;super().__init__(address,Handler)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--db',type=Path,required=True)
    p.add_argument('--port',type=int,required=True)
    a=p.parse_args()
    admin=os.environ.get('CHIMERA_FLEET_SUPERVISOR_TOKEN','')
    enroll=os.environ.get('CHIMERA_FLEET_ENROLLMENT_TOKEN','')
    if not admin or not enroll:
        p.error('Set distinct supervisor/enrollment secrets outside agent worktrees; never paste secrets into prompts.')
    ctl=ReviewHandoffControl(a.db,admin,enroll,a.root)
    # Loopback only. Remote/WSL transport needs an explicit deployment adapter.
    server=Server(('127.0.0.1',a.port),ctl)
    print(f'Control service listening on 127.0.0.1:{server.server_port}; no engine/Git/model actions enabled.',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=='__main__':main()
