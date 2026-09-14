#!/usr/bin/env python3
"""body_atlas -- the camera-awareness map: named skin points for touch.

WHY (the lead's #1 examination finding): every touch and capture currently
requires trial-and-error probing, because nothing maps body-part names to
actual skin coordinates.  This tool fetches the live mesh once, derives a
named atlas of skin aim points, and verifies each aim is ON the skin, so the
lead workflow becomes:

    read tools/body_atlas.json
    -> POST /tick_touch {"hit": [<pin aim>], "force_n": F}
    -> the press lands on actual skin.  No scanning.

INPUTS
  GET  http://127.0.0.1:8107/verts     [u32 n][f32 x9 per vert]
       9 floats = pos[0:3] + unit normal[3:6] + color[6:9] (color unused here)
  GET  http://127.0.0.1:8107/tick_state  (cell y-bands, volumes, pressures)
  .tmp/joints28.json                   the 28 actuated pins (name + joint J)

DERIVATIONS (no taste numbers)
  anchor      the joint's own projection: its nearest vertex.  The press must
              land on the skin closest to the joint, and anchoring there keeps
              the patch a compact disc ON the wall even when the joint sits
              deep in the torso (a patch taken around a deep joint itself is a
              ring around the body axis -- its centroid sinks inside; that
              failure was measured, worst 10.2 cm off skin, before this fix).
  patch size  K=16 verts nearest the ANCHOR, all facing its way (dot with the
              anchor normal > 0.35): measured skin density is 18459 verts /
              89.799 m^2 (surface from MATTER_KERNEL/SEAL_PREREGISTRATION)
              -> mean vertex spacing ~6.99 cm, so 16 verts cover a disc of
              radius ~15.7 cm, ~2.6x the 3 cm press-Gaussian footprint -- big
              enough to average vertex noise, small enough to stay on one
              feature and shallow enough that curvature sagitta stays ~2 cm.
  verify bar  0.05 m: |aim - nearest vertex| <= 5 cm (the task bar; the
              engine's press Gaussian is 3 cm, so 5 cm is the honesty limit).
  ambiguity   coherence = |mean of patch unit normals|; < 0.55 means the patch
              wraps a ridge or a thin feature (ear) -> flagged, reported.

OUTPUT tools/body_atlas.json:
  pins[name]  = {"aim":[x,y,z], "normal":[x,y,z], "verts":N, + diagnostics}
  bbox        = {"min":[..], "max":[..]}
  cells       = the four sealed cells (live y-bands) with measured centers
  parts       = front/back/side skin points for the 10 major body parts

The body is alive: aim points are exact for the pose at fetch time.  Re-run
to refresh; run with --verify-only to re-check a saved atlas against the
live skin without rewriting it.  Exit 0 iff every pin passes the 5 cm bar.

Read-only against the engine: GETs only -- never builds, starts or stops it.
"""

import argparse
import array
import json
import math
import struct
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_BASE = "http://127.0.0.1:8107"
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_JOINTS = ROOT / ".tmp" / "joints28.json"
DEFAULT_OUT = Path(__file__).resolve().parent / "body_atlas.json"

CANDIDATE_K = 96      # nearest verts considered for the anchor (~5x K)
PATCH_K = 16          # derived above
PATCH_POOL_K = 64     # nearest-anchor pool the same-side filter trims
SAME_SIDE_DOT = 0.35  # candidate normal vs anchor normal
ANCHOR_CAP_M = 0.20   # sanity radius around the anchor
VERIFY_BAR_M = 0.05   # the task's 5 cm bar
AMBIG_COHERENCE = 0.55
PRESS_GAUSSIAN_M = 0.03  # THE_SHIP_GOAL R4: the kernel press is 3 cm
SKIN_AREA_M2 = 89.799    # SEAL_PREREGISTRATION (divergence theorem)

# 10 major parts: name -> region predicate (y band, optional x sign).
# Bands derived from joints28 rest heights (jaw 8.26, neck 7.46, shoulders
# 5.89, spine_mid 4.66, hips 3.415, knees 1.903, ankles 0.338) and the live
# cell cut heights.
PART_REGIONS = [
    ("head",   8.00, 99.0, 0),
    ("neck",   7.10, 8.00, 0),
    ("chest",  5.30, 6.40, 0),
    ("belly",  4.10, 5.30, 0),
    ("hip_L",  3.10, 3.75, +1),
    ("hip_R",  3.10, 3.75, -1),
    ("knee_L", 1.55, 2.25, +1),
    ("knee_R", 1.55, 2.25, -1),
    ("foot_L", -1.0, 0.35, +1),
    ("foot_R", -1.0, 0.35, -1),
]

