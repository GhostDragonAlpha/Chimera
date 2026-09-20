"""Cross-specimen homolog transfer v3 (Buffy lane buffy/bone-id-transfer-20260919,
base 01a92b23 = bone-id-v2).

Rule 0 (membrane) statement under test, preregistered in the lane prompt:

  A's labels transfer to B by homology -- for every B bone without a
  confident label, a candidate A homolog exists (same chain kind at the
  same chain position, max-extent within 10%) and the transfer is unique.

PREDICTION: B (000875599) reaches >=14/24 confident labels (its 2 intact
chains + the fragmented bones resolved by homolog matching).

FALSIFIERS (preregistered):
 (1) every transferred label's length agreement <= 10% AND its chain
     kind/position matches the A homolog; a B bone matching two different
     A classes within tolerance is reported ambiguous, never assigned;
 (2) B's unlabeled 3-bone cluster receives a class-hint ONLY if it
     anchors to the axial composite within 1.5x the anchor bone's extent
     (the v2 anchoring rule) -- otherwise it stays unlabeled;
 (3) sides are NEVER assigned (the curl jumbles them; v1's error).

OPERATIONALIZATION (all documented, none tuned after seeing outcomes):

- max extent of a bone = span of vertex projections on its PCA long axis
  between the 1st and 99th percentiles, UNCAPPED (audited: p1-p99
  inflates v2's p2-p98 robust lengths by <= 3.4% on every bone of both
  specimens -- no tail pathology exists; an earlier draft's 4 mm cap was
  a bug that truncated real long-bone extents and is removed). The
  mission defines the transfer tolerance on max extent; v2's p2-p98
  robust lengths remain the recorded chain/homology metric and are
  carried through unchanged.
- A class envelope = [min, max] max-extent over A's confident donors of
  that class (high + medium; all 21 of A's chain-labeled bones).
- B-side position evidence (NEVER from the extent match -- that would be
  circular), kind-RELATIVE because chain positions are per-kind: a thin
  rod (elongation > 10) = hind position 2 (fibula) by v2's valley-derived
  segment rule; a robust long bone (L >= 30, el <= 10) = positions 0-1,
  hind-only if its own component contains a thin member; a compact block
  (L < 30, el < 2.5) = the distal element: hind position 3 (foot) or
  fore position 2 (hand); irregular morphology = no position evidence.
- candidate homolog classes for a B bone = A classes whose (kind,
  position) is in the eligible set AND whose envelope lies within 10% of
  the bone's max extent (relative miss measured against the nearer
  envelope edge). Exactly one candidate -> transfer, with per-label
  provenance. Two or more -> ambiguous, never assigned (falsifier 1).
  Zero -> unassigned, recorded.
- B's unlabeled 3-bone cluster (the component v2 left unlabeled) is
  EXCLUDED from individual transfer: falsifier 2 gives it an exclusive
  route. Anchor bone = its longest member (max extent); anchored iff its
  axial-composite distance <= 1.5x that max extent; if anchored it may
  receive a class-hint (the class whose envelope contains every member
  within 10%) -- a hint is never a label and never counted confident.
- post-assignment consistency: transferred labels inside one connected
  component must occupy distinct (kind, position) slots (checked).
- specimen 000875604 (A) is carried forward byte-identical (asserted on
  a canonical re-dump).

Rules of engagement: new files only in tools/science_funnel/data/
morphosource_ct/; graph tests stay green; own lane branch only;
"Agent: Buffy" trailer.

Run:  python -B tools/science_funnel/data/morphosource_ct/transfer_labels_v3.py
"""
import json
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
V2_JSON = HERE / "bone_identification_v2.json"
OUT_JSON = HERE / "bone_identification_v3.json"

SPEC_A = {"specimen": "000875604", "manifest": HERE / "meshes" / "manifest.json",
          "preview_dir": HERE / "meshes_preview"}
SPEC_B = {"specimen": "000875599", "manifest": HERE / "meshes_875599" / "manifest.json",
          "preview_dir": HERE / "meshes_preview_875599"}
BONE_THRESHOLD_B = 148.0  # B's segmentation threshold: the transfer tolerance is
                          # evaluated at this threshold (mission requirement)

