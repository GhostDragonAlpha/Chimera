"""Exploration for identify_bones_v2 (lane buffy/bone-id-v2-20260919).

Question: does 'mutual proximity = touching at joints' separate cleanly?
Measures for every bone pair: centroid gap, surface-to-surface min distance
(KD-tree over decimated vertices), end-to-end tip distance (PCA p2/p98 ends).
No thresholds changed; this only informs the edge-rule operationalization,
which is documented in the receipt.
"""
import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import identify_bones_v2 as v2

for spec in v2.SPECS:
    man, bones, axial_tree = v2.load_specimen(spec)
    trees, ranks = {}, sorted(bones)
    for r in ranks:
        f = sorted(spec["preview_dir"].glob(f"bone_{r:02d}_*.obj"))[0]
        m = trimesh.load(f, process=False)
        trees[r] = cKDTree(np.asarray(m.vertices, dtype=float))
    print("=== ", spec["specimen"], " pairs with surface gap < 3.0 mm ===")
    print("  (a, b, surf_gap, centroid_gap, tip_gap_end combos)")
    for i, a in enumerate(ranks):
        for b in ranks[i + 1:]:
            d_surf, _ = trees[a].query(bones[b]["centroid"], k=1)
            # proper symmetric min surface distance
            d1, _ = trees[a].query(trees[b].data, k=1)
            gap = float(d1.min())
            d2, _ = trees[b].query(trees[a].data, k=1)
            gap = min(gap, float(d2.min()))
            if gap < 3.0:
                d_cent = float(np.linalg.norm(bones[a]["centroid"] - bones[b]["centroid"]))
                # tip distances: min over the 4 end-end combos
                tips = [np.linalg.norm(bones[a][e1] - bones[b][e2])
                        for e1 in ("end_a", "end_b") for e2 in ("end_a", "end_b")]
                print(f"  {a:2d}-{b:2d}  surf={gap:5.2f}  cent={d_cent:6.2f}  "
                      f"tip_min={min(tips):6.2f}  tip_max={max(tips):6.2f}  "
                      f"L=({bones[a]['length']:.1f},{bones[b]['length']:.1f})")
