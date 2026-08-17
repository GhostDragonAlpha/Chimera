"""matter_items — EXAMPLE ITEMS forged from the Matter Library, rendered as splats.

Commissioned 2026-07-18, the human: "make some example items with the method so we can
work things out and see how much quality we can get."

THE METHOD (THE_COMPOSITIONAL_WORLD_MODEL.md PART II sections 11/12/16):
    library entry  ->  voxel shape  ->  splat emission (per-particle optics SAMPLED
    from the entry's DISTRIBUTIONS)  ->  relight under a moving directional light.

Everything optical comes from Chimera/docs/rep_batteries/matter_library.json — nothing is authored
per-item. An item is a SHAPE plus library entries; "what the surface looks like" is the
per-particle average the human named: albedo mottle is sqrt(albedo_mottle_var) sampled
per splat, so no two rocks are the same rock and nobody painted either of them.

WHAT THIS REUSES vs EXTENDS (honest scope):
- Emission geometry (surface voxels -> oriented flattened Gaussians) is core.splat_emit's
  proven rung-A path, reused by INJECTING library entries into its OPTICAL registry —
  splat_emit.py itself is untouched (tb-0174 owns the real rewiring).
- The rasterizer here EXTENDS rung A's (same orthographic projection, same front-to-back
  3DGS compositing recurrence) with the two terms the library carries and rung A's
  shading ignored: a Blinn-Phong specular lobe driven by roughness_mean (metal cannot
  read as metal without it — 'metallic' tints the lobe by albedo) and per-particle
  sampled albedo. This is a SANDBOX QUALITY PROBE — the production path is rung D-prime
  (UE Substrate slabs, tb-0170), where the engine's own lighting replaces all of this.
- FACTS only in results.json; the PNGs are the evidence. Quality is judged by LOOKING
  (H-2 doctrine: the pixels are the terminal, not the numbers).

Run:  python -m core.matter_items            (all items -> Chimera/Saved/MatterItems/)
      python -m core.matter_items boulder    (just one)
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

from core import splat_emit as se
from core.splat_emit import (_camera_frame, _dir_from_azel, emit_splats,
                             hstack_strip, surface_voxels)

ROOT = Path(__file__).resolve().parents[1]
LIB_PATH = ROOT / "docs" / "matter" / "matter_library.json"
OUT_DIR = ROOT / "Saved" / "MatterItems"

GRID = 96                       # voxel resolution per item (same order as the limb's)
RES = 340                       # render resolution per frame
RELIGHT = [(20, 35), (110, 45), (200, 30), (300, 40)]   # (light_azim, light_elev) sweep
CAM = (-55, 22)                 # fixed camera; light moves (rung A's convention)
SEED = 7


# --- the library is the source of every optical number ------------------------------

def load_library() -> dict:
    return json.loads(LIB_PATH.read_text(encoding="utf-8"))


def register_material(lib: dict, name: str) -> dict:
    """Inject a library entry into splat_emit.OPTICAL so the proven emitter can emit
    it, and return the EXTENDED optical row (roughness/metallic/mottle) the extended
    shader consumes. Appearance means -> the emitter; distributions -> the sampler."""
    ap = lib["materials"][name]["appearance"]
    alpha = float(ap.get("alpha", 1.0))
    subsurface = float(ap.get("subsurface_strength",
                              0.5 * ap.get("translucency", 0.0) + (0.25 if ap.get("subsurface_mfp_mm", 0) > 2 else 0.0)))
    se.OPTICAL[name] = {
        "albedo": tuple(ap["albedo_mean_rgb"]),
        "roughness": float(ap["roughness_mean"]),
        "alpha": alpha,
        "subsurface": subsurface,
    }
    return {
        "roughness": float(ap["roughness_mean"]),
        "roughness_var": float(ap.get("roughness_var", 0.0)),
        "metallic": float(ap.get("metallic", 0.0)),
        "mottle_sd": math.sqrt(float(ap.get("albedo_mottle_var", 0.0))),
    }


def sample_variance(splats: dict, ext: dict, rng: np.random.Generator) -> dict:
    """Per-particle sampling of the entry's DISTRIBUTIONS — the 'average, not a
    surface' thesis made visible. A scalar luma factor ~N(1, mottle_sd) preserves hue
    (mineral mottling is mostly value, not color); a small independent RGB jitter
    (mottle_sd/3) breaks the residual uniformity; roughness jitters within its var."""
    n = len(splats["pos"])
    # Value-dominant mottle: minerals vary in BRIGHTNESS far more than hue. The first
    # cut used independent RGB jitter and rendered as chromatic confetti (seen, fixed
    # 2026-07-18): now a shared luma factor + a hue jitter an order of magnitude weaker.
    luma = rng.normal(1.0, ext["mottle_sd"], size=(n, 1))
    rgbj = rng.normal(0.0, ext["mottle_sd"] / 12.0, size=(n, 3))
    splats["albedo"] = np.clip(splats["albedo"] * np.clip(luma, 0.35, 1.8) + rgbj, 0.0, 1.0)
    splats["roughness"] = np.clip(
        rng.normal(ext["roughness"], math.sqrt(max(ext["roughness_var"], 0.0)), size=n), 0.02, 1.0)
    splats["metallic"] = np.full(n, ext["metallic"])
    return splats


def attach_flat(splats: dict, ext: dict) -> dict:
    """Variance OFF: every particle gets the mean (the coalesced-aggregate look)."""
    n = len(splats["pos"])
    splats["roughness"] = np.full(n, ext["roughness"])
    splats["metallic"] = np.full(n, ext["metallic"])
    return splats


# --- extended rasterizer: rung A's compositing + the library's specular -------------

def rasterize(splats: dict, center: np.ndarray, radius: float,
              azim: float, elev: float, light_azim: float, light_elev: float,
              w: int = RES, h: int = RES) -> np.ndarray:
    """Same orthographic projection + front-to-back 3DGS recurrence as
    splat_emit.rasterize_splats; adds a Blinn-Phong lobe: exponent from roughness
    (p = 4 + (1-r)^2 * 220), dielectric ks=0.06 white, metal ks=0.55 tinted by albedo
    (a metal's highlight IS its color; a dielectric's is the light's)."""
    right, up, view_dir = _camera_frame(azim, elev)
    rel = splats["pos"] - center
    depth = rel @ view_dir
    scale_px = 0.42 * min(w, h) / radius
    sx = w / 2 + (rel @ right) * scale_px
    sy = h / 2 - (rel @ up) * scale_px

    J = np.stack([right, up], axis=0)
    cov2 = np.einsum('ij,njk,lk->nil', J, splats["cov"], J) * (scale_px ** 2)

    light_toward = _dir_from_azel(light_azim, light_elev)
    ndotl = np.clip(splats["normal"] @ light_toward, 0, None)
    back = np.clip(splats["normal"] @ (-light_toward), 0, None)
    shade = se.AMBIENT + (1 - se.AMBIENT) * ndotl + splats["subsurface"] * 0.6 * back
    base = np.clip(splats["albedo"] * shade[:, None], 0.0, 1.0)

    half = light_toward + (-view_dir)
    half = half / np.linalg.norm(half)
    ndoth = np.clip(splats["normal"] @ half, 0.0, None)
    r = splats["roughness"]
    p = 4.0 + (1.0 - r) ** 2 * 220.0
    spec_i = (ndoth ** p) * (ndotl > 0)
    m = splats["metallic"][:, None]
    ks = 0.06 * (1 - m) + 0.55 * m
    spec_color = np.ones(3)[None, :] * (1 - m) + splats["albedo"] * m
    color = np.clip(base + ks * spec_i[:, None] * spec_color, 0.0, 1.0)

    order = np.argsort(depth)
    img = np.zeros((h, w, 3), dtype=np.float64)
    T = np.ones((h, w), dtype=np.float64)
    for i in order:
        C = cov2[i]
        det = C[0, 0] * C[1, 1] - C[0, 1] * C[1, 0]
        if det <= 1e-8:
            continue
        inv00, inv01, inv11 = C[1, 1] / det, -C[0, 1] / det, C[0, 0] / det
        rad = 3.0 * math.sqrt(max(C[0, 0], C[1, 1]) + 1e-6)
        cx, cy = sx[i], sy[i]
        x0, x1 = max(0, int(cx - rad)), min(w, int(cx + rad) + 1)
        y0, y1 = max(0, int(cy - rad)), min(h, int(cy + rad) + 1)
        if x1 <= x0 or y1 <= y0:
            continue
        xs = np.arange(x0, x1) - cx
        ys = np.arange(y0, y1) - cy
        dx, dy = np.meshgrid(xs, ys)
        mdist = inv00 * dx * dx + 2 * inv01 * dx * dy + inv11 * dy * dy
        a = float(splats["alpha"][i]) * np.exp(-0.5 * mdist)
        Tp = T[y0:y1, x0:x1]
        img[y0:y1, x0:x1] += (Tp * a)[..., None] * color[i][None, None, :]
        T[y0:y1, x0:x1] = Tp * (1 - a)
    img += T[..., None] * 0.06
    return np.clip(img, 0.0, 1.0)


# --- shapes: voxel fields, up = axis 2 ----------------------------------------------

def _coords(n: int = GRID):
    ax = np.arange(n, dtype=np.float64)
    return np.meshgrid(ax, ax, ax, indexing="ij")


def _bumpy_radius(x, y, z, cx, cy, cz, rng, n_waves: int = 6, amp: float = 0.22):
    """Radial noise from a few random cosine plane-waves — cheap fbm stand-in; gives a
    lumpy natural silhouette instead of a CAD sphere."""
    dx, dy, dz = x - cx, y - cy, z - cz
    r = np.sqrt(dx * dx + dy * dy + dz * dz) + 1e-9
    bump = np.zeros_like(r)
    for _ in range(n_waves):
        k = rng.normal(size=3)
        k = k / np.linalg.norm(k) * rng.uniform(0.10, 0.30)
        ph = rng.uniform(0, 2 * math.pi)
        bump += np.cos(dx * k[0] + dy * k[1] + dz * k[2] + ph)
    return r, 1.0 + amp * bump / n_waves * 3.0


def boulder_field(rng, radius: float = 26.0, squash: float = 0.82, n: int = GRID):
    x, y, z = _coords(n)
    c = n / 2
    r, mod = _bumpy_radius(x, y, (z - c) / squash + c, c, c, c, rng)
    return r < radius * mod


def pad_field(n: int = GRID):
    """A landing-pad plate: cylinder with a chamfered rim and a shallow center boss —
    a BUILT thing (uniform, machined) to contrast the grown/natural ones."""
    x, y, z = _coords(n)
    c = n / 2
    rad = np.sqrt((x - c) ** 2 + (y - c) ** 2)
    base = (rad < 36) & (z > c - 6) & (z < c + 5)
    chamfer = rad < (36 - np.clip(z - (c + 1), 0, None) * 2.2)
    boss = (rad < 10) & (z >= c + 5) & (z < c + 8)
    return (base & chamfer) | boss


def ice_shard_field(rng, n: int = GRID):
    """A faceted crystal: an elongated ellipsoid cut by random planes — facets are what
    make translucency READ (each plane catches the light at its own angle)."""
    x, y, z = _coords(n)
    c = n / 2
    ell = ((x - c) / 20) ** 2 + ((y - c) / 15) ** 2 + ((z - c) / 34) ** 2 < 1.0
    for _ in range(9):
        nrm = rng.normal(size=3)
        nrm /= np.linalg.norm(nrm)
        d = rng.uniform(9.0, 20.0)
        ell &= ((x - c) * nrm[0] + (y - c) * nrm[1] + (z - c) * nrm[2]) < d
    return ell


def sand_mound_field(lib: dict, rng, n: int = GRID):
    """A poured regolith pile whose slope IS the library's friction angle — physics
    informing shape: sand cannot stand steeper than its own angle of repose."""
    phi = math.radians(lib["materials"]["sand"]["physical"]["friction_angle_deg"]["mean"])
    x, y, z = _coords(n)
    c = n / 2
    rad = np.sqrt((x - c) ** 2 + (y - c) ** 2)
    apex = c + 30
    ripple = 1.0 + 0.06 * np.cos(rad * 0.9 + rng.uniform(0, 6))
    cone_h = (apex - rad * math.tan(math.pi / 2 - phi) * 0.0)  # placeholder simplify
    height = apex - rad / math.tan(phi) * ripple
    return (z < height) & (z > c - 14) & (rad < 40)


def shovel_fields(n: int = GRID):
    """The seed's own tool: a metal blade + a composite ('interior' family) shaft —
    a two-material BUILT item. Returns {material: field}."""
    x, y, z = _coords(n)
    c = n / 2
    # shaft: thin cylinder leaning through the volume
    sx_, sz = x - (c - 12), z - c
    t = (sz * 0.94 + sx_ * 0.34)
    px = sx_ - 0.34 * t
    pz = sz - 0.94 * t
    shaft = (px ** 2 + (y - c) ** 2 + pz ** 2 * 0.0 + (pz) ** 2) < 3.2 ** 2
    shaft &= (t > -34) & (t < 26)
    # blade: a curved scoop = thick shell of a big sphere, clipped to a paddle
    bx, by, bz = x - (c + 16), y - c, z - (c - 22)
    sph = np.sqrt(bx ** 2 + by ** 2 + (bz + 26) ** 2)
    shell = (sph > 27.0) & (sph < 31.5)
    paddle = (np.abs(by) < 13) & (bz > -6) & (bz < 22) & (bx > -8)
    blade = shell & paddle
    return {"metal": blade, "interior": shaft & ~blade}


# --- items: name -> [(material, field)] ---------------------------------------------

def build_items(lib: dict, rng: np.random.Generator) -> dict:
    return {
        "boulder": [("rock", boulder_field(rng))],
        "pad": [("metal", pad_field())],
        "ice_shard": [("ice", ice_shard_field(rng))],
        "sand_mound": [("sand", sand_mound_field(lib, rng))],
        "shovel": list(shovel_fields().items()),
    }


def emit_item(parts, lib, rng, variance: bool = True) -> dict:
    chunks = []
    for mat, field in parts:
        ext = register_material(lib, mat)
        s = emit_splats(field, mat, sigma=0.9)
        if s is None:
            continue
        s = sample_variance(s, ext, rng) if variance else attach_flat(s, ext)
        chunks.append(s)
    if not chunks:
        raise RuntimeError("item produced no splats")
    out = {k: np.concatenate([c[k] for c in chunks], axis=0)
           for k in ("pos", "normal", "cov", "albedo", "alpha", "subsurface",
                     "roughness", "metallic")}
    out["tissue"] = sum((c["tissue"] for c in chunks), [])
    return out


def frame_of(splats: dict):
    center = splats["pos"].mean(axis=0)
    radius = float(np.linalg.norm(splats["pos"] - center, axis=1).max()) + 3.0
    return center, radius


def pick_rasterizer():
    """GPU (Warp, core.splat_gpu) when a CUDA device is up — measured 41x per frame,
    162 fps relight sweeps, parity MAE 2.2e-4 vs this file's CPU path (2026-07-18).
    CHIMERA_SPLAT_GPU=0 forces the CPU reference path."""
    import os
    if os.environ.get("CHIMERA_SPLAT_GPU", "1") != "0":
        try:
            from core import splat_gpu
            if splat_gpu.available():
                return splat_gpu.rasterize, "gpu (warp/cuda)"
        except Exception:
            pass
    return rasterize, "cpu (numpy reference)"


def main() -> int:
    only = sys.argv[1] if len(sys.argv) > 1 else None
    rng = np.random.default_rng(SEED)
    lib = load_library()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RASTER, backend = pick_rasterizer()
    print(f"rasterizer: {backend}")
    items = build_items(lib, rng)
    if only:
        items = {only: items[only]}
    results, contact, contact_labels = {}, [], []
    t0 = time.time()

    for name, parts in items.items():
        t = time.time()
        splats = emit_item(parts, lib, rng, variance=True)
        center, radius = frame_of(splats)
        frames = [RASTER(splats, center, radius, *CAM, la, le) for la, le in RELIGHT]
        labels = [f"light{la}/{le}" for la, le in RELIGHT]
        p = OUT_DIR / f"item_{name}_relight.png"
        hstack_strip(frames, labels).save(p)
        contact.append(frames[1]); contact_labels.append(name)
        results[name] = {"splats": len(splats["pos"]),
                         "materials": sorted(set(splats["tissue"])),
                         "secs": round(time.time() - t, 1), "png": str(p)}
        print(f"  {name}: {results[name]['splats']} splats "
              f"({'+'.join(results[name]['materials'])}) {results[name]['secs']}s -> {p}")

    if not only:
        # the thesis shot: same entry, variance OFF vs ON
        rock_parts = [("rock", boulder_field(np.random.default_rng(21)))]
        off = emit_item(rock_parts, lib, np.random.default_rng(3), variance=False)
        on = emit_item(rock_parts, lib, np.random.default_rng(3), variance=True)
        c, r = frame_of(on)
        la, le = RELIGHT[1]
        pair = [RASTER(off, c, r, *CAM, la, le), RASTER(on, c, r, *CAM, la, le)]
        pv = OUT_DIR / "rock_variance_off_on.png"
        hstack_strip(pair, ["variance OFF (the mean)", "variance ON (sampled)"]).save(pv)
        results["rock_variance_pair"] = str(pv)

        # the family shot: five boulders from ONE library entry, no two alike
        fam_frames, fam_labels = [], []
        for i in range(5):
            f_rng = np.random.default_rng(100 + i)
            s = emit_item([("rock", boulder_field(f_rng))], lib, f_rng, variance=True)
            c, r = frame_of(s)
            fam_frames.append(RASTER(s, c, r, *CAM, 110, 45, w=250, h=250))
            fam_labels.append(f"rock #{i + 1}")
        pf = OUT_DIR / "rock_family.png"
        hstack_strip(fam_frames, fam_labels).save(pf)
        results["rock_family"] = str(pf)

        pc = OUT_DIR / "contact_sheet.png"
        hstack_strip(contact, contact_labels).save(pc)
        results["contact_sheet"] = str(pc)

    results["total_secs"] = round(time.time() - t0, 1)
    (OUT_DIR / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"done in {results['total_secs']}s -> {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
