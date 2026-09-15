#!/usr/bin/env python3
"""AN2: the band COMPONENT CENSUS (window-11 diagnosis).

Pure structure — NO volumes (the deleted twin proved uncapped-sheet
divergences are meaningless; this tool only reads connectivity and
positions, which never lie). For each band (the authored cut planes
y = 0.338 / 1.903 / 3.415): split the surface, flood components via
shared quantized positions (this matched the ENGINE's own component
counts 3/1/6 at window #11 — verified twice), then dump per component:
tri count, centroid (x,y,z), y-range, and BOTH centroid estimators
(mean triangle-centroid x, and the engine's mean slot-occurrence x).
"""
import json
import struct
import sys
from collections import defaultdict

SNAP = sys.argv[1] if len(sys.argv) > 1 else ".tmp/build_tick/Release/session_snapshot"
OUT = sys.argv[2] if len(sys.argv) > 2 else \
    "docs/evidence/agent_fleet/SHIP/ONE_LIMB/band_census.json"

ANKLE_Y, KNEE_Y, HIP_Y = 0.3378, 1.9033, 3.4153   # the measured pins


def load():
    mesh = open(SNAP + "/mesh_bin.blob", "rb").read()
    N, idx_count = struct.unpack_from("<II", mesh, 0)
    verts = list(struct.unpack_from("<%df" % (N * 9), mesh, 24))
    idx = list(struct.unpack_from("<%dI" % idx_count, mesh, 24 + N * 36))
    return N, verts, idx


def split_tris(verts, idx, planes):
    tris = []
    for t in range(len(idx) // 3):
        vs = [verts[idx[t * 3 + k] * 9: idx[t * 3 + k] * 9 + 3]
              for k in range(3)]
        stack = [vs]
        while stack:
            v = stack.pop()
            hit = None
            for pl in planes:
                s = [(p[1] - pl) < 0 for p in v]
                above = [(p[1] - pl) > 0 for p in v]
                if 0 < sum(s) < 3 and any(above):
                    hit = (pl, s)
                    break
            if hit is None:
                tris.append(v)
                continue
            pl, s = hit

            def cut(P, Q):
                t = (pl - P[1]) / (Q[1] - P[1])
                return [P[k] + t * (Q[k] - P[k]) for k in range(3)]

            if sum(s) == 1:
                i0 = s.index(True)
                A = v[i0]
                B = v[(i0 + 1) % 3]
                C = v[(i0 + 2) % 3]
                Pab = cut(A, B)
                Pca = cut(C, A)
                stack.append([A, Pab, Pca])
                stack.append([Pab, B, C])
                stack.append([Pab, C, Pca])
            else:
                iC = s.index(False)
                C = v[iC]
                A = v[(iC + 1) % 3]
                B = v[(iC + 2) % 3]
                Pbc = cut(B, C)
                Pca = cut(C, A)
                stack.append([A, B, Pbc])
                stack.append([A, Pbc, Pca])
                stack.append([Pbc, C, Pca])
    return tris


def components(tris):
    parent = list(range(len(tris)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    first = {}
    for i, tri in enumerate(tris):
        for p in tri:
            k = (round(p[0] * 1e4), round(p[1] * 1e4), round(p[2] * 1e4))
            if k in first:
                ra, rb = find(first[k]), find(i)
                if ra != rb:
                    parent[ra] = rb
            else:
                first[k] = i
    groups = defaultdict(list)
    for i in range(len(tris)):
        groups[find(i)].append(i)
    return list(groups.values())


def main():
    N, verts, idx = load()
    tris = split_tris(verts, idx, [ANKLE_Y, KNEE_Y, HIP_Y])

    bands = {"feet": [], "calf": [], "thigh": [], "torso": []}
    for t in tris:
        y = (t[0][1] + t[1][1] + t[2][1]) / 3.0
        if y < ANKLE_Y:
            bands["feet"].append(t)
        elif y < KNEE_Y:
            bands["calf"].append(t)
        elif y < HIP_Y:
            bands["thigh"].append(t)
        else:
            bands["torso"].append(t)

    out = {}
    for name, tl in bands.items():
        comps = components(tl)
        rows = []
        for c in comps:
            xs = [p[0] for i in c for p in tl[i]]
            ys = [p[1] for i in c for p in tl[i]]
            zs = [p[2] for i in c for p in tl[i]]
            rows.append({
                "tris": len(c),
                "centroid_xyz": [round(sum(xs) / len(xs), 4),
                                 round(sum(ys) / len(ys), 4),
                                 round(sum(zs) / len(zs), 4)],
                "ylo": round(min(ys), 4), "yhi": round(max(ys), 4),
                "x_min": round(min(xs), 4), "x_max": round(max(xs), 4),
            })
        rows.sort(key=lambda r: -r["tris"])
        out[name] = {"n_components": len(comps), "components": rows}

    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    for name in ("feet", "calf", "thigh", "torso"):
        b = out[name]
        print("== %s: %d components" % (name, b["n_components"]))
        for r in b["components"][:8]:
            print("   tris %5d  c=%s  y[%s..%s]  x[%s..%s]" % (
                r["tris"], r["centroid_xyz"], r["ylo"], r["yhi"],
                r["x_min"], r["x_max"]))


if __name__ == "__main__":
    main()
