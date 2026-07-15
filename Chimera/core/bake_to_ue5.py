"""rung 2, the in-editor half — the grown limb becomes a NANITE character in live UE5.

core/bake.py turned the voxel anatomy into a UE5-importable GLB. This drives the LIVE
editor (through the MCP bridge, core.telemetry_probe.MCPStdioClient) to:

    1. IMPORT the GLB  -> three static meshes /Game/Grown/limb/StaticMeshes/{skin,muscle,bone}
    2. NANITE each     -> the dense grown surface is now virtualized geometry
    3. SPAWN the three tissues in an exploded anatomical row (skin | muscle | bone)
    4. SCREENSHOT the viewport

This is the moment the Matter Model stops being a picture and becomes a character: the
cellular model, grown by adhesion around an L-system skeleton, is now native UE5 Nanite
geometry that renders and shadows like anything else in the engine.

REQUIRES the editor running with the MCP bridge (port 8091). If it is not up, this fails
loudly rather than pretending — the headless bake (core/bake.py) is what stands on its own.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from core import bake, limb
from core.telemetry_probe import MCPStdioClient

DEST = "/Game/Grown/"
TISSUES = ("skin", "muscle", "bone")
ROW_X = {"skin": 0.0, "muscle": 200.0, "bone": 400.0}      # exploded anatomical row, cm apart
SPAWN_Z = 100.0
CAMERA = "200 -560 110 0 90 0"      # BugItGo: stand back on -Y, look at the row (+Y)


def _ok(resp) -> tuple:
    """(success, message) out of the nested JSON-RPC envelope."""
    try:
        sc = resp["result"]["structuredContent"]
        return bool(sc.get("success")), sc.get("message", "")
    except (KeyError, TypeError):
        return False, json.dumps(resp)[:200] if resp else "no response"


def to_ue5(glb: Path, shot: Path, client=None) -> dict:
    c = client or MCPStdioClient()
    log = {}
    try:
        ok, msg = _ok(c.call("manage_asset", {
            "action": "import", "sourcePath": str(glb), "destinationPath": DEST}))
        log["import"] = (ok, msg)
        meshes = {t: f"{DEST}limb/StaticMeshes/{t}" for t in TISSUES}

        for t, path in meshes.items():
            ok, msg = _ok(c.call("manage_asset", {
                "action": "nanite_rebuild_mesh", "assetPath": path, "meshPath": path,
                "bEnableNanite": True}))
            log[f"nanite:{t}"] = (ok, msg)

        for t in TISSUES:                              # clear any prior run's actors first
            c.call("control_actor", {"action": "delete_actor", "actorName": f"Grown_{t}"})
        for t, path in meshes.items():
            ok, msg = _ok(c.call("control_actor", {
                "action": "spawn_actor", "classPath": "/Script/Engine.StaticMeshActor",
                "meshPath": path, "actorName": f"Grown_{t}",
                "location": {"x": ROW_X[t], "y": 0.0, "z": SPAWN_Z}}))
            log[f"spawn:{t}"] = (ok, msg)

        # camera: stand back on -Y and look toward the row (yaw 90 = +Y)
        c.call("control_editor", {"action": "console_command",
                                  "command": f"BugItGo {CAMERA}"})
        sresp = c.call("control_editor", {
            "action": "screenshot", "filename": str(shot), "mode": "editor_viewport"})
        ok, msg = _ok(sresp)
        log["screenshot"] = (ok, msg or json.dumps(sresp)[:300])
    finally:
        if client is None:
            c.close()
    return log


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--glb", default=None, help="baked GLB; baked fresh if omitted")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--target-cm", type=float, default=170.0, help="limb size in the level")
    ap.add_argument("--shot", default=r"E:\PythonChimera\Chimera\Saved\Grown\limb_ue5.png")
    a = ap.parse_args()

    glb = Path(a.glb) if a.glb else Path(r"E:\PythonChimera\Chimera\Saved\Grown\limb.glb")
    if not a.glb:                                      # always grow + bake a fresh limb
        print(f"growing + baking a fresh limb ({a.target_cm:.0f} cm) -> {glb}")
        _s, fleshed, shape, _t = limb.grow_limb(limb.bent_limb(), seed=a.seed)
        glb.parent.mkdir(parents=True, exist_ok=True)
        bake.bake(fleshed, shape, target_cm=a.target_cm).export(str(glb))

    print(f"driving the live editor with {glb.name} ...")
    log = to_ue5(glb, Path(a.shot))
    print()
    for step, (ok, msg) in log.items():
        print(f"  {'OK ' if ok else 'FAIL'} {step:<16} {msg}")

    good = all(ok for ok, _ in log.values())
    print()
    print("  IN ENGINE. The grown limb is a Nanite mesh rendering in UE5." if good
          else "  Some steps failed — see above. The headless bake (core/bake.py) still stands.")
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
