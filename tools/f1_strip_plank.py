"""f1_strip_plank.py -- remove the hallucinated wooden plank from the Hunyuan3D bear.

The shape model added a ~2x2-unit plank under the bear (not in the reference).
Strategy: the source mesh is heavily fragmented (~219 disconnected shells -- the
bear is ~200 small parts, the plank is 2 giant flat sheets). So: drop components
that are plank-LIKE (huge horizontal extent, near-zero vertical extent), then cut
any leftover faces outside the bear's footprint radius in the bottom slice (plank
rim remnants). Keep ALL remaining parts -- the bear is many small shells, so
"keep largest component" would delete the bear and keep the plank's inner disc.

Usage: .venv-hy3d/Scripts/python.exe tools/f1_strip_plank.py
"""
from __future__ import annotations

import numpy as np
import trimesh

SRC = "models/genbear3/f1_hunyuan_anchor03.glb"
DST = "models/genbear3/f1_hunyuan_anchor03_bear.glb"
FOOTPRINT_R = 0.55   # horizontal keep radius (bear bbox is ~±0.35; plank is ±1.0)


def main() -> None:
    scene = trimesh.load(SRC)
    if isinstance(scene, trimesh.Scene):
        # scene.dump() applies the scene-graph transforms (GLB Y-up); raw
        # scene.geometry values are in a PERMUTED local frame -- do not use them.
        mesh = trimesh.util.concatenate(scene.dump())
    else:
        mesh = scene
    print(f"loaded: {len(mesh.vertices)} verts, {len(mesh.faces)} faces, "
          f"bbox {mesh.bounds[0]} .. {mesh.bounds[1]}")

    try:
        centroids = mesh.triangles_center
    except AttributeError:
        centroids = mesh.triangles.mean(axis=1)

    # Do not assume Y-up -- measure it. After scene.dump() the transforms are
    # baked, so the short axis IS the vertical one for this asset.
    extents = mesh.bounds[1] - mesh.bounds[0]
    up_axis = int(np.argmin(extents))
    print(f"extents {np.round(extents, 3)} -> up axis = {'XYZ'[up_axis]}")

    z = centroids[:, up_axis]
    z_lo, z_hi = mesh.bounds[0][up_axis], mesh.bounds[1][up_axis]
    z_mid = z_lo + 0.15 * (z_hi - z_lo)  # plank lives in the bottom slice

    # bear center in the horizontal plane, from the upper (bear) faces only
    horiz = [i for i in range(3) if i != up_axis]
    upper = centroids[z > z_mid]
    center_h = np.median(upper[:, horiz], axis=0)
    r_h = np.linalg.norm(centroids[:, horiz] - center_h, axis=1)

    # 1) drop plank-LIKE components: flat sheets with a huge horizontal span.
    # Face-level labels via face-adjacency connected components (split()
    # remaps vertices, so map by faces instead).
    from trimesh.graph import connected_components

    drop = np.zeros(len(mesh.faces), dtype=bool)
    n_comp = 0
    for face_ids in connected_components(mesh.face_adjacency):
        n_comp += 1
        pts = centroids[face_ids]
        lo, hi = pts.min(axis=0), pts.max(axis=0)
        ext = hi - lo
        if ext[up_axis] < 0.05 and max(ext[horiz]) > 1.0:
            drop[face_ids] = True
    print(f"plank-like components dropped: {int(drop.sum())} faces of {n_comp} parts")

    # 2) cut leftover rim faces outside the footprint, in the bottom slice only
    rim = (r_h > FOOTPRINT_R) & (z < z_mid)
    print(f"rim cut: {int(rim.sum())} faces outside r={FOOTPRINT_R} below z={z_mid:.3f}")
    mesh.update_faces(~(drop | rim))
    mesh.remove_unreferenced_vertices()

    mesh.export(DST)
    print(f"saved {DST}: {len(mesh.vertices)} verts, {len(mesh.faces)} faces, "
          f"bbox {mesh.bounds[0]} .. {mesh.bounds[1]}")


if __name__ == "__main__":
    main()
