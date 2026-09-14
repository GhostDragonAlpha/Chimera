"""classify_run.py -- classify the real monkey's triangles into CA types
(nearest measured joint), bind its vertices for travel, and post:
  /mesh_bin      the full-format monkey mesh
  /tick_classify [u32 n][u8 joint per triangle]
  /tick_vertbind [u32 n][u8 joint per vertex]
  /tick_joints   [u32 n][f32 x,y,z per joint]
Then pose/press intents drive the REAL object through the membrane tick.

// W8 (seam route 1, 2026-09-13): the vertbind generation now restricts
each vertex's pin candidates to pins of the vertex's OWN limb -- the limb
is inherited from the per-triangle classification -- and bounds the weight
of any out-of-limb fill pins. `--report` prints the before/after diagnosis
offline (no posts; run WITHOUT --report to ship the binding to a live
engine).
"""
from __future__ import annotations

import json
import struct
import sys
import time
import urllib.request
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

    verts, idx = parse_full(root / "monkey_full.bin")
    pos = verts[:, 0:3]
    centroids = pos[idx].mean(axis=1)
    nv = len(pos)

    # per-triangle CA type: nearest measured joint to the centroid
    d2t = ((centroids[:, None, :] - pins[None, :, :]) ** 2).sum(axis=2)
    tri_joint = d2t.argmin(axis=1).astype(np.uint8)

    d2v = ((pos[:, None, :] - pins[None, :, :]) ** 2).sum(axis=2)
    order_all = np.argsort(d2v, axis=1)               # all pins, nearest first

    # BEFORE (pre-W8) binding: the 3 global nearest pins. Kept ONLY as the
    # --report baseline; the shipped binding is the // W8 one below.
    order_old = order_all[:, :3]

    # // W8: SAME-LIMB PIN RESTRICTION + BOUNDED FALLOFF -------------------
    # E2 measured the seam cause: the 3-NEAREST-PINS rule flips pin sets
    # across shear bands (thigh verts bind [spine_lower, hip_L, hip_R] while
    # one ring away binds [spine_lower, hip_L, knee_L], knee weight
    # 0.17-0.26 -> a band of creases 0.5-1.0 m above the knee). Fix at the
    # source, derived from data this script already computes: a vertex's
    # candidate pins are restricted to pins whose cell group TOUCHES the
    # vertex's own limb, the limb being INHERITED from the per-triangle
    # classification above (a vertex owns its incident triangles' joints).
    # If fewer than 3 pins remain in-limb, fill from the next-nearest pins,
    # but the fill pins' COMBINED weight is capped at 0.25 -- a far pin can
    # never dominate a near one. Inverse-distance^2 shape is kept inside
    # each group (the cap rescales groups, never reorders within them).
    in_limb = np.zeros((nv, npins), dtype=bool)
    in_limb[idx.ravel(), np.repeat(tri_joint, 3)] = True

    order_new = np.empty((nv, 3), dtype=np.int64)
    w_new = np.empty((nv, 3), dtype=np.float64)
    n_fill = 0        # verts that needed out-of-limb fill pins
    n_capped = 0      # verts whose fill pins hit the 0.25 combined cap
    for v in range(nv):
        rank = order_all[v]
        limb = in_limb[v]
        chosen = [int(p) for p in rank if limb[p]][:3]
        if len(chosen) < 3:
            n_fill += 1
            for p in rank:
                if not limb[p]:
                    chosen.append(int(p))
                    if len(chosen) == 3:
                        break
        # (a vertex with no incident triangles falls through with 3 pure
        # fill pins and s_in == 0 -> plain idw2 below = the old behavior)
        d3 = d2v[v, chosen].astype(np.float64)
        raw = 1.0 / (d3 + 1e-6) ** 2
        is_in = np.fromiter((limb[p] for p in chosen), dtype=bool, count=3)
        s_in = raw[is_in].sum()
        s_out = raw[~is_in].sum()
        if s_in > 0 and s_out / (s_in + s_out) > 0.25:
            n_capped += 1
            w = np.where(is_in, raw * (0.75 / s_in), raw * (0.25 / s_out))
        else:
            w = raw / raw.sum()
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
    band_old = flip_band(key_old, edges, nv)
    band_new = flip_band(key_new, edges, nv)

    print("triangle types:", np.bincount(tri_joint, minlength=npins).tolist())

    if report:
        cnt_old = np.bincount(order_old[:, 0], minlength=npins)
        cnt_new = np.bincount(order_new[:, 0], minlength=npins)
        print("== W8 vertbind report (offline, no posts) ==")
        print(f"verts {nv}  tris {len(idx)}  pins {npins}  edges {len(edges)}")
        print("per-pin vert counts (primary pin = weight-max slot 0):")
        print("  pin  name          before  after")
        for p in range(npins):
            print(f"  {p:3d}  {names[p]:<14} {cnt_old[p]:6d}  {cnt_new[p]:6d}")
        print(f"fill verts (needed out-of-limb pins): {n_fill} "
              f"(of those, combined weight hit the 0.25 cap: {n_capped})")
        print(f"flip-band verts (3-pin set differs from a ring neighbor):")
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
