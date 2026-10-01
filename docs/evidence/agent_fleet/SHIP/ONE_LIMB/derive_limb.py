#!/usr/bin/env python3
"""AN2 ONE-LIMB: the connectivity derivation table (prereg P1/P2/P3).

Reads the engine's own snapshot blobs (the same bytes the engine boots
from) and derives the limb pin chain from mesh-edge adjacency of
dominant-binding labels -- NOT from pin names, NOT from horizontal
bands, NOT from Euclidean nearest-pin. This is the offline twin of the
engine-side derivation in MembraneTick::limb_partition (the same law,
run against the same measured data, so the table exists before the
build window).

Blob formats (little-endian), from main.cpp:
  mesh_bin.blob     [u32 N][u32 idxCount][f32 cam*4][f32 verts N*9][u32 idx]
  tick_vertbind.blob [u32 n][n * (u8 pin0..2, f32 w0..2)]   (15 B/vertex)
  tick_joints.blob   [u32 n][n * (f32 x, y, z)]             (12 B/pin)
"""
import json
import struct
import sys
from collections import Counter

SNAP = sys.argv[1] if len(sys.argv) > 1 else ".tmp/build_tick/Release/session_snapshot"
OUT = sys.argv[2] if len(sys.argv) > 2 else \
    "docs/evidence/agent_fleet/SHIP/ONE_LIMB/derivation_table.json"

NAMES = ["neck", "jaw", "spine_upper", "spine_mid", "spine_lower",
         "tail_base", "tail_mid", "shoulder_L", "shoulder_R",
         "elbow_L", "elbow_R", "wrist_L", "wrist_R",
         "hip_L", "hip_R", "knee_L", "knee_R", "ankle_L", "ankle_R",
         "tail_tip", "ear_L", "ear_R", "lid_L", "lid_R",
         "brow_L", "brow_R", "mouth_L", "mouth_R"]


def read_blob(path):
    with open(path, "rb") as f:
        return f.read()


