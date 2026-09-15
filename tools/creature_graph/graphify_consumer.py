"""Graphify CONSUMER bridge -- the projection meets its REAL consumer.

The missing half of the integration (2026-09-15): graphify_projection.py
exports a node-link multidigraph, but nothing ever showed a Graphify surface
CONSUMING it. This module closes that with the main repo's OWN machinery
(Chimera/core/graphify_interface.py + dna_sqlite_backend.py -- verified
byte-identical to E:/PythonChimera's copy at a12bfbcc):

  projection JSON --load+validate--> collision pre-check --> ingest through
  gi.save_dna_graph (provenance-stamped, lock-guarded, SQLite replace-all +
  JSON snapshot) --> queries back through gi.load_dna_graph /
  gi.graphify_query("health") / gi.because_of / dna FTS search.

Contract enforced here (the bridge's own falsifiers):
  (a) SCHEMA GATE: the projection is validated BEFORE load -- directed
      multidigraph, graph.schema_version == schema.SCHEMA_VERSION exactly
      (the legacy "1.0.0-unversioned" is REFUSED), id_map/node/edge
      structural agreement. A bridge that loads without validation fails
      its own contract.
  (b) ROUND-TRIP IDENTITY: every node and every edge ingested is queried
      back THROUGH the consumer store and compared against the native
      CreatureGraph -- _authored_id reversibility, label/kind/status
      equality, edge DIRECTION, relation MULTIPLICITY (parallel edges stay
      parallel), and a 2-hop traversal parity check. Any mismatch -> the
      bridge reports NOT HONEST and exits nonzero.
  (c) SANITIZER PRE-CHECK: the exporter's _sanitize is not provably
      injective (D3 #5); the bridge inverts id_map and REFUSES ingestion on
      any collision rather than corrupt the store. (Current store measures
      0 collisions -- the defect is latent; the fix routes to the packet,
      not here.)

WHERE IT WRITES: a SCRATCH Graphify store under
  tools/creature_graph/data/graphify_demo/   (CHIMERA_DNA_DB +
  CHIMERA_DNA_SNAPSHOT pinned to sqlite scratch BEFORE core is imported, so
  neither the worktree's real DNA store nor the read-only canonical root is
  ever touched). Set CHIMERA_DNA_DB yourself to aim the bridge at a store of
  your choosing (import this module BEFORE core.graphify_interface then).
  Ingestion is IDEMPOTENT: previously-ingested projection nodes/edges
  (marker: origin == "creature_graph_projection") are replaced, never
  duplicated.

SEMANTICS KEPT HONEST: creature relations are ingested as plain dual-keyed
edges (src/dst/rel + source/target/type, exactly because_edge's convention)
but NEVER via because_edge()/record_because() -- a creature edge is not a
why-edge, so rel=="because" is refused and proves/question are never
fabricated. Node type "CreatureObject" is a distinct Graphify family; "name"
mirrors "label" only because dna_sqlite_backend._searchable_text indexes
name/type/status -- that alias is the FTS findability contract, nothing
more. Graph-layout coordinates ride as node ATTRIBUTES only; no engine
coordinate is read or written.

One-command demo:  python tools/creature_graph/graphify_consumer.py
"""

import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

DEMO_DIR = os.path.join(HERE, "data", "graphify_demo")
DEMO_DB = os.path.join(DEMO_DIR, "dna_consumer_demo.db")
DEMO_SNAPSHOT = os.path.join(DEMO_DIR, "dna_consumer_demo_snapshot.json")
DEMO_PROJECTION = os.path.join(DEMO_DIR, "creature_graph_projection.json")
DEMO_REPORT = os.path.join(DEMO_DIR, "consumer_demo_report.json")

ORIGIN = "creature_graph_projection"
NODE_TYPE = "CreatureObject"
RESERVED_RELS = ("because",)   # the why-edge rel; a creature edge must never take it


class ProjectionRejected(ValueError):
    """The projection failed the schema/structure gate (falsifier a)."""


# ---------------------------------------------------------------- store pin
def pin_scratch_store():
    """Pin the Graphify store env to the scratch demo store BEFORE core is
    imported (dna_sqlite_backend reads CHIMERA_DNA_DB at import time). An
    operator-set CHIMERA_DNA_DB is respected; the JSON backend is refused
    because its path is the worktree's real tracked snapshot."""
    os.makedirs(DEMO_DIR, exist_ok=True)
    os.environ["CHIMERA_DNA_BACKEND"] = "sqlite"
    os.environ.setdefault("CHIMERA_DNA_DB", DEMO_DB)
    os.environ.setdefault("CHIMERA_DNA_SNAPSHOT", DEMO_SNAPSHOT)


