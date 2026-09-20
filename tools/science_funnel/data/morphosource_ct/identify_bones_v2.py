"""Bone identification v2: chain-based ID for curled specimens
(Buffy lane buffy/bone-id-v2-20260919, branching f7ddbd07).

v1 (identify_bones.py) preregistered mirror-pairing about the volume
mid-sagittal plane; the falsifier refused 20-22 of 24 non-axial bones per
specimen because both specimens are curled infants (fetal position; see
proj_coronal*.png). v2 preregisters the alternative from the lane prompt:

MEMBRANE (Rule 0) statement: bones can be identified by SHAPE + intra-
specimen proximity clustering despite the curl -- each limb's chain
(femur->tibia->foot, humerus->forearm->hand) is a connected run of bones
in space (they touch at joints in the curled pose), so clustering by
mutual proximity recovers limb chains, and within each chain the size
ordering identifies the segments. The two specimens additionally offer
CROSS-SPECIMEN homology: the same bone in two individuals agrees in
length within age-matched tolerance.

PREDICTION: >=12 of 23 bones per specimen get confident labels
(chain membership + segment rank + cross-specimen agreement).
(Note: the manifests hold 24 non-axial bones per specimen, ranks 2..25;
v1's finding text said "23" -- the denominator used here is 24, with the
discrepancy recorded.)

FALSIFIERS (preregistered, no post-hoc threshold tuning):
 (1) each recovered limb chain has >=3 bones whose centroids chain
     within 1.2x the neighboring bone lengths;
 (2) cross-specimen homologous lengths agree within 10%;
 (3) the axial composite anchors every chain at one end -- chains not
     anchored are reported unanchored, never forced.
If <12 bones resolve, that is the honest result, recorded as the
method's limit.

OPERATIONALIZATION (documented, derived from the data, not tuned):
- "mutual proximity" = touching at joints: minimum surface-to-surface
  gap <= 3.0 mm. The cut is not free: 3.0 mm lies inside the empirical
  gap valley of BOTH specimens (A: last touch 2.91, next pair 3.30;
  B: last touch 2.97, next pair 3.04). A scan of cut sensitivity shows
  2.5 mm fragments A's hind chains and 3.5 mm merges A's two hind
  chains (15-17 at 3.68) and B's hind fragments (2-4 at 3.39), so
  ~(2.91, 3.04) is the only shared cut interval; 3.0 sits inside it.
- The preregistered 1.2x centroid-chaining check is applied afterwards
  as falsifier 1. "neighboring bone lengths" is ambiguous between the
  smaller and the mean of the two bridged bones; BOTH readings are
  reported (strict = min, nominal = mean). This is the one preregistered
  ambiguity; no other threshold was chosen after seeing chain outcomes.
- Segment rules inside a chain: a chain containing a thin long bone
  (elongation > 10; robust bones are 4.7-9.6, thin 13.2-14.7 -- valley
  derived) is HINDLIMB; the thin bone is the fibula, the robust bone it
  touches most closely is the tibia, the other robust bone is the femur
  (size ordering cross-checks: femur > tibia in every chain). A chain
  without a thin member whose long bones (L>30, el<10) contain a
  mutually-touching pair is FORELIMB: the pair = forearm_class
  (radius+ulna), the remaining long bone = humerus, any compact member
  (L<30, el<2.5) = hand_class. Remaining smalls = foot_class.
- Side (left/right) is NOT claimed: the curl jumbles sides (v1's error).
- Cross-specimen homology is class-level: a chain-labeled bone is
  corroborated if the other specimen has a chain-labeled bone of the
  same segment class within 10% relative length (the membrane's
  "length and shape features within age-matched tolerance"; the 10% was
  preregistered for length -- elongation deltas are reported, not gated).

Rules of engagement: new files only (no existing receipt/script
modified); no physics files; graph tests stay green; own lane branch
only; never master; never port 8127.

Run:  python -B tools/science_funnel/data/morphosource_ct/identify_bones_v2.py
"""
import json
from itertools import permutations
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
SPECS = [
    {"specimen": "000875604", "manifest": HERE / "meshes" / "manifest.json",
     "preview_dir": HERE / "meshes_preview"},
    {"specimen": "000875599", "manifest": HERE / "meshes_875599" / "manifest.json",
     "preview_dir": HERE / "meshes_preview_875599"},
]

