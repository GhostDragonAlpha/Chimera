# SPIACE T1 — voxelize the TRELLIS teddy onto the CA lattice.
#
# The claim (Rule 0): a membrane is a cell set with a rig declaration, so a
# TRELLIS-generated body walks with ZERO changes to ca_core.cpp's physics/gait/
# nav layers. This tool only DECIDES the scale and ORIENTATION of that mapping;
# it does not touch the simulation.
#
#   python voxelize_teddy.py [models/trellis/teddy.ply] [stem] [body_h]
#
# Emits, next to this file (stem defaults to "teddy"):
#   genomes/<stem>.cells    — the occupancy cell set + rig chains (DATA)
#   genomes/<stem>.chimera  — kind=vox genome table pointing at <stem>.cells
#
# body_h (default 8, T1's bear-matching scale): the import resolution. T9
# DERIVES it from feature legibility instead of scale-matching: canon teddy
# proportions put the head at ~0.45 of height and the eye at ~1/6 of the
# head, so an eye spans H*0.45/6 cells; an eye needs >= 2 cells to exist on
# the lattice at all -> H >= 26.7. H=28 gives a 2.1-cell eye.
#
# SCALE IS DERIVED, NOT PICKED. The bear body stands 8 cells tall (bodyH = 8,
# groundMinY = -4, measured from the beargoal selftest). We size the teddy so
# its standing height in cells equals that: s = BEAR_BODYH / H_teddy, where
# H_teddy is the model-space extent along the up axis. Orientation (model +z
# -> CA +y) is verified empirically by rendering the cell set before rigging;
# here we just record which mapping was used.

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GENOMES = HERE / "genomes"
PLY = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    HERE.parent.parent / "models" / "trellis" / "teddy.ply")
STEM = sys.argv[2] if len(sys.argv) > 2 else "teddy"   # T9: output stem —
                                   # teddy.cells stays frozen as T1's fossil

BEAR_BODYH = int(sys.argv[3]) if len(sys.argv) > 3 else 8
                          # default 8 = T1 bear-matching; T9 honey uses 28
                          # (2.1-cell eye — see the header derivation)
CELL = 0.06             # CA lattice cell size (cells are integer indices)


def read_ply_verts(path):
    """Read a binary-little-endian PLY vertex block -> (x, y, z) float arrays.

    Handles the two TRELLIS outputs: teddy.ply (xyz + rgb uchar, stride 15)
    and myvox.ply (xyz only, stride 12). We parse the header to find the
    vertex element's byte offset and per-vertex stride rather than hardcoding.
    """
    import numpy as np
    with open(path, "rb") as f:
        hdr = b""
        while True:
            line = f.readline()
            if line.strip() == b"end_header":
                break
            hdr += line
        off = f.tell()
    # parse header for the vertex element's properties + count
    vcount, props = 0, []
    in_vert = False
    for raw in hdr.split(b"\n"):
        t = raw.strip()
        if t.startswith(b"element vertex"):
            in_vert = True
            vcount = int(t.split()[2])
            continue
        if in_vert and t.startswith(b"property"):
            props.append(t)  # property <type> <name>
            continue
        if in_vert and not (t.startswith(b"element") or t.startswith(b"property")):
            break
    # build a numpy dtype from the vertex properties (skip face element)
    names, fmts = [], []
    for p in props:
        parts = p.split()
        typ, nm = parts[1], parts[2]
        if typ == b"float":
            names.append(nm.decode()); fmts.append("<f4")
        elif typ == b"uchar":
            names.append(nm.decode()); fmts.append("u1")
    dt = np.dtype(list(zip(names, fmts)))
    with open(path, "rb") as f:
        f.seek(off)
        v = np.fromfile(f, dtype=dt, count=vcount)
    return (v["x"].astype(np.float64), v["y"].astype(np.float64),
            v["z"].astype(np.float64))


