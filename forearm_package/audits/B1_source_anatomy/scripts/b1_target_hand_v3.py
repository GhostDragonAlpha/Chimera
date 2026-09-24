"""B1 target hand-region, v3: identify WHAT the skin distal of each wrist is.

Questions:
  1. In distal slabs along elbow->wrist axis (0..115 mm, r<25 mm): who owns the skin,
     and where is it (centroid z/x/y per slab)?
  2. Are the tail_base/spine_lower-owned distal verts a spatially separate blob
     (tail hanging near the hand) or part of the hand surface?
  3. What is at the far end (100-112 mm): a palm pad? digit-like protrusions?
     -> transverse spread + connected component count on a coarse voxel grid.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "work"))
from mesh_target import MonkeyTarget  # noqa: E402

BIRTH = r"E:\PythonChimera\forearm_package\baseline_snapshot\inputs\monkey_birth.bin"
PACK = r"E:\PythonChimera\forearm_package\baseline_snapshot\inputs\monkey_joints.bin"
OUT = Path(r"E:\PythonChimera\forearm_package\audits\B1_source_anatomy\receipts\target_hand_region_v3.txt")


def main() -> int:
    mt = MonkeyTarget(birth_path=BIRTH, pack_path=PACK)
    L: list[str] = []
    for side, (elb, wri) in (("L", ("elbow_L", "wrist_L")),):
        P = mt.joint_pos(elb)
        W = mt.joint_pos(wri)
        a = (W - P) / np.linalg.norm(W - P)
        rel = mt.V - W
        axial = rel @ a
        perp = rel - np.outer(axial, a)
        r = np.linalg.norm(perp, axis=1)
        m = (axial > 0) & (r < 0.025)
        L.append(f"=== {side}: distal skin census along elbow->wrist axis (r<25 mm) ===")
        L.append(f"axis a = {np.round(a, 3)}, |elbow-wrist| = {np.linalg.norm(W - P)*1000:.1f} mm, wrist at {np.round(W, 4)}")
        edges = np.arange(0, 0.12, 0.005)
        idx = np.where(m)[0]
        ax_v = axial[idx]
        for i in range(len(edges) - 1):
            sel = idx[(ax_v >= edges[i]) & (ax_v < edges[i + 1])]
            if len(sel) == 0:
                continue
            u, c = np.unique(mt.assign[sel], return_counts=True)
            o = np.argsort(-c)
            cen = mt.V[sel].mean(axis=0)
            own = " ".join(f"{mt.names[u[j]]}:{c[j]}" for j in o[:4])
            L.append(f"  slab {int(edges[i]*1000):3d}-{int(edges[i+1]*1000):3d} mm n={len(sel):4d} "
                     f"centroid={np.round(cen, 4)}  owners: {own}")
        L.append("")

        # tail/spine-owned distal verts: where are they?
        for owner in ("tail_base", "spine_lower", "elbow_L", "wrist_L"):
            sel = m & (mt.assign == mt.idx[owner])
            if not sel.any():
                continue
            pts = mt.V[sel]
            L.append(f"  owner {owner}: n={int(sel.sum())} distal-range "
                     f"[{axial[sel].min()*1000:.1f}, {axial[sel].max()*1000:.1f}] mm  "
                     f"z-range [{pts[:,2].min()*1000:.1f}, {pts[:,2].max()*1000:.1f}] mm  "
                     f"x-range [{pts[:,0].min()*1000:.1f}, {pts[:,0].max()*1000:.1f}] mm  "
                     f"y-range [{pts[:,1].min()*1000:.1f}, {pts[:,1].max()*1000:.1f}] mm")
        L.append("")

        # far-end structure: verts 80-115 mm distal, all radii < 40 mm
        far = (axial > 0.08) & (axial < 0.115) & (r < 0.04)
        pts = mt.V[far]
        L.append(f"far end 80-115 mm distal (r<40 mm): n={int(far.sum())}")
        if far.sum():
            u, c = np.unique(mt.assign[far], return_counts=True)
            L.append("  owners: " + " ".join(f"{mt.names[u2]}:{c2}" for u2, c2 in sorted(zip(u, c), key=lambda t: -t[1])))
            L.append(f"  bbox x [{pts[:,0].min()*1000:.1f}, {pts[:,0].max()*1000:.1f}] "
                     f"y [{pts[:,1].min()*1000:.1f}, {pts[:,1].max()*1000:.1f}] "
                     f"z [{pts[:,2].min()*1000:.1f}, {pts[:,2].max()*1000:.1f}] mm")
            # transverse (perp) spread at the far end: b/c extents
            pp = perp[far]
            # build perp ONB from a: pick any orthogonal
            tmp = np.array([1.0, 0, 0]) if abs(a[0]) < 0.9 else np.array([0, 1.0, 0])
            b1 = np.cross(a, tmp); b1 /= np.linalg.norm(b1)
            c1 = np.cross(a, b1)
            L.append(f"  transverse extents: b1 {((pp@b1).max()-(pp@b1).min())*1000:.1f} mm, "
                     f"c1 {((pp@c1).max()-(pp@c1).min())*1000:.1f} mm")
        L.append("")

        # voxel occupancy of the distal region (is it one blob or several digits?)
        region = (axial > 0.03) & (r < 0.035)
        pts = mt.V[region]
        L.append(f"voxel occupancy, axial>30mm r<35mm: n={int(region.sum())}")
        if len(pts):
            res = 0.008  # 8 mm voxels
            g = np.floor(pts / res).astype(int)
            occ = {tuple(row) for row in g}
            L.append(f"  8-mm voxels occupied: {len(occ)}")
            # crude connected components (26-neighborhood via BFS on voxel set)
            occset = occ
            seen: set = set()
            comps = []
            for v in occ:
                if v in seen:
                    continue
                stack = [v]
                seen.add(v)
                size = 0
                while stack:
                    cur = stack.pop()
                    size += 1
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            for dz in (-1, 0, 1):
                                nb = (cur[0]+dx, cur[1]+dy, cur[2]+dz)
                                if nb in occset and nb not in seen:
                                    seen.add(nb)
                                    stack.append(nb)
                comps.append(size)
            comps.sort(reverse=True)
            L.append(f"  connected components (26-neigh, voxel sizes): {comps[:12]}")
        L.append("")

    txt = "\n".join(L)
    OUT.write_text(txt, encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