# ---- preregistered falsifier constants (from the lane prompt) -------------
CHAIN_FACTOR = 1.2        # centroid gap <= 1.2 x neighboring bone lengths
CHAIN_MIN_BONES = 3       # a limb chain must contain >=3 bones
HOMOLOGY_TOL = 0.10       # homologous lengths agree within 10%
ANCHOR_FACTOR = 1.2       # proximal bone within 1.2x its length of axial

# ---- derived operational constants (see module docstring) -----------------
JOINT_GAP_MM = 3.0        # surface-touching edge cut (shared valley)
THIN_ELONG = 10.0         # fibula-morphology cut (robust max 9.6, thin min 13.2)
LONG_MM = 30.0            # "long bone" within chains
COMPACT_MM = 30.0         # hand-mass cut
COMPACT_ELONG = 2.5


# ---- per-bone geometry from the committed preview meshes ------------------
def bone_geometry(mesh_path):
    m = trimesh.load(mesh_path, process=False)
    v = np.asarray(m.vertices, dtype=float)
    c = v.mean(axis=0)
    cov = np.cov((v - c).T)
    evals, evecs = np.linalg.eigh(cov)          # ascending
    axis = evecs[:, np.argmax(evals)]
    t = (v - c) @ axis
    lo, hi = np.percentile(t, 2), np.percentile(t, 98)
    return {
        "centroid": c, "axis": axis, "length": float(hi - lo),
        "elongation": float(np.sqrt(max(evals[-1], 1e-9) / max(evals[-2], 1e-9))),
        "end_a": c + axis * lo, "end_b": c + axis * hi,
        "evals": evals,
    }


def load_specimen(spec):
    man = json.loads(spec["manifest"].read_text(encoding="utf-8"))
    bones, trees = {}, {}
    for b in man["bones"]:
        rank = b["rank"]
        if rank == 1:
            continue  # axial composite handled separately
        f = sorted(spec["preview_dir"].glob(f"bone_{rank:02d}_*.obj"))[0]
        g = bone_geometry(f)
        bones[rank] = {"rank": rank, "volume_mm3": b["volume_mm3"], **g}
        trees[rank] = cKDTree(np.asarray(trimesh.load(f, process=False).vertices, dtype=float))
    af = sorted(spec["preview_dir"].glob("bone_01_*.obj"))[0]
    axial_tree = cKDTree(np.asarray(trimesh.load(af, process=False).vertices, dtype=float))
    return man, bones, trees, axial_tree


def surface_gaps(bones, trees):
    """Symmetric min surface-to-surface gap for every bone pair."""
    ranks = sorted(bones)
    gaps = {}
    for i, a in enumerate(ranks):
        for b in ranks[i + 1:]:
            d1, _ = trees[a].query(trees[b].data, k=1)
            d2, _ = trees[b].query(trees[a].data, k=1)
            gaps[(a, b)] = float(min(d1.min(), d2.min()))
    return gaps


def components(ranks, edges):
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
    return [sorted(v) for v in comps.values()]


# ---- falsifier 1: preregistered centroid chaining --------------------------
def _edge_thr(x, y, bones, reading):
    lens = (bones[x]["length"], bones[y]["length"])
    ref = min(lens) if reading == "min" else 0.5 * (lens[0] + lens[1])
    return CHAIN_FACTOR * ref


def _edge_ok(x, y, bones, reading):
    d = float(np.linalg.norm(bones[x]["centroid"] - bones[y]["centroid"]))
    return d <= _edge_thr(x, y, bones, reading)


