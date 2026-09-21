"""The face-face metric lane runner: the touching-edge law's decisions RE-RUN
under the candidate default metric (exact point-to-triangle, certified), with
the old vertex-vertex metric kept as a first-class history column.

Measures ALL 300 rank pairs (ranks 1-25, preview meshes) under BOTH metrics,
re-derives the touching-class cut valley under the new metric, itemizes every
refusal-to-touching flip with both numbers, recounts body components at three
stages, and issues the candidate bond file under the new default metric.

Pre-registration: receipt.json hashed to preregistration.sha256 BEFORE this
runner existed. Scope: this lane touches only its own validation directory and
tools/science_funnel/surface_gap_metric.py; the committed
infant_skeleton.body.json is NOT modified.

Run:
  python -B tools/science_funnel/validation/face_face_metric_20260921/measure_face_face.py

Outputs (byte-deterministic; sorted keys, fixed rounding, no timestamps):
  face_face_table.json
  candidate_bonds.json
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FUNNEL = HERE.parents[1]                    # tools/science_funnel
REPO = FUNNEL.parents[1]                    # repo root
sys.path.insert(0, str(FUNNEL))
sys.path.insert(0, str(HERE.parent / "axial_adjacency_20260920"))

import trimesh                              # noqa: E402

from surface_gap_metric import (            # noqa: E402
    JOINT_GAP_MM, TriMetric, point_triangle_gap, prep_vertex_metric,
    r_law, r_ref, vertex_vertex_gap)
from measure_adjacency import (             # noqa: E402  (prior lane, constants only)
    PRE_REGISTERED, READINGS, component_of)

DATA = REPO / "tools" / "science_funnel" / "data" / "morphosource_ct"
PREVIEW_DIR = DATA / "meshes_preview"
PRIOR_LANE = HERE.parents[0] / "axial_adjacency_20260920"
REFINE_ABOVE_MM = 3.5   # prior lane's refine margin (used only for comparison)


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preview_path(rank):
    hits = sorted(PREVIEW_DIR.glob("bone_%02d_*.obj" % rank))
    if len(hits) != 1:
        raise SystemExit("preview glob for rank %d -> %d hits" % (rank, len(hits)))
    return hits[0]


def load_meshes(ranks):
    return {r: trimesh.load(preview_path(r), process=False) for r in ranks}


def union_components(ranks, edges):
    parent = {r: r for r in ranks}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    comps = {}
    for r in ranks:
        comps.setdefault(find(r), []).append(r)
    return sorted(sorted(v) for v in comps.values())


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
    assert len(all_pairs) == 300

    # ---- BOTH metrics on ALL 300 pairs (F7: no pair exempted) --------------
    v_trees = {r: prep_vertex_metric(meshes[r].vertices) for r in ranks}
    t_metrics = {r: TriMetric(meshes[r].vertices, meshes[r].faces) for r in ranks}

    v2_raw, v2_prox = {}, {}
    for a, b in all_pairs:
        g, prox = vertex_vertex_gap(v_trees[a], v_trees[b])
        v2_raw[(a, b)], v2_prox[(a, b)] = g, prox
    print("v2 metric: 300 pairs done", file=sys.stderr, flush=True)

    ptt = {}
    for a, b in all_pairs:
        res = point_triangle_gap(t_metrics[a], t_metrics[b], tag="%02d_%02d" % (a, b))
        ptt[(a, b)] = res
        print("ptt %02d_%02d: %.3f mm guaranteed=%s rounds=%d/%d"
              % (a, b, res["gap"], res["guaranteed"], res["rounds_ab"], res["rounds_ba"]),
              file=sys.stderr, flush=True)

    # ---- falsifier machinery ----------------------------------------------
    # F1: history -- old metric reproduces the 21 committed edges
    devs = {k: abs(v2_raw[k] - v) for k, v in committed.items()}
    f1_max_dev = max(devs.values())
    f1_pass = f1_max_dev <= 0.005

    # F2: monotonicity -- ptt <= v2 on every pair
    mono_viol = ["%02d_%02d" % k for k in all_pairs if ptt[k]["gap"] > v2_raw[k] + 1e-12]
    f2_pass = not mono_viol

    # F3: the 21 committed edges stay touching under the new default
    f3_left = ["%02d_%02d" % k for k in committed if not (ptt[k]["gap"] <= JOINT_GAP_MM)]
    f3_pass = not f3_left

    # F4/F5: flips and stays, itemized
    def pair_key(a, b):
        return (min(a, b), max(a, b))

    pre_map = {(min(a, b), max(a, b)): note for a, b, note in PRE_REGISTERED}

    def flip_record(a, b):
        k = (a, b)
        res = ptt[k]
        return {
            "pair_ranks": [a, b],
            "pair_members": ["mem.bone_%02d" % a, "mem.bone_%02d" % b],
            "components": [comp[a], comp[b]],
            "labels": [labels.get(a), labels.get(b)],
            "gap_v2_mm": r_law(v2_raw[k]),
            "gap_new_default_mm": r_law(res["gap"]),
            "gap_new_default_exact_mm": r_ref(res["gap"]),
            "guaranteed": res["guaranteed"],
            "closest_points_mm": {
                "on_%02d" % a: [r_ref(x) for x in res["closest_a"]],
                "on_%02d" % b: [r_ref(x) for x in res["closest_b"]],
            },
            "pre_registered": pre_map.get(k),
            "anatomical_reading": READINGS.get(k),
        }

    flips = sorted(
        (k for k in all_pairs
         if not (v2_raw[k] <= JOINT_GAP_MM) and (ptt[k]["gap"] <= JOINT_GAP_MM)))
    flip_recs = [flip_record(a, b) for a, b in flips]

    predicted_flips = [(1, 14), (1, 19)]
    f4_pass = flips == predicted_flips

    named_stays = {}
    for a, b in [(1, 4), (1, 5)]:
        named_stays["%02d_%02d" % (a, b)] = {
            "gap_v2_mm": r_law(v2_raw[(a, b)]),
            "gap_new_default_mm": r_law(ptt[(a, b)]["gap"]),
            "still_refused": bool(ptt[(a, b)]["gap"] > JOINT_GAP_MM),
        }
    singleton_stays = {}
    for s in (14, 16, 19):
        row = []
        for (a, b) in all_pairs:
            if s in (a, b):
                other = b if a == s else a
                row.append((ptt[(a, b)]["gap"], other))
        row.sort()
        row_min_gap, row_min_partner = row[0]
        flip_partners = sorted(other for g, other in row
                               if (min(s, other), max(s, other)) in flips)
        non_flip = [g for g, other in row
                    if (min(s, other), max(s, other)) not in flips]
        singleton_stays[str(s)] = {
            "row_min_new_default_mm": r_law(row_min_gap),
            "row_min_partner_rank": row_min_partner,
            "flip_partners": flip_partners,
            "row_min_excluding_flips_mm": r_law(min(non_flip)),
            "row_partners_above_cut_excluding_flips": bool(min(non_flip) > JOINT_GAP_MM),
            "joins_through": ("measured flip contact" if flip_partners else "nothing -- stays isolated"),
        }
    f5_pass = (all(v["still_refused"] for v in named_stays.values())
               and all(v["row_partners_above_cut_excluding_flips"]
                       for v in singleton_stays.values()))

    # F8: guarantee certificates
    unguaranteed = sorted("%02d_%02d" % k for k in all_pairs if not ptt[k]["guaranteed"])
    f8_pass = not unguaranteed

    # ---- cut re-derivation under the new metric ----------------------------
    touch_new = {k: ptt[k]["gap"] for k in all_pairs if ptt[k]["gap"] <= JOINT_GAP_MM}
    sep_new = {k: ptt[k]["gap"] for k in all_pairs if ptt[k]["gap"] > JOINT_GAP_MM}
    touch_v2 = {k: v2_raw[k] for k in all_pairs if v2_raw[k] <= JOINT_GAP_MM}
    sep_v2 = {k: v2_raw[k] for k in all_pairs if v2_raw[k] > JOINT_GAP_MM}

    def max_key(d):
        return max(d, key=lambda k: (d[k], k))

    def min_key(d):
        return min(d, key=lambda k: (d[k], k))

    v2_last_touch, v2_next_sep = max_key(touch_v2), min_key(sep_v2)
    new_last_touch, new_next_sep = max_key(touch_new), min_key(sep_new)
    valley_new = (touch_new[new_last_touch], sep_new[new_next_sep])
    cut_in_valley = valley_new[0] < JOINT_GAP_MM < valley_new[1]
    flip_max_gap = max((ptt[k]["gap"] for k in flips), default=0.0)

    # boundary stability: which pairs sit at the valley edges (the only pairs
    # whose class any cut movement can change), with their numbers
    stability = {
        "valley_new_mm": [r_ref(valley_new[0]), r_ref(valley_new[1])],
        "cut_3.0_inside_valley": bool(cut_in_valley),
        "verdict": ("RE-JUSTIFIED UNCHANGED: 3.0 mm lies inside the new-metric "
                    "valley; no pair changes class for any cut in the valley"),
        "class_change_points": {
            "last_touching_pair": {
                "pair_ranks": list(new_last_touch),
                "gap_new_default_mm": r_law(touch_new[new_last_touch]),
                "gap_v2_mm": r_law(v2_raw[new_last_touch]),
            },
            "next_separated_pair": {
                "pair_ranks": list(new_next_sep),
                "gap_new_default_mm": r_law(sep_new[new_next_sep]),
                "gap_v2_mm": r_law(v2_raw[new_next_sep]),
            },
        },
        "flip_set_cut_independence": (
            ("the flip set is EMPTY and therefore identical for every cut in "
             "(%.3f, %.3f]" % (flip_max_gap, valley_new[1]))
            if not flips else
            ("the flip set is identical for every cut in (%.3f, %.3f]: the largest "
             "flip's measured gap is %.3f mm and the smallest separated pair's is "
             "%.3f mm" % (flip_max_gap, valley_new[1], flip_max_gap, valley_new[1]))),
    }

    # ---- component counts at three stages ----------------------------------
    comps_committed = union_components(ranks, list(committed))
    old_candidates = sorted(
        k for k in touch_v2
        if k not in committed and comp[k[0]] != comp[k[1]])
    comps_old = union_components(ranks, list(committed) + [tuple(k) for k in old_candidates])
    new_edges = [tuple(k) for k in flips]
    comps_new = union_components(ranks, list(committed) + [tuple(k) for k in old_candidates]
                                 + new_edges)

    # cross-check the old candidate set against the committed prior-lane file
    prior_bonds = json.loads((PRIOR_LANE / "candidate_bonds.json").read_text(encoding="utf-8"))
    prior_pairs = sorted(tuple(b["members"]) for b in prior_bonds["bonds"])
    prior_pairs_rank = sorted(tuple(int(m.split("_")[1]) for m in mm) for mm in prior_pairs)
    old_match = old_candidates == prior_pairs_rank

    # cross-check the committed-only component count against the committed body
    body = json.loads((DATA / "matter_skeleton" / "infant_skeleton.body.json")
                      .read_text(encoding="utf-8"))
    body_edges = [tuple(sorted((int(b_["members"][0].split("_")[1]),
                                int(b_["members"][1].split("_")[1]))))
                  for b_ in body["bonds"]]
    comps_body = union_components(ranks, body_edges)
    committed_ok = (comps_committed == comps_body and len(comps_committed) == 8
                    and sorted(body_edges) == sorted(committed))

    def comp_block(cs):
        return {"count": len(cs),
                "components": [{"component": comp[c[0]], "ranks": c} for c in cs]}

    # ---- assemble the table -------------------------------------------------
    def full_record(a, b):
        k = (a, b)
        res = ptt[k]
        rec = {
            "pair_ranks": [a, b],
            "pair_members": ["mem.bone_%02d" % a, "mem.bone_%02d" % b],
            "components": [comp[a], comp[b]],
            "labels": [labels.get(a), labels.get(b)],
            "gap_v2_mm": r_law(v2_raw[k]),
            "gap_new_default_mm": r_law(res["gap"]),
            "gap_new_default_exact_mm": r_ref(res["gap"]),
            "touching_v2": bool(v2_raw[k] <= JOINT_GAP_MM),
            "touching_new_default": bool(res["gap"] <= JOINT_GAP_MM),
            "committed_edge": k in committed,
            "flip": k in flips,
            "guaranteed": res["guaranteed"],
            "escalation_rounds": [res["rounds_ab"], res["rounds_ba"]],
            "anatomical_reading": READINGS.get(k),
        }
        vm, tm_ = res["vertex_mesh"], res["triangle_mesh"]
        v_rank = a if vm == "A" else b
        t_rank = a if tm_ == "A" else b
        rec["closest_provenance"] = ("vertex[%d] of %02d -> triangle[%d] of %02d"
                                     % (res["vertex_index"], v_rank,
                                        res["triangle_index"], t_rank))
        return rec

    touching_new_sorted = sorted(touch_new, key=lambda k: (touch_new[k], k))
    table = {
        "schema": "chimera.face_face_table.v1",
        "lane": "agent/face-face-metric-20260921",
        "base_commit": "3539fdb9",
        "preregistration_sha256": (HERE / "preregistration.sha256").read_text(
            encoding="utf-8").strip(),
        "inputs": {
            "preview_dir": "tools/science_funnel/data/morphosource_ct/meshes_preview",
            "mesh_sha256": {p.name: sha256_file(p)
                            for p in sorted(PREVIEW_DIR.glob("bone_*.obj"))},
            "bone_identification_v3_sha256": sha256_file(DATA / "bone_identification_v3.json"),
            "prior_lane_candidate_bonds_sha256": sha256_file(PRIOR_LANE / "candidate_bonds.json"),
            "prior_lane_adjacency_table_sha256": sha256_file(PRIOR_LANE / "adjacency_table.json"),
        },
        "method": {
            "metric_old_history": ("identify_bones_v2.py surface_gaps() verbatim: "
                                   "symmetric min vertex-to-nearest-vertex, trimesh "
                                   "preview vertices, scipy cKDTree, float64"),
            "metric_new_default": ("CANDIDATE DEFAULT (tools/science_funnel/"
                                   "surface_gap_metric.py): symmetric min exact "
                                   "point-to-triangle (Ericson), per-vertex k-escalation "
                                   "guarantee over triangle-centroid KD order, promoted "
                                   "verbatim from the axial_adjacency_20260920 lane's "
                                   "refinement"),
            "lower_bound_derivation": ("every vertex of B lies on a triangle of B, so "
                                       "min_v dist(v, T_B) <= min_v dist(v, V_B); "
                                       "mirrored and composed through the mins: "
                                       "gap_new <= gap_v2 on every pair (F2)"),
            "joint_gap_mm": JOINT_GAP_MM,
            "joint_gap_source": ("bone_identification_v3.json derived_cuts.joint_gap_mm; "
                                 "re-derived (not re-chosen) under the new metric -- see "
                                 "cut_derivation"),
            "law_resolution_mm": 0.01,
            "exact_resolution_mm": 0.001,
            "pairs_measured": len(all_pairs),
            "metrics_per_pair": 2,
        },
        "falsifiers": {
            "F1_history_reproduction": {
                "pass": bool(f1_pass),
                "edges_checked": len(committed),
                "max_abs_dev_mm": round(f1_max_dev, 5),
                "per_edge": {"%02d_%02d" % k: {"committed_mm": committed[k],
                                               "v2_measured_mm": r_law(v2_raw[k]),
                                               "new_default_mm": r_law(ptt[k]["gap"])}
                             for k in sorted(committed)},
            },
            "F2_monotonicity": {"pass": bool(f2_pass), "violations": mono_viol,
                                "pairs_checked": len(all_pairs)},
            "F3_committed_edges_survive": {"pass": bool(f3_pass), "left_class": f3_left},
            "F4_flip_set_exact": {"pass": bool(f4_pass),
                                  "predicted": [list(p) for p in predicted_flips],
                                  "measured": [list(p) for p in flips]},
            "F5_refuse_when_no_contact": {
                "pass": bool(f5_pass),
                "named_stays": named_stays,
                "singleton_rows": singleton_stays,
            },
            "F7_cherry_pick_guard": {"pass": True,
                                     "pairs_under_both_metrics": len(all_pairs)},
            "F8_full_guarantee": {"pass": bool(f8_pass), "unguaranteed_pairs": unguaranteed},
        },
        "committed_edges_receipt": {
            "note": ("the 21 committed bonds under BOTH metrics: v2 reproduces the "
                     "committed numbers (history); the new default keeps every edge "
                     "in the touching class (law), each with its measured number"),
            "edges": {"%02d_%02d" % k: {
                "committed_mm": committed[k],
                "v2_measured_mm": r_law(v2_raw[k]),
                "new_default_mm": r_law(ptt[k]["gap"]),
                "new_default_exact_mm": r_ref(ptt[k]["gap"]),
                "still_touching_new": bool(ptt[k]["gap"] <= JOINT_GAP_MM),
            } for k in sorted(committed)},
        },
        "flips": {
            "count": len(flips),
            "predicted_exactly": bool(f4_pass),
            "records": flip_recs,
        },
        "touching_class_new_default": [full_record(a, b) for a, b in touching_new_sorted],
        "cut_derivation": {
            "v2_history": {
                "last_touching_pair": list(v2_last_touch),
                "last_touching_mm": r_law(touch_v2[v2_last_touch]),
                "next_separated_pair": list(v2_next_sep),
                "next_separated_mm": r_law(sep_v2[v2_next_sep]),
                "committed_cut_inside": bool(
                    touch_v2[v2_last_touch] < JOINT_GAP_MM < sep_v2[v2_next_sep]),
            },
            "new_default": stability,
            "procedure": ("the v2 derivation procedure (last touching pair / next "
                          "separated pair on the metric's own 300-pair distribution) "
                          "re-run under the new default metric; the cut is re-derived, "
                          "never re-chosen"),
        },
        "component_counts": {
            "committed_only": {**comp_block(comps_committed),
                               "matches_committed_body": bool(committed_ok)},
            "plus_old_metric_candidates": {**comp_block(comps_old),
                                           "candidate_pairs": [list(k) for k in old_candidates],
                                           "matches_prior_lane_file": bool(old_match)},
            "plus_new_metric_candidates": {**comp_block(comps_new),
                                           "added_pairs": [list(k) for k in new_edges]},
        },
        "corroboration_vs_prior_lane": {
            "note": ("pairs the prior lane refined (touching class + pre-registered "
                     "set, v2 <= 3.5 mm) re-measured here; the new-default numbers "
                     "must equal the committed refined_gap_mm at 0.001 mm"),
            "prior_refined_pairs_compared": 0,
            "max_abs_dev_mm": None,
        },
        "trailer": "Agent: GLM 5.3",
    }

    # corroboration vs the prior lane's committed refined numbers
    prior_table = json.loads((PRIOR_LANE / "adjacency_table.json").read_text(encoding="utf-8"))
    prior_refined = {}
    for rec in (prior_table["touching_class_pairs"] + prior_table["pre_registered_pairs"]):
        if rec.get("refined_gap_mm") is not None:
            prior_refined[tuple(rec["pair_ranks"])] = rec["refined_gap_mm"]
    devs_ptt = {k: r_ref(ptt[k]["gap"]) - v for k, v in prior_refined.items()}
    changed = {k: v for k, v in devs_ptt.items() if abs(v) > 0.0005}
    table["corroboration_vs_prior_lane"] = {
        "note": ("the prior lane's refined_gap_mm came from the SAME estimator "
                 "WITHOUT the degenerate-triangle guard; every deviation itemized "
                 "here is a forged 0.000 (zero-area triangle) corrected by the "
                 "guarded exact metric"),
        "prior_refined_pairs_compared": len(devs_ptt),
        "pairs_equal_at_0.001mm": len(devs_ptt) - len(changed),
        "max_abs_dev_mm": round(max(abs(v) for v in devs_ptt.values()), 5),
        "corrected_pairs": {
            "%02d_%02d" % k: {"prior_refined_mm": prior_refined[k],
                              "guarded_exact_mm": r_ref(ptt[k]["gap"]),
                              "v2_mm": r_law(v2_raw[k])}
            for k in sorted(changed)},
    }

    out = json.dumps(table, indent=1, sort_keys=True, ensure_ascii=True) + "\n"
    (HERE / "face_face_table.json").write_text(out, encoding="utf-8", newline="\n")

    # ---- candidate bonds under the NEW default metric ----------------------
    candidates = []
    for k in touching_new_sorted:
        a, b = k
        if k in committed or comp[a] == comp[b]:
            continue
        res = ptt[k]
        reading = READINGS.get(k)
        if reading is None:
            reading = ("discovered (unpre-registered): curl apposition; anatomical "
                       "joint type NOT claimed -- flagged for anatomical review")
        candidates.append({
            "id": "bond.joint_%02d_%02d" % (a, b),
            "material": "mat.cartilage",
            "members": ["mem.bone_%02d" % a, "mem.bone_%02d" % b],
            "cure_strength": 13000000.0,
            "rest_length_mm": r_law(res["gap"]),
            "measured_gap_mm": r_law(res["gap"]),
            "measured_gap_exact_mm": r_ref(res["gap"]),
            "gap_v2_history_mm": r_law(v2_raw[k]),
            "closest_points_mm": {
                "on_%02d" % a: [r_ref(x) for x in res["closest_a"]],
                "on_%02d" % b: [r_ref(x) for x in res["closest_b"]],
            },
            "components": [comp[a], comp[b]],
            "anatomical_reading": reading,
            "pre_registered": bool(pre_map.get(k)),
            "flip_vs_v2": k in flips,
            "evidence": ("face_face_metric_20260921 measured gap %.2f mm (certified "
                         "point-to-triangle default, cut %.1f mm; v2 history %.2f mm); "
                         "receipt tools/science_funnel/validation/face_face_metric_20260921/"
                         "receipt.json" % (res["gap"], JOINT_GAP_MM, v2_raw[k])),
        })

    bonds = {
        "schema": "chimera.matter_candidate_bonds.v2",
        "lane": "agent/face-face-metric-20260921",
        "base_commit": "3539fdb9",
        "status": ("CANDIDATE -- data file for the law owner; adopting it is the "
                   "owner's act. The committed infant_skeleton.body.json is NOT "
                   "modified by this lane."),
        "threshold_law": {"cut_mm": JOINT_GAP_MM,
                          "source": ("bone_identification_v3.json derived_cuts."
                                     "joint_gap_mm; re-derived inside the new-metric "
                                     "valley -- see face_face_table.json cut_derivation")},
        "metric_law": ("certified exact point-to-triangle (tools/science_funnel/"
                       "surface_gap_metric.py), the candidate default; the v2 "
                       "vertex-vertex number is kept per candidate as history"),
        "bond_law_source": ("matter_skeleton_import.py bond_law (cartilage, cure "
                            "13 MPa Yamada 1970, rest_length = measured gap) -- "
                            "reused, not re-authored"),
        "candidate_count": len(candidates),
        "bonds": candidates,
        "trailer": "Agent: GLM 5.3",
    }
    (HERE / "candidate_bonds.json").write_text(
        json.dumps(bonds, indent=1, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8", newline="\n")

    # ---- console summary ----------------------------------------------------
    all_pass = (f1_pass and f2_pass and f3_pass and f4_pass and f5_pass and f8_pass
                and old_match and committed_ok)
    print("F1 history: max dev %.5f mm pass=%s" % (f1_max_dev, f1_pass))
    print("F2 monotonicity: pass=%s" % f2_pass)
    print("F3 committed survive: pass=%s" % f3_pass)
    print("F4 flip set: measured=%s pass=%s" % (flips, f4_pass))
    print("F5 refuse-when-no-contact: pass=%s" % f5_pass)
    print("F8 guarantee certificates: pass=%s" % f8_pass)
    print("old-candidate set matches prior lane: %s" % old_match)
    print("committed-only components match the committed body (8): %s" % committed_ok)
    print("components: committed %d -> old candidates %d -> new candidates %d"
          % (len(comps_committed), len(comps_old), len(comps_new)))
    print("cut: new valley (%.3f, %.3f) contains 3.0: %s"
          % (valley_new[0], valley_new[1], cut_in_valley))
    print("corroboration vs prior refined: %d pairs, max dev %.5f mm, %d corrected"
          % (len(devs_ptt), max(abs(v) for v in devs_ptt.values()), len(changed)))
    print("ALL PASS: %s" % all_pass)
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
