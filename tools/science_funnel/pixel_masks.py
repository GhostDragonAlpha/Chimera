"""pixel_masks.py -- the MASK LIBRARY for pixel_truth's coverage metric
(lane agent/pixel-masks-20260920).

THE GAP (operator-visible): pixel_truth.coverage divides object pixels by a
PROJECTED-FOOTPRINT mask, and for the CT skeleton renders nobody could generate
that mask outside measure_triangle_monkey.run_a_regions -- the per-bone hulls
that banked the triangle_monkey_20260920 numbers were built ad hoc inside that
one lane script, never saved, never loadable. Per-bone coverage verification of
any other frame set was manual. This module makes the masks first-class:
per-bone + macro-region screen-space masks for the CT skeleton renders,
generated OFFLINE and deterministically (no engine, no model), storable as
PNGs, loadable, and scored by pixel_truth's unchanged metric through the
`masks` CLI subcommand (one call -> the per-bone/per-region coverage table).

THE ROUTE (pre-declared in the Rule-0 receipt BEFORE any mask was generated --
tools/science_funnel/validation/pixel_masks_20260920/receipt.json):

  ANALYTIC VERTEX-CLOUD PROJECTION. Each bone's mask is the convex hull of its
  OWN committed preview vertices (the exact payload rows the lane posted),
  projected through the replicated engine camera law
  (measure_triangle_monkey.project_points: 45 deg y-FOV, Y-negated Vulkan NDC,
  orbit camera), rasterized by pixel_truth.hull_mask (dilate_px=1; macro
  regions as ONE hull over their concatenated rows). This is the precise
  generator of the banked denominators -- which is exactly why it, and not the
  two alternatives named in the brief, reproduces them:

  * OBB-corner projection (project the manifest bbox box) is MEASURED in the
    receipt's route_justification and REJECTED: a box over-covers any curved
    bone (the composite bone_01 is a curled skull+spine+rib cage), so its
    denominator is not the banked denominator. Recorded numbers, not taste.
  * render-each-bone-alone-and-threshold needs a live engine (25 extra renders
    per pose), inherits anti-aliasing/shading dependence, and is the WRONG
    denominator in principle: the banked metric divides by the projected
    VERTEX-FOOTPRINT hull, not by a solo-bone rasterization.

DETERMINISM: every input is committed (meshes_preview OBJs, manifest.json, the
sha256-pinned walker derivation, the creature graph's seat height) and every
step is fixed-order float arithmetic or a deterministic rasterization; the
generation is byte-reproducible (FALSIFIER_2 in the receipt). The camera for a
frame set comes from an explicit camera JSON, the recorded pose-A law
(theta 0.6, phi 0.3, lift A_LIFT, fit_radius -- the lane's own derivation), or
per-frame overrides.

CLI (wired through pixel_truth.py's `masks` subcommand):
  python -B tools/science_funnel/pixel_truth.py masks FRAME_DIR --glob "a_regions_mesh.png" \
      --presentation mesh --outdir tools/science_funnel/validation/pixel_masks_20260920/masks
  # -> generates mask PNGs + masks_manifest.json AND prints the per-bone /
  #    per-region coverage table for every matched frame, one call.
  # Add --load to reuse previously generated masks (no regeneration).
  # Add --route obb to run the measured-and-rejected OBB-corner route (study).
  # Add --width W --height H [--resample {nearest,bilinear,lanczos}] when the
  # committed frames are downscales of the render viewport (see the receipt).
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.science_funnel import pixel_truth as pt
from tools.science_funnel import ct_skeleton_layer as CSL
from tools.science_funnel import measure_triangle_monkey as MTM

MANIFEST_NAME = "masks_manifest.json"


def _require(condition, code, detail=None):
    if not condition:
        raise ValueError(f"pixel_masks refusal: {code} {detail or ''}")


# ── the skeleton geometry (the lane's own compose + region law, REUSED verbatim) ──

_SKEL_CACHE: dict = {}


def skeleton(presentation: str) -> dict:
    """The registered skeleton as the lane's `compose(presentation)` payload
    (bit-identical: this CALLS compose -- the same float32 casts and recentring
    -- it does not reimplement it), plus the per-bone row table and the
    skull/spine_ribs/limbs macro regions from the lane's own
    regions_along_trunk (the committed manifest's bone order + the composite's
    trunk-axis bands). Memoized: the payload is a pure function of committed
    inputs, so the cache cannot change any number."""
    _require(presentation in ("mesh", "splat"), "unknown_presentation", presentation)
    if presentation not in _SKEL_CACHE:
        comp = MTM.compose(presentation)
        reg = MTM.regions_along_trunk(comp, presentation)
        bones = [{"bone": b["preview"], "rows": b["rows"]} for b in reg["per_bone"]]
        _SKEL_CACHE[presentation] = {
            "pos": comp["payload"][:, 0:3].astype(np.float64),
            "bones": bones,
            "macro": {k: np.concatenate(v) for k, v in reg["macro"].items()},
            "camera_a": pose_a_camera(comp),
            "record": comp.get("record", {}),
        }
    return _SKEL_CACHE[presentation]


def pose_a_camera(comp: dict) -> dict:
    """The lane's recorded fixed-pose-A camera, derived the same way run_a /
    run_a_regions derive it (fit_radius on the payload; target at the body
    centre). Reproducing the banked stills starts from the lane's own law."""
    radius = MTM.fit_radius(comp)
    ctr = (comp["payload"][:, 1].min() + comp["payload"][:, 1].max()) / 2.0
    return {
        "radius": float(radius),
        "theta": 0.6,
        "phi": 0.3,
        "lift": MTM.A_LIFT,
        "target": [0.0, MTM.A_LIFT + float(ctr), 0.0],
        "law": "pose_a (measure_triangle_monkey: theta 0.6, phi 0.3, lift A_LIFT, fit_radius)",
    }


