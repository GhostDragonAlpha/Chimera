"""Cross-component adjacency measurement for the matter skeleton's axial-limb pairs.

Replicates identify_bones_v2.py's surface-gap metric VERBATIM (trimesh preview
vertices, scipy cKDTree, symmetric min) and extends the gap table to the pairs
the v2/v3 lanes never measured: every pair involving rank 1 (the axial
composite, excluded by v2's loader) and the singletons (14, 16, 19).

All 300 rank pairs are measured (cherry-pick guard, receipt falsifier F6).
The touching-class cut is the law's own: JOINT_GAP_MM = 3.0
(bone_identification_v3.json derived_cuts.joint_gap_mm).

Outputs (byte-deterministic; no timestamps, sorted keys, fixed rounding):
  adjacency_table.json  -- method validation vs the 21 committed edges,
                           touching-class pairs, pre-registered pairs,
                           full singleton rows.
  candidate_bonds.json  -- cross-component touching-class pairs as
                           integrator-ready candidate bonds (data file only;
                           the committed body definition is NOT modified).

Run:  python -B tools/science_funnel/validation/axial_adjacency_20260920/measure_adjacency.py
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DATA = ROOT / "tools" / "science_funnel" / "data" / "morphosource_ct"
PREVIEW_DIR = DATA / "meshes_preview"

JOINT_GAP_MM = 3.0          # the committed law's own cut (never re-chosen)
REFINE_ABOVE_MM = 3.5       # refine touching-class pairs + small margin
LAW_RESOLUTION = 2          # 0.01 mm, the committed gap_mm resolution
REF_RESOLUTION = 3          # 0.001 mm for triangle-refined numbers

PRE_REGISTERED = [          # receipt P1-P6, fixed before the run
    (2, 1, "P1 hip A: femur 2 <-> axial composite"),
    (3, 1, "P2 hip B: femur 3 <-> axial composite"),
    (4, 1, "P3 shoulder A: humerus 4 <-> axial composite"),
    (5, 1, "P4 shoulder B: humerus 5 <-> axial composite"),
    (16, 1, "P5 singleton 16 <-> composite (epiphyseal/pelvic reading)"),
    (16, 2, "P5 singleton 16 <-> femur 2 (epiphyseal reading)"),
    (14, 1, "P6 singleton 14 <-> composite (caudal reading)"),
    (19, 1, "P6 singleton 19 <-> composite (caudal reading)"),
]

READINGS = {                       # keys are (min_rank, max_rank)
    (1, 2): "hip joint: femoral head apposed to the acetabular region of the composite pelvis mass (Hartman & Straus 1933, The Anatomy of the Rhesus Monkey)",
    (1, 3): "hip joint: femoral head apposed to the acetabular region of the composite pelvis mass (Hartman & Straus 1933)",
    (1, 4): "shoulder joint: humeral head apposed to the glenoid region of the composite scapula mass, segmentation-merged with the ribcage (Hartman & Straus 1933)",
    (1, 5): "shoulder joint: humeral head apposed to the glenoid region of the composite scapula mass (Hartman & Straus 1933)",
    (1, 16): "pelvic/iliac-region ossification apposition (epiphyseal-class block at composite z-top, pelvis x-band; Scheuer & Black 2000 for juvenile separate ossification centers)",
    (2, 16): "unfused proximal femoral epiphysis apposed to the femur end across growth-plate cartilage (Scheuer & Black 2000)",
    (1, 14): "caudal-vertebra cluster apposed to the sacrum/caudal base of the composite (positional reading: beyond composite pelvis-end bbox)",
    (1, 19): "caudal-vertebra cluster apposed to the sacrum/caudal base of the composite (positional reading: beyond composite pelvis-end bbox)",
}


def component_of(rank, v3spec):
    if rank == 1:
        return "axial_composite"
    for b in v3spec["bones"]:
        if b["rank"] == rank and b.get("chain"):
            return "%s_chain_min%02d" % (b["chain_kind"], min(b["chain"]))
    return "singleton_%02d" % rank


def preview_path(rank):
    hits = sorted(PREVIEW_DIR.glob("bone_%02d_*.obj" % rank))
    if len(hits) != 1:
        raise SystemExit("preview glob for rank %d -> %d hits" % (rank, len(hits)))
    return hits[0]


def load_meshes(ranks):
    meshes = {}
    for r in ranks:
        meshes[r] = trimesh.load(preview_path(r), process=False)
    return meshes


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vertex_gaps(meshes, pairs):
    """identify_bones_v2.py surface_gaps() verbatim + argmin provenance."""
    trees = {r: cKDTree(np.asarray(meshes[r].vertices, dtype=float)) for r in meshes}
    out = {}
    for a, b in pairs:
        ta, tb = trees[a], trees[b]
        d1, i1 = tb.query(ta.data, k=1)   # each A vertex -> nearest B vertex
        d2, i2 = ta.query(tb.data, k=1)   # each B vertex -> nearest A vertex
        if d1.min() <= d2.min():
            j = int(np.argmin(d1))
            prox = ("vertex", j, "vertex", int(i1[j]))  # (A-kind, A-idx, B-kind, B-idx)
        else:
            j = int(np.argmin(d2))
            prox = ("vertex", int(i2[j]), "vertex", j)
        out[(a, b)] = (float(min(d1.min(), d2.min())), prox)
    return out


def seg_point_dist(p, a, b):
    ab = b - a
    t = ((p - a) * ab).sum(-1) / np.clip((ab * ab).sum(-1), 1e-20, None)
    t = np.clip(t, 0.0, 1.0)
    proj = a + t[..., None] * ab
    return np.linalg.norm(p - proj, axis=-1)


def tri_point_dist(p, tri_a, tri_b, tri_c):
    """Exact point-to-triangle distance, vectorized over triangles (Ericson)."""
    ap = p - tri_a
    ab, ac = tri_b - tri_a, tri_c - tri_a
    d11 = (ab * ab).sum(-1)
    d12 = (ab * ac).sum(-1)
    d22 = (ac * ac).sum(-1)
    dp1 = (ap * ab).sum(-1)
    dp2 = (ap * ac).sum(-1)
    det = d11 * d22 - d12 * d12
    det = np.where(np.abs(det) < 1e-20, 1e-20, det)
    u = (d22 * dp1 - d12 * dp2) / det
    v = (d11 * dp2 - d12 * dp1) / det
    face_ok = (u >= 0) & (v >= 0) & (u + v <= 1)
    n = np.cross(ab, ac)
    face_d = np.abs((n * ap).sum(-1)) / np.sqrt(np.clip((n * n).sum(-1), 1e-20, None))
    edge_d = np.minimum(seg_point_dist(p, tri_a, tri_b),
                        np.minimum(seg_point_dist(p, tri_b, tri_c),
                                   seg_point_dist(p, tri_c, tri_a)))
    return np.where(face_ok, np.minimum(face_d, edge_d), edge_d)


def refine_pair(meshes, a, b):
    """Exact point-to-triangle refinement, both directions, k-guarantee loop.

    Returns (gap, point_on_a, point_on_b, guaranteed). The k-guarantee: for
    every query vertex, all triangles whose centroid lies within
    (best + max_circumradius) have been evaluated -- guaranteed only if the
    k-th centroid distance exceeds best + R_max, else k doubles (cap 1024).
    Edge-edge interior minima (neither mesh vertex involved) are outside this
    estimator; the vertex-metric law number remains the bond metric.
    """
    va = np.asarray(meshes[a].vertices, dtype=float)
    vb = np.asarray(meshes[b].vertices, dtype=float)
    fa = np.asarray(meshes[a].faces)
    fb = np.asarray(meshes[b].faces)

    def prep(v, f):
        tri = v[f]                       # (T, 3, 3)
        cen = tri.mean(axis=1)
        # max circumradius per mesh (triangle vertices are shared, global cap)
        rr = np.sqrt(((tri - cen[:, None, :]) ** 2).sum(-1)).max()
        return tri, cKDTree(cen), float(rr)

    (tri_a, tree_ca, r_a) = prep(va, fa)
    (tri_b, tree_cb, r_b) = prep(vb, fb)

    def direction(pv, tri, tree_c, r_max, tag):
        """Exact global-min point-to-triangle over every vertex of pv, with a
        k-escalation guarantee on the GLOBAL MIN: a vertex v is exempt from
        deeper search iff kth(v) - r_max >= best_global (an unevaluated
        triangle for v cannot beat best_global); non-exempt vertices get k
        quadrupled (cap n_tri, which is a full guarantee). Ties in kth/exempt
        resolution are handled by re-deriving the exempt set every round
        (best_global only decreases)."""
        n_tri = len(tree_c.data)
        k0 = 64
        k = min(k0, n_tri)
        dc, ic = tree_c.query(pv, k=k)
        ic = np.asarray(ic)
        if ic.ndim == 1:
            ic = ic[:, None]
            dc = np.asarray(dc)[:, None]
        kth = np.asarray(dc)[:, -1].copy()

        def evaluate(rows, kk_idx):
            """exact distances for vertex rows x candidate triangle columns"""
            flat_idx = kk_idx.reshape(-1)
            flat_ver = np.repeat(np.arange(len(rows)), kk_idx.shape[1])
            d_parts = []
            chunk = 1 << 21
            for s in range(0, flat_idx.size, chunk):
                vi = flat_ver[s:s + chunk]
                ti = flat_idx[s:s + chunk]
                d_parts.append(tri_point_dist(pv[rows[vi]], tri[ti, 0], tri[ti, 1], tri[ti, 2]))
            d_all = np.concatenate(d_parts)
            starts = np.flatnonzero(np.r_[True, flat_ver[1:] != flat_ver[:-1]])
            ends = np.r_[starts[1:], flat_ver.size]
            mins = np.empty(len(rows))
            argmins = np.empty(len(rows), dtype=np.int64)
            for i in range(len(rows)):
                seg = d_all[starts[i]:ends[i]]
                mins[i] = seg.min()
                argmins[i] = flat_idx[starts[i] + int(seg.argmin())]
            return mins, argmins

        rows = np.arange(len(pv))
        best_v, arg_v = evaluate(rows, ic)
        g = int(np.argmin(best_v))
        best_global, best_pair = float(best_v[g]), (int(rows[g]), int(arg_v[g]))
        it = 0
        while True:
            it += 1
            exempt = (kth - r_max) >= best_global
            active = rows[~exempt]
            if active.size == 0 or k >= n_tri:
                return best_global, best_pair, bool(active.size == 0 or k >= n_tri)
            k = min(k * 4, n_tri)
            dc2, ic2 = tree_c.query(pv[active], k=k)
            ic2 = np.asarray(ic2)
            if ic2.ndim == 1:
                ic2 = ic2[:, None]
            kth[active] = np.asarray(dc2)[:, -1]
            b2, a2 = evaluate(active, ic2)
            upd = b2 < best_v[active]
            best_v[active[upd]] = b2[upd]
            arg_v[active[upd]] = a2[upd]
            g = int(np.argmin(best_v))
            best_global, best_pair = float(best_v[g]), (int(rows[g]), int(arg_v[g]))
            print("refine %s: round %d k=%d active=%d best=%.3f" % (tag, it, k, active.size, best_global),
                  file=sys.stderr, flush=True)

    e_ab, arg_ab, g_ab = direction(va, tri_b, tree_cb, r_b, "%02d->%02d" % (a, b))  # A vertices -> B triangles
    e_ba, arg_ba, g_ba = direction(vb, tri_a, tree_ca, r_a, "%02d->%02d" % (b, a))  # B vertices -> A triangles

    gap = min(e_ab, e_ba)
    if e_ab <= e_ba:
        vi, ti = arg_ab
        p_on_a = va[vi]
        q = _closest_point_on_tri(p_on_a, tri_b[ti])
        return gap, p_on_a, q, bool(g_ab and g_ba)
    vi, ti = arg_ba
    p_on_b = vb[vi]
    q = _closest_point_on_tri(p_on_b, tri_a[ti])
    return gap, q, p_on_b, bool(g_ab and g_ba)


def _closest_point_on_tri(p, tri):
    a, b, c = tri
    ab, ac = b - a, c - a
    ap = p - a
    d1 = (ab * ap).sum()
    d2 = (ac * ap).sum()
    if d1 <= 0 and d2 <= 0:
        return a
    bp = p - b
    d3 = (ab * bp).sum()
    d4 = (ac * bp).sum()
    if d3 >= 0 and d4 <= d3:
        return b
    vc = d1 * d4 - d3 * d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        den = d1 - d3
        t = d1 / den if den != 0 else 0.0
        return a + t * ab
    cp = p - c
    d5 = (ab * cp).sum()
    d6 = (ac * cp).sum()
    if d6 >= 0 and d5 <= d6:
        return c
    vb = d5 * d2 - d1 * d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        den = d2 - d6
        t = d2 / den if den != 0 else 0.0
        return a + t * ac
    va = d3 * d6 - d5 * d4
    if va <= 0 and (d4 - d3) >= 0 and (d5 - d6) >= 0:
        den = (d4 - d3) + (d5 - d6)
        t = (d4 - d3) / den if den != 0 else 0.0
        return b + t * (c - b)
    denom = 1.0 / (va + vb + vc)
    v = vb * denom
    w = vc * denom
    return a + ab * v + ac * w


def r2(x):
    return round(x, LAW_RESOLUTION)


def r3(x):
    return round(x, REF_RESOLUTION)


def main():
    v3 = json.loads((DATA / "bone_identification_v3.json").read_text(encoding="utf-8"))
    spec = v3["specimens"]["000875604"]

    ranks = list(range(1, 26))
    meshes = load_meshes(ranks)

    comp = {r: component_of(r, spec) for r in ranks}
    labels = {1: "axial_composite"}
    for b in spec["bones"]:
        labels[b["rank"]] = b.get("segment_label")

    # committed evidence: the 21 touching edges from v3 touching_neighbors
    committed = {}
    for b in spec["bones"]:
        for tn in b.get("touching_neighbors", []):
            key = (min(b["rank"], tn["rank"]), max(b["rank"], tn["rank"]))
            committed[key] = float(tn["gap_mm"])
    if len(committed) != 21:
        raise SystemExit("expected 21 committed touching edges, got %d" % len(committed))

    all_pairs = [(a, b) for i, a in enumerate(ranks) for b in ranks[i + 1:]]
    gaps = vertex_gaps(meshes, all_pairs)

    # F1: metric transfer vs the 21 committed edges
    devs = {k: abs(gaps[k][0] - v) for k, v in committed.items()}
    max_dev = max(devs.values())
    metric_ok = max_dev <= 0.005

    # refinement set: touching class + margin, plus every pre-registered pair
    pre_map = {(min(a, b), max(a, b)): note for a, b, note in PRE_REGISTERED}
    refine_set = {k for k, (g, _) in gaps.items() if g <= REFINE_ABOVE_MM}
    refine_set |= set(pre_map)
    refined = {}
    for k in sorted(refine_set):
        a, b = k
        g, pa, pb, guar = refine_pair(meshes, a, b)
        refined[k] = (g, pa, pb, guar)

    def pair_record(a, b):
        g, prox = gaps[(a, b)]
        key = (a, b)
        rec = {
            "pair_ranks": [a, b],
            "pair_members": ["mem.bone_%02d" % a, "mem.bone_%02d" % b],
            "components": [comp[a], comp[b]],
            "labels": [labels.get(a), labels.get(b)],
            "law_gap_mm": r2(g),
            "touching_class": bool(g <= JOINT_GAP_MM),
            "committed_edge": key in committed,
            "pre_registered": pre_map.get(key),
        }
        kind_a, idx_a, kind_b, idx_b = prox
        rec["closest_law_pair"] = {
            "a_vertex_mm": [r3(x) for x in np.asarray(meshes[a].vertices, dtype=float)[idx_a]],
            "b_vertex_mm": [r3(x) for x in np.asarray(meshes[b].vertices, dtype=float)[idx_b]],
            "metric": "%s[%d]-to-%s[%d]" % (kind_a, idx_a, kind_b, idx_b),
        }
        if key in refined:
            rg, pa, pb, guar = refined[key]
            rec["refined_gap_mm"] = r3(rg)
            rec["refined_closest_points_mm"] = {
                "on_%02d" % a: [r3(x) for x in pa],
                "on_%02d" % b: [r3(x) for x in pb],
            }
            rec["refinement_guaranteed"] = guar
        reading = READINGS.get(key)
        if reading is None:
            reading = ("discovered (unpre-registered): curl apposition; anatomical joint "
                       "type NOT claimed -- flagged for anatomical review")
        rec["anatomical_reading"] = reading
        return rec

    touching = [pair_record(a, b) for (a, b) in all_pairs if gaps[(a, b)][0] <= JOINT_GAP_MM]
    pre_regs = [pair_record(min(a, b), max(a, b)) for a, b, _ in PRE_REGISTERED]

    singleton_rows = {}
    for s in (14, 16, 19):
        rows = []
        for (a, b) in all_pairs:
            if s in (a, b):
                g, _ = gaps[(a, b)]
                other = b if a == s else a
                rows.append({"partner_rank": other, "partner_component": comp[other],
                             "partner_label": labels.get(other), "law_gap_mm": r2(g)})
        rows.sort(key=lambda rr: rr["law_gap_mm"])
        singleton_rows[str(s)] = rows

    table = {
        "schema": "chimera.axial_adjacency_table.v1",
        "lane": "agent/axial-limb-adjacency-20260920",
        "base_commit": "2d585c7b",
        "inputs": {
            "preview_dir": "tools/science_funnel/data/morphosource_ct/meshes_preview",
            "mesh_sha256": {p.name: sha256_file(p) for p in sorted(PREVIEW_DIR.glob("bone_*.obj"))},
            "bone_identification_v3_sha256": sha256_file(DATA / "bone_identification_v3.json"),
            "manifest_sha256": sha256_file(DATA / "meshes" / "manifest.json"),
        },
        "method": {
            "law_metric": "identify_bones_v2.py surface_gaps() verbatim: symmetric min vertex-to-nearest-vertex on trimesh.load(preview, process=False) vertices, scipy cKDTree, float64",
            "joint_gap_mm": JOINT_GAP_MM,
            "joint_gap_source": "bone_identification_v3.json derived_cuts.joint_gap_mm (shared empirical gap valley, v2)",
            "law_resolution_mm": 0.01,
            "refinement": "exact point-to-triangle both directions over k-nearest triangle centroids with k-doubling guarantee; edge-edge interior cases not covered; law number stays the bond metric",
            "pairs_measured": len(all_pairs),
        },
        "method_validation_vs_committed_21_edges": {
            "edges_checked": len(committed),
            "max_abs_dev_mm": round(max_dev, 5),
            "pass": metric_ok,
            "per_edge_law_gap_mm": {"%02d_%02d" % k: r2(gaps[k][0]) for k in sorted(committed)},
        },
        "touching_class_pairs": touching,
        "pre_registered_pairs": pre_regs,
        "singleton_rows": singleton_rows,
        "trailer": "Agent: GLM 5.3",
    }
    (HERE / "adjacency_table.json").write_text(
        json.dumps(table, indent=1, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")

    # candidate bonds: NEW cross-component touching-class pairs only
    candidates = []
    for rec in touching:
        a, b = rec["pair_ranks"]
        if rec["committed_edge"]:
            continue
        ca, cb = rec["components"]
        cross = not (ca == cb)
        if not cross:
            continue
        candidates.append({
            "id": "bond.joint_%02d_%02d" % (a, b),
            "material": "mat.cartilage",
            "members": ["mem.bone_%02d" % a, "mem.bone_%02d" % b],
            "cure_strength": 13000000.0,
            "rest_length_mm": rec["law_gap_mm"],
            "measured_gap_mm": rec["law_gap_mm"],
            "refined_gap_mm": rec.get("refined_gap_mm"),
            "closest_points_mm": rec.get("refined_closest_points_mm"),
            "components": rec["components"],
            "anatomical_reading": rec["anatomical_reading"],
            "pre_registered": bool(rec["pre_registered"]),
            "evidence": "axial_adjacency_20260920 measured law gap %.2f mm (identify_bones_v2 metric, cut %.1f mm); receipt tools/science_funnel/validation/axial_adjacency_20260920/receipt.json" % (rec["law_gap_mm"], JOINT_GAP_MM),
        })

    bonds = {
        "schema": "chimera.matter_candidate_bonds.v1",
        "lane": "agent/axial-limb-adjacency-20260920",
        "base_commit": "2d585c7b",
        "status": "CANDIDATE -- data file for the integrator; adopting it is the integrator's act. The committed infant_skeleton.body.json is NOT modified by this lane.",
        "threshold_law": {"cut_mm": JOINT_GAP_MM,
                          "source": "bone_identification_v3.json derived_cuts.joint_gap_mm (v2 shared gap valley)"},
        "bond_law_source": "matter_skeleton_import.py bond_law (cartilage, cure 13 MPa Yamada 1970, rest_length = measured gap) -- reused, not re-authored",
        "candidate_count": len(candidates),
        "bonds": candidates,
        "trailer": "Agent: GLM 5.3",
    }
    (HERE / "candidate_bonds.json").write_text(
        json.dumps(bonds, indent=1, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")

    print("pairs measured: %d" % len(all_pairs))
    print("method_validation_vs_committed_21_edges: max_abs_dev=%.5f mm pass=%s" % (max_dev, metric_ok))
    print("touching_class pairs (incl. 21 committed): %d" % len(touching))
    print("candidate cross-component bonds: %d" % len(candidates))
    for rec in pre_regs:
        print("pre-registered %s -> law gap %.2f mm, touching=%s" %
              (rec["pre_registered"], rec["law_gap_mm"], rec["touching_class"]))
    return 0 if metric_ok else 1


if __name__ == "__main__":
    sys.exit(main())
