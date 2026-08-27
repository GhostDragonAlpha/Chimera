"""theShape -- the voxel lattice body: the cloud becomes cells, and the cells are the SAME body.

S0 FRAME (recorded at the engine): "the voxel lattice body built from the generated
3DGS cloud has the same center of mass as the cloud it was built from, to within one
lattice cell of discretization slack."

RULE 0 -- stated before the build:
    STATEMENT : discretizing the seed's cloud (alpha >= 0.5, the honest matter cut
                theSeed published) into a uniform-mass voxel lattice moves the body's
                center of mass by less than one cell -- the CA will animate the bear
                the seed grew, not a shifted cousin.
    PREDICTION: |lattice_com - cloud_com| / cell_size < 1.0 per axis AND in magnitude,
                measured on the SAME cloud theSeed proved, at the cell size the body's
                own smallest load-bearing member derives.
    FALSIFIER : any axis, at any of 8 lattice origin phases, lands at or past 1.0 cell
                -- then the lattice is a different body and the fix is a finer lattice
                law, never a wider slack. (Named before the run; the run read 0.653
                cells worst-case, so the bound stands untuned.)

THE CELL SIZE IS DERIVED, NOT CHOSEN (law 2, the same law cad_sample's packet rule
uses): the smallest load-bearing member is the paw; measured from the cloud (lowest
2% of splats, 1 cm XZ blobs): min paw semi-axis = 6 cm, and a member must carry >= 3
cells across, so s = 0.02 m. A bigger cell would loosen the one-cell slack in metres
-- choosing it would be tolerance-widening in disguise, so the number comes from the
body or nowhere.

THE LATTICE IS SOLID. The cloud is a surface shell; the CA owns a body, and a body
has an inside (theMuscle will add/remove cells THROUGH it). Enclosed voids are filled
(scipy.ndimage.binary_fill_holes); the fill shifts the measured CoM and that shift is
part of the honest measurement, not hidden from it.

MATTER CONVENTIONS, each recorded because each could silently move the answer:
  - cloud side: uniform weight over surviving splat CENTERS (the alpha cut already
    decided what is matter; anisotropic splat extent is not claimed as extra matter).
  - lattice side: one cell, one unit of mass, at the cell center.
  - ties: floor((p - origin)/s) -- a splat exactly on a boundary falls to the lower
    cell, every time, so the build is reproducible to the bit.
  - axes: the asset is Y-up; the membrane scene is Z-up via (x, y, z) -> (x, -z, y)
    (theSeed's own convention). The CoM comparison runs in the ASSET frame.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]                       # story/theShape -> repo root
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

SPLAT_PATH = _ROOT / "models" / "genbear2" / "genbear2_final_engine.splat"
NUMBERS_PATH = _HERE / "numbers.json"
LATTICE_PATH = _HERE / "lattice_cells.npz"

ALPHA_CUT = 0.5         # theSeed's honest matter cut -- its published law, reused
PAW_FRACTION = 0.02     # lowest 2% of splats = the paw band (the contact members)
PAW_BLOB_RES = 0.01     # 1 cm XZ blobs for the paw measurement
MIN_CELLS_ACROSS = 3    # a load-bearing member must carry >= 3 cells (law 2)

NCOLS = 28
PX, PY, PZ = 0, 1, 2
TYPE = 11
CR, CG, CB, ALPHA = 16, 17, 18, 19
SIZE = 20

_CACHE: dict = {}


def _decode() -> tuple[np.ndarray, np.ndarray]:
    """Packed 32B 3DGS -> (pos, alpha), matter cut applied. Convention: theSeed's."""
    raw = np.fromfile(SPLAT_PATH, dtype=np.uint8)
    n = len(raw) // 32
    rec = raw[: n * 32].reshape(n, 32)
    pos = rec[:, 0:12].view(np.float32).reshape(n, 3).astype(np.float64)
    alpha = rec[:, 27].astype(np.float32) / 255.0
    return pos[alpha >= ALPHA_CUT], alpha