# ── mask generation ──────────────────────────────────────────────────────────

def _project(pos: np.ndarray, cam: dict, width: int, height: int) -> np.ndarray:
    """Scene metres -> pixel coordinates at THIS camera (the engine camera law,
    measure_triangle_monkey.project_points, reused verbatim)."""
    return MTM.project_points(
        pos, float(cam["radius"]), float(cam["theta"]), float(cam["phi"]),
        width, height, target=tuple(cam.get("target", (0.0, 0.0, 0.0))))


def masks_for_frame(shape: tuple, camera: dict, skel: dict,
                    dilate_px: int = 1, route: str = "vertices") -> dict:
    """Per-bone + macro-region bool masks for ONE frame's camera.

    route "vertices": hull of the bone's own projected payload rows -- the
    banked route. route "obb": hull of the projected registered manifest-bbox
    corners (the MEASURED-and-rejected alternative; receipt route_justification).

    Returns {"bones": [{"bone", "mask" (bool array or None), "note"}],
             "regions": {name: mask}}."""
    _require(route in ("vertices", "obb"), "unknown_route", route)
    H, W = int(shape[0]), int(shape[1])
    pos = skel["pos"].copy()
    pos[:, 1] += float(camera.get("lift", 0.0))
    obb_pts = None
    if route == "obb":
        obb_pts = obb_corners_scene(skel)
        for v in obb_pts.values():
            v[:, 1] += float(camera.get("lift", 0.0))   # same lift the rows see
    out_bones, regions = [], {}
    for b in skel["bones"]:
        rows = b["rows"]
        if route == "vertices":
            pts = _project(pos[rows], camera, W, H)
            if len(pts) < 3 or np.ptp(pts[:, 0]) < 1 or np.ptp(pts[:, 1]) < 1:
                out_bones.append({"bone": b["bone"], "mask": None,
                                  "note": "degenerate footprint (<3 pts or <1px span)"})
                continue
        else:
            pts = _project(obb_pts[b["bone"]], camera, W, H)
        mask = pt.hull_mask(pts, (H, W), dilate_px=dilate_px)
        if not int(mask.sum()):
            out_bones.append({"bone": b["bone"], "mask": None,
                              "note": "footprint off-frame"})
            continue
        out_bones.append({"bone": b["bone"], "mask": mask, "note": None})
    for name, rows in skel["macro"].items():
        pts = _project(pos[rows], camera, W, H)
        mask = pt.hull_mask(pts, (H, W), dilate_px=dilate_px)
        regions[name] = mask if int(mask.sum()) else None
    return {"bones": out_bones, "regions": regions}


_OBB_CACHE: list = []


