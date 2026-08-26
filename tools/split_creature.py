"""split_creature.py -- the first Chimera: a teddy/monkey 50-50 split, straight down the midline.

THE SEED (operator goal, 2026-08-26): the first Chimera creature is a TEDDY-BEAR / MONKEY
genetic split, right down the middle -- left half one lineage, right half the other. This is
the eventual target of `theSeed`; this script is the pipeline seed: take two source meshes,
cut each at the x=0 plane, and fuse them into ONE triangle mesh whose seam is the midline.

MEMBRANE (Rule 0):
  STATEMENT  -- two half-meshes fused at x=0 yield one watertight-ish creature with a clean
                midline seam; the dyad (LM Studio eye via mesh_view) reads "two distinct
                lineages meeting at a midline," not a single animal.
  PREDICTION -- the merged mesh has (a) every vertex of the left lineage at x<=0, every vertex
                of the right lineage at x>=0, (b) coincident seam vertices at x~0, (c) two
                clearly distinct surface identities (brown bear right, green monkey left).
  FALSIFIER  -- a gap or overlap at the seam, or the dyad reads a single lineage / cannot
                find the midline.

LAWS: triangle-primary (the mesh is the carrier; splat is deferred frosting); the dyad's
MOVIE premise (judge the orbit, not a still). The monkey here is a PROCEDURAL STAND-IN
(operator-approved) -- the pipeline is what is being proven, not the fidelity of the monkey.

Run:  python tools/split_creature.py
Prints mesh stats + (if the engine boots) the /judge verdict dict.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))            # so `import tools.mesh_view` works when run as a script
TEDDY = ROOT / ".tmp" / "cad_bear_rebuild.glb"
OUT = ROOT / ".tmp" / "split_creature.glb"

# lineage colors (linear-ish 0..1 RGB)
BROWN = (0.55, 0.35, 0.15)
GREEN = (0.20, 0.62, 0.22)


def _clip(mesh: trimesh.Trimesh, keep_right: bool) -> trimesh.Trimesh:
    """Keep the half of `mesh` on one side of x=0. keep_right=True -> x>=0, else x<=0.
    Open cut at x=0 (not capped); the two open boundaries will coincide after the seam snap."""
    v = np.asarray(mesh.vertices)
    f = np.asarray(mesh.faces)
    if keep_right:
        mask = np.all(v[f][..., 0] >= -1e-4, axis=1)
    else:
        mask = np.all(v[f][..., 0] <= 1e-4, axis=1)
    sub = mesh.submesh([mask], append=True) if hasattr(mesh, "submesh") else _submesh(mesh, mask)
    return sub


def _submesh(mesh, face_mask):
    f = np.asarray(mesh.faces)[face_mask]
    used = np.unique(f)
    remap = np.full(mesh.vertices.shape[0], -1)
    remap[used] = np.arange(len(used))
    return trimesh.Trimesh(vertices=mesh.vertices[used],
                           faces=remap[f], process=False,
                           visual=mesh.visual)


def build_monkey() -> trimesh.Trimesh:
    """Procedural monkey-ish stand-in: a green ellipsoid head + snout + two ears."""
    parts = []
    head = trimesh.creation.uv_sphere(radius=0.40, count=(24, 16))
    head.apply_scale([1.25, 1.0, 1.0])
    parts.append(head)
    snout = trimesh.creation.uv_sphere(radius=0.18, count=(16, 12))
    snout.apply_translation([0.34, -0.02, 0.12])
    parts.append(snout)
    for sx in (-0.30, 0.30):
        ear = trimesh.creation.uv_sphere(radius=0.15, count=(14, 10))
        ear.apply_translation([sx, 0.30, 0.02])
        parts.append(ear)
    if hasattr(trimesh.util, "concatenate"):
        merged = trimesh.util.concatenate(parts)
    else:
        merged = parts[0]
        for p in parts[1:]:
            merged += p
    return merged


def _snap_seam(mesh: trimesh.Trimesh, tol: float = 0.02) -> None:
    """Pull near-plane vertices exactly onto x=0 so the two halves meet with no gap."""
    v = np.asarray(mesh.vertices)
    v[np.abs(v[:, 0]) < tol, 0] = 0.0
    mesh.vertices = v


def _color(mesh: trimesh.Trimesh, rgb) -> None:
    n = len(mesh.vertices)
    cols = np.tile(np.array(rgb + (1.0,)) * 255, (n, 1)).astype(np.uint8)
    mesh.visual = trimesh.visual.ColorVisuals(
        mesh=mesh, vertex_colors=cols[:, :3])


def build_split_creature(teddy_path: Path = TEDDY) -> trimesh.Trimesh:
    if not teddy_path.exists():
        raise FileNotFoundError(f"teddy source missing: {teddy_path}")
    teddy = trimesh.load(str(teddy_path), process=False)
    teddy = teddy if isinstance(teddy, trimesh.Trimesh) else teddy.dump(concatenate=True)

    monkey = build_monkey()

    # center each on the origin so the midline cut is the body's own mid-plane
    teddy.vertices -= teddy.bounding_box.centroid
    monkey.vertices -= monkey.bounding_box.centroid

    right = _clip(teddy, keep_right=True)    # teddy -> right half (x>=0), brown
    left = _clip(monkey, keep_right=False)   # monkey -> left half (x<=0), green
    _snap_seam(right)
    _snap_seam(left)
    _color(right, BROWN)
    _color(left, GREEN)

    # fuse: concatenate vertices + offset face indices
    rv, rf = np.asarray(right.vertices), np.asarray(right.faces)
    lv, lf = np.asarray(left.vertices), np.asarray(left.faces)
    verts = np.vstack([rv, lv])
    faces = np.vstack([rf, lf + len(rv)])
    fused = trimesh.Trimesh(vertices=verts, faces=faces, process=False,
                            visual=trimesh.visual.ColorVisuals(
                                vertex_colors=np.vstack([
                                    np.tile(np.array(BROWN + (1.0,)) * 255, (len(rv), 1)).astype(np.uint8)[:, :3],
                                    np.tile(np.array(GREEN + (1.0,)) * 255, (len(lv), 1)).astype(np.uint8)[:, :3]])))
    return fused


def main() -> dict:
    fused = build_split_creature()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fused.export(str(OUT))

    v = np.asarray(fused.vertices)
    stats = {
        "out": str(OUT),
        "verts": int(len(fused.vertices)),
        "faces": int(len(fused.faces)),
        "right_half_verts": int(np.sum(v[:, 0] >= 0)),
        "left_half_verts": int(np.sum(v[:, 0] <= 0)),
        "watertight": bool(fused.is_watertight),
        "extent": fused.extents.tolist(),
    }
    print("[split_creature] mesh built:", stats)

    # dyad judgment -- boot the engine if needed, else report the mesh only
    try:
        os.environ.setdefault("CHIMERA_ENGINE_URL", "http://localhost:8090")
        import tools.mesh_view as mv
        ok, msg = mv.ensure_engine()
        print(f"[split_creature] engine boot: {ok} ({msg})")
        if ok:
            mv.load_mesh(OUT)
            verdict = mv.do_judge(6)
            stats["judge"] = {k: verdict.get(k) for k in ("alignment", "observed", "expected")}
            print("[split_creature] judge alignment:", verdict.get("alignment"))
            print("[split_creature] judge observed:", (verdict.get("observed") or "")[:240])
    except Exception as e:  # engine/adopt issues are advisory, never a block
        print(f"[split_creature] judge skipped (engine/adopt unavailable): {e}")
    return stats


if __name__ == "__main__":
    main()
