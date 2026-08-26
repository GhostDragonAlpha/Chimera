"""
The Fractal Spiral — the studio's whole structure as a self-similar DNA spiral
rooted at the player (the trunk).

Vision (2026-07-12, the human): complexity should UNFOLD like a fractal. The
player is the trunk; features spiral around it; each feature's exams spiral
around IT; the SAME golden-angle law places every node at every scale, so
growth is self-similar, never ad hoc. The pattern (of nodes and edges) is what
links the board, tunnel, gauntlet, curriculum, and faculty into one body.

Three truths this makes literal
-------------------------------
1. PHYLLOTAXIS. The golden angle (137.507°) is exactly how a tree arranges
   leaves so none shades another (the entropy monologue's own image). Features
   placed on r = c*sqrt(n), theta = n*golden never overlap at any density.
2. THE FRACTAL. The layout is RECURSIVE: player -> loops -> features -> exams
   -> verify-specs, each level a smaller spiral seeded by its parent's angle.
   One rule, every scale. New complexity is always placed by the same law.
3. THE DOUBLE HELIX. A feature has two strands — IMPLEMENTATION and
   VERIFICATION (its curriculum transcript). Checkpoints are the base-pair
   rungs binding them. The DNA is the feature paired with its exams.

Substrate: the DNA graph (docs/chimera_dna_graph.json) via graphify_interface —
the same graph the graphify MCP server exposes. This module READS the live
structure and computes a deterministic (zero-LM, zero-random) layout. It does
NOT bloat the graph (the node-count gate is tight); the layout is a derived
overlay emitted to docs/spiral/, and --sign records ONE summary node.

CLI
---
    python -m core.fractal_spiral build [--svg] [--sign]
    python -m core.fractal_spiral neighborhood --node <id>
    python -m core.fractal_spiral stats
"""

import json
import math
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
OUT_DIR = Path(os.environ.get("CHIMERA_SPIRAL_DIR", ROOT / "docs" / "spiral"))

GOLDEN_ANGLE = math.pi * (3.0 - math.sqrt(5.0))   # 137.507...°, in radians
CHILD_SCALE = 0.34                                 # each depth's spiral shrinks -> self-similar
RING_UNIT = 150.0                                  # top-level radius unit (px)

LOOP_NAMES = {
    0: "The Player", 1: "The Ground", 2: "Basic Verbs", 3: "The Sky",
    4: "Tools", 5: "Other Dots", 6: "Shelter", 7: "Travel",
    8: "Systems", 9: "The Universe",
}

# Status -> strand health (color intent; the SVG maps these to CSS).
_STATUS_TIER = {
    "verified": "done", "encoded": "done", "observed": "done", "deferred": "done",
    "observed_provisional": "ripening", "sim_verified": "ripening",
    "accepted_tacit": "ripening", "implemented": "growing",
    "needs_refinement": "scarred", "blocked": "scarred",
    "not_started": "seed", None: "seed",
}