def obb_corners_scene(skel: dict) -> dict:
    """The manifest bbox's 8 corners per bone, registered to scene metres and
    framed by the SAME skeleton recentre the payload sees (the camera is held
    at the recorded pose, so the route study isolates ONE variable: the hull
    source). ONE registration for all bones (the manifest's own order)."""
    key = id(skel)
    if _OBB_CACHE and _OBB_CACHE[0] == key:
        return _OBB_CACHE[1]
    man = json.loads((CSL.CT_DIR / "meshes" / "manifest.json").read_text())
    raw = CSL.WALKER_DERIVED_PATH.read_bytes()
    CSL._require(CSL._sha256(raw) == CSL.WALKER_DERIVED_SHA256,
                 "walker_derivation_pin_drift")
    hat = float(json.loads(raw)["body_model"]["segments_Table1"]["HAT"]["length_m"])
    composite = CSL.load_obj_vertices(CSL.PREVIEW_DIR / CSL.COMPOSITE_PREVIEW)
    scale, R, translation, _ = CSL.ct_registration(composite, hat, CSL._seat_height())
    ctr = (skel["pos"].min(axis=0) + skel["pos"].max(axis=0)) / 2.0
    by_name = {Path(e["file"]).name.replace(".obj", "_lo.obj"): e for e in man["bones"]}
    out = {}
    for b in skel["bones"]:
        entry = by_name[b["bone"]]
        lo = np.asarray(entry["bbox_min_mm"], dtype=np.float64)
        hi = np.asarray(entry["bbox_max_mm"], dtype=np.float64)
        corners_mm = np.array([[x, y, z] for x in (lo[0], hi[0])
                               for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        scene = CSL.apply_registration(corners_mm, scale, R, translation)
        out[b["bone"]] = scene - ctr
    _OBB_CACHE.clear()
    _OBB_CACHE.extend([key, out])
    return out


# ── save / load (the masks become artifacts, not lane-internal state) ────────

def _mask_name(stem: str, kind: str, name: str) -> str:
    return f"{stem}__{kind}__{name}.png"


def save_masks(masks: dict, outdir: Path, stem: str, camera: dict,
               presentation: str, route: str, dilate_px: int) -> dict:
    """Write each mask as an 8-bit 0/255 PNG (Pillow's PNG writer is
    deterministic: no timestamps) + the manifest entry."""
    outdir.mkdir(parents=True, exist_ok=True)
    files = {}
    for b in masks["bones"]:
        if b["mask"] is None:
            continue
        fname = _mask_name(stem, "bone", Path(b["bone"]).stem)
        Image.fromarray(b["mask"].astype(np.uint8) * 255, mode="L").save(outdir / fname)
        files[f"bone:{b['bone']}"] = fname
    for name, mask in masks["regions"].items():
        if mask is None:
            continue
        fname = _mask_name(stem, "region", name)
        Image.fromarray(mask.astype(np.uint8) * 255, mode="L").save(outdir / fname)
        files[f"region:{name}"] = fname
    any_mask = next((b["mask"] for b in masks["bones"] if b["mask"] is not None), None)
    shape = [int(any_mask.shape[0]), int(any_mask.shape[1])] if any_mask is not None else [0, 0]
    return {"stem": stem, "camera": camera, "presentation": presentation,
            "route": route, "dilate_px": dilate_px, "shape": shape,
            "files": files,
            "sha256": {fname: sha256_file(outdir / fname)
                       for fname in files.values()}}


def load_masks(outdir: Path, stem: str) -> dict:
    """Reload a previously generated mask set (0/255 PNG -> bool)."""
    manifest_path = outdir / MANIFEST_NAME
    _require(manifest_path.is_file(), "masks_manifest_missing", str(manifest_path))
    man = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = next((e for e in man["masks"] if e["stem"] == stem), None)
    _require(entry is not None, "mask_set_missing_for_stem", stem)
    bones, regions = [], {}
    for key, fname in entry["files"].items():
        mask = np.asarray(Image.open(outdir / fname)) > 0
        kind, name = key.split(":", 1)
        if kind == "bone":
            bones.append({"bone": name, "mask": mask, "note": None})
        else:
            regions[name] = mask
    return {"bones": bones, "regions": regions,
            "camera": entry["camera"], "route": entry["route"]}


def write_manifest(outdir: Path, entries: list):
    (outdir / MANIFEST_NAME).write_text(
        json.dumps({"schema": "chimera.pixel_masks.v1", "masks": entries},
                   indent=1) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ── the coverage table (pixel_truth's UNCHANGED metric, mask-driven) ─────────

def coverage_table(img: np.ndarray, masks: dict) -> dict:
    """Per-bone + macro-region coverage of ONE frame: pixel_truth.warm_mask and
    pixel_truth.coverage, exactly the banked lane's calls -- only the masks are
    now first-class, loadable artifacts."""
    obj = pt.warm_mask(img)
    table = []
    for b in masks["bones"]:
        if b["mask"] is None:
            table.append({"bone": b["bone"], "coverage": None, "note": b["note"]})
            continue
        table.append({"bone": b["bone"], **pt.coverage(obj, b["mask"])})
    macro = {}
    for name, mask in masks["regions"].items():
        macro[name] = (pt.coverage(obj, mask) if mask is not None
                       else {"coverage": None, "note": "empty footprint"})
    covered = [t["coverage"] for t in table if t.get("coverage") is not None]
    return {
        "per_bone": table,
        "macro": macro,
        "median_coverage_all_bones": (round(float(np.median(covered)), 4)
                                      if covered else None),
        "bones_at_zero": int(sum(1 for t in table if t.get("coverage") == 0.0)),
    }


# ── the one-call driver (pixel_truth.py `masks` subcommand) ──────────────────

_RESAMPLE = {"nearest": Image.NEAREST, "bilinear": Image.BILINEAR,
             "lanczos": Image.LANCZOS, "none": None}


def _resolve_camera(fname: str, camera_json: dict | None, skel: dict) -> dict:
    if camera_json:
        frames = camera_json.get("frames", {})
        if fname in frames:
            return dict(frames[fname])
        for pat, cam in frames.items():
            if fnmatch.fnmatch(fname, pat):
                return dict(cam)
        if "default" in camera_json:
            return dict(camera_json["default"])
    return dict(skel["camera_a"])


def run_masks(frame_dir: Path, glob: str, presentation: str = "mesh",
              camera_json_path: str | None = None, outdir: Path | None = None,
              load: bool = False, route: str = "vertices",
              dilate_px: int = 1, width: int | None = None,
              height: int | None = None, resample: str = "nearest") -> dict:
    """Generate-or-load masks for every frame matching `glob` and emit the
    per-bone/per-region coverage table for each -- ONE call.

    width/height: the VIEWPORT the masks are built at (the engine's client
    rectangle). Default: the frame's own pixel size. When the committed frames
    are DOWNSCALES of the render viewport (the triangle_monkey_20260920 stills
    are 960x513 downscales of the lane's 2560x1369 client rectangle -- measured
    by exact hull-area identity in the receipt), pass the viewport and the
    frames are carried up to it: `resample` picks the carrier (nearest carries
    the committed pixel VALUES with no invented colors; bilinear/lanczos
    interpolate). The warm-mask numerator keeps the downscale's information
    loss either way -- quantified in the receipt; the hull denominators are
    viewport-exact regardless."""
    frames = sorted(Path(frame_dir).glob(glob))
    _require(frames, "no_frames_matched", f"{frame_dir} / {glob}")
    camera_json = None
    if camera_json_path:
        camera_json = json.loads(Path(camera_json_path).read_text(encoding="utf-8"))
    skel = skeleton(presentation)
    entries = []
    if outdir is not None:
        man_path = Path(outdir) / MANIFEST_NAME
        if man_path.is_file():   # merge with (or reuse) what the outdir holds
            entries = json.loads(man_path.read_text(encoding="utf-8"))["masks"]
    if load:
        _require(outdir is not None, "load_needs_outdir")
        man_path = Path(outdir) / MANIFEST_NAME
        _require(man_path.is_file(), "masks_manifest_missing", str(man_path))
        _require(entries, "masks_manifest_missing", str(man_path))
    results = {}
    saved_sha = {}
    for f in frames:
        stem = f.stem
        camera = _resolve_camera(f.name, camera_json, skel)
        img = pt.load(f)
        shape = (height, width) if (width and height) else img.shape[:2]
        if (width and height) and tuple(img.shape[:2]) != (height, width):
            carrier = _RESAMPLE.get(resample)
            _require(carrier is not None, "unknown_resample", resample)
            img = np.asarray(Image.fromarray(img).resize((width, height), carrier))
        if load:
            masks = load_masks(Path(outdir), stem)
            route_used = masks.get("route", route)
        else:
            masks = masks_for_frame(shape, camera, skel,
                                    dilate_px=dilate_px, route=route)
            route_used = route
            if outdir is not None:
                entry = save_masks(masks, Path(outdir), stem, camera,
                                   presentation, route, dilate_px)
                saved_sha[f.name] = entry["sha256"]
                entries = [e for e in entries if e["stem"] != stem] + [entry]
        table = coverage_table(img, masks)
        table["png"] = str(f)
        table["camera"] = camera
        table["route"] = route_used
        table["viewport"] = [int(shape[1]), int(shape[0])]
        results[f.name] = table
    if outdir is not None and not load:
        write_manifest(Path(outdir), entries)
    return {
        "presentation": presentation,
        "route": route,
        "frames": results,
        "masks_sha256": saved_sha,
        "outdir": str(outdir) if outdir else None,
        "loaded": bool(load),
    }
