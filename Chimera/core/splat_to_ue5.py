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
PORTRAIT_FILL = 0.45      # fill for an ELONGATED subject: its bounding-SPHERE radius is
# the half-diagonal, so fill=0.7 puts a 90-degree camera ~0.5 radii from the surface and
# the frame is wall-to-wall speckle (seen live, tl224). 0.45 backs off to ~2.2 radii.


def quad_cloud(splats: dict, scale: float, tangent_scale: float = 1.15,
              overlap: float = 1.35) -> "object":
    """One small double-sided quad per splat, oriented by its normal, colored by ITS
    OWN albedo (COLOR_0). Quad half-size = tangent_scale (the SAME voxel-space footprint
    passed to emit_limb — the emission's own disk radius, not a re-guessed number) x
    scale (cm/voxel) x overlap (closes seams between neighbouring quads; tb-0179: shrink
    this ALONGSIDE tangent_scale, not instead of finer voxel pitch, when pushing density
    up — the recipe's lever (2), independent of lever (1)).

    UNITS (the 100x plate bug, found by engine bounds read-back, tl224 2026-07-18):
    glTF's spec unit is METERS; UE's importer multiplies by 100 on the m->cm convert.
    This function's math is in CENTIMETERS (scale = cm/voxel), so the export step below
    divides by 100 — the GLB carries meters, the importer's x100 restores true size.
    Before this fix every splat GLB spawned 100x oversized: the first 22.6k cloud's
    bounds measured 87 METERS ([3234, 8690, 3799] cm extent for an 87.7cm-radius GLB),
    which is the mechanism behind the human's original 'giant plates' — 2.7cm quads
    rendered as 2.7 METER slabs. The prediction-vs-pixels loop plus one
    get_actor_bounds call caught what three sessions of eyeballing had not measured."""
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
    verts = verts * 0.01                                        # cm -> glTF METERS (see docstring)
    base = np.arange(len(pos)) * 4
    f1 = np.stack([base, base + 1, base + 2], axis=1)
    f2 = np.stack([base, base + 2, base + 3], axis=1)
    faces = np.concatenate([f1, f2])       # single-sided; glTF doubleSided flag
    # (injected by write_splat_glb) replaces the old duplicated-reversed-faces
    # hack — half the triangles, same coverage
    rgba = np.concatenate([np.clip(splats["albedo"], 0, 1),
                           np.clip(splats["alpha"], 0, 1)[:, None]], axis=1)
    vcol = (np.repeat(rgba, 4, axis=0) * 255).astype(np.uint8)
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, vertex_colors=vcol, process=False)
    scene = trimesh.Scene()
    scene.add_geometry(mesh, node_name="cloud", geom_name="cloud")
    return scene


def _inject_material(glb_path: Path) -> None:
    """Make the GLB SELF-DESCRIBING: declare a PBR material on the primitive.

    ROOT CAUSE (found by pixel-forensics, 2026-07-18): trimesh's ColorVisuals
    path exports COLOR_0 but NO material; UE's glTF importer then assigns a dead
    default that ignores vertex color, so every splat imported WHITE (verified:
    blob mean RGB 224.7/223.3/221.5 — neutral — where skin tint demands R>G>B by
    ~46 8-bit steps; the debug-material override showed white = missing attr).
    Per the glTF spec a declared material MUST be multiplied by COLOR_0, and
    UE's importer builds that graph when — and only when — a material exists in
    the file. doubleSided=true here replaces geometric double-siding."""
    import struct

    with open(glb_path, "rb") as f:
        magic, ver, _total = struct.unpack("<III", f.read(12))
        clen, ctype = struct.unpack("<II", f.read(8))
        doc = json.loads(f.read(clen))
        rest = f.read()                                    # BIN chunk(s), untouched
    doc["materials"] = [{
        "name": "M_SplatVC",
        "pbrMetallicRoughness": {"baseColorFactor": [1.0, 1.0, 1.0, 1.0],
                                  "metallicFactor": 0.0, "roughnessFactor": 0.85},
        "doubleSided": True,
    }]
    for mesh in doc.get("meshes", []):
        for prim in mesh.get("primitives", []):
            prim["material"] = 0
    payload = json.dumps(doc, separators=(",", ":")).encode()
    payload += b" " * (-len(payload) % 4)                  # 4-byte alignment (spec)
    with open(glb_path, "wb") as f:
        f.write(struct.pack("<III", magic, ver, 12 + 8 + len(payload) + len(rest)))
        f.write(struct.pack("<II", len(payload), ctype))
        f.write(payload)
        f.write(rest)


def write_splat_glb(splats: dict, scale: float, path: Path, **kw) -> Path:
    """Export + material injection in one step — the only correct way to write
    a splat GLB for engine import (a bare quad_cloud().export() produces the
    dead-default-material import; see _inject_material)."""
    quad_cloud(splats, scale, **kw).export(str(path))
    _inject_material(path)
    return path


SPLAT_MATERIAL = "/Game/Materials/M_SplatVC_Lit"