# ---------------------------------------------------------------------------
# Read the live structure from the DNA graph + curriculum transcripts.
# ---------------------------------------------------------------------------
def _load_structure():
    """Return the studio as a nested dict tree, WITHOUT coordinates:
       player -> loops -> features -> (implementation strand + verification
       strand of graduated exam bands)."""
    try:
        from core.graphify_interface import load_dna_graph
        from core.preflight import _latest_feature_statuses
    except ImportError:
        sys.path.insert(0, str(HERE))
        from graphify_interface import load_dna_graph
        from preflight import _latest_feature_statuses

    nodes = load_dna_graph().get("nodes", [])
    updates = _latest_feature_statuses(nodes)

    ledger = {}   # loop -> {feature: ledger_status}
    for n in nodes:
        if n.get("type") == "Feature" and str(n.get("spiral_loop", "")).startswith("Loop"):
            try:
                ln = int(n["spiral_loop"].split()[-1])
            except (ValueError, IndexError):
                continue
            ledger.setdefault(ln, {})[n.get("name")] = n.get("status", "not_started")

    transcripts = _load_transcripts()

    root = {"id": "player", "kind": "trunk", "label": "The Player",
            "status": None, "children": []}
    matched = set()
    for ln in sorted(ledger):
        loop_node = {"id": f"loop-{ln}", "kind": "loop",
                     "label": f"Loop {ln} · {LOOP_NAMES.get(ln, '?')}",
                     "status": None, "children": []}
        for fname, ledger_status in sorted(ledger[ln].items()):
            status = updates.get(fname, (None, ledger_status))[1] or ledger_status
            feat = {"id": f"feat::{fname}", "kind": "feature", "label": fname,
                    "status": status, "children": []}
            tr = transcripts.get(fname)
            if tr:                       # the verification strand exists
                feat["children"] = _exam_strand(tr)
                feat["enrolled"] = True
                matched.add(fname)
            loop_node["children"].append(feat)
        if loop_node["children"]:
            root["children"].append(loop_node)

    # Features in school but not in the loop ledger (candidate-named) still carry
    # a full verification strand — attach them as their own limb off the trunk so
    # the fractal's recursion (the double helix, depth 3+) stays visible. The
    # name mismatch itself is a real bridge gap, surfaced here rather than hidden.
    orphans = [f for f in transcripts if f not in matched]
    if orphans:
        school = {"id": "loop-school", "kind": "loop",
                  "label": "In School (enrolled)", "status": None, "children": []}
        for fname in sorted(orphans):
            tr = transcripts[fname]
            band_i = tr.get("band_index", 0)
            tier = "done" if band_i >= 7 else "ripening"
            school["children"].append(
                {"id": f"feat::{fname}", "kind": "feature", "label": fname,
                 "status": "verified" if band_i >= 7 else "sim_verified",
                 "enrolled": True, "children": _exam_strand(tr)})
        root["children"].append(school)
    return root


def _load_transcripts():
    out = {}
    feats_dir = ROOT / "docs" / "gauntlet" / "features"
    if not feats_dir.exists():
        return out
    for tp in feats_dir.glob("*/transcript.json"):
        try:
            tr = json.loads(tp.read_text(encoding="utf-8"))
            out[tr["feature"]] = tr
        except Exception:
            continue
    return out


def _exam_strand(tr):
    """The verification strand: one node per band the feature has entered, each
    carrying its passed checkpoints as base-pair rungs."""
    passed = tr.get("passed", {})
    by_band = {}
    for cid, rec in passed.items():
        band = cid.split(".")[0]
        by_band.setdefault(band, []).append(cid)
    bands = []
    for band, cids in by_band.items():
        bands.append({"id": f"band::{tr['feature']}::{band}", "kind": "band",
                      "label": f"{band} ({len(cids)})", "status": "done",
                      "children": [{"id": f"cp::{c}", "kind": "checkpoint",
                                    "label": c, "status": "done", "children": []}
                                   for c in sorted(cids)]})
    return bands


# ---------------------------------------------------------------------------
# THE FRACTAL LAYOUT — recursive golden-angle phyllotaxis. This is the whole
# idea: the same law at every scale, seeded by the parent's own angle so the
# child spiral swirls off the parent like a branch off a trunk.
# ---------------------------------------------------------------------------
def layout(root):
    placed = []
    edges = []

    def place(node, cx, cy, scale, depth, seed_angle, parent_id):
        node = {**node}
        node["x"], node["y"], node["depth"] = cx, cy, depth
        node["tier"] = _STATUS_TIER.get(node.get("status"), "seed")
        children = node.pop("children", [])
        keep = ("id", "kind", "label", "x", "y", "depth", "tier", "status", "enrolled")
        placed.append({k: node[k] for k in keep if k in node})
        if parent_id is not None:
            edges.append((parent_id, node["id"]))
        n = len(children)
        for i, child in enumerate(children):
            # Vogel phyllotaxis: radius grows as sqrt(index), angle steps by the
            # golden angle. seed_angle offsets the whole child fan so it trails
            # the parent's own bearing -> a branch, not a starburst.
            r = scale * math.sqrt(i + 0.5)
            theta = seed_angle + (i + 1) * GOLDEN_ANGLE
            place(child, cx + r * math.cos(theta), cy + r * math.sin(theta),
                  scale * CHILD_SCALE, depth + 1, theta, node["id"])

    place(root, 0.0, 0.0, RING_UNIT, 0, 0.0, None)
    return placed, edges