def _cell_size(pos: np.ndarray) -> tuple[float, dict]:
    """s = min paw semi-axis / 3, measured from the cloud's own paw band."""
    y_lo = float(np.quantile(pos[:, 1], PAW_FRACTION))
    paws = pos[pos[:, 1] <= y_lo]
    ij = np.floor((paws[:, [0, 2]] - paws[:, [0, 2]].min(0)) / PAW_BLOB_RES).astype(int)
    grid = np.zeros(ij.max(0) + 2, dtype=bool)
    grid[ij[:, 0], ij[:, 1]] = True
    from scipy import ndimage
    lab, nl = ndimage.label(grid, structure=np.ones((3, 3)))
    semi_min = np.inf
    blobs = []
    for k in range(1, nl + 1):
        ys, xs = np.where(lab == k)
        if len(ys) < 20:                 # dust is not a paw
            continue
        w = sorted(((ys.max() - ys.min() + 1) * PAW_BLOB_RES,
                    (xs.max() - xs.min() + 1) * PAW_BLOB_RES))
        blobs.append(w)
        semi_min = min(semi_min, w[0] / 2.0)
    s = float(semi_min / MIN_CELLS_ACROSS)
    return s, {"paw_band_splats": int(len(paws)), "paw_blobs": blobs,
               "min_paw_semiaxis_m": float(semi_min)}


def _build(s: float, phase: int = 0):
    """Voxelize at one origin phase. Returns (filled, origin, cells, cloud_pos)."""
    from scipy import ndimage
    pos, _ = _decode()
    off = np.array([(phase >> 0) & 1, (phase >> 1) & 1, (phase >> 2) & 1]) * (s / 2)
    origin = pos.min(0) - s * 0.5 + off
    idx = np.floor((pos - origin) / s).astype(np.int64)
    grid = np.zeros(idx.max(0) + 1, dtype=bool)
    grid[idx[:, 0], idx[:, 1], idx[:, 2]] = True
    filled = ndimage.binary_fill_holes(grid)
    return filled, origin, np.argwhere(filled), pos


def _lattice():
    """The canonical (phase-0) lattice, built once."""
    if "lat" not in _CACHE:
        s, paw = _cell_size(_decode()[0])
        filled, origin, cells, pos = _build(s, 0)
        _CACHE["lat"] = (s, paw, filled, origin, cells, pos)
    return _CACHE["lat"]


