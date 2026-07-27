"""system_to_ue5 — stand on a grown world: the solar ladder wired into the live editor.

Commissioned 2026-07-18 (tb-0195, the human: "wiring a grown system into UE5 so you
can stand on one of these worlds (workflow development)"). This is a WORKFLOW, not a
stunt: re-runnable, idempotent (destroys its own actors first), reading only trained
artifacts, driving only proven MCP pathways.

THE SCALE LADDER AT PLAY (docs/THE_COMPOSITIONAL_WORLD_MODEL.md section 13/18):
standing on a planet, the planet IS the ground — one average, fractured to a local
patch — while the REST of the system coalesces into sky: the star is a light with a
disk, sibling planets are wandering points. Chain consumed:

    docs/objectives/bigbang.systems.json   (solar rung: 5 grown systems, m/a/e)
    docs/objectives/planet.trained.json    (planet rung: trained climate laws)
        -> core.trainables.planet.resolve_system: each planet ONE state
        -> this module: ocean world = ground patch at the origin;
           star = emissive-scale sphere + the level's DirectionalLight aimed
           along the true star azimuth; siblings = spheres on the ecliptic
           band at their TRUE relative azimuths (deterministic golden-angle
           orbital phases — the catalog stores no phases; a visualization
           choice, documented, not physics).

PROVEN PATHWAYS ONLY (docs/MCP_PATHWAYS.md): control_actor destroy_actor (the real
verb — delete_actor is a silent no-op), spawn_actor with /Engine/BasicShapes,
set_transform, find_by_class; control_editor screenshot mode=editor_viewport (H-2).
Materials are deliberately OUT OF SCOPE for this lane (the matter-library /
splat aesthetic pass is its own rung); this lane is GEOMETRY, LIGHT, THE WITNESS.

Run:  python -m core.system_to_ue5 [--system 0] [--shot name.png]
Then: python -m core.witness_runner --beats docs/beats/solar_system_stand.beats.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from core.telemetry_probe import MCPStdioClient
from core.trainables.planet import resolve_system

CATALOG = Path(r"E:\PythonChimera\Chimera\docs\objectives\bigbang.systems.json")
PLANET_TRAINED = Path(r"E:\PythonChimera\Chimera\docs\objectives\planet.trained.json")

GOLDEN_DEG = 137.50776       # deterministic orbital phases for siblings
STAR_DIST_UU = 1_400_000.0   # 14 km out
STAR_DIAM_UU = 90_000.0      # ~3.7 deg disk — a close-in star looms larger than Sol
SIB_ELEV_DEG = 15.0          # ecliptic band elevation (surface-view convention)
SIB_BASE_UU = 500_000.0      # 5 km
SIB_STEP_UU = 250_000.0      # + 2.5 km per rank of true separation
SIB_DIAM_UU = 16_000.0       # 160 m per Earth-radius (angular ~1-2 deg)
GROUND_SCALE = 1000.0        # engine Plane 100uu -> 1 km standing patch
SUN_ELEV_DEG = 35.0          # afternoon light on the ocean world


def _ok(resp):
    try:
        sc = resp["result"]["structuredContent"]
        return bool(sc.get("success", True)), sc.get("message", "")
    except (KeyError, TypeError):
        return False, str(resp)[:160]


def _spawn_sphere(c, name, x, y, z, diam_uu):
    c.call("control_actor", {"action": "destroy_actor", "actorName": name})
    ok, msg = _ok(c.call("control_actor", {
        "action": "spawn_actor", "classPath": "/Script/Engine.StaticMeshActor",
        "meshPath": "/Engine/BasicShapes/Sphere", "actorName": name,
        "location": {"x": x, "y": y, "z": z}}))
    if ok:
        s = diam_uu / 100.0
        c.call("control_actor", {"action": "set_transform", "actorName": name,
                                 "location": {"x": x, "y": y, "z": z},
                                 "scale": {"x": s, "y": s, "z": s}})
    return ok, msg


def wire(system_idx: int = 0, shot: str = "grown_world_stand.png") -> dict:
    catalog = json.loads(CATALOG.read_text())
    genome = json.loads(PLANET_TRAINED.read_text())["genome"]
    planets = catalog["systems"][system_idx]
    states = resolve_system(planets, genome)

    stand = next((p for p in states if p["class"] == "ocean"), None)
    if stand is None:
        raise SystemExit(f"system {system_idx} grew no ocean world — pick another")
    sibs = [p for p in states if p is not stand]

    log = {}
    c = MCPStdioClient()
    try:
        # THE GROUND: the ocean world, fractured to a 1 km standing patch.
        c.call("control_actor", {"action": "destroy_actor",
                                 "actorName": "Grown_Ground"})
        ok, msg = _ok(c.call("control_actor", {
            "action": "spawn_actor", "classPath": "/Script/Engine.StaticMeshActor",
            "meshPath": "/Engine/BasicShapes/Plane", "actorName": "Grown_Ground",
            "location": {"x": 0.0, "y": 0.0, "z": 20.0}}))
        if ok:
            c.call("control_actor", {"action": "set_transform",
                "actorName": "Grown_Ground",
                "location": {"x": 0.0, "y": 0.0, "z": 20.0},
                "scale": {"x": GROUND_SCALE, "y": GROUND_SCALE, "z": 1.0}})
        log["ground"] = (ok, msg[:60])

        # THE STAR: true azimuth from the standing world toward the system
        # barycenter (phase convention puts the standing world at +X).
        az_star = math.radians(180.0)
        el_star = math.radians(SUN_ELEV_DEG)
        sx = STAR_DIST_UU * math.cos(el_star) * math.cos(az_star)
        sy = STAR_DIST_UU * math.cos(el_star) * math.sin(az_star)
        sz = STAR_DIST_UU * math.sin(el_star)
        log["star"] = _spawn_sphere(c, "Grown_Star", sx, sy, sz, STAR_DIAM_UU)

        # THE LIGHT: aim the level's DirectionalLight down the star direction.
        r = c.call("control_actor", {"action": "find_by_class",
                                     "className": "DirectionalLight"})
        try:
            lights = r["result"]["structuredContent"]["result"]["data"]["actors"]
        except (KeyError, TypeError):
            lights = []
        if lights:
            ok, msg = _ok(c.call("control_actor", {
                "action": "set_transform", "actorName": lights[0]["name"],
                "rotation": {"pitch": -SUN_ELEV_DEG,
                             "yaw": math.degrees(az_star) - 180.0,
                             "roll": 0.0}}))
            log["light"] = (ok, f"{lights[0]['name']} aimed")
        else:
            log["light"] = (False, "no DirectionalLight in level")

        # THE SIBLINGS: true relative azimuths from deterministic phases,
        # ranked display distance, ecliptic-band elevation.
        a_s = stand["a_au"]
        rel = []
        for i, p in enumerate(sibs):
            th = math.radians(GOLDEN_DEG * (i + 1))
            dx = p["a_au"] * math.cos(th) - a_s
            dy = p["a_au"] * math.sin(th)
            rel.append((math.hypot(dx, dy), math.atan2(dy, dx), p))
        rel.sort(key=lambda t: t[0])
        el = math.radians(SIB_ELEV_DEG)
        for rank, (sep, az, p) in enumerate(rel):
            d = SIB_BASE_UU + SIB_STEP_UU * rank
            x = d * math.cos(el) * math.cos(az)
            y = d * math.cos(el) * math.sin(az)
            z = d * math.sin(el)
            name = f"Grown_P{rank}_{p['class']}"
            log[name] = _spawn_sphere(c, name, x, y, z,
                                      SIB_DIAM_UU * max(p["radius"], 0.5))

        c.call("control_editor", {"action": "console_command",
                                  "command": "BugItGo 0 -600 200 8 90 0"})
        import time
        time.sleep(2.2)                      # capture race: settle (proven)
        ok, msg = _ok(c.call("control_editor", {
            "action": "screenshot", "filename": shot,
            "mode": "editor_viewport"}))
        log["screenshot"] = (ok, shot)
    finally:
        c.close()

    print(f"STANDING WORLD: ocean @ {stand['a_au']:.2f} AU, "
          f"{stand['t_surf']:.0f} K, {stand['ocean_cov'] * 100:.0f}% water, "
          f"{stand['m_earth']:.1f} M_e")
    for k, (ok, msg) in log.items():
        print(f"  {'OK ' if ok else 'FAIL'} {k:<22} {msg}")
    return log


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--system", type=int, default=0)
    ap.add_argument("--shot", default="grown_world_stand.png")
    a = ap.parse_args()
    log = wire(a.system, a.shot)
    return 0 if all(ok for ok, _ in log.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
