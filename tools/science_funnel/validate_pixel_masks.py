"""validate_pixel_masks.py -- the pre-registered falsifier battery for receipt
pixel_masks_20260920 (lane agent/pixel-masks-20260920).

Deterministic, offline, NO engine and NO model calls. Runs, against the
COMMITTED triangle_monkey_20260920 artifacts:

  1. reproduction at the committed stills' own resolution (the falsifier as
     written: masks regenerated from the committed geometry + the lane's
     recorded pose-A camera, pixel_truth.coverage unchanged, vs the banked
     tables);
  2. viewport exactness: the lane's TRUE render viewport, recovered by exact
     hull-area identity (2560x1369 -- the engine's 2560x1440 client rectangle
     minus the 71 px title bar; MEASURED, not assumed: all 25 per-bone + 3
     macro hull areas equal the banked pixel counts exactly), i.e. the
     regenerated hull masks vs the banked denominators, plus the camera radii;
  3. coverage at that viewport with the committed pixels carried up by
     nearest / bilinear / lanczos (the committed stills are 960x513 downscales
     of the viewport -- the numerator keeps that information loss; measured);
  4. the OBB-corner route study (receipt FALSIFIER_4): manifest-bbox hulls vs
     the banked vertex-hull denominators;
  5. determinism (receipt FALSIFIER_2): two FRESH-PROCESS `pixel_truth masks`
     CLI generations -> sha256 of every mask file + byte-equality of the
     coverage tables.

Writes reproduction.json / route_justification.json / determinism.json next to
the receipt and prints one summary JSON.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.science_funnel import pixel_truth as pt
from tools.science_funnel import pixel_masks as PM

FUNNEL = Path(__file__).resolve().parent
LANE = FUNNEL / "validation" / "triangle_monkey_20260920"
OUT = FUNNEL / "validation" / "pixel_masks_20260920"

# The lane's true render viewport, MEASURED (see module docstring + receipt):
# at this (W, H) every regenerated hull's pixel area equals the banked count.
VIEWPORT = (2560, 1369)
RESAMPLE_KEYS = {"nearest": Image.NEAREST, "bilinear": Image.BILINEAR,
                 "lanczos": Image.LANCZOS}
STILLS = {"mesh": ("after", "a_regions_mesh.png", "after/measure_regions_mesh.json"),
          "splat": ("before", "a_regions_splat.png", "before/measure_regions_splat.json")}


def _banked(pres: str) -> dict:
    sub, _, jf = STILLS[pres]
    return json.loads((LANE / jf).read_text(encoding="utf-8"))["a_regions"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _deltas(covs: dict, ref: dict) -> dict:
    """Named coverage deltas + summary bands, keyed by bone name."""
    rows = []
    for b in ref["per_bone"]:
        mine = covs[b["bone"]]
        rows.append({"bone": b["bone"], "mine": mine, "banked": b["coverage"],
                     "abs_delta": round(abs(mine - b["coverage"]), 4)})
    d = np.array([r["abs_delta"] for r in rows])
    mine_med = round(float(np.median([r["mine"] for r in rows])), 4)
    return {
        "per_bone": rows,
        "n_bones": len(rows),
        "n_exact": int(sum(1 for r in rows if r["mine"] == r["banked"])),
        "max_abs_delta": round(float(d.max()), 4),
        "n_gt_0p02": int((d > 0.02).sum()),
        "median_mine": mine_med,
        "median_banked": ref["median_coverage_all_bones"],
        "median_abs_delta": round(abs(mine_med - ref["median_coverage_all_bones"]), 4),
        "bones_at_zero_mine": int(sum(1 for r in rows if r["mine"] == 0.0)),
        "bones_at_zero_banked_table": int(sum(1 for b in ref["per_bone"]
                                              if b["coverage"] == 0.0)),
        "bones_zero_numerator_banked_table": int(sum(1 for b in ref["per_bone"]
                                                     if b["object_pixels_in_hull"] == 0)),
    }


def _hulls_and_masks(skel: dict, cam: dict, W: int, H: int):
    pos = skel["pos"].copy()
    pos[:, 1] += float(cam["lift"])
    hulls = {b["bone"]: pt.hull_mask(PM._project(pos[b["rows"]], cam, W, H),
                                     (H, W), dilate_px=1)
             for b in skel["bones"]}
    macro = {k: pt.hull_mask(PM._project(pos[rows], cam, W, H), (H, W), dilate_px=1)
             for k, rows in skel["macro"].items()}
    return hulls, macro


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}

    # ── 2. viewport exactness + 3. carried coverage + 4. OBB study ──────────
    W, H = VIEWPORT
    reproduction, route_study = {}, {}
    for pres in ("mesh", "splat"):
        sub, still, _ = STILLS[pres]
        ref = _banked(pres)
        skel = PM.skeleton(pres)
        cam = skel["camera_a"]
        hulls, macro_hulls = _hulls_and_masks(skel, cam, W, H)

        # (2) exact denominators: regenerated hull masks vs banked pixel counts
        bone_eq = {b["bone"]: int(hulls[b["bone"]].sum()) == b["hull_pixels"]
                   for b in ref["per_bone"]}
        macro_mine = {k: int(m.sum()) for k, m in macro_hulls.items()}
        macro_ref = {k: v["hull_pixels"] for k, v in ref["macro"].items()}
        banked_radius = json.loads(
            (LANE / sub / ("measure_a_mesh.json" if pres == "mesh"
                           else "measure_a_splat.json")).read_text()
        )["a_fixed_pose"]["camera"]["radius_m"]
        reproduction[pres] = {
            "viewport": [W, H],
            "camera_radius_mine": round(float(cam["radius"]), 6),
            "camera_radius_banked": banked_radius,
            "camera_radius_abs_delta": round(abs(float(cam["radius"]) - banked_radius), 6),
            "hull_masks_exact": int(all(bone_eq.values())),
            "n_hull_masks_exact": int(sum(bone_eq.values())),
            "n_hull_masks_total": len(bone_eq),
            "macro_hulls_exact": macro_mine == macro_ref,
            "macro_pixels_mine": macro_mine,
            "macro_pixels_banked": macro_ref,
        }

        # (3) the committed still carried up to the viewport; unchanged warm_mask
        img_native = pt.load(LANE / sub / still)
        carried = {}
        for key, flt in RESAMPLE_KEYS.items():
            big = img_native if img_native.shape[:2] == (H, W) else np.asarray(
                Image.fromarray(img_native).resize((W, H), flt))
            obj = pt.warm_mask(big)
            covs = {b["bone"]: pt.coverage(obj, hulls[b["bone"]])["coverage"]
                    for b in skel["bones"]}
            comp = _deltas(covs, ref)
            comp["macro"] = {k: pt.coverage(obj, macro_hulls[k])["coverage"]
                             for k in sorted(macro_hulls)}
            comp["macro_abs_delta_max"] = round(max(
                abs(comp["macro"][k] - ref["macro"][k]["coverage"]) for k in comp["macro"]), 4)
            carried[key] = comp
        reproduction[pres]["coverage_at_viewport"] = carried

        # (1) the falsifier AS WRITTEN: masks + coverage at the still's OWN size
        res = PM.run_masks(LANE / sub, still, presentation=pres, outdir=OUT / "masks")
        table = res["frames"][still]
        covs_native = {b["bone"]: b["coverage"] for b in table["per_bone"]}
        comp_native = _deltas(covs_native, ref)
        comp_native["macro"] = {k: v["coverage"] for k, v in table["macro"].items()}
        comp_native["macro_abs_delta_max"] = round(max(
            abs(comp_native["macro"][k] - ref["macro"][k]["coverage"])
            for k in comp_native["macro"]), 4)
        comp_native["viewport"] = [img_native.shape[1], img_native.shape[0]]
        comp_native["camera"] = table["camera"]
        reproduction[pres]["coverage_at_still_resolution"] = comp_native

        # (4) OBB-corner route at the same viewport (mesh carries the study)
        if pres == "mesh":
            obb = PM.masks_for_frame((H, W), cam, skel, dilate_px=1, route="obb")
            obj = pt.warm_mask(np.asarray(
                Image.fromarray(img_native).resize((W, H), Image.NEAREST)))
            obb_cov, obb_ratio = {}, {}
            for b, rb in zip(obb["bones"], ref["per_bone"]):
                key = rb["bone"]
                if b["mask"] is None:
                    obb_cov[key], obb_ratio[key] = None, None
                    continue
                obb_cov[key] = pt.coverage(obj, b["mask"])["coverage"]
                obb_ratio[key] = round(int(b["mask"].sum()) / rb["hull_pixels"], 4)
            vert = carried["nearest"]["per_bone"]
            obb_d = [abs(obb_cov[r["bone"]] - r["coverage"])
                     for r in ref["per_bone"] if obb_cov[r["bone"]] is not None]
            vert_d = [r["abs_delta"] for r in vert]
            ratios = [v for v in obb_ratio.values() if v is not None]
            route_study = {
                "viewport": [W, H],
                "obb_hull_over_banked_hull": {"min": round(min(ratios), 4),
                                              "max": round(max(ratios), 4),
                                              "mean": round(float(np.mean(ratios)), 4)},
                "obb_per_bone_abs_delta_max": round(float(max(obb_d)), 4),
                "vertex_per_bone_abs_delta_max": round(float(max(vert_d)), 4),
                "obb_worse_than_vertex": bool(max(obb_d) > max(vert_d)),
                "per_bone": [{"bone": r["bone"], "obb": obb_cov[r["bone"]],
                              "obb_hull_ratio": obb_ratio[r["bone"]],
                              "vertex": next(v["mine"] for v in vert
                                             if v["bone"] == r["bone"]),
                              "banked": r["coverage"]} for r in ref["per_bone"]],
            }
        summary[f"{pres}_viewport_hulls_exact"] = reproduction[pres]["hull_masks_exact"]
        summary[f"{pres}_stillres_median_delta"] = comp_native["median_abs_delta"]
        summary[f"{pres}_nearest_median_delta"] = carried["nearest"]["median_abs_delta"]

    (OUT / "reproduction.json").write_text(
        json.dumps({"schema": "chimera.pixel_masks.reproduction.v1",
                    "viewport_measured": list(VIEWPORT),
                    "reproduction": reproduction}, indent=1) + "\n", encoding="utf-8")
    (OUT / "route_justification.json").write_text(
        json.dumps({"schema": "chimera.pixel_masks.route_study.v1",
                    "obb_vs_vertices": route_study}, indent=1) + "\n", encoding="utf-8")

    # ── 5. determinism: two FRESH-PROCESS CLI generations ───────────────────
    sub, still, _ = STILLS["mesh"]
    runs = []
    for i in (1, 2):
        outdir = OUT / f"masks_det_run{i}"
        proc = subprocess.run(
            [sys.executable, "-B", str(FUNNEL / "pixel_truth.py"), "masks",
             str(LANE / sub), "--glob", still, "--presentation", "mesh",
             "--outdir", str(outdir)],
            capture_output=True, text=True, check=True)
        runs.append((outdir, proc.stdout))
    sha_runs = [{p.name: _sha(p) for p in sorted(outdir.glob("*.png"))}
                for outdir, _ in runs]
    # compare the coverage TABLES (the `outdir` metadata path differs by design)
    tables = [json.dumps(json.loads(stdout)["frames"], sort_keys=True)
              for _, stdout in runs]
    determinism = {
        "fresh_processes": 2,
        "mask_files_compared": len(sha_runs[0]),
        "all_mask_bytes_identical": sha_runs[0] == sha_runs[1],
        "coverage_tables_byte_identical": tables[0] == tables[1],
        "sha256_first_8": {k: v[:8] for k, v in list(sha_runs[0].items())[:8]},
    }
    (OUT / "determinism.json").write_text(
        json.dumps({"schema": "chimera.pixel_masks.determinism.v1",
                    "determinism": determinism}, indent=1) + "\n", encoding="utf-8")
    summary["determinism_masks_identical"] = determinism["all_mask_bytes_identical"]
    summary["determinism_tables_identical"] = determinism["coverage_tables_byte_identical"]

    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