def derive(parent_nums=None, free=None):
    """Every discovered variable, measured from the cloud and the lattice. No chosen
    numbers: the cell size comes from the paws, the slack bound is one cell, and the
    gap is reported for all 8 origin phases so the verdict is not a lucky phase."""
    s, paw, filled, origin, cells, pos = _lattice()
    cloud_com = pos.mean(0)
    centers = origin + (cells + 0.5) * s
    lattice_com = centers.mean(0)

    gaps = []
    for ph in range(8):
        f2, o2, c2, _ = _build(s, ph)
        com2 = (o2 + (c2 + 0.5) * s).mean(0)
        gaps.append(((com2 - cloud_com) / s).tolist())
    gaps = np.array(gaps)
    gap0 = (lattice_com - cloud_com) / s

    # grain pitch, theSeed's derivation, recorded for completeness (the tiling
    # spacing is NOT the cell law here -- the paw is)
    sub = pos[:: max(1, len(pos) // 4000)]
    d = np.linalg.norm(sub[None, :, :] - sub[:, None, :], axis=2)
    d[d == 0.0] = np.inf
    pitch = float(np.median(d.min(axis=1)))

    nums = {
        "source_cloud": "models/genbear2/genbear2_final_engine.splat (packed 32B 3DGS, "
                        "the asset theSeed proved)",
        "splat_count": {"raw": 182724, "after_alpha_cut": int(len(pos))},
        "alpha_cut": ALPHA_CUT,
        "cell_size": s,
        "cell_size_law": (f"min paw semi-axis {paw['min_paw_semiaxis_m']:.4f} m "
                          f"/ {MIN_CELLS_ACROSS} cells across = {s:.4f} m; paw band = lowest "
                          f"{PAW_FRACTION:.0%} of splats, {paw['paw_blobs']} m blobs at "
                          f"{PAW_BLOB_RES} m"),
        "grain_pitch": pitch,
        "lattice_extent": {"bbox_min": pos.min(0).tolist(), "bbox_max": pos.max(0).tolist(),
                           "grid_shape": list(filled.shape)},
        "occupancy_rule": ">= occupancy_threshold surviving splat centers in the cell",
        "occupancy_threshold": 1,
        "cell_count": int(filled.sum()),
        "mass_per_cell": "uniform -- one cell, one unit of mass, at the cell center",
        "cloud_weighting": "uniform over surviving splat centers",
        "cloud_com": cloud_com.tolist(),
        "lattice_com": lattice_com.tolist(),
        "com_gap_cells": {"per_axis_phase0": gap0.tolist(),
                          "magnitude_phase0": float(np.linalg.norm(gap0)),
                          "worst_magnitude_over_8_phases": float(np.abs(gaps).max()
                                                                 and np.linalg.norm(gaps, axis=1).max())},
        "slack_bound": 1.0,
        "slack_per_axis": "bound applied per axis AND magnitude (strictest reading)",
        "gap_metric": "per-axis cells + Euclidean magnitude, cells",
        "lattice_origin": {"phase0": origin.tolist(),
                           "rule": "cloud bbox min - s/2 + phase*(s/2) per axis, 8 phases"},
        "axis_convention": "asset Y-up; membrane Z-up via (x,-z,y); CoM compared in asset frame",
        "void_fill": "enclosed voids filled (scipy.ndimage.binary_fill_holes)",
        "shell_vs_solid": "solid -- the CA owns a body, not a shell",
        "boundary_tie_rule": "floor((p-origin)/s) -- boundary ties fall to the lower cell",
        "lattice_artifact": "story/theShape/lattice_cells.npz (int32 cell indices + origin + s)",
        "cloud_scale": "unit-normalized, height on Y (extent_m 1.0 per theSeed)",
        "splat_extent": "point-center convention; anisotropic splat extent not claimed as matter",
        "extent_m": float(pos[:, 1].max() - pos[:, 1].min()),
        "duration_s": 15.02,     # theSeed's own clock: half the 721-frame AI orbit @ 24 fps
    }
    verdict = (np.abs(gap0).max() < 1.0) and (np.linalg.norm(gaps, axis=1).max() < 1.0)
    nums["verdict"] = ("HOLDS" if verdict else "FALSIFIED")
    return nums


def derive_commit():
    nums = derive()
    NUMBERS_PATH.write_text(json.dumps(nums, indent=1) + "\n", encoding="utf8")
    s, paw, filled, origin, cells, pos = _lattice()
    np.savez_compressed(LATTICE_PATH, cells=cells.astype(np.int32),
                        origin=origin.astype(np.float64), cell_size=np.float64(s))
    return nums


def emit(nums: dict, t: float) -> np.ndarray:
    """The lattice bear, turntabled a half-turn over the same fixed ground theSeed
    used: t=0 front, t=1 back. The grains are the CELLS -- the body the CA owns,
    shown as the body, so the blind eye can say whether the discretization still
    reads as the bear the seed grew."""
    s, paw, filled, origin, cells, pos = _lattice()
    centers = origin + (cells + 0.5) * s
    n = len(centers)
    buf = np.zeros((n, NCOLS), dtype=np.float32)
    # asset Y-up -> membrane Z-up: (x, y, z) -> (x, -z, y)
    buf[:, PX] = centers[:, 0]
    buf[:, PY] = -centers[:, 2]
    buf[:, PZ] = centers[:, 1]
    buf[:, TYPE] = 3.0
    buf[:, CR], buf[:, CG], buf[:, CB] = 0.45, 0.30, 0.18     # bear brown
    buf[:, ALPHA] = 1.0
    buf[:, SIZE] = s

    ang = np.pi * float(np.clip(t, 0.0, 1.0))
    if ang != 0.0:
        c, sn = np.cos(ang), np.sin(ang)
        x = buf[:, PX].copy()
        y = buf[:, PY].copy()
        buf[:, PX] = c * x - sn * y
        buf[:, PY] = sn * x + c * y

    z_floor = float(buf[:, PZ].min()) - s
    r_xy = float(np.abs(buf[:, [PX, PY]]).max()) * 1.5
    n_g = 900
    rng = np.random.default_rng(7)
    th = rng.random(n_g) * 2.0 * np.pi
    rr = r_xy * np.sqrt(rng.random(n_g))
    g = np.zeros((n_g, NCOLS), dtype=np.float32)
    g[:, PX], g[:, PY], g[:, PZ] = rr * np.cos(th), rr * np.sin(th), z_floor
    g[:, TYPE], g[:, ALPHA] = 3.0, 1.0
    g[:, SIZE] = r_xy * 0.06
    g[:, CR], g[:, CG], g[:, CB] = 0.16, 0.15, 0.14
    return np.concatenate([buf, g], axis=0)


if __name__ == "__main__":
    out = derive_commit()
    print(json.dumps({k: out[k] for k in ("cell_size", "cell_count", "com_gap_cells",
                                          "verdict")}, indent=1))
