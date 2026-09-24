"""B1 target-side dossier: what does the monkey pack + mesh contain for the hand region?

Read-only on baseline_snapshot/inputs/*.bin (verified byte-identical to
E:/PythonChimera/Saved/meshes/*.bin by sha256). Uses the baseline loader copy in work/.

Measured (all in authored metres, MESH_UNIT_TO_M = 0.065):
  - full pack joint list + parents + positions
  - digit-like joints (expected: NONE)
  - per wrist: distal mesh surface (vertices beyond wrist along elbow->wrist axis),
    axial extent, transverse spread, vertex counts in distal slabs (density)
  - pack ownership (assign) of distal-hand vertices: which joints own them
  - triangle ownership near/beyond the wrist by majority vertex vote
Output -> receipts/target_hand_region.txt
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "work"))
from mesh_target import MESH_UNIT_TO_M, MonkeyTarget  # noqa: E402

BIRTH = r"E:\PythonChimera\forearm_package\baseline_snapshot\inputs\monkey_birth.bin"
PACK = r"E:\PythonChimera\forearm_package\baseline_snapshot\inputs\monkey_joints.bin"
OUT = Path(r"E:\PythonChimera\forearm_package\audits\B1_source_anatomy\receipts\target_hand_region.txt")


def main() -> int:
    mt = MonkeyTarget(birth_path=BIRTH, pack_path=PACK)
    L = []
    L.append(f"birth sha256 {mt.birth_sha} bytes {mt.input_bytes['birth']}")
    L.append(f"pack  sha256 {mt.pack_sha} bytes {mt.input_bytes['pack']}")
    L.append(f"mesh_unit_to_m = {MESH_UNIT_TO_M} (authored)")
    L.append(f"mesh verts {len(mt.V)} tris {len(mt.F)}")
    L.append(f"pack joints {len(mt.names)}")
    L.append("")
    L.append("JOINT LIST (name, parent, pos_m, has_band_verts):")
    for i, n in enumerate(mt.names):
        par = mt.names[mt.parents[i]] if mt.parents[i] >= 0 else "ROOT"
        nb = int((mt.assign == i).sum())
        L.append(f"  [{i:2d}] {n:12s} parent={par:12s} J={np.round(mt.J[i], 4)} band_verts={nb}")
    L.append("")

    digit_names = [n for n in mt.names if any(k in n.lower() for k in
                   ("finger", "digit", "thumb", "hand", "mcp", "pip", "dip", "prox", "dist", "tip"))]
    L.append(f"digit/hand-like joint names: {digit_names}")
    ulna_names = [n for n in mt.names if "ulna" in n.lower()]
    L.append(f"ulna-specific joint names: {ulna_names}")
    L.append("")

    # ---- distal-hand surface per wrist -------------------------------------
    for side, (elb, wri) in (("L", ("elbow_L", "wrist_L")), ("R", ("shoulder_R", "wrist_R")) if False else ("R", ("elbow_R", "wrist_R"))):
        P = mt.joint_pos(elb)
        W = mt.joint_pos(wri)
        a = W - P
        a /= np.linalg.norm(a)  # distal direction (down the forearm)
        rel = mt.V - W
        axial = rel @ a
        perp = rel - np.outer(axial, a)
        r = np.linalg.norm(perp, axis=1)

        # hand-region candidates: distal of the wrist, within a radius cap of the
        # wrist axis line. Cap chosen as 1.6x the wrist band's own transverse extent
        band = mt.band_verts(wri)
        band_rel = band - W
        band_axial = band_rel @ a
        band_perp = band_rel - np.outer(band_axial, a)
        band_r = np.linalg.norm(band_perp, axis=1)
        band_extent = float(band_r.max()) if len(band_r) else 0.0
        cap = 1.6 * band_extent + 0.01
        L.append(f"=== {side} hand: elbow {elb} -> wrist {wri}")
        L.append(f"  |elbow->wrist| = {np.linalg.norm(W - P):.4f} m")
        L.append(f"  wrist band (assign=={wri}): {len(band)} verts, transverse extent {band_extent*1000:.1f} mm")
        L.append(f"  hand-region radius cap = 1.6 * band extent + 10 mm = {cap*1000:.1f} mm")

        m = (axial > 0) & (r < cap)
        nv = int(m.sum())
        L.append(f"  vertices distal of wrist within cap: {nv}")
        if nv:
            d = mt.V[m]
            am = axial[m]
            L.append(f"  distal axial extent (max (v-wrist).a): {am.max()*1000:.1f} mm  "
                     f"({am.max():.4f} m)")
            rm = r[m]
            L.append(f"  max radial distance from axis: {rm.max()*1000:.1f} mm")
            # slabs of 10 mm: vertex density profile
            edges = np.arange(0, am.max() + 0.01, 0.01)
            hist, _ = np.histogram(am, bins=edges)
            L.append("  vertex count per 10 mm distal slab (slab_start_mm:count): "
                     + " ".join(f"{int(edges[i]*1000)}:{hist[i]}" for i in range(len(hist))))
            # tip estimate: centroid of the 30 most distal verts (mirrors rig's tip law)
            idx = np.argsort(-am)[:30]
            tip = d[idx].mean(axis=0)
            L.append(f"  30-vert distal tip centroid: {np.round(tip, 4)} m, "
                     f"|tip-wrist| = {np.linalg.norm(tip - W):.4f} m")
            L.append(f"  |wrist-elbow| vs |tip-wrist| ratio: {np.linalg.norm(tip - W) / np.linalg.norm(W - P):.3f}")
            # ownership of the distal region
            own_ids = mt.assign[m]
            uniq, cnt = np.unique(own_ids, return_counts=True)
            order = np.argsort(-cnt)
            L.append("  pack ownership of those verts:")
            for o in order:
                L.append(f"    {mt.names[uniq[o]]:12s} {cnt[o]:5d}")
            # how far does each owner's region reach distally?
            L.append("  per-owner distal reach (max axial mm):")
            for o in order:
                sel = m & (mt.assign == uniq[o])
                L.append(f"    {mt.names[uniq[o]]:12s} {(axial[sel].max()*1000):8.1f}")
        else:
            L.append("  NO VERTICES distal of wrist within cap -> hand region EMPTY")
        L.append("")

    # ---- triangle ownership just distal of each wrist -----------------------
    tri_v = mt.V[mt.F]  # (M,3,3)
    for side, wri in (("L", "wrist_L"), ("R", "wrist_R")):
        W = mt.joint_pos(wri)
        cent = tri_v.mean(axis=1)
        dd = np.linalg.norm(cent - W, axis=1)
        near = np.argsort(dd)[:400]
        own = mt.assign[mt.F[near]]
        # majority vote per triangle
        maj = np.zeros(len(near), dtype=int)
        for k in range(len(near)):
            u, c = np.unique(own[k], return_counts=True)
            maj[k] = u[np.argmax(c)]
        uniq, cnt = np.unique(maj, return_counts=True)
        order = np.argsort(-cnt)
        L.append(f"=== {side}: 400 triangles nearest wrist_{side} (centroid dist {dd[near].min()*1000:.1f}-{dd[near].max()*1000:.1f} mm), majority owner:")
        for o in order:
            L.append(f"    {mt.names[uniq[o]]:12s} {cnt[o]:5d}")
        L.append("")

    txt = "\n".join(L)
    OUT.write_text(txt, encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
