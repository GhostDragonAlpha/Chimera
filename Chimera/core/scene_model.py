"""scene_model — the editor world held as MATH, so nothing is ever found by looking.

Commissioned 2026-07-18, the human, watching the camera fumble by screenshots:
"You shouldn't be doing any of this by looking at the camera... you don't even need to
look at screenshots if you understand the phys, the math, the science... the entire
game world is just one giant cube. Just think about the maximum coordinate space of
Unreal Engine. THIS is what I mean by world model."

THE INVERSION: the world model is not only the game's substrate — it is the AGENT'S
SENSES. An LLM has no embodied spatial intuition, so it must not navigate by pixels.
Instead:

    1. INGEST   — one bulk read of the live world: every actor, class, transform.
                  The world is a bounded cube (UE coordinate space); every thing in it
                  is a coordinate + extent. Held here as typed state.
    2. DERIVE   — cameras, framings, visibility, occlusion, clear ground: ALL solved
                  from the state analytically (photo_studio's solver on this state).
    3. PREDICT  — before any screenshot: what SHOULD be in frame (which actors, at
                  what screen coverage). The prediction is written down first.
    4. VERIFY   — the screenshot is compared against the prediction. A mismatch is
                  never debugged by more looking: it is EVIDENCE — either the model
                  is stale (re-ingest) or a pathway LIES (record the trap). The
                  set_transform-vs-render divergence of 2026-07-18 becomes a one-step
                  detection instead of five hand-aimed screenshots.

Prediction error IS the training signal — the same loop the game's own features train
under, pointed at the agent's own tooling.

Run:  python -m core.scene_model            (ingest + inventory + a solved prediction)
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from core.telemetry_probe import MCPStdioClient

# The cube. UE5 large-world coords go much further, but the PLAYABLE studio world
# lives well inside classic WORLD_MAX; anything outside this is flagged as suspect.
WORLD_HALF_CM = 2_097_152.0
FOV_H_DEG = 90.0

# Classes worth holding (extend as the world grows richer).
CLASSES = ("StaticMeshActor", "DirectionalLight", "SkyLight", "NiagaraActor",
           "Character", "Pawn", "ExponentialHeightFog", "VolumetricCloud")

# Known extents (cm) for things whose size the DATA already tells us — never guessed
# by looking. Anything unknown gets a conservative default and is marked so.
KNOWN_RADIUS = {"Splat_Cloud": 160.0, "Mesh_Skin": 85.0, "Studio_Ground": 3000.0}
DEFAULT_RADIUS = 120.0


class SceneModel:
    def __init__(self, client=None):
        self.c = client or MCPStdioClient()
        self.actors: dict[str, dict] = {}

    # --- 1. INGEST ------------------------------------------------------------

    def ingest(self) -> int:
        self.actors.clear()
        for cls in CLASSES:
            r = self.c.call("control_actor", {"action": "find_by_class",
                                              "className": cls})
            try:
                found = r["result"]["structuredContent"]["result"]["data"]["actors"]
            except (KeyError, TypeError):
                continue
            for a in found:
                name = a.get("name")
                if not name:
                    continue
                t = self.c.call("control_actor", {"action": "get_transform",
                                                  "actorName": name})
                try:
                    d = t["result"]["structuredContent"]["result"]["data"]
                    loc = np.array(d["location"], dtype=float)
                    scale = np.array(d["scale"], dtype=float)
                except (KeyError, TypeError):
                    continue
                r0 = KNOWN_RADIUS.get(name, DEFAULT_RADIUS) * float(np.max(scale))
                self.actors[name] = {
                    "class": cls, "loc": loc, "rot": np.array(d.get("rotation", [0, 0, 0]), float),
                    "scale": scale, "radius": r0,
                    "radius_known": name in KNOWN_RADIUS,
                    "in_cube": bool(np.all(np.abs(loc) < WORLD_HALF_CM)),
                }
        return len(self.actors)

    # --- 2. DERIVE ------------------------------------------------------------

    def solve_camera(self, target: str, azim_deg=205.0, elev_deg=12.0, fill=0.65):
        s = self.actors[target]
        rad = s["radius"]
        d = max(rad / (fill * math.tan(math.radians(FOV_H_DEG) / 2)), rad * 1.5)
        az, el = math.radians(azim_deg), math.radians(elev_deg)
        eye = s["loc"] + np.array([math.cos(el) * math.cos(az),
                                   math.cos(el) * math.sin(az),
                                   math.sin(el)]) * d
        look = s["loc"] - eye
        yaw = math.degrees(math.atan2(look[1], look[0]))
        pitch = math.degrees(math.asin(look[2] / np.linalg.norm(look)))
        return eye, pitch, yaw

    # --- 3. PREDICT -----------------------------------------------------------

    def predict(self, eye: np.ndarray, pitch_deg: float, yaw_deg: float) -> list[dict]:
        """What a camera at (eye, pitch, yaw) SHOULD see: every held actor tested
        against the frustum by angle, with approximate screen coverage from its
        radius/distance. Sorted by coverage. This is written BEFORE any screenshot."""
        p, y = math.radians(pitch_deg), math.radians(yaw_deg)
        fwd = np.array([math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), math.sin(p)])
        half = math.radians(FOV_H_DEG) / 2
        out = []
        for name, a in self.actors.items():
            rel = a["loc"] - eye
            dist = float(np.linalg.norm(rel))
            if dist < 1e-3:
                continue
            ang = math.acos(float(np.clip(rel @ fwd / dist, -1, 1)))
            ang_rad = math.atan2(a["radius"], dist)
            visible = ang - ang_rad < half
            coverage = (ang_rad / half) ** 2 if visible else 0.0
            out.append({"name": name, "visible": visible,
                        "coverage": round(min(coverage, 1.0), 4),
                        "dist_cm": round(dist, 1),
                        "off_axis_deg": round(math.degrees(ang), 1)})
        out.sort(key=lambda e: -e["coverage"])
        return out

    def expectation(self, target: str, **kw) -> dict:
        eye, pitch, yaw = self.solve_camera(target, **kw)
        pred = self.predict(eye, pitch, yaw)
        return {"camera": {"eye": [round(v, 1) for v in eye],
                           "pitch": round(pitch, 1), "yaw": round(yaw, 1)},
                "bugitgo": f"BugItGo {eye[0]:.0f} {eye[1]:.0f} {eye[2]:.0f} "
                           f"{pitch:.1f} {yaw:.1f} 0",
                "must_see": [e for e in pred if e["visible"] and e["coverage"] > 0.02],
                "clutter": [e["name"] for e in pred
                            if e["visible"] and 0 < e["coverage"] <= 0.02]}

    def close(self):
        self.c.close()


def main() -> int:
    m = SceneModel()
    try:
        n = m.ingest()
        print(f"WORLD CUBE ingested: {n} held actors (of the classes the model tracks)")
        for name, a in sorted(m.actors.items(), key=lambda kv: kv[0]):
            flag = "" if a["in_cube"] else "  !! OUTSIDE THE CUBE"
            known = "known" if a["radius_known"] else "assumed"
            print(f"  {name:<24} {a['class']:<20} loc=({a['loc'][0]:.0f},"
                  f"{a['loc'][1]:.0f},{a['loc'][2]:.0f}) r~{a['radius']:.0f}cm "
                  f"[{known}]{flag}")
        if "Splat_Cloud" in m.actors:
            exp = m.expectation("Splat_Cloud")
            print("\nPREDICTION for the Splat_Cloud portrait (written before any pixel):")
            print(json.dumps(exp, indent=1))
    finally:
        m.close()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