def load_graphify():
    """Import the REAL Graphify interface (worktree copy) AFTER the store is
    pinned, and assert the pin actually took effect."""
    pin_scratch_store()
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    chimera_dir = os.path.join(ROOT, "Chimera")
    if chimera_dir not in sys.path:
        sys.path.insert(0, chimera_dir)
    from core import graphify_interface as gi       # noqa: E402
    from core import dna_sqlite_backend as dna_db   # noqa: E402
    if gi.DNA_BACKEND != "sqlite":
        raise RuntimeError("consumer requires the sqlite DNA backend; got "
                           f"{gi.DNA_BACKEND!r}")
    if os.environ.get("CHIMERA_DNA_DB") == DEMO_DB and \
            str(dna_db.DNA_DB_PATH) != DEMO_DB:
        raise RuntimeError("store pin failed: backend resolved "
                           f"{dna_db.DNA_DB_PATH}, expected {DEMO_DB}")
    return gi, dna_db


# ------------------------------------------------------------- falsifier (a)
def load_projection(path=DEMO_PROJECTION):
    """Validate BEFORE load. Returns the projection dict or raises
    ProjectionRejected with EVERY violation found."""
    import schema  # sibling module: the store's own schema law

    errs = []
    proj = None
    if not os.path.exists(path):
        raise ProjectionRejected([f"projection file missing: {path}"])
    try:
        with open(path, encoding="utf-8") as f:
            proj = json.load(f)
    except (json.JSONDecodeError, OSError) as ex:
        raise ProjectionRejected([f"projection unreadable: {ex}"]) from ex

    if proj.get("directed") is not True:
        errs.append(f"directed must be true, got {proj.get('directed')!r}")
    if proj.get("multigraph") is not True:
        errs.append(f"multigraph must be true, got {proj.get('multigraph')!r}")
    graph_meta = proj.get("graph") or {}
    version = graph_meta.get("schema_version")
    if version != schema.SCHEMA_VERSION:
        errs.append("schema_version must be "
                    f"{schema.SCHEMA_VERSION!r}, got {version!r} "
                    f"(legacy {schema.SCHEMA_VERSION_LEGACY!r} is refused)")
    id_map = proj.get("id_map")
    if not isinstance(id_map, dict) or not id_map:
        errs.append("id_map missing or empty")
    nodes = proj.get("nodes")
    edges = proj.get("edges")
    if not isinstance(nodes, list) or not nodes:
        errs.append("nodes missing or empty")
    if not isinstance(edges, list):
        errs.append("edges missing or not a list")

    node_ids = set()
    if isinstance(nodes, list):
        for n in nodes:
            nid = n.get("id")
            if not nid:
                errs.append(f"node without id: {n!r:.120}")
                continue
            if nid in node_ids:
                errs.append(f"duplicate node id: {nid}")
            node_ids.add(nid)
            for field in ("label", "kind", "status", "_authored_id"):
                if not n.get(field):
                    errs.append(f"node {nid}: missing {field}")
    if isinstance(id_map, dict) and node_ids:
        if set(id_map.values()) != node_ids:
            only_map = set(id_map.values()) - node_ids
            only_nodes = node_ids - set(id_map.values())
            errs.append(f"id_map/node disagreement: map-only={sorted(only_map)[:5]} "
                        f"node-only={sorted(only_nodes)[:5]}")

    if isinstance(edges, list):
        for e in edges:
            for field in ("source", "target", "relation", "key"):
                if e.get(field) is None and field != "key":
                    errs.append(f"edge missing {field}: {e!r:.120}")
            if e.get("relation") in RESERVED_RELS:
                errs.append(f"edge uses reserved rel 'because': {e!r:.120}")
            if node_ids:
                for end in ("source", "target"):
                    if e.get(end) not in node_ids:
                        errs.append(f"edge endpoint {end}={e.get(end)!r} "
                                    "names no node")
    if errs:
        raise ProjectionRejected(errs)
    return proj


