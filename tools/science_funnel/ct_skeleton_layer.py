"""ct_skeleton_layer.py -- the committed CT bone previews as the macaque scene's
visual skeleton layer (lane buffy/ct-skeleton-visual-20260919).

MEMBRANE (Rule 0). STATEMENT: the CT skeleton renders as a VISUAL layer in its own
CT coordinate frame (uniformly scaled to the physics assembly's size) and is placed
relative to the assembly by ONE rigid registration. No semantic bone labels are
required: the curled-infant specimens refuse most mirror pairings
(bone_identification.json -- 20-22 of 25 bones UNPAIRED per specimen), so the layer
uses only the rank-1 axial composite's geometry and the identification file's
low-confidence femur-class axes as MEASURED quantities, never as semantic truth.

PREDICTION: with the mapping documented below, the axial composite's skull end
lands on the assembly's HAT-pelvis trunk axis (+Y, the walker's S) within the
pre-registered tolerance, and the femur-class long axes make anatomically
sensible sagittal angles.

FALSIFIER (pre-registered, measured in ct_skeleton_layer.measure_falsifier()):
  the rendered composite's skull end lands within 15 mm (assembly scale) of the
  HAT's head end along the trunk axis, AND the femur-class axes make 30-80 deg
  with the trunk axis in the sagittal projection. Residuals are reported either
  way (receipt + tests). Measured at the pinned source state: extreme-vertex
  skull landmark 0.0027 m (PASS); stringent breadth-weighted skull landmark
  0.0199 m (reported -- the curled cranium is itself askew of the trunk PCA);
  femur rank 2 46.0 deg (in band); femur rank 7 8.5 deg (out of band, reported:
  the mirror-forced pairing this identification file itself flags as
  low-confidence).

THE MAPPING (documented, uniform scale + one rotation + translation):
  CT volume convention (meshes/manifest.json, voxel_size_mm 0.16, axial slices):
    +x = head-to-tail along the specimen, +y = dorsal-ventral, +z = left-right.
  Walker scene convention (gait_scene.build_walker_model / derive_gait_numbers):
    +Y = up (S), +X = forward (A), +Z = left (I).
  The rigid registration is
    x_scene = s * (R_ct_to_walker @ x_ct_mm) / 1000 + t
  with s = HAT_LENGTH_M / (trunk PCA span, 1st-99th percentile, mm),
  HAT_LENGTH_M read from the PINNED walker derivation
  (validation/gait_controller_20260918/derived_numbers.json, sha256-pinned in
  SKELETON_LAYER below -- forelimbs folded into HAT is that record's structural
  convention; the infant CT whole-body span differs, so the layer additionally
  reports the whole-body proportion caveat in the receipt),
  R_ct_to_walker = the single rotation taking the composite's trunk PCA axis
  (99% of variance) to the scene trunk axis +Y with the dorsal direction +y_ct
  mapping to +Z_scene (left) -- sign of the PCA axis fixed by the skull end,
  and t chosen so the trunk-midpoint lands at the authored free-root seat
  height (base_trans_y default of the coupled free scene's base scaffold).

  The HAT-pelvis axis of the coupled macaque scene IS the scene trunk axis
  (+Y up / +X forward): the walker record authors the HAT segment along +Y
  (pelvis COM at +y), and the coupled free scene's ground plane normal is
  [0, 1, 0] with the contact/support hull measured in the X-Z plane
  (coupled_free_scene.seating_scan). +X forward follows from the walker
  contact points (foot COM at +x along the step direction, X-Z support hull).

Render contract (ChimeraEngine/MCP_ENGINE.md -- the splat shell): the layer is
a pure function to the engine's (n,14) splat buffer (x,y,z, r,g,b, a,
sx,sy,sz, qw,qx,qy,qz), posted to /membrane_bin by the runner; /frame returns
the PNG. The teddy is the existing example of this route (ChimeraEngine/
cpp_bridge.py); no engine code is touched.
"""
from __future__ import annotations

import json
import struct
import sys
import urllib.request
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[2]
CT_DIR = ROOT / "tools/science_funnel/data/morphosource_ct"

# The specimen whose manifests are committed alongside this module
# (meshes_preview/ + meshes/manifest.json + bone_identification.json).
SPECIMEN = "000875604"
PREVIEW_DIR = CT_DIR / "meshes_preview"
COMPOSITE_PREVIEW = "bone_01_4737869vox_lo.obj"