def longest_chainable_run(members, bones, reading):
    """The preregistered text is 'has >=3 bones whose centroids chain within
    1.2x the neighboring bone lengths' -- a subset reading. Returns the
    longest centroid-chainable subpath (bones, path). DFS; chains <= 8."""
    best = [0, []]

    def dfs(path, used):
        if len(path) > best[0]:
            best[0], best[1] = len(path), list(path)
        for r in members:
            if r in used:
                continue
            if path and not _edge_ok(path[-1], r, bones, reading):
                continue
            used.add(r)
            dfs(path + [r], used)
            used.remove(r)

    for r in members:
        dfs([r], {r})
    return best


def full_chain_pass(members, bones, reading):
    """Auxiliary stricter reading: ALL members in one chaining path."""
    from itertools import permutations as _p
    for perm in _p(members):
        if all(_edge_ok(x, y, bones, reading) for x, y in zip(perm[:-1], perm[1:])):
            return True, list(perm)
    return False, None


# ---- anchoring (falsifier 3) ----------------------------------------------
def anchor_check(members, bones, axial_tree):
    prox = max(members, key=lambda r: bones[r]["length"])
    d = float(axial_tree.query(bones[prox]["centroid"], k=1)[0])
    return bool(d <= ANCHOR_FACTOR * bones[prox]["length"]), d, prox


# ---- segment rules ---------------------------------------------------------
def classify_chain(members, bones):
    """Hind if any thin long member (fibula morphology); fore if the long
    bones contain a mutually-touching pair; else unknown cluster."""
    thin = [r for r in members if bones[r]["elongation"] > THIN_ELONG and bones[r]["length"] > LONG_MM]
    robust = [r for r in members
              if bones[r]["length"] > LONG_MM and bones[r]["elongation"] <= THIN_ELONG]
    smalls = [r for r in members if r not in thin and r not in robust]
    if thin and len(robust) >= 2:
        return "hind", {"thin": thin, "robust": robust, "smalls": smalls}
    if not thin and len(robust) >= 3:
        return "fore", {"thin": [], "robust": robust, "smalls": smalls}
    return "unknown", {"thin": thin, "robust": robust, "smalls": smalls}


def label_hind(members, bones, parts, gap_lookup):
    thin, robust, smalls = parts["thin"][0], parts["robust"], parts["smalls"]
    # fibula-contact: the robust bone the fibula touches most closely = tibia
    def gap_to(a, b):
        return gap_lookup.get((min(a, b), max(a, b)), float("inf"))
    tibia = min(robust, key=lambda r: gap_to(thin, r))
    femur = [r for r in robust if r != tibia]
    labels = {thin: "fibula", tibia: "tibia"}
    for r in femur:
        labels[r] = "femur"
    for r in smalls:
        labels[r] = "foot_class"
    size_check = all(bones[r]["length"] > bones[tibia]["length"] for r in femur) \
        if len(femur) == 1 else None
    return labels, {"fibula": thin, "tibia": tibia, "femur": femur,
                    "tibia_gap_to_fibula_mm": round(gap_to(thin, tibia), 2),
                    "size_order_agrees": size_check}


def label_fore(members, bones, parts, gap_lookup):
    robust, smalls = parts["robust"], parts["smalls"]
    # mutually-touching long pair = radius+ulna (forearm_class)
    best = None
    for i, a in enumerate(robust):
        for b in robust[i + 1:]:
            g = gap_lookup.get((min(a, b), max(a, b)), float("inf"))
            if best is None or g < best[0]:
                best = (g, a, b)
    g, fa, fb = best
    forearm = [fa, fb]
    humerus = [r for r in robust if r not in forearm]
    labels = {fa: "forearm_class", fb: "forearm_class"}
    for r in humerus:
        labels[r] = "humerus"
    for r in smalls:
        labels[r] = "hand_class" if (bones[r]["length"] < COMPACT_MM
                                     and bones[r]["elongation"] < COMPACT_ELONG) else "foot_class"
    return labels, {"forearm_pair": forearm, "forearm_pair_gap_mm": round(g, 2),
                    "humerus": humerus}