# ------------------------------------------------------------- falsifier (c)
def id_collision_report(id_map):
    """Invert the exporter's id_map. A sanitized id claimed by 2+ originals
    would collapse distinct objects in ANY consumer keyed by node id."""
    seen = {}
    for oid, sid in id_map.items():
        seen.setdefault(sid, []).append(oid)
    collisions = {sid: oids for sid, oids in sorted(seen.items()) if len(oids) > 1}
    return {"n_originals": len(id_map),
            "n_distinct_sanitized": len(seen),
            "collisions": collisions,
            "collision_count": len(collisions)}


# ------------------------------------------------------------------ mapping
def projection_to_dna(proj):
    """Map the projection into DNA-graph dicts (PURE -- no store touched).

    Nodes keep EVERY projection field verbatim (lossless) plus:
      type     "CreatureObject"  (distinct Graphify node family)
      name     mirror of label   (FTS-indexed field; see module docstring)
      timestamp  the projection's generated_utc (provenance anchor; the
                 interface stamps recorded_by/run_id itself on save)
      origin   ORIGIN marker     (idempotent replace on re-ingest)
    Edges are dual-keyed exactly like because_edge builds them
    (src/dst/rel + source/target/type) -- WITHOUT because-edge semantics.
    """
    generated = (proj.get("graph") or {}).get("generated_utc")
    nodes = []
    for n in proj["nodes"]:
        d = dict(n)
        d["type"] = NODE_TYPE
        d["name"] = n.get("label")
        d["timestamp"] = generated
        d["origin"] = ORIGIN
        nodes.append(d)
    edges = []
    for e in proj["edges"]:
        d = {"src": e["source"], "dst": e["target"], "rel": e["relation"],
             "note": e.get("note", ""), "key": e.get("key"),
             "source": e["source"], "target": e["target"],
             "type": e["relation"], "origin": ORIGIN}
        edges.append(d)
    return nodes, edges


def ingest(gi, nodes, edges):
    """Ingest through the REAL write path: load -> extend -> save_dna_graph
    (provenance stamping + atomic sqlite replace-all + JSON snapshot).
    Idempotent: previous projection nodes/edges are replaced, not stacked."""
    graph = gi.load_dna_graph()
    nodes_before = len(graph.get("nodes", []))
    edges_before = len(graph.get("edges", []))
    # idempotent replace: prior projection rows are removed, then re-added --
    # never stacked (a re-run must leave the store at exactly one projection)
    nodes_replaced = sum(1 for n in graph.get("nodes", [])
                         if n.get("origin") == ORIGIN)
    edges_replaced = sum(1 for e in graph.get("edges", [])
                         if e.get("origin") == ORIGIN)
    kept_nodes = [n for n in graph.get("nodes", []) if n.get("origin") != ORIGIN]
    kept_edges = [e for e in graph.get("edges", []) if e.get("origin") != ORIGIN]
    kept_nodes.extend(nodes)
    kept_edges.extend(edges)
    gi.save_dna_graph({"nodes": kept_nodes, "edges": kept_edges})
    return {"nodes_before": nodes_before, "edges_before": edges_before,
            "nodes_added": len(nodes), "edges_added": len(edges),
            "nodes_replaced": nodes_replaced, "edges_replaced": edges_replaced}


# ------------------------------------------------------------- falsifier (b)
def _native_edge_multiset(g):
    return Counter((r["src"], r["rel"], r["dst"], r.get("note", ""))
                   for r in g.relations)


def _consumer_edge_multiset(back, inv_map):
    out = Counter()
    for e in back.get("edges", []):
        if e.get("origin") != ORIGIN:
            continue
        src_oid = inv_map.get(e.get("src"))
        dst_oid = inv_map.get(e.get("dst"))
        out[(src_oid, e.get("rel"), dst_oid, e.get("note", ""))] += 1
    return out


def _bfs(adj, start, depth):
    seen = {start}
    frontier = {start}
    for _ in range(depth):
        nxt = set()
        for node in frontier:
            for tgt in adj.get(node, ()):
                if tgt not in seen:
                    seen.add(tgt)
                    nxt.add(tgt)
        frontier = nxt
    seen.discard(start)
    return seen