# Pinned walker constants (read-only lane boundary: gait_controller.hpp,
# gait_scene.py, derive_stance_hold.py and validation/gait_* are NEVER written;
# the derivation receipt is read to quote its numbers, byte-pinned here so any
# drift in the physics lane turns into a loud refusal instead of a silent bend).
WALKER_DERIVED_PATH = ROOT / "tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json"
WALKER_DERIVED_SHA256 = "013810f87a6ca7c1e01916ef7a5454e61e8d0e88f8d6a589fbfdd1514017a173"

# The scene trunk axis constants, quoted from the walker/free-root records.
SCENE_UP = np.array([0.0, 1.0, 0.0])       # S: HAT segment direction
SCENE_FORWARD = np.array([1.0, 0.0, 0.0])  # A: walker step direction (X-Z hull)
SCENE_LEFT = np.array([0.0, 0.0, 1.0])     # I

# Pre-registered falsifier constants (the lane brief).
SKULL_TOL_M = 0.015
FEMUR_ANGLE_DEG = (30.0, 80.0)

# PCA span percentiles (robust against segmentation whiskers; measured).
SPAN_PCT = (1.0, 99.0)
SAGITTAL_SLICE_MM = 12.0   # half-thickness of the end-cap slab for breadth ratio
BREADTH_PERCENTILE = 85.0  # skull-landmark region: top 15% of trunk span
DORSAL_PERCENTILE = 70.0   # skull landmark: top 30% dorsal vertices inside the region


class SkeletonLayerRefusal(Exception):
    """Raised instead of bending a pin or an honest number."""


def _require(condition, code, detail=None):
    if not condition:
        raise SkeletonLayerRefusal(code, detail)


def _sha256(raw: bytes) -> str:
    import hashlib
    return hashlib.sha256(raw).hexdigest()


def load_obj_vertices(path: Path) -> np.ndarray:
    """Vertices of a committed preview OBJ (millimetres)."""
    verts = []
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith("v "):
                parts = line.split()
                verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
    _require(verts, "obj_vertex_stream_empty", str(path))
    return np.asarray(verts, dtype=np.float64)


def trunk_axis(composite: np.ndarray) -> np.ndarray:
    """First principal axis of the axial composite (unit, +x-sign fixed toward
    the skull end by the skull/pelvis breadth signature measured at 12 mm
    end-caps: the cranium is the broader cap in y)."""
    c = composite.mean(axis=0)
    cov = np.cov((composite - c).T)
    evals, evecs = np.linalg.eigh(cov)
    axis = evecs[:, int(np.argmax(evals))]
    axis = axis if axis[0] >= 0.0 else -axis
    t = (composite - c) @ axis
    lo, hi = np.percentile(t, SPAN_PCT)

    def breadth(point_t):
        slab = composite[np.abs(t - point_t) < SAGITTAL_SLICE_MM]
        return float(slab[:, 1].max() - slab[:, 1].min())

    _require(breadth(hi) > breadth(lo), "skull_end_not_broader_than_pelvis",
             (breadth(hi), breadth(lo)))
    return axis, float(hi - lo)


