"""In-memory graph server: eliminates the 166s rebuild and 3.4s load
from the development loop by keeping the graph resident and applying
changes incrementally.

Usage:
    # Start the server (one time):
    python -m tools.science_funnel.graph_server --port 8290 &

    # Query / update (from any script):
    python -m tools.science_funnel.graph_client --query work.creature.coupled_arm_friction
    python -m tools.science_funnel.graph_client --add-object '{"id": ...}'
    python -m tools.science_funnel.graph_client --hash
"""
import argparse
import hashlib
import json
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.creature_graph.store import CreatureGraph

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STORE_PATH = os.path.join(ROOT, "tools", "creature_graph", "data", "creature_graph.json")


class GraphServerState:
    """Holds the graph in memory, serves queries, applies incremental updates."""

    def __init__(self):
        self.graph = None
        self.lock = threading.Lock()
        self.graph_hash = None
        self.load_count = 0
        self.query_count = 0
        self.update_count = 0

    def load(self):
        with self.lock:
            t0 = os.times()
            self.graph = CreatureGraph.load(STORE_PATH)
            self.graph_hash = self.graph.graph_hash()
            self.load_count += 1
            return {
                "objects": len(self.graph.objects),
                "relations": len(self.graph.relations),
                "graph_hash": self.graph_hash,
                "errors": self.graph.check()[:5] if self.graph.check() else [],
            }

    def query(self, object_id):
        with self.lock:
            if self.graph is None:
                self.load()
            obj = self.graph.objects.get(object_id)
            self.query_count += 1
            if obj:
                return {"found": True, "object": obj}
            return {"found": False}

    def hash(self):
        with self.lock:
            if self.graph is None:
                self.load()
            return self.graph_hash

    def add_object(self, obj):
        """Add or update an object incrementally (no full rebuild)."""
        with self.lock:
            if self.graph is None:
                self.load()
            oid = obj.get("id")
            if not oid:
                return {"ok": False, "error": "no id"}
            self.graph.objects[oid] = obj
            self.update_count += 1
            self.graph_hash = self.graph.graph_hash()
            return {"ok": True, "id": oid, "hash": self.graph_hash}

    def stats(self):
        return {
            "objects": len(self.graph.objects) if self.graph else 0,
            "graph_hash": self.graph_hash,
            "load_count": self.load_count,
            "query_count": self.query_count,
            "update_count": self.update_count,
        }


state = GraphServerState()


class GraphHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/load":
            result = state.load()
        elif parsed.path == "/query":
            oid = params.get("id", [None])[0]
            result = state.query(oid) if oid else {"error": "missing id"}
        elif parsed.path == "/hash":
            result = {"graph_hash": state.hash()}
        elif parsed.path == "/stats":
            result = state.stats()
        else:
            result = {"error": f"unknown path {parsed.path}"}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode())

    def do_POST(self):
        if self.path == "/add":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                obj = json.loads(body)
                result = state.add_object(obj)
            except json.JSONDecodeError:
                result = {"ok": False, "error": "invalid JSON"}
        else:
            result = {"error": f"unknown path {self.path}"}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def log_message(self, format, *args):
        pass  # suppress request logging


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8290)
    args = ap.parse_args()

    server = HTTPServer(("127.0.0.1", args.port), GraphHandler)
    print(f"graph server on 127.0.0.1:{args.port} (graph will load on first query)")
    server.serve_forever()


if __name__ == "__main__":
    main()