def verify(g, proj, gi, dna_db, ingest_report):
    """Query EVERYTHING back through the consumer store and compare against
    the native store. Returns (checks, all_pass)."""
    back = gi.load_dna_graph()
    inv_map = {sid: oid for oid, sid in proj["id_map"].items()}
    back_nodes = {}
    for n in back.get("nodes", []):
        if n.get("origin") == ORIGIN:
            back_nodes[n["id"]] = n
    checks = []

    def add(name, expected, observed, ok, evidence=None):
        checks.append({"check": name, "expected": expected,
                       "observed": observed, "pass": bool(ok),
                       **({"evidence": evidence} if evidence else {})})

    # -- node identity: ALL objects, reversibility + content
    mismatches = []
    for oid, sid in sorted(proj["id_map"].items()):
        bn = back_nodes.get(sid)
        native = g.objects[oid]
        if bn is None:
            mismatches.append(f"{oid}: node {sid} absent from consumer store")
            continue
        if bn.get("_authored_id") != oid:
            mismatches.append(f"{sid}: _authored_id {bn.get('_authored_id')!r} "
                              f"!= {oid!r}")
        for field, key in (("label", "name"), ("kind", "kind"),
                           ("status", "status")):
            if bn.get(field) != native.get(key):
                mismatches.append(f"{oid}: {field} {bn.get(field)!r} != "
                                  f"{native.get(key)!r}")
    add("node_identity_round_trip", f"all {len(proj['id_map'])} objects "
        "reversible + label/kind/status equal", 
        f"{len(proj['id_map']) - len(mismatches)}/{len(proj['id_map'])} ok",
        not mismatches, {"mismatches": mismatches[:10]})

    # -- edge identity: direction + notes, as a multiset over native ids
    native_ms = _native_edge_multiset(g)
    consumer_ms = _consumer_edge_multiset(back, inv_map)
    missing = list((native_ms - consumer_ms).elements())
    extra = list((consumer_ms - native_ms).elements())
    add("edge_identity_round_trip",
        f"all {sum(native_ms.values())} relations with direction+note intact",
        f"missing={len(missing)} extra={len(extra)}",
        not missing and not extra,
        {"missing_sample": [str(m) for m in missing[:5]],
         "extra_sample": [str(e) for e in extra[:5]]})

    # -- multiplicity: per-(src,rel,dst) totals must match exactly; a
    #    consumer that collapsed parallel edges would show smaller totals
    nat_tot = Counter((s, r, d) for (s, r, d, _n) in native_ms.elements())
    con_tot = Counter((s, r, d) for (s, r, d, _n) in consumer_ms.elements())
    add("multiplicity_preserved",
        {str(k): v for k, v in sorted(nat_tot.items()) if v > 1} or
        "no parallel groups in store (all pairs single-edged)",
        {str(k): v for k, v in sorted(con_tot.items()) if v > 1} or
        "no parallel groups in store",
        nat_tot == con_tot)

    # -- traversal parity: 2 hops from the max-degree native node
    native_adj = {}
    for r in g.relations:
        native_adj.setdefault(r["src"], []).append(r["dst"])
    start = max(sorted(g.objects), key=lambda o: len(native_adj.get(o, ())))
    con_adj = {}
    for e in back.get("edges", []):
        if e.get("origin") == ORIGIN:
            con_adj.setdefault(e["src"], []).append(e["dst"])
    start_sid = proj["id_map"][start]
    native_reach = _bfs(native_adj, start, 2)
    con_reach = {inv_map.get(s) for s in _bfs(con_adj, start_sid, 2)}
    add("traversal_parity_2hop",
        sorted(native_reach),
        sorted(x for x in con_reach if x is not None),
        native_reach == con_reach,
        {"start": start, "out_degree": len(native_adj.get(start, ()))})

    # -- consumer surface: the interface's own health query sees the ingest
    health = gi.graphify_query("health")
    # replace-all semantics: prior projection rows were REPLACED, so the
    # store total is (foreign rows) + (this projection's rows)
    exp_total = (ingest_report["nodes_before"]
                 - ingest_report["nodes_replaced"]
                 + ingest_report["nodes_added"])
    add("graphify_query_health", exp_total, health.get("total_nodes"),
        health.get("total_nodes") == exp_total,
        {"mutations": health.get("mutations"),
         "pathways": health.get("pathways"),
         "features": health.get("features"),
         "note": "creature objects must not pollute the DNA families"})

    # -- consumer surface: because_of runs over ingested data and answers
    #    honestly (creature nodes carry no why-edges -> [])
    why = gi.because_of(start_sid, graph=back)
    add("because_of_honest_empty", [], why, why == [])

    # -- consumer surface: FTS search finds an ingested node by name
    probe_oid = start
    probe_word = (g.objects[probe_oid].get("name") or probe_oid).split()[0]
    hits = dna_db.search(probe_word)
    hit_ids = {h["id"] for h in hits}
    add("fts_search_finds_ingested", proj["id_map"][probe_oid],
        sorted(hit_ids)[:5], proj["id_map"][probe_oid] in hit_ids,
        {"query": probe_word, "n_hits": len(hits)})

    return checks, all(c["pass"] for c in checks)