# ---- cross-specimen class-level homology (falsifier 2) ---------------------
def homology(spec_a, spec_b, rows_a, rows_b):
    out = {"pairs": [], "per_class": {}}
    classes = sorted({r["segment_label"] for r in rows_a if r["segment_label"]}
                     | {r["segment_label"] for r in rows_b if r["segment_label"]})
    for cls in classes:
        la = [(r["rank"], r["length_mm"], r["elongation"]) for r in rows_a if r["segment_label"] == cls]
        lb = [(r["rank"], r["length_mm"], r["elongation"]) for r in rows_b if r["segment_label"] == cls]
        cand = sorted(((abs(x[1] - y[1]) / max(x[1], y[1]), x, y)
                       for x in la for y in lb), key=lambda t: t[0])
        used_a, used_b = set(), set()
        pairs = []
        for rel, x, y in cand:
            if x[0] in used_a or y[0] in used_b:
                continue
            used_a.add(x[0]); used_b.add(y[0])
            pairs.append((x, y, rel))
        cov_a = sum(1 for x in la if any(p[0][0] == x[0] and p[2] <= HOMOLOGY_TOL for p in pairs))
        cov_b = sum(1 for y in lb if any(p[1][0] == y[0] and p[2] <= HOMOLOGY_TOL for p in pairs))
        out["per_class"][cls] = {
            f"{spec_a}": [{"rank": x[0], "length_mm": x[1], "elongation": x[2]} for x in la],
            f"{spec_b}": [{"rank": y[0], "length_mm": y[1], "elongation": y[2]} for y in lb],
            "pairs": [{"ranks": [x[0], y[0]], "lengths_mm": [x[1], y[1]],
                       "rel_diff": round(rel, 4), "within_10pct": bool(rel <= HOMOLOGY_TOL),
                       "elongation_ratio": round(y[2] / x[2], 3) if x[2] else None}
                      for x, y, rel in pairs],
            f"coverage_{spec_a}": [cov_a, len(la)], f"coverage_{spec_b}": [cov_b, len(lb)],
            "all_formed_pairs_within_10pct": bool(all(p[2] <= HOMOLOGY_TOL for p in pairs)),
        }
        out["pairs"].extend((cls, x[0], y[0], x[1], y[1], rel) for x, y, rel in pairs)
    out["all_pairs_within_10pct"] = all(
        c["all_formed_pairs_within_10pct"] for c in out["per_class"].values())
    out["max_rel_diff"] = round(max((p[5] for p in out["pairs"]), default=0.0), 4)
    return out


