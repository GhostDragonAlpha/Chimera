"""Graphify PROJECTION exporter -- the authored store stays canonical and local.

Contract (docs/graphify-agent-integration note + brief 2026-09-15):
  * The canonical AUTHORED store (data/creature_graph.json + data/authored/)
    stays local and durable; this module only EXPORTS a compatible projection.
  * Extraction refreshes never overwrite authored content: a refresh re-reads
    the authored store and the EXTRACTED engine snapshot, and rewrites ONLY the
    projection directory.
  * The projection is a node-link MULTIDIGRAPH: edge direction and relation
    multiplicity are preserved (parallel distinct relations between the same
    pair export as separate edges with distinct keys) -- verified by
    acceptance.py (evidence items 7-8).
  * Graph-layout coordinates are exported as node ATTRIBUTES (roadmap_tier/
    roadmap_x), never as engine coordinates; the engine's live state is never
    written back into the authored store.

Output: data/graphify_projection/creature_graph_projection.json
Format-compatible with the main repo's Chimera/core/graphify-out/graph.json:
{"directed": true, "multigraph": true, "graph": {...}, "nodes": [...], "edges": [...]}
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PROJ_DIR = os.path.join(HERE, "data", "graphify_projection")
PROJ_PATH = os.path.join(PROJ_DIR, "creature_graph_projection.json")


def _sanitize(oid: str) -> str:
    """Graphify-compatible node id: lowercase, [a-z0-9_] only, collision-safe.
    The mapping original->sanitized is exported alongside (identity of objects
    is preserved across the projection boundary)."""
    s = re.sub(r"[^a-z0-9_]", "_", oid.lower())
    return s


def export(g, extracted_snapshot: dict = None) -> dict:
    """Build + write the projection. Returns the export report."""
    nodes = []
    id_map = {}
    for oid, obj in sorted(g.objects.items()):
        sid = _sanitize(oid)
        id_map[oid] = sid
        node = {
            "id": sid,
            "label": obj.get("name") or oid,
            "kind": obj.get("kind"),
            "status": obj.get("status"),
            "priority": obj.get("priority"),
            "classification": obj.get("classification"),
            "inventory_anchor": obj.get("inventory_anchor"),
            "external_ids": obj.get("external_ids"),
            "units": obj.get("units"),
            "value": obj.get("value"),
            "source": obj.get("source"),
            "applicability": obj.get("applicability"),
            "validation": obj.get("validation"),
            "unknowns": obj.get("unknowns"),
            "falsifier_statement": (obj.get("falsifier") or {}).get("statement"),
            "_authored_id": oid,   # reversible join to the canonical store
        }
        # layout positions ride ONLY as graph-drawing attributes
        lay = g.layout.get(oid)
        if lay:
            node["roadmap_tier"] = lay.get("roadmap_tier")
            node["roadmap_x"] = lay.get("roadmap_x")
        nodes.append(node)
    edges = []
    for i, r in enumerate(sorted(g.relations,
                                 key=lambda r: (r["src"], r["rel"], r["dst"],
                                                r.get("note", "")))):
        edges.append({
            "source": id_map[r["src"]],
            "target": id_map[r["dst"]],
            "relation": r["rel"],       # typed, DIRECTION PRESERVED
            "note": r.get("note", ""),
            "key": i,                   # MULTIPPLICITY preserved (multiDiGraph)
        })
    projection = {
        "directed": True,
        "multigraph": True,
        "graph": {
            "origin": "tools/creature_graph (ChimeraWork slot-01)",
            "canonical_store": "tools/creature_graph/data/creature_graph.json",
            "schema_version": g.meta.get("schema_version"),
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "note": "PROJECTION ONLY -- the authored store is canonical; "
                    "extracting/refreshing this projection never rewrites "
                    "authored requirements or spatial design; graph-layout "
                    "coordinates are drawing attributes, never engine "
                    "coordinates",
        },
        "nodes": nodes,
        "edges": edges,
        "id_map": id_map,
    }
    if extracted_snapshot is not None:
        projection["graph"]["engine_snapshot"] = {
            "ticks": extracted_snapshot.get("ticks"),
            "ts_us": extracted_snapshot.get("ts_us"),
            "note": "read-only live-state reference; the engine owns live state",
        }
    os.makedirs(PROJ_DIR, exist_ok=True)
    tmp = PROJ_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(projection, f, indent=1, ensure_ascii=False)
    os.replace(tmp, PROJ_PATH)
    return {"path": os.path.normpath(PROJ_PATH),
            "n_nodes": len(nodes), "n_edges": len(edges),
            "sha256": hashlib.sha256(
                json.dumps(projection, sort_keys=True).encode()).hexdigest()[:16]}


def refresh(g, extracted_snapshot: dict = None) -> dict:
    """A refresh = re-export from the canonical store. Authored inputs are
    opened READ-ONLY; only the projection directory is written."""
    return export(g, extracted_snapshot)