# --------------------------------------------------------------------- demo
def run_demo():
    """One command: build native store -> export projection -> validate ->
    collision pre-check -> ingest -> verify round trip. Exit 0 iff honest."""
    import build_graph          # sibling
    import graphify_projection  # sibling exporter (used, never modified)

    report = {"origin": ORIGIN,
              "bridge": "tools/creature_graph/graphify_consumer.py"}

    # 1. the native store is the truth (in memory; the authored store file
    #    is never rewritten by this demo)
    g = build_graph.build(with_reference=True)
    report["native_store"] = {"objects": len(g.objects),
                              "relations": len(g.relations),
                              "schema_version": g.meta.get("schema_version")}
    print(f"[1] native store: {len(g.objects)} objects / "
          f"{len(g.relations)} relations (schema {g.meta.get('schema_version')})")

    # 2. export a FRESH projection into the demo dir (the exporter's own
    #    code path; the committed projection under data/graphify_projection/
    #    is left untouched)
    graphify_projection.PROJ_DIR = DEMO_DIR
    graphify_projection.PROJ_PATH = DEMO_PROJECTION
    export_report = graphify_projection.export(g)
    report["export"] = export_report
    print(f"[2] exported projection: {export_report['n_nodes']} nodes / "
          f"{export_report['n_edges']} edges -> "
          f"{os.path.relpath(DEMO_PROJECTION, ROOT)}")

    # 3. falsifier (a): validate BEFORE load
    try:
        proj = load_projection(DEMO_PROJECTION)
        gate = {"accepted": True, "schema_version":
                proj["graph"]["schema_version"]}
    except ProjectionRejected as ex:
        gate = {"accepted": False, "violations": ex.args[0]}
        report["schema_gate"] = gate
        _write_report(report)
        print("SCHEMA GATE REFUSED THE PROJECTION:")
        for v in ex.args[0]:
            print("   -", v)
        return 1
    report["schema_gate"] = gate
    print(f"[3] schema gate: ACCEPTED (schema_version "
          f"{proj['graph']['schema_version']}, directed multidigraph)")

    # 4. falsifier (c): sanitizer collision pre-check
    col = id_collision_report(proj["id_map"])
    report["sanitizer_precheck"] = col
    print(f"[4] sanitizer pre-check: {col['n_originals']} originals -> "
          f"{col['n_distinct_sanitized']} distinct ids, "
          f"{col['collision_count']} collisions")
    if col["collision_count"]:
        print("   INGESTION REFUSED -- sanitized-id collisions would corrupt "
              "identity (D3 #5); fix routes to the Codex packet:")
        for sid, oids in list(col["collisions"].items())[:10]:
            print(f"   {sid} <- {oids}")
        _write_report(report)
        return 1

    # 5. ingest through the REAL write path
    gi, dna_db = load_graphify()
    nodes, edges = projection_to_dna(proj)
    ingest_report = ingest(gi, nodes, edges)
    report["ingest"] = ingest_report
    print(f"[5] ingested via save_dna_graph: +{ingest_report['nodes_added']} "
          f"nodes / +{ingest_report['edges_added']} edges "
          f"(store was {ingest_report['nodes_before']}/"
          f"{ingest_report['edges_before']})")

    # 6. falsifier (b): round-trip identity through the consumer store
    checks, ok = verify(g, proj, gi, dna_db, ingest_report)
    report["round_trip_checks"] = checks
    report["honest"] = ok
    print("[6] round-trip verification (against the native store):")
    for c in checks:
        print(f"    {'PASS' if c['pass'] else 'FAIL'}  {c['check']}"
              + ("" if c["pass"] else
                 f"  expected={c['expected']!r:.100} observed={c['observed']!r:.100}"))
    verdict = "HONEST -- the consumer round-trips the projection" if ok else \
              "NOT HONEST -- mismatches recorded above"
    print(f"VERDICT: {verdict}")
    report["verdict"] = verdict
    _write_report(report)
    return 0 if ok else 1


def _write_report(report):
    os.makedirs(DEMO_DIR, exist_ok=True)
    with open(DEMO_REPORT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=1, ensure_ascii=False, default=str)
    print(f"report: {os.path.relpath(DEMO_REPORT, ROOT)}")


if __name__ == "__main__":
    sys.exit(run_demo())