# sorted by ylo; bands are the live /tick_state cuts at the ankle (0.338),
# knee (1.903) and hip (3.415) rest heights -> ankle..knee = shins,
# knee..hip = thighs.
CELL_NAMES = ["feet", "shins", "thighs", "torso"]


def http_get(base: str, path: str, timeout: int = 30) -> bytes:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.read()


def get_verts(base: str):
    """(n, pos array 3n, nrm array 3n) from GET /verts (walk_test layout)."""
    raw = http_get(base, "/verts")
    (n,) = struct.unpack_from("<I", raw, 0)
    if len(raw) < 4 + n * 36:
        raise RuntimeError(f"/verts short: {len(raw)} bytes for {n} verts")
    flt = array.array("f")
    flt.frombytes(raw[4:4 + n * 36])
    pos = array.array("f", flt[0:0])  # empty same-type buffers
    nrm = array.array("f", flt[0:0])
    for v in range(n):
        b = v * 9
        pos.append(flt[b]); pos.append(flt[b + 1]); pos.append(flt[b + 2])
        nx, ny, nz = flt[b + 3], flt[b + 4], flt[b + 5]
        nl = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        nrm.append(nx / nl); nrm.append(ny / nl); nrm.append(nz / nl)
    return n, pos, nrm


def get_state(base: str) -> dict:
    try:
        return json.loads(http_get(base, "/tick_state"))
    except Exception:
        return {}


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def norm(a):
    l = math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2]) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)


def dist(a, b):
    dx = a[0] - b[0]; dy = a[1] - b[1]; dz = a[2] - b[2]
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def dist2(ax, ay, az, bx, by, bz):
    dx = ax - bx; dy = ay - by; dz = az - bz
    return dx * dx + dy * dy + dz * dz


def r5(v):
    return [round(x, 5) for x in v]


