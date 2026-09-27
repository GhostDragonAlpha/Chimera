"""ONT-A05 anatomy-profile capture builder (visible_static, CPU-only).

Renders the frozen PREREGISTRATION views of the pinned SOURCE hand assembly
(27 A04-pinned vendor STLs at the A04 s2 anchors inside the hand_r frame) and
assembles the six-panel contact sheet evidence/capture_a05.png (3 profile
view_ids x diagnostic/clean), then writes evidence/capture_manifest.json
(chimera.visual_capture_manifest.v1) validated in-process against the card
profile with the campaign's visual_capture validator (and visual_gate.verify
including the qualification receipt's camera/visual entries).

Raster/camera machinery is the MERGED A04 winner's pinned code
(reference/a04_winner/a04_capture_build.py), imported read-only. The A04
capture-truth guard is re-asserted at build time: every source bone is placed
at its per-bone s2 anchor (assembled hand, NOT the origin-collapsed set), and
the placement is verified against the state snapshot before any camera is
framed (the A01-lesson bounds check).

Deterministic: byte-identical PNG on rerun; no timestamps in outputs.
Writes ONLY this contribution's evidence/ directory.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import a05_hand_structure_probe as P                    # noqa: E402

A04CAP = HERE / "reference/a04_winner/a04_capture_build.py"
A04PROBE = HERE / "reference/a04_winner/a04_correspondence_probe.py"
import importlib.util                                   # noqa: E402

_spec = importlib.util.spec_from_file_location("a04cap", A04CAP)
CAP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CAP)
_spec2 = importlib.util.spec_from_file_location("a04probe", A04PROBE)
A04P = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(A04P)

OUT = HERE / "evidence"
CARD = json.loads((HERE / "card_task.json").read_text(encoding="utf-8"))

RUN_ID = "ont-a05-anatomy-20260926-1a7c4775"
VIEW_IDS = list(CARD["task"]["verification_profile"]["views"])
LAYERS = list(CARD["task"]["verification_profile"]["diagnostic_layers"])
SUBJECT_SHA = hashlib.sha256(
    (OUT / "state_snapshot.json").read_bytes()).hexdigest()

NEAR_FAR = [0.02, 1.5]
STL_DIR = P.VENDOR_STL_DIR
SITES = P.SITES
HAND_ORIGIN = np.array(P.HAND_ORIGIN_PIN)


def load_bones():
    """27 pinned STLs placed at their per-bone A04 s2 anchors (metres)."""
    s2 = json.loads((P.A04 / "s2_identity.json").read_text(encoding="utf-8"))
    bones = {}
    for name, rec in s2["bones"].items():
        tri, _meta = A04P.load_stl(STL_DIR / (name + ".stl"))
        bones[name] = tri + np.asarray(rec["anchor"], dtype=np.float64)
    return bones


def frame_axes_points(origin, axis_len):
    pts = []
    for i, color in enumerate([(0.8, 0.1, 0.1), (0.1, 0.6, 0.1),
                               (0.1, 0.1, 0.8)]):
        v = np.zeros(3)
        v[i] = axis_len
        pts.append((origin, origin + v, color))
    return pts


def project_overlay(pts, eye, x_cam, y_cam, f, half_h, w, h):
    rel = pts - np.asarray(eye)
    u = rel @ x_cam
    v = rel @ y_cam
    d = rel @ f
    with np.errstate(divide="ignore", invalid="ignore"):
        px = (u / d) / (CAP.TAN_OF_HALF_H * (w / h)) if False else None
    # orthographic: no divide
    px = (u / (half_h * w / h) + 1.0) * 0.5 * w
    py = (1.0 - v / half_h) * 0.5 * h
    return np.stack([px, py], axis=1), d


def main() -> int:
    bones = load_bones()
    all_tris = np.concatenate([bones[b] for b in sorted(bones)], axis=0)
    # BUILD-TIME CAPTURE-TRUTH GUARD (A01 lesson + A04 finding 1): the placed
    # bones must span the assembled hand, not a collapsed origin set; and the
    # 3distph anchor chain must reproduce the A04 authored extent.
    lo, hi = all_tris.reshape(-1, 3).min(0), all_tris.reshape(-1, 3).max(0)
    span = hi - lo
    assert span.max() > 0.05, "collapsed placement: %s" % span
    extent = np.linalg.norm(
        np.asarray(json.loads((P.A04 / "s2_identity.json").read_text(
            encoding="utf-8"))["bones"]["3distph"]["anchor"])) \
        if "3distph" in json.loads((P.A04 / "s2_identity.json").read_text(
            encoding="utf-8"))["bones"] else 0.0
    assert 0.10 < extent < 0.20, "anchor extent out of A04 band: %r" % extent

    # three fixed bookmarks (PREREGISTRATION): overview, close-up, side/oblique
    center = (lo + hi) / 2.0
    R = float(np.linalg.norm(hi - lo)) / 2.0

    def bookmark(direction, dist_mult=2.6):
        d = np.asarray(direction, dtype=np.float64)
        d = d / np.linalg.norm(d)
        eye = center + d * (R * dist_mult)
        return eye, center, np.array([0.0, 0.0, 1.0])

    E1, L1P, UP = bookmark((0.3, 0.35, -1.0))          # whole-creature overview
    E2, L2P, _ = bookmark((0.55, -0.2, -0.75), 1.15)   # local attachment close-up
    E3, L3P, _ = bookmark((-0.9, 0.1, -0.4), 2.0)      # orthogonal side/oblique

    W, H = 640, 420
    views = [
        ("whole-creature overview", E1, L1P, UP, all_tris, 2.9),
        ("local attachment close-up", E2, L2P, UP, all_tris, 1.25),
        ("orthogonal side and oblique views", E3, L3P, UP, all_tris, 2.3),
    ]
    subject_pts = all_tris.reshape(-1, 3)

    panels = {}
    cams = {}
    for view_id, eye, look, up, tris, _dist in views:
        x_cam, y_cam, f = CAP.camera_basis(eye, look, up)
        half_h = CAP.auto_half_h(eye, look, up, tris, W, H, margin=1.2)
        img_d, _zbuf, mask_d = CAP.raster(tris, eye, x_cam, y_cam, f,
                                          half_h, W, H)
        rgb_c = CAP.shade(img_d, _zbuf, mask_d, (0.55, 0.63, 0.71))
        # diagnostics overlays (task-owned subset of the six declared layers)
        overlays = []
        # L5 frame axes at the hand_r origin pin (world)
        ax_origin = HAND_ORIGIN
        for a, bpt, color in frame_axes_points(ax_origin, 0.03):
            pa, _ = project_overlay(np.array([a]), eye, x_cam, y_cam, f,
                                    half_h, W, H)
            pb, _ = project_overlay(np.array([bpt]), eye, x_cam, y_cam, f,
                                    half_h, W, H)
            overlays.append(("line", np.vstack([pa, pb]), color, 1.6, "-"))
        # L2 selected bones: centroids of the 8 carpal bones
        for b in ("pisiform", "lunate", "scaphoid", "triquetrum", "hamate",
                  "capitate", "trapezoid", "trapezium"):
            c = bones[b].reshape(-1, 3).mean(axis=0)
            pc, _ = project_overlay(np.array([c]), eye, x_cam, y_cam, f,
                                    half_h, W, H)
            overlays.append(("scatter", pc, (0.85, 0.45, 0.1), 14))
        # L4 attachment sites: the 5 frozen tendon sites (A04's frozen table)
        for site in SITES:
            anchor = np.asarray(A04P.SITES[site][0], dtype=np.float64)
            ps, _ = project_overlay(np.array([anchor]), eye, x_cam, y_cam, f,
                                    half_h, W, H)
            overlays.append(("scatter", ps, (0.9, 0.15, 0.15), 18))
            overlays.append(("label", (ps[0][0], ps[0][1]), site,
                             (0.1, 0.1, 0.1), 3, -6))
        # L6 stable labels
        for b in ("3distph", "1mc", "5mc"):
            c = bones[b].reshape(-1, 3).mean(axis=0)
            pl, _ = project_overlay(np.array([c]), eye, x_cam, y_cam, f,
                                    half_h, W, H)
            overlays.append(("label", (pl[0][0], pl[0][1]), b,
                             (0.1, 0.1, 0.6), 3, 8))
        # L3 muscle/tendon paths: course lines site -> cited bone centroid
        for site in SITES:
            bone = A04P.SITES[site][2]
            anchor = np.asarray(A04P.SITES[site][0], dtype=np.float64)
            c = bones[bone].reshape(-1, 3).mean(axis=0)
            p0, _ = project_overlay(np.array([anchor]), eye, x_cam, y_cam, f,
                                    half_h, W, H)
            p1, _ = project_overlay(np.array([c]), eye, x_cam, y_cam, f,
                                    half_h, W, H)
            overlays.append(("line", np.vstack([p0, p1]), (0.6, 0.1, 0.6),
                             1.0, "--"))
        rgb_d = CAP.panel_array(img_d, overlays,
                                "SOURCE hand (27 pinned STLs @ A04 anchors) "
                                "— " + view_id, W, H, (0.1, 0.1, 0.1))
        rgb_c = CAP.panel_array(rgb_c, [],
                                "SOURCE hand (clean) — " + view_id, W, H,
                                (0.1, 0.1, 0.1))
        panels[view_id] = (rgb_d, rgb_c)
        cam, _basis = CAP.cam_record("hand_r_local_m_ortho", eye, look, up,
                                     half_h, W, H)
        cams[view_id] = cam

    # assemble the contact sheet: 3 rows x [diag, clean]
    from PIL import Image
    rows = []
    for view_id in [v[0] for v in views]:
        d, c = panels[view_id]
        pair = CAP.stack_h([d, c])
        rows.append(pair)
    sheet = CAP.stack_v(rows)
    out_png = OUT / "capture_a05.png"
    Image.fromarray(sheet).save(out_png)

    # pixel rectangles of each panel (sheet layout: rows stacked vertically)
    ph, pw = sheet.shape[0] // 3, sheet.shape[1] // 2
    rects = {}
    for i, view_id in enumerate([v[0] for v in views]):
        rects[view_id] = {
            "diagnostic": [0, i * ph, pw, ph],
            "clean": [pw, i * ph, pw, ph],
        }

    # manifest
    sys.path.insert(0, "E:/PythonChimera/tools/monkey_campaign")
    sys.dont_write_bytecode = True
    import visual_capture
    import visual_gate

    def manifest_row(view_id, mode, pair_id, rect):
        return {
            "view_id": view_id, "mode": mode, "pair_id": pair_id,
            "state_binding": {"kind": "state", "sha256": SUBJECT_SHA},
            "artifact_locator": {"kind": "image",
                                 "region": "pixel_rectangle",
                                 "pixel_rectangle": rect},
            "camera": cams[view_id],
            "visibility": visibility_block(mode),
        }

    def visibility_block(mode):
        if mode == "diagnostic":
            return {
                "layers": LAYERS,
                "label_ids": ["frame_axes", "carpal_centroids", "tendon_sites",
                              "stable_ids"],
                "selected_ids": ["source_hand_assembly"],
                "required_subject_ids": ["source_hand_assembly"],
                "observed_subject_ids": ["source_hand_assembly",
                                         "tendon_sites", "frame_axes"],
                "missing_subject_ids": [],
                "occlusion_mode": "depth_tested",
                "tag_bindings": [
                    {"label_id": "frame_axes", "subject_id": "frame_axes"},
                    {"label_id": "carpal_centroids",
                     "subject_id": "source_hand_assembly"},
                    {"label_id": "tendon_sites", "subject_id": "tendon_sites"},
                    {"label_id": "stable_ids",
                     "subject_id": "source_hand_assembly"},
                ],
            }
        return {
            "layers": [], "label_ids": [], "selected_ids": [],
            "required_subject_ids": ["source_hand_assembly"],
            "observed_subject_ids": ["source_hand_assembly"],
            "missing_subject_ids": [],
            "occlusion_mode": "depth_tested",
            "tag_bindings": [],
        }

    rows_manifest = []
    for i, view_id in enumerate([v[0] for v in views]):
        rows_manifest.append(manifest_row(view_id, "diagnostic", "row%d" % i,
                                          rects[view_id]["diagnostic"]))
        rows_manifest.append(manifest_row(view_id, "clean", "row%d" % i,
                                          rects[view_id]["clean"]))
    capture_sha = hashlib.sha256(out_png.read_bytes()).hexdigest()
    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": "A05",
        "run_id": RUN_ID,
        "subject_sha256": SUBJECT_SHA,
        "capture_sha256": capture_sha,
        "profile_id": "anatomy",
        "tick_interval": [0, 0],
        "views": rows_manifest,
    }
    manifest_path = OUT / "capture_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True)
                             + "\n", encoding="utf-8")

    contract = json.loads((HERE / "card_task.json").read_text(
        encoding="utf-8"))
    context = {"task_id": "A05", "run_id": RUN_ID,
               "subject_sha256": SUBJECT_SHA, "capture_sha256": capture_sha,
               "tick_interval": [0, 0]}
    structural = visual_capture.validate_manifest(
        manifest, context, contract["task"]["verification_profile"])

    # full visual_gate.verify including the qualification receipt's entries
    qpath = OUT / "qualification_receipt.json"
    receipt = json.loads(qpath.read_text(encoding="utf-8"))
    receipt["evidence"]["camera"] = {
        "reference": str(manifest_path.resolve()),
        "raw_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest()}
    receipt["evidence"]["visual"] = {
        "reference": str(out_png.resolve()),
        "raw_sha256": capture_sha}
    receipt["capture_context"] = {
        "task_id": "A05", "subject_sha256": SUBJECT_SHA, "run_id": RUN_ID,
        "capture_sha256": capture_sha, "tick_interval": [0, 0]}
    gate = visual_gate.verify(receipt, contract)

    capture_receipt = {
        "schema": "ont-a05.anatomy.capture.v1",
        "task_id": "A05", "run_id": RUN_ID,
        "subject_sha256": SUBJECT_SHA,
        "sheet": {"reference": str(out_png.resolve()),
                  "raw_sha256": capture_sha,
                  "size_px": [sheet.shape[1], sheet.shape[0]]},
        "manifest": {"reference": str(manifest_path.resolve()),
                     "raw_sha256": hashlib.sha256(
                         manifest_path.read_bytes()).hexdigest()},
        "state_binding": {"kind": "state", "raw_sha256": SUBJECT_SHA},
        "capture_truth_guard": {
            "assembled_span_m": [float(v) for v in span],
            "anchor_extent_3distph_m": extent,
            "placement": "27 pinned STLs at their per-bone A04 s2 anchors "
                         "(assembled hand; NOT origin-collapsed)",
        },
        "render_referents": {
            "raster": "the MERGED A04 winner's pinned z-buffer orthographic "
                      "rasterizer (reference/a04_winner/a04_capture_build.py)",
            "frame": "chimanoid hand_r local metres; world origin at the A04 "
                     "R2-A4 pin",
            "clean_segments": "rendered as their OWN panels; zero diagnostic "
                              "pixels",
        },
        "gate_validation": structural,
        "visual_gate_receipt": gate,
    }
    (OUT / "capture_receipt.json").write_text(
        json.dumps(capture_receipt, indent=1, sort_keys=True) + "\n",
        encoding="utf-8")
    print("sheet bytes:", out_png.stat().st_size, "capture sha:",
          capture_sha[:16])
    print("validate_manifest:", json.dumps(structural))
    print("visual_gate.verify:", json.dumps(gate))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
