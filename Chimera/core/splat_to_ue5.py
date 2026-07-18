"""splat_to_ue5 — rung D-prime: the grown limb's SPLATS in the LIVE editor, under
Substrate, beside its own marching-cubes mesh, lit by a moving sun.

(tb-0170, fable-5. Research + route choice: docs/research/substrate_splats_ue58.md.)

THE ROUTE (all proven pathways, no Niagara authoring — that bridge lane is a
documented dead end):
    1. Grow + flesh the limb (core.limb), emit splats (core.splat_emit.emit_limb).
    2. Bake the SAME grid to the marching-cubes GLB (core.bake — the proven mesh path).
    3. Build a QUAD-PER-SPLAT mesh: each Gaussian becomes a small oriented, double-sided
       quad; per-splat albedo rides COLOR_0 vertex colors (the library's mottle — "an
       average, not a surface" — flows into the engine per-particle). Export GLB.
    4. MCP-drive the live editor (mirrors core.bake_to_ue5): import both GLBs, spawn
       splat-cloud and mesh side by side, sweep the directional light through 3 angles
       (the 27h-sun stand-in), viewport screenshot at each.
With r.Substrate=1 the importer's generated materials are Substrate slabs (legacy
conversion), so these screenshots are literally "splats shaded by Substrate under a
moving light" — the rung's kill criterion, exercised for real.

Run:  python -m core.splat_to_ue5            (editor must be up with the bridge)
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

from core import bake, limb
from core.splat_emit import MEDIUM, emit_limb
from core.telemetry_probe import MCPStdioClient

OUT = Path(r"E:\PythonChimera\Chimera\Saved\SubstrateSplats")
DEST = "/Game/Grown/"
TARGET_CM = 170.0
SPAWN_Z = 100.0
SPLAT_X, MESH_X = 0.0, 260.0
CAMERA = "130 -520 130 0 90 0"          # stand back on -Y, look at the pair
SUN_SWEEP = [(-35, 25), (-45, 140), (-25, 260)]   # (pitch, yaw) — three sun positions


def quad_cloud(splats: dict, scale: float) -> "object":
    """One small double-sided quad per splat, oriented by its normal, colored by ITS
    OWN albedo (COLOR_0). Quad half-size from the emission's tangent footprint."""
    import trimesh

    pos = splats["pos"] * scale
    n = splats["normal"]
    up = np.where(np.abs(n[:, 2:3]) < 0.9, np.array([0., 0., 1.]), np.array([1., 0., 0.]))
    t1 = np.cross(up, n)
    t1 /= np.clip(np.linalg.norm(t1, axis=1, keepdims=True), 1e-9, None)
    t2 = np.cross(n, t1)
    h = 1.15 * scale * 1.35                     # tangent_scale voxels -> cm, +overlap

    corners = []
    for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        corners.append(pos + a * h * t1 + b * h * t2)
    verts = np.stack(corners, axis=1).reshape(-1, 3)            # (N*4, 3)
    verts = verts - verts.mean(axis=0)                          # CENTER the pivot —
    # uncentered verts (0..340cm from origin) made the spawned actor's geometry hang
    # far from its pivot: it hovered in the sky while its transform read (x,y,100)
    # (seen live 2026-07-18; the bake path recentres per-tissue for the same reason)
    base = np.arange(len(pos)) * 4
    f1 = np.stack([base, base + 1, base + 2], axis=1)
    f2 = np.stack([base, base + 2, base + 3], axis=1)
    faces = np.concatenate([f1, f2, f1[:, ::-1], f2[:, ::-1]])  # double-sided
    rgba = np.concatenate([np.clip(splats["albedo"], 0, 1),
                           np.clip(splats["alpha"], 0, 1)[:, None]], axis=1)
    vcol = (np.repeat(rgba, 4, axis=0) * 255).astype(np.uint8)
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, vertex_colors=vcol, process=False)
    scene = trimesh.Scene()
    scene.add_geometry(mesh, node_name="cloud", geom_name="cloud")
    return scene


