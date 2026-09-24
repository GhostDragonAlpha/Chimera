"""Figure — assembled identity-tested hand skeleton + the derived palm normal.
matplotlib Agg backend set BEFORE pyplot import (no GPU/OpenGL context, CPU-only).
Documentation only (method (b) analog, O1 sec.3 discipline); not evidence.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
import handlib as H  # noqa: E402

OUT = H.OUT / "figures" / "hand_source_assembly_normal.png"
S3 = json.loads((H.OUT / "receipts" / "s3_palm_normal.json").read_text())
PLATE = set(H.PLATE)

anchors_r, _, sites_r, _, _ = H.parse_hand_xml()
placed = {}
for b in H.BONES:
    tri, _ = H.load_stl(H.VENDOR / f"{b}.stl")
    placed[b] = tri + anchors_r[b][None, None, :]

n_palm = np.array(S3["right"]["n_palm_hand_r_local"])
c_all = np.array(S3["right"]["c_all_hand_r_local_mm"]) / 1000.0

fig = plt.figure(figsize=(16, 5.5))
views = [("palmar-side view: camera at c_all - 0.25*n_palm, view dir +n_palm",
          c_all - 0.25 * n_palm),
         ("dorsal-side view: camera at c_all + 0.25*n_palm, view dir -n_palm",
          c_all + 0.25 * n_palm),
         ("distal view: camera at (c_all_x, -0.30, c_all_z), view dir +y",
          np.array([c_all[0], -0.30, c_all[2]]))]
for k, (title, cam) in enumerate(views):
    ax = fig.add_subplot(1, 3, k + 1, projection="3d")
    for b in H.BONES:
        T = placed[b]
        if len(T) > 1600:
            T = T[:: len(T) // 1600]
        col = "#d94f4f" if b == "pisiform" else ("#bbbbcc" if b in PLATE else "#777788")
        pc = Poly3DCollection(T, facecolor=col, edgecolor="none", alpha=0.55)
        ax.add_collection3d(pc)
    L = 0.06
    ax.quiver(c_all[0], c_all[1], c_all[2],
              n_palm[0] * L, n_palm[1] * L, n_palm[2] * L,
              color="crimson", linewidth=2.5, arrow_length_ratio=0.12)
    ax.text(*(c_all + 0.062 * n_palm), "n_palm", color="crimson", fontsize=9)
    comp = {"flexor": "crimson", "extensor": "tab:blue"}
    for sname, (p, c) in H.SITES.items():
        p = np.array(p)
        ax.scatter(*p, color=comp[c], s=28, depthshade=False)
        ax.text(p[0], p[1], p[2], " " + sname.split("-")[0], fontsize=6,
                color=comp[c])
    v = np.vstack([placed[b].reshape(-1, 3) for b in H.BONES])
    ctr = v.mean(axis=0); rad = (v.max(axis=0) - v.min(axis=0)).max() * 0.62
    ax.set_xlim(ctr[0] - rad, ctr[0] + rad); ax.set_ylim(ctr[1] - rad, ctr[1] + rad)
    ax.set_zlim(ctr[2] - rad, ctr[2] + rad)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=8,
                 azim=np.degrees(np.arctan2(-(cam[0] - c_all[0]), -(cam[1] - c_all[1]))))
    ax.set_title(title, fontsize=8)
    ax.set_xlabel("x (hand_r local, m)"); ax.set_ylabel("y (m)"); ax.set_zlabel("z (m)")
fig.suptitle("HAND_SOURCE_EVIDENCE: 27 identity-tested vendor hand bones assembled at XML "
             "geom anchors (scale 1 1 1) - palm plate (12 bones, gray), pisiform (red, "
             "sign rule),\n derived n_palm = (+0.128427, -0.168691, -0.977266) hand_r "
             "local (12.24 deg from -z); sites: flexors crimson, extensors blue; "
             "acceptance split 5/5 clean", fontsize=9)
fig.tight_layout(rect=(0, 0, 1, 0.88))
fig.savefig(OUT, dpi=150)
print(f"wrote {OUT}")
