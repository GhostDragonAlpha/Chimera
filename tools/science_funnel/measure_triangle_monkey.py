"""measure_triangle_monkey.py -- the pre-registered falsifier measurements for
receipt triangle_monkey_20260920 (lane agent/triangle-monkey-grid-20260920).

Deterministic, pixel-based, NO model calls. Drives a running engine over HTTP:

  A  fixed-pose monkey render, splat presentation (BEFORE) and mesh
     presentation (AFTER): grain + coverage + per-region coverage
     (regions derived from manifest.json bone extents).
  B  two fixed camera poses (above the plane with the body BELOW it; below the
     plane with the body ABOVE it): object_seen + guide_seen from both sides.
  C  full 36-frame orbit at a sub-clearance radius: the clip scan.

Every number is appended to the receipt's measurement block by the caller.
Usage (see --help): the three subcommands `a`, `b`, `c` each take --engine,
--presentation {splat,mesh}, --outdir, and write PNG + JSON evidence.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.science_funnel import pixel_truth as pt
from tools.science_funnel import ct_skeleton_layer as CSL
from tools.science_funnel import ct_skeleton_triangle as CST

ROOT = CSL.ROOT
ENGINE_FOV_Y_DEG = 45.0
CAMERA_MARGIN = 1.35
ORBIT_FRAMES = 36
CLIP_RADIUS = 1.0           # the engine's own /camera radius floor (the reachable
                            # orbit distance; radius_floor() = max(1, sphere*1.02))
CLIP_PHI = 0.20             # low elevation: the eye passes just under the body
CLIP_PAN = -0.93            # THE OPERATOR'S SCENARIO (pan, then orbit): pan is
                            # the unclamped eye offset (mouse pan in the studio),
                            # so orbiting with it swings the eye to within
                            # |cos(phi)-|pan|| = 0.059 of the axis at the close
                            # phase — eye-to-surface ~0.05-0.08, INSIDE the old
                            # fixed 0.1 near plane — while at the front phase it
                            # sits at ~1.94. The tracking near plane
                            # (clearance*0.25) does not clip.
                            # (Negative controls, recorded: radius 0.40/0.20
                            # without pan never clips — the radius clamp keeps
                            # the eye >= 1.0 from the axis.)
C_LIFT = 0.55               # the C orbit is flown with the body fully ABOVE the
                            # plane so Defect B's floor occlusion (fixed in the
                            # same lane) cannot confound the paired counts; the
                            # C verdict is the PAIRED per-frame metric:
                            # clip_stolen_pixels[frame] =
                            #   max(0, count_fixed[frame] - count_before[frame])
                            # same pose, same pan, only the near law differs.
                            # VERDICT fires if any frame's BEFORE count
                            # < 0.5 x the AFTER count at the same frame.
POSE_ABOVE = 1.23           # camera elevation for the above pose: the eye
                            # height is target_y + radius*sin(phi) = -0.55 +
                            # 1.0087*sin(1.23) = +0.40 -- the eye stays ABOVE
                            # the plane (0.40 clear of it, so the plane's own
                            # near-field is beyond the 0.1 near wall) while
                            # looking down at the below-plane body: the plane
                            # crosses every sight line to the body
POSE_BELOW = -1.23          # mirror pose: eye at +0.55 - 0.95 = -0.40,
                            # BELOW the plane, looking up at the above-plane body
MESH_LIFT = 0.55            # |y| offset that puts the recentered body fully
                            # on one side of the plane (body half-height 0.31)
A_LIFT = 0.40               # fixed-pose A lift: body min y (-0.31) -> +0.09,
                            # fully above the plane on both engines
                            # on one side of the plane (body half-height 0.31)


def _retry_urlopen(req, timeout: float, attempts: int = 4):
    """The engine serves HTTP on ONE worker; a STRICTLY FRESH /frame wait can
    block that worker so the next request hits a full listen backlog (WinError
    10061 — the skeleton_movie._retry_urlopen precedent). Retry with backoff."""
    last = None
    for i in range(attempts):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except (urllib.error.URLError, ConnectionError, OSError) as e:
            last = e
            time.sleep(0.25 * (i + 1))
    raise last


def _require(condition, code, detail=None):
    if not condition:
        raise RuntimeError(f"measure refusal: {code} {detail or ''}")


def _fetch(url: str, path: str, timeout: float = 30.0) -> bytes:
    req = urllib.request.Request(url + path)
    with _retry_urlopen(req, timeout=timeout) as r:
        return r.read()


def _post_json(url: str, path: str, payload: dict, timeout: float = 15.0):
    req = urllib.request.Request(url + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with _retry_urlopen(req, timeout=timeout) as r:
        return r.status == 200


def _settle_frame(url: str, prev: bytes | None, timeout: float = 12.0) -> bytes:
    """Two consecutive equal fresh captures (skeleton_movie's settle law)."""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        b = _fetch(url, "/frame")
        if prev is not None and b == prev:
            last = None
            time.sleep(0.06)
            continue
        if last is not None and b == last:
            return b
        last = b
        time.sleep(0.06)
    return _fetch(url, "/frame")


# ── the engine camera law, replicated for the projected footprints ──────────
# (engine.cpp update_camera_matrices: 45 deg y-FOV, Y-negated perspective for
# Vulkan, eye from spherical coords, up = d(eye)/d(phi); near plane irrelevant
# for the footprint hull.)

def project_points(pts_m: np.ndarray, radius: float, theta: float, phi: float,
                   width: int, height: int,
                   target: tuple = (0.0, 0.0, 0.0)) -> np.ndarray:
    """World metres -> pixel coordinates under the engine camera law (orbit
    around the camera TARGET; the engine looks at the target)."""
    pts = np.asarray(pts_m, dtype=np.float64)
    c, s = math.cos(phi), math.sin(phi)
    cx, sx = math.cos(theta), math.sin(theta)
    tgt = np.asarray(target, dtype=np.float64)
    eye = tgt + np.array([radius * c * sx, radius * s, -radius * c * cx])
    up = np.array([-s * sx, c, s * cx])
    fwd = tgt - eye
    fwd = fwd / np.linalg.norm(fwd)                     # look at the target
    right = np.cross(fwd, up)
    right /= np.linalg.norm(right)
    upv = np.cross(right, fwd)
    rel = pts - eye
    cam = np.stack([rel @ right, rel @ upv, rel @ fwd], axis=1)
    half = math.tan(math.radians(ENGINE_FOV_Y_DEG) / 2.0)
    aspect = width / height
    x_ndc = (cam[:, 0] / (cam[:, 2] * half * aspect))
    y_ndc = (cam[:, 1] / (cam[:, 2] * half))
    px = (x_ndc * 0.5 + 0.5) * width
    py = (1.0 - (y_ndc * 0.5 + 0.5)) * height           # Vulkan NDC is Y-down
    return np.stack([px, py], axis=1)


def compose(presentation: str) -> dict:
    """The registered layer, recentered (bbox centre -> the orbit origin)."""
    if presentation == "mesh":
        layer = CST.layer_triangle_mesh()
        payload = layer["verts9"].copy()
        tris = layer["tris"]
    else:
        buf, record = CSL.layer_splat_buffer(3)
        payload = buf
        tris = None
        layer = {"record": record}
    ctr = (payload[:, 0:3].min(axis=0) + payload[:, 0:3].max(axis=0)) / 2.0
    payload[:, 0:3] = (payload[:, 0:3] - ctr.astype(np.float32))
    return {"payload": payload, "tris": tris, "record": layer.get("record", {})}


def post_presentation(url: str, comp: dict, radius: float, theta: float,
                      phi: float, lift: float = 0.0,
                      target: tuple = (0.0, 0.0, 0.0)) -> bool:
    """Upload the presentation payload (mesh -> /mesh_bin, splat ->
    /membrane_bin), with an optional +y lift for the two-sided grid poses and
    the orbit target the /camera posts carry."""
    payload = comp["payload"].copy()
    if lift:
        payload[:, 1] += np.float32(lift)
    if comp["tris"] is not None:
        return CST.post_layer_mesh(url, payload, comp["tris"], radius, theta, phi)
    n = int(payload.shape[0])
    header = np.zeros(1, dtype=np.uint32).tobytes()
    import struct
    header = struct.pack("<I3f", n, float(radius), float(theta), float(phi))
    req = urllib.request.Request(
        f"{url.rstrip('/')}/membrane_bin",
        data=header + np.ascontiguousarray(payload, dtype=np.float32).tobytes(),
        headers={"Content-Type": "application/octet-stream"}, method="POST")
    with urllib.request.urlopen(req, timeout=180.0) as r:
        return r.status == 200 and b'"ok":true' in r.read()


def fit_radius(comp: dict) -> float:
    pos = comp["payload"][:, 0:3].astype(np.float64)
    h = float(pos[:, 1].max() - pos[:, 1].min())
    return CAMERA_MARGIN * (h / 2.0) / math.tan(math.radians(ENGINE_FOV_Y_DEG) / 2.0)


def fit_radius_offset(pos: np.ndarray, theta: float, phi: float,
                      width: int, height: int, margin: float = CAMERA_MARGIN) -> float:
    """Smallest orbit radius at which the LIFTED body fits the frame with the
    fit margin, computed by bisection on the ACTUAL projection law (the engine
    always looks at the ORIGIN, so a lifted body sits off the view axis; the
    closed-form height fit no longer applies). Derived, not picked."""
    sample = pos[::max(1, len(pos) // 20000)]          # bounded, deterministic
    lo, hi = 0.3, 20.0

    def fits(r: float) -> bool:
        pts = project_points(sample, r, theta, phi, width, height)
        return (pts[:, 0].min() > (1 - 1 / margin) * width / 2
                and pts[:, 0].max() < (1 + 1 / margin) * width / 2
                and pts[:, 1].min() > (1 - 1 / margin) * height / 2
                and pts[:, 1].max() < (1 + 1 / margin) * height / 2)

    _require(fits(hi), "body_does_not_fit_even_at_r20")
    for _ in range(24):                                 # 2^-24 convergence
        mid = 0.5 * (lo + hi)
        if fits(mid):
            hi = mid
        else:
            lo = mid
    return hi


def regions_along_trunk(comp: dict, presentation: str = "mesh") -> dict:
    """Per-bone + macro regions derived from manifest.json bone extents.

    Macro regions (operator's skull / spine-ribs / limbs, derived, not picked):
    the composite bone_01 IS the fused axial skeleton (skull+spine+ribs), so a
    vertex split of bone_01 along the composite's trunk axis (the registration's
    own PCA, p30/p85 of the bone_01 span) separates the skull end from the
    spine/rib cage; every other committed bone is appendicular (limbs)."""
    man = json.loads((CSL.CT_DIR / "meshes" / "manifest.json").read_text())
    raw = CSL.WALKER_DERIVED_PATH.read_bytes()
    hat = float(json.loads(raw)["body_model"]["segments_Table1"]["HAT"]["length_m"])
    composite = CSL.load_obj_vertices(CSL.PREVIEW_DIR / CSL.COMPOSITE_PREVIEW)
    scale, R, translation, _ = CSL.ct_registration(composite, hat, CSL._seat_height())
    comp01_scene = CSL.apply_registration(composite, scale, R, translation)
    bone01_centered = comp01_scene - comp01_scene.mean(axis=0)
    cov = np.cov(bone01_centered.T)
    evals, evecs = np.linalg.eigh(cov)
    axis = evecs[:, int(np.argmax(evals))]
    if axis[1] < 0:
        axis = -axis                                    # +Y = skull end (upright)
    t01 = (bone01_centered @ axis)
    p30, p85 = np.percentile(t01, [30.0, 85.0])

    stride = 3 if presentation == "splat" else 1   # the splat payload samples
                                                   # every 3rd vertex per bone
    per_frame = []
    macro = {"skull": [], "spine_ribs": [], "limbs": []}
    offset = 0
    for entry in man["bones"]:
        name = Path(entry["file"]).name
        preview = name.replace(".obj", "_lo.obj")
        verts_mm, _ = CST.load_obj_mesh(CSL.PREVIEW_DIR / preview)
        scene = CSL.apply_registration(verts_mm, scale, R, translation)
        n = scene.shape[0]
        # payload rows are CONSECUTIVE; the stride subsampling happens in the
        # bone's own vertex space (the payload stores ceil(n/stride) per bone)
        count = int(len(np.arange(0, n, stride)))
        rows = np.arange(offset, offset + count)
        offset += count
        per_frame.append({"preview": preview, "rows": rows, "n": count})
        if preview != CSL.COMPOSITE_PREVIEW:
            macro["limbs"].append(rows)
        else:
            t_this = (scene - scene.mean(axis=0)) @ axis
            # the payload rows are the stride-subsampled vertices, so the
            # macro masks subsample identically ([::stride] alignment)
            skull_sel = (t_this >= p85)[::stride]
            mid_sel = ((t_this >= p30) & (t_this < p85))[::stride]
            macro["skull"].append(rows[skull_sel])
            macro["spine_ribs"].append(rows[mid_sel])
    return {"per_bone": per_frame, "macro": macro}


# ── the three falsifier runs ────────────────────────────────────────────────

def run_a(engine: str, presentation: str, outdir: Path) -> dict:
    comp = compose(presentation)
    theta, phi = 0.6, 0.3
    lift = A_LIFT              # the fixed-pose A comparison is made with the
                               # body fully ABOVE the plane on BOTH engines:
                               # on the pre-repair engine the opaque floor
                               # hides the sub-plane half (Defect B), which
                               # would confound the splat-vs-mesh coverage
                               # comparison with the grid defect.
    pos = comp["payload"][:, 0:3].astype(np.float64).copy()
    pos[:, 1] += lift
    # the camera TARGET is the lifted body's centre: the orbit looks at the
    # body, so the closed-form height fit applies again (radius ~1.01)
    radius = fit_radius(comp)
    ctr = (comp["payload"][:, 1].min() + comp["payload"][:, 1].max()) / 2.0
    target = (0.0, lift + float(ctr), 0.0)
    ok = post_presentation(engine, comp, radius, theta, phi, lift=lift,
                           target=target)
    _require(ok, "presentation_post_refused", presentation)
    _post_json(engine, "/camera", {"cam_radius": radius, "cam_theta": theta,
                                   "cam_phi": phi,
                                   "target_x": target[0], "target_y": target[1],
                                   "target_z": target[2]})
    time.sleep(0.8)
    png = _settle_frame(engine, None)
    out = outdir / f"a_fixed_pose_{presentation}.png"
    out.write_bytes(png)
    img = pt.load(out)
    W, H = img.shape[1], img.shape[0]
    pts_px = project_points(pos, radius, theta, phi, W, H, target)
    hull = pt.hull_mask(pts_px, img.shape)
    obj = pt.warm_mask(img)
    res = {
        "presentation": presentation,
        "png": str(out),
        "camera": {"radius_m": round(radius, 4), "theta": theta, "phi": phi,
                   "lift_m": lift, "target": target},
        "grain": pt.grain(img, obj),
        "coverage": pt.coverage(obj, hull),
    }
    return res


def run_a_regions(engine: str, outdir: Path, presentation: str) -> dict:
    """Per-region coverage for ONE presentation (the operator's density
    complaint, quantified per bone and per macro region). One presentation per
    engine session: the mesh and the splat buffer are competing pose owners."""
    out = {}
    comp = compose(presentation)
    theta, phi = 0.6, 0.3
    lift = A_LIFT     # same above-the-plane law as run_a (no grid confound)
    pos = comp["payload"][:, 0:3].astype(np.float64).copy()
    pos[:, 1] += lift
    radius = fit_radius(comp)
    ctr = (comp["payload"][:, 1].min() + comp["payload"][:, 1].max()) / 2.0
    target = (0.0, lift + float(ctr), 0.0)
    ok = post_presentation(engine, comp, radius, theta, phi, lift=lift,
                           target=target)
    _require(ok, "presentation_post_refused", presentation)
    _post_json(engine, "/camera", {"cam_radius": radius, "cam_theta": theta,
                                   "cam_phi": phi,
                                   "target_x": target[0], "target_y": target[1],
                                   "target_z": target[2]})
    time.sleep(0.8)
    png = _settle_frame(engine, None)
    out_png = outdir / f"a_regions_{presentation}.png"
    out_png.write_bytes(png)
    img = pt.load(out_png)
    obj = pt.warm_mask(img)
    pos = comp["payload"][:, 0:3].astype(np.float64).copy()
    pos[:, 1] += lift
    W, H = img.shape[1], img.shape[0]
    reg = regions_along_trunk(comp, presentation)
    table = []
    for b in reg["per_bone"]:
        pts_px = project_points(pos[b["rows"]], radius, theta, phi, W, H, target)
        if len(pts_px) < 3 or np.ptp(pts_px[:, 0]) < 1 or np.ptp(pts_px[:, 1]) < 1:
            table.append({"bone": b["preview"], "coverage": None,
                          "note": "degenerate footprint (<3 pts or <1px span)"})
            continue
        hull = pt.hull_mask(pts_px, img.shape, dilate_px=1)
        if int(hull.sum()) == 0:
            table.append({"bone": b["preview"], "coverage": None,
                          "note": "footprint off-frame"})
            continue
        cov = pt.coverage(obj, hull)
        table.append({"bone": b["preview"], **cov})
    macro = {}
    for k, chunks in reg["macro"].items():
        rows = np.concatenate(chunks)
        pts_px = project_points(pos[rows], radius, theta, phi, W, H, target)
        hull = pt.hull_mask(pts_px, img.shape, dilate_px=1)
        macro[k] = (pt.coverage(obj, hull) if int(hull.sum())
                    else {"coverage": None, "note": "empty footprint"})
    covered = [t["coverage"] for t in table if t.get("coverage") is not None]
    return {
        "png": str(out_png), "per_bone": table, "macro": macro,
        "median_coverage_all_bones": (round(float(np.median(covered)), 4)
                                      if covered else None),
    }


def run_b(engine: str, presentation: str, outdir: Path) -> dict:
    """Two-sided guide evidence: object BELOW the plane seen from above, and
    object ABOVE the plane seen from below; guide lines present both sides.

    Guide presence protocol (fixed BEFORE the after-run): line ink pixels in
    the side's half-frame ROI, normalized by the above-pose ROI's own ink (the
    uncontested reference) — the grid's own-footprint presence."""
    comp = compose(presentation)
    poses = [("above_object_below", POSE_ABOVE, -MESH_LIFT),
             ("below_object_above", POSE_BELOW, +MESH_LIFT)]
    results = {}
    ref_count = None
    for name, phi, lift in poses:
        payload = comp["payload"].copy()
        payload[:, 1] += np.float32(lift)
        pos = payload[:, 0:3].astype(np.float64)
        radius = fit_radius(comp)
        ctr = (comp["payload"][:, 1].min() + comp["payload"][:, 1].max()) / 2.0
        target = (0.0, lift + float(ctr), 0.0)
        ok = post_presentation(engine, comp, radius, 0.0, phi, lift=lift)
        _require(ok, "presentation_post_refused", name)
        _post_json(engine, "/camera", {"cam_radius": radius, "cam_theta": 0.0,
                                       "cam_phi": phi,
                                       "target_x": target[0], "target_y": target[1],
                                       "target_z": target[2]})
        time.sleep(0.8)
        png = _settle_frame(engine, None)
        out_png = outdir / f"b_{name}_{presentation}.png"
        out_png.write_bytes(png)
        img = pt.load(out_png)
        W, H = img.shape[1], img.shape[0]
        # footprint of the LIFTED body from THIS camera
        pts_px = project_points(pos, radius, 0.0, phi, W, H, target)
        hull = pt.hull_mask(pts_px, img.shape)
        # guide ROI: the plane's own pixels = lower half of frame from above,
        # upper half from below (the plane fills the half-space in front).
        roi = np.zeros(img.shape[:2], bool)
        if phi > 0:
            roi[H // 2:, :] = True
        else:
            roi[:H // 2, :] = True
        if name.startswith("above"):
            g = pt.guide_seen(img, roi)
            ref_count = g["guide_pixels_in_roi"]   # the uncontested reference
        else:
            g = pt.guide_seen(img, roi, reference_count=ref_count)
        results[name] = {
            "png": str(out_png),
            "camera": {"radius_m": round(radius, 4), "phi": phi,
                       "lift_m": lift, "target": target},
            "object": pt.object_seen(img, hull, dim=True),
            "guide": g,
        }
    return results


def run_c(engine: str, presentation: str, outdir: Path) -> dict:
    comp = compose(presentation)
    theta0, phi = 0.0, CLIP_PHI
    ok = post_presentation(engine, comp, CLIP_RADIUS, theta0, phi, lift=C_LIFT)
    _require(ok, "presentation_post_refused", presentation)
    counts, touches, paths = [], [], []
    prev = None
    for i in range(ORBIT_FRAMES):
        theta = 2.0 * math.pi * i / ORBIT_FRAMES
        _post_json(engine, "/camera",
                   {"cam_radius": CLIP_RADIUS, "cam_theta": theta,
                    "cam_phi": phi, "pan_x": CLIP_PAN, "pan_y": 0.0,
                    "target_x": 0.0, "target_y": C_LIFT, "target_z": 0.0})
        b = _settle_frame(engine, prev)
        prev = b
        out_png = outdir / f"c_orbit_{presentation}_f{i:03d}.png"
        out_png.write_bytes(b)
        m = pt.warm_mask(pt.load(out_png))
        counts.append(int(m.sum()))
        touches.append(pt.boundary_touch(m))
        paths.append(str(out_png))
    return {
        "presentation": presentation,
        "radius_m": CLIP_RADIUS, "phi": phi, "pan_x": CLIP_PAN,
        "lift_m": C_LIFT, "frames": ORBIT_FRAMES,
        "scan": pt.clip_scan(counts, touches),
        "counts": counts,
        "png_dir": str(outdir),
    }


def run_d(engine: str, outdir: Path) -> dict:
    """Membrane D: full fixed-radius orbit, pivot = bbox centre (before) vs
    pivot = mass CoG (after). Per-frame silhouette area, frame bbox extents,
    and the projected geometry centroid's offset from the frame center."""
    from tools.science_funnel import ct_skeleton_triangle as cst
    results = {}
    for pivot in ("bbox", "cog"):
        layer = cst.layer_triangle_mesh(pivot=pivot)
        comp = {"payload": layer["verts9"].copy(), "tris": layer["tris"],
                "record": layer["record"]}
        # the payload ships AS the pivot law produced it (no further recenter)
        radius = fit_radius(comp)
        theta0 = phi = 0.3
        ok = post_presentation(engine, comp, radius, theta0, phi)
        _require(ok, "presentation_post_refused", pivot)
        _post_json(engine, "/camera", {"cam_radius": radius, "cam_theta": 0.0,
                                       "cam_phi": phi, "pan_x": 0.0, "pan_y": 0.0,
                                       "target_x": 0.0, "target_y": 0.0,
                                       "target_z": 0.0})
        time.sleep(0.8)
        counts, extents, cent_off = [], [], []
        prev = None
        for i in range(ORBIT_FRAMES):
            theta = 2.0 * math.pi * i / ORBIT_FRAMES
            _post_json(engine, "/camera", {"cam_radius": radius, "cam_theta": theta,
                                           "cam_phi": phi, "pan_x": 0.0, "pan_y": 0.0,
                                           "target_x": 0.0, "target_y": 0.0,
                                           "target_z": 0.0})
            b = _settle_frame(engine, prev)
            prev = b
            out_png = outdir / f"d_orbit_{pivot}_f{i:03d}.png"
            out_png.write_bytes(b)
            img = pt.load(out_png)
            m = pt.warm_mask(img)
            counts.append(int(m.sum()))
            ys, xs = np.where(m)
            extents.append([int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())]
                           if len(xs) else [0, 0, 0, 0])
            H, W = img.shape[:2]
            ppts = project_points(comp["payload"][:, 0:3].astype(np.float64),
                                  radius, theta, phi, W, H)
            cxy = ppts.mean(axis=0)
            cent_off.append(float(np.hypot(cxy[0] - W / 2, cxy[1] - H / 2)))
        arr = np.asarray(counts, dtype=np.float64)
        results[pivot] = {
            "radius_m": radius, "phi": phi, "frames": ORBIT_FRAMES,
            "area_counts": counts,
            "area_cv": round(float(arr.std() / arr.mean()), 4),
            "bbox_extents": extents,
            "centroid_offset_px_max": round(float(np.max(cent_off)), 1),
            "centroid_offset_px": [round(float(v), 1) for v in cent_off],
            "png_dir": str(outdir),
        }
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=("a", "regions", "b", "c", "d", "all"))
    ap.add_argument("--engine", default="http://localhost:8155")
    ap.add_argument("--presentation", choices=("splat", "mesh"), default="mesh")
    ap.add_argument("--outdir", type=Path, required=True)
    args = ap.parse_args(argv)
    args.outdir.mkdir(parents=True, exist_ok=True)
    out = {}
    if args.cmd in ("a", "all"):
        out["a_fixed_pose"] = run_a(args.engine, args.presentation, args.outdir)
    if args.cmd == "regions":
        out["a_regions"] = run_a_regions(args.engine, args.outdir, args.presentation)
    if args.cmd in ("b", "all"):
        out["b_two_sided"] = run_b(args.engine, args.presentation, args.outdir)
    if args.cmd in ("c", "all"):
        out["c_clip_scan"] = run_c(args.engine, args.presentation, args.outdir)
    if args.cmd == "d":
        out["d_orbit_pivot"] = run_d(args.engine, args.outdir)
    (args.outdir / f"measure_{args.cmd}_{args.presentation}.json").write_text(
        json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
