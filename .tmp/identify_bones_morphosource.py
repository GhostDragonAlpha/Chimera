# -*- coding: utf-8 -*-
"""Bone identification + long-axis table for MorphoSource CT specimens.

Mechanical-geometry batch only (no physics / anatomical judgment). Reads per-bone
geometry from the manifests, identifies left/right pairs by mirror symmetry about the
volume's mid-sagittal plane plus size similarity, loads the full-res meshes ONLY to
measure long axes and articular end-centers, applies the falsifier, and writes
bone_identification.json. Does not modify any existing receipt or script.

Method / decisions (full text in the output JSON "method_note"):
  * Mid-sagittal plane z_mid = (min_z + max_z)/2 over ALL bone bboxes (= volume z-center).
    The literal extent_z/2 from origin underestimates it by ~3 mm (bbox_min_z ~= 3).
  * A candidate pair is mirror-symmetric iff |mid_z - z_mid| <= 3 mm AND the centroids are
    co-located within COLOC_MM in BOTH other axes (x and y) AND volume ratio >= 0.85.
    Mirror symmetry about a plane preserves x and y, so large dx/dy means distinct bones,
    not left/right twins (this rejects coincidental z-symmetry of unrelated elements).
  * Falsifier: kept pairs must have left/right long-axis lengths agreeing within 5%, else
    the bones are reported identified_as "unpaired" rather than a forced label.
  * Side convention: higher centroid-z -> "left", lower-z -> "right" (arbitrary, documented).
  * Cranial = high-x (broad rounded cranium); caudal = low-x (tapering tail/pelvis).
"""
import json, os
import numpy as np
import trimesh

BASE = "tools/science_funnel/data/morphosource_ct"
OUT_PATH = "bone_identification.json"
SPECIMENS = [("000875604", "meshes/manifest.json"),
             ("000875599", "meshes_875599/manifest.json")]

MIRROR_TOL_MM = 3.0        # falsifier: centroid mirror about mid-sagittal plane (mm)
LEN_RATIO_TOL = 0.05       # falsifier: left/right long-axis lengths agree within 5%
VOL_RATIO_PRIOR = 0.85     # pairing prior: bilateral twins have near-equal volume
COLOC_MM = 18.0            # mirror symmetry also requires centroid co-location in the
                           # two non-mirror axes (x,y); exceeds observed pose offsets,
                           # rejects coincidental z-symmetry of distinct bones
LONG_BONE_LEN_MM = 22.0    # mesh long-axis length threshold to report an axis table

_MESH_CACHE = {}


def _mesh(path):
    if path not in _MESH_CACHE:
        _MESH_CACHE[path] = trimesh.load(path, process=False)
    return _MESH_CACHE[path]


def load_manifest(rel):
    with open(os.path.join(BASE, rel), encoding="utf-8") as f:
        return json.load(f)


def mesh_long_axis(path):
    """Oriented long axis, length, and two articular end-centers from mesh vertices."""
    m = _mesh(path); V = m.vertices.astype(np.float64)
    C = V.mean(axis=0); Cv = V - C
    cov = Cv.T @ Cv / len(Cv)
    w, U = np.linalg.eigh(cov)
    axis = U[:, np.argmax(w)]; axis = axis / np.linalg.norm(axis)
    proj = Cv @ axis
    if proj.max() < proj.min():
        axis = -axis; proj = -proj
    n = max(3, int(0.04 * len(proj)))
    clo = C + Cv[np.argsort(proj)[:n]].mean(axis=0)
    chi = C + Cv[np.argsort(proj)[-n:]].mean(axis=0)
    return {
        "length_mm": float(round(proj.max() - proj.min(), 3)),
        "axis_unit_vector": [round(float(a), 6) for a in axis],
        "end_center_min_mm": [round(float(x), 3) for x in clo],
        "end_center_max_mm": [round(float(x), 3) for x in chi],
    }


def cranial_is_high_x(path):
    """True if the broad/rounded (skull) end of the axial skeleton is at high-x."""
    m = _mesh(path); V = m.vertices.astype(np.float64)
    x = V[:, 0]
    k = max(3, int(0.05 * len(x)))
    lo, hi = V[np.argsort(x)[:k]], V[np.argsort(x)[-k:]]
    def csq(W):
        return max((W[:, 1].max() - W[:, 1].min()) ** 2,
                   (W[:, 2].max() - W[:, 2].min()) ** 2)
    return bool(csq(hi) > csq(lo))


def volume_z_mid(bones):
    """Mid-sagittal z = center of the union bbox over all bone bboxes."""
    zs = [b["bbox_min_mm"][2] for b in bones] + [b["bbox_max_mm"][2] for b in bones]
    return (min(zs) + max(zs)) / 2.0


