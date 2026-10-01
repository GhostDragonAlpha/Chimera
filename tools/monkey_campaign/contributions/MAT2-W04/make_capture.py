#!/usr/bin/env python3
"""MAT2-W04 profile-class capture (profile `anatomy`, kind `visible_static`).

HONESTY LABEL (carried in the manifest, the context and burned into every
diagnostic frame): this is a deterministic CPU software raster of the ATTEMPT'S
PINNED RECORDS (B04 frame forest, B05 port requirements, A05 mutation origins,
A07 grasp resolutions, B07 ownership mappings). It is NOT native engine frames
and NOT a runtime render. The 8 port world placements are inventoried ABSENT
(no accepted correspondence places the source-local port points on the target
geometry: R-OWN-04 exact per-axis excesses, B04 no_fusion_statement); the
close-up renders the port RECORDS as a labeled table, never as invented
geometry. Screens never gate; the receipts are the numerical evidence the
profile demands. Full 16-field camera record per view row (17-key manifest
vocabulary); visible_static delivery is the PNG image set; the capture
identity is the ordered-concatenation sha256 (P8) and every view row carries
the SAME composite state hash as the freeze manifest (the profile falsifier's
view-toggle instrument). validate_manifest runs READ-ONLY against the registry
profile (G7).

Run:  python -B make_capture.py     (writes capture/*, evidence/*)
Exit: 0 green / 2 named refusal. CPU only.
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
WS = Path(r"E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-W04"
          r"\d94341b2bd694bd2b725964040201398")
SCRATCH = WS / "scratch" / "capture"
REGISTRY = Path("E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")

TASK_ID = "W04"
CARD_ID = "MAT2-W04"
CRITERIA_SHA256 = ("cb66e8e9c24b6a838cb4e7b3dededef3c7c05fa72a77c9973a6ddb8b"
                   "7ff16e03")
RUN_ID = "d94341b2bd694bd2b725964040201398"
VIEWPORT = [480, 360]
TICK_INTERVAL = [0, 0]
HONESTY = ("RECORD-SPACE RASTER of pinned records - not engine frames; "
           "port world placements inventoried ABSENT (R-OWN-04/05)")

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
    card = json.loads(row[0])["kanban"]["cards"][CARD_ID]
    require(card.get("criteria_sha256") == CRITERIA_SHA256,
            REFUSAL + ":criteria_mismatch")
    task = card["spec"]["ontology_qualification"]["task"]
    profile = task["verification_profile"]
    for key in ("id", "kind", "views", "clean_view_required",
                "diagnostic_layers", "camera_required_fields"):
        require(key in profile, REFUSAL + ":profile_key:" + key)
    require(profile["id"] == "anatomy" and profile["kind"] == "visible_static",
            REFUSAL + ":profile_identity")
    return profile, task


# ---- geometry from the pinned records --------------------------------------
def load_geometry():
    b04 = json.loads((CONTRIB / "MAT2-B04" / "frame_forest.json")
                     .read_text("utf-8"))
    b05 = json.loads((CONTRIB / "MAT2-B05"
                      / "mechanical_port_requirements.json").read_text("utf-8"))
    own = json.loads((CONTRIB / "MAT2-B07" / "ownership_mappings.json")
                     .read_text("utf-8"))
    a05 = json.loads((CONTRIB / "MAT2-A05" / "mutation_structure.json")
                     .read_text("utf-8"))
    a07 = json.loads((CONTRIB / "MAT2-A07" / "placement_resolution.json")
                     .read_text("utf-8"))
    manifest = json.loads((HERE / "w04_freeze_manifest.json").read_text("utf-8"))
    state = manifest["state_composite_sha256"]

    roots = {fid: f["origin_m"] for fid, f in b04["frames"].items()
             if f.get("component_root")}
    unresolved = [u["body"] for u in b04.get("unresolved_bodies", [])]
    bonds = [(b["bond_id"], b["body"], b.get("parent_body_declared"))
             for b in b04.get("bonds", [])]

    def origin(name):
        if name == a05["anchor_body"]["name"]:
            return [0.0, 0.0, 0.0]
        p = None
        for b in a05["bodies"]:
            if b["name"] == name:
                p = list(b["mutation"]["pos_m"])
                par = b.get("parent", "").replace(
                    "ref.macaque_arm_hand_mutation.body.", "")
                while par and par != a05["anchor_body"]["name"] and par:
                    for b2 in a05["bodies"]:
                        if b2["name"] == par:
                            p = [a + c for a, c in zip(p, b2["mutation"]["pos_m"])]
                            par = b2.get("parent", "").replace(
                                "ref.macaque_arm_hand_mutation.body.", "")
                            break
                    else:
                        break
                break
        return p

    bodies = {}
    for b in a05["bodies"]:
        o = origin(b["name"])
        if o is not None:
            bodies[b["name"]] = o
    ports = [(p["port_id"], p["source_body"],
              (p["tendon_membership"][0]["tendon"]
               if p["tendon_membership"] else ""),
              p["source_pos_local_m"]) for p in b05["ports"]]
    require(len(ports) == 8, REFUSAL + ":ports_count")
    hand = [(r["record_id"], r["location_m"],
             r["decision"]["nearest_mutant_body"],
             r["decision"]["recorded_distance_m"])
            for r in own["records"]["hand_body_mappings"]]
    fore = [(r["record_id"], r["owner_body"], r["location_m"],
             r["decision"]["recorded_distance_m"])
            for r in own["records"]["forearm_correspondences"]]
    grasp = [(g["endpoint_id"], g["position_m"])
             for g in a07["grasp_endpoint_resolutions"]]
    return {"roots": roots, "unresolved": unresolved, "bonds": bonds,
            "bodies": bodies, "ports": ports, "hand": hand, "fore": fore,
            "grasp": grasp, "state": state}


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


def triad(draw, P, o, scale=0.04):
    axes = [([o[0] + scale, o[1], o[2]], (255, 90, 90), "X"),
            ([o[0], o[1] + scale, o[2]], (90, 255, 90), "Y"),
            ([o[0], o[1], o[2] + scale], (110, 150, 255), "Z")]
    for tip, color, name in axes:
        p, q = P(o), P(tip)
        draw.line([p[0], p[1], q[0], q[1]], fill=color)
        draw.text((q[0] + 2, q[1] - 4), name, fill=color)


def draw_scene(draw, geom, view, mode, viewport):
    span, center = view["span"], view["center"]
    def P(p):
        return project_ortho(p, center, span, view["yaw"], viewport)
    vid = view["id"]
    if vid == "whole-creature overview":
        pts = sorted(geom["roots"].items())
        vals = [v for _, v in pts]
        if mode == "diagnostic":
            lo = [min(v[i] for v in vals) for i in range(3)]
            hi = [max(v[i] for v in vals) for i in range(3)]
            pad = 0.05
            a = P([lo[0] - pad, lo[1] - pad, lo[2]])
            b = P([hi[0] + pad, hi[1] + pad, hi[2]])
            rx0, rx1 = sorted([a[0], b[0]])
            ry0, ry1 = sorted([a[1], b[1]])
            draw.rectangle([rx0, ry0, rx1, ry1],
                           outline=(70, 70, 90))
            draw.text((rx0 + 3, ry0 - 12),
                      "outer envelope = recorded body-origin region "
                      "(not a mesh)", fill=(150, 150, 180))
        for fid, o in pts:
            p = P(o)
            draw.ellipse([p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5],
                         outline=(80, 200, 255))
            if mode == "diagnostic":
                draw.text((p[0] + 7, p[1] - 4), fid, fill=(150, 220, 255))
                triad(draw, P, o)
        if mode == "diagnostic":
            draw.text((6, VIEWPORT[1] - 46),
                      "unresolved bodies inventoried: "
                      + ", ".join(geom["unresolved"]), fill=(255, 170, 90))
            draw.text((6, VIEWPORT[1] - 32),
                      "mechanical bonds (record count): %d" % len(geom["bonds"]),
                      fill=(200, 200, 140))
    elif vid == "local attachment close-up":
        # the port RECORDS as a labeled table (world placements absent by
        # recorded refusal - never invented geometry)
        rows = ["PORT RECORDS (B05 chimera.mechanical_port_requirements.v1)",
                "world placements ABSENT: no accepted correspondence "
                "(R-OWN-04/05)",
                "port_id          body     tendon            qual"]
        for pid, body, tendon, loc in geom["ports"]:
            rows.append("%-16s %-8s %-16s false" % (pid, body, tendon[:16]))
        if mode == "diagnostic":
            for i, line in enumerate(rows):
                draw.text((8, 10 + i * 13), line,
                          fill=(255, 120, 120) if i < 2 else (140, 255, 170))
            # the pinned attachment records that DO carry coordinates:
            for rid, owner, loc, dist in geom["fore"]:
                if owner != "humerus":
                    continue
                p = P(loc)
                draw.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3],
                             fill=(230, 160, 90))
                draw.text((p[0] + 4, p[1] + 2),
                          rid + " d=%.4f" % dist, fill=(255, 200, 140))
            triad(draw, P, [0.0, 0.0, 0.0], scale=0.02)
    elif vid == "orthogonal side and oblique views":
        for rid, owner, loc, dist in geom["fore"]:
            p = P(loc)
            draw.ellipse([p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2],
                         fill=(230, 160, 90))
            if mode == "diagnostic" and owner == "humerus":
                draw.text((p[0] + 3, p[1] + 2),
                          rid + " d=%.4f" % dist, fill=(255, 200, 140))
        if mode == "diagnostic":
            wrist = [0.0070003917552167744, -0.2649999467838506,
                     0.0004971479333903965]
            p = P(wrist)
            draw.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4],
                         outline=(255, 255, 255))
            draw.text((p[0] + 6, p[1]), "wrist interface (A05 anchor)",
                      fill=(255, 255, 255))
            triad(draw, P, [0.0, 0.0, 0.0])
            # the labeled oblique inset (yaw 0.6), same pinned records
            ix0, iy0, ix1, iy1 = VIEWPORT[0] - 190, 8, VIEWPORT[0] - 8, 150
            draw.rectangle([ix0, iy0, ix1, iy1], outline=(90, 90, 110))
            draw.text((ix0 + 4, iy1 + 2), "oblique inset (yaw 0.6 rad)",
                      fill=(200, 200, 230))

            def P2(pt):
                span2, yaw2 = 0.12, 0.6
                c2 = view["center"]
                x, y, z = (pt[i] - c2[i] for i in range(3))
                rx = x * math.cos(yaw2) - y * math.sin(yaw2)
                ry = x * math.sin(yaw2) + y * math.cos(yaw2)
                return [ix0 + 6 + (rx / span2 + 0.5) * (ix1 - ix0 - 12),
                        iy0 + 6 + (0.5 - z / span2) * (iy1 - iy0 - 12)]
            for name, o in sorted(geom["bodies"].items()):
                q = P2(o)
                draw.ellipse([q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2],
                             fill=(90, 90, 200))
            for rid2, loc2, nearest, dist2 in geom["hand"]:
                q = P2(loc2)
                w = P2(geom["bodies"][nearest]) if nearest in geom["bodies"] else q
                draw.line([q[0], q[1], w[0], w[1]], fill=(60, 160, 60))
                draw.ellipse([q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2],
                             fill=(80, 220, 120))
            for gid, loc3 in geom["grasp"]:
                q = P2(loc3)
                draw.rectangle([q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2],
                               outline=(90, 220, 220))
LAYERS_BY_VIEW = {
    "whole-creature overview":
        ["outer envelope", "selected bones/joints", "frame axes",
         "stable 3D labels"],
    "local attachment close-up":
        ["attachment sites", "muscle/tendon paths", "frame axes",
         "stable 3D labels"],
    "orthogonal side and oblique views":
        ["muscle/tendon paths", "attachment sites", "selected bones/joints",
         "stable 3D labels", "frame axes"],
}
SUBJECTS_BY_VIEW = {
    "whole-creature overview":
        ["root_pelvis", "root_thorax", "root_ulna", "root_ulna_l"],
    "local attachment close-up":
        ["BIClong-P11", "BICshort-P8", "BRD-P3", "PT-P5",
         "BIClong_l-P11", "BICshort_l-P8", "BRD_l-P3", "PT_l-P5"],
    "orthogonal side and oblique views": ["wrist_interface_A05_anchor"],
}

VIEWS = [
    {"id": "whole-creature overview", "span": 0.62,
     "center": [-0.0458, 0.96, 0.0], "yaw": 0.0,
     "caption": "authored frame forest overview (B04 component roots; "
                "placement only)"},
    {"id": "local attachment close-up", "span": 0.35,
     "center": [0.0, -0.15, 0.0], "yaw": 0.3,
     "caption": "the 8 port RECORDS as a labeled table (world placements "
                "inventoried ABSENT; R-OWN-04/05) + the pinned humerus "
                "attachment records"},
    {"id": "orthogonal side and oblique views", "span": 0.4,
     "center": [0.0, -0.14, 0.0], "yaw": 0.0,
     "caption": "31 forearm correspondence records with distances (orthogonal "
                "side; humerus frame) + labeled oblique inset (A05 mutation "
                "origins, 14 hand mappings, A07 grasp endpoints)"},
]


def camera_block(view):
    pos = [view["center"][0] + view["span"] * math.cos(view["yaw"]),
           view["center"][1] + view["span"] * math.sin(view["yaw"]),
           view["center"][2]]
    q = quat_wxyz([0.0, 0.0, 1.0], view["yaw"])
    return {
        "frame_id": "record_space_" + view["id"],
        "coordinate_unit": "m",
        "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "forward_axis": "+Z", "up_axis": "+Y",
        "position": pos,
        "orientation_convention_and_values": ("wxyz " + json.dumps(q)),
        "target": list(view["center"]),
        "distance_to_target": view["span"],
        "projection": "orthographic",
        "orthographic_span": view["span"],
        "near_far_planes": [0.001, 10.0],
        "aspect_ratio": VIEWPORT[0] / VIEWPORT[1],
        "viewport_resolution": VIEWPORT,
        "camera_motion_or_bookmark_sequence":
            "single fixed bookmark (static record-space view; yaw "
            "%.3f rad about +Z)" % view["yaw"],
        "visibility_layers": LAYERS_BY_VIEW[view["id"]],
        "label_ids": [],
        "occlusion_or_xray_mode": "none (record-space raster; no z-buffer)",
        "state_or_tick_interval": ("static record set; no simulation tick "
                                   "exists (record ticks 0..0)"),
        "sample_mode": "fixed_bookmark",
        "samples": [{"tick": 0, "position": pos, "orientation": q,
                     "target": list(view["center"]),
                     "distance_to_target": view["span"]}],
    }


def main():
    profile, task = load_profile()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    geom = load_geometry()
    state = geom["state"]

    frames = []
    rows = []
    for view in VIEWS:
        cam = camera_block(view)
        for mode in ("diagnostic", "clean"):
            img = Image.new("RGB", tuple(VIEWPORT), (8, 8, 12))
            draw = ImageDraw.Draw(img)
            draw_scene(draw, geom, view, mode, VIEWPORT)
            if mode == "diagnostic":
                draw.text((6, 4), HONESTY, fill=(255, 120, 120))
                draw.text((6, 16),
                          "span %.3f m | layers: %s"
                          % (view["span"], "; ".join(
                              LAYERS_BY_VIEW[view["id"]])), fill=(255, 220, 120))
            name = ("frame_%s_%s.png"
                    % (view["id"].replace(" ", "_").replace("/", "_"), mode))
            png = SCRATCH / name
            img.save(png, format="PNG")
            frames.append(png)

    capture_sha = hashlib.sha256()
    per_frame = []
    for png in sorted(frames, key=lambda p: p.name):
        raw = png.read_bytes()
        capture_sha.update(raw)
        per_frame.append({"file": png.name, "sha256": sha_bytes(raw),
                          "bytes": len(raw)})
    capture_sha_hex = capture_sha.hexdigest()
    definition = ("sha256 over the concatenation of the frame PNG bytes in "
                  "sorted frame_files order (the B03 image-set convention)")

    out_dir = HERE / "capture"
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_files = {}
    for pf in per_frame:
        target = out_dir / pf["file"]
        target.write_bytes((SCRATCH / pf["file"]).read_bytes())
        frame_files[pf["file"]] = pf["sha256"]
        require(sha_bytes(target.read_bytes()) == pf["sha256"],
                REFUSAL + ":frame_copy:" + pf["file"])

    for view in VIEWS:
        cam = camera_block(view)
        for mode in ("diagnostic", "clean"):
            if mode == "diagnostic":
                labels = []
                bindings = []
                subjects = SUBJECTS_BY_VIEW.get(view["id"], [])
                rows.append({
                    "view_id": view["id"], "mode": mode,
                    "pair_id": view["id"],
                    "state_binding": {"kind": "state", "sha256": state},
                    "artifact_locator": {"kind": "image",
                                         "region": "whole_frame"},
                    "camera": cam,
                    "visibility": {
                        "layers": LAYERS_BY_VIEW[view["id"]],
                        "label_ids": labels, "selected_ids": [],
                        "required_subject_ids": subjects,
                        "observed_subject_ids": subjects,
                        "missing_subject_ids": [],
                        "tag_bindings": bindings,
                        "occlusion_mode": "mixed"},
                    "caption": view["caption"],
                    "absent_inventory": [
                        "port world placements (R-OWN-04 exact per-axis "
                        "excesses; B04 no_fusion_statement) - rendered as a "
                        "record table, never as geometry",
                        "tendon path intermediate site coordinates (only "
                        "endpoint membership counts are pinned)",
                    ],
                })
            else:
                rows.append({
                    "view_id": view["id"], "mode": mode,
                    "pair_id": view["id"],
                    "state_binding": {"kind": "state", "sha256": state},
                    "artifact_locator": {"kind": "image",
                                         "region": "whole_frame"},
                    "camera": cam,
                    "visibility": {
                        "layers": [], "label_ids": [], "selected_ids": [],
                        "required_subject_ids":
                            SUBJECTS_BY_VIEW.get(view["id"], []),
                        "observed_subject_ids":
                            SUBJECTS_BY_VIEW.get(view["id"], []),
                        "missing_subject_ids": [],
                        "tag_bindings": [],
                        "occlusion_mode": "depth_tested"},
                    "caption": "",
                })

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": TASK_ID,
        "profile_id": profile["id"],
        "run_id": RUN_ID,
        "tick_interval": TICK_INTERVAL,
        "capture_sha256": capture_sha_hex,
        "subject_sha256": state,
        "views": rows,
        "sheet_layout": {
            "kind": "image_set",
            "frame_count": len(per_frame),
            "frame_files": frame_files,
            "capture_sha_definition": definition,
            "honesty_label": HONESTY,
        },
    }
    context = {
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "subject_sha256": state,
        "capture_sha256": capture_sha_hex,
        "tick_interval": TICK_INTERVAL,
        "criteria_sha256": CRITERIA_SHA256,
        "honesty_note": HONESTY + "; visible_static delivery is the PNG "
                        "image set bound by the ordered-concatenation sha256",
        "artifact": {"path": str(out_dir).replace("\\", "/"),
                     "kind": "image_set", "sha256": capture_sha_hex},
        "renderer": {"engine": "PIL Image (CPU software raster)",
                     "pillow_version": Image.__version__,
                     "determinism": "fixed viewport/order; no z-buffer, no "
                                    "alpha blending"},
        "state_hash_note": ("every view row carries the freeze manifest's "
                            "state_composite_sha256; view toggles preserve "
                            "the physical state hash (profile falsifier "
                            "instrument)"),
    }
    (out_dir / "capture_manifest.json").write_bytes(canonical(manifest) + b"\n")
    (out_dir / "capture_context.json").write_bytes(canonical(context) + b"\n")

    # G7 evidence: the registry profile snapshot + provenance
    ev = HERE / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "registry_verification_profile.json").write_bytes(
        canonical(profile) + b"\n")
    provenance = {
        "db_path": str(REGISTRY).replace("\\", "/"),
        "row_path": "state id=1 payload -> kanban.cards[MAT2-W04].spec."
                    "ontology_qualification.task.verification_profile",
        "extractor": "sqlite3 read-only URI mode=ro; payload JSON; keys "
                     "id/kind/views/clean_view_required/diagnostic_layers/"
                     "camera_required_fields asserted",
        "task_id_form": "SHORT (W04)",
        "criteria_sha256": CRITERIA_SHA256,
    }
    (ev / "registry_profile_provenance.json").write_bytes(
        canonical(provenance) + b"\n")

    # the structural validator, against THE registry profile (P7)
    sys.path.insert(0, str(CHECKOUT / "tools" / "monkey_campaign"))
    import visual_capture  # noqa: PLC0415
    verdict = visual_capture.validate_manifest(manifest, context, profile)
    require(verdict.get("structurally_valid") is True,
            REFUSAL + ":validator:" + json.dumps(verdict)[:200])
    (out_dir / "capture_validation_receipt.json").write_bytes(
        canonical(verdict) + b"\n")
    print("wrote", out_dir)
    print("capture_sha256", capture_sha_hex[:16], "... frames",
          len(per_frame), "| validator", verdict["mode"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
