#!/usr/bin/env python3
"""SHAPE TRAINER — the pre-movement gate of the construction order.

Law (operator, 2026-08-16): shape is trained physically correct BEFORE any
movement training. Physical correctness is measured, not vibes:
  1. paws coplanar on the ground plane
  2. COM ground projection inside the paw support polygon with margin >= 1
     cell (one lattice step of discretization slack — sub-cell stability is
     unrepresentable on the CA substrate, so 1 cell is the derived bound)
  3. the body stays the imported scan — the trainable DOF is SUPPORT
     PLACEMENT: grow new leg pillars from the torso underside down to the
     ground (adding voxels, the CA-native edit). Never trims the scan.

Measured motivation (teddy.cells, pre-training): COM projection (0.37, 0.29)
vs paw hull x in [2,4], z in [0,2] — margin ZERO, the doll tips. And no other
ground-touching columns exist, so re-rigging alone cannot fix it.

Emits genomes/teddy_s1.cells: identical CELLS plus the grown pillars, CHAINS
= original 6 + grown legs (each with fore/side derived from its position
relative to the COM). Run from ChimeraEngine/native/.
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = sys.argv[1] if len(sys.argv) > 1 else "teddy"   # T9: stem param —
SRC = HERE / "genomes" / f"{STEM}.cells"               # teddy stays frozen
DST = HERE / "genomes" / f"{STEM}_s1.cells"
MARGIN_REQ = 1.0          # derived: one lattice step of discretization slack
D6 = [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]

def load(path):
    lines = [l.split('#')[0].split() for l in open(path)]
    lines = [l for l in lines if l]
    assert lines[0][0] == 'CELLS'
    n = int(lines[0][1])
    cells = [tuple(map(int, lines[1 + j])) for j in range(n)]
    i = 1 + n
    assert lines[i][0] == 'CHAINS'
    m = int(lines[i][1]); i += 1
    chains = []
    for _ in range(m):
        fore, side, nx = map(int, lines[i]); i += 1
        path = [tuple(map(int, lines[i + k])) for k in range(nx)]
        i += nx
        chains.append((fore, side, path))
    return cells, chains

def hull2(ps):
    ps = sorted(set(ps))
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo = []
    for p in ps:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    hi = []
    for p in reversed(ps):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0: hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]

def margin(px, pz, H):
    """inside? and min signed distance to any hull edge (CCW hull)."""
    best = 1e9
    for a, b in zip(H, H[1:] + H[:1]):
        ex, ey = b[0]-a[0], b[1]-a[1]
        L = (ex*ex + ey*ey) ** .5
        d = (ex*(pz-a[1]) - ey*(px-a[0])) / L   # signed: >0 = left of edge
        best = min(best, d)
    return best            # negative = outside (hull from hull2 is CCW)

def instrument(cells, chains, label):
    n = len(cells)
    gy = min(c[1] for c in cells)
    cx = sum(c[0] for c in cells) / n
    cz = sum(c[2] for c in cells) / n
    paws = [c[2][-1] for c in chains]
    coplanar = all(p[1] == gy for p in paws)
    H = hull2([(p[0], p[2]) for p in paws])
    m = margin(cx, cz, H)
    print(f"[{label}] cells={n} legs={len(chains)} COM=({cx:.3f},{cz:.3f}) "
          f"hull={H} coplanar={coplanar} margin={m:.3f} cells")
    return dict(com=(cx, cz), hull=H, coplanar=coplanar, margin=m, gy=gy)

def main():
    cells, chains = load(SRC)
    base = instrument(cells, chains, "pre-training")
    body = set(cells)
    gy = base["gy"]

    # buildable support positions: any (x,z) with a torso cell above ground
    # and no existing ground run (the pillar fills lowestTorsoCell..gy)
    xz = {}
    for c in body:
        if c[1] > gy:
            k = (c[0], c[2])
            xz[k] = min(xz.get(k, 999), c[1])
    taken = {(c[2][-1][0], c[2][-1][2]) for c in chains}
    candidates = {k: v for k, v in xz.items() if k not in taken}

    # greedy: add the pillar that most increases the COM's hull margin,
    # until margin >= MARGIN_REQ. The COM MOVES as pillar mass is added —
    # recompute every round (the pillar's own mass counts).
    grown = []
    cur_cells = list(cells)
    cur_chains = list(chains)
    while True:
        st = instrument(cur_cells, cur_chains, f"round {len(grown)}")
        if st["coplanar"] and st["margin"] >= MARGIN_REQ:
            break
        best = None
        for (px, pz), topy in candidates.items():
            pillar = [(px, y, pz) for y in range(gy, topy)]
            trial_cells = cur_cells + pillar
            trial_paws = [c[2][-1] for c in cur_chains] + [(px, gy, pz)]
            n2 = len(trial_cells)
            cx2 = sum(c[0] for c in trial_cells) / n2
            cz2 = sum(c[2] for c in trial_cells) / n2
            m2 = margin(cx2, cz2, hull2([(p[0], p[2]) for p in trial_paws]))
            if best is None or m2 > best[0]:
                best = (m2, px, pz, topy, pillar)
        if best is None or best[0] <= st["margin"]:
            print("STALL: no candidate improves the margin — CASE B, report it")
            sys.exit(2)
        m2, px, pz, topy, pillar = best
        del candidates[(px, pz)]
        cur_cells = cur_cells + pillar
        cx_now = sum(c[0] for c in cur_cells) / len(cur_cells)
        cz_now = sum(c[2] for c in cur_cells) / len(cur_cells)
        fore = 1 if px > cx_now else 0
        side = 1 if pz > cz_now else -1
        path = [(px, y, pz) for y in range(topy, gy - 1, -1)]   # hip->paw
        cur_chains.append((fore, side, path))
        grown.append(dict(pos=[px, pz], top=topy, cells=len(pillar),
                          marginAfter=m2))
        print(f"  grow pillar at ({px},{pz}) top y={topy} len={len(pillar)} "
              f"-> margin {m2:.3f}")

    final = instrument(cur_cells, cur_chains, "TRAINED")
    ok = final["coplanar"] and final["margin"] >= MARGIN_REQ
    # the grown pillars must not disconnect anything they pass through, and
    # the union must be one face-connected component
    S = set(cur_cells)
    seen = {next(iter(S))}; stack = list(seen)
    while stack:
        c = stack.pop()
        for d in D6:
            q = (c[0]+d[0], c[1]+d[1], c[2]+d[2])
            if q in S and q not in seen:
                seen.add(q); stack.append(q)
    conn = len(seen) == len(S)
    print(f"connected={conn} ({len(seen)}/{len(S)})")
    ok = ok and conn
    if not ok:
        print("SHAPE TRAINING FAILED ITS GATE — nothing written")
        sys.exit(1)

    with open(DST, "w") as f:
        f.write("# teddy_s1.cells — SHAPE-TRAINED teddy (shape_train.py)\n")
        f.write("# Body == the imported scan; the support polygon was trained:\n")
        f.write(f"# {len(grown)} pillars grown so the COM projects inside the "
                f"paw hull with margin >= {MARGIN_REQ} cell.\n")
        f.write(f"# pre: margin {base['margin']:.3f} (UNSTABLE) -> "
                f"post: {final['margin']:.3f} cells\n")
        f.write(f"CELLS {len(cur_cells)}\n")
        for c in cur_cells:
            f.write(f"{c[0]} {c[1]} {c[2]}\n")
        f.write(f"CHAINS {len(cur_chains)}\n")
        for fore, side, path in cur_chains:
            f.write(f"{fore} {side} {len(path)}\n")
            for p in path:
                f.write(f"{p[0]} {p[1]} {p[2]}\n")
    print(f"WROTE {DST.name}: {len(cur_cells)} cells (+{len(cur_cells)-len(cells)} grown), "
          f"{len(cur_chains)} legs, margin {final['margin']:.3f}")

if __name__ == "__main__":
    main()