def ensure_splat_material(client, material_path: str = SPLAT_MATERIAL) -> bool:
    """Author (idempotently) the LIT per-splat-color material via the bridge and
    return True when it exists wired: VertexColor -> BaseColor, DefaultLit — under
    r.Substrate=1 this auto-converts to a Substrate slab, so splats are engine-lit
    with their own COLOR_0 per particle.

    THE MAZE THIS ENCODES (paid for 2026-07-18, tb-0170 — do not rediscover it):
    - The bridge has THREE material handler families (MaterialGraph /
      MaterialAuthoring / the JS router above both) with DIFFERENT key vocab.
      `connect_material_pins` lives in MaterialAuthoring; nodes added by the
      MaterialGraph family (`add_material_node`) are found by the authoring
      family's lookup ONLY when the connect payload carries the full
      belt-and-suspenders key set below — single-key variants return
      NODE_NOT_FOUND / INVALID_PIN misleadingly.
    - A Custom-HLSL node reading `Parameters.VertexColor` compiles but samples
      BLACK: raw access does not set the material's bUsesVertexColor usage flag,
      so the interpolator is stripped. Only a real MaterialExpressionVertexColor
      node sets the flag — that is why this authors the real node.
    - `add_material_node` returns nodeId = the expression object's GetName()
      (e.g. 'MaterialExpressionVertexColor_0'); it is stable per-asset."""
    import json as _json

    def sc(r):
        try:
            return r["result"]["structuredContent"]
        except (KeyError, TypeError):
            return {}

    client.call("manage_asset", {"action": "create_material",
                                 "name": material_path.rsplit("/", 1)[-1],
                                 "destinationPath": material_path.rsplit("/", 1)[0]})
    add = sc(client.call("manage_asset", {"action": "add_material_node",
                                          "assetPath": material_path,
                                          "nodeType": "VertexColor"}))
    nid = ((add.get("data") or {}).get("result") or add.get("result") or {}) \
        .get("nodeId") or add.get("nodeId") or "MaterialExpressionVertexColor_0"
    conn = sc(client.call("manage_asset", {
        "action": "connect_material_pins",
        "assetPath": material_path, "materialPath": material_path,
        "sourceNodeId": nid, "fromExpression": nid, "sourceNode": nid, "nodeId": nid,
        "inputName": "BaseColor", "targetNodeId": "Main",
        "targetPin": "BaseColor", "sourcePin": "0"}))
    built = sc(client.call("manage_asset", {"action": "rebuild_material",
                                            "assetPath": material_path}))
    return bool(conn.get("success")) and bool(built.get("success"))


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
            # NOT "delete_actor" — that action does not exist in the bridge (silent no-op;
            # McpTool_ControlActor.cpp registers "delete"/"destroy_actor"). Found live
            # 2026-07-18 when a "deleted" cloud photobombed the next portrait.
            c.call("control_actor", {"action": "destroy_actor", "actorName": name})
            ok, msg = _ok(c.call("control_actor", {
                "action": "spawn_actor", "classPath": "/Script/Engine.StaticMeshActor",
                "meshPath": path, "actorName": name,
                "location": {"x": x, "y": 0.0, "z": SPAWN_Z}}))
            log[f"spawn:{name}"] = (ok, msg)

        # LIT per-splat color: author (idempotent) + apply the VertexColor->BaseColor
        # material — without this the importer's default ignores COLOR_0 and the
        # cloud renders grey (the whole 2026-07-18 material odyssey, encoded).
        ok = ensure_splat_material(c)
        log["material:wired"] = (ok, SPLAT_MATERIAL if ok else "authoring failed")
        if ok:
            ok2, msg2 = _ok(c.call("control_actor", {
                "action": "set_material", "actorName": "Splat_Cloud",
                "materialPath": SPLAT_MATERIAL, "slot": 0}))
            log["material:applied"] = (ok2, msg2)

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

        c.call("control_actor", {"action": "destroy_actor", "actorName": "Splat_Cloud"})
        ok, msg = _ok(c.call("control_actor", {
            "action": "spawn_actor", "classPath": "/Script/Engine.StaticMeshActor",
            "meshPath": mesh_path, "actorName": "Splat_Cloud",
            "location": {"x": 0.0, "y": 0.0, "z": 0.0}}))
        log["spawn:Splat_Cloud"] = (ok, msg)

        placed, msg = st.place("Splat_Cloud", 0, cloud_radius)
        log["place:Splat_Cloud"] = (placed, msg)

        sm = SceneModel(client=c)
        n = sm.ingest()
        log["scene_model:ingest"] = (n > 0, f"{n} actors held")
        if "Splat_Cloud" in sm.actors:
            # ONE radius for prediction AND portrait — scene_model's KNOWN_RADIUS table
            # holds 160cm baked from the FIRST (22.6k) cloud; solving the prediction with
            # the stale constant while the portrait used the true export-time radius put
            # the two cameras 117cm apart, and the divergence showed up as pixels-vs-
            # prediction mismatch (caught live, tl224, 2026-07-18 — the one-step stale-
            # model detection scene_model's docstring promises). The export-time radius
            # is the DATA; the table is only a fallback for actors with no exporter.
            sm.actors["Splat_Cloud"]["radius"] = float(cloud_radius)
            sm.actors["Splat_Cloud"]["radius_known"] = True
            exp = sm.expectation("Splat_Cloud", azim_deg=205.0, elev_deg=12.0, fill=PORTRAIT_FILL)
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

        if placed:               # portrait only if the subject registered (KeyError guard —
            # the first tl224 run died HERE unlogged when place failed, taking the whole
            # step log with it; a failed step must fail ITS OWN line, not the report)
            shot = st.portrait("Splat_Cloud", fill=PORTRAIT_FILL)  # SOLVED camera, settled
            log["portrait"] = (True, str(shot))
        else:
            log["portrait"] = (False, "skipped: place failed, no registered subject to solve for")
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
    ap.add_argument("--no-raster", action="store_true",
                    help="skip the per-pixel/tiled ms-per-frame measurement (GPU required)")
    ap.add_argument("--raster-wide", action="store_true",
                    help="ALSO time a wide framing (3x radius -> mostly-empty tiles) — "
                         "isolates the tile pipeline's real advantage (sparse occupancy) "
                         "from a tight portrait where the object fills most of the frame")
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

    results = {"tag": tag, "target_len": a.target_len, "tangent_scale": a.tangent_scale,
               "quad_overlap": a.quad_overlap, "shape": list(shape), "splats": n_splats,
               "verts": n_verts, "scale_cm_per_voxel": scale, "quad_halfsize_cm": quad_h_cm,
               "grow_s": t_grow, "emit_s": t_emit, "splat_export_s": t_splat_export,
               "mesh_export_s": t_mesh_export, "splat_glb_mb": splat_mb, "mesh_glb_mb": mesh_mb}

    if not a.no_raster:
        from core import splat_gpu as sg
        center_vox = (occ.min(axis=0) + occ.max(axis=0)) / 2.0
        radius_vox = extent / 2.0 * 1.15
        if sg.available():
            _ = sg.rasterize(splats, center_vox, radius_vox, -60, 20, 60, 35, 340, 340)
            t0 = time.time(); img_pp = sg.rasterize(splats, center_vox, radius_vox, -60, 20, 60, 35, 340, 340)
            t_pp = time.time() - t0
            _ = sg.rasterize_tiled(splats, center_vox, radius_vox, -60, 20, 60, 35, 340, 340)
            t0 = time.time(); img_tl = sg.rasterize_tiled(splats, center_vox, radius_vox, -60, 20, 60, 35, 340, 340)
            t_tl = time.time() - t0
            mae_rt = float(np.abs(img_pp - img_tl).mean())
            results["per_pixel_ms"] = t_pp * 1000
            results["tiled_ms"] = t_tl * 1000
            results["per_pixel_vs_tiled_mae"] = mae_rt
            print(f"  rasterizer (tight, fill~0.84): per-pixel={t_pp*1000:.2f}ms  "
                  f"tiled={t_tl*1000:.2f}ms  MAE={mae_rt:.5f}  "
                  f"(wall={MALCOLM_FRAME_MS}ms: per-pixel {'HOLDS' if t_pp*1000<=MALCOLM_FRAME_MS else 'MISSES'}, "
                  f"tiled {'HOLDS' if t_tl*1000<=MALCOLM_FRAME_MS else 'MISSES'})")

            if a.raster_wide:
                wide_r = radius_vox * 3.0     # object fills ~1/9 the area -> mostly-empty tiles
                _ = sg.rasterize(splats, center_vox, wide_r, -60, 20, 60, 35, 340, 340)
                t0 = time.time(); sg.rasterize(splats, center_vox, wide_r, -60, 20, 60, 35, 340, 340)
                t_pp_w = time.time() - t0
                _ = sg.rasterize_tiled(splats, center_vox, wide_r, -60, 20, 60, 35, 340, 340)
                t0 = time.time(); sg.rasterize_tiled(splats, center_vox, wide_r, -60, 20, 60, 35, 340, 340)
                t_tl_w = time.time() - t0
                results["per_pixel_ms_wide3x"] = t_pp_w * 1000
                results["tiled_ms_wide3x"] = t_tl_w * 1000
                print(f"  rasterizer (WIDE 3x radius, sparse occupancy): per-pixel={t_pp_w*1000:.2f}ms  "
                      f"tiled={t_tl_w*1000:.2f}ms  speedup x{t_pp_w/max(t_tl_w,1e-9):.2f}")
        else:
            print("  rasterizer: no CUDA device — skipped (use --no-raster to silence this)")

    print(f"DENSITY_ROW tag={tag} target_len={a.target_len} splats={n_splats} "
          f"verts={n_verts} scale_cm_per_voxel={scale:.4f} quad_halfsize_cm={quad_h_cm:.4f} "
          f"grow_s={t_grow:.3f} emit_s={t_emit:.3f} splat_export_s={t_splat_export:.3f} "
          f"mesh_export_s={t_mesh_export:.3f} splat_glb_mb={splat_mb:.3f} mesh_glb_mb={mesh_mb:.3f} "
          f"per_pixel_ms={results.get('per_pixel_ms')} tiled_ms={results.get('tiled_ms')}")
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