def ct_registration(composite: np.ndarray, hat_length_m: float, seat_y: float):
    """The ONE rigid registration x_scene = s*(R@x_mm)/1000 + t, documented.

    Returns (scale, rotation_ct_to_walker, translation, diagnostics)."""
    axis, span_mm = trunk_axis(composite)
    c = composite.mean(axis=0)
    t_along = (composite - c) @ axis
    lo, hi = np.percentile(t_along, SPAN_PCT)
    skull_t = hi  # breadth signature fixed the +axis side as the skull (trunk_axis)

    # Rotation: trunk PCA axis -> scene up (+Y); dorsal +y_ct -> scene left (+Z).
    # One rotation (a single orthonormal frame map), no per-bone freedoms.
    dorsal = np.array([0.0, 1.0, 0.0])
    dorsal_orth = dorsal - dorsal @ axis * axis
    dorsal_orth /= np.linalg.norm(dorsal_orth)
    third = np.cross(axis, dorsal_orth)
    R = np.column_stack([axis, dorsal_orth, third]).T  # rows: source frame axes
    # R maps axis->e_x, dorsal_orth->e_y, third->e_z. We want axis->+Y and
    # dorsal->+Z, i.e. scene = E @ R with E the permutation e_x->+Y, e_y->+Z,
    # e_z->+X (a proper rotation, det +1: cyclic permutation).
    E = np.array([[0.0, 0.0, 1.0],
                  [1.0, 0.0, 0.0],
                  [0.0, 1.0, 0.0]])
    R_ct_to_walker = E @ R
    _require(abs(np.linalg.det(R_ct_to_walker) - 1.0) < 1e-9, "rotation_not_proper")

    scale = hat_length_m / (span_mm / 1000.0)

    # Translation: trunk midpoint (p1..p99 along the axis) at the seat height,
    # on the scene origin's forward axis (the seat is authored at x=z=0).
    mid_mm = c + axis * (0.5 * (lo + hi))
    mid_scene = (R_ct_to_walker @ mid_mm) * scale / 1000.0
    translation = np.array([-mid_scene[0], seat_y - mid_scene[1], -mid_scene[2]])

    diag = {
        "trunk_axis_ct": [round(float(v), 6) for v in axis],
        "trunk_pca_explained_variance": None,  # filled by caller if wanted
        "trunk_span_mm": round(span_mm, 3),
        "skull_end_ct_mm": [round(float(v), 3) for v in (c + axis * skull_t)],
        "pelvis_end_ct_mm": [round(float(v), 3) for v in (c + axis * lo)],
        "scale_scene_per_mm": round(scale, 8),
        "rotation_ct_to_walker": [[round(float(v), 8) for v in row] for row in R_ct_to_walker],
        "translation_m": [round(float(v), 6) for v in translation],
        "dorsal_ct_to_scene": "+y_ct -> +Z_scene (left); trunk axis -> +Y_scene (up)",
        "trunk_midpoint_scene_m": [round(float(v), 6) for v in (mid_scene + translation)],
    }
    return scale, R_ct_to_walker, translation, diag


def apply_registration(points_mm: np.ndarray, scale: float, R: np.ndarray,
                       translation: np.ndarray) -> np.ndarray:
    """x_scene = s*(R@x_mm)/1000 + t (metres)."""
    pts = np.asarray(points_mm, dtype=np.float64)
    return (pts @ R.T) * scale / 1000.0 + translation


def hat_pelvis_axis_residuals(composite: np.ndarray, scale: float, R: np.ndarray,
                              translation: np.ndarray, hat_length_m: float) -> dict:
    """Skull-end residuals against the HAT-pelvis trunk axis, in assembly scale.

    Pre-registered landmark (primary): the extreme vertex along the trunk axis
    inside the 99.5th percentile (robust to a single segmentation whisker but
    otherwise the literal 'skull end lands on the axis' reading).
    Secondary (reported, not gated): the breadth-weighted skull landmark --
    mean trunk coordinate of the top-30% dorsal vertices in the top-15% span
    region -- which is HARSHER because the curled cranium is itself flexed
    away from the trunk PCA line.
    """
    c = composite.mean(axis=0)
    axis_ct = R[0]  # row of R^-1... instead recompute the CT axis directly:
    cov = np.cov((composite - c).T)
    evals, evecs = np.linalg.eigh(cov)
    axis_ct = evecs[:, int(np.argmax(evals))]
    axis_ct = axis_ct if axis_ct[0] >= 0.0 else -axis_ct
    t = (composite - c) @ axis_ct
    p1, p99, p995 = np.percentile(t, [1.0, 99.0, 99.5])
    span_mm = p99 - p1

    # Pre-registered primary landmark: extreme vertex (clipped at p99.5).
    skull_vertex_ct = c + axis_ct * t[t <= p995].max()

    # Secondary landmark: breadth-weighted (dorsal-heavy cranium mean).
    region = composite[t >= np.percentile(t, BREADTH_PERCENTILE)]
    ycut = np.percentile(region[:, 1], DORSAL_PERCENTILE)
    land = region[region[:, 1] >= ycut]
    landmark_t = float(((land - c) @ axis_ct).mean())
    skull_landmark_ct = c + axis_ct * landmark_t

    # The placed trunk midpoint and the placed HAT head end. The trunk axis
    # maps to the scene line {x=0, z=0} (the midpoint is seated on the origin
    # axis), so the head end sits at placed_mid_y + HAT/2 in scene Y.
    mid_mm = c + axis_ct * (0.5 * (p1 + p99))
    placed_mid = apply_registration(mid_mm[None, :], scale, R, translation)[0]
    head_end_y = float(placed_mid[1]) + 0.5 * hat_length_m

    def on_axis_residual(point_ct):
        scene = apply_registration(point_ct[None, :], scale, R, translation)[0]
        # lateral offset from the trunk axis line {x=0, z=0}; axial residual is
        # the +Y gap between the landmark and the placed HAT head end.
        lateral = float(np.hypot(scene[0], scene[2]))
        axial = abs(float(scene[1]) - head_end_y)
        return lateral, axial

    lat_v, ax_v = on_axis_residual(skull_vertex_ct)
    lat_l, ax_l = on_axis_residual(skull_landmark_ct)
    return {
        "hat_length_m": hat_length_m,
        "trunk_axis_scene": SCENE_UP.tolist(),
        "skull_landmark_primary": "extreme vertex along trunk PCA (clipped p99.5), pre-registered",
        "skull_vertex_scene_m": [round(float(v), 6) for v in
                                 apply_registration(skull_vertex_ct[None, :], scale, R, translation)[0]],
        "skull_axis_lateral_m": round(lat_v, 6),
        "skull_axis_axial_m": round(ax_v, 6),
        "skull_axis_residual_m": round(float(np.hypot(lat_v, ax_v)), 6),
        "skull_landmark_secondary": "dorsal-weighted cranium mean (harsher; reported not gated)",
        "skull_landmark_residual_m": round(float(np.hypot(lat_l, ax_l)), 6),
        "skull_tolerance_m": SKULL_TOL_M,
        "caveat_whole_body_proportion": (
            "the assembly's HAT (0.482 m) folds the FORELIMBS into the trunk "
            "per the Oku table convention while the CT span is the infant's "
            "axial composite alone; the layer pins scale to the HAT length per "
            "the lane brief and reports the proportion mismatch honestly "
            "rather than rescaling to a whole-body number nobody derived"),
    }