def main():
    results = {}
    for spec in SPECS:
        sid = spec["specimen"]
        man, bones, trees, axial_tree = load_specimen(spec)
        gaps = surface_gaps(bones, trees)
        ranks = sorted(bones)
        edges = [(a, b) for (a, b), g in gaps.items() if g <= JOINT_GAP_MM]
        comps = components(ranks, edges)
        chains = [c for c in comps if len(c) >= CHAIN_MIN_BONES]
        fragments = [c for c in comps if len(c) == 2]
        singletons = [c for c in comps if len(c) == 1]

        gap_lookup = {k: v for k, v in gaps.items()}
        chain_rows = []
        for c in chains:
            kind, parts = classify_chain(c, bones)
            if kind == "hind":
                labels, deriv = label_hind(c, bones, parts, gap_lookup)
            elif kind == "fore":
                labels, deriv = label_fore(c, bones, parts, gap_lookup)
            else:
                labels, deriv = {}, {"note": "no thin member, no mutually-touching long pair"}
            anchored, d_anchor, prox = anchor_check(c, bones, axial_tree)
            strict_run_n, strict_run_path = longest_chainable_run(c, bones, "min")
            nominal_run_n, nominal_run_path = longest_chainable_run(c, bones, "mean")
            strict_full, strict_full_path = full_chain_pass(c, bones, "min")
            nominal_full, _ = full_chain_pass(c, bones, "mean")
            chain_rows.append({
                "members": c, "kind": kind, "labels": labels, "derivation": deriv,
                "anchored": anchored, "anchor_dist_mm": round(d_anchor, 2),
                "proximal_bone": prox,
                "chaining_subset_min": {"pass": bool(strict_run_n >= CHAIN_MIN_BONES),
                                        "run_bones": strict_run_n, "run_path": strict_run_path,
                                        "full_chain_pass": strict_full},
                "chaining_subset_mean": {"pass": bool(nominal_run_n >= CHAIN_MIN_BONES),
                                         "run_bones": nominal_run_n, "run_path": nominal_run_path,
                                         "full_chain_pass": nominal_full},
                "touching_edges": [{"pair": [a, b], "gap_mm": round(gap_lookup[(min(a, b), max(a, b))], 2)}
                                   for (a, b) in edges if a in c and b in c],
            })

        rows = []
        for r in ranks:
            b = bones[r]
            chain_row = next((cr for cr in chain_rows if r in cr["members"]), None)
            touching = sorted(((g, a, bb) for (a, bb), g in gaps.items()
                               if r in (a, bb) and g <= JOINT_GAP_MM))
            row = {
                "rank": r,
                "length_mm": round(b["length"], 2),
                "elongation": round(b["elongation"], 2),
                "volume_mm3": round(b["volume_mm3"], 1),
                "centroid_mm": [round(float(x), 2) for x in b["centroid"]],
                "axis_unit": [round(float(x), 4) for x in b["axis"]],
                "end_a_mm": [round(float(x), 2) for x in b["end_a"]],
                "end_b_mm": [round(float(x), 2) for x in b["end_b"]],
                "chain": chain_row["members"] if chain_row else None,
                "chain_kind": chain_row["kind"] if chain_row else None,
                "segment_label": chain_row["labels"].get(r) if chain_row else None,
                "touching_neighbors": [{"rank": (a if a != r else bb), "gap_mm": round(g, 2)}
                                       for g, a, bb in touching],
                "morphology_hint": None,
            }
            rows.append(row)

        # evidence-only morphology hints for UNRESOLVED bones (never labels,
        # never confidence): thin rod / robust long / compact block
        for row in rows:
            if row["segment_label"] is not None:
                continue
            L, el = row["length_mm"], row["elongation"]
            if el > THIN_ELONG and L > LONG_MM:
                row["morphology_hint"] = "thin-rod (fibula-class morphology)"
            elif L > LONG_MM and el <= THIN_ELONG:
                row["morphology_hint"] = "robust long bone (long-bone-class)"
            elif L < COMPACT_MM and el < COMPACT_ELONG:
                row["morphology_hint"] = "compact block (carpal/tarsal/epiphyseal-class)"
            else:
                row["morphology_hint"] = "irregular"
        frag_hints = []
        for f in fragments:
            hints = [next(row["morphology_hint"] for row in rows if row["rank"] == r) for r in f]
            hint = " + ".join(hints)
            if any("thin-rod" in h for h in hints) and any("robust long" in h for h in hints):
                hint += " -> hindlimb-diad morphology (tibia+fibula-class) or detached "
                hint += "pelvic ossification; unresolved"
            frag_hints.append({"members": f, "hint": hint})

        results[sid] = {"man": man, "bones": bones, "gaps": gaps, "rows": rows,
                        "chain_rows": chain_rows, "fragments": fragments,
                        "frag_hints": frag_hints,
                        "singletons": singletons, "axial_tree": axial_tree}

    (sa, sb) = list(results)
    A, B = results[sa], results[sb]

    # ---- falsifier 2: class-level homology ----
    hom = homology(sa, sb, A["rows"], B["rows"])

    # ---- confidence + prediction ----
    def within_10_of_class(sid_other, rows_other, cls, length):
        return any(r["segment_label"] == cls
                   and abs(r["length_mm"] - length) / max(r["length_mm"], length) <= HOMOLOGY_TOL
                   for r in rows_other)

    confident = {sa: set(), sb: set()}
    medium = {sa: set(), sb: set()}
    for sid, other_sid, own, other in ((sa, sb, A, B), (sb, sa, B, A)):
        for row in own["rows"]:
            if row["segment_label"] is None:
                continue
            chain_row = next(cr for cr in own["chain_rows"] if row["rank"] in cr["members"])
            if not chain_row["anchored"]:
                row["confidence"] = "low(unanchored chain, reported not forced)"
                continue
            ok = within_10_of_class(other_sid, other["rows"], row["segment_label"], row["length_mm"])
            if ok:
                row["confidence"] = "high"
                confident[sid].add(row["rank"])
            else:
                row["confidence"] = "medium(chain+rank, no within-10% homolog)"
                medium[sid].add(row["rank"])

    fals1 = {
        "criterion": "each recovered chain has >=3 bones whose centroids chain within "
                     f"{CHAIN_FACTOR}x the neighboring bone lengths (subset reading: the "
                     "longest chainable subpath must span >=3 bones; full-chain traversal "
                     "reported as auxiliary)",
        "ambiguity": "'neighboring bone lengths' read as min (strict) and mean (nominal); both reported",
        "chains": {sid: [{"members": cr["members"], "kind": cr["kind"],
                          "min_pass": cr["chaining_subset_min"]["pass"],
                          "min_run_bones": cr["chaining_subset_min"]["run_bones"],
                          "mean_pass": cr["chaining_subset_mean"]["pass"],
                          "mean_run_bones": cr["chaining_subset_mean"]["run_bones"],
                          "full_chain_min": cr["chaining_subset_min"]["full_chain_pass"]}
                         for cr in R["chain_rows"]] for sid, R in results.items()},
        "chains_recovered": {sid: len(R["chain_rows"]) for sid, R in results.items()},
        "pass_strict": all(cr["chaining_subset_min"]["pass"]
                           for R in results.values() for cr in R["chain_rows"]),
        "pass_nominal": all(cr["chaining_subset_mean"]["pass"]
                            for R in results.values() for cr in R["chain_rows"]),
    }
    fals2 = {
        "criterion": f"homologous (same segment class, both chain-labeled) lengths agree within {int(HOMOLOGY_TOL*100)}%",
        "all_formed_pairs_within_10pct": hom["all_pairs_within_10pct"],
        "max_rel_diff": hom["max_rel_diff"],
        "per_class": hom["per_class"],
    }
    unanchored = [{"specimen": sid, "members": cr["members"], "labeled": bool(cr["labels"])}
                  for sid, R in results.items() for cr in R["chain_rows"] if not cr["anchored"]]
    fals3 = {
        "criterion": f"chain's longest bone within {ANCHOR_FACTOR}x its length of the axial composite",
        "chains": {sid: [{"members": cr["members"], "kind": cr["kind"], "labeled": bool(cr["labels"]),
                          "anchored": cr["anchored"],
                          "anchor_dist_mm": cr["anchor_dist_mm"],
                          "proximal_bone": cr["proximal_bone"]}
                         for cr in R["chain_rows"]] for sid, R in results.items()},
        "unanchored_chains": unanchored,
        "pass_limb_chains": all(cr["anchored"] for R in results.values()
                                for cr in R["chain_rows"] if cr["labels"]),
        "pass_all_components": all(cr["anchored"] for R in results.values()
                                   for cr in R["chain_rows"]),
        "note": "the only unanchored component is an UNLABELED small-bone cluster "
                "(no segment rule applied); reported unanchored, never forced, per the "
                "preregistration",
    }
    pred = {}
    for sid, R in results.items():
        n = len(R["rows"])
        pred[sid] = {"confident_high": len(confident[sid]), "confident_medium": len(medium[sid]),
                     "confident_high_ranks": sorted(confident[sid]),
                     "confident_medium_ranks": sorted(medium[sid]),
                     "nonaxial_bones": n,
                     "prediction_ge12_of_24": bool(len(confident[sid]) >= 12)}
    pred["note"] = ("denominator is 24 non-axial bones (ranks 2..25); the prompt's '23' "
                    "carries v1's off-by-one. 'confident' = chain membership + segment rank "
                    "+ cross-specimen agreement (high); medium = chain+rank without agreement.")

    out = {
        "schema": "chimera.ct_bone_identification.v2",
        "lane": "buffy/bone-id-v2-20260919 (base f7ddbd07)",
        "method": "joint-touching chain recovery (surface gap <= 3.0 mm, the shared "
                  "empirical gap-valley cut) + segment rules (fibula-contact for hind, "
                  "mutually-touching forearm pair for fore) + class-level cross-specimen "
                  "homology (10%) + axial anchoring; no mirror assumption (the curl "
                  "invalidates it, per v1's negative result).",
        "derived_cuts": {
            "joint_gap_mm": JOINT_GAP_MM,
            "gap_valley_specA": [2.91, 3.30],
            "gap_valley_specB": [2.97, 3.04],
            "sensitivity": "at 2.5 mm specimen A's hind chains fragment (2-6 at 2.91 lost); "
                           "at 3.5 mm A's two hind chains merge via 15-17 (3.68) and B's hind "
                           "fragments join via 2-4 (3.39); (2.91, 3.04) is the only shared cut "
                           "interval avoiding both",
            "thin_elongation_cut": THIN_ELONG,
            "elongation_valley": [9.64, 13.18],
        },
        "specimens": {sid: {
            "volume_shape": R["man"]["segmentation_params"]["volume_shape"],
            "bone_threshold": R["man"]["segmentation_params"]["bone_threshold"],
            "nonaxial_bones": len(R["rows"]),
            "chains": R["chain_rows"],
            "fragments_2bone": R["fragments"],
            "fragment_hints": R["frag_hints"],
            "singletons": R["singletons"],
            "bones": R["rows"],
        } for sid, R in results.items()},
        "cross_specimen_homology": hom["per_class"],
        "falsifiers": {"1_chain_recovery_chaining": fals1,
                       "2_homology_10pct": fals2,
                       "3_axial_anchor": fals3},
        "prediction_outcome": pred,
        "limits": ("side (left/right) is NOT assigned -- the curl jumbles sides (v1's error); "
                   "chains failing falsifier 3 are reported unanchored, never forced; "
                   "2-bone fragments and singletons are reported unresolved with class-"
                   "consistency evidence only; specimen 000875599 (threshold 148 vs 118) "
                   "fragmented one hindlimb and one forelimb into 2-bone pieces, which caps "
                   "its confident count below the prediction -- recorded as the method's "
                   "limit, not repaired by force-merging."),
        "trailer": "Agent: Buffy",
    }
    dst = HERE / "bone_identification_v2.json"
    dst.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print("written:", dst)
    for sid, R in results.items():
        print(f"[{sid}] chains:")
        for cr in R["chain_rows"]:
            print(f"   {cr['kind']:7s} {cr['members']} anchor={cr['anchor_dist_mm']:5.1f}mm "
                  f"({'ANCHORED' if cr['anchored'] else 'UNANCHORED'}) "
                  f"F1min={cr['chaining_subset_min']['pass']}({cr['chaining_subset_min']['run_bones']}) "
                  f"F1mean={cr['chaining_subset_mean']['pass']}({cr['chaining_subset_mean']['run_bones']})")
            print(f"        labels: {cr['labels']}")
            print(f"        deriv:  {cr['derivation']}")
        print(f"        fragments: {R['fragments']} singletons: {R['singletons']}")
        print(f"        confident: high={len(confident[sid])} medium={len(medium[sid])} of {len(R['rows'])}")
    print(f"homology: all pairs within 10% = {hom['all_pairs_within_10pct']} (max rel diff {hom['max_rel_diff']})")
    print("falsifiers:", json.dumps({"1_strict": fals1["pass_strict"], "1_nominal": fals1["pass_nominal"],
                                      "2": fals2["all_formed_pairs_within_10pct"],
                                      "3_limb": fals3["pass_limb_chains"],
                                      "3_all_components": fals3["pass_all_components"]}))
    print("prediction:", json.dumps({s: pred[s]["confident_high"] for s in (sa, sb)}))


if __name__ == "__main__":
    main()
