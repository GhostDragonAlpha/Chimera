#!/usr/bin/env python3
"""RIG TEDDY — add ARM chains to a vox fossil and face the walk direction.

The claim (Rule 0): an imported body is DATA, and rigging is a DATA
operation — the arms already exist as geometry; the rigger only TRACES the
chain that was always there (shoulder -> hand through the arm tube's
centerline) and rotates the whole body so it FACES the gait's travel axis.
Falsifier: the traced chain must be face-connected, lie entirely inside the
arm slab, and end within 2 cells of the measured hand centroid — otherwise
the trace (not the body) is wrong.

Measurements this tool is built on (teddy_stand_s1.cells, 2026-08-17):
  - the per-y extent profile: y -14..1 torso+legs (x -4..6), y 2..6 the ARM
    slab (x -11..11, z -5..5), y 7..14 the head.
  - the arms are straight horizontal tubes along +/-x; hands at |x| >= 10.
  - the face is -z (the chin/jaw juts to z=-7 at y=7 and tapers with height);
    the gait travels +x, so the body must rotate: new = (-z, y, x) puts the
    face at +x (east) and the arms along +/-z (sideways, where arms belong).
Rotation is a rigid isometry: the shape-trained support margin is preserved.

Emits genomes/teddy_stand_r1.cells: same CELLS (rotated), CHAINS = the 4
grown leg chains (rotated) + 2 traced arm chains. fore/side are derived from
each chain's position relative to the COM. Run from ChimeraEngine/native/.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "genomes" / (sys.argv[1] if len(sys.argv) > 1 else "teddy_stand_s1.cells")
DST = HERE / "genomes" / (sys.argv[2] if len(sys.argv) > 2 else "teddy_stand_r1.cells")

D6 = [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]

def read_cells(p):
    cells, chains = [], []
    mode = None
    for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#")[0].strip()
        if not line:
            continue
        t = line.split()
        if t[0] == "CELLS":
            mode = "cells"; continue
        if t[0] == "CHAINS":
            mode = ("chains", int(t[1])); continue
        if mode == "cells":
            cells.append(tuple(map(int, t)))
        elif mode and mode[0] == "chains":
            if len(t) == 3 and len(chains) < mode[1] * 2:
                # header (fore side len) vs cell line: a header's 3rd number
                # is the COUNT and is followed by that many cells; detect by
                # trying the state machine instead
                pass
            chains.append(tuple(map(int, t)))
    # chains list mixes headers and cells; reparse with a cursor
    return cells, chains

def parse(p):
    lines = []
    for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#")[0].strip()
        if line:
            lines.append(line.split())
    i = 0
    assert lines[i][0] == "CELLS"; n = int(lines[i][1]); i += 1
    cells = [tuple(map(int, lines[i + j])) for j in range(n)]; i += n
    assert lines[i][0] == "CHAINS"; m = int(lines[i][1]); i += 1
    chains = []
    for _ in range(m):
        fore, side, cnt = map(int, lines[i]); i += 1
        path = [tuple(map(int, lines[i + j])) for j in range(cnt)]; i += cnt
        chains.append({"fore": fore, "side": side, "path": path})
    return cells, chains

def trace_arm(occ, s):
    """Greedy centerline trace through the arm slab, root -> tip.
    Slab: y in 3..6, x*s >= 5 (beyond the torso edge, below the head)."""
    slab = {c for c in occ if 3 <= c[1] <= 6 and c[0] * s >= 5}
    assert slab, f"no arm slab on side {s}"
    zs = [c[2] for c in slab]; ys = [c[1] for c in slab]
    zc, yc = sum(zs) / len(zs), sum(ys) / len(ys)
    root = min(slab, key=lambda c: (c[0] * s, abs(c[1] - yc) + abs(c[2] - zc)))
    tip = max(slab, key=lambda c: (c[0] * s, -abs(c[1] - yc) - abs(c[2] - zc)))
    # axis for tie-breaks
    ax = [tip[0] - root[0], tip[1] - root[1], tip[2] - root[2]]
    alen = max(1e-9, sum(a * a for a in ax) ** 0.5)
    def d_axis(c):
        v = [c[0] - root[0], c[1] - root[1], c[2] - root[2]]
        t = sum(v[k] * ax[k] for k in range(3)) / (alen * alen)
        px = [root[k] + t * ax[k] for k in range(3)]
        return sum((c[k] - px[k]) ** 2 for k in range(3))
    path = [root]; cur = root; seen = {root}
    while cur != tip:
        nxt = None
        for d in D6:
            c = (cur[0] + d[0], cur[1] + d[1], cur[2] + d[2])
            if c in slab and c not in seen:
                key = (c[0] * s, -d_axis(c))
                if nxt is None or key > nxt[0]:
                    nxt = (key, c)
        if nxt is None:
            raise SystemExit(f"trace stalled at {cur} side {s} — falsifier fired")
        cur = nxt[1]; seen.add(cur); path.append(cur)
    # falsifier: connected (by construction), inside slab (by construction),
    # and the path end is the measured hand
    hand = [c for c in slab if c[0] * s >= 10]
    hx = sum(c[0] for c in hand) / len(hand)
    assert abs(path[-1][0] - hx) <= 2, f"tip {path[-1]} misses hand x {hx}"
    return {"fore": 0, "side": s, "path": path}

def main():
    cells, chains = parse(SRC)
    occ = set(cells)
    arms = [trace_arm(occ, -1), trace_arm(occ, +1)]
    com = [sum(c[k] for c in cells) / len(cells) for k in range(3)]
    # rotate: new = (-z, y, x) — face -z -> +x (east), arms +/-x -> +/-z
    def rot(c):
        return (-c[2], c[1], c[0])
    cells_r = [rot(c) for c in cells]
    all_ch = chains + arms
    out = []
    out.append("# teddy_stand_r1.cells — RIGGED standing teddy (rig_teddy.py)")
    out.append("# teddy_stand_s1 + 2 traced arm chains, rotated to face +x")
    out.append("# (the walk direction). Legs: chains 0-3 (grown). Arms:")
    out.append("# chains 4-5 (traced centerlines, root=shoulder, tip=hand).")
    out.append(f"CELLS {len(cells_r)}")
    out += [f"{c[0]} {c[1]} {c[2]}" for c in cells_r]
    out.append(f"CHAINS {len(all_ch)}")
    for ch in all_ch:
        path_r = [rot(c) for c in ch["path"]]
        cx = sum(c[0] for c in path_r) / len(path_r)
        cz = sum(c[2] for c in path_r) / len(path_r)
        comz_r = -com[2]  # rotated COM z = -old com x... compute directly:
        com_r = (-com[2], com[1], com[0])
        fore = 1 if cx > com_r[0] else 0
        side = 1 if cz > com_r[2] else -1
        out.append(f"{fore} {side} {len(path_r)}")
        out += [f"{c[0]} {c[1]} {c[2]}" for c in path_r]
    DST.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {DST.name}: {len(cells_r)} cells, {len(all_ch)} chains")
    for i, ch in enumerate(all_ch):
        p0 = ch["path"][0]; p1 = ch["path"][-1]
        print(f"  chain {i}: len {len(ch['path'])} root {rot(p0)} tip {rot(p1)}")

if __name__ == "__main__":
    main()
