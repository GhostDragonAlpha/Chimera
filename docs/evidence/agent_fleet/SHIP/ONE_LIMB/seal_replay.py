#!/usr/bin/env python3
"""AN2: EXACT offline replay of resolve_band + cell_cx from the engine's
own seal-state blob (the same bytes the engine restored at boot).

The blob carries the tree as piece->slot lists; the mesh blob carries
positions. No quantization, no proxies: this is the engine's own data
run through the engine's own grouping (containment in the band window)
and the engine's own centroid estimator (mean slot-occurrence x).
"""
import json
import struct
import sys

SNAP = sys.argv[1] if len(sys.argv) > 1 else ".tmp/build_tick/Release/session_snapshot"
OUT = sys.argv[2] if len(sys.argv) > 2 else \
    "docs/evidence/agent_fleet/SHIP/ONE_LIMB/seal_replay.json"

ANKLE_Y, KNEE_Y, HIP_Y = 0.3378, 1.9033, 3.4153
TOL = 2e-3
SEAL_MAGIC = 0x31534553  # 'SEL1'


def load_mesh():
    mesh = open(SNAP + "/mesh_bin.blob", "rb").read()
    N, idx_count = struct.unpack_from("<II", mesh, 0)
    verts = list(struct.unpack_from("<%df" % (N * 9), mesh, 24))
    return N, verts


def load_seal_state():
    b = open(SNAP + "/tick_seal_state.blob", "rb").read()
    magic, nv, n_cuts = struct.unpack_from("<III", b, 0)
    assert magic == SEAL_MAGIC, "bad seal magic"
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
        (deg,) = struct.unpack_from("<B", b, off)
        off += 1
        cells.append({"pieces": pieces, "v0": v0, "vol": vol, "p": p,
                      "caps": caps, "ylo": ylo, "yhi": yhi,
                      "degenerate": bool(deg)})
    return nv, cuts, cells


def main():
    nv, verts = load_mesh()
    snv, cuts, cells = load_seal_state()
    assert nv == snv, "seal blob nv %d != mesh %d" % (snv, nv)

    # rest geometry: the engine's rest9 (angles 0 = authored positions)
    # and cutrest (blends over rest9) -- exactly rest_geometry_locked_.
    cutrest = []
    for (n, vs, ws) in cuts:
        acc = [0.0, 0.0, 0.0]
        for i in range(n):
            for d in range(3):
                acc[d] += ws[i] * verts[vs[i] * 9 + d]
        cutrest.extend(acc)

    def slot_pos(s):
        if s < nv:
            return verts[s * 9: s * 9 + 3]
        return cutrest[(s - nv) * 3: (s - nv) * 3 + 3]

    # THE ENGINE'S cell_cx: mean slot-occurrence x over the cell's pieces
    def cell_cx(cell):
        sx = 0.0
        sw = 0
        for s in cell["pieces"]:
            sx += slot_pos(s)[0]
            sw += 1
        return (sx / sw) if sw else 0.0

    def cell_cy(cell):
        sy = 0.0
        sw = 0
        for s in cell["pieces"]:
            sy += slot_pos(s)[1]
            sw += 1
        return (sy / sw) if sw else 0.0

    # THE SPLIT: flood the cell's pieces through shared slots (exact
    # split_locked_ semantics), components in the engine's map order
    # (sorted by first-seen root -- we approximate with sorted roots).
    def split_components(cell_idx):
        pieces = cells[cell_idx]["pieces"]
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
            comps.setdefault(find(p), []).extend(
                pieces[p * 3: p * 3 + 3])
        return [comps[r] for r in sorted(comps)]

    report = {"n_cells": len(cells), "cells": []}
    for i, c in enumerate(cells):
        report["cells"].append({
            "cell": i, "pieces": len(c["pieces"]) // 3,
            "v0": c["v0"], "ylo": c["ylo"], "yhi": c["yhi"],
            "cell_cx": round(cell_cx(c), 4),
        })

    # THE CONTAINMENT GROUPING (resolve_band's members, unsplit tree)
    def members(has_lo, lo, hi):
        out = []
        for i, c in enumerate(cells):
            if has_lo and c["ylo"] < lo - TOL:
                continue
            if c["yhi"] > hi + TOL:
                continue
            out.append(i)
        return out

    thigh_m = members(True, KNEE_Y, HIP_Y)
    calf_m = members(True, ANKLE_Y, KNEE_Y)
    feet_m = members(False, 0.0, ANKLE_Y)
    replay = {}
    for name, mem, has_lo, lo, hi in (
            ("thigh", thigh_m, True, KNEE_Y, HIP_Y),
            ("calf", calf_m, True, ANKLE_Y, KNEE_Y),
            ("feet", feet_m, False, 0.0, ANKLE_Y)):
        rows = []
        grew_log = []
        m = list(mem)
        for guard in range(8):
            grew = False
            for idx_c in m:
                comps = split_components(idx_c)
                if len(comps) < 2:
                    continue          # nothing to split
                # the split publishes daughter 0 in place, appends rest
                new_cells = []
                for pi, comp in enumerate(comps):
                    nc = {"pieces": comp}
                    v = 0.0
                    lo_y, hi_y = 1e30, -1e30
                    for s in comp:
                        p = slot_pos(s)
                        v += 0  # volume not needed for the grouping
                        lo_y = min(lo_y, p[1])
                        hi_y = max(hi_y, p[1])
                    nc["ylo"] = lo_y
                    nc["yhi"] = hi_y
                    nc["cell_cx"] = None
                    new_cells.append(nc)
                # emulate: daughter 0 replaces idx_c; daughters 1.. append
                cells[idx_c] = new_cells[0]
                cells.extend(new_cells[1:])
                grew = True
                grew_log.append({"split_cell": idx_c,
                                 "components": len(comps)})
                break
            if not grew:
                break
            # regroup
            m = members(has_lo, lo, hi)
        for idx_c in m:
            c = cells[idx_c]
            rows.append({
                "cell": idx_c,
                "tris": len(c["pieces"]) // 3,
                "cell_cx": round(cell_cx(c), 4),
                "mean_y": round(cell_cy(c), 4),
                "ylo": round(c["ylo"], 4), "yhi": round(c["yhi"], 4),
            })
        rows.sort(key=lambda r: -r["tris"])
        n_left = sum(1 for r in rows if r["cell_cx"] >= 0)
        replay[name] = {"members": len(rows), "left": n_left,
                        "splits": grew_log, "components": rows}

    out = {"report": report, "replay": replay}
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(replay, indent=1))


if __name__ == "__main__":
    main()
