"""ct_skeleton_triangle.py -- the CT bone previews through the engine's TRIANGLE
path (lane agent/triangle-monkey-grid-20260920, Defect A repair).

THE LAW (standing, predates the divergence this lane repairs):
  * docs/THE_RENDERER_DECISION.md -- the C++ Vulkan engine is the renderer; the
    triangle pipeline is the accepted fill ("create_triangle_pipeline",
    depth-tested, stencil-marking per docs/THE_STUDIO_GRID_DEPTH.md item 4).
  * Matter-kernel law 5 / B5 PREREGISTRATION
    (docs/evidence/agent_fleet/MATTER_KERNEL/B5_PREREGISTRATION.md): "Triangles
    are weights: membranes load onto the GPU ONCE and stay resident".
  * docs/THE_TRIANGLE_CARRIER.md: "triangles are matter elements".
  Creature/bone visuals are real indexed TRIANGLE geometry: depth-tested,
  shaded, filling their own silhouette.

THE DEFECT (operator, 2026-09-20): "the monkey is a collection of bones and it
is also a collection of a splat cloud, which is wrong. It's using the old splat
cloud technique when we should be using the triangle technique."

THE REPAIR: the SAME registered geometry ct_skeleton_layer places (ONE rigid
registration, scale pinned to the walker HAT length) is ingested as ONE merged
indexed triangle mesh through the engine's standing /mesh_bin route
(ChimeraEngine/engine/main.cpp: [u32 N][u32 idxCount][f32 r][f32 theta][f32
phi][f32 slotmode][f32 * N*9 verts: pos3+normal3+color3][u32 * idxCount]).
The splat machinery stays (other users; skeleton_movie --render splat keeps
working); the monkey scene's DEFAULT compose is the triangle layer.

RULE 0 receipt: tools/science_funnel/validation/triangle_monkey_20260920/receipt.json
"""
from __future__ import annotations

import json
import struct
import sys
import urllib.request
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.science_funnel import ct_skeleton_layer as CSL

ROOT = CSL.ROOT
CT_DIR = CSL.CT_DIR
PREVIEW_DIR = CSL.PREVIEW_DIR