def main():
    mesh = read_blob(SNAP + "/mesh_bin.blob")
    vb = read_blob(SNAP + "/tick_vertbind.blob")
    jp = read_blob(SNAP + "/tick_joints.blob")

    N, idx_count = struct.unpack_from("<II", mesh, 0)
    verts = struct.unpack_from("<%df" % (N * 9), mesh, 24)
    idx = struct.unpack_from("<%dI" % idx_count, mesh, 24 + N * 36)

    n_vb = struct.unpack_from("<I", vb, 0)[0]
    assert n_vb == N, "vertbind vertex count %d != mesh %d" % (n_vb, N)
    dom = [0] * N
    pop = Counter()
    for v in range(N):
        off = 4 + v * 15
        pins = struct.unpack_from("<3B", vb, off)
        ws = struct.unpack_from("<3f", vb, off + 3)
        best = max(range(3), key=lambda k: ws[k])
        d = pins[best]
        dom[v] = d
        pop[d] += 1

    n_pins = struct.unpack_from("<I", jp, 0)[0]
    pins = [struct.unpack_from("<3f", jp, 4 + i * 12) for i in range(n_pins)]

    # adjacency: crossing mesh edges between dominant-pin regions
    adj = Counter()
    for t in range(idx_count // 3):
        tri = idx[t * 3:t * 3 + 3]
        for k in range(3):
            a, b = tri[k], tri[(k + 1) % 3]
            if dom[a] != dom[b]:
                key = (min(dom[a], dom[b]), max(dom[a], dom[b]))
                adj[key] += 1

    # the adjacency floor: 1% of the smaller pin's population (prereg P1)
    def adj_count(p, q):
        return adj.get((min(p, q), max(p, q)), 0)

    def adjacent(p, q):
        m = min(pop[p], pop[q])
        return m > 0 and adj_count(p, q) >= 0.01 * m

    HIP, KNEE, ANKLE = 13, 15, 17
    # derive knee: hip's strongest adjacent pin
    best, d_knee = 0, -1
    for q in range(n_pins):
        if q == HIP or pop[q] == 0 or not adjacent(HIP, q):
            continue
        c = adj_count(HIP, q)
        if c > best:
            best, d_knee = c, q
    best, d_ankle = 0, -1
    for q in range(n_pins):
        if q in (HIP, d_knee) or pop[q] == 0 or not adjacent(d_knee, q):
            continue
        c = adj_count(d_knee, q)
        if c > best:
            best, d_ankle = c, q

    chain_ok = (d_knee == KNEE and d_ankle == ANKLE
                and adjacent(HIP, KNEE) and adjacent(KNEE, ANKLE)
                and not adjacent(HIP, ANKLE))

    # seed-vs-wall preview (P2/P3): plane through knee, normal hip->knee;
    # plane through ankle, normal knee->ankle.
    def sub(a, b):
        return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

    def norm(a):
        L = sum(x * x for x in a) ** 0.5
        return (a[0] / L, a[1] / L, a[2] / L)

    def dot(a, b):
        return sum(x * y for x, y in zip(a, b))

    n_knee = norm(sub(pins[KNEE], pins[HIP]))
    n_ankle = norm(sub(pins[ANKLE], pins[KNEE]))

    def pd(nrm, pt, v):
        p = verts[v * 9:v * 9 + 3]
        return dot(nrm, (p[0] - pt[0], p[1] - pt[1], p[2] - pt[2]))

    seed_tot = [0, 0, 0]
    seed_ok = [0, 0, 0]
    seg_verts = [0, 0, 0]
    for v in range(N):
        d = dom[v]
        if d == HIP:
            i = 0
        elif d == KNEE:
            i = 1
        elif d == ANKLE:
            i = 2
        else:
            continue
        seed_tot[i] += 1
        thigh_side = pd(n_knee, pins[KNEE], v) < 0
        foot_side = (not thigh_side) and pd(n_ankle, pins[ANKLE], v) >= 0
        wall = 0 if thigh_side else (2 if foot_side else 1)
        seg_verts[wall] += 1
        if wall == i:
            seed_ok[i] += 1

    table = {
        "source": "session_snapshot blobs (mesh_bin, tick_vertbind, tick_joints)",
        "mesh": {"N": N, "tris": idx_count // 3},
        "pin_populations": {NAMES[i] if i < len(NAMES) else str(i):
                            pop.get(i, 0) for i in range(n_pins)
                            if pop.get(i, 0) > 0},
        "chain": {
            "derived": [HIP, d_knee, d_ankle],
            "pinned": [HIP, KNEE, ANKLE],
            "matches": chain_ok,
            "adj_hip_knee": adj_count(HIP, KNEE),
            "adj_knee_ankle": adj_count(KNEE, ANKLE),
            "adj_hip_ankle": adj_count(HIP, ANKLE),
            "floor_rule": "adjacent iff crossing_edges >= 1% of min(pop)",
        },
        "leg_adjacency_detail": {
            "%s-%s" % (NAMES[a] if a < len(NAMES) else a,
                       NAMES[b] if b < len(NAMES) else b): c
            for (a, b), c in sorted(adj.items())
            if a in (HIP, KNEE, ANKLE) or b in (HIP, KNEE, ANKLE)
        },
        "seed_vs_wall": {
            "thigh(hip-dominant)": {"n": seed_tot[0], "ok": seed_ok[0]},
            "shin(knee-dominant)": {"n": seed_tot[1], "ok": seed_ok[1]},
            "foot(ankle-dominant)": {"n": seed_tot[2], "ok": seed_ok[2]},
            "all": {"n": sum(seed_tot), "ok": sum(seed_ok),
                    "frac": (sum(seed_ok) / sum(seed_tot)) if sum(seed_tot) else 0},
        },
        "wall_sided_verts": {"thigh": seg_verts[0], "shin": seg_verts[1],
                             "foot": seg_verts[2]},
        "verdict": {
            "P1_chain": "PASS" if chain_ok else "FALSIFIED",
            "P2_P3_agreement_bar_90pct":
                "PASS" if sum(seed_tot) and sum(seed_ok) / sum(seed_tot) > 0.90
                else "FALSIFIED",
        },
    }
    with open(OUT, "w") as f:
        json.dump(table, f, indent=1)
    print(json.dumps(table["chain"], indent=1))
    print(json.dumps(table["seed_vs_wall"], indent=1))
    print(json.dumps(table["verdict"], indent=1))


if __name__ == "__main__":
    main()
