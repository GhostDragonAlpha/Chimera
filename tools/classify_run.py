"""classify_run.py -- classify the real monkey's triangles into CA types
(nearest measured joint), bind its vertices for travel, and post:
  /mesh_bin      the full-format monkey mesh
  /tick_classify [u32 n][u8 joint per triangle]
  /tick_vertbind [u32 n][u8 joint per vertex]
  /tick_joints   [u32 n][f32 x,y,z per joint]
Then pose/press intents drive the REAL object through the membrane tick.

// W8 (seam route 1, 2026-09-13): the vertbind generation now restricts
each vertex's pin candidates to its OWN LIMB, derived from the
per-triangle classification (no authored limb table): the vertex INHERITS
its triangles' joint, its limb is that joint's cell group plus the cell
groups that TOUCH it (edge-adjacent, sane faces only -- the sculpt's
sliver faces span the body and would wire every group to every other).
Fewer than 3 in-limb pins (chain ends: wrist, ankle, tail tip): fill from
the next-nearest pins, capped so the fill pins' COMBINED weight stays
<= 0.25 -- a far pin can never dominate a near one. Weights keep the
inverse-distance^2 law and the exact 15-byte vertbind row that
MembraneTick::load_vertbind parses (the engine consumes them RAW, so they
ship normalized to sum 1). The per-triangle classification keeps the
original float32 arithmetic, so /tick_classify bytes are unchanged.

`--report` runs OFFLINE (no posts) and prints: per-pin vert counts
before/after, the flip-band count before/after, fill/cap stats, the
duplicate-position binding-split check (duplicates must move together,
E2), and the E2 posed-surface crease metric before/after so the route's
effect is reproducible with one command. Run WITHOUT --report to ship the
binding to a live engine.

// G7 (seam route 1 verification, 2026-09-14): the W8 generation above
// was re-run independently (python tools/classify_run.py --report,
// hash-pinned 47368352d8c960eb51e4a3bf6c08c06d) and every printed
// number reproduced: flip bands 4243 -> 4117 of 18459; fill 5880, 88
// capped; creases 193 -> 180 (knee45) and 237 -> 212 (compound);
// duplicate-position splits 0 -> 0; all 28 per-pin PRIMARY counts
// identical before/after. Hard constraints re-proven against the same
// binding math: weights sum to 1 in float32 (max |sum-1| 4.5e-8), the
// deg=0 blend returns the authored rest to 4.4e-7 (E2's recorded
// bound), and the 15-byte row round-trips MembraneTick::load_vertbind
// (body 4+n*15 = 276889 bytes). Mechanism audit: the left-thigh
// population still binding hip_R fell 370 -> 165, and every survivor
// is spine_lower-INHERITED with hip_R in-limb via the touch graph
// (spine_lower touches hip_R across the centerline; hip_L does NOT
// touch hip_R -- 0 sane bridge edges), never a capped fill. No code
// changed in this pass; the W8 generation is verified as shipped.
"""
from __future__ import annotations

import json
import struct
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np


def parse_full(path: Path):
    raw = path.read_bytes()
    n, ic = struct.unpack_from("<II", raw, 0)   # ic = INDEX count (3/tri)
    verts = np.frombuffer(raw, dtype=np.float32, count=n * 9,
                          offset=24).reshape(n, 9)
    idx = np.frombuffer(raw, dtype=np.uint32, count=ic,
                        offset=24 + n * 36).reshape(-1, 3)
    return verts, idx


def vert_normal_acc(pos: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """area-weighted accumulation of face normals at each vertex."""
    f = np.cross(pos[idx][:, 1] - pos[idx][:, 0],
                 pos[idx][:, 2] - pos[idx][:, 0])
    acc = np.zeros((len(pos), 3))
    for k in range(3):
        for d in range(3):
            acc[:, d] += np.bincount(idx[:, k], weights=f[:, d],
                                     minlength=len(pos))
    return acc


def unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=1, keepdims=True)
    n[n < 1e-12] = 1.0
    return v / n


