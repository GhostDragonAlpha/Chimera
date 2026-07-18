"""materialize — SUPERSEDED editor-staged prototype. The REAL bubble is the runtime
UMaterializationSubsystem (generator-owned, Source/Chimera/ProceduralGenerated/
Materialization/, tb-0198) — use that; this file stays as the Python reference
implementation of the forming rule ONLY.

REFUTED AS A REALIZATION (surprise_f14d0396d25cb260, the human's screenshot,
2026-07-18): the GLB path imports ROTATED 90 deg (glTF Y-up vs UE Z-up — the
terrain here is built Z-up and this exporter was never corrected), and tb-0197's
witness asserted existence, not contact — the pawn stood on the flat plane beside
a sideways wall. Editor staging is the WRONG WAY (operator directive): the runtime
subsystem has no glTF, no importer, no staging — the whole bug class dissolves.

Original doctrine text follows (still true — it just lives in C++ now):
the materialization bubble: trained matter FORMS the ground under the player.

Commissioned 2026-07-18 (tb-0197), the human, killing the phrase "aesthetic pass":
"It shouldn't need an aesthetic pass if you have all the LOD for the meaning — I
should be able to have a character that can walk on the planet and essentially
materializes the ground particles around the player. Basically this entire game is
a big fractal that we can zoom in and out of." And the interruption that names this
module's job: "THIS IS THE PART WHERE YOU HAVE TO MIX MATTER TOGETHER."

THE LOD OF MEANING (no aesthetic passes — appearance DERIVES or the model is
incomplete): each scale is the rung below's average. This module walks DOWN one
rung: the planet's climate averages (planet rung) decide a MATTER MIX; the trained
granular rule (matter rung) FORMS it; the matter library colors it; the mesh is
just the current bottom of the ladder, rendered.

THE MIX IS DERIVED, THE ARRANGEMENT IS PHYSICS — nothing is placed:
    ROCK      immovable bedrock cells (crit = FROZEN in the same rule) — a
              deterministic ridge field from the patch seed. Exposed wherever
              the regolith cover thins to nothing: outcrops are WHERE SAND
              COULD NOT REST, never painted.
    REGOLITH  poured onto the bedrock and settled BY THE TRAINED GENOME
              (docs/objectives/granular.trained.json — the 40-degree rule that
              earned its angle against Carrier/Lunar-Sourcebook anchors). The
              relief of the ground IS the fixed point of that rule.
    WATER     only if the planet's resolved state says so (ocean class /
              liquid window): finds its level — a flat sheet at the sea level
              implied by the planet's ocean coverage. Frozen worlds get none
              (ice is a later matter); hot worlds get none.

DETERMINISM IS THE FRACTAL: seed = (system, planet, patch coords). The same
coordinates materialize the same ground, forever — the world is the seed plus the
trained laws; zooming in is decompression, walking away lets it coalesce back to
the average (the flat Grown_Ground plane, which this patch sits INSIDE — one
screenshot shows both LODs of meaning).

Pipeline: chain artifacts -> 2D sandpile (bounded, quiet-stop, totality) ->
classify cells -> per-cell-crisp vertex-colored mesh + water sheet -> GLB
(METERS — the x100 lesson) -> _inject_material (COLOR_0 multiplies only when a
material is declared) -> import -> spawn under the pawn -> M_SplatVC_Lit.

Run:  python -m core.materialize [--system 0] [--patch 0 0] [--no-engine]
Then: python -m core.witness_runner --beats docs/beats/materialized_ground.beats.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from core.trainables.planet import resolve_system

CATALOG = Path(r"E:\PythonChimera\Chimera\docs\objectives\bigbang.systems.json")
PLANET_TRAINED = Path(r"E:\PythonChimera\Chimera\docs\objectives\planet.trained.json")
GRANULAR_TRAINED = Path(r"E:\PythonChimera\Chimera\docs\objectives\granular.trained.json")
MATTER_LIB = Path(r"E:\PythonChimera\Chimera\docs\matter\matter_library.json")
OUT_DIR = Path(r"E:\PythonChimera\Chimera\Saved\Materialize")
DEST = "/Game/Grown/"

N = 160                    # cells per side
CELL_W_CM = 25.0           # patch = 40 m
CELL_H_CM = 12.5           # trained aspect 2:1 (granular CELL_W=2, CELL_H=1)
BASE_Z_UU = 20.0           # sits on the coalesced average plane (Grown_Ground)
MAX_SWEEPS = 4000          # totality: bounded for, quiet-stop
QUIET = 30
FROZEN = 255
RAIN_MEAN = 3.0            # mean regolith depth poured (cells)
N_MOUNDS = 5
MOUND_GRAINS = 2500
N_RIDGES = 6               # bedrock field bumps
RIDGE_AMP = 22.0           # cells (~2.75 m) — crests must OUTRUN the rain so
                           # outcrops emerge where the cover slides off; at 10
                           # the first patch buried every ridge (rock 0%)

FALLBACK_COLORS = {
    "regolith": ([0.42, 0.38, 0.33], 0.05),
    "rock": ([0.26, 0.25, 0.24], 0.03),
    "water": ([0.05, 0.13, 0.22], 0.01),
}


def _library_color(family: str) -> tuple[list[float], float]:
    """Albedo mean + mottle spread from the matter library; fallback if absent."""
    try:
        lib = json.loads(MATTER_LIB.read_text())
        for key in ("materials", "families", "entries"):
            entries = lib.get(key)
            if not isinstance(entries, (dict, list)):
                continue
            items = entries.items() if isinstance(entries, dict) else [
                (e.get("name", ""), e) for e in entries]
            for name, e in items:
                if family not in str(name).lower():
                    continue
                app = e.get("appearance") or {}
                alb = app.get("albedo") or app.get("albedo_mean_rgb") or {}
                mean = (alb.get("mean") if isinstance(alb, dict) else alb) or None
                spread = (alb.get("spread") if isinstance(alb, dict) else None)
                if isinstance(mean, list) and len(mean) == 3:
                    s = float(spread) if isinstance(spread, (int, float)) else \
                        FALLBACK_COLORS[family][1]
                    return [float(v) for v in mean], s
    except (OSError, json.JSONDecodeError, KeyError, AttributeError):
        pass
    return FALLBACK_COLORS[family]


def _form_patch(planet_state: dict, seed: int):
    """Run the trained rule: bedrock (frozen) + poured regolith -> fixed point.
    Returns (heights_cells float array, sand depth, bedrock, masks dict)."""
    genome = json.loads(GRANULAR_TRAINED.read_text())["genome"]
    h_crit_mean, p_topple = genome["h_crit_mean"], genome["p_topple"]
    rng = np.random.default_rng(seed)

    yy, xx = np.mgrid[0:N, 0:N]
    bed = np.zeros((N, N))
    for _ in range(N_RIDGES):
        cx, cy = rng.uniform(0, N, 2)
        sx = rng.uniform(N * 0.08, N * 0.25)
        amp = rng.uniform(0.3, 1.0) * RIDGE_AMP
        bed += amp * np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2)
                              / (2.0 * sx * sx)))
    bed = np.floor(bed).astype(np.int64)

    sand = rng.poisson(RAIN_MEAN, (N, N)).astype(np.int64)
    for _ in range(N_MOUNDS):
        cx, cy = rng.integers(N // 8, N - N // 8, 2)
        gx = np.clip(rng.normal(cx, N * 0.04, MOUND_GRAINS), 0,
                     N - 1).astype(np.int64)
        gy = np.clip(rng.normal(cy, N * 0.04, MOUND_GRAINS), 0,
                     N - 1).astype(np.int64)
        np.add.at(sand, (gy, gx), 1)

    base = int(math.floor(h_crit_mean))
    frac = h_crit_mean - base
    crit = (base + (rng.random((N, N)) < frac)).astype(np.int64)

    INF = 1 << 30
    for sweep in range(MAX_SWEEPS):
        h = bed + sand
        d = np.full((4, N, N), -INF, dtype=np.int64)
        d[0, 1:, :] = h[1:, :] - h[:-1, :]     # to -y
        d[1, :-1, :] = h[:-1, :] - h[1:, :]    # to +y
        d[2, :, 1:] = h[:, 1:] - h[:, :-1]     # to -x
        d[3, :, :-1] = h[:, :-1] - h[:, 1:]    # to +x
        best = d.max(axis=0)
        which = d.argmax(axis=0)
        move = (sand >= 1) & (best > crit) & (rng.random((N, N)) < p_topple)
        if not move.any():
            break
        my, mx = np.nonzero(move)
        w = which[my, mx]
        ty = my + np.where(w == 0, -1, np.where(w == 1, 1, 0))
        tx = mx + np.where(w == 2, -1, np.where(w == 3, 1, 0))
        np.subtract.at(sand, (my, mx), 1)
        np.add.at(sand, (ty, tx), 1)
        # quenched stability resampled where grains land (same rule as trained)
        crit[ty, tx] = base + (rng.random(ty.size) < frac)

    h = bed + sand
    rock = sand <= 0                          # cover thinned to nothing
    return h.astype(float), sand, bed, rock


def _sea_level(h_cells: np.ndarray, planet_state: dict) -> float | None:
    """Water finds its level; the AREA it claims derives from the planet's
    ocean coverage (shoreline-locus bias x3, clamped — a documented siting
    choice: the bubble materializes near a shore, not mid-ocean)."""
    if planet_state["class"] != "ocean" or planet_state["ocean_cov"] <= 0.0:
        return None
    frac = float(np.clip(planet_state["ocean_cov"] * 3.0, 0.05, 0.35))
    return float(np.percentile(h_cells, frac * 100.0))


def build_patch_glb(system_idx: int, patch: tuple[int, int],
                    out: Path) -> dict:
    catalog = json.loads(CATALOG.read_text())
    genome = json.loads(PLANET_TRAINED.read_text())["genome"]
    states = resolve_system(catalog["systems"][system_idx], genome)
    stand = next((p for p in states if p["class"] == "ocean"), states[0])
    planet_idx = states.index(stand)

    seed = abs(hash((system_idx, planet_idx, patch[0], patch[1]))) % (2 ** 31)
    h, sand, bed, rock = _form_patch(stand, seed)
    sea = _sea_level(h, stand)
    water = np.zeros_like(rock) if sea is None else (h < sea)

    rng = np.random.default_rng(seed + 1)
    col_reg, var_reg = _library_color("regolith")
    col_rock, var_rock = _library_color("rock")
    col_wat, _ = _library_color("water")

    # value-dominant mottle (the chromatic-confetti lesson): one luma factor
    luma = np.clip(rng.normal(1.0, var_reg * 2.0, (N, N)), 0.6, 1.4)
    cell_col = np.empty((N, N, 3))
    cell_col[:] = np.array(col_reg)[None, None, :]
    cell_col *= luma[..., None]
    cell_col[rock] = np.array(col_rock)[None, :] * np.clip(
        rng.normal(1.0, var_rock * 2.0, (int(rock.sum()), 1)), 0.7, 1.3)

    # corner heights (smooth relief) with per-cell verts (crisp matter edges)
    hp = np.pad(h, 1, mode="edge")
    corner = 0.25 * (hp[:-1, :-1] + hp[1:, :-1] + hp[:-1, 1:] + hp[1:, 1:])

    import trimesh

    def cell_quads(mask, z_of_corner, colors):
        idx = np.argwhere(mask)
        nq = idx.shape[0]
        v = np.empty((nq * 4, 3))
        c = np.empty((nq * 4, 4), dtype=np.uint8)
        f = np.empty((nq * 2, 3), dtype=np.int64)
        half = N * CELL_W_CM / 2.0
        for k, (cy, cx) in enumerate(idx):
            zs = z_of_corner(cy, cx)
            for j, (dy, dx) in enumerate(((0, 0), (0, 1), (1, 1), (1, 0))):
                v[4 * k + j] = ((cx + dx) * CELL_W_CM - half,
                                (cy + dy) * CELL_W_CM - half,
                                zs[j] * CELL_H_CM)
            rgba = np.clip(np.array(colors[cy, cx]) * 255.0, 0, 255)
            c[4 * k:4 * k + 4, :3] = rgba.astype(np.uint8)
            c[4 * k:4 * k + 4, 3] = 255
            f[2 * k] = (4 * k, 4 * k + 1, 4 * k + 2)
            f[2 * k + 1] = (4 * k, 4 * k + 2, 4 * k + 3)
        m = trimesh.Trimesh(vertices=v / 100.0, faces=f,                # METERS
                            vertex_colors=c, process=False)
        return m

    terr = cell_quads(np.ones((N, N), bool),
                      lambda cy, cx: (corner[cy, cx], corner[cy, cx + 1],
                                      corner[cy + 1, cx + 1], corner[cy + 1, cx]),
                      cell_col)
    geoms = {"terrain": terr}
    if sea is not None and water.any():
        wat_col = np.empty((N, N, 3))
        wat_col[:] = np.array(col_wat)[None, None, :]
        geoms["water"] = cell_quads(water,
                                    lambda cy, cx: (sea, sea, sea, sea),
                                    wat_col)

    out.parent.mkdir(parents=True, exist_ok=True)
    trimesh.Scene(geoms).export(str(out))
    from core.splat_to_ue5 import _inject_material
    _inject_material(out)

    stats = {
        "seed": seed, "planet": f"{stand['class']}@{stand['a_au']:.2f}au"
        f"/{stand['t_surf']:.0f}K", "relief_cm": float(
            (h.max() - h.min()) * CELL_H_CM),
        "rock_pct": float(rock.mean() * 100.0),
        "water_pct": float(water.mean() * 100.0),
        "regolith_pct": float((~rock & ~water).mean() * 100.0),
        "sea_cells": None if sea is None else float(sea),
        "glb": str(out),
    }
    return stats


def to_engine(glb: Path, stem: str) -> dict:
    from core.telemetry_probe import MCPStdioClient

    def ok(resp):
        try:
            sc = resp["result"]["structuredContent"]
            return bool(sc.get("success", True)), sc.get("message", "")[:70]
        except (KeyError, TypeError):
            return False, str(resp)[:70]

    log = {}
    c = MCPStdioClient()
    try:
        log["import"] = ok(c.call("manage_asset", {
            "action": "import", "sourcePath": str(glb),
            "destinationPath": DEST}))
        for name, actor in (("terrain", "Materialized_Ground"),
                            ("water", "Materialized_Water")):
            path = f"{DEST}{stem}/StaticMeshes/{name}"
            c.call("control_actor", {"action": "destroy_actor",
                                     "actorName": actor})
            okd, msg = ok(c.call("control_actor", {
                "action": "spawn_actor",
                "classPath": "/Script/Engine.StaticMeshActor",
                "meshPath": path, "actorName": actor,
                "location": {"x": 0.0, "y": 0.0, "z": BASE_Z_UU}}))
            log[f"spawn:{name}"] = (okd, msg)
            if okd:
                log[f"mat:{name}"] = ok(c.call("control_actor", {
                    "action": "set_material", "actorName": actor,
                    "materialPath": "/Game/Materials/M_SplatVC_Lit",
                    "path": "/Game/Materials/M_SplatVC_Lit"}))
        import time
        time.sleep(2.2)
        log["screenshot"] = ok(c.call("control_editor", {
            "action": "screenshot", "filename": "materialized_patch.png",
            "mode": "editor_viewport"}))
    finally:
        c.close()
    return log


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--system", type=int, default=0)
    ap.add_argument("--patch", type=int, nargs=2, default=(0, 0))
    ap.add_argument("--no-engine", action="store_true")
    a = ap.parse_args()
    stem = f"patch_s{a.system}_{a.patch[0]}_{a.patch[1]}"
    glb = OUT_DIR / f"{stem}.glb"
    stats = build_patch_glb(a.system, tuple(a.patch), glb)
    print("MATERIALIZED:", json.dumps(stats, indent=1))
    if not a.no_engine:
        log = to_engine(glb, stem)
        bad = [k for k, (okd, _) in log.items() if not okd]
        for k, (okd, msg) in log.items():
            print(f"  {'OK ' if okd else 'FAIL'} {k:<14} {msg}")
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