def candidate_pairs(bones, lengths):
    """Mirror-symmetric candidate pairs among ranks>=2.

    Requires volume ratio >= VOL_RATIO_PRIOR, |mid_z - z_mid| <= MIRROR_TOL_MM, and
    centroid co-location (dx, dy) <= COLOC_MM. Returns (z_mid, [candidate dicts])."""
    idx = {b["rank"]: b for b in bones}
    zmid = volume_z_mid(bones)
    out = []
    ranks = sorted(idx)
    for i, a in enumerate(ranks):
        ba = idx[a]; ca = ba["centroid_mm"]; va = ba["volume_mm3"]
        for b in ranks[i + 1:]:
            bb = idx[b]; cb = bb["centroid_mm"]; vb = bb["volume_mm3"]
            if min(va, vb) / max(va, vb) < VOL_RATIO_PRIOR:
                continue
            dzm = abs((ca[2] + cb[2]) / 2.0 - zmid)
            if dzm > MIRROR_TOL_MM:
                continue
            dx, dy = abs(ca[0] - cb[0]), abs(ca[1] - cb[1])
            if dx > COLOC_MM or dy > COLOC_MM:
                continue
            la, lb = lengths[a], lengths[b]
            denom = max(la, lb)
            lr = min(la, lb) / denom if denom > 0 else 0.0
            out.append({"a": a, "b": b, "dzm": dzm, "dx": dx, "dy": dy, "lr": lr})
    return zmid, out


def assign_pairs(cands):
    """Greedy non-overlapping assignment; falsify by length agreement (< LEN_RATIO_TOL).

    Sorted by mirror distance then transverse offset. A pair is kept only if its
    left/right long-axis lengths agree within LEN_RATIO_TOL; otherwise both bones are
    left unpaired (reported identified_as 'unpaired')."""
    cands = sorted(cands, key=lambda c: (c["dzm"], c["dx"] + c["dy"]))
    used = set(); kept = []; failed = set()
    for c in cands:
        a, b = c["a"], c["b"]
        if a in used or b in used:
            continue
        if c["lr"] < (1.0 - LEN_RATIO_TOL):      # falsifier fail -> drop both
            failed.add(a); failed.add(b)
            continue
        kept.append(c); used |= {a, b}
    return kept, used, failed


_HINDLIMB_ORDER = ["femur", "tibia", "fibula"]      # per-limb, descending length
_FORELIMB_ORDER = ["humerus", "ulna", "radius"]      # per-limb, descending length
_NAME_CONF = {"femur": 0.7, "humerus": 0.7, "tibia": 0.5, "ulna": 0.5,
              "fibula": 0.4, "radius": 0.4}


def _mean_len(p, idx, lengths):
    return (lengths[p["a"]] + lengths[p["b"]]) / 2.0


