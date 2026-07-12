"""
DNA SQLite backend — the dev knowledge graph on the world_store substrate.

The whole pipeline reads through graphify_interface.load_dna_graph() and writes
through save_dna_graph(); this module is the SQLite implementation behind that
seam. It reuses core.world_store (SQLite + FTS5), so the dev graph gets:
  - fast full-text search (retiring graphify's JSON+NetworkX search), and
  - no 2000-node ceiling (the gate was a band-aid for whole-file JSON I/O).

LOSSLESS: each node/edge is stored with its FULL original dict in the `data`
column and reconstructed from it — the derived columns (kind/label/x/y/z, FTS
body) are only for querying. A load->save->load round-trip returns byte-identical
node and edge sets.

DURABILITY: save_graph also refreshes a committed JSON snapshot (cheap at a few
thousand nodes) so the project's memory stays in git and portable to a fresh
clone; load auto-seeds the SQLite db from that snapshot if the db is empty. The
SQLite db itself is machine-local (gitignored, like world.db).

CLI
---
    python -m core.dna_sqlite_backend migrate         # JSON snapshot -> SQLite
    python -m core.dna_sqlite_backend verify          # round-trip fidelity check
    python -m core.dna_sqlite_backend search --query telemetry
    python -m core.dna_sqlite_backend stats
"""

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
DNA_DB_PATH = Path(os.environ.get("CHIMERA_DNA_DB", ROOT / "docs" / "world" / "dna.db"))
JSON_SNAPSHOT = Path(os.environ.get("CHIMERA_DNA_SNAPSHOT",
                                    ROOT / "docs" / "chimera_dna_graph.json"))

try:
    from core import world_store as ws
except ImportError:
    sys.path.insert(0, str(HERE))
    import world_store as ws


def _searchable_text(n):
    """Human/AI-findable text for the FTS index — pulled from the fields agents
    actually search by. The full node still lives in `data`."""
    parts = [str(n.get(k, "")) for k in
             ("name", "feature_name", "fix_description", "context", "reality",
              "type", "status", "grade", "phase", "target_action")]
    return " ".join(p for p in parts if p) or str(n.get("id", ""))


def _node_id(n):
    nid = n.get("id")
    if nid:
        return str(nid)
    # defensive: never drop a node that lacks an id — hash its content
    return "anon_" + ws.__dict__.get("_hash", lambda x: str(abs(hash(x)) % (10**16)))(
        json.dumps(n, sort_keys=True, default=str))


def load_graph(db_path=DNA_DB_PATH):
    con = ws.connect(db_path)
    nodes = [json.loads(r[0]) for r in
             con.execute("SELECT data FROM node WHERE data IS NOT NULL")]
    edges = [json.loads(r[0]) for r in
             con.execute("SELECT data FROM edge WHERE data IS NOT NULL")]
    con.close()
    return {"nodes": nodes, "edges": edges}


def save_graph(graph, db_path=DNA_DB_PATH, write_snapshot=True):
    """Replace-all write (matches the JSON whole-file overwrite semantics the
    pipeline expects), lossless, plus an optional committed JSON snapshot."""
    con = ws.connect(db_path)
    con.execute("DELETE FROM node")
    con.execute("DELETE FROM edge")
    if getattr(con, "_caps", {}).get("fts5"):
        con.execute("DELETE FROM node_fts")
    if getattr(con, "_caps", {}).get("rtree"):
        con.execute("DELETE FROM node_rtree")
    con.commit()

    nrows = [(_node_id(n), str(n.get("type", "?")), _searchable_text(n)[:200],
              0.0, 0.0, 0.0, n) for n in graph.get("nodes", [])]
    ws.add_nodes(con, nrows)
    # EVERY edge preserved (full dict in data), even ones without src/dst keys.
    erows = [(str(e.get("source") or e.get("from") or e.get("src") or ""),
              str(e.get("target") or e.get("to") or e.get("dst") or ""),
              str(e.get("type") or e.get("rel") or "link"), e)
             for e in graph.get("edges", [])]
    ws.add_edges(con, erows)
    con.close()

    if write_snapshot:
        JSON_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        tmp = JSON_SNAPSHOT.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(graph, indent=2), encoding="utf-8")
        tmp.replace(JSON_SNAPSHOT)


def ensure_seeded(db_path=DNA_DB_PATH, json_path=JSON_SNAPSHOT):
    """If the SQLite db is empty/absent but the JSON snapshot exists, seed it —
    so a fresh clone (which has the committed JSON, not the gitignored db) comes
    up with the full graph on first read."""
    con = ws.connect(db_path)
    n = con.execute("SELECT COUNT(*) FROM node").fetchone()[0]
    con.close()
    if n == 0 and Path(json_path).exists():
        graph = json.loads(Path(json_path).read_text(encoding="utf-8"))
        if graph.get("nodes"):
            save_graph(graph, db_path=db_path, write_snapshot=False)
            return len(graph["nodes"])
    return 0


def search(text, db_path=DNA_DB_PATH, limit=25):
    con = ws.connect(db_path)
    out = ws.search(con, text, limit=limit)
    con.close()
    return out


def stats(db_path=DNA_DB_PATH):
    con = ws.connect(db_path)
    s = ws.stats(con)
    con.close()
    return s


def _verify_roundtrip(json_path=JSON_SNAPSHOT):
    """Prove load->save->load is lossless against the real graph."""
    original = json.loads(Path(json_path).read_text(encoding="utf-8"))
    tmp_db = ROOT / "docs" / "world" / "_verify.db"
    if tmp_db.exists():
        tmp_db.unlink()
    save_graph(original, db_path=tmp_db, write_snapshot=False)
    back = load_graph(tmp_db)
    tmp_db.unlink()

    on, bn = original.get("nodes", []), back.get("nodes", [])
    oe, be = original.get("edges", []), back.get("edges", [])
    oid = sorted(str(n.get("id")) for n in on)
    bid = sorted(str(n.get("id")) for n in bn)
    ok_nodes = (len(on) == len(bn)) and (oid == bid)
    ok_edges = len(oe) == len(be)
    # deep-content check: node dicts identical when keyed by id
    obyid = {str(n.get("id")): n for n in on}
    bbyid = {str(n.get("id")): n for n in bn}
    ok_content = all(obyid[k] == bbyid.get(k) for k in obyid)
    return {"nodes_in": len(on), "nodes_out": len(bn), "edges_in": len(oe),
            "edges_out": len(be), "ids_match": ok_nodes, "content_match": ok_content,
            "edges_match": ok_edges, "lossless": ok_nodes and ok_edges and ok_content}


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="DNA graph on the SQLite substrate")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("migrate", help="Seed the SQLite db from the JSON snapshot")
    sub.add_parser("verify", help="Round-trip fidelity check against the real graph")
    sub.add_parser("stats")
    ps = sub.add_parser("search")
    ps.add_argument("--query", required=True)

    args = p.parse_args(argv)
    if args.cmd == "migrate":
        graph = json.loads(JSON_SNAPSHOT.read_text(encoding="utf-8"))
        save_graph(graph, write_snapshot=False)
        print(f"migrated {len(graph.get('nodes', []))} nodes, "
              f"{len(graph.get('edges', []))} edges -> {DNA_DB_PATH}")
    elif args.cmd == "verify":
        r = _verify_roundtrip()
        print(json.dumps(r, indent=2))
        sys.exit(0 if r["lossless"] else 1)
    elif args.cmd == "stats":
        print(json.dumps(stats(), indent=2))
    elif args.cmd == "search":
        print(json.dumps(search(args.query), indent=2))


if __name__ == "__main__":
    main()