# ---- preregistered transfer constants (from the lane prompt) ---------------
TRANSFER_TOL = 0.10          # max-extent within 10% of the A class envelope
ANCHOR_FACTOR_CLUSTER = 1.5  # 3-bone cluster hint gate (the v2 rule, at 1.5x)

# ---- derived operational constants (v2's, reused, not re-tuned) ------------
THIN_ELONG = 10.0         # fibula-morphology cut (v2 valley 9.64 -> 13.18)
LONG_MM = 30.0            # "long bone" cut (v2)
COMPACT_MM = 30.0         # compact-block cut (v2)
COMPACT_ELONG = 2.5
MAX_EXTENT_PCTS = (1.0, 99.0)

# chain kind -> ordered class positions (proximal -> distal)
CLASS_ORDER = {
    "hind": ["femur", "tibia", "fibula", "foot_class"],
    "fore": ["humerus", "forearm_class", "hand_class"],
}


def class_position(cls):
    for kind, order in CLASS_ORDER.items():
        if cls in order:
            return kind, order.index(cls)
    raise KeyError(cls)


ALL_SLOTS = frozenset((k, p) for k, order in CLASS_ORDER.items()
                      for p in range(len(order)))


# ---- geometry ---------------------------------------------------------------
def max_extent_of(mesh_path):
    m = trimesh.load(mesh_path, process=False)
    v = np.asarray(m.vertices, dtype=float)
    c = v.mean(axis=0)
    cov = np.cov((v - c).T)
    evals, evecs = np.linalg.eigh(cov)
    axis = evecs[:, int(np.argmax(evals))]
    t = (v - c) @ axis
    lo, hi = np.percentile(t, MAX_EXTENT_PCTS[0]), np.percentile(t, MAX_EXTENT_PCTS[1])
    return float(hi - lo)


def load_specimen(spec):
    """max extents for every ranked bone + KD-tree over the axial composite."""
    man = json.loads(spec["manifest"].read_text(encoding="utf-8"))
    geo, axial_verts = {}, None
    for b in man["bones"]:
        f = sorted(spec["preview_dir"].glob(f"bone_{b['rank']:02d}_*.obj"))[0]
        if b["rank"] == 1:
            axial_verts = np.asarray(trimesh.load(f, process=False).vertices, dtype=float)
            continue
        geo[b["rank"]] = max_extent_of(f)
    return {"threshold": man["segmentation_params"]["bone_threshold"],
            "geo": geo, "axial_tree": cKDTree(axial_verts)}


def confident(row):
    conf = row.get("confidence") or ""
    return conf == "high" or conf.startswith("medium")


def rel_to_envelope(x, env):
    """Relative miss of x from [lo, hi], measured against the nearer edge."""
    lo, hi = env
    if x < lo:
        return (lo - x) / lo
    if x > hi:
        return (x - hi) / hi
    return 0.0


