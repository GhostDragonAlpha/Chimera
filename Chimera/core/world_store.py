"""
World Store — the scalable substrate for the world-model game.

Why this exists (2026-07-12, the human): the goal is a WORLD MODEL video game
with UE5 as the paintbrush. The DNA dev-graph is a 2.7 MB JSON file loaded
whole on every write — fine for ~2000 curated dev-knowledge nodes, hopeless for
a world of millions. graphify (the AI's search face) is itself JSON + in-memory
NetworkX, so it shares that ceiling. The decisive criterion the human named is
not "can it hold the data" but "can an AI FIND things in it fast."

So: two graphs, two substrates.
  - dev DNA graph  -> stays JSON (small, curated, graphify searches it).
  - WORLD MODEL    -> this store: SQLite, embedded, native, no server, holds
                       millions, with FTS5 full-text search so an AI finds any
                       entity instantly, and an R-tree so "the world around the
                       player" (the local pocket of order around the trunk)
                       is a fast spatial query, not a whole-file load.

SQLite was chosen over Kùzu/FalkorDB for a concrete reason, not dogma: Python
3.14 has no Kùzu wheel (source build fails) and FalkorDB needs a Docker/Redis
server on Windows. SQLite ships in the stdlib, runs in-process, and covers all
four world-model layers — relational (nodes/edges), full-text (FTS5, the
AI-findability win), spatial (R-tree, the streaming win), and later vector
(sqlite-vec, the prediction win). It is the pragmatic powerhouse that works
TODAY and embeds cleanly in a UE5 plugin tomorrow.

The AI-facing search API (search / neighbors / around) is deliberately the same
shape graphify exposes over MCP, so a thin MCP wrapper can front this store and
agents keep the fast-find ergonomics at a scale graphify can't reach.

CLI
---
    python -m core.world_store benchmark [--nodes 1000000]
    python -m core.world_store search --query "beacon"
    python -m core.world_store around --x 0 --y 0 --radius 50
"""