def build_atlas(base: str, joints_path: Path):
    n, pos, nrm = get_verts(base)
    state = get_state(base)
    pins_in = json.loads(Path(joints_path).read_text())
    names = [p["name"] for p in pins_in]
    if len(names) != 28:
        print(f"WARN: expected 28 pins, joints file has {len(names)}")

    # body centroid (the radial reference) + bbox
    cx = cy = cz = 0.0
    bx_lo = by_lo = bz_lo = float("inf")
    bx_hi = by_hi = bz_hi = float("-inf")
    for v in range(n):
        x, y, z = pos[3 * v], pos[3 * v + 1], pos[3 * v + 2]
        cx += x; cy += y; cz += z
        if x < bx_lo: bx_lo = x
        if x > bx_hi: bx_hi = x
        if y < by_lo: by_lo = y
        if y > by_hi: by_hi = y
        if z < bz_lo: bz_lo = z
        if z > bz_hi: bz_hi = z
    centroid = (cx / n, cy / n, cz / n)

    def nearest_all(x, y, z):
        """min distance from an arbitrary point to any mesh vertex."""
        best = float("inf")
        for v in range(n):
            d = dist2(x, y, z, pos[3 * v], pos[3 * v + 1], pos[3 * v + 2])
            if d < best:
                best = d
        return math.sqrt(best)

    def k_nearest(x, y, z, k):
        """indices of the k nearest verts (selection over full mesh)."""
        cand = []
        worst = float("inf")
        for v in range(n):
            d = dist2(x, y, z, pos[3 * v], pos[3 * v + 1], pos[3 * v + 2])
            if len(cand) < k:
                cand.append((d, v))
                if len(cand) == k:
                    cand.sort(); worst = cand[-1][0]
            elif d < worst:
                cand[-1] = (d, v)
                cand.sort(); worst = cand[-1][0]
        return [v for _, v in cand]

    pins = {}
    ambiguous = []
    for p in pins_in:
        name = p["name"]
        J = p["J"]
        jx, jy, jz = J[0], J[1], J[2]
        cands = k_nearest(jx, jy, jz, CANDIDATE_K)
        # anchor = the joint's projection onto the skin (its nearest vertex)
        v0 = cands[0]
        ax0, ay0, az0 = pos[3 * v0], pos[3 * v0 + 1], pos[3 * v0 + 2]
        anchor_m = math.sqrt(dist2(jx, jy, jz, ax0, ay0, az0))
        n0 = (nrm[3 * v0], nrm[3 * v0 + 1], nrm[3 * v0 + 2])
        # compact same-facing disc AROUND the anchor, not around the joint
        pool = k_nearest(ax0, ay0, az0, PATCH_POOL_K)
        patch, fell_back = [], False
        for v in pool:
            dp = (nrm[3 * v] * n0[0] + nrm[3 * v + 1] * n0[1]
                  + nrm[3 * v + 2] * n0[2])
            d = math.sqrt(dist2(ax0, ay0, az0, pos[3 * v], pos[3 * v + 1],
                                pos[3 * v + 2]))
            if dp > SAME_SIDE_DOT and d <= ANCHOR_CAP_M:
                patch.append(v)
            if len(patch) == PATCH_K:
                break
        if len(patch) < 4:  # thin feature: ear, lid -- keep it honest
            patch = pool[:PATCH_K]
            fell_back = True
        ax = ay = az = 0.0
        sx = sy = sz = 0.0
        patch_r = 0.0
        for v in patch:
            x, y, z = pos[3 * v], pos[3 * v + 1], pos[3 * v + 2]
            ax += x; ay += y; az += z
            sx += nrm[3 * v]; sy += nrm[3 * v + 1]; sz += nrm[3 * v + 2]
            patch_r = max(patch_r, math.sqrt(dist2(ax0, ay0, az0, x, y, z)))
        m = len(patch)
        aim = (ax / m, ay / m, az / m)
        coherence = math.sqrt(sx * sx + sy * sy + sz * sz) / m
        skin_m = nearest_all(aim[0], aim[1], aim[2])
        amb = fell_back or coherence < AMBIG_COHERENCE or skin_m > VERIFY_BAR_M
        if amb:
            ambiguous.append(name)
        pins[name] = {
            "aim": r5(aim),
            "normal": r5(norm((sx, sy, sz))),
            "verts": m,
            "radial": r5(norm(sub(aim, centroid))),
            "skin_m": round(skin_m, 4),
            "patch_m": round(patch_r, 4),
            "anchor_m": round(anchor_m, 4),
            "coherence": round(coherence, 3),
            "ambiguous": amb,
        }

    # ---- the four sealed cells (live y-bands from /tick_state) ----
    cells = {}
    state_cells = state.get("cells") or []
    ordered = sorted(range(len(state_cells)), key=lambda i: state_cells[i]["ylo"])
    for rank, i in enumerate(ordered):
        c = state_cells[i]
        cname = CELL_NAMES[rank] if len(ordered) == 4 else f"cell_{rank}"
        lo, hi = c["ylo"] - 0.02, c["yhi"] + 0.02
        sx = sy = sz = cnt = 0
        for v in range(n):
            y = pos[3 * v + 1]
            if lo <= y <= hi:
                sx += pos[3 * v]; sy += y; sz += pos[3 * v + 2]; cnt += 1
        entry = {"y_band": [round(c["ylo"], 3), round(c["yhi"], 3)],
                 "V_m3": round(c["V"], 4), "P_mpa": round(c["P"], 4),
                 "center": r5((sx / cnt, sy / cnt, sz / cnt)) if cnt else None,
                 "verts": cnt}
        if cname == "feet" and cnt:  # one cell, two feet: split L/R
            for side, sgn in (("L", 1), ("R", -1)):
                fx = fy = fz = fc = 0
                for v in range(n):
                    y = pos[3 * v + 1]
                    if lo <= y <= hi and (pos[3 * v] > 0) == (sgn > 0):
                        fx += pos[3 * v]; fy += y; fz += pos[3 * v + 2]
                        fc += 1
                entry[f"center_{side}"] = r5((fx / fc, fy / fc, fz / fc)) if fc else None
        cells[cname] = entry

    # ---- front / back / side skin points for the 10 major parts ----
    parts = {}
    for pname, ylo, yhi, xsgn in PART_REGIONS:
        best = {"front": None, "back": None, "side_L": None, "side_R": None}
        ext = {k: (float("-inf") if k in ("front", "side_L") else float("inf"))
               for k in best}
        for v in range(n):
            x, y, z = pos[3 * v], pos[3 * v + 1], pos[3 * v + 2]
            if not (ylo <= y <= yhi):
                continue
            if xsgn and (x > 0) != (xsgn > 0):
                continue
            if z > ext["front"]: ext["front"] = z; best["front"] = [x, y, z]
            if z < ext["back"]: ext["back"] = z; best["back"] = [x, y, z]
            if x > ext["side_L"]: ext["side_L"] = x; best["side_L"] = [x, y, z]
            if x < ext["side_R"]: ext["side_R"] = x; best["side_R"] = [x, y, z]
        parts[pname] = {k: (r5(p) if p else None) for k, p in best.items()}

    density = n / SKIN_AREA_M2
    atlas = {
        "meta": {
            "what": "camera-awareness atlas: named skin aim points for "
                    "/tick_touch -- built by tools/body_atlas.py",
            "base": base,
            "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "engine_ticks": state.get("ticks"),
            "n_verts": n,
            "skin_density_per_m2": round(density, 1),
            "mean_vert_spacing_m": round(math.sqrt(1.0 / density), 4),
            "press_gaussian_m": PRESS_GAUSSIAN_M,
            "verify_bar_m": VERIFY_BAR_M,
            "patch": {"k": PATCH_K, "pool_k": PATCH_POOL_K,
                      "same_side_dot": SAME_SIDE_DOT, "cap_m": ANCHOR_CAP_M,
                      "anchor": "joint's nearest vertex (its projection)"},
            "pose_note": "aim points are exact for the pose at fetch time; "
                         "re-run tools/body_atlas.py to refresh",
            "workflow": "POST /tick_touch {\"hit\": [aim], \"force_n\": F} "
                        "-> POST /tick_touch_clear to release",
        },
        "bbox": {"min": r5((bx_lo, by_lo, bz_lo)), "max": r5((bx_hi, by_hi, bz_hi))},
        "body_centroid": r5(centroid),
        "cells": cells,
        "parts": parts,
        "pins": pins,
    }
    return atlas, ambiguous