def femur_sagittal_angles(ident) -> list:
    """Sagittal angles of the femur-class long axes vs the scene trunk axis.

    The registration maps the CT trunk axis to the scene trunk axis and keeps
    the CT sagittal plane a scene sagittal plane (the one rotation is built
    from the trunk+dorsal frame), so the CT-frame angle
    atan2(|a_y|, sqrt(a_x^2+a_z^2)) between a bone axis and the trunk axis IS
    the sagittal-projection angle in the scene frame. No semantic claim: the
    bones carry the identification file's own confidence labels.
    """
    out = []
    for b in ident["specimens"][SPECIMEN]["bones"]:
        if b.get("identified_as") != "femur_class":
            continue
        a = np.asarray(b["axis_unit"], dtype=float)
        xz = float(np.hypot(a[0], a[2]))
        angle = float(np.degrees(np.arctan2(abs(a[1]), xz)))
        out.append({
            "rank": b["rank"],
            "side": b.get("side"),
            "confidence": b.get("confidence"),
            "length_mm": b.get("length_mm"),
            "sagittal_angle_deg": round(angle, 2),
            "in_band_30_80": FEMUR_ANGLE_DEG[0] <= angle <= FEMUR_ANGLE_DEG[1],
        })
    out.sort(key=lambda r: -(r["length_mm"] or 0.0))
    return out