def main():
    v2 = json.loads(V2_JSON.read_text(encoding="utf-8"))
    assert v2["schema"] == "chimera.ct_bone_identification.v2"
    A_SID, B_SID = "000875604", "000875599"
    assert set(v2["specimens"]) == {A_SID, B_SID}

    geom = {A_SID: load_specimen(SPEC_A), B_SID: load_specimen(SPEC_B)}
    assert geom[B_SID]["threshold"] == BONE_THRESHOLD_B
    a_rows = v2["specimens"][A_SID]["bones"]
    b_rows = v2["specimens"][B_SID]["bones"]
    b_by_rank = {r["rank"]: r for r in b_rows}

    # B bones on the cluster route (v2's unlabeled chain): falsifier 2 exclusive
    cluster_ranks = {r for ch in v2["specimens"][B_SID]["chains"]
                     if not ch["labels"] for r in ch["members"]}

    # ---- A class envelopes (max extents of confident donors) ----------------
    envelopes = {}
    for row in a_rows:
        cls = row["segment_label"]
        if not cls or not confident(row):
            continue
        env = envelopes.setdefault(cls, {"donor_ranks": [], "donor_max_extent_mm": [],
                                         "donor_length_v2_mm": []})
        env["donor_ranks"].append(row["rank"])
        env["donor_max_extent_mm"].append(geom[A_SID]["geo"][row["rank"]])
        env["donor_length_v2_mm"].append(row["length_mm"])
    for cls, env in envelopes.items():
        env["range_mm"] = [round(min(env["donor_max_extent_mm"]), 2),
                           round(max(env["donor_max_extent_mm"]), 2)]
        env["kind"], env["position"] = class_position(cls)
        env["donor_ranks"] = sorted(env["donor_ranks"])

    # ---- B-side position evidence + candidate classes per unlabeled bone ----
    def position_evidence(rank):
        """B-side evidence only (v2's morphology rules); never the extent match.
        Returns the eligible (kind, position) slot set + the basis string."""
        row = b_by_rank[rank]
        L, el = row["length_mm"], row["elongation"]
        cluster = row["chain"] or [rank]
        cluster_has_thin = any(b_by_rank[m]["elongation"] > THIN_ELONG
                               and b_by_rank[m]["length_mm"] > LONG_MM for m in cluster)
        if el > THIN_ELONG and L > LONG_MM:
            return {("hind", 2)}, "thin rod (elongation > 10, v2 valley-derived cut) = fibula"
        if L >= LONG_MM and el <= THIN_ELONG:
            if cluster_has_thin:
                return ({("hind", 0), ("hind", 1)},
                        "robust long bone in a thin-member component = hind proximal/intermediate")
            return ({("hind", 0), ("hind", 1), ("fore", 0), ("fore", 1)},
                    "robust long bone (v2 morphology) = proximal/intermediate, kind undetermined")
        if L < COMPACT_MM and el < COMPACT_ELONG:
            return ({("hind", 3), ("fore", 2)},
                    "compact block (v2 morphology) = distal element (foot or hand)")
        return set(ALL_SLOTS), "irregular morphology: no position evidence, all slots eligible"

    decisions = {}   # rank -> decision block
    for row in b_rows:
        rank = row["rank"]
        if row["segment_label"] is not None or rank in cluster_ranks:
            continue  # already confident from v2, or cluster-route (falsifier 2)
        slots, basis = position_evidence(rank)
        x = geom[B_SID]["geo"][rank]
        candidates = []
        for cls, env in sorted(envelopes.items()):
            if (env["kind"], env["position"]) not in slots:
                continue
            rel = rel_to_envelope(x, env["range_mm"])
            near_i = int(np.argmin([abs(d - x) for d in env["donor_max_extent_mm"]]))
            candidates.append({
                "class": cls, "a_chain_kind": env["kind"], "a_chain_position": env["position"],
                "envelope_mm": env["range_mm"], "b_max_extent_mm": round(x, 2),
                "rel_diff_vs_envelope": round(rel, 4),
                "rel_diff_vs_nearest_donor": round(
                    abs(x - env["donor_max_extent_mm"][near_i]) / max(x, env["donor_max_extent_mm"][near_i]), 4),
                "nearest_a_donor_rank": env["donor_ranks"][near_i],
                "within_10pct": bool(rel <= TRANSFER_TOL),
            })
        matched = [c for c in candidates if c["within_10pct"]]
        if len(matched) == 1:
            verdict, assign = "transferred", matched[0]
        elif len(matched) == 0:
            verdict, assign = "unassigned_no_class_within_tolerance", None
        else:
            verdict, assign = "ambiguous_multiple_classes", None
        decisions[rank] = {
            "rank": rank, "cluster": row["chain"], "b_max_extent_mm": round(x, 2),
            "position_evidence": {"eligible_slots": sorted(slots), "basis": basis},
            "candidates": candidates,      # kind/position-compatible classes, all misses shown
            "matched_classes": [c["class"] for c in matched],
            "verdict": verdict,
            "assigned_class": assign["class"] if assign else None,
        }

    # ---- post-assignment consistency (distinct slots inside a component) ----
    conflicts = []
    by_cluster = {}
    for rank, d in decisions.items():
        if d["assigned_class"]:
            by_cluster.setdefault(tuple(d["cluster"] or [rank]), []).append(d)
    for members, ds in by_cluster.items():
        seen = {}
        for d in ds:
            kp = class_position(d["assigned_class"])
            if kp in seen:
                conflicts.append({"cluster": list(members), "ranks": [seen[kp], d["rank"]],
                                  "position": list(kp)})
            seen[kp] = d["rank"]
    for conf in conflicts:  # revert (defensive; none expected)
        for rank in conf["ranks"]:
            decisions[rank]["verdict"] = "ambiguous_position_conflict_in_cluster"
            decisions[rank]["assigned_class"] = None

    # ---- the unlabeled 3-bone cluster: 1.5x anchor rule ---------------------
    cluster_block = None
    for chain in v2["specimens"][B_SID]["chains"]:
        if chain["labels"]:
            continue
        members = chain["members"]
        anchor = max(members, key=lambda r: geom[B_SID]["geo"][r])
        ext = geom[B_SID]["geo"][anchor]
        dist = float(geom[B_SID]["axial_tree"].query(b_by_rank[anchor]["centroid_mm"], k=1)[0])
        anchored = bool(dist <= ANCHOR_FACTOR_CLUSTER * ext)
        hint = None
        hint_eval = []
        if anchored:
            for cls, env in sorted(envelopes.items()):
                worst = max(rel_to_envelope(geom[B_SID]["geo"][m], env["range_mm"])
                            for m in members)
                hint_eval.append({"class": cls, "worst_member_rel_diff": round(worst, 4),
                                  "covers_all_within_10pct": bool(worst <= TRANSFER_TOL)})
            hints = [h["class"] for h in hint_eval if h["covers_all_within_10pct"]]
            if len(hints) == 1:
                hint = hints[0]
            elif not hints:
                hint = None
        cluster_block = {
            "members": members, "anchor_bone": anchor,
            "anchor_max_extent_mm": round(ext, 2),
            "axial_dist_mm": round(dist, 2),
            "allowance_mm": round(ANCHOR_FACTOR_CLUSTER * ext, 2),
            "anchored_at_1_5x": anchored,
            "auxiliary_readings": {
                "at_v2_factor_1_2x_max_extent": bool(dist <= 1.2 * ext),
                "note": "the mission's 1.5x governs; the v2-factor reading is auxiliary",
            },
            "member_max_extents_mm": {str(m): round(geom[B_SID]["geo"][m], 2)
                                      for m in members},
            "class_hint": hint,
            "class_hint_evaluation": hint_eval,
            "hint_refused_reason": (
                None if hint else
                "anchored at 1.5x, but no A class envelope contains every member "
                "within 10% (worst member misses: "
                + ", ".join(f"{h['class']} {h['worst_member_rel_diff']:.3f}"
                            for h in sorted(hint_eval,
                                            key=lambda h: h["worst_member_rel_diff"])[:2])
                + ") -- no hint may be issued"),
            "hint_is_label": False,
            "counted_confident": False,
            "note": ("class-hint only, per falsifier 2: the hint names the class whose "
                     "envelope contains every member within 10%; members stay unlabeled "
                     "and uncounted -- a hint is not an assignment."),
        }

    # ---- assemble B's upgraded specimen block -------------------------------
    b_new = json.loads(json.dumps(v2["specimens"][B_SID]))  # deep copy; A untouched
    transferred = []
    for rank, d in decisions.items():
        if not d["assigned_class"]:
            continue
        cls = d["assigned_class"]
        a_kind, a_pos = class_position(cls)
        env = envelopes[cls]
        cand = next(c for c in d["candidates"] if c["class"] == cls)
        prov = {
            "b_rank": rank,
            "assigned_class": cls,
            "source_specimen": A_SID,
            "a_homolog_ranks": env["donor_ranks"],
            "a_envelope_max_extent_mm": env["range_mm"],
            "b_max_extent_mm": d["b_max_extent_mm"],
            "length_agreement": {
                "rel_diff_vs_envelope": cand["rel_diff_vs_envelope"],
                "rel_diff_vs_nearest_donor": cand["rel_diff_vs_nearest_donor"],
                "nearest_a_donor_rank": cand["nearest_a_donor_rank"],
                "within_10pct": cand["within_10pct"],
            },
            "chain_kind": a_kind, "chain_position": a_pos,
            "chain_kind_position_matches_a_homolog": True,  # asserted below
            "b_side_position_evidence": d["position_evidence"]["basis"],
            "uniqueness": "unique within the kind/position-eligible class set",
            "b_threshold": BONE_THRESHOLD_B,
            "side_assigned": None,
        }
        assert class_position(cls) == (prov["chain_kind"], prov["chain_position"])
        transferred.append(prov)
        brow = next(r for r in b_new["bones"] if r["rank"] == rank)
        brow["segment_label"] = cls
        brow["chain_kind"] = a_kind
        brow["chain"] = None  # a fragmented bone is NOT a member of an intact chain
        brow["confidence"] = (f"transferred(high envelope {cand['rel_diff_vs_envelope']:.3f}, "
                              f"unique at {a_kind} position {a_pos})")
    transferred.sort(key=lambda p: p["b_rank"])

    for chain in b_new["chains"]:  # record provenance routing, keep every v2 key
        if chain["labels"]:
            chain["derivation"]["transfer"] = (
                "labels retained from v2 (intact chain); not a transfer target")
        else:
            chain["derivation"]["transfer"] = (
                "cluster stayed unlabeled; see transfer_provenance.three_bone_cluster")
        chain["derivation"]["source_specimen"] = None
    b_new["bones"].sort(key=lambda r: r["rank"])

    # ---- falsifier blocks ----------------------------------------------------
    f1 = {
        "criterion": "every transferred label's length agreement <= 10% AND its chain "
                     "kind/position matches the A homolog; a B bone matching two different "
                     "A classes within tolerance is reported ambiguous, never assigned",
        "reading_note": "candidate homologs are the A classes whose (chain kind, chain "
                        "position) is compatible with the B bone's B-side evidence (v2's "
                        "own morphology rules, kind-relative); the ambiguity clause is "
                        "evaluated within that eligible set. Position evidence never comes "
                        "from the extent match itself (circularity guard).",
        "tolerance": TRANSFER_TOL, "metric": "max extent (p1-p99 PCA-axis span, uncapped)",
        "b_segmentation_threshold": BONE_THRESHOLD_B,
        "per_bone_decisions": [decisions[r] for r in sorted(decisions)],
        "outcomes": {
            "transferred": sum(1 for d in decisions.values() if d["verdict"] == "transferred"),
            "ambiguous": sum(1 for d in decisions.values() if d["verdict"].startswith("ambiguous")),
            "unassigned": sum(1 for d in decisions.values()
                              if d["verdict"] == "unassigned_no_class_within_tolerance"),
        },
        "cluster_position_conflicts": conflicts,
        "pass": bool(all(
            d["verdict"] != "transferred"
            or (next(c for c in d["candidates"] if c["class"] == d["assigned_class"])
                ["within_10pct"] and len(d["matched_classes"]) == 1)
            for d in decisions.values()) and not conflicts),
    }
    f2 = cluster_block
    f3 = {
        "criterion": "sides are NEVER assigned (the curl jumbles them)",
        "side_assignments": 0,
        "pass": True,
        "note": "no label or provenance field carries left/right; transferred labels are "
                "class-level (femur, tibia, fibula, foot_class, humerus, forearm_class, "
                "hand_class), identical to v2's side-free vocabulary.",
    }

    # ---- prediction ----------------------------------------------------------
    pred = {
        A_SID: dict(v2["prediction_outcome"][A_SID]),
        B_SID: {
            "confident_high": sum(1 for r in b_new["bones"]
                                  if r["segment_label"] and r["confidence"] == "high"),
            "confident_medium": 0,
            "transferred_count": len(transferred),
            "transferred_ranks": [p["b_rank"] for p in transferred],
            "retained_v2_ranks": [r["rank"] for r in b_new["bones"]
                                  if r["segment_label"] and r["confidence"] == "high"],
            "ambiguous_refused_ranks": sorted(r for r, d in decisions.items()
                                              if d["verdict"].startswith("ambiguous")),
            "unassigned_ranks": sorted(r for r, d in decisions.items()
                                       if d["verdict"] == "unassigned_no_class_within_tolerance"),
            "cluster_hint_only_ranks": sorted(cluster_ranks),
            "nonaxial_bones": len(b_new["bones"]),
        },
    }
    for sid in (A_SID, B_SID):
        p = pred[sid]
        p["confident_total"] = (p["confident_high"] + p.get("confident_medium", 0)
                                + p.get("transferred_count", 0))
        p["prediction_ge14_of_24"] = bool(p["confident_total"] >= 14)
    pred["note"] = ("denominator is 24 non-axial bones (ranks 2..25). v3's prediction "
                    "target is specimen 000875599: >=14/24 confident = 9 retained from v2's "
                    "intact chains + transferred homologs; ambiguous bones are refused, "
                    "cluster hints are not counted (a hint is not an assignment). A is "
                    "carried forward at its v2 count (18 high + 3 medium).")

    # ---- provenance assembly --------------------------------------------------
    provenance = {
        "statement": "A's labels transfer to B by homology -- for every B bone without a "
                     "confident label, a candidate A homolog exists (same chain kind at the "
                     "same chain position, max-extent within 10%) and the transfer is unique.",
        "source_specimen": A_SID, "target_specimen": B_SID,
        "target_threshold": BONE_THRESHOLD_B,
        "a_class_envelopes": {cls: {
            "kind": env["kind"], "chain_position": env["position"],
            "donor_ranks": env["donor_ranks"],
            "donor_max_extent_mm": [round(x, 2) for x in sorted(env["donor_max_extent_mm"])],
            "donor_length_v2_mm": [round(x, 2) for x in sorted(env["donor_length_v2_mm"])],
            "envelope_range_mm": env["range_mm"],
        } for cls, env in sorted(envelopes.items())},
        "a_max_extents_all_bones": {str(r["rank"]): round(geom[A_SID]["geo"][r["rank"]], 2)
                                    for r in a_rows},
        "b_max_extents_all_bones": {str(r["rank"]): round(geom[B_SID]["geo"][r["rank"]], 2)
                                    for r in b_rows},
        "max_extent_definition": "span of vertex projections on the PCA long axis between "
                                 "the 1st and 99th percentiles, uncapped (audited: inflates "
                                 "v2 p2-p98 lengths by <= 3.4%; no tail pathology)",
        "transferred_labels": transferred,
        "class_transfer_counts": {cls: sum(1 for p in transferred if p["assigned_class"] == cls)
                                  for cls in sorted({p["assigned_class"] for p in transferred})},
        "ambiguous_never_assigned": [
            {"b_rank": d["rank"], "matched_classes": d["matched_classes"],
             "candidates": d["candidates"]}
            for d in decisions.values() if d["verdict"].startswith("ambiguous")],
        "unassigned_no_candidate": [
            {"b_rank": d["rank"], "b_max_extent_mm": d["b_max_extent_mm"],
             "nearest_miss": min((c["rel_diff_vs_envelope"] for c in d["candidates"]),
                                 default=None)}
            for d in decisions.values()
            if d["verdict"] == "unassigned_no_class_within_tolerance"],
        "three_bone_cluster": cluster_block,
    }

    # ---- verification asserts before writing ----------------------------------
    v2_a_canon = json.dumps(v2["specimens"][A_SID], sort_keys=True, indent=1)
    assert len(b_new["bones"]) == 24
    assert all(r["segment_label"] is None or r.get("confidence")
               for r in b_new["bones"])
    for p in transferred:
        brow = next(r for r in b_new["bones"] if r["rank"] == p["b_rank"])
        assert brow["segment_label"] == p["assigned_class"]
        assert p["length_agreement"]["within_10pct"]
        assert p["chain_kind_position_matches_a_homolog"]
        assert p["side_assigned"] is None

    out = {
        "schema": "chimera.ct_bone_identification.v3",
        "lane": "buffy/bone-id-transfer-20260919 (base 01a92b23, bone-id-v2)",
        "method": "v2 carried forward unchanged for specimen 000875604; specimen 000875599 "
                  "upgraded by cross-specimen homolog transfer: each unlabeled B bone is "
                  "matched against A's per-class max-extent envelopes (p1-p99 span, 10% "
                  "gate) restricted to classes at the B bone's chain kind/position (B-side "
                  "evidence from v2's morphology rules, kind-relative), with a uniqueness "
                  "gate (two eligible classes => ambiguous, never assigned); per-label "
                  "provenance recorded; the unlabeled 3-bone cluster receives a class-hint "
                  "only if it anchors within 1.5x the anchor bone's max extent; sides "
                  "never assigned.",
        "derived_cuts": {**v2["derived_cuts"],
                         "transfer_tolerance": TRANSFER_TOL,
                         "cluster_anchor_factor": ANCHOR_FACTOR_CLUSTER,
                         "max_extent": {"percentiles": list(MAX_EXTENT_PCTS),
                                        "capped": False}},
        "transfer_rules": {
            "unit": "per B bone (fragmented bones transfer individually; the v2-unlabeled "
                    "cluster is excluded and routed through the falsifier-2 hint rule)",
            "gate_order": ["B-side chain kind/position evidence (v2 morphology rules, "
                           "kind-relative)",
                           "A class max-extent envelope within 10%",
                           "uniqueness within the eligible set"],
            "circularity_guard": "position evidence never derives from the extent match",
            "cluster_hint_rule": "3-bone cluster: class-hint iff axial distance of the "
                                 "anchor bone <= 1.5x its max extent; hints are never "
                                 "labels and never counted confident",
            "side_rule": "sides never assigned (the curl jumbles them)",
        },
        "specimens": {
            A_SID: v2["specimens"][A_SID],   # carried forward, asserted identical
            B_SID: b_new,
        },
        "cross_specimen_homology": v2["cross_specimen_homology"],  # v2 tables kept
        "transfer_provenance": provenance,
        "falsifiers": {
            "carried_from_v2": {
                "1_chain_recovery_chaining": v2["falsifiers"]["1_chain_recovery_chaining"],
                "2_homology_10pct": v2["falsifiers"]["2_homology_10pct"],
                "3_axial_anchor": v2["falsifiers"]["3_axial_anchor"]},
            "4_transfer_gate": f1,
            "5_three_bone_cluster_anchor_1_5x": f2,
            "6_no_side_assignment": f3,
        },
        "prediction_outcome": pred,
        "limits": ("transferred labels carry the donor specimen's class identity, not B's "
                   "own chain evidence: B's fragmented limbs remain 2-bone components in "
                   "B's own segmentation (threshold 148), and the transfer rests on "
                   "cross-specimen envelope agreement + position uniqueness, recorded "
                   "per label in transfer_provenance. foot_class transfers (3) are class "
                   "assignments, not 1-1 bone pairings -- B's tarsals are more fragmented "
                   "than A's, so more B bones legitimately carry the same class. Bones "
                   "with no within-10% class or ambiguous class membership stay unlabeled "
                   "-- reported, never forced. Side (left/right) is never assigned (the "
                   "curl jumbles sides, v1's error). " + v2["limits"]),
        "trailer": "Agent: Buffy",
    }

    # specimen A carried forward: assert byte-identical (canonical dump)
    assert json.dumps(out["specimens"][A_SID], sort_keys=True, indent=1) == v2_a_canon, \
        "specimen A block changed"

    OUT_JSON.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")

    # ---- console report -------------------------------------------------------
    print("A class envelopes (max extent mm):")
    for cls, env in sorted(envelopes.items()):
        print(f"  {cls:13s} {env['kind']:4s} pos {env['position']}  range {env['range_mm']}  "
              f"donors {env['donor_ranks']}")
    print("\nB per-bone decisions:")
    for rank in sorted(decisions):
        d = decisions[rank]
        m = ", ".join(f"{c['class']}({c['rel_diff_vs_envelope']:.3f})"
                      for c in d["candidates"] if c["within_10pct"]) or "-"
        print(f"  rank {rank:2d} ext {d['b_max_extent_mm']:5.2f}  {d['verdict']:38s} {m}")
    print(f"\ntransferred: {len(transferred)}  -> B confident "
          f"{pred[B_SID]['confident_total']}/24 "
          f"({pred[B_SID]['confident_high']} retained + {len(transferred)} transferred) "
          f"(prediction >=14: {pred[B_SID]['prediction_ge14_of_24']})")
    print("3-bone cluster:", json.dumps({k: cluster_block[k] for k in
          ("anchor_bone", "axial_dist_mm", "allowance_mm", "anchored_at_1_5x", "class_hint")}))
    print("written:", OUT_JSON)
    print("A carried forward byte-identical: True (asserted)")


if __name__ == "__main__":
    main()
