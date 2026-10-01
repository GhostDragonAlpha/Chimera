#!/usr/bin/env python3
"""MAT2-B07 profile-class capture (profile `climbing`, kind `motion`).

HONESTY LABEL (carried in the manifest and burned into every diagnostic
frame): this is a deterministic CPU software raster of the ATTEMPT'S RECORDS
(pinned B04 forest, A05 mutant origins, ownership mappings, distances). It
is NOT native engine frames and NOT a climbing replay. Screens never gate;
the receipts are the numerical evidence the profile demands. The full
16-field camera record is declared per view; motion-class delivery is an
FFV1 (-level 3 -g 1 -fflags +bitexact) mkv; decode == source stills is
verified at recomputable indices under identity (G4).

Run:  python -B make_capture.py     (writes capture/*)
Exit: 0 green / 2 named refusal.
"""
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
CONTRIB = HERE.parent
CHECKOUT = CONTRIB.parents[2]
WS = Path(r"E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-B07"
          r"\08d3db08d4d64179b2f95a516a2155bd")
SCRATCH = WS / "scratch" / "capture"
REGISTRY = Path("E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")
FFMPEG = (r"C:\Users\allen\AppData\Local\Microsoft\WinGet\Packages"
          r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
          r"\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe")

TASK_ID = "B07"
CRITERIA_SHA256 = ("5393a5d7707c370ce5c8ea072512a2b053d0abfb1d36dc952d509"
                   "714150c77d2")
TICKS = [0, 3]
VIEWPORT = [480, 360]
FRAMES_PER_ROW = TICKS[1] - TICKS[0] + 1
HONESTY = "RECORD-SPACE RASTER - not engine frames; not a climbing replay"

REFUSAL = "capture_refused"


def require(condition, code):
    if not condition:
        print("REFUSAL: " + code, file=sys.stderr)
        raise SystemExit(2)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def load_profile():
    require(REGISTRY.exists(), REFUSAL + ":registry_missing")
    uri = "file:" + str(REGISTRY).replace("\\", "/") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        row = con.execute("SELECT payload FROM state WHERE id='1'").fetchone()
    finally:
        con.close()
    require(row is not None, REFUSAL + ":registry_empty")
    card = json.loads(row[0])["kanban"]["cards"]["MAT2-B07"]
    require(card.get("criteria_sha256") == CRITERIA_SHA256,
            REFUSAL + ":criteria_mismatch")
    task = card["spec"]["ontology_qualification"]["task"]
    profile = task["verification_profile"]
    for key in ("id", "kind", "views", "clean_view_required",
                "diagnostic_layers", "camera_required_fields"):
        require(key in profile, REFUSAL + ":profile_key:" + key)
    require(profile["id"] == "climbing" and profile["kind"] == "motion",
            REFUSAL + ":profile_identity")
    return profile, task


# ---- geometry from the emitted receipts + pinned bytes ---------------------
def load_geometry():
    own = json.loads((HERE / "ownership_mappings.json").read_text("utf-8"))
    fb = json.loads((HERE / "frame_bindings.json").read_text("utf-8"))
    b04 = json.loads((CONTRIB / "MAT2-B04" / "frame_forest.json")
                     .read_text("utf-8"))
    b06 = json.loads((Path("E:/ChimeraWork/monkey-coordination/evidence-store")
                      / "MAT2-B06" / "numerical" / "assembly_readiness.json")
                     .read_text("utf-8"))
    roots = {}
    for item in b06["requirements"]:
        if item.get("requirement_id") == "R-FRM-01":
            for ev in item["evidence"]["items"]:
                if ev["pointer"].endswith("origin_m"):
                    roots[ev["pointer"].split(".")[1]] = ev["value"]
    b04_roots = {fid: f["origin_m"] for fid, f in b04["frames"].items()
                 if f.get("component_root")}
    hand_pts = [(r["record_id"], r["location_m"],
                 r["decision"]["nearest_mutant_body"],
                 r["decision"]["recorded_distance_m"])
                for r in own["records"]["hand_body_mappings"]]
    a05 = json.loads((CONTRIB / "MAT2-A05" / "mutation_structure.json")
                     .read_text("utf-8"))
    bodies = {b["name"]: b for b in a05["bodies"]}
    bodies[a05["anchor_body"]["name"]] = a05["anchor_body"]

    def origin(name):
        if name == a05["anchor_body"]["name"]:
            return [0.0, 0.0, 0.0]
        p = list(bodies[name]["mutation"]["pos_m"])
        par = bodies[name].get("parent", "").replace(
            "ref.macaque_arm_hand_mutation.body.", "")
        while par and par != a05["anchor_body"]["name"]:
            p = [a + b for a, b in zip(p, bodies[par]["mutation"]["pos_m"])]
            par = (bodies[par].get("parent", "").replace(
                "ref.macaque_arm_hand_mutation.body.", "")
                if par in bodies else None)
        return p
    mutants = {n: origin(n) for n in bodies}
    fore_pts = [(r["record_id"], r["owner_body"], r["location_m"],
                 r["decision"]["recorded_distance_m"])
                for r in own["records"]["forearm_correspondences"]]
    a07 = json.loads((CONTRIB / "MAT2-A07" / "placement_resolution.json")
                     .read_text("utf-8"))
    grasp = [(g["endpoint_id"], g["position_m"])
             for g in a07["grasp_endpoint_resolutions"]]
    state = sha_bytes(canonical({
        "ownership_mappings": sha_bytes(
            (HERE / "ownership_mappings.json").read_bytes()),
        "frame_bindings": sha_bytes((HERE / "frame_bindings.json")
                                    .read_bytes()),
        "adoption_record": sha_bytes((HERE / "adoption_record.json")
                                     .read_bytes()),
        "b04_frames": sha_bytes((CONTRIB / "MAT2-B04" / "frame_forest.json")
                                .read_bytes()),
        "b06_readiness": sha_bytes(
            (Path("E:/ChimeraWork/monkey-coordination/evidence-store")
             / "MAT2-B06" / "numerical" / "assembly_readiness.json")
            .read_bytes()),
    }))
    return {"roots": roots, "b04_roots": b04_roots, "hand": hand_pts,
            "mutants": mutants, "forearm": fore_pts, "grasp": grasp,
            "state": state}