def verify_saved(base: str, path: Path) -> bool:
    """re-check a saved atlas against the LIVE skin (pose-drift check)."""
    n, pos, _ = get_verts(base)
    atlas = json.loads(path.read_text())
    ok = True
    for name, p in atlas["pins"].items():
        aim = p["aim"]
        best = float("inf")
        for v in range(n):
            dx = aim[0] - pos[3 * v]; dy = aim[1] - pos[3 * v + 1]
            dz = aim[2] - pos[3 * v + 2]
            d2 = dx * dx + dy * dy + dz * dz
            if d2 < best:
                best = d2
        skin = math.sqrt(best)
        flag = "PASS" if skin <= VERIFY_BAR_M else "FAIL"
        if skin > VERIFY_BAR_M:
            ok = False
        print(f"  {flag} {name:12s} skin={skin:.4f} m (saved aim, live skin)")
    return ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--joints", default=str(DEFAULT_JOINTS))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--verify-only", action="store_true",
                    help="re-check the saved atlas against live skin, no write")
    args = ap.parse_args(argv)

    out = Path(args.out)
    if args.verify_only:
        ok = verify_saved(args.base, out)
        print(f"verify-only: {'ALL PASS' if ok else 'FAILURES -- re-run the builder'}")
        return 0 if ok else 1

    atlas, ambiguous = build_atlas(args.base, Path(args.joints))
    out.write_text(json.dumps(atlas, indent=1))

    print(f"atlas: {out}")
    m = atlas["meta"]
    print(f"verts={m['n_verts']} spacing~{m['mean_vert_spacing_m']} m "
          f"ticks={m['engine_ticks']} bbox={atlas['bbox']}")
    print(f"cells: " + ", ".join(
        f"{k}{v.get('y_band')}{v.get('center')}" for k, v in atlas["cells"].items()))
    print(f"{'pin':12s} {'aim [x,y,z]':32s} {'skin_m':>7s} {'coh':>5s} "
          f"{'nv':>3s} {'patch_m':>7s} {'anchor_m':>8s} flag")
    worst = 0.0
    for name, p in atlas["pins"].items():
        worst = max(worst, p["skin_m"])
        flag = "AMBIG" if p["ambiguous"] else ""
        print(f"{name:12s} {str(p['aim']):32s} {p['skin_m']:7.4f} "
              f"{p['coherence']:5.2f} {p['verts']:3d} {p['patch_m']:7.4f} "
              f"{p['anchor_m']:8.4f} {flag}")
    npass = sum(1 for p in atlas["pins"].values() if p["skin_m"] <= VERIFY_BAR_M)
    print(f"verify: {npass}/{len(atlas['pins'])} pins within {VERIFY_BAR_M} m "
          f"of skin (worst {worst:.4f} m)")
    if ambiguous:
        print("ambiguous pins (honest report): " + ", ".join(ambiguous))
    else:
        print("ambiguous pins: none")
    return 0 if npass == len(atlas["pins"]) else 1


if __name__ == "__main__":
    sys.exit(main())