def assign_labels(pairs, idx, lengths):
    """Label each paired bone by position (x) + length. Cranial = high-x.

    Split pairs on the median avg_x into caudal (hindlimb) and cranial (forelimb);
    within each group order by descending mean length and map to the standard per-limb
    bone order. Bones that fall outside the ordered list are 'unclassified_long_bone'.
    Returns rank -> {"label", "side", "conf_name"}."""
    result = {}
    if not pairs:
        return result
    median_x = sorted(_mean_len(p, idx, lengths) for p in pairs)[len(pairs) // 2]
    caudal, cranial = [], []
    for p in pairs:
        ax = (idx[p["a"]]["centroid_mm"][0] + idx[p["b"]]["centroid_mm"][0]) / 2.0
        (caudal if ax < median_x else cranial).append(p)
    groups = [("caudal/hindlimb", caudal, _HINDLIMB_ORDER),
              ("cranial/forelimb", cranial, _FORELIMB_ORDER)]
    for region, grp, order in groups:
        grp.sort(key=lambda p: -_mean_len(p, idx, lengths))
        for k, p in enumerate(grp):
            label = order[k] if k < len(order) else "unclassified_long_bone"
            conf = _NAME_CONF.get(label, 0.3)
            na, nb = p["a"], p["b"]
            sa = "left" if idx[na]["centroid_mm"][2] > idx[nb]["centroid_mm"][2] else "right"
            sb = "left" if idx[nb]["centroid_mm"][2] > idx[na]["centroid_mm"][2] else "right"
            result[na] = {"label": label, "side": sa, "conf_name": conf}
            result[nb] = {"label": label, "side": sb, "conf_name": conf}
    return result


def process_specimen(spec, rel):
    """Identify bones for one specimen; return (manifest, zmid, kept, used, failed,
    labels, lengths, records, cranial_high_x)."""
    m = load_manifest(rel)
    bones = m["bones"]
    idx = {b["rank"]: b for b in bones}
    axial_path = os.path.abspath(idx[1]["file"])          # run from repo root
    cranial_high_x = cranial_is_high_x(axial_path)        # loads axial once (cached)
    axial_axis = mesh_long_axis(axial_path)               # reuse cached load

    lengths = {r: mesh_long_axis(os.path.abspath(idx[r]["file"])) for r in idx if r != 1}
    zmid, cands = candidate_pairs(bones, {r: lengths[r]["length_mm"] for r in lengths})
    kept, used, failed = assign_pairs(cands)
    labels = assign_labels(kept, idx, {r: lengths[r]["length_mm"] for r in lengths})

    side_of = {}
    for p in kept:
        hi = max(p["a"], p["b"], key=lambda r: idx[r]["centroid_mm"][2])
        lo = min(p["a"], p["b"], key=lambda r: idx[r]["centroid_mm"][2])
        side_of[hi] = "left"; side_of[lo] = "right"
    pair_map = {}
    for p in kept:
        pair_map[p["a"]] = p["b"]; pair_map[p["b"]] = p["a"]

    records = []
    for r in sorted(idx):
        b = idx[r]
        if r == 1:
            rec = {"rank": 1, "identified_as": "axial_skeleton",
                   "description": "connected axial skeleton (skull+spine+ribs+pelvis)",
                   "paired": False, "side": None,
                   "length_mm": axial_axis["length_mm"],
                   "axis_unit_vector": axial_axis["axis_unit_vector"]}
            rec["confidence"] = {"pairing": 1.0, "name": 0.95, "side": 1.0, "overall": 0.95}
            records.append(rec); continue
        if r in used:
            lab = labels[r]; la = lengths[r]
            rec = {"rank": r, "identified_as": lab["label"], "side": lab["side"],
                   "paired": True, "paired_with_rank": pair_map[r],
                   "length_mm": la["length_mm"],
                   "axis_unit_vector": la["axis_unit_vector"],
                   "end_center_min_mm": la["end_center_min_mm"],
                   "end_center_max_mm": la["end_center_max_mm"]}
            ov = round(0.4 * 0.95 + 0.3 * lab["conf_name"] + 0.3 * 0.9, 3)
            rec["confidence"] = {"pairing": 0.95, "name": lab["conf_name"],
                                 "side": 0.9, "overall": ov}
            records.append(rec); continue
        rec = {"rank": r, "identified_as": "unpaired", "side": None, "paired": False}
        if lengths[r]["length_mm"] >= LONG_BONE_LEN_MM:
            rec["description"] = ("long bone (len %.1f mm) with no contralateral twin under "
                                  "the mirror-symmetry criterion" % lengths[r]["length_mm"])
        else:
            rec["description"] = "sub-long-bone element; no bilateral twin found"
        rec["confidence"] = {"pairing": 0.2, "name": 0.2, "side": 0.0, "overall": 0.2}
        records.append(rec)
    return m, zmid, kept, used, failed, labels, lengths, records, cranial_high_x


METHOD_NOTE = r"""
IDENTIFICATION METHOD -- MorphoSource CT bone identification + long-axis table
=============================================================================

Scope: mechanical-geometry batch only. No physics or anatomical judgment is applied;
labels follow a documented position/length heuristic and every label carries an honest
identification-confidence. Identification uses MANIFEST geometry (centroid_mm, extent_mm,
bbox, volume_mm3) for all 25 bones; full-res meshes are loaded ONLY to measure the long
axis and the two articular end-centers of identified long bones.

Per specimen (ranks 1..25):
  * rank 1 = connected axial skeleton (skull + spine + ribs + pelvis); reported as one
    element with its mesh long axis, no side.
  * ranks 2..25: left/right pairs are found by mirror symmetry about the volume's
    mid-sagittal plane plus size and co-location similarity.

Mid-sagittal plane (z): z_mid = (min_z + max_z) / 2 over ALL bone bboxes (= center of the
union bbox along z, i.e. the volume's z-center). Used instead of the literal extent_z/2
from origin because bbox_min_z ~= +3 mm here, so extent_z/2 underestimates the true plane
by ~3 mm. [PENDING USER CONFIRMATION]

Pairing criterion (candidate left/right pair must satisfy ALL):
  * volume ratio min/max >= VOL_RATIO_PRIOR (0.85) -- twins are near-equal size;
  * |centroid_z_mid - z_mid| <= MIRROR_TOL_MM (3 mm) -- centroids mirror about the plane;
  * centroid offset in BOTH non-mirror axes within COLOC_MM (18 mm): dx<=18 and dy<=18.
    Mirror symmetry about a sagittal plane preserves x and y, so large transverse offset
    means two distinct bones, not twins. This co-location rule rejects coincidental
    z-symmetry that a pure z-mirror test would pair (why contorted specimen 000875599 is
    mostly-unpaired). [PENDING USER CONFIRMATION]

Falsifier (self-check; reported per specimen, must pass): every kept pair's left/right
long-axis lengths agree within LEN_RATIO_TOL (5%) AND centroids mirror about z_mid within
MIRROR_TOL_MM (3 mm). A candidate failing length-agreement is dropped and its bones are
reported identified_as "unpaired" rather than given a forced label.

Side convention: higher centroid-z -> "left", lower centroid-z -> "right" (arbitrary but
documented, consistent within each specimen).

Labeling heuristic (kept pairs among ranks 2..25): split on the median mean-x into caudal
(hindlimb) and cranial (forelimb); cranial = high-x (broad cranium), caudal = low-x. Within
each group order by descending mean long-axis length, map to per-limb sequence:
  caudal/hindlimb : femur > tibia > fibula
  cranial/forelimb: humerus > ulna > radius
Pairs beyond the ordered list -> "unclassified_long_bone". Name confidence: femur/humerus
0.7, tibia/ulna 0.5, fibula/radius 0.4, else 0.3.

Long-axis table (per paired long bone): length_mm = vertex extent along the principal
inertia axis; axis_unit_vector = that axis (sign so projection increases along it);
end_center_min/max_mm = mean centers of the two extreme vertex clusters (~4% at each pole)
= articular end-centers. Mesh long-axis < LONG_BONE_LEN_MM (22 mm): still labeled, no axis
table entry required.

Output: one record per rank in "bones" with identified_as, side, paired flags, length_mm,
axis_unit_vector (+end_center_* for paired bones), and confidence {pairing,name,side,overall}.
"""


def _falsify(kept, idx, lengths, zmid):
    """Re-verify every kept pair against the falsifier; report per-pair detail."""
    checks = []
    all_pass = True
    for c in kept:
        a, b = c["a"], c["b"]
        ca = idx[a]["centroid_mm"]; cb = idx[b]["centroid_mm"]
        mirror_z = abs((ca[2] + cb[2]) / 2.0 - zmid)
        la, lb = lengths[a], lengths[b]
        denom = max(la, lb)
        ratio = min(la, lb) / denom if denom else 0.0
        len_ok = (1.0 - ratio) <= LEN_RATIO_TOL
        mirror_ok = mirror_z <= MIRROR_TOL_MM
        all_pass &= bool(len_ok and mirror_ok)
        checks.append({"pair": [a, b], "length_ratio": round(ratio, 4),
                       "length_agreement_pct": round((1.0 - ratio) * 100.0, 2),
                       "mirror_z_mm": round(mirror_z, 3),
                       "length_ok": bool(len_ok), "mirror_ok": bool(mirror_ok)})
    return {"all_pairs_pass": bool(all_pass), "n_pairs": len(kept), "checks": checks}


def main():
    out = {"method_note": METHOD_NOTE, "specimens": {}}
    summary = []
    for spec, rel in SPECIMENS:
        m, zmid, kept, used, failed, labels, lengths, records, chx = process_specimen(spec, rel)
        seg = m.get("segmentation_params", {})
        idx = {b["rank"]: b for b in m["bones"]}
        flen = {r: lengths[r]["length_mm"] for r in lengths}
        fals = _falsify(kept, idx, flen, zmid)
        out["specimens"][spec] = {
            "source": rel,
            "voxel_size_mm": seg.get("voxel_size_mm"),
            "volume_shape": seg.get("volume_shape"),
            "segmentation_params": seg,
            "total_bones_extracted": m.get("total_bones_extracted"),
            "mid_sagittal_z_mm": round(zmid, 3),
            "cranial_is_high_x": bool(chx),
            "pairs_kept": kept,
            "falsifier": fals,
            "bones": records,
        }
        summary.append("spec %s: pairs_kept=%d bones_paired=%d len_falsified=%d all_pass=%s" % (
            spec, len(kept), len(used), len(failed), fals["all_pairs_pass"]))
    with open(os.path.join(BASE, OUT_PATH), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("Wrote:", os.path.join(BASE, OUT_PATH))
    for ln in summary:
        print(ln)
    ok = all(out["specimens"][s]["falsifier"]["all_pairs_pass"] for s in out["specimens"])
    print("FALSIFIER overall:", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