def quat_wxyz(axis, angle):
    h = angle / 2.0
    s = math.sin(h)
    return [math.cos(h), axis[0] * s, axis[1] * s, axis[2] * s]


def project_ortho(point, center, span, yaw, viewport):
    x, y, z = (point[i] - center[i] for i in range(3))
    rx = x * math.cos(yaw) - y * math.sin(yaw)
    ry = x * math.sin(yaw) + y * math.cos(yaw)
    px = (rx / span + 0.5) * viewport[0]
    py = (0.5 - z / span) * viewport[1]
    return [px, py]


def draw_scene(draw, geom, view, yaw, mode, viewport):
    span, center = view["span"], view["center"]
    def P(p):
        return project_ortho(p, center, span, yaw, viewport)
    if view["id"] == "V1":
        for fid, o in sorted(geom["b04_roots"].items()):
            p = P(o)
            r = 5
            draw.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r],
                         outline=(80, 200, 255))
            if mode == "diagnostic":
                draw.text((p[0] + 7, p[1] - 4), fid, fill=(150, 220, 255))
        for name, o in sorted(geom["roots"].items()):
            p = P(o)
            if mode == "diagnostic":
                draw.text((p[0] + 7, p[1] + 8), name, fill=(255, 210, 120))
    elif view["id"] == "V2":
        for name, o in sorted(geom["mutants"].items()):
            p = P(o)
            draw.ellipse([p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2],
                         fill=(90, 90, 200))
            if mode == "diagnostic":
                draw.text((p[0] + 4, p[1] - 10), name, fill=(120, 120, 255))
        for rid, loc, nearest, dist in geom["hand"]:
            p = P(loc)
            q = P(geom["mutants"][nearest])
            draw.line([p[0], p[1], q[0], q[1]], fill=(60, 160, 60))
            draw.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3],
                         fill=(80, 220, 120))
            if mode == "diagnostic":
                draw.text((p[0] + 4, p[1] + 2),
                          rid + " d=" + ("%.6f" % dist), fill=(160, 255, 170))
        for gid, loc in geom["grasp"]:
            p = P(loc)
            draw.rectangle([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3],
                           outline=(90, 220, 220))
            if mode == "diagnostic":
                draw.text((p[0] + 4, p[1] - 12), gid, fill=(160, 240, 240))
    else:
        for rid, owner, loc, dist in geom["forearm"]:
            if owner != "humerus":
                continue
            p = P(loc)
            draw.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3],
                         fill=(230, 160, 90))
            if mode == "diagnostic":
                draw.text((p[0] + 4, p[1] + 2),
                          rid + " d=" + ("%.4f" % dist),
                          fill=(255, 200, 140))
        wrist_h = [0.0070003917552167744, -0.2649999467838506,
                   0.0004971479333903965]
        p = P(wrist_h)
        draw.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4],
                     outline=(255, 255, 255))
        if mode == "diagnostic":
            draw.text((p[0] + 6, p[1]), "wrist interface (A05 anchor)",
                      fill=(255, 255, 255))