def _ok(resp) -> tuple:
    try:
        sc = resp["result"]["structuredContent"]
        return bool(sc.get("success")), sc.get("message", "")
    except (KeyError, TypeError):
        return False, json.dumps(resp)[:200] if resp else "no response"


def drive(splat_glb: Path, mesh_glb: Path) -> dict:
    c = MCPStdioClient()
    log = {}
    try:
        for glb in (splat_glb, mesh_glb):
            ok, msg = _ok(c.call("manage_asset", {
                "action": "import", "sourcePath": str(glb), "destinationPath": DEST}))
            log[f"import:{glb.stem}"] = (ok, msg)

        # single-mesh GLBs import as <stem>/StaticMeshes/<stem> (probed live 2026-07-18);
        # multi-mesh (the baked limb) keeps its node names (skin/muscle/bone).
        spawns = [
            ("Splat_Cloud", f"{DEST}{splat_glb.stem}/StaticMeshes/{splat_glb.stem}", SPLAT_X),
            ("Mesh_Skin", f"{DEST}{mesh_glb.stem}/StaticMeshes/skin", MESH_X),
        ]
        for name, path, x in spawns:
            c.call("control_actor", {"action": "delete_actor", "actorName": name})
            ok, msg = _ok(c.call("control_actor", {
                "action": "spawn_actor", "classPath": "/Script/Engine.StaticMeshActor",
                "meshPath": path, "actorName": name,
                "location": {"x": x, "y": 0.0, "z": SPAWN_Z}}))
            log[f"spawn:{name}"] = (ok, msg)

        c.call("control_editor", {"action": "console_command",
                                  "command": f"BugItGo {CAMERA}"})

        # find the sun; sweep it. If the level names differ, take the first hit.
        sun = None
        resp = c.call("control_actor", {"action": "find_by_class",
                                        "className": "DirectionalLight"})
        try:  # automation_response nests actors under result.data (probed live)
            sc = resp["result"]["structuredContent"]
            actors = sc["result"]["data"]["actors"]
            sun = actors[0].get("name") if actors else None
        except (KeyError, TypeError, AttributeError, IndexError):
            sun = None
        log["find:sun"] = (sun is not None, sun or "no DirectionalLight found")

        OUT.mkdir(parents=True, exist_ok=True)
        for i, (pitch, yaw) in enumerate(SUN_SWEEP):
            if sun:
                ok, msg = _ok(c.call("control_actor", {
                    "action": "set_transform", "actorName": sun,
                    "rotation": {"pitch": pitch, "yaw": yaw, "roll": 0.0}}))
                log[f"sun:{i}"] = (ok, msg)
            shot = OUT / f"substrate_splats_light{i}.png"
            ok, msg = _ok(c.call("control_editor", {
                "action": "screenshot", "filename": str(shot),
                "mode": "editor_viewport"}))
            log[f"shot:{i}"] = (ok, msg or str(shot))
    finally:
        c.close()
    return log


def main() -> int:
    print("growing + fleshing the limb ...")
    _s, fleshed, shape, _t = limb.grow_limb(limb.bent_limb(), seed=0)

    splats = emit_limb(fleshed)
    occ = np.argwhere(fleshed != MEDIUM)
    extent = float((occ.max(axis=0) - occ.min(axis=0)).max())
    scale = TARGET_CM / max(extent, 1.0)
    print(f"  {len(splats['pos'])} splats, scale {scale:.2f} cm/voxel")

    OUT.mkdir(parents=True, exist_ok=True)
    splat_glb = OUT / "splatlimb.glb"
    quad_cloud(splats, scale).export(str(splat_glb))
    mesh_glb = OUT / "meshlimb.glb"
    bake.bake(fleshed, shape, target_cm=TARGET_CM).export(str(mesh_glb))
    print(f"  wrote {splat_glb.name} + {mesh_glb.name}")

    print("driving the live editor ...")
    log = drive(splat_glb, mesh_glb)
    for step, (ok, msg) in log.items():
        print(f"  {'OK ' if ok else 'FAIL'} {step:<18} {str(msg)[:90]}")
    good = all(ok for ok, _ in log.values())
    print("\n  SPLATS UNDER SUBSTRATE." if good else "\n  Some steps failed — see above.")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
