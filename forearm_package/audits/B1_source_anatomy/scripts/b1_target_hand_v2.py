"""B1 target hand-region, v2: tighter isolation + rig-tip law + ownership census.

Strategy:
  A. The rig's own tip law (mesh_target._measure_tips.beyond) for L; replicate for R.
  B. Tight ball around each wrist (radius sweep 10..60 mm): ownership census of the
     verts in each ball -> whose skin is the hand.
  C. Hand-surface isolation: verts closer to wrist than to ANY other joint
     (nearest-joint field) -> an ownership-free isolation; extent + slabs.
  D. Distal profile along elbow->wrist axis continued beyond the wrist, radius
     capped at 25 mm (tight), with per-10mm slabs and radial hull stats.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "work"))
from mesh_target import MESH_UNIT_TO_M, MonkeyTarget  # noqa: E402

BIRTH = r"E:\PythonChimera\forearm_package\baseline_snapshot\inputs\monkey_birth.bin"
PACK = r"E:\PythonChimera\forearm_package\baseline_snapshot\inputs\monkey_joints.bin"
OUT = Path(r"E:\PythonChimera\forearm_package\audits\B1_source_anatomy\receipts\target_hand_region_v2.txt")


def main() -> int:
    mt = MonkeyTarget(birth_path=BIRTH, pack_path=PACK)
    L = []
    L.append(f"verts {len(mt.V)} tris {len(mt.F)} joints {len(mt.names)}")

    # ---- A. rig tip law ------------------------------------------------------
    for side, (dist_j, prox_j) in (("L", ("wrist_L", "elbow_L")), ("R", ("wrist_R", "elbow_R"))):
        dJ = mt.joint_pos(dist_j)
        pJ = mt.joint_pos(prox_j)
        arm = np.linalg.norm(dJ - pJ)
        dd = np.linalg.norm(mt.V - dJ, axis=1)
        pdd = np.linalg.norm(mt.V - pJ, axis=1)
        cand = np.where((pdd < 1.2 * arm) & (dd > arm))[0]
        L.append(f"[tip law {side}] |elbow-wrist|={arm:.4f} m  candidates={len(cand)}")
        if len(cand):
            order = cand[np.argsort(-dd[cand])]
            for k in (10, 30, 100):
                sel = order[:k]
                tip = mt.V[sel].mean(axis=0)
                L.append(f"   top-{k:3d} centroid |tip-wrist|={np.linalg.norm(tip - dJ):.4f} m "
                         f"pos={np.round(tip, 4)}  owners={ {mt.names[u]: int(c) for u, c in zip(*np.unique(mt.assign[sel], return_counts=True))} }")
        L.append("")

    # ---- B. ball ownership census -------------------------------------------
    for side, wri in (("L", "wrist_L"), ("R", "wrist_R")):
        W = mt.joint_pos(wri)
        d = np.linalg.norm(mt.V - W, axis=1)
        L.append(f"[ball census {side}] around {wri} at {np.round(W, 4)}")
        for rad in (0.01, 0.02, 0.03, 0.04, 0.05, 0.06):
            sel = d < rad
            if not sel.any():
                L.append(f"   r<{rad*1000:.0f} mm: 0")
                continue
            u, c = np.unique(mt.assign[sel], return_counts=True)
            o = np.argsort(-c)
            L.append(f"   r<{rad*1000:.0f} mm: n={int(sel.sum()):5d}  " +
                     " ".join(f"{mt.names[u[i]]}:{c[i]}" for i in o[:6]))
        L.append("")

    # ---- C. nearest-joint field beyond the wrist ----------------------------
    for side, (elb, wri) in (("L", ("elbow_L", "wrist_L")), ("R", ("elbow_R", "wrist_R"))):
        P = mt.joint_pos(elb)
        W = mt.joint_pos(wri)
        a = (W - P) / np.linalg.norm(W - P)
        JJ = mt.J
        dist_all = np.linalg.norm(mt.V[:, None, :] - JJ[None, :, :], axis=2)  # (V, 28)
        nearest = np.argmin(dist_all, axis=1)
        rel = mt.V - W
        axial = rel @ a
        perp = rel - np.outer(axial, a)
        r = np.linalg.norm(perp, axis=1)
        iw = mt.idx[wri]
        hand_field = (nearest == iw) & (axial > 0)
        L.append(f"[nearest-joint field {side}] verts whose NEAREST joint is {wri} AND distal of it: {int(hand_field.sum())}")
        if hand_field.sum():
            am = axial[hand_field]
            rm = r[hand_field]
            L.append(f"   axial extent {am.max()*1000:.1f} mm; radial max {rm.max()*1000:.1f} mm; radial median {np.median(rm)*1000:.1f} mm")
            edges = np.arange(0, am.max() + 0.005, 0.005)
            hist, _ = np.histogram(am, bins=edges)
            L.append("   5-mm slab counts: " + " ".join(f"{int(edges[i]*1000)}:{hist[i]}" for i in range(len(hist))))
        # wrist-owned verts total
        n_own = int((mt.assign == iw).sum())
        L.append(f"   {wri}-owned verts total: {n_own}; of those distal of wrist: "
                 f"{int(((mt.assign == iw) & (axial > 0)).sum())}")
        # who owns the skin 20-60 mm distal of the wrist within 25 mm radius?
        m = (axial > 0.02) & (axial < 0.06) & (r < 0.025)
        L.append(f"   skin band 20-60mm distal, r<25mm: n={int(m.sum())} owners=" +
                 " ".join(f"{mt.names[u]}:{c}" for u, c in sorted(zip(*np.unique(mt.assign[m], return_counts=True)), key=lambda t: -t[1])[:6]))
        # how far distal does ANY skin within 25 mm of the axis go?
        m2 = (axial > 0) & (r < 0.025)
        if m2.any():
            L.append(f"   max distal extent within 25 mm of axis: {axial[m2].max()*1000:.1f} mm")
        L.append("")

    txt = "\n".join(L)
    OUT.write_text(txt, encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