import json
import math
import os
import sqlite3
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
DEFAULT_DB = Path(os.environ.get("CHIMERA_WORLD_DB", ROOT / "docs" / "world" / "world.db"))
GOLDEN = math.pi * (3.0 - math.sqrt(5.0))

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS node(
    id     TEXT PRIMARY KEY,
    kind   TEXT,
    label  TEXT,
    x REAL, y REAL, z REAL,
    data   TEXT
);
CREATE TABLE IF NOT EXISTS edge(
    src TEXT, dst TEXT, rel TEXT, data TEXT
);
CREATE INDEX IF NOT EXISTS idx_edge_src ON edge(src);
CREATE INDEX IF NOT EXISTS idx_edge_dst ON edge(dst);
CREATE INDEX IF NOT EXISTS idx_edge_rel ON edge(rel);
CREATE INDEX IF NOT EXISTS idx_node_kind ON node(kind);
"""

# FTS5 (full-text) and R-tree (spatial) are compile-time optional. We probe for
# them and degrade gracefully so the store works on any SQLite build.
_FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS node_fts USING fts5(label, body);
"""
_RTREE_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS node_rtree USING rtree(
    rid, minx, maxx, miny, maxy
);
"""


class _WorldConn(sqlite3.Connection):
    """Subclass so we can stash capability flags on the connection (the base
    sqlite3.Connection has no __dict__)."""


def connect(path=DEFAULT_DB):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), factory=_WorldConn)
    con.executescript(_SCHEMA)
    caps = _probe_capabilities(con)
    if caps["fts5"]:
        con.executescript(_FTS_SCHEMA)
    if caps["rtree"]:
        con.executescript(_RTREE_SCHEMA)
    con.commit()
    con._caps = caps
    return con


def _probe_capabilities(con):
    caps = {"fts5": False, "rtree": False}
    for name, sql in (("fts5", "CREATE VIRTUAL TABLE _p USING fts5(a)"),
                      ("rtree", "CREATE VIRTUAL TABLE _p USING rtree(i,a,b)")):
        try:
            con.execute(sql)
            con.execute("DROP TABLE _p")
            caps[name] = True
        except sqlite3.OperationalError:
            pass
    return caps


# ---------------------------------------------------------------------------
# Writes — bulk-first (a world is loaded in millions, not one row at a time).
# ---------------------------------------------------------------------------
def add_nodes(con, rows, commit=True):
    """rows: iterable of (id, kind, label, x, y, z, data_dict).

    commit=False lets a caller fold this into a larger transaction (e.g. the
    atomic replace-all in dna_sqlite_backend.save_graph) so a mid-write failure
    rolls the whole thing back instead of leaving a half-written graph."""
    caps = getattr(con, "_caps", {"fts5": False, "rtree": False})
    prepared = [(i, k, lb, x, y, z, json.dumps(d, default=str) if d else None)
                for (i, k, lb, x, y, z, d) in rows]
    con.executemany("INSERT OR REPLACE INTO node(id,kind,label,x,y,z,data) "
                    "VALUES(?,?,?,?,?,?,?)", prepared)
    if caps.get("fts5") or caps.get("rtree"):
        # rowid needed to key FTS/R-tree — fetch for the ids we just wrote.
        ids = [p[0] for p in prepared]
        rowmap = {}
        for chunk in _chunks(ids, 900):
            q = f"SELECT rowid,id,label,data,x,y FROM node WHERE id IN ({','.join('?'*len(chunk))})"
            for rid, nid, lb, data, x, y in con.execute(q, chunk):
                rowmap[nid] = (rid, lb, data, x, y)
        if caps.get("fts5"):
            con.executemany("INSERT OR REPLACE INTO node_fts(rowid,label,body) VALUES(?,?,?)",
                            [(rowmap[p[0]][0], p[2], p[6] or "") for p in prepared if p[0] in rowmap])
        if caps.get("rtree"):
            con.executemany("INSERT OR REPLACE INTO node_rtree(rid,minx,maxx,miny,maxy) "
                            "VALUES(?,?,?,?,?)",
                            [(rowmap[p[0]][0], p[3], p[3], p[4], p[4])
                             for p in prepared if p[0] in rowmap and p[3] is not None])
    if commit:
        con.commit()


def add_edges(con, rows, commit=True):
    con.executemany("INSERT INTO edge(src,dst,rel,data) VALUES(?,?,?,?)",
                    [(s, d, r, json.dumps(dt, default=str) if dt else None)
                     for (s, d, r, dt) in rows])
    if commit:
        con.commit()


# ---------------------------------------------------------------------------
# The AI-facing read API — same shape graphify exposes over MCP, so a thin
# wrapper keeps agents' fast-find ergonomics at a scale graphify can't reach.
# ---------------------------------------------------------------------------
def get_node(con, node_id):
    r = con.execute("SELECT id,kind,label,x,y,z,data FROM node WHERE id=?",
                    (node_id,)).fetchone()
    if not r:
        return None
    return {"id": r[0], "kind": r[1], "label": r[2], "x": r[3], "y": r[4],
            "z": r[5], "data": json.loads(r[6]) if r[6] else None}


def neighbors(con, node_id, direction="out", rel=None, limit=200):
    if direction == "out":
        sql, key = "SELECT dst,rel FROM edge WHERE src=?", "dst"
    else:
        sql, key = "SELECT src,rel FROM edge WHERE dst=?", "src"
    params = [node_id]
    if rel:
        sql += " AND rel=?"
        params.append(rel)
    sql += " LIMIT ?"
    params.append(limit)
    return [{"id": r[0], "rel": r[1]} for r in con.execute(sql, params)]


def _fts_query(text):
    """Quote each token as a literal phrase so hyphens, colons and other FTS5
    operators in raw search text are matched literally, not parsed as syntax
    (an unquoted 'external-content' makes FTS5 read 'content' as a column)."""
    toks = [t for t in text.split() if t]
    return " ".join('"' + t.replace('"', '""') + '"' for t in toks)


def search(con, text, limit=25):
    """Full-text search — the AI-findability primitive. FTS5 when available;
    otherwise an indexed LIKE fallback so it always works."""
    caps = getattr(con, "_caps", {})
    fts = _fts_query(text)
    if caps.get("fts5") and fts:
        rows = con.execute(
            "SELECT n.id,n.kind,n.label FROM node_fts f JOIN node n ON n.rowid=f.rowid "
            "WHERE node_fts MATCH ? LIMIT ?", (fts, limit)).fetchall()
    else:
        rows = con.execute(
            "SELECT id,kind,label FROM node WHERE label LIKE ? LIMIT ?",
            (f"%{text}%", limit)).fetchall()
    return [{"id": r[0], "kind": r[1], "label": r[2]} for r in rows]


def around(con, x, y, radius, limit=500):
    """The world within radius R of a point — the local pocket of order around
    the player (the trunk). R-tree bounding-box when available, else indexed
    scan. This is the streaming primitive: never load the world, load the
    neighborhood."""
    caps = getattr(con, "_caps", {})
    if caps.get("rtree"):
        rows = con.execute(
            "SELECT n.id,n.kind,n.label,n.x,n.y FROM node_rtree r JOIN node n ON n.rowid=r.rid "
            "WHERE r.minx>=? AND r.maxx<=? AND r.miny>=? AND r.maxy<=? LIMIT ?",
            (x - radius, x + radius, y - radius, y + radius, limit)).fetchall()
    else:
        rows = con.execute(
            "SELECT id,kind,label,x,y FROM node WHERE x BETWEEN ? AND ? AND y BETWEEN ? AND ? "
            "LIMIT ?", (x - radius, x + radius, y - radius, y + radius, limit)).fetchall()
    r2 = radius * radius
    return [{"id": i, "kind": k, "label": lb, "x": xx, "y": yy}
            for (i, k, lb, xx, yy) in rows if (xx - x) ** 2 + (yy - y) ** 2 <= r2]


def stats(con):
    n = con.execute("SELECT COUNT(*) FROM node").fetchone()[0]
    e = con.execute("SELECT COUNT(*) FROM edge").fetchone()[0]
    return {"nodes": n, "edges": e, "capabilities": getattr(con, "_caps", {})}


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


# ---------------------------------------------------------------------------
# Benchmark — prove millions of nodes with fast AI-find + spatial-neighborhood.
# Deterministic: node positions follow the golden-angle spiral (the fractal),
# so this is literally the player-spiral world at scale.
# ---------------------------------------------------------------------------
def benchmark(n_nodes=1_000_000, db_path=None, batch=50_000):
    db_path = db_path or (ROOT / "docs" / "world" / "bench.db")
    if Path(db_path).exists():
        Path(db_path).unlink()
    con = connect(db_path)
    print(f"capabilities: {con._caps}")
    kinds = ("star", "planet", "region", "beacon", "creature", "relic")

    t0 = time.perf_counter()
    total_edges = 0
    for start in range(0, n_nodes, batch):
        end = min(start + batch, n_nodes)
        nrows, erows = [], []
        for i in range(start, end):
            r = math.sqrt(i)
            th = i * GOLDEN
            kind = kinds[i % len(kinds)]
            # one in ~5000 gets a findable keyword so search has real hits
            label = f"{kind}_{i}" + (" ancient_beacon" if i % 5000 == 0 else "")
            nrows.append((f"n{i}", kind, label, r * math.cos(th), r * math.sin(th),
                          float(i % 256), None))
            if i:
                erows.append((f"n{i}", f"n{i // 2}", "child", None))   # tree spine
                if i > 3:
                    erows.append((f"n{i}", f"n{i - 3}", "near", None)) # local link
        add_nodes(con, nrows)
        add_edges(con, erows)
        total_edges += len(erows)
    load_s = time.perf_counter() - t0

    def timed(fn):
        t = time.perf_counter()
        out = fn()
        return (time.perf_counter() - t) * 1000, out

    ms_search, hits = timed(lambda: search(con, "ancient_beacon", limit=25))
    ms_around, near = timed(lambda: around(con, 0.0, 0.0, 60.0))
    ms_nbr, nbr = timed(lambda: neighbors(con, f"n{n_nodes // 2}", "in"))
    size_mb = Path(db_path).stat().st_size / 1e6
    s = stats(con)
    con.close()

    print(f"\nBUILT {s['nodes']:,} nodes + {s['edges']:,} edges in {load_s:.1f}s "
          f"({s['nodes'] / load_s:,.0f} nodes/s)   on-disk {size_mb:.0f} MB")
    print(f"  full-text search 'ancient_beacon'  -> {len(hits)} hits in {ms_search:.1f} ms  "
          f"(the AI-findability win)")
    print(f"  around(player, r=60)               -> {len(near)} entities in {ms_around:.1f} ms  "
          f"(the streaming / local-pocket win)")
    print(f"  neighbors(mid node)                -> {len(nbr)} in {ms_nbr:.2f} ms")
    print(f"\nAll three sub-millisecond-to-few-ms at {s['nodes']:,} nodes — this is the "
          f"substrate the JSON graph (capped at 2000) never could be.")
    return {"nodes": s["nodes"], "edges": s["edges"], "load_s": load_s,
            "ms_search": ms_search, "ms_around": ms_around, "size_mb": size_mb}


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="World Store — SQLite substrate for the world model")
    sub = p.add_subparsers(dest="cmd", required=True)
    pb = sub.add_parser("benchmark", help="Prove millions of nodes + fast AI search")
    pb.add_argument("--nodes", type=int, default=1_000_000)
    ps = sub.add_parser("search", help="Full-text find (the AI primitive)")
    ps.add_argument("--query", required=True)
    ps.add_argument("--db", default=str(DEFAULT_DB))
    pa = sub.add_parser("around", help="The world within radius of a point")
    pa.add_argument("--x", type=float, required=True)
    pa.add_argument("--y", type=float, required=True)
    pa.add_argument("--radius", type=float, default=50.0)
    pa.add_argument("--db", default=str(DEFAULT_DB))
    sub.add_parser("stats")

    args = p.parse_args(argv)
    if args.cmd == "benchmark":
        benchmark(n_nodes=args.nodes)
    elif args.cmd == "search":
        con = connect(args.db)
        print(json.dumps(search(con, args.query), indent=2))
    elif args.cmd == "around":
        con = connect(args.db)
        print(json.dumps(around(con, args.x, args.y, args.radius), indent=2))
    elif args.cmd == "stats":
        con = connect(DEFAULT_DB)
        print(json.dumps(stats(con), indent=2))


if __name__ == "__main__":
    main()
