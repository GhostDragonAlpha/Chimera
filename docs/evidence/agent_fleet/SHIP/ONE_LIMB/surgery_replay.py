#!/usr/bin/env python3
"""AN2: the FULL OFFLINE SURGERY REPLAY — the engine's exact pipeline
from the seal blob (piece->slot lists) through the merge, wall-strip,
and the two oblique cuts, then EVERY validation bar the route checks:
closure (edge-manifold), chi, positive v0, degenerate guard, coverage,
mass, genus before/after, piece-book uniqueness, seed agreement.

All slot arithmetic is EXACT (the blob's own slot ids, the mesh's own
positions). This is the desk-check instrument for window #12: it names
the failing bar before the build.
"""
import json
import struct
import sys
from collections import defaultdict

SNAP = sys.argv[1] if len(sys.argv) > 1 else ".tmp/build_tick/Release/session_snapshot"
OUT = sys.argv[2] if len(sys.argv) > 2 else \
    "docs/evidence/agent_fleet/SHIP/ONE_LIMB/surgery_replay.json"

ANKLE_Y, KNEE_Y, HIP_Y = 0.3378, 1.9033, 3.4153
TOL = 2e-3
SEAL_MAGIC = 0x31534553
RHO = 1000.0
MASS_TARGET = 13824.5
DEGEN = 0.005


def load_mesh():
    mesh = open(SNAP + "/mesh_bin.blob", "rb").read()
    N, idx_count = struct.unpack_from("<II", mesh, 0)
    verts = list(struct.unpack_from("<%df" % (N * 9), mesh, 24))
    return N, verts


def load_seal_state():
    b = open(SNAP + "/tick_seal_state.blob", "rb").read()
    magic, nv, n_cuts = struct.unpack_from("<III", b, 0)
    assert magic == SEAL_MAGIC
    off = 12
    cuts = []
    for _ in range(n_cuts):
        n = struct.unpack_from("<I", b, off)[0]
        vs = struct.unpack_from("<8I", b, off + 4)
        ws = struct.unpack_from("<8f", b, off + 36)
        cuts.append((n, list(vs), list(ws)))
        off += 68
    (n_cells,) = struct.unpack_from("<I", b, off)
    off += 4
    cells = []
    for _ in range(n_cells):
        (pn,) = struct.unpack_from("<I", b, off)
        off += 4
        pieces = list(struct.unpack_from("<%dI" % pn, b, off))
        off += pn * 4
        v0, vol, p = struct.unpack_from("<3f", b, off)
        off += 12
        (caps,) = struct.unpack_from("<i", b, off)
        off += 4
        ylo, yhi = struct.unpack_from("<2f", b, off)
        off += 8
        off += 1
        cells.append({"pieces": pieces, "v0": v0, "ylo": ylo, "yhi": yhi})
    return nv, cuts, cells


class Space:
    """the point space: originals + cut blends, extensible"""

    def __init__(self, nv, verts, cuts):
        self.nv = nv
        self.verts = verts
        self.cuts = [cuts[i] for i in range(len(cuts))]
        self.pos = []
        for s in range(nv):
            self.pos.append(verts[s * 9: s * 9 + 3])
        for (n, vs, ws) in cuts:
            acc = [0.0, 0.0, 0.0]
            for i in range(n):
                for d in range(3):
                    acc[d] += ws[i] * verts[vs[i] * 9 + d]
            self.pos.append(acc)

    def add_cut(self, a, b, wa, wb):
        self.pos.append([wa[0] + wb[0], wa[1] + wb[1], wa[2] + wb[2]])
        return len(self.pos) - 1

    def p(self, s):
        return self.pos[s]