def load_obj_mesh(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Vertices (n,3, float64, millimetres) and triangle indices (m,3, int64) of
    a committed preview OBJ. Handles `v`, `f a b c ...` (fan-triangulated),
    `v/vt`, `v/vt/vn` and negative (relative) indices."""
    verts: list[tuple[float, float, float]] = []
    tris: list[tuple[int, int, int]] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith("v "):
                p = line.split()
                verts.append((float(p[1]), float(p[2]), float(p[3])))
            elif line.startswith("f "):
                p = line.split()[1:]
                idx = []
                for tok in p:
                    s = tok.split("/")[0]
                    i = int(s)
                    idx.append(i - 1 if i > 0 else len(verts) + i)
                for k in range(1, len(idx) - 1):   # fan triangulation
                    tris.append((idx[0], idx[k], idx[k + 1]))
    CSL._require(verts, "obj_vertex_stream_empty", str(path))
    CSL._require(tris, "obj_face_stream_empty", str(path))
    return (np.asarray(verts, dtype=np.float64),
            np.asarray(tris, dtype=np.int64))


def mesh_normals(verts: np.ndarray, tris: np.ndarray) -> np.ndarray:
    """Area-weighted per-vertex normals (each triangle's cross product
    accumulated). Same estimator as ChimeraEngine/cpp_bridge._mesh_normals."""
    v0, v1, v2 = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    fn = np.cross(v1 - v0, v2 - v0)
    n = np.zeros_like(verts)
    np.add.at(n, tris[:, 0], fn)
    np.add.at(n, tris[:, 1], fn)
    np.add.at(n, tris[:, 2], fn)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    ln[ln == 0] = 1.0
    return n / ln


def _seat_height() -> float:
    return CSL._seat_height()


MASS_BOOK_TOTAL_G = 52.31   # the matter-skeleton import's per-compartment mass
                            # book: 25 compartments, 52.31 g total (operator-
                            # stated; the composite alone is ~35.7 g of it, so
                            # the CoG sits in the trunk). Per-bone masses share
                            # the total by the manifest's MEASURED volumes.


def mass_book() -> tuple[np.ndarray, np.ndarray]:
    """Per-bone masses (g) and centroids (scene metres) from the manifest's
    measured volumes and centroids, normalized to the 52.31 g total."""
    man = json.loads((CT_DIR / "meshes" / "manifest.json").read_text())
    raw = CSL.WALKER_DERIVED_PATH.read_bytes()
    CSL._require(CSL._sha256(raw) == CSL.WALKER_DERIVED_SHA256,
                 "walker_derivation_pin_drift")
    hat_length_m = float(json.loads(raw)["body_model"]["segments_Table1"]["HAT"]["length_m"])
    composite = CSL.load_obj_vertices(PREVIEW_DIR / CSL.COMPOSITE_PREVIEW)
    scale, R, translation, _ = CSL.ct_registration(composite, hat_length_m,
                                                   _seat_height())
    vols = np.array([b["volume_mm3"] for b in man["bones"]])
    masses = MASS_BOOK_TOTAL_G * vols / vols.sum()
    cents = []
    for entry in man["bones"]:
        name = Path(entry["file"]).name
        preview = name.replace(".obj", "_lo.obj")
        verts_mm, _ = load_obj_mesh(PREVIEW_DIR / preview)
        scene = CSL.apply_registration(verts_mm, scale, R, translation)
        cents.append(scene.mean(axis=0))
    return masses, np.asarray(cents)


def layer_triangle_mesh(pivot: str = "bbox") -> dict:
    """The full skeleton layer as ONE merged indexed triangle mesh, in scene
    metres, under the SAME ONE rigid registration the law pins (reused from
    ct_skeleton_layer, not re-derived -- one mount, two presentations).

    pivot: what sits at the orbit origin (the viewer's pivot):
      'bbox' -- the geometry bbox centre (framing normalization, unchanged);
      'cog'  -- the MASS centre of gravity from the mass book (membrane D: the
                viewer orbits the body's centre of gravity; the committed data
                is untouched -- the translation is render-time framing, applied
                to the uploaded copy only).

    Returns {"verts9": (N,9) float32 [pos3 normal3 color3],
             "tris": (3M,) uint32 flattened, "record": {...}}."""
    man = json.loads((CT_DIR / "meshes" / "manifest.json").read_text())
    raw = CSL.WALKER_DERIVED_PATH.read_bytes()
    CSL._require(CSL._sha256(raw) == CSL.WALKER_DERIVED_SHA256,
                 "walker_derivation_pin_drift")
    hat_length_m = float(json.loads(raw)["body_model"]["segments_Table1"]["HAT"]["length_m"])

    composite = CSL.load_obj_vertices(PREVIEW_DIR / CSL.COMPOSITE_PREVIEW)
    scale, R, translation, diag = CSL.ct_registration(composite, hat_length_m,
                                                      _seat_height())
    vert_chunks: list[np.ndarray] = []
    tri_chunks: list[np.ndarray] = []
    bones: list[dict] = []
    offset = 0
    for entry in man["bones"]:
        name = Path(entry["file"]).name          # full-res name ...
        preview = name.replace(".obj", "_lo.obj")  # ... the committed preview
        path = PREVIEW_DIR / preview
        CSL._require(path.is_file(), "preview_mesh_missing", preview)
        verts_mm, tris = load_obj_mesh(path)
        scene = CSL.apply_registration(verts_mm, scale, R, translation)
        normals = mesh_normals(scene, tris)
        n = scene.shape[0]
        v9 = np.zeros((n, 9), dtype=np.float32)
        v9[:, 0:3] = scene.astype(np.float32)
        v9[:, 3:6] = normals.astype(np.float32)
        v9[:, 6] = CSL.CT_BONE_COLOR[0]
        v9[:, 7] = CSL.CT_BONE_COLOR[1]
        v9[:, 8] = CSL.CT_BONE_COLOR[2]
        vert_chunks.append(v9)
        tri_chunks.append((tris + offset).astype(np.uint32).ravel())
        bones.append({"preview": preview, "vertices": int(n),
                      "triangles": int(tris.shape[0])})
        offset += n
    verts9 = np.concatenate(vert_chunks, axis=0)
    tris = np.concatenate(tri_chunks, axis=0)
    pos = verts9[:, 0:3].astype(np.float64)
    pivot_offset = [0.0, 0.0, 0.0]
    if pivot == "cog":
        masses, cents = mass_book()
        cog = (masses[:, None] * cents).sum(axis=0) / masses.sum()
        pivot_offset = [round(float(v), 6) for v in cog]
        verts9[:, 0:3] -= cog.astype(np.float32)
    record = {
        "schema": "chimera.ct_skeleton_triangle.v1",
        "lane": "agent/triangle-monkey-grid-20260920",
        "specimen": CSL.SPECIMEN,
        "bones": len(man["bones"]),
        "vertices": int(verts9.shape[0]),
        "triangles": int(tris.size // 3),
        "registration": diag,
        "scale_scene_per_mm": diag["scale_scene_per_mm"],
        "units": "scene metres (walker/free-root frame: +Y up, +X forward, +Z left)",
        "endpoint": "/mesh_bin (engine triangle pipeline: depth-tested, stencil-marking)",
        "pivot": pivot,
        "pivot_offset_m": pivot_offset,
        "bbox_min_m": [round(float(v), 6) for v in pos.min(axis=0)],
        "bbox_max_m": [round(float(v), 6) for v in pos.max(axis=0)],
    }
    return {"verts9": verts9, "tris": tris, "record": record, "bones": bones}


def post_layer_mesh(engine_url: str, verts9: np.ndarray, tris: np.ndarray,
                    radius: float, theta: float, phi: float,
                    timeout: float = 120.0) -> bool:
    """POST the merged mesh to the engine's /mesh_bin (triangle pipeline).

    Wire contract (ChimeraEngine/engine/main.cpp):
      [u32 N][u32 idxCount][f32 cam_radius][f32 cam_theta][f32 cam_phi][f32 slotmode]
      [f32 * N * 9: pos3, normal3, color3][u32 * idxCount]
    slotmode 0 -> slot 0 (main mesh), mode 0 (fill)."""
    n = int(verts9.shape[0])
    header = struct.pack("<II4f", n, int(tris.size),
                         float(radius), float(theta), float(phi), 0.0)
    payload = (header
               + np.ascontiguousarray(verts9, dtype=np.float32).tobytes()
               + np.ascontiguousarray(tris, dtype=np.uint32).tobytes())
    req = urllib.request.Request(f"{engine_url.rstrip('/')}/mesh_bin", data=payload,
                                 headers={"Content-Type": "application/octet-stream"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status == 200 and b'"ok":true' in resp.read()


def recenter_mesh(layer: dict) -> dict:
    """Framing normalization identical in law to skeleton_movie.recenter: the
    orbit camera looks at the ORIGIN, so the merged mesh is translated so its
    bbox centre sits at the origin. The registration is untouched (render-time
    framing, applied identically to every presentation)."""
    out = {"tris": layer["tris"], "record": layer["record"], "bones": layer["bones"]}
    v9 = layer["verts9"].copy()
    c = (v9[:, 0:3].min(axis=0) + v9[:, 0:3].max(axis=0)) / 2.0
    v9[:, 0:3] -= c.astype(np.float32)
    out["verts9"] = v9
    return out


def derive_camera_from_layer(layer: dict) -> dict:
    """Camera radius derived from the layer's bounding box and the engine's
    45 deg vertical FOV -- the same derivation skeleton_movie.derive_camera
    performs on the splat buffer (fit the height, one margin), so the mesh and
    splat presentations are camera-comparable."""
    pos = layer["verts9"][:, 0:3].astype(np.float64)
    lo, hi = pos.min(axis=0), pos.max(axis=0)
    height = float(hi[1] - lo[1])
    half_fov = np.deg2rad(45.0) / 2.0  # engine FOV (engine.cpp update_camera_matrices)
    radius = 1.35 * (height / 2.0) / np.tan(half_fov)
    return {
        "bbox_min_m": [round(float(v), 6) for v in lo],
        "bbox_max_m": [round(float(v), 6) for v in hi],
        "bbox_height_m": round(height, 6),
        "fov_y_deg": 45.0,
        "camera_margin": 1.35,
        "radius_m": round(float(radius), 6),
    }
