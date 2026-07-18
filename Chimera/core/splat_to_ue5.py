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

tb-0179 (the baby-toy critique, 2026-07-18): the FIRST in-engine cloud (22.6k splats,
1.77cm/voxel, ~2.7cm quads) was `limb.grow_limb(limb.bent_limb())` at its DEFAULT
target_len=64 — the human's verdict verbatim: "resolution is going to have to be much
much higher and you got giant plates when we need smaller things — a baby toy compared
to what we need." Two independent, MEASURED levers close that gap:
  (1) finer voxel pitch  — target_len (core.limb.voxelize's own knob; grow_limb forwards
      **kw straight through, so no change to core.limb was even needed to exercise it —
      it was already there, just never turned up).
  (2) smaller footprint  — tangent_scale (the splat's own disk radius, core.splat_emit)
      and quad half-size overlap (this file's quad_cloud) — SEPARATE from (1): (1) makes
      MORE, smaller voxels; (2) makes each splat's OWN footprint tighter so densely-
      packed splats don't overlap into "plates" even at a given resolution.
Both are now CLI knobs (see main()); every run prints an instrumented DENSITY_ROW line
(emission time, splat/vert counts, GLB size) so a density study is a rerun, not a rebuild.
The in-engine check drives cameras through core.photo_studio + core.scene_model (SOLVED,
PREDICTION-before-pixel — never hand-aimed BugItGo) per the standing rule.

Run:  python -m core.splat_to_ue5 --target-len 160          (editor must be up + bridge)
      python -m core.splat_to_ue5 --target-len 64 --no-editor   (headless density row only)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

from core import bake, limb
from core.splat_emit import MEDIUM, emit_limb
from core.telemetry_probe import MCPStdioClient, probe_fps

OUT = Path(r"E:\PythonChimera\Chimera\Saved\SubstrateSplats")
DEST = "/Game/Grown/"
TARGET_CM = 170.0
SPAWN_Z = 100.0
SPLAT_X, MESH_X = 0.0, 260.0
CAMERA = "130 -520 130 0 90 0"          # stand back on -Y, look at the pair
SUN_SWEEP = [(-35, 25), (-45, 140), (-25, 260)]   # (pitch, yaw) — three sun positions
EDITOR_TITLE = "Chimera - Unreal Editor"
MALCOLM_FRAME_MS = 16.6


def quad_cloud(splats: dict, scale: float, tangent_scale: float = 1.15,
              overlap: float = 1.35) -> "object":
    """One small double-sided quad per splat, oriented by its normal, colored by ITS
    OWN albedo (COLOR_0). Quad half-size = tangent_scale (the SAME voxel-space footprint
    passed to emit_limb — the emission's own disk radius, not a re-guessed number) x
    scale (cm/voxel) x overlap (closes seams between neighbouring quads; tb-0179: shrink
    this ALONGSIDE tangent_scale, not instead of finer voxel pitch, when pushing density
    up — the recipe's lever (2), independent of lever (1))."""
    import trimesh

    pos = splats["pos"] * scale
    n = splats["normal"]
    up = np.where(np.abs(n[:, 2:3]) < 0.9, np.array([0., 0., 1.]), np.array([1., 0., 0.]))
    t1 = np.cross(up, n)
    t1 /= np.clip(np.linalg.norm(t1, axis=1, keepdims=True), 1e-9, None)
    t2 = np.cross(n, t1)
    h = tangent_scale * scale * overlap          # tangent_scale voxels -> cm, +overlap

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


def _foreground_editor() -> bool:
    """Defeat the background-throttle trap (CLAUDE.md H-2 / MASTER_ONBOARDING 8c): a
    BACKGROUNDED UE5 editor ticks at ~3fps (FWaitForInteractiveFrameRate never
    releases) — every fps/frame-time reading taken like that is throttle noise, not a
    measurement of what the splat cloud actually costs. Win32 SetForegroundWindow by
    exact title (proven live 2026-07-18); non-fatal if the window can't be found."""
    try:
        import ctypes
        hwnd = ctypes.windll.user32.FindWindowW(None, EDITOR_TITLE)
        if not hwnd:
            return False
        if ctypes.windll.user32.IsIconic(hwnd):
            ctypes.windll.user32.ShowWindow(hwnd, 9)
        return bool(ctypes.windll.user32.SetForegroundWindow(hwnd))
    except Exception:
        return False


def drive(splat_glb: Path, mesh_glb: Path) -> dict:
    """The ORIGINAL rung D' proof: splat cloud + mesh side by side, sun swept through 3
    angles, screenshot at each — tb-0170's own kill criterion (relighting vs the mesh).
    UNCHANGED signature/behavior; tb-0179 does not touch this — it is a different rung's
    evidence path and still open on the board. See drive_density_study for tb-0179's own
    (photo_studio-solved, prediction-first) in-engine check."""
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


def drive_density_study(splat_glb: Path, cloud_radius: float, tag: str = "",
                        try_nanite: bool = True) -> dict:
    """tb-0179's in-engine check, for ONE density tier: import -> (try) Nanite -> stage
    at a KNOWN-extent slot (core.photo_studio) -> a scene_model PREDICTION written
    BEFORE any pixel -> the photo_studio SOLVED portrait (built-in ~2.2s settle). Editor
    is FOREGROUNDED first and performance stats are sampled before/after spawn so the
    frame-time reading is real, not the ~3fps background-throttle artifact."""
    from core.photo_studio import Studio
    from core.scene_model import SceneModel

    log = {}
    fg = _foreground_editor()
    log["foreground_editor"] = (fg, "SetForegroundWindow OK" if fg
                                else "window not found by title — fps readings may be throttle noise")

    c = MCPStdioClient()
    try:
        ok, msg = _ok(c.call("manage_asset", {
            "action": "import", "sourcePath": str(splat_glb), "destinationPath": DEST}))
        log["import:splat"] = (ok, msg)
        mesh_path = f"{DEST}{splat_glb.stem}/StaticMeshes/{splat_glb.stem}"

        fps0, fps0_note = probe_fps(c)
        log["fps_before_spawn"] = (fps0 is not None, f"{fps0}  ({fps0_note})")

        if try_nanite:
            ok, msg = _ok(c.call("manage_asset", {
                "action": "nanite_rebuild_mesh", "assetPath": mesh_path, "meshPath": mesh_path,
                "bEnableNanite": True}))
            log["nanite"] = (ok, msg)

        st = Studio(client=c)
        ok, msg = st.build()
        log["stage:ground"] = (ok, msg)

        c.call("control_actor", {"action": "delete_actor", "actorName": "Splat_Cloud"})
        ok, msg = _ok(c.call("control_actor", {
            "action": "spawn_actor", "classPath": "/Script/Engine.StaticMeshActor",
            "meshPath": mesh_path, "actorName": "Splat_Cloud",
            "location": {"x": 0.0, "y": 0.0, "z": 0.0}}))
        log["spawn:Splat_Cloud"] = (ok, msg)

        ok, msg = st.place("Splat_Cloud", 0, cloud_radius)
        log["place:Splat_Cloud"] = (ok, msg)

        sm = SceneModel(client=c)
        n = sm.ingest()
        log["scene_model:ingest"] = (n > 0, f"{n} actors held")
        if "Splat_Cloud" in sm.actors:
            exp = sm.expectation("Splat_Cloud")
            pred_path = OUT / f"prediction{('_' + tag) if tag else ''}.json"
            OUT.mkdir(parents=True, exist_ok=True)
            pred_path.write_text(json.dumps(exp, indent=2), encoding="utf-8")
            log["prediction_written"] = (True, str(pred_path))
        else:
            log["prediction_written"] = (False, "Splat_Cloud not in ingested actors")

        time.sleep(1.0)          # let the spawn/Nanite build settle before steady-state fps
        fps1, fps1_note = probe_fps(c)
        log["fps_after_spawn"] = (fps1 is not None, f"{fps1}  ({fps1_note})")
        if fps1:
            frame_ms = 1000.0 / fps1
            log["frame_vs_malcolm_wall"] = (frame_ms <= MALCOLM_FRAME_MS,
                                            f"{frame_ms:.2f}ms  (wall={MALCOLM_FRAME_MS}ms)")

        shot = st.portrait("Splat_Cloud", fill=0.7)      # SOLVED camera, settled, per the rule
        log["portrait"] = (True, str(shot))
    finally:
        c.close()
    return log


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--target-len", type=int, default=64,
                    help="core.limb.voxelize's grid-resolution knob (lever 1)")
    ap.add_argument("--tangent-scale", type=float, default=1.15,
                    help="splat disk radius, voxel units (lever 2, with --quad-overlap)")
    ap.add_argument("--quad-overlap", type=float, default=1.35,
                    help="quad half-size overlap multiplier (lever 2)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--sweeps", type=int, default=70, help="adhesion sweeps (grow_limb)")
    ap.add_argument("--tag", default="", help="output filename suffix for this density tier")
    ap.add_argument("--no-editor", action="store_true", help="headless: emit + export only")
    ap.add_argument("--no-nanite", action="store_true", help="skip the Nanite attempt")
    ap.add_argument("--sun-sweep", action="store_true",
                    help="also run the ORIGINAL drive() sun-sweep (tb-0170's own check)")
    a = ap.parse_args()

    tag = a.tag or f"tl{a.target_len}"
    print(f"growing + fleshing the limb (target_len={a.target_len}, sweeps={a.sweeps}) ...")
    t0 = time.time()
    bones = limb.bent_limb()
    _s, fleshed, shape, _t = limb.grow_limb(bones, seed=a.seed, target_len=a.target_len,
                                            sweeps=a.sweeps)
    t_grow = time.time() - t0

    t0 = time.time()
    splats = emit_limb(fleshed, tangent_scale=a.tangent_scale)
    t_emit = time.time() - t0
    n_splats = len(splats["pos"])

    occ = np.argwhere(fleshed != MEDIUM)
    extent_vox = occ.max(axis=0) - occ.min(axis=0)
    extent = float(extent_vox.max())
    scale = TARGET_CM / max(extent, 1.0)
    cloud_radius = float(np.linalg.norm(extent_vox * scale) / 2.0)
    print(f"  lattice {shape}  {n_splats:,} splats  scale {scale:.3f} cm/voxel")

    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    scene = quad_cloud(splats, scale, tangent_scale=a.tangent_scale, overlap=a.quad_overlap)
    n_verts = int(scene.geometry["cloud"].vertices.shape[0])
    splat_glb = OUT / f"splatlimb_{tag}.glb"
    scene.export(str(splat_glb))
    t_splat_export = time.time() - t0
    splat_mb = splat_glb.stat().st_size / 1e6

    t0 = time.time()
    mesh_glb = OUT / f"meshlimb_{tag}.glb"
    bake.bake(fleshed, shape, target_cm=TARGET_CM).export(str(mesh_glb))
    t_mesh_export = time.time() - t0
    mesh_mb = mesh_glb.stat().st_size / 1e6

    quad_h_cm = a.tangent_scale * scale * a.quad_overlap
    print(f"  wrote {splat_glb.name} ({splat_mb:.2f} MB, {n_verts:,} verts) "
          f"+ {mesh_glb.name} ({mesh_mb:.2f} MB)")
    print(f"DENSITY_ROW tag={tag} target_len={a.target_len} splats={n_splats} "
          f"verts={n_verts} scale_cm_per_voxel={scale:.4f} quad_halfsize_cm={quad_h_cm:.4f} "
          f"grow_s={t_grow:.3f} emit_s={t_emit:.3f} splat_export_s={t_splat_export:.3f} "
          f"mesh_export_s={t_mesh_export:.3f} splat_glb_mb={splat_mb:.3f} mesh_glb_mb={mesh_mb:.3f}")

    results = {"tag": tag, "target_len": a.target_len, "tangent_scale": a.tangent_scale,
               "quad_overlap": a.quad_overlap, "shape": list(shape), "splats": n_splats,
               "verts": n_verts, "scale_cm_per_voxel": scale, "quad_halfsize_cm": quad_h_cm,
               "grow_s": t_grow, "emit_s": t_emit, "splat_export_s": t_splat_export,
               "mesh_export_s": t_mesh_export, "splat_glb_mb": splat_mb, "mesh_glb_mb": mesh_mb}
    (OUT / f"density_{tag}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    if a.no_editor:
        print("\n  --no-editor: headless density row only, no in-engine check.")
        return 0

    print("\ndriving the live editor (photo_studio solved portrait) ...")
    log = drive_density_study(splat_glb, cloud_radius, tag=tag, try_nanite=not a.no_nanite)
    for step, (ok, msg) in log.items():
        print(f"  {'OK ' if ok else 'FAIL'} {step:<24} {str(msg)[:100]}")
    good = all(ok for ok, _ in log.values())

    if a.sun_sweep:
        print("\nrunning the ORIGINAL rung D' sun-sweep (tb-0170) ...")
        log2 = drive(splat_glb, mesh_glb)
        for step, (ok, msg) in log2.items():
            print(f"  {'OK ' if ok else 'FAIL'} {step:<18} {str(msg)[:90]}")

    print("\n  SPLATS UNDER SUBSTRATE." if good else "\n  Some in-engine steps failed — see above.")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
