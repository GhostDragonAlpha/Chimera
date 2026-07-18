"""photo_studio — a deterministic photography studio inside the live editor.

Commissioned 2026-07-18, the human, on watching the camera fumbling: "You have no idea
how to move a camera in three dimensional space since you've never done that before...
we need some sort of consistent method. You can put everything together in your head
and make things arrange right but you can't do this."

Correct. An LLM has no embodied spatial intuition — every hand-typed BugItGo is a
guess. So this module removes intuition from the loop entirely, the same way the
trainer removed hand-tuning: THE CAMERA IS SOLVED, NEVER EYEBALLED.

THE STUDIO:
- A reserved stage block far from the playfield (STAGE origin), with a spawned
  engine-shape ground plane as a clean backdrop. No dust fountains, no mannequins.
- Subjects are placed at EXACT stage slots (set_transform is proven reliable).
- Every subject carries its KNOWN extent (measured at export/emission time — the
  exporter knows the true bounds; nothing is estimated by looking).
- frame() computes the camera from geometry: given subject center c, radius r, a
  view direction (azim/elev) and a fill fraction, the distance is
      d = r / (fill * tan(fov/2))
  and pitch/yaw point the camera back along the view direction. BugItGo gets the
  eight solved numbers. A settle delay defeats the capture race (proven 2026-07-18:
  the bridge executes commands for real but an immediate screenshot grabs the
  PRE-command frame; ~2s settles it).

Result: turntables, side-by-sides and contact sheets that frame correctly EVERY time,
because no number in them was ever guessed.

Run:  python -m core.photo_studio            (stages the splat cloud + mesh limb demo)
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np

from core.telemetry_probe import MCPStdioClient

OUT = Path(r"E:\PythonChimera\Chimera\Saved\PhotoStudio")
STAGE = np.array([20000.0, 20000.0, 200.0])     # cm — 200 m from the playfield
SLOT_SPACING = 400.0                             # cm between subject slots
GROUND = "Studio_Ground"
FOV_H_DEG = 90.0                                 # editor perspective default
SETTLE_S = 2.2


def _ok(resp):
    try:
        sc = resp["result"]["structuredContent"]
        return bool(sc.get("success", True)), sc.get("message", "")
    except (KeyError, TypeError):
        return False, str(resp)[:160]


class Studio:
    def __init__(self, client=None):
        self.c = client or MCPStdioClient()
        self.subjects = {}          # name -> {"center": np.array, "radius": float}

    # --- rig ------------------------------------------------------------------

    def build(self):
        """Ground plane at the stage block. Engine basic shapes are stable paths."""
        self.c.call("control_actor", {"action": "delete_actor", "actorName": GROUND})
        ok, msg = _ok(self.c.call("control_actor", {
            "action": "spawn_actor", "classPath": "/Script/Engine.StaticMeshActor",
            "meshPath": "/Engine/BasicShapes/Plane", "actorName": GROUND,
            "location": {"x": STAGE[0], "y": STAGE[1], "z": STAGE[2] - 1.0}}))
        if ok:
            self.c.call("control_actor", {"action": "set_transform", "actorName": GROUND,
                "location": {"x": STAGE[0], "y": STAGE[1], "z": STAGE[2] - 1.0},
                "rotation": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
                "scale": {"x": 60.0, "y": 60.0, "z": 1.0}})
        return ok, msg

    def place(self, actor: str, slot: int, extent_cm: float,
              rotation=(90.0, 0.0, 0.0), z_lift: float | None = None):
        """Put a KNOWN-extent subject at a slot. extent_cm = its bounding radius,
        known from export — never estimated visually. Pivot must be centered
        (splat_to_ue5.quad_cloud centers; bake recentres per tissue)."""
        pos = STAGE + np.array([slot * SLOT_SPACING, 0.0, 0.0])
        pos[2] = STAGE[2] + (z_lift if z_lift is not None else extent_cm * 0.55)
        ok, msg = _ok(self.c.call("control_actor", {
            "action": "set_transform", "actorName": actor,
            "location": {"x": pos[0], "y": pos[1], "z": pos[2]},
            "rotation": {"pitch": rotation[0], "yaw": rotation[1], "roll": rotation[2]},
            "scale": {"x": 1.0, "y": 1.0, "z": 1.0}}))
        if ok:
            self.subjects[actor] = {"center": pos, "radius": float(extent_cm)}
        return ok, msg

    # --- the solved camera ----------------------------------------------------

    def _solve(self, center: np.ndarray, radius: float, azim_deg: float,
               elev_deg: float, fill: float):
        d = radius / (fill * math.tan(math.radians(FOV_H_DEG) / 2.0))
        d = max(d, radius * 1.5)
        az, el = math.radians(azim_deg), math.radians(elev_deg)
        off = np.array([math.cos(el) * math.cos(az),
                        math.cos(el) * math.sin(az),
                        math.sin(el)]) * d
        eye = center + off
        look = center - eye
        yaw = math.degrees(math.atan2(look[1], look[0]))
        pitch = math.degrees(math.asin(look[2] / np.linalg.norm(look)))
        return eye, pitch, yaw

    def shoot(self, name: str, center, radius, azim, elev,
              fill: float = 0.65) -> Path:
        eye, pitch, yaw = self._solve(np.asarray(center, float), radius, azim, elev, fill)
        self.c.call("control_editor", {"action": "console_command",
            "command": f"BugItGo {eye[0]:.0f} {eye[1]:.0f} {eye[2]:.0f} "
                       f"{pitch:.1f} {yaw:.1f} 0"})
        time.sleep(SETTLE_S)
        shot = f"{name}.png"
        self.c.call("control_editor", {"action": "screenshot",
                                       "filename": shot, "mode": "editor_viewport"})
        return Path(r"E:\PythonChimera\Chimera\Saved\Screenshots") / shot

    def portrait(self, actor: str, azim=205.0, elev=12.0, fill=0.65) -> Path:
        s = self.subjects[actor]
        return self.shoot(f"studio_{actor}", s["center"], s["radius"], azim, elev, fill)

    def turntable(self, actor: str, n: int = 4, elev: float = 12.0) -> list:
        s = self.subjects[actor]
        return [self.shoot(f"studio_{actor}_az{int(a)}", s["center"], s["radius"], a, elev)
                for a in np.linspace(0, 360, n, endpoint=False)]

    def pair(self, a: str, b: str, azim=205.0, elev=10.0) -> Path:
        sa, sb = self.subjects[a], self.subjects[b]
        center = (sa["center"] + sb["center"]) / 2.0
        radius = float(np.linalg.norm(sa["center"] - sb["center"]) / 2.0
                       + max(sa["radius"], sb["radius"]))
        return self.shoot(f"studio_pair_{a}_{b}", center, radius, azim, elev, 0.75)

    def close(self):
        self.c.close()


def main() -> int:
    """Demo: rebuild the CENTERED splat cloud, refresh the import, stage both
    subjects in the studio, portrait + pair. Extents come from the DATA."""
    from core import bake, limb
    from core.splat_emit import MEDIUM, emit_limb
    from core.splat_to_ue5 import DEST, TARGET_CM, quad_cloud

    print("re-exporting centered splat cloud ...")
    _s, fleshed, shape, _t = limb.grow_limb(limb.bent_limb(), seed=0)
    splats = emit_limb(fleshed)
    occ = np.argwhere(fleshed != MEDIUM)
    extent_vox = (occ.max(axis=0) - occ.min(axis=0))
    scale = TARGET_CM / float(extent_vox.max())
    cloud_radius = float(np.linalg.norm(extent_vox * scale) / 2.0)

    out = Path(r"E:\PythonChimera\Chimera\Saved\SubstrateSplats")
    glb = out / "splatlimb.glb"
    quad_cloud(splats, scale).export(str(glb))

    st = Studio()
    try:
        ok, msg = _ok(st.c.call("manage_asset", {
            "action": "import", "sourcePath": str(glb), "destinationPath": DEST}))
        print(f"  reimport: {ok} {msg[:60]}")
        print("  studio ground:", st.build()[0])
        print("  place cloud:", st.place("Splat_Cloud", 0, cloud_radius)[0])
        print("  place mesh: ", st.place("Mesh_Skin", 1, TARGET_CM / 2.0)[0])
        p1 = st.portrait("Splat_Cloud")
        p2 = st.portrait("Mesh_Skin")
        p3 = st.pair("Splat_Cloud", "Mesh_Skin")
        for p in (p1, p2, p3):
            print("  shot ->", p)
    finally:
        st.close()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