def main():
    import numpy as np
    x, y, z = read_ply_verts(PLY)

    # Orientation: model +z is the up axis (feet at min_z, ears/top at max_z).
    H = float(z.max() - z.min())          # standing height in model units
    s = BEAR_BODYH / H                     # cells per model unit (DERIVED)
    print(f"H_teddy = {H:.6f} model units  ->  s = {s:.4f} cells/unit "
          f"(bear bodyH = {BEAR_BODYH})")

    # Axis mapping (verified empirically, see PLAN T1): CA y(up) = model z,
    # CA x(forward) = model x, CA z(side) = model y. Round to nearest cell.
    cx = np.round(x * s).astype(int)
    cy = np.round(z * s).astype(int)        # up axis
    cz = np.round(y * s).astype(int)

    cells = sorted(set(zip(cx, cy, cz)))     # occupancy (dedupe), mat=0 skin
    print(f"cells: {len(cells)}  "
          f"x[{min(c[0] for c in cells)}, {max(c[0] for c in cells)}] "
          f"y(up)[{min(c[1] for c in cells)}, {max(c[1] for c in cells)}] "
          f"z[{min(c[2] for c in cells)}, {max(c[2] for c in cells)}]")

    # Rig chains: the leg-like columns are those touching the ground plane
    # (gy = the body's own lowest cell — derived, not the bear's hardcoded -4;
    # T9 imports at H=28 where the ground is wherever the body says it is).
    # A sitting bear touches ground with its whole bottom RIM, so raw
    # ground-touching columns overcount legs (honey: 30). T9 clusters
    # face-adjacent ground columns into REGIONS and rigs one chain per region
    # (its tallest contiguous run) — a foot cluster is one leg, not nine.
    gy = min(b for (_, b, _) in cells)
    cols = {}
    for (a, b, c) in cells:
        cols.setdefault((a, c), set()).add(b)
    ground_cols = {k for k, v in cols.items() if gy in v}
    # face-adjacency clustering over (a, c)
    clusters = []
    seen = set()
    for k in sorted(ground_cols):
        if k in seen:
            continue
        stack, comp = [k], []
        seen.add(k)
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for da, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (cur[0] + da, cur[1] + dc)
                if nb in ground_cols and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        clusters.append(comp)
    chains = []
    for comp in clusters:
        best = None
        for (ax, az) in comp:
            run = [gy]
            while (run[-1] + 1) in cols[(ax, az)]:
                run.append(run[-1] + 1)
            if len(run) >= 3 and (best is None or len(run) > len(best[2])):
                best = (ax, az, run)
        if best:
            chains.append(best)

    # gait flags by column position (phase variety); the displacement law is
    # independent of them — see ca_core.cpp's N7 earned-stride comment.
    xs = [c[0] for c in chains]; zs = [c[1] for c in chains]
    mx, mz = max(xs), max(zs)
    chain_defs = []
    for (ax, az, run) in chains:
        fore = 1 if ax >= mx else 0
        side = 1 if az >= mz else -1
        path = [(ax, yy, az) for yy in reversed(run)]   # hip(top)->paw(bottom)
        chain_defs.append((fore, side, path))

    print(f"rig chains: {len(chain_defs)} (one per face-adjacent ground "
          f"region; {len(ground_cols)} ground columns in "
          f"{len(clusters)} regions, ground y={gy})")

    # ---- emit <stem>.cells --------------------------------------------------
    lines = [f"# {STEM}.cells — generated by voxelize_teddy.py (do not hand-edit)",
             f"# scale s = {s:.6f} cells/unit (bear bodyH={BEAR_BODYH}); "
             f"CA y(up)=model z, CA x=model x, CA z=model y",
             f"CELLS {len(cells)}"]
    for (a, b, c) in cells:
        lines.append(f"{a} {b} {c}")
    lines.append(f"CHAINS {len(chain_defs)}")
    for (fore, side, path) in chain_defs:
        lines.append(f"{fore} {side} {len(path)}")
        for (px, py, pz) in path:
            lines.append(f"{px} {py} {pz}")
    (GENOMES / f"{STEM}.cells").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---- emit teddy.chimera --------------------------------------------------
    # kind=vox: the cell set is DATA (teddy.cells), not grown. Same B4/N5
    # conventions as beargoal; L5/R5/N6/N8 are omitted because F-T1 stand/walk
    # does not use them (they drive learner/terrain/goal).
    ch = f"""# SPIACE genome table — {STEM} (voxelized TRELLIS body, DATA)
# The cell set is imported (genomes/{STEM}.cells), NOT grown: kind=vox loads
# it directly and rigs the leg columns off that same data. Every B4/N5
# constant is copied from beargoal.chimera — the physics membrane is UNCHANGED
# (the shape-agnostic claim). L5/R5/N6/N8 are omitted: stand/walk does not
# use them; the goal variant adds the goal membrane.

kind           = vox
genome         = {STEM}-v1
embodiment     = 1
tickMs         = 120
cell           = 0.06
cellsFile      = {STEM}.cells

# --- B4: FK/IK rig (copied from beargoal — the gait is shape-agnostic) ------
b4A            = 2              # gait swing amplitude, cells
b4T            = 60             # gait period, anim ticks
b4Lam          = 12.25          # = 7*7/4 damping
b4Dth          = 0.08           # rad per IK iteration
b4ThMax        = 2.6            # joint bound, rad
b4Iters        = 5              # IK iterations per anim tick per chain

# --- N5: physics membrane (copied from beargoal — SI in, sim units derived) --
gravity        = 9.81
tickHz         = 60
"""
    (GENOMES / f"{STEM}.chimera").write_text(ch, encoding="utf-8")

    print(f"wrote {GENOMES/(STEM + '.cells')} and {GENOMES/(STEM + '.chimera')}")


if __name__ == "__main__":
    main()