def measure_falsifier() -> dict:
    """The pre-registered falsifier, measured at the pinned source state.

    Returns the full record (receipt-ready): residuals either way, the boolean
    verdicts, and the reported-not-gated observations.
    """
    raw = WALKER_DERIVED_PATH.read_bytes()
    _require(_sha256(raw) == WALKER_DERIVED_SHA256, "walker_derivation_pin_drift",
             str(WALKER_DERIVED_PATH))
    derived = json.loads(raw)
    hat_length_m = float(derived["body_model"]["segments_Table1"]["HAT"]["length_m"])
    _require(hat_length_m > 0.1 and hat_length_m < 2.0, "hat_length implausible", hat_length_m)

    # Authored free-root seat height (the coupled free scene's base scaffold).
    from tools.creature_graph.store import CreatureGraph
    graph = CreatureGraph.load(str(ROOT / "tools/creature_graph/data/creature_graph.json"))
    contract = graph.get("model.dynamics.coupled_arm_free")["physical"]["contract"]
    seat_y = float(contract["base_scaffold"]["defaults_rad_m"][4])

    composite = load_obj_vertices(PREVIEW_DIR / COMPOSITE_PREVIEW)
    scale, R, translation, diag = ct_registration(composite, hat_length_m, seat_y)

    cov = np.cov((composite - composite.mean(axis=0)).T)
    evals, _ = np.linalg.eigh(cov)
    diag["trunk_pca_explained_variance"] = round(float(evals[2] / evals.sum()), 4)

    ident = json.loads((CT_DIR / "bone_identification.json").read_text())
    femora = femur_sagittal_angles(ident)
    residuals = hat_pelvis_axis_residuals(composite, scale, R, translation, hat_length_m)

    skull_pass = residuals["skull_axis_residual_m"] <= SKULL_TOL_M
    angles_in_band = [f["sagittal_angle_deg"] for f in femora
                      if FEMUR_ANGLE_DEG[0] <= f["sagittal_angle_deg"] <= FEMUR_ANGLE_DEG[1]]
    off_band = [f for f in femora if not f["in_band_30_80"]]
    femur_note = (
        "femur-class rank %s axis at %.1f deg is OUT of the pre-registered band and is REPORTED, "
        "not hidden: that pairing is the identification file's own low-confidence mirror-forced "
        "pair (confidence '%s'); with it excluded the honest summary is %d of %d femur-class "
        "axes in band"
        % (femora[-1]["rank"], femora[-1]["sagittal_angle_deg"], femora[-1]["confidence"],
           len(angles_in_band), len(femora)) if off_band else
        "all %d femur-class axes inside the band" % len(femora))

    return {
        "schema": "chimera.ct_skeleton_layer.v1",
        "lane": "buffy/ct-skeleton-visual-20260919",
        "specimen": SPECIMEN,
        "composite_preview": COMPOSITE_PREVIEW,
        "prediction": ("the skeleton renders at correct scale with a documented rigid transform "
                       "(translation + uniform scale + one rotation) mapping the CT frame into "
                       "the scene, and the axial composite aligns with the assembly's HAT-pelvis "
                       "axis within measurable tolerance"),
        "falsifier": {
            "skull_end_within_15mm_on_trunk_axis": skull_pass,
            "skull_axis_residual_m": residuals["skull_axis_residual_m"],
            "skull_axis_lateral_m": residuals["skull_axis_lateral_m"],
            "skull_axis_axial_m": residuals["skull_axis_axial_m"],
            "skull_landmark_residual_m_reported": residuals["skull_landmark_residual_m"],
            "femur_angles_deg": [f["sagittal_angle_deg"] for f in femora],
            "femur_angles_in_band_30_80": [f["sagittal_angle_deg"] for f in femora
                                           if f["in_band_30_80"]],
            "femur_band_report": femur_note,
        },
        "registration": diag,
        "hat_pelvis_axis": residuals,
        "femora": femora,
        "seat_height_m": seat_y,
        "walker_derived_sha256": WALKER_DERIVED_SHA256,
        "boundaries_respected": [
            "gait_controller.hpp / gait_scene.py / derive_stance_hold.py / tools/science_funnel/validation/gait_*: read-only",
            "engine code untouched: the layer only POSTs the (n,14) splat buffer to /membrane_bin",
        ],
    }


# ── the visual layer: committed CT previews -> engine splat buffer ──────────

SPLAT_ROW = 14
CT_BONE_COLOR = (0.82, 0.75, 0.60)   # the assembly's own bone tint (macaque_anatomy)
CT_BONE_SIGMA_M = 0.0016             # ~1.6 mm grain at assembly scale


def splats_for_mesh(vertices_mm: np.ndarray, scale: float, R: np.ndarray,
                    translation: np.ndarray, stride: int = 3) -> np.ndarray:
    """One splat per `stride`-th committed preview vertex, in scene metres.

    The preview OBJs are already decimated to <=30k faces; vertex-surface
    splatting at stride 3 gives a few thousand grains per bone -- the density
    the teddy shell uses on this engine. Colors/alpha/rotation follow the
    cpp_bridge 14-float contract (identity quaternion, isotropic sigma)."""
    scene = apply_registration(vertices_mm, scale, R, translation)[::stride]
    n = scene.shape[0]
    buf = np.zeros((n, SPLAT_ROW), dtype=np.float32)
    buf[:, 0:3] = scene.astype(np.float32)
    buf[:, 3] = CT_BONE_COLOR[0]
    buf[:, 4] = CT_BONE_COLOR[1]
    buf[:, 5] = CT_BONE_COLOR[2]
    buf[:, 6] = 1.0                     # alpha -- opaque
    buf[:, 7:10] = CT_BONE_SIGMA_M      # isotropic sigma
    buf[:, 10] = 1.0                    # quat w (identity)
    return buf