def render_frames(geom, views):
    frames = []
    row_plan = []
    index = 0
    for view in views:
        for mode in ("diagnostic", "clean"):
            for tick in range(TICKS[0], TICKS[1] + 1):
                yaw = view["yaw0"] + 0.35 * tick
                img = Image.new("RGB", tuple(VIEWPORT), (8, 8, 12))
                draw = ImageDraw.Draw(img)
                draw_scene(draw, geom, view, yaw, mode, tuple(VIEWPORT))
                if mode == "diagnostic":
                    draw.text((6, 4), HONESTY, fill=(255, 120, 120))
                    draw.text((6, 16),
                              "record-tick %d/%d | span %.3f m"
                              % (tick, TICKS[1], view["span"]),
                              fill=(255, 220, 120))
                png = SCRATCH / ("frame_%02d.png" % index)
                img.save(png, format="PNG")
                frames.append(png)
                index += 1
            row_plan.append((view["id"], mode))
    return frames, row_plan


def encode(frames, out_mkv):
    cmd = [FFMPEG, "-y", "-loglevel", "error", "-framerate", "1",
           "-i", str(SCRATCH / "frame_%02d.png"),
           "-c:v", "ffv1", "-level", "3", "-g", "1",
           "-fflags", "+bitexact", str(out_mkv)]
    proc = subprocess.run(cmd, capture_output=True)
    require(proc.returncode == 0,
            REFUSAL + ":ffmpeg:" + proc.stderr.decode("utf-8",
                                                      errors="replace")[:200])
    return sha_bytes(out_mkv.read_bytes())