def build(sign=False):
    root = _load_structure()
    placed, edges = layout(root)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"generated_by": "core.fractal_spiral",
               "golden_angle_deg": round(math.degrees(GOLDEN_ANGLE), 4),
               "child_scale": CHILD_SCALE,
               "counts_by_depth": _counts_by_depth(placed),
               "counts_by_kind": _counts_by_kind(placed),
               "nodes": placed,
               "edges": [{"from": a, "to": b} for a, b in edges]}
    (OUT_DIR / "spiral_layout.json").write_text(json.dumps(payload, indent=1),
                                                encoding="utf-8")
    if sign:
        _sign_to_graph(payload)
    return payload


def _counts_by_depth(placed):
    out = {}
    for p in placed:
        out[p["depth"]] = out.get(p["depth"], 0) + 1
    return {str(k): out[k] for k in sorted(out)}


def _counts_by_kind(placed):
    out = {}
    for p in placed:
        out[p["kind"]] = out.get(p["kind"], 0) + 1
    return out


def _sign_to_graph(payload):
    """Use the power of the graph WITHOUT bloating it: record ONE node that
    signs the fractal's current shape (root, depth profile, kind counts), so the
    graph itself carries the spiral's signature over time."""
    try:
        from core.graphify_interface import record_phase
        record_phase("Fractal spiral signature",
                     f"root=player golden={payload['golden_angle_deg']} "
                     f"depths={payload['counts_by_depth']} "
                     f"kinds={payload['counts_by_kind']}", "")
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# The linking query — the fractal neighborhood of any node.
# ---------------------------------------------------------------------------
def neighborhood(node_id, payload=None):
    payload = payload or build()
    by_id = {p["id"]: p for p in payload["nodes"]}
    if node_id not in by_id:
        raise KeyError(f"{node_id!r} not in the spiral")
    parent = next((e["from"] for e in payload["edges"] if e["to"] == node_id), None)
    children = [e["to"] for e in payload["edges"] if e["from"] == node_id]
    siblings = [e["to"] for e in payload["edges"]
                if e["from"] == parent and e["to"] != node_id] if parent else []
    return {"node": by_id[node_id], "trunk": parent,
            "siblings": siblings, "branches": children}


# ---------------------------------------------------------------------------
# SVG render — the DNA spiral swirling around the player. Self-contained,
# theme-aware (currentColor + a small palette), no external assets.
# ---------------------------------------------------------------------------
_TIER_COLOR = {"done": "#3fb950", "ripening": "#d29922", "growing": "#58a6ff",
               "scarred": "#f85149", "seed": "#8b949e"}
_KIND_R = {"trunk": 13, "loop": 6.5, "feature": 4.5, "band": 3.0, "checkpoint": 1.8}