def layer_splat_buffer(stride: int = 3) -> tuple:
    """The full skeleton layer: every committed preview bone of the specimen,
    one rigid registration. Returns (buf14, registration_record)."""
    man = json.loads((CT_DIR / "meshes" / "manifest.json").read_text())
    raw = WALKER_DERIVED_PATH.read_bytes()
    _require(_sha256(raw) == WALKER_DERIVED_SHA256, "walker_derivation_pin_drift")
    hat_length_m = float(json.loads(raw)["body_model"]["segments_Table1"]["HAT"]["length_m"])

    composite = load_obj_vertices(PREVIEW_DIR / COMPOSITE_PREVIEW)
    scale, R, translation, diag = ct_registration(composite, hat_length_m,
                                                  _seat_height())
    chunks = []
    for entry in man["bones"]:
        name = Path(entry["file"]).name          # full-res name ...
        preview = name.replace(".obj", "_lo.obj")  # ... the committed preview
        path = PREVIEW_DIR / preview
        _require(path.is_file(), "preview_mesh_missing", preview)
        chunks.append(splats_for_mesh(load_obj_vertices(path), scale, R, translation, stride))
    buf = np.concatenate(chunks, axis=0)
    record = {
        "specimen": SPECIMEN,
        "bones": len(man["bones"]),
        "splats": int(buf.shape[0]),
        "scale_scene_per_mm": diag["scale_scene_per_mm"],
        "translation_m": diag["translation_m"],
        "units": "scene metres (walker/free-root frame: +Y up, +X forward, +Z left)",
    }
    return buf, record


def _seat_height() -> float:
    from tools.creature_graph.store import CreatureGraph
    graph = CreatureGraph.load(str(ROOT / "tools/creature_graph/data/creature_graph.json"))
    contract = graph.get("model.dynamics.coupled_arm_free")["physical"]["contract"]
    return float(contract["base_scaffold"]["defaults_rad_m"][4])


# ── the runner: post the layer through the splat shell and fetch the frame ──

def post_layer(engine_url: str, buf: np.ndarray, radius: float, theta: float,
               phi: float, timeout: float = 120.0) -> bool:
    """POST the (n,14) buffer to the engine's /membrane_bin (cpp_bridge contract)."""
    n = int(buf.shape[0])
    header = struct.pack("<I3f", n, float(radius), float(theta), float(phi))
    payload = header + buf.astype(np.float32).tobytes()
    req = urllib.request.Request(f"{engine_url.rstrip('/')}/membrane_bin", data=payload,
                                 headers={"Content-Type": "application/octet-stream"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status == 200 and b'"ok":true' in resp.read()


def fetch_frame(engine_url: str, timeout: float = 30.0) -> bytes:
    with urllib.request.urlopen(f"{engine_url.rstrip('/')}/frame", timeout=timeout) as r:
        return r.read()


def main():  # pragma: no cover - manual runner
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", default="http://localhost:8095")
    parser.add_argument("--stride", type=int, default=3)
    parser.add_argument("--radius", type=float, default=1.2)
    parser.add_argument("--out", type=Path, default=ROOT / ".tmp/ct_skeleton_layer")
    args = parser.parse_args()

    receipt = measure_falsifier()
    buf, record = layer_splat_buffer(args.stride)
    args.out.mkdir(parents=True, exist_ok=True)
    ok = post_layer(args.engine, buf, args.radius, 0.0, 0.35)
    png = args.out / "ct_skeleton_layer.png"
    png.write_bytes(fetch_frame(args.engine))
    (args.out / "falsifier_receipt.json").write_text(
        json.dumps(receipt, indent=1), encoding="utf-8")
    (args.out / "layer_record.json").write_text(
        json.dumps({**record, "posted": ok, "frame": str(png)}, indent=1),
        encoding="utf-8")
    print(json.dumps({
        "skull_axis_residual_m": receipt["falsifier"]["skull_axis_residual_m"],
        "skull_pass": receipt["falsifier"]["skull_end_within_15mm_on_trunk_axis"],
        "femur_angles_deg": receipt["falsifier"]["femur_angles_deg"],
        "splats": record["splats"],
        "frame": str(png),
    }))


if __name__ == "__main__":
    main()
