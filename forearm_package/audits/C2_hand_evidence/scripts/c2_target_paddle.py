"""C2 step 2b — TARGET paddle geometry from baseline inputs/monkey_birth.bin.

Read-only (MonkeyTarget hashes inputs; baseline never written). Measures, for
each side, along the elbow->wrist axis continued distally:
  - paddle length (max axial in r<25 mm tube; also r<40 mm)
  - per-4mm-slab profile: vertex count, width/thickness extents (b/c), centroid
    offset (cross-section asymmetry)
  - lobation tests:
      (i) width-profile local minima (grooves) and their axial persistence
      (ii) angular radial profile r(theta) per slab; angular minima persistent
           over >=20 mm
      (iii) 2D cross-section component split (gap threshold) persistent >=20 mm
  - paddle PCA principal axis vs elbow->wrist axis angle
  - connected components at 8 / 4 / 2 mm voxels
  - far-end bbox and transverse extents (compare B1: 47.1 x 18.1 mm)
  - proportions paddle:forearm
Writes receipt to audits/C2_hand_evidence/receipts/target_paddle_measures.txt.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "work"))
from mesh_target import MonkeyTarget  # noqa: E402

BIRTH = r"E:\PythonChimera\forearm_package\baseline_snapshot\inputs\monkey_birth.bin"
PACK = r"E:\PythonChimera\forearm_package\baseline_snapshot\inputs\monkey_joints.bin"
OUT = Path(r"E:\PythonChimera\forearm_package\audits\C2_hand_evidence\receipts\target_paddle_measures.txt")

L: list[str] = []


def say(s: str = "") -> None:
    L.append(s)
    print(s)


mt = MonkeyTarget(birth_path=BIRTH, pack_path=PACK)
say("=== C2 TARGET PADDLE MEASURES (baseline inputs; MESH_UNIT_TO_M authored 0.065) ===")
say(f"verts {mt.V.shape[0]}, joints {len(mt.names)}")

for side, (E, W) in (("R", ("elbow_R", "wrist_R")), ("L", ("elbow_L", "wrist_L"))):
    P = mt.joint_pos(E)
    Wr = mt.joint_pos(W)
    axis = Wr - P
    fore_len = np.linalg.norm(axis)
    a = axis / fore_len
    say("")
    say(f"########## SIDE {side}: elbow {np.round(P,4)} -> wrist {np.round(Wr,4)}  |forearm| = {fore_len*1000:.3f} mm")
    rel = mt.V - Wr
    axial = rel @ a
    perp = rel - np.outer(axial, a)
    r = np.linalg.norm(perp, axis=1)

    tmp = np.array([1.0, 0, 0]) if abs(a[0]) < 0.9 else np.array([0, 1.0, 0])
    b1 = np.cross(a, tmp); b1 /= np.linalg.norm(b1)
    c1 = np.cross(a, b1)
    say(f"axis a = {np.round(a,4)}; ONB b1 = {np.round(b1,4)}, c1 = {np.round(c1,4)}")

    for rtube in (0.025, 0.040):
        sel = (axial > 0) & (r < rtube)
        say(f"distal skin (axial>0, r<{rtube*1000:.0f} mm): n={int(sel.sum())}, max axial = {axial[sel].max()*1000:.1f} mm")

    # ---- paddle region (generous tube) ----
    reg = (axial > -0.005) & (axial < 0.120) & (r < 0.045)
    idx = np.where(reg)[0]
    axr = axial[idx]
    say(f"paddle region (axial>-5..120 mm, r<45 mm): n={len(idx)}")

    # ---- length profile per 4 mm slab ----
    say("")
    say("--- per-4mm-slab profile (width=b1 extent, thick=c1 extent, centroid offsets) ---")
    say("  slab(mm)   n   width_mm  thick_mm  cen_b_mm  cen_c_mm")
    edges = np.arange(-0.004, 0.124, 0.004)
    slab_rec = []
    for i in range(len(edges) - 1):
        s = idx[(axr >= edges[i]) & (axr < edges[i + 1])]
        if len(s) < 4:
            continue
        pp = perp[s]
        bb = pp @ b1
        cc = pp @ c1
        wb = bb.max() - bb.min()
        wc = cc.max() - cc.min()
        slab_rec.append((0.5 * (edges[i] + edges[i + 1]), len(s), wb, wc, bb.mean(), cc.mean()))
        say(f"  {edges[i]*1000:6.0f}  {len(s):5d}   {wb*1000:7.1f}  {wc*1000:8.1f}  {bb.mean()*1000:8.1f}  {cc.mean()*1000:8.1f}")

    A = np.array([t[0] for t in slab_rec])
    WB = np.array([t[2] for t in slab_rec])
    WC = np.array([t[3] for t in slab_rec])
    CB = np.array([t[4] for t in slab_rec])
    CC = np.array([t[5] for t in slab_rec])

    # ---- lobation test (i): local minima of width profile, persistence ----
    def local_minima(x):
        m = []
        for i in range(1, len(x) - 1):
            if x[i] <= x[i - 1] and x[i] <= x[i + 1] and (x[i] < x[i - 1] or x[i] < x[i + 1]):
                m.append(i)
        return m

    say("")
    say("--- lobation (i): width-profile local minima ---")
    for nm, Wp in (("width(b1)", WB), ("thick(c1)", WC)):
        mins = local_minima(Wp)
        out = []
        for i in mins:
            # persistence: distance until profile rises >=10% of local scale on both sides
            thresh = Wp[i] + 0.10 * (np.percentile(Wp, 90) - np.percentile(Wp, 10))
            li = i
            while li > 0 and Wp[li] < thresh:
                li -= 1
            ri = i
            while ri < len(Wp) - 1 and Wp[ri] < thresh:
                ri += 1
            pers = (A[ri] - A[li]) * 1000
            out.append(f"@{A[i]*1000:.0f}mm (w={Wp[i]*1000:.1f}) span<{pers:.0f}mm")
        say(f"  {nm}: minima {len(mins)}: " + "; ".join(out))
    say(f"  (persistence >=20 mm required for a 'groove' under the preregistration)")

    # ---- lobation test (ii): angular radial profile persistence ----
    say("")
    say("--- lobation (ii): angular r(theta) minima persistent >=20 mm ---")
    nth = 24
    slab_ang = []
    sedges = np.arange(0.055, 0.116, 0.004)  # distal half where digits would be
    for i in range(len(sedges) - 1):
        s = idx[(axr >= sedges[i]) & (axr < sedges[i + 1])]
        if len(s) < 10:
            continue
        pp = perp[s] - perp[s].mean(axis=0)
        th = np.arctan2(pp @ c1, pp @ b1)
        rr = np.linalg.norm(pp, axis=1)
        prof = np.zeros(nth)
        bins = ((th + np.pi) / (2 * np.pi) * nth).astype(int) % nth
        for k in range(nth):
            selk = bins == k
            prof[k] = rr[selk].max() if selk.any() else np.nan
        # fill nans by interpolation
        ok = ~np.isnan(prof)
        if ok.sum() < nth // 2:
            continue
        prof = np.interp(np.arange(nth), np.where(ok)[0], prof[ok])
        slab_ang.append((0.5 * (sedges[i] + sedges[i + 1]), prof))
    # find angular minima per slab, track persistence across slabs
    min_tracks: dict[int, list[float]] = {}
    for aa, prof in slab_ang:
        for k in range(nth):
            prev = prof[(k - 1) % nth]
            nxt = prof[(k + 1) % nth]
            if prof[k] <= prev and prof[k] <= nxt:
                # record depth
                min_tracks.setdefault(k, []).append(aa)
    persistent = []
    for k, aas in sorted(min_tracks.items()):
        aas = sorted(aas)
        # longest run with gaps <= 8 mm
        best = cur = [aas[0]] if aas else []
        for x in aas[1:]:
            if x - cur[-1] <= 0.008:
                cur = cur + [x]
            else:
                cur = [x]
            if (cur[-1] - cur[0]) > (best[-1] - best[0]):
                best = cur
        span = (best[-1] - best[0]) * 1000 if best else 0
        if span >= 20:
            persistent.append((k, span, len(aas)))
    say(f"  slabs analysed: {len(slab_ang)} from {sedges[0]*1000:.0f} to {sedges[-1]*1000:.0f} mm; angular bins {nth}")
    if persistent:
        for k, span, naas in persistent:
            say(f"  persistent angular minimum at theta-bin {k} ({np.degrees(2*np.pi*k/nth)-180:.0f} deg): span {span:.0f} mm over {naas} slabs")
        say(f"  => persistent-groove count (>=20 mm): {len(persistent)}")
    else:
        say("  persistent angular minimum (>=20 mm span): NONE")

    # ---- lobation test (iii): cross-section splits ----
    say("")
    say("--- lobation (iii): 2D cross-section splits (gap threshold 6 mm), distal half ---")
    split_slabs = 0
    first_split = None
    last_split = None
    for i in range(len(sedges) - 1):
        s = idx[(axr >= sedges[i]) & (axr < sedges[i + 1])]
        if len(s) < 10:
            continue
        pp = (perp[s])[:, :]; pp2 = pp @ np.vstack([b1, c1]).T
        # greedy single-linkage at 6 mm via grid
        g = np.floor(pp2 / 0.006).astype(int)
        cells = {tuple(row) for row in g}
        seen = set(); ncomp = 0
        for v in cells:
            if v in seen:
                continue
            ncomp += 1
            stack = [v]; seen.add(v)
            while stack:
                cur = stack.pop()
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nb = (cur[0] + dx, cur[1] + dy)
                        if nb in cells and nb not in seen:
                            seen.add(nb); stack.append(nb)
        if ncomp > 1:
            split_slabs += 1
            if first_split is None:
                first_split = sedges[i]
            last_split = sedges[i + 1]
    say(f"  slabs with >1 component at 6 mm gap: {split_slabs} / {len(sedges)-1}")
    if first_split is not None:
        say(f"  split axial range: [{first_split*1000:.0f}, {last_split*1000:.0f}] mm")
    else:
        say("  NO slab splits into >1 component (single convex-ish cross-section throughout)")

    # ---- paddle PCA axis vs forearm axis ----
    say("")
    pts = mt.V[idx]
    ctr = pts.mean(axis=0)
    u_, s_, vt_ = np.linalg.svd(pts - ctr, full_matrices=False)
    p1 = vt_[0]
    if p1 @ a < 0:
        p1 = -p1
    ang_pca = np.degrees(np.arccos(np.clip(p1 @ a, -1, 1)))
    say(f"paddle PCA axis = {np.round(p1,4)}, angle vs elbow->wrist axis = {ang_pca:.1f} deg (map falsifier (a) threshold 15 deg)")
    say(f"paddle extent along a / b1 / c1 (region bbox): "
        f"{(axial[idx].max()-axial[idx].min())*1000:.1f} / {((perp[idx]@b1).max()-(perp[idx]@b1).min())*1000:.1f} / "
        f"{((perp[idx]@c1).max()-(perp[idx]@c1).min())*1000:.1f} mm")

    # ---- far end ----
    far = (axial > 0.080) & (axial < 0.115) & (r < 0.040)
    pf = mt.V[far]
    say(f"far end (80-115 mm, r<40 mm): n={int(far.sum())}; bbox x [{pf[:,0].min()*1000:.1f}, {pf[:,0].max()*1000:.1f}] "
        f"y [{pf[:,1].min()*1000:.1f}, {pf[:,1].max()*1000:.1f}] z [{pf[:,2].min()*1000:.1f}, {pf[:,2].max()*1000:.1f}] mm")
    ppf = perp[far]
    say(f"  transverse extents: b1 {((ppf@b1).max()-(ppf@b1).min())*1000:.1f} mm, c1 {((ppf@c1).max()-(ppf@c1).min())*1000:.1f} mm")

    # ---- voxel connectivity at 8 / 4 / 2 mm ----
    say("")
    say("--- connected components (26-neigh voxel BFS), region axial>30 mm r<35 mm ---")
    rreg = (axial > 0.03) & (r < 0.035)
    pr = mt.V[rreg]
    say(f"  verts in region: {len(pr)}")
    for res_mm in (8, 4, 2):
        res = res_mm / 1000
        g = np.floor(pr / res).astype(int)
        occ = {tuple(row) for row in g}
        seen = set(); comps = []
        for v in occ:
            if v in seen:
                continue
            stack = [v]; seen.add(v); size = 0
            while stack:
                cur = stack.pop(); size += 1
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            nb = (cur[0] + dx, cur[1] + dy, cur[2] + dz)
                            if nb in occ and nb not in seen:
                                seen.add(nb); stack.append(nb)
            comps.append(size)
        comps.sort(reverse=True)
        say(f"  {res_mm:2d} mm voxels: {len(occ)} occupied, components {comps[:8]}")

    # ---- proportions ----
    maxax25 = axial[(axial > 0) & (r < 0.025)].max()
    maxax40 = axial[(axial > 0) & (r < 0.040)].max()
    say("")
    say("--- proportions ---")
    say(f"forearm elbow->wrist = {fore_len*1000:.3f} mm")
    say(f"paddle:forearm (max axial r<25mm) = {maxax25/fore_len:.4f}   (r<40mm: {maxax40/fore_len:.4f})")

say("")
say("=== MIRROR CHECK ===")
jL = mt.joint_pos("wrist_L"); jR = mt.joint_pos("wrist_R")
say(f"wrist_L {np.round(jL,4)}  wrist_R {np.round(jR,4)}  (x-mirrors: {abs(jL[0]+jR[0])<1e-9 and abs(jL[1]-jR[1])<1e-9})")

OUT.write_text("\n".join(L), encoding="utf-8")
print(f"\n[receipt written: {OUT}]")