def ang(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.degrees(np.arccos(np.clip((a * b).sum(1), -1, 1)))


def posed(pos: np.ndarray, pins: np.ndarray, order: np.ndarray,
          w: np.ndarray, deg: np.ndarray) -> np.ndarray:
    """MembraneTick::apply_travel in numpy (same arithmetic path)."""
    pv = pins[order]                                   # n x 3 pins x xyz
    b = pos[:, None, :] - pv
    th = deg[order]
    c, s = np.cos(th), np.sin(th)
    return np.stack([
        (w * (b[:, :, 0] + pv[:, :, 0])).sum(1),
        (w * (b[:, :, 1] * c - b[:, :, 2] * s + pv[:, :, 1])).sum(1),
        (w * (b[:, :, 1] * s + b[:, :, 2] * c + pv[:, :, 2])).sum(1)], 1)


def pin_key(order3: np.ndarray, npins: int) -> np.ndarray:
    """one int per vertex: its SORTED 3-pin set (set equality = key equality)."""
    s = np.sort(order3.astype(np.int64), axis=1)
    return (s[:, 0] * npins + s[:, 1]) * npins + s[:, 2]


def flip_band(key: np.ndarray, edges: np.ndarray, nv: int) -> np.ndarray:
    """verts whose 3-pin set differs from at least one ring neighbor."""
    band = np.zeros(nv, dtype=bool)
    diff = key[edges[:, 0]] != key[edges[:, 1]]
    band[edges[diff].ravel()] = True
    return band


def main() -> int:
    argv = sys.argv[1:]
    report = "--report" in argv
    pos_args = [a for a in argv if a != "--report"]
    base = pos_args[0] if pos_args else "http://127.0.0.1:8107"
    root = Path(r"E:\ChimeraWork\slot-01\.tmp")
    joints = json.loads((root / "joints28.json").read_text())
    names = [j["name"] for j in joints]
    pins = np.asarray([j["J"] for j in joints], dtype=np.float32)
    npins = len(pins)
    KNEE = names.index("knee_L")
    HIP = names.index("hip_L")

    verts, idx = parse_full(root / "monkey_full.bin")
    pos = verts[:, 0:3]                       # float32: original arithmetic
    idx = idx.astype(np.int64)
    nv = len(pos)
    centroids = pos[idx].mean(axis=1)

    # per-triangle CA type: nearest measured joint to the centroid
    # (float32, byte-identical to the pre-W8 classification)
    d2t = ((centroids[:, None, :] - pins[None, :, :]) ** 2).sum(axis=2)
    tri_joint = d2t.argmin(axis=1).astype(np.uint8)
    sane = 0.5 * np.linalg.norm(np.cross(pos[idx][:, 1] - pos[idx][:, 0],
                                         pos[idx][:, 2] - pos[idx][:, 0]),
                                axis=1) > 1e-8   # E2: slivers span the body

    # cell-group TOUCH graph: joints whose sane cells share a mesh edge
    edge_faces = defaultdict(list)
    for t in range(len(idx)):
        a, b, c = idx[t]
        for e in ((a, b), (b, c), (c, a)):
            edge_faces[(min(e), max(e))].append(t)
    touches = defaultdict(set)
    for e, ts in edge_faces.items():
        if len(ts) == 2 and sane[ts[0]] and sane[ts[1]]:
            x, y = int(tri_joint[ts[0]]), int(tri_joint[ts[1]])
            if x != y:
                touches[x].add(y)
                touches[y].add(x)

    # the vertex INHERITS its triangles' joint (majority vote; ties broken
    # by the nearer pin). Its limb = that joint's cell group + touchers.
    votes = np.zeros((nv, npins), np.int32)
    votes[idx.ravel(), np.repeat(tri_joint, 3)] = 1
    tied = votes == votes.max(axis=1, keepdims=True)
    d2v = ((pos[:, None, :] - pins[None, :, :]) ** 2).sum(axis=2)
    vjoint = np.where(tied, d2v, np.inf).argmin(axis=1)
    limb_of = [{j} | touches[j] for j in range(npins)]

    order_all = np.argsort(d2v, axis=1)          # all pins, nearest first

    # BEFORE (pre-W8) binding: the 3 global nearest pins. Kept ONLY as the
    # --report baseline; the shipped binding is the // W8 one below.
    order_old = order_all[:, :3]
    d3o = np.take_along_axis(d2v, order_old, axis=1)
    w_old = 1.0 / (d3o + 1e-6) ** 2
    w_old /= w_old.sum(axis=1, keepdims=True)

    # // W8: SAME-LIMB PIN RESTRICTION + BOUNDED FALLOFF -------------------
    # E2 measured the seam cause at the joints: the 3-NEAREST-PINS rule
    # races wrong-limb pins into the sets (thigh verts bound hip_R while
    # one ring away binds knee_L at 0.17-0.26 -> shear/crease rings).
    # Candidates are now restricted to the vertex's own limb; the idw2 law
    # is unchanged inside the limb; out-of-limb FILL pins (only at chain
    # ends) carry at most 0.25 COMBINED weight, split by idw2 proportion.
    order_new = np.empty((nv, 3), dtype=np.int64)
    w_new = np.empty((nv, 3), dtype=np.float64)
    n_fill = 0        # verts that needed out-of-limb fill pins
    n_capped = 0      # verts whose fill pins hit the 0.25 combined cap
    for v in range(nv):
        limb = limb_of[vjoint[v]]
        rank = order_all[v]
        chosen = [int(p) for p in rank if p in limb][:3]
        if len(chosen) < 3:
            n_fill += 1
            for p in rank:
                if p not in limb:
                    chosen.append(int(p))
                    if len(chosen) == 3:
                        break
        d3 = d2v[v, chosen]
        raw = 1.0 / (d3 + 1e-6) ** 2
        is_in = np.fromiter((p in limb for p in chosen), dtype=bool, count=3)
        raw64 = raw.astype(np.float64)
        s_in = raw64[is_in].sum()
        s_out = raw64[~is_in].sum()
        if s_in > 0 and s_out / (s_in + s_out) > 0.25:
            n_capped += 1
            w = np.where(is_in, raw64 * (0.75 / s_in), raw64 * (0.25 / s_out))
        else:
            w = raw64 / raw64.sum()
        order_new[v] = chosen
        w_new[v] = w
    w_new = w_new.astype(np.float32)
    # sums stay 1.0 to float32 exactly like the old code: the engine
    # (MembraneTick::apply_travel) consumes the weights RAW.

    # -- report data: ring edges, flip bands, per-pin counts ---------------
    e = np.concatenate([idx[:, [0, 1]], idx[:, [1, 2]], idx[:, [2, 0]]])
    edges = np.unique(np.sort(e, axis=1), axis=0)
    key_old = pin_key(order_old, npins)
    key_new = pin_key(order_new, npins)

    print("triangle types:", np.bincount(tri_joint, minlength=npins).tolist())

    if report:
        cnt_old = np.bincount(order_old[:, 0], minlength=npins)
        cnt_new = np.bincount(order_new[:, 0], minlength=npins)
        band_old = flip_band(key_old, edges, nv)
        band_new = flip_band(key_new, edges, nv)
        print("== W8 vertbind report (offline, no posts) ==")
        print(f"verts {nv}  tris {len(idx)}  pins {npins}  edges {len(edges)}")
        print("per-pin vert counts (primary pin = weight-max slot 0):")
        print("  pin  name          before  after")
        for p in range(npins):
            print(f"  {p:3d}  {names[p]:<14} {cnt_old[p]:6d}  {cnt_new[p]:6d}")
        print(f"fill verts (needed out-of-limb pins): {n_fill} "
              f"(of those, combined weight hit the 0.25 cap: {n_capped})")
        print("flip-band verts (3-pin set differs from a ring neighbor):")
        print(f"  before: {int(band_old.sum())} / {nv}")
        print(f"  after : {int(band_new.sum())} / {nv}")
        # duplicates must keep identical bindings (E2: they move together)
        _, inv = np.unique(pos, axis=0, return_inverse=True)
        gsize = npins ** 3

        def split_groups(key):
            first = np.unique(inv.astype(np.int64) * gsize + key) // gsize
            _, c = np.unique(first, return_counts=True)
            return int((c > 1).sum())
        print(f"duplicate-position groups with split bindings: "
              f"before {split_groups(key_old)}, after {split_groups(key_new)}")

        # E2 posed-surface metric, before vs after (method of
        # .tmp/e2_seam_analysis4.py: interior sane edges with midpoint
        # within 1.5 m of knee_L; introduced vertex-normal delta at
        # knee45 and hip20+knee45; count > 10 deg).
        interior = {e_: fs for e_, fs in edge_faces.items() if len(fs) == 2}
        ef = np.array(list(interior.keys()))
        ft = np.array([interior[(a, b)] for a, b in ef])
        edge_sane = sane[ft[:, 0]] & sane[ft[:, 1]]
        mid = (pos[ef[:, 0]].astype(np.float64)
               + pos[ef[:, 1]].astype(np.float64)) / 2
        region = (np.linalg.norm(mid - pins.astype(np.float64)[KNEE],
                                 axis=1) < 1.5) & edge_sane
        pos64 = pos.astype(np.float64)
        pins64 = pins.astype(np.float64)
        nd0 = ang(unit(vert_normal_acc(pos64, idx))[ef[:, 0]],
                  unit(vert_normal_acc(pos64, idx))[ef[:, 1]])
        print("posed-surface crease check (E2 knee region, >10 deg edges):")
        for label, order, w in (("before", order_old, w_old.astype(np.float64)),
                                ("after ", order_new, w_new.astype(np.float64))):
            line = []
            for pose, degv in (("knee45", {KNEE: 45.0}),
                               ("hip20+knee45", {KNEE: 45.0, HIP: 20.0})):
                deg = np.zeros(npins)
                for j, d in degv.items():
                    deg[j] = np.radians(d)
                acc = unit(vert_normal_acc(posed(pos64, pins64, order, w, deg),
                                           idx))
                intro = np.maximum(0, ang(acc[ef[:, 0]], acc[ef[:, 1]]) - nd0)
                line.append(f"{pose}: {int((region & (intro > 10)).sum())} "
                            f"(max {intro[region].max():.1f} deg)")
            print(f"  {label}: " + " | ".join(line))
        return 0

    def post(path: str, body: bytes, timeout: int = 60) -> str:
        req = urllib.request.Request(base + path, data=body, method="POST",
                                     headers={"Content-Type":
                                              "application/octet-stream"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode()[:60]

    mesh = (root / "monkey_full.bin").read_bytes()
    print("mesh:", post("/mesh_bin", mesh, timeout=120))
    print("classify:", post("/tick_classify",
                            struct.pack("<I", len(tri_joint))
                            + tri_joint.tobytes()))
    # travel binding: 3 pin indices (u8) + 3 weights (f32) per vertex --
    # the exact 15-byte row MembraneTick::load_vertbind parses
    vb = np.empty(nv * 15, dtype=np.uint8)
    for v in range(nv):
        row = np.empty(15, dtype=np.uint8)
        row[0:3] = order_new[v].astype(np.uint8)
        row[3:15] = np.frombuffer(w_new[v].tobytes(), dtype=np.uint8)
        vb[v * 15:(v + 1) * 15] = row
    print("vertbind:", post("/tick_vertbind",
                            struct.pack("<I", nv) + vb.tobytes(),
                            timeout=120))
    pins_body = struct.pack("<I", npins) + np.ascontiguousarray(pins).tobytes()
    print("joints:", post("/tick_joints", pins_body))
    return 0


if __name__ == "__main__":
    sys.exit(main())
