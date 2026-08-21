"""spray_parts.py -- tile a region genome onto a fitted CAD primitive (one part).

The operator's method (2026-08-21): each part = an analytic CAD shape + a splat
texture. The shape is complete by construction (no donor holes); the texture is
the donor's material genome TILED over the primitive's UV chart like a game-dev
texture tile: every surface sample fetches a random genome entry from its UV
neighborhood (variation, never averaging). Relief (elevation off the surface)
is CLAMPED relative to the part size -- that clamp is what kills floaters and
keeps a bad scan from contaminating the part.

UV source: donor genome splats are projected onto their OWN fitted primitive
(same UV convention for every primitive, so charts are compatible); the target
part samples that chart. Uncovered UV = nearest entry -> holes close by tiling.

Usage (one part at a time, per tools/specs/bear34_parts_plan.json):
  .venv-gs/Scripts/python.exe tools/spray_parts.py --part torso \
      --plan tools/specs/bear34_parts_plan.json --shells models/co3d/bear34_shells.npz \
      --outdir models/co3d/parts
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
import cpp_bridge as cb  # noqa: E402
from extract_genomes import core_frames, frame_quat, quat_mul  # noqa: E402
from fit_parts import sample_surface  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402


def knud_thomsen(r: np.ndarray) -> float:
    """Ellipsoid surface area estimate."""
    a, b, c = r
    p = 1.6075
    return float(4 * np.pi * (((a * b) ** p + (a * c) ** p + (b * c) ** p) / 3) ** (1 / p))


def prim_area(prim: dict) -> float:
    if prim["type"] == "ellipsoid":
        return knud_thomsen(np.array(prim["radii"]))
    p0, p1, rad = np.array(prim["p0"]), np.array(prim["p1"]), prim["radius"]
    L = np.linalg.norm(p1 - p0)
    return float(2 * np.pi * rad * L + 4 * np.pi * rad * rad)


def uv_of_points(pos: np.ndarray, prim: dict) -> np.ndarray:
    """Central projection of donor splats onto their primitive's UV chart."""
    if prim["type"] == "ellipsoid":
        c = np.array(prim["center"]); V = np.array(prim["axes"]); r = np.array(prim["radii"])
        local = ((pos - c) @ V) / np.maximum(r[None, :], 1e-12)
        g = local / np.maximum(np.linalg.norm(local, axis=1, keepdims=True), 1e-12)
        u = (np.arctan2(g[:, 1], g[:, 0]) / (2 * np.pi)) % 1.0
        v = np.clip((g[:, 2] + 1.0) / 2.0, 0, 1)
        return np.stack([u, v], 1)
    p0 = np.array(prim["p0"]); p1 = np.array(prim["p1"])
    a = p1 - p0; L = np.linalg.norm(a); a /= L
    ref = np.array([0.0, 1.0, 0.0]) if abs(a[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    t1 = np.cross(a, ref); t1 /= np.linalg.norm(t1)
    t2 = np.cross(a, t1)
    rel = pos - p0
    t = np.clip(rel @ a, 0, L) / L
    w = rel - (rel @ a)[:, None] * a[None, :]
    th = np.arctan2(w @ t2, w @ t1)
    return np.stack([t, (th / (2 * np.pi)) % 1.0], 1)


def uv_metric(uv: np.ndarray, periodic_col: int) -> np.ndarray:
    """Embed UV so the periodic column wraps (u for ellipsoid, angle for capsule)."""
    ang = uv[:, periodic_col] * 2 * np.pi
    return np.stack([np.cos(ang), np.sin(ang), uv[:, 1 - periodic_col] * 2.0], 1)


def surface_frames(normals: np.ndarray) -> np.ndarray:
    """(t1, t2, n) column frames from outward normals -- matches extract_genomes."""
    n = normals
    ref = np.where(np.abs(n[:, 1:2]) < 0.9,
                   np.broadcast_to(np.array([0.0, 1.0, 0.0]), (len(n), 3)),
                   np.broadcast_to(np.array([1.0, 0.0, 0.0]), (len(n), 3)))
    t1 = np.cross(n, ref)
    t1 /= np.linalg.norm(t1, axis=1, keepdims=True)
    t2 = np.cross(n, t1)
    return np.stack([t1, t2, n], axis=2)


GENOME_FIELDS = {"core_idx", "h", "u", "v", "q_local", "scale", "rgb", "alpha"}


def require_14var_genome(genome: dict, where: str) -> None:
    """MANDATORY GATE (operator, 2026-08-21): a sample must be full 14-variable
    3DGS -- position, color, alpha, ANISOTROPIC scale (3), rotation quaternion (4).
    A 7-variable isotropic source cannot carry fur-level detail and is refused."""
    missing = GENOME_FIELDS - set(genome)
    if missing:
        raise SystemExit(f"REFUSED: {where} is not a 14-variable sample "
                         f"(missing {sorted(missing)}). Find a different sample.")
    sc = genome["scale"]
    if sc.shape[1] != 3 or np.allclose(sc[:, 0], sc[:, 1], rtol=1e-3, atol=1e-9) and \
            np.allclose(sc[:, 1], sc[:, 2], rtol=1e-3, atol=1e-9):
        raise SystemExit(f"REFUSED: {where} has isotropic scales -- 7-variable "
                         f"format, not 14. Find a different sample.")
    qn = np.linalg.norm(genome["q_local"], axis=1)
    if not np.all(np.isfinite(qn)) or (qn < 1e-6).any():
        raise SystemExit(f"REFUSED: {where} has degenerate rotation quaternions.")


def gmm_score(model: dict, X: np.ndarray) -> np.ndarray:
    from scipy.stats import multivariate_normal
    lw = np.log(model["weights"])
    lp = np.stack([lw[j] + multivariate_normal.logpdf(X, model["means"][j],
                                                      model["covariances"][j])
                   for j in range(len(lw))], 1)
    mx = lp.max(1)
    return mx + np.log(np.exp(lp - mx[:, None]).sum(1))


def gmm_sample(model: dict, n: int, rng) -> np.ndarray:
    """Draw n samples, rejecting anything below the concept's likelihood floor."""
    floor = float(model["floor"][0])
    w, mu = model["weights"], model["means"]
    out = np.empty((0, mu.shape[1]))
    while len(out) < n:
        m = int((n - len(out)) * 1.4) + 32
        comp = rng.choice(len(w), size=m, p=w)
        xs = np.empty((m, mu.shape[1]))
        for j in range(len(w)):
            sel = comp == j
            if sel.any():
                xs[sel] = rng.multivariate_normal(mu[j], model["covariances"][j],
                                                  size=int(sel.sum()))
        out = np.concatenate([out, xs[gmm_score(model, xs) >= floor]])
    return out[:n]


def spray_material(part_name: str, prim: dict, src_prim: dict, model: dict,
                   n_donor: int, rng, clamp_max: float) -> np.ndarray:
    """Grow the coat from a TRAINED MATERIAL (no donor splats are copied):
    color/size/relief/alpha are synthesized by the concept's density model;
    fiber tilt is bootstrapped from the material's real q_local samples."""
    n_out = max(200, int(round(n_donor * prim_area(prim) / max(prim_area(src_prim), 1e-9))))
    surf, normals, _ = sample_surface(part_name, prim, n_out, rng)
    X = gmm_sample(model, n_out, rng)
    h = np.clip(X[:, 6] / 1000.0,
                float(model["h_lo"][0]) if "h_lo" in model else -0.002,
                min(clamp_max, float(model["h_tip"][0])) if "h_tip" in model else clamp_max)
    pos = surf + h[:, None] * normals
    qb = model["q_local"][rng.integers(0, len(model["q_local"]), size=n_out)]
    q_world = quat_mul(frame_quat(surface_frames(normals)), qb)
    q_world /= np.linalg.norm(q_world, axis=1, keepdims=True)

    b = np.zeros((n_out, 14), dtype=np.float32)
    b[:, 0:3] = pos
    if "rgb_lo" in model:  # the material's real color box -- hard geometric bound
        b[:, 3:6] = np.clip(X[:, 0:3], model["rgb_lo"][None, :], model["rgb_hi"][None, :])
    else:
        b[:, 3:6] = np.clip(X[:, 0:3], 0, 1)
    b[:, 6] = np.clip(X[:, 7], 0, 1)
    cap = float(model["scale_cap"][0]) if "scale_cap" in model else clamp_max * 1.5
    b[:, 7:10] = np.clip(np.exp(np.clip(X[:, 3:6], np.log(1e-6), np.log(1e-1))),
                         1e-5, cap)
    b[:, 10:14] = q_world
    return b


def spray(part: dict, prim: dict, src_prim: dict, genome: dict,
          shells, rng, clamp_max: float, lum_band=None) -> np.ndarray:
    """Grow the coat on `prim` from genome entries charted on `src_prim`."""
    require_14var_genome(genome, "genome (spray source)")
    inner = shells["inner"].astype(np.float64)
    nrm, frames = core_frames(shells)
    ci = genome["core_idx"]
    n_full = len(ci)  # density is measured on the UNFILTERED donor region
    fr = frames[ci]
    donor_pos = (inner[ci] + genome["h"][:, None] * fr[:, :, 2]
                 + genome["u"][:, None] * fr[:, :, 0]
                 + genome["v"][:, None] * fr[:, :, 1])
    if lum_band is not None:
        lum = genome["rgb"] @ np.array([0.299, 0.587, 0.114])
        keep = (lum >= lum_band[0]) & (lum <= lum_band[1])
        # hue gate: within the lit band, drop color outliers (printed tags,
        # pattern flowers) -- fur hue varies little, decals are far from it
        med = np.median(genome["rgb"][keep], axis=0)
        dcol = np.linalg.norm(genome["rgb"] - med[None, :], axis=1)
        keep &= dcol <= np.percentile(dcol[keep], 90)
        donor_pos = donor_pos[keep]
        genome = {k: (v[keep] if isinstance(v, np.ndarray) and len(v) == len(keep) else v)
                  for k, v in genome.items()}
        print(f"  lum band {lum_band} + hue gate: kept {keep.sum()}/{len(keep)} genome entries")
    src_uv = uv_of_points(donor_pos, src_prim)
    per_col = 0 if src_prim["type"] == "ellipsoid" else 1
    tree = cKDTree(uv_metric(src_uv, per_col))

    n_out = max(200, int(round(n_full * prim_area(prim) / max(prim_area(src_prim), 1e-9))))
    surf, normals, _ = sample_surface(part["name"], prim, n_out, rng)
    tgt_uv = uv_of_points(surf, prim)  # chart-compatible; used only for lookup
    per_col_t = 0 if prim["type"] == "ellipsoid" else 1
    _, idx = tree.query(uv_metric(tgt_uv, per_col_t), k=8)
    pick = np.array([rng.choice(row) for row in idx])

    h = np.clip(genome["h"][pick], -0.002, clamp_max)
    pos = surf + h[:, None] * normals
    q_frame = frame_quat(surface_frames(normals))
    q_world = quat_mul(q_frame, genome["q_local"][pick])
    q_world /= np.linalg.norm(q_world, axis=1, keepdims=True)

    b = np.zeros((n_out, 14), dtype=np.float32)
    b[:, 0:3] = pos
    b[:, 3:6] = genome["rgb"][pick]
    b[:, 6] = genome["alpha"][pick]
    b[:, 7:10] = genome["scale"][pick]
    b[:, 10:14] = q_world
    return b


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--part", required=True, help="part name from the plan")
    ap.add_argument("--plan", default=str(ROOT / "tools/specs/bear34_parts_plan.json"))
    ap.add_argument("--shells", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--lumband", nargs=2, type=float, metavar=("LO", "HI"),
                    help="keep only genome entries with luminance in [LO, HI] "
                         "(fur tile selection -- drops face markings/shadows)")
    ap.add_argument("--material", help="trained material name (library) -- synthesize "
                                       "from the concept instead of copying genome entries")
    ap.add_argument("--materialdir", default=str(ROOT / "models/co3d/materials"))
    a = ap.parse_args()

    plan = json.loads(Path(a.plan).read_text())
    entry = next(p for p in plan["parts"] if p["name"] == a.part)
    parts = json.loads((ROOT / plan["parts_json"]).read_text())["parts"]
    shells = np.load(a.shells)

    prim = parts[entry["fit_region"]][0]
    if entry["shape"] == "capsule":
        bone = entry["bone"]
        prim = next(p for p in parts[entry["fit_region"]] if p.get("bone") == bone)
    src_name = entry["texture"]["genome"]
    src_prim = parts[src_name][0]

    genome = dict(np.load(ROOT / plan["genomes"] / f"{src_name}.npz"))
    min_axis = (min(prim["radii"]) if prim["type"] == "ellipsoid" else prim["radius"])
    clamp_max = min(0.010, 0.15 * min_axis)

    rng = np.random.default_rng(0)
    if a.material:
        mdir = Path(a.materialdir)
        model = dict(np.load(mdir / f"{a.material}.npz"))
        meta = json.loads((mdir / f"{a.material}.json").read_text())
        for k in ("weights", "means", "covariances", "floor", "q_local"):
            if k not in model:
                raise SystemExit(f"REFUSED: material {a.material} missing {k} "
                                 f"-- not a 14-variable concept model")
        src_prim = parts[meta["source_region"]][0]
        coat = spray_material(a.part, prim, src_prim, model, meta["donor_count"],
                              rng, clamp_max)
        tex_desc = f"material={a.material} (synthesized, floor={float(model['floor'][0]):.1f})"
    else:
        coat = spray({"name": a.part}, prim, src_prim, genome, shells, rng, clamp_max,
                     lum_band=a.lumband)
        tex_desc = f"texture={src_name}"

    outdir = Path(a.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{a.part}.splat"
    cb.save_splat(str(out), coat)
    print(f"{a.part}: {len(coat)} splats, relief clamp {clamp_max*1000:.1f}mm, "
          f"{tex_desc}, shape={prim['type']} -> {out}")
    (outdir / f"{a.part}.json").write_text(json.dumps({
        "part": a.part, "primitive": prim, "texture": a.material or src_name,
        "synthesized": bool(a.material),
        "connects_to": entry.get("connects_to"), "joint": entry.get("joint"),
        "relief_clamp_m": clamp_max, "splats": int(len(coat)),
        "lum_band": a.lumband,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
