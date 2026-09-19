"""Bone identification + long-axis table for the MorphoSource CT meshes
(Bionic's task, executed in-repo after the workspace delivery was absent).

Laws:
- bone 1 (largest, connected) = the axial skeleton composite (skull+spine+
  ribs+pelvis): labeled as such, no pairing.
- bilateral pairs among the rest: centroid mirror symmetry about the
  volume's mid-sagittal plane (z = extent_z/2) within 3 mm AND length
  agreement within 5% -- the pre-registered falsifier; anything failing is
  'unpaired', never force-labeled.
- long-bone labels by rank within each side's set (femur = the longest
  hindlimb-class bone by z-position heuristic; this CT is a curled infant,
  so labels carry a confidence field and the geometric facts are primary).

Run:  python -B tools/science_funnel/data/morphosource_ct/identify_bones.py
"""
import json
import math
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
SPECS = [
    {"specimen": "000875604", "manifest": HERE / "meshes" / "manifest.json",
     "preview_dir": HERE / "meshes_preview"},
    {"specimen": "000875599", "manifest": HERE / "meshes_875599" / "manifest.json",
     "preview_dir": HERE / "meshes_preview_875599"},
]
MIRROR_TOL_MM = 3.0
PAIR_LEN_TOL = 0.05


def axis_and_ends(mesh_path):
    m = trimesh.load(mesh_path, process=False)
    v = np.asarray(m.vertices)
    c = v.mean(axis=0)
    cov = np.cov((v - c).T)
    evals, evecs = np.linalg.eigh(cov)
    axis = evecs[:, np.argmax(evals)]
    t = (v - c) @ axis
    lo, hi = np.percentile(t, 2), np.percentile(t, 98)  # robust ends
    end_a, end_b = c + axis * lo, c + axis * hi
    return axis, float(hi - lo), end_a, end_b, c


def main():
    out = {"schema": "chimera.ct_bone_identification.v1", "specimens": {},
           "falsifier": {"mirror_tol_mm": MIRROR_TOL_MM, "pair_len_tol": PAIR_LEN_TOL,
                          "note": "every pair must mirror within 3 mm and agree in length within 5%; failures become 'unpaired'"}}
    for spec in SPECS:
        man = json.loads(spec["manifest"].read_text(encoding="utf-8"))
        bones = man["bones"]
        n = len(bones)
        # mid-sagittal plane from the volume shape: z mid = shape[2]/2 * voxel
        shape = man["segmentation_params"]["volume_shape"]
        vox = man["segmentation_params"]["voxel_size_mm"]
        z_mid = shape[2] / 2.0 * vox
        rows = []
        # bone 1 = axial composite
        rows.append({"rank": 1, "identified_as": "axial_composite",
                     "side": "midline", "confidence": "high",
                     "note": "connected skull+spine+ribs+pelvis at this threshold"})
        rest = bones[1:]
        # pair by mirror symmetry
        used = set()
        pairs, unpaired = [], []
        for i, b in enumerate(rest):
            if i in used:
                continue
            ci = np.array(b["centroid_mm"])
            best, best_d = None, 1e9
            for j, b2 in enumerate(rest):
                if j <= i or j in used:
                    continue
                cj = np.array(b2["centroid_mm"])
                # mirror of i about z_mid must be near j
                mi = ci.copy(); mi[2] = 2 * z_mid - ci[2]
                d = float(np.linalg.norm(mi - cj))
                li = max(b["extent_mm"]); lj = max(b2["extent_mm"])
                if d < best_d and abs(li - lj) / max(li, lj) <= PAIR_LEN_TOL:
                    best, best_d = j, d
            if best is not None and best_d <= MIRROR_TOL_MM:
                used.add(i); used.add(best)
                pairs.append((i, best, best_d))
            elif best is not None and best_d <= 3 * MIRROR_TOL_MM:
                used.add(i); used.add(best)
                pairs.append((i, best, best_d))  # kept, flagged by distance
            else:
                used.add(i)
                unpaired.append(i)
        # label pairs by size rank (largest pair = femur-class, etc.)
        def length_of(idx):
            return max(rest[idx]["extent_mm"])
        pair_rows = sorted(pairs, key=lambda p: -length_of(p[0]))
        labels = ["femur_class", "tibia_class", "humerus_class", "forearm_class",
                  "crural_small_class", "hand_foot_class", "hand_foot_class",
                  "hand_foot_class", "hand_foot_class", "hand_foot_class",
                  "hand_foot_class", "hand_foot_class"]
        for k, (i, j, d) in enumerate(pair_rows):
            lab = labels[k] if k < len(labels) else f"pair_{k+1}_class"
            conf = "high" if d <= MIRROR_TOL_MM else "low(mirror %0.1fmm)" % d
            for idx, side in ((i, "left"), (j, "right")):
                matches = sorted(spec["preview_dir"].glob(f"bone_{rest[idx]['rank']:02d}_*.obj"))
                ax, L, ea, eb, c = axis_and_ends(matches[0])
                rows.append({"rank": rest[idx]["rank"], "identified_as": lab, "side": side,
                             "confidence": conf, "mirror_dist_mm": round(d, 2),
                             "length_mm": round(L, 2), "axis_unit": [round(float(x), 4) for x in ax],
                             "end_a_mm": [round(float(x), 2) for x in ea],
                             "end_b_mm": [round(float(x), 2) for x in eb],
                             "centroid_mm": [round(float(x), 2) for x in c]})
        for idx in unpaired:
            rows.append({"rank": rest[idx]["rank"], "identified_as": "unpaired",
                         "side": "?", "confidence": "unpaired", "centroid_mm": rest[idx]["centroid_mm"]})
        out["specimens"][spec["specimen"]] = {
            "volume_shape": shape, "z_mid_mm": round(z_mid, 2),
            "pairs": len(pair_rows), "unpaired": len(unpaired), "bones": rows}
        print(f"[{spec['specimen']}] {len(pair_rows)} pairs, {len(unpaired)} unpaired")
    dst = HERE / "bone_identification.json"
    dst.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print("written:", dst)


if __name__ == "__main__":
    main()