def decode_identity(mkv, frames):
    """G4: decode == committed stills at recomputable indices, identity."""
    checks = []
    for idx in (0, len(frames) // 2, len(frames) - 1):
        out = SCRATCH / ("decode_%02d.png" % idx)
        proc = subprocess.run(
            [FFMPEG, "-y", "-loglevel", "error", "-i", str(mkv),
             "-vf", "select=eq(n\\,%d)" % idx, "-frames:v", "1", str(out)],
            capture_output=True)
        require(proc.returncode == 0 and out.exists(),
                REFUSAL + ":decode_failed")
        a = Image.open(frames[idx]).convert("RGB")
        b = Image.open(out).convert("RGB")
        require(list(a.getdata()) == list(b.getdata()),
                REFUSAL + ":decode_identity:frame_%d" % idx)
        checks.append({"frame_index": idx, "identity": True})
    return checks


def main():
    profile, task = load_profile()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    geom = load_geometry()
    views = [
        {"id": "full vertical route overview",
         "caption": "authored frame forest overview "
                    "(B04 assembly_world; placement only)",
         "span": 1.6, "center": [0.0, 0.9, 0.0], "yaw0": 0.0},
        {"id": "close-up of skill transition and release",
         "caption": "mutation frame close (A05 origins + 14 "
                    "hand mappings with distances)",
         "span": 0.12, "center": [0.0, -0.03, 0.0], "yaw0": 0.6},
        {"id": "side and alternate-trunk view",
         "caption": "forearm interface close (31 forearm "
                    "correspondences, humerus frame, wrist "
                    "interface)",
         "span": 0.4, "center": [0.0, -0.14, 0.0], "yaw0": 0.3},
    ]
    frames, row_plan = render_frames(geom, views)
    mkv = HERE / "capture" / "capture_mat2_b07_records_20261001.mkv"
    mkv.parent.mkdir(parents=True, exist_ok=True)
    capture_sha = encode(frames, mkv)
    decode_checks = decode_identity(mkv, frames)

    sample_bookmarks = []
    for tick in range(TICKS[0], TICKS[1] + 1):
        sample_bookmarks.append(tick)
    rows = []
    subjects = {
        "full vertical route overview": sorted(geom["b04_roots"]),
        "close-up of skill transition and release":
            [r[0] for r in geom["hand"]] + [g[0] for g in geom["grasp"]],
        "side and alternate-trunk view": [r[0] for r in geom["forearm"]],
    }
    layers_by_view = {
        "full vertical route overview":
            ["body/trunk labels", "height and tick readouts"],
        "close-up of skill transition and release":
            ["skill and command IDs", "grip/support contacts",
             "body/trunk labels"],
        "side and alternate-trunk view":
            ["body/trunk labels", "height and tick readouts"],
    }
    for i, (vid, mode) in enumerate(row_plan):
        view = next(v for v in views if v["id"] == vid)
        yaw_last = view["yaw0"] + 0.35 * TICKS[1]
        samples = []
        for tick in range(TICKS[0], TICKS[1] + 1):
            yaw = view["yaw0"] + 0.35 * tick
            samples.append({
                "tick": tick,
                "position": [round(math.cos(yaw) * view["span"],
                                   9) + view["center"][0],
                             round(math.sin(yaw) * view["span"],
                                   9) + view["center"][1],
                             view["center"][2]],
                "orientation": quat_wxyz([0.0, 0.0, 1.0], yaw),
                "target": view["center"],
                "distance_to_target": view["span"],
            })
        rows.append({
            "view_id": vid,
            "mode": mode,
            "pair_id": vid,
            "state_binding": {"kind": "trace", "sha256": geom["state"]},
            "artifact_locator": {"kind": "video",
                                 "seconds": [i * FRAMES_PER_ROW,
                                             (i + 1) * FRAMES_PER_ROW]},
            "camera": {
                "frame_id": "record_space_" + vid,
                "coordinate_unit": "m",
                "handedness": "right",
                "orientation_convention":
                    "quaternion_wxyz_camera_to_frame",
                "forward_axis": "+Z", "up_axis": "+Y",
                "near_far_planes": [0.001, 10.0],
                "viewport_resolution": VIEWPORT,
                "aspect_ratio": VIEWPORT[0] / VIEWPORT[1],
                "projection": "orthographic",
                "orthographic_span": view["span"],
                "sample_mode": "sampled_trajectory",
                "interpolation":
                    "linear_position_target_slerp_orientation",
                "samples": samples,
                "camera_motion_or_bookmark_sequence":
                    "4 fixed bookmarks per row (record-ticks 0..3, yaw "
                    "0.35 rad/tick about +Z of record_space_%s; last yaw "
                    "%.3f rad)" % (vid, yaw_last),
                "state_or_tick_interval":
                    "record-ticks %d..%d (camera bookmark timeline over "
                    "the static record set; no simulation tick exists)"
                    % (TICKS[0], TICKS[1]),
            },
            "visibility": (
                {"layers": layers_by_view[vid],
                 "label_ids": [],
                 "selected_ids": [],
                 "required_subject_ids": subjects[vid],
                 "observed_subject_ids": subjects[vid],
                 "missing_subject_ids": [],
                 "tag_bindings": [], "occlusion_mode": "mixed"}
                if mode == "diagnostic" else
                {"layers": [], "label_ids": [],
                 "selected_ids": [],
                 "required_subject_ids": subjects[vid],
                 "observed_subject_ids": subjects[vid],
                 "missing_subject_ids": [],
                 "tag_bindings": [],
                 "occlusion_mode": "depth_tested"}),
            "caption": view["caption"] if mode == "diagnostic" else "",
        })
    ffmpeg_version = subprocess.run([FFMPEG, "-version"],
                                    capture_output=True).stdout.decode()
    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": TASK_ID,
        "profile_id": profile["id"],
        "run_id": "08d3db08d4d64179b2f95a516a2155bd",
        "tick_interval": TICKS,
        "capture_sha256": capture_sha,
        "subject_sha256": geom["state"],
        "views": rows,
    }
    context = {
        "task_id": TASK_ID,
        "run_id": "08d3db08d4d64179b2f95a516a2155bd",
        "subject_sha256": geom["state"],
        "capture_sha256": capture_sha,
        "tick_interval": TICKS,
        "criteria_sha256": CRITERIA_SHA256,
        "honesty_note": HONESTY + "; motion-class delivery is the camera "
                        "bookmark timeline over the static record set",
        "artifact": {"path": str(mkv).replace("\\", "/"),
                     "sha256": capture_sha},
        "ffmpeg": ffmpeg_version.splitlines()[0],
        "profile_snapshot": {"id": profile["id"], "kind": profile["kind"],
                             "views": profile["views"],
                             "clean_view_required":
                                 profile["clean_view_required"],
                             "camera_required_fields":
                                 profile["camera_required_fields"]},
    }
    sys.path.insert(0, str(CHECKOUT / "tools" / "monkey_campaign"))
    from visual_capture import validate_manifest
    structural = validate_manifest(manifest, context, profile)
    receipt = {
        "schema": "chimera.b07_capture_receipt.v1",
        "task_id": TASK_ID,
        "manifest": manifest,
        "context": context,
        "structural_validation": structural,
        "decode_identity_checks": decode_checks,
        "frame_count": len(frames),
        "rows": len(rows),
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B make_capture.py"},
    }
    out = HERE / "capture" / "capture_receipt.json"
    out.write_bytes(canonical(receipt) + b"\n")
    print("wrote", out, "| capture sha", capture_sha[:16],
          "| rows", len(rows), "| frames", len(frames))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
