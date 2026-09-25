"""Loopback-only, read-only ontology inspector. Stops after idle time; no polling."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import time
from urllib.parse import urlsplit
from model import canonical, snapshot


def handler_for(root, definition, web):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            self.request.settimeout(5)
            super().setup()

        def log_message(self, *args):
            pass

        def send(self, status, raw, kind):
            self.send_response(status)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            self.server.last_request = time.monotonic()
            path = urlsplit(self.path).path
            if path == '/api/ontology':
                try:
                    raw = canonical(snapshot(definition, root))
                    self.send(200, raw, 'application/json; charset=utf-8')
                except (OSError, ValueError, TypeError, RecursionError) as exc:
                    self.send(422, canonical({'refused': str(exc)}), 'application/json; charset=utf-8')
                return
            routes = {'/': ('index.html', 'text/html'), '/index.html': ('index.html', 'text/html'),
                      '/assets/app.js': ('assets/app.js', 'text/javascript'),
                      '/assets/style.css': ('assets/style.css', 'text/css')}
            if path not in routes:
                self.send(404, b'Not found', 'text/plain')
                return
            name, kind = routes[path]
            try:
                self.send(200, (web / name).read_bytes(), kind + '; charset=utf-8')
            except OSError:
                self.send(404, b'Asset unavailable', 'text/plain')

        def do_POST(self):
            self.send(405, b'Read-only inspector', 'text/plain')

    return Handler


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument('--definition', type=Path, default=Path(__file__).with_name('ontology.json'))
    p.add_argument('--port', type=int, default=8029)
    p.add_argument('--idle-seconds', type=int, default=1800)
    args = p.parse_args()
    if not 1 <= args.idle_seconds <= 86400:
        p.error('idle-seconds must be 1..86400')
    web = Path(__file__).resolve().parents[2] / 'web/ontology'
    with HTTPServer(('127.0.0.1', args.port), handler_for(args.root.resolve(), args.definition.resolve(), web)) as server:
        server.timeout = 1
        server.last_request = time.monotonic()
        print(f'http://127.0.0.1:{server.server_port}/ (read-only; idle exit {args.idle_seconds}s)', flush=True)
        try:
            while time.monotonic() - server.last_request < args.idle_seconds:
                server.handle_request()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