def render_svg(payload=None, size=900):
    payload = payload or build()
    nodes = payload["nodes"]
    by_id = {p["id"]: p for p in nodes}
    xs = [p["x"] for p in nodes] or [0]
    ys = [p["y"] for p in nodes] or [0]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    pad = size * 0.08
    scale = (size - 2 * pad) / span
    cx0 = (max(xs) + min(xs)) / 2
    cy0 = (max(ys) + min(ys)) / 2

    def sx(x): return round(size / 2 + (x - cx0) * scale, 1)
    def sy(y): return round(size / 2 + (y - cy0) * scale, 1)

    parts = [
        f'<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="ui-sans-serif,system-ui,sans-serif">',
        f'<rect width="{size}" height="{size}" fill="#0d1117"/>',
        '<g stroke="#30363d" stroke-width="0.6" fill="none" opacity="0.55">',
    ]
    for e in payload["edges"]:
        a, b = by_id.get(e["from"]), by_id.get(e["to"])
        if a and b:
            parts.append(f'<line x1="{sx(a["x"])}" y1="{sy(a["y"])}" '
                         f'x2="{sx(b["x"])}" y2="{sy(b["y"])}"/>')
    parts.append('</g>')
    # nodes, deepest first so the trunk draws on top
    for p in sorted(nodes, key=lambda p: -p["depth"]):
        r = _KIND_R.get(p["kind"], 2.0)
        color = _TIER_COLOR.get(p.get("tier", "seed"), "#8b949e")
        if p["kind"] == "trunk":
            parts.append(f'<circle cx="{sx(p["x"])}" cy="{sy(p["y"])}" r="{r}" '
                         f'fill="#c9d1d9" stroke="#f0f6fc" stroke-width="2"/>')
            parts.append(f'<text x="{sx(p["x"])}" y="{sy(p["y"]) - r - 6}" '
                         f'fill="#f0f6fc" font-size="15" font-weight="700" '
                         f'text-anchor="middle">THE PLAYER</text>')
        else:
            parts.append(f'<circle cx="{sx(p["x"])}" cy="{sy(p["y"])}" r="{r}" '
                         f'fill="{color}" opacity="0.92"/>')
    # loop labels
    for p in nodes:
        if p["kind"] == "loop":
            parts.append(f'<text x="{sx(p["x"])}" y="{sy(p["y"]) - 9}" fill="#8b949e" '
                         f'font-size="9" text-anchor="middle">'
                         f'{p["label"].split("·")[-1].strip()}</text>')
    parts.append(f'<text x="{size/2}" y="{size - 14}" fill="#6e7681" font-size="11" '
                 f'text-anchor="middle">DNA spiral · golden angle '
                 f'{payload["golden_angle_deg"]}° · {len(nodes)} nodes · '
                 f'the player is the trunk</text>')
    parts.append('</svg>')
    svg = "\n".join(parts)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "player_spiral.svg").write_text(svg, encoding="utf-8")
    return svg


def _ascii(payload, width=63, height=31):
    """A terminal-visible depiction so the spiral is real in the transcript."""
    nodes = payload["nodes"]
    xs = [p["x"] for p in nodes]
    ys = [p["y"] for p in nodes]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    grid = [[" "] * width for _ in range(height)]
    glyph = {"trunk": "@", "loop": "O", "feature": "*", "band": "+", "checkpoint": "."}
    for p in sorted(nodes, key=lambda p: p["depth"]):
        gx = int((p["x"] - min(xs)) / span * (width - 1))
        gy = int((p["y"] - min(ys)) / span * (height - 1))
        if 0 <= gx < width and 0 <= gy < height:
            grid[gy][gx] = glyph.get(p["kind"], "?")
    return "\n".join("".join(row) for row in grid)


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="The Fractal Spiral — studio as a DNA "
                                            "spiral rooted at the player")
    sub = p.add_subparsers(dest="cmd", required=True)
    pb = sub.add_parser("build", help="Compute + emit the spiral layout")
    pb.add_argument("--svg", action="store_true", help="also render player_spiral.svg")
    pb.add_argument("--sign", action="store_true", help="record ONE signature node to the graph")
    pb.add_argument("--ascii", action="store_true", help="print a terminal depiction")
    pn = sub.add_parser("neighborhood", help="Fractal neighbors of a node")
    pn.add_argument("--node", required=True)
    sub.add_parser("stats", help="Shape of the current spiral")

    args = p.parse_args(argv)
    if args.cmd == "build":
        payload = build(sign=args.sign)
        print(f"spiral built: {len(payload['nodes'])} nodes, "
              f"{len(payload['edges'])} edges, depth profile "
              f"{payload['counts_by_depth']} -> {OUT_DIR / 'spiral_layout.json'}")
        if args.svg:
            render_svg(payload)
            print(f"rendered -> {OUT_DIR / 'player_spiral.svg'}")
        if args.ascii:
            print("\n" + _ascii(payload))
    elif args.cmd == "neighborhood":
        try:
            nb = neighborhood(args.node)
        except KeyError as e:
            print(f"REFUSED: {e}")
            sys.exit(1)
        print(json.dumps(nb, indent=2))
    elif args.cmd == "stats":
        payload = build()
        print(f"golden angle: {payload['golden_angle_deg']}°   child scale: "
              f"{payload['child_scale']} (self-similar)")
        print(f"by depth: {payload['counts_by_depth']}")
        print(f"by kind : {payload['counts_by_kind']}")


if __name__ == "__main__":
    main()