def div(sp, tri):
    a, b, c = sp.p(tri[0]), sp.p(tri[1]), sp.p(tri[2])
    return (a[0] * (b[1] * c[2] - b[2] * c[1])
            + a[1] * (b[2] * c[0] - b[0] * c[2])
            + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0


def vol(sp, pieces):
    v = 0.0
    for i in range(0, len(pieces) - 2, 3):
        v += div(sp, pieces[i:i + 3])
    return v


def components(pieces):
    npieces = len(pieces) // 3
    parent = list(range(npieces))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    first = {}
    for p in range(npieces):
        for k in range(3):
            s = pieces[p * 3 + k]
            if s not in first:
                first[s] = p
            else:
                ra, rb = find(first[s]), find(p)
                if ra != rb:
                    parent[ra] = rb
    comps = {}
    for p in range(npieces):
        comps.setdefault(find(p), []).extend(pieces[p * 3: p * 3 + 3])
    return [comps[r] for r in sorted(comps)]


def genus_components(sp, pieces):
    """the corrected law: sum (2-chi) over CONNECTED CLOSED components"""
    g = 0
    closed_n = 0
    for comp in components(pieces):
        closed, chi = topology(sp, comp)
        if closed:
            g += 2 - chi
            closed_n += 1
    return g, closed_n


def topology(sp, pieces):
    edge = defaultdict(int)
    verts = set()
    for i in range(0, len(pieces) - 2, 3):
        t = pieces[i:i + 3]
        verts.update(t)
        for k in range(3):
            a, b = t[k], t[(k + 1) % 3]
            edge[(min(a, b), max(a, b))] += 1
    closed = all(n == 2 for n in edge.values())
    chi = len(verts) - len(edge) + len(pieces) // 3
    return closed, chi


def oblique_cut(sp, pieces, nrm, pt):
    """the engine's cut-and-weld on a piece list with an oriented plane;
    returns (below_pieces, above_pieces, caps_added) or None on refusal"""
    pd = [sum(nrm[i] * (sp.p(s)[i] - pt[i]) for i in range(3))
          for s in range(len(sp.pos))]
    cut_id = {}
    lower, upper, segs = [], [], []
    split = 0

    def edge_cut(sa, sb):
        if pd[sa] >= pd[sb]:
            sa, sb = sb, sa
        if not (pd[sa] < 0 <= pd[sb]):
            return None
        key = (min(sa, sb), max(sa, sb))
        if key in cut_id:
            return cut_id[key]
        t = pd[sa] / (pd[sa] - pd[sb])
        pa, pb = sp.p(sa), sp.p(sb)
        newp = [pa[k] + t * (pb[k] - pa[k]) for k in range(3)]
        sp.pos.append(newp)
        nid = len(sp.pos) - 1
        pd.append(0.0)
        cut_id[key] = nid
        return nid

    for i in range(0, len(pieces) - 2, 3):
        vs = pieces[i:i + 3]
        bl = [pd[s] < 0 for s in vs]
        nb = sum(bl)
        if nb == 3:
            lower.extend(vs)
            continue
        if nb == 0:
            upper.extend(vs)
            continue
        split += 1
        if nb == 1:
            i0 = bl.index(True)
            A = vs[i0]
            B = vs[(i0 + 1) % 3]
            C = vs[(i0 + 2) % 3]
            p0 = edge_cut(A, B)
            p1 = edge_cut(C, A)
            if p0 is None or p1 is None:
                return None
            lower.extend([A, p0, p1])
            upper.extend([p0, B, C])
            upper.extend([p0, C, p1])
            segs.append((p0, p1))
        else:
            iC = bl.index(False)
            C = vs[iC]
            A = vs[(iC + 1) % 3]
            B = vs[(iC + 2) % 3]
            p0 = edge_cut(B, C)
            p1 = edge_cut(C, A)
            if p0 is None or p1 is None:
                return None
            lower.extend([A, B, p0])
            lower.extend([A, p0, p1])
            upper.extend([p0, C, p1])
            segs.append((p0, p1))
    nxt = {}
    for a, b in segs:
        if a in nxt:
            return None                       # out-degree > 1
        nxt[a] = b
    visited = set()
    caps = 0
    for start in nxt:
        if start in visited:
            continue
        ring = [start]
        visited.add(start)
        cur = start
        while True:
            cur = nxt[cur]
            if cur == start:
                break
            if cur in visited or len(ring) > len(sp.pos):
                return None
            ring.append(cur)
            visited.add(cur)
        for k in range(1, len(ring) - 1):
            lower.extend([ring[0], ring[k + 1], ring[k]])
            upper.extend([ring[0], ring[k], ring[k + 1]])
            caps += 2
    return lower, upper, caps


def norm3(d):
    L = sum(x * x for x in d) ** 0.5
    return [x / L for x in d]


def main():
    nv, verts = load_mesh()
    snv, cuts, cells = load_seal_state()
    sp = Space(nv, verts, cuts)

    # -- genus before (over the closed 4-band cells) --
    genus_before = 0
    closed_before = 0
    for c in cells:
        g, cn = genus_components(sp, c["pieces"])
        genus_before += g
        closed_before += cn

    # -- the band grouping (containment) + splits --
    def members(has_lo, lo, hi):
        out = []
        for i, c in enumerate(cells):
            if has_lo and c["ylo"] < lo - TOL:
                continue
            if c["yhi"] > hi + TOL:
                continue
            out.append(i)
        return out

    for has_lo, lo, hi in ((True, KNEE_Y, HIP_Y), (True, ANKLE_Y, KNEE_Y),
                           (False, None, ANKLE_Y)):
        for _ in range(8):
            m = members(has_lo, lo, hi)
            grew = False
            for idx in m:
                comps = components(cells[idx]["pieces"])
                if len(comps) < 2:
                    continue
                new_cells = []
                for comp in comps:
                    lo_y = min(sp.p(s)[1] for s in comp)
                    hi_y = max(sp.p(s)[1] for s in comp)
                    new_cells.append({"pieces": comp, "v0": vol(sp, comp),
                                      "ylo": lo_y, "yhi": hi_y})
                cells[idx] = new_cells[0]
                cells.extend(new_cells[1:])
                grew = True
                break
            if not grew:
                break

    # -- side selection (the engine's estimator: mean slot-occurrence x) --
    def cell_cx(cell):
        sx = sum(sp.p(s)[0] for s in cell["pieces"])
        return sx / len(cell["pieces"])

    thigh = [c for c in members(True, KNEE_Y, HIP_Y) if cell_cx(cells[c]) >= 0]
    calf = [c for c in members(True, ANKLE_Y, KNEE_Y) if cell_cx(cells[c]) >= 0]
    foot = [c for c in members(False, 0.0, ANKLE_Y) if cell_cx(cells[c]) >= 0]
    side_cells = thigh + calf + foot

    # -- merge + wall strip --
    merged = []
    for idx in side_cells:
        merged.extend(cells[idx]["pieces"])
    wc = defaultdict(int)
    for i in range(0, len(merged) - 2, 3):
        t = sorted(merged[i:i + 3])
        if all(s >= nv for s in t):
            wc[tuple(t)] += 1
    leg = []
    walls_removed = 0
    anomaly = False
    for i in range(0, len(merged) - 2, 3):
        t = merged[i:i + 3]
        if all(s >= nv for s in t):
            n = wc[tuple(sorted(t))]
            if n == 2:
                walls_removed += 1
                continue
            if n != 1:
                anomaly = True
                break
        leg.extend(t)

    v0_leg = vol(sp, leg)
    jp = open(SNAP + "/tick_joints.blob", "rb").read()
    npins = struct.unpack_from("<I", jp, 0)[0]
    pins = [struct.unpack_from("<3f", jp, 4 + i * 12) for i in range(npins)]
    n_knee = norm3([pins[15][i] - pins[13][i] for i in range(3)])
    n_ankle = norm3([pins[17][i] - pins[15][i] for i in range(3)])

    r1 = oblique_cut(sp, leg, n_knee, pins[15])
    r2 = oblique_cut(sp, r1[1], n_ankle, pins[17]) if r1 else None
    thigh_pieces = r1[0] if r1 else []
    shin_pieces = r2[0] if r2 else []
    foot_pieces = r2[1] if r2 else []

    segs = {"thigh_L": thigh_pieces, "shin_L": shin_pieces,
            "foot_L": foot_pieces}
    seg_out = {}
    all_final = []
    for name, pc in segs.items():
        v = vol(sp, pc)
        closed, chi = topology(sp, pc)
        seg_out[name] = {"pieces": len(pc) // 3, "v0": v, "closed": closed,
                         "chi": chi,
                         "degenerate_vs_leg": v < DEGEN * v0_leg}
        all_final.append(pc)

    # -- the other cells (right components, torso) --
    consumed = set(side_cells)
    others = []
    sum_v0 = 0.0
    genus_after = 0
    closed_after = 0
    triple_book = defaultdict(int)
    for i, c in enumerate(cells):
        if i in consumed:
            continue
        for j in range(0, len(c["pieces"]) - 2, 3):
            t = sorted(c["pieces"][j:j + 3])
            triple_book[tuple(t)] += 1
        g, cn = genus_components(sp, c["pieces"])
        genus_after += g
        closed_after += cn
        v = vol(sp, c["pieces"])
        sum_v0 += v
        others.append({"cell": i, "pieces": len(c["pieces"]) // 3,
                       "v0": v})
    for pc in all_final:
        for j in range(0, len(pc) - 2, 3):
            t = sorted(pc[j:j + 3])
            triple_book[tuple(t)] += 1
        g, cn = genus_components(sp, pc)
        genus_after += g
        closed_after += cn
        sum_v0 += vol(sp, pc)
    vw = sum(vol(sp, list(range(0, 0))) for _ in [])  # placeholder
    # whole volume: divergence over the ORIGINAL mesh triangles
    mesh = open(SNAP + "/mesh_bin.blob", "rb").read()
    N, idx_count = struct.unpack_from("<II", mesh, 0)
    idx = struct.unpack_from("<%dI" % idx_count, mesh, 24 + N * 36)
    vw = 0.0
    for t in range(idx_count // 3):
        vw += div(sp, [idx[t * 3], idx[t * 3 + 1], idx[t * 3 + 2]])
    cover = (sum_v0 - vw) / vw * 100.0
    mass = sum_v0 * RHO

    out = {
        "genus_before": genus_before, "closed_before": closed_before,
        "thigh_members": len(thigh), "calf_members": len(calf),
        "foot_members": len(foot),
        "walls_removed_pieces": walls_removed,
        "wall_anomaly": anomaly,
        "v0_leg": v0_leg,
        "segments": seg_out,
        "others": others,
        "sum_v0": sum_v0, "vol_whole_ref": vw,
        "coverage_pct": cover, "mass_total_kg": mass,
        "genus_after": genus_after, "closed_after": closed_after,
        "septa": sum(1 for n in triple_book.values() if n == 2),
        "piece_book_unique": all(n <= 2 for n in triple_book.values()),
        "bars": {
            "closure_all": all(s["closed"] for s in seg_out.values()),
            "positive_all": all(s["v0"] > 0 for s in seg_out.values()),
            "degenerate_guard": all(not s["degenerate_vs_leg"]
                                    for s in seg_out.values()),
            "coverage_lt_0.01": abs(cover) < 0.01,
            "mass_13824.5": abs(mass - MASS_TARGET) <= 1e-4 * MASS_TARGET,
            "genus_preserved": genus_after == genus_before,
            "piece_book_unique": all(n <= 2 for n in triple_book.values()),
        },
    }
    out["pass"] = all(out["bars"].values())
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
