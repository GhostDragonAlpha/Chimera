"""run_terrain_contact -- MAT2-F02 build harness.

Order is the discipline: bites first (all five must bite, recorded), then the
pinned pass (P1-P6), then frames + 16-field camera records (P7) and the
determinism pass (P8). Everything lands in evidence/ as JSON/BMP; report.md is
generated from the receipt by make_report.py -- never hand-written.

Verbs (from this directory):
    python -B run_terrain_contact.py build    # bites + checks + frames + receipt
    python -B run_terrain_contact.py all      # build + capture manifest + report

CPU-only, stdlib-only, deterministic.
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

import terrain_contact as tc
import f01_implementation as f01

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"

SCHEMA = "chimera.mat2_f02.qualification.v1"
CARD = "MAT2-F02"
ATTEMPT_ID = "c05153d7973f4e92bcda2759e0977b8d"
CRITERIA_SHA256 = "16ee643245f3db63a9ca367ab05792e4ed4bcdc13f5bbab95d506319290f59c1"
RUN_ID = "mat2-f02-forest-20260928-c05153d7"
TASK_SHORT = "F02"

# --- frozen cameras (PREREGISTRATION section 5) --------------------------------
VIEWS = {
    "V1_clearing_overview": {
        "position": [0.0, 46.0, -32.0], "target": [0.0, 0.0, 0.0], "vfov_deg": 55.0},
    # V2/V3 targets are the settled probe centres (declared intent: frame the
    # settled probe; the prereg formula named the pre-settle centre; disclosed
    # as Amendment A2 in report.md -- no bar changed).
    "V2_contact_seam": None,      # target = settled S4 probe centre
    "V3_side_depth": None,        # target = settled S3 probe centre
    "V4_oblique_depth": {
        "position": [-34.0, 20.0, -30.0], "target": [0.0, 0.0, 0.0], "vfov_deg": 55.0},
}
V2_SPEC = {"position": [9.95, 1.30, 1.60], "vfov_deg": 55.0}
V3_SPEC = {"position": [-15.035646, 2.60, -14.50], "vfov_deg": 45.0}
MANIFEST_VIEW_ORDER = ["V1_clearing_overview", "V2_contact_seam", "V3_side_depth"]
PROFILE_VIEW_IDS = {
    "V1_clearing_overview": "clearing overview",
    "V2_contact_seam": "terrain/trunk seam close-up",
    "V3_side_depth": "side and oblique depth checks",
}
PAIR_IDS = {
    "V1_clearing_overview": "pair-clearing-overview",
    "V2_contact_seam": "pair-terrain-contact-seam",
    "V3_side_depth": "pair-side-depth",
}
GATE_BOUND_FILE = "frame_V1_clearing_overview_clean.bmp"

# assigned probe-site visibility per view (P5; PREREGISTRATION section 3)
ASSIGNED = {
    "V1_clearing_overview": ["S1", "S3"],
    "V2_contact_seam": ["S4"],
    "V3_side_depth": ["S3"],
    "V4_oblique_depth": ["S5"],
}

SUBJECTS = ["monkey_clearing_ground", "monkey_clearing_boundary_posts", "trunk_01"]
PROBE_SUBJECT = "contact_probe_set"
PROFILE_LAYERS = ["render mesh", "collision surfaces",
                  "normals/contact markers", "scene bounds", "stable 3D labels"]
DIAGNOSTIC_OVERLAYS = ["diagnostic: render-mesh wireframe",
                       "diagnostic: collision surfaces (probe shell + contacted "
                       "ground triangles)",
                       "diagnostic: normals/contact markers",
                       "diagnostic: scene bounds",
                       "diagnostic: stable 3D labels"]


def require(ok, code, detail=""):
    if not ok:
        raise tc.Refusal(code, detail)


# --- labels ---------------------------------------------------------------------
def f02_labels(declaration, trunk, obs):
    labels = f01.frozen_labels(declaration, trunk)          # the 15 frozen labels
    for key in sorted(obs):                                  # + the five site markers
        c = obs[key]["rest_probe_centre_clearing_m"]
        labels.append({"id": "probe_" + key, "anchor": [c[0], c[1] + 0.12, c[2]]})
    require(len(labels) == 20, "f02_label_count", len(labels))
    return labels


LABEL_SUBJECT = {
    "spawn": "monkey_clearing_ground", "trunk_01": "trunk_01",
    "corner_SW": "monkey_clearing_boundary_posts", "corner_SE": "monkey_clearing_boundary_posts",
    "corner_NE": "monkey_clearing_boundary_posts", "corner_NW": "monkey_clearing_boundary_posts",
    "edge_N": "monkey_clearing_boundary_posts", "edge_E": "monkey_clearing_boundary_posts",
    "edge_S": "monkey_clearing_boundary_posts", "edge_W": "monkey_clearing_boundary_posts",
    "mound_m1": "monkey_clearing_ground", "mound_m2": "monkey_clearing_ground",
    "mound_m3": "monkey_clearing_ground", "mound_m4": "monkey_clearing_ground",
    "mound_m5": "monkey_clearing_ground",
    "probe_S1": PROBE_SUBJECT, "probe_S2": PROBE_SUBJECT, "probe_S3": PROBE_SUBJECT,
    "probe_S4": PROBE_SUBJECT, "probe_S5": PROBE_SUBJECT,
}


# --- contact-site probes for the render/collision correspondence (P5) -----------
def site_probes(surface, obs):
    """One probe per settled site: the last-tick contact point with the largest
    normal impulse -- an actual contact surface point reported by the shared
    path, classified through F01's camera machinery."""
    out = {}
    for key in sorted(obs):
        recs = obs[key]["records_last_tick"]
        require(bool(recs), "f02_no_contact_records", key)
        best = max(recs, key=lambda r: (r["jn_Ns"], -r["tri_ground"]))
        p = best["contact_point_clearing_m"]
        # Amendment A1 (P5 oracle): contact points may sit ON a triangle edge
        # or vertex (feature contacts). F01's own piecewise-linear mechanism
        # applies: the oracle normal is the SET of normals of all ground
        # triangles whose footprint contains the point; the ray-hit face must
        # be one of them (bar 1e-12). Heights stay exact (bar 1e-9).
        out[key] = {"id": "contact_" + key, "kind": "ground",
                    "point": list(p), "surface": tc.GROUND_SURFACE_ID,
                    "oracle_h": surface.height_at(p[0], p[2]),
                    "oracle_n": list(surface.normal_at(p[0], p[2])),
                    "oracle_n_set": f01._incident_ground_normals(surface,
                                                                 p[0], p[2])}
    return out


def correspondence_checks(mesh, views, site_pts):
    """P5: assigned markers VISIBLE_EXACT; no VISIBLE_BUT_MISMATCH anywhere."""
    per_view = {}
    for vname, cam in views.items():
        per_view[vname] = {}
        for key, pr in site_pts.items():
            per_view[vname][key] = f01.classify_probe(mesh, cam, pr)
    failures = []
    for vname, rows in per_view.items():
        for key, rec in rows.items():
            if rec["outcome"] == "VISIBLE_BUT_MISMATCH":
                failures.append({"site": key, "view": vname, "why": "bars breached",
                                 "rec": rec})
        for key in ASSIGNED[vname]:
            rec = rows[key]
            if rec["outcome"] != "VISIBLE_EXACT":
                failures.append({"site": key, "view": vname,
                                 "why": "assigned marker not VISIBLE_EXACT",
                                 "outcome": rec["outcome"], "rec": rec})
    return {"prediction": "P5_render_collision_correspondence",
            "per_view": {v: {k: r["outcome"] for k, r in rows.items()}
                         for v, rows in per_view.items()},
            "details": {v: {k: r for k, r in rows.items()} for v, rows in per_view.items()},
            "assigned": ASSIGNED, "failures": failures,
            "ok": not failures}


# --- contact diagnostic drawing (the profile's collision/markers layers) --------
ORANGE = (255, 140, 0)
MAGENTA = (255, 0, 255)
GREEN = (0, 220, 0)
CYAN = (0, 255, 255)


def draw_contact_diagnostics(cam, colour, obs, site_pts, contact_tris):
    """Probe shell edges + contacted ground triangle outlines + contact points
    and up-normal stubs. Diagnostic layers only; clean frames never call this."""
    for key in sorted(obs):
        probe = obs[key]["probe"]
        for tri in tc.BOX_TRIANGLES:                      # shell wireframe
            pts = [cam.pixel(tc.to_clearing(probe.vertices[i])) for i in tri]
            if all(p is not None for p in pts):
                f01._line(colour, pts[0][0], pts[0][1], pts[1][0], pts[1][1], ORANGE)
                f01._line(colour, pts[1][0], pts[1][1], pts[2][0], pts[2][1], ORANGE)
                f01._line(colour, pts[2][0], pts[2][1], pts[0][0], pts[0][1], ORANGE)
    for tri in sorted(contact_tris):                      # contacted ground tris
        idx = mesh_indices_ground(tri)
        pts = []
        skip = False
        for i in idx:
            v = MESH_VERTICES[9 * i:9 * i + 3]
            p = cam.pixel(v)
            if p is None or p[2] > 60.0:
                skip = True
                break
            pts.append(p)
        if skip:
            continue
        f01._line(colour, pts[0][0], pts[0][1], pts[1][0], pts[1][1], GREEN)
        f01._line(colour, pts[1][0], pts[1][1], pts[2][0], pts[2][1], GREEN)
        f01._line(colour, pts[2][0], pts[2][1], pts[0][0], pts[0][1], GREEN)
    for key, pr in site_pts.items():                      # markers + normal stubs
        base = cam.pixel(pr["point"])
        if base is None:
            continue
        x, y = int(base[0]), int(base[1])
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                if 0 <= x + dx < f01.W and 0 <= y + dy < f01.H:
                    colour[y + dy][x + dx] = MAGENTA
        tip_pt = [pr["point"][i] + 0.25 * pr["oracle_n"][i] for i in range(3)]
        tip = cam.pixel(tip_pt)
        if tip is not None:
            f01._line(colour, base[0], base[1], tip[0], tip[1], CYAN)


MESH_VERTICES = None
MESH_INDICES = None
views_cache = None


def mesh_indices_ground(tri_index):
    k = tri_index * 3
    return MESH_INDICES[k], MESH_INDICES[k + 1], MESH_INDICES[k + 2]


# --- 16-field camera record (F01's field order, MAT2-F02 identity) --------------
def fmt_vec(v):
    return "[%.17g, %.17g, %.17g]" % (v[0], v[1], v[2])


def camera_record(view_name, variant, cam, labels_proj, layers):
    return {
        "frame_id": "MAT2-F02/%s_%s" % (view_name, variant),
        "coordinate_unit": "m",
        "position": cam.position,
        "orientation_convention_and_values": (
            "look-at, right-handed, x=east y=up z=south; fwd=%s right=%s up=%s "
            "(unit vectors)" % (fmt_vec(cam.fwd), fmt_vec(cam.right), fmt_vec(cam.up))),
        "target": cam.target,
        "distance_to_target": cam.distance_to_target,
        "projection": "perspective pinhole",
        "vertical_fov_or_orthographic_span": math.degrees(cam.vfov),
        "near_far_planes": [f01.NEAR, f01.FAR],
        "aspect_ratio": cam.aspect,
        "viewport_resolution": [f01.W, f01.H],
        "camera_motion_or_bookmark_sequence": "static bookmark (single frozen frame)",
        "visibility_layers": layers,
        "label_ids": labels_proj,
        "occlusion_or_xray_mode": "opaque z-buffer (no x-ray)",
        "state_or_tick_interval": "static scene, settled contact state (t=0)",
    }


def basis_quaternion(position, target):
    """Unit quaternion (w,x,y,z) of the look-at basis (F01's conversion law)."""
    fwd = f01.vnorm(f01.vsub(target, position))
    right = f01.vnorm(f01.vcross(fwd, [0.0, 1.0, 0.0]))
    up = f01.vcross(right, fwd)
    neg_fwd = [-x for x in fwd]
    m = [[right[0], up[0], neg_fwd[0]],
         [right[1], up[1], neg_fwd[1]],
         [right[2], up[2], neg_fwd[2]]]
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2.0
        q = [0.25 * s, (m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s,
             (m[1][0] - m[0][1]) / s]
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2.0
        q = [(m[2][1] - m[1][2]) / s, 0.25 * s, (m[1][0] + m[0][1]) / s,
             (m[0][2] + m[2][0]) / s]
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2.0
        q = [(m[0][2] - m[2][0]) / s, (m[1][0] + m[0][1]) / s, 0.25 * s,
             (m[2][1] + m[1][2]) / s]
    else:
        s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2.0
        q = [(m[1][0] - m[0][1]) / s, (m[0][2] + m[2][0]) / s,
             (m[2][1] + m[1][2]) / s, 0.25 * s]
    q = [x / math.sqrt(sum(x * x for x in q)) for x in q]
    w, x, y, z = q
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
         [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
         [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]]
    q_err = max(abs(r[i][j] - m[i][j]) for i in range(3) for j in range(3))
    return q, q_err


# --- the build -------------------------------------------------------------------
def build():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    results = {"schema": SCHEMA, "card": CARD, "attempt_id": ATTEMPT_ID,
               "criteria_sha256": CRITERIA_SHA256, "run_id": RUN_ID,
               "order": ["pins", "bites_first_failing", "pinned_pass_second",
                         "frames", "determinism"]}
    pins = tc.load_pins()
    results["pins"] = pins
    results["pin_source_tree"] = tc.PIN_SOURCE_TREE
    bundle, raw, asset_receipt, surface, declaration, trunk, law = tc.load_sources()
    results["asset_validator_receipt"] = asset_receipt

    # ---- failing-first falsifier bites, recorded BEFORE the pass ----
    bites = [
        tc.bite_ghost_support_decoupled_asset(bundle, surface),
        tc.bite_parallel_solver_unaccepted(surface),
        tc.bite_material_identity_detached(bundle),
        tc.bite_ghost_support_past_boundary(bundle),
        tc.bite_off_frame_probe_subject(f01),
    ]
    results["falsifier_bites"] = bites
    results["all_bites_bite"] = all(b["bites"] for b in bites)
    (EVIDENCE / "bites.json").write_bytes(json.dumps(
        {"bites": bites, "all_bite": results["all_bites_bite"]},
        indent=1, sort_keys=True).encode("utf-8"))

    # ---- pinned pass (run A) ----
    body = tc.ground_contact_body(bundle)
    obs = tc.run_sites(bundle, surface)
    results["P1_tied_asset"] = tc.tied_asset_checks(bundle, raw, body)
    results["P2_shared_path"] = tc.shared_path_checks(obs, law)
    results["P2b_exhaustive_reference"] = tc.exhaustive_reference_check(bundle, surface)
    results["P3_resting_agreement"] = tc.resting_checks(obs, bundle)
    results["P4_point_normal"] = tc.point_normal_checks(obs, bundle)
    results["P6_shear"] = tc.shear_checks(obs, bundle)

    # ---- P8 determinism: the pinned pass again, byte-identical ----
    body_b = tc.ground_contact_body(bundle)
    obs_b = tc.run_sites(bundle, surface)
    pass_a = {k: results[k] for k in ("P1_tied_asset", "P2_shared_path",
                                      "P3_resting_agreement", "P4_point_normal",
                                      "P6_shear")}
    pass_b = {
        "P1_tied_asset": tc.tied_asset_checks(bundle, raw, body_b),
        "P2_shared_path": tc.shared_path_checks(obs_b, law),
        "P3_resting_agreement": tc.resting_checks(obs_b, bundle),
        "P4_point_normal": tc.point_normal_checks(obs_b, bundle),
        "P6_shear": tc.shear_checks(obs_b, bundle),
    }
    raw_a = tc.canonical(pass_a)
    raw_b = tc.canonical(pass_b)
    results["P8_determinism"] = {
        "prediction": "P8_determinism",
        "pass_a_sha256": tc.sha_bytes(raw_a), "pass_b_sha256": tc.sha_bytes(raw_b),
        "canonical_results_identical": raw_a == raw_b,
        "ok": raw_a == raw_b}

    # ---- frames + camera records (P7) ----
    mesh = f01.SceneMesh(surface, trunk)
    global MESH_VERTICES, MESH_INDICES
    MESH_VERTICES, MESH_INDICES = mesh.vertices, mesh.indices
    site_pts = site_probes(surface, obs)
    contact_tris = sorted({r["tri_ground"] for key in obs
                           for r in obs[key]["records_last_tick"]})
    views = {"V1_clearing_overview": f01.Camera(VIEWS["V1_clearing_overview"]),
             "V4_oblique_depth": f01.Camera(VIEWS["V4_oblique_depth"])}
    v2 = dict(V2_SPEC)
    v2["target"] = list(obs["S4"]["rest_probe_centre_clearing_m"])
    v3 = dict(V3_SPEC)
    v3["target"] = list(obs["S3"]["rest_probe_centre_clearing_m"])
    views["V2_contact_seam"] = f01.Camera(v2)
    views["V3_side_depth"] = f01.Camera(v3)

    results["P5_correspondence"] = correspondence_checks(mesh, views, site_pts)

    labels = f02_labels(declaration, trunk, obs)
    global views_cache
    views_cache = views
    frames = {}
    manifest = {}
    for vname in ("V1_clearing_overview", "V2_contact_seam", "V3_side_depth",
                  "V4_oblique_depth"):
        cam = views[vname]
        labels_proj = []
        for lab in labels:
            px = cam.pixel(lab["anchor"])
            labels_proj.append({"id": lab["id"], "anchor": lab["anchor"],
                                "projected_px": [px[0], px[1]] if px else None,
                                "in_frame": bool(px and 0 <= px[0] < f01.W
                                                 and 0 <= px[1] < f01.H)})
        clean_name = "frame_%s_clean.bmp" % vname
        colour, depth, stats = f01.render_frame(mesh, cam, diagnostic=False)
        f01.write_bmp(EVIDENCE / clean_name, colour)
        depth_name = "depth_%s.bmp" % vname
        dinfo = f01.write_depth_bmp(EVIDENCE / depth_name, depth)
        marker_probes = [site_pts[k] for k in ASSIGNED[vname]]
        colour_d, _, stats_d = f01.render_frame(mesh, cam, diagnostic=False)
        f01._draw_diagnostic(mesh, cam, colour_d, probes=marker_probes, labels=labels)
        draw_contact_diagnostics(cam, colour_d, obs, site_pts, contact_tris)
        diag_name = "frame_%s_diagnostic.bmp" % vname
        f01.write_bmp(EVIDENCE / diag_name, colour_d)
        layers = list(SUBJECTS)
        manifest[vname + "_clean"] = camera_record(
            vname, "clean", cam, labels_proj, layers)
        manifest[vname + "_diagnostic"] = camera_record(
            vname, "diagnostic", cam, labels_proj,
            layers + DIAGNOSTIC_OVERLAYS)
        frames[vname] = {"clean": clean_name, "diagnostic": diag_name,
                         "depth": depth_name,
                         "triangles_drawn_clean": stats["triangles_drawn"],
                         "triangles_drawn_diagnostic": stats_d["triangles_drawn"],
                         "depth_range": dinfo}
    results["P7_frames"] = {
        "prediction": "P7_frames_and_manifest",
        "frames": frames,
        "camera_manifest_views": sorted(manifest.keys()),
        "camera_fields_order": [
            "frame_id", "coordinate_unit", "position",
            "orientation_convention_and_values", "target", "distance_to_target",
            "projection", "vertical_fov_or_orthographic_span",
            "near_far_planes", "aspect_ratio", "viewport_resolution",
            "camera_motion_or_bookmark_sequence", "visibility_layers",
            "label_ids", "occlusion_or_xray_mode", "state_or_tick_interval"],
        "ok": len(frames) == 4 and all(len(manifest[m]) == 16 for m in manifest)}
    (EVIDENCE / "camera_manifest.json").write_bytes(json.dumps(
        {"views": manifest}, indent=1, sort_keys=True).encode("utf-8"))

    # the settled contact state the diagnostic rows draw (state_binding target)
    trace = {
        "schema": "chimera.mat2_f02.contact_trace.v1",
        "run_id": RUN_ID,
        "frame_map": "clearing (x, y, z) -> contact (x, -z, y); inverse "
                     "contact (a, b, c) -> clearing (a, c, -b)",
        "sites": {key: {
            "drop_target_xz": obs[key]["drop_target_xz"],
            "query_height_at_target_m": obs[key]["query_height_at_target_m"],
            "rest_probe_centre_clearing_m": obs[key]["rest_probe_centre_clearing_m"],
            "min_corner_separation_m": obs[key]["min_corner_separation_m"],
            "probe_vertices_clearing_m": [list(tc.to_clearing(v))
                                          for v in obs[key]["probe"].vertices],
            "records_last_tick": obs[key]["records_last_tick"],
        } for key in sorted(obs)},
        "contact_ground_triangle_indices": sorted(contact_tris),
    }
    (EVIDENCE / "contact_trace.json").write_bytes(json.dumps(
        trace, indent=1, sort_keys=True).encode("utf-8"))

    # P7's manifest half is built by make_capture_manifest.py (campaign schema +
    # registry profile validation); its receipt is merged here at report time.

    check_keys = ["P1_tied_asset", "P2_shared_path", "P2b_exhaustive_reference",
                  "P3_resting_agreement", "P4_point_normal",
                  "P5_correspondence", "P6_shear", "P7_frames", "P8_determinism"]
    results["all_ok"] = (results["all_bites_bite"]
                         and all(results[k]["ok"] for k in check_keys))
    results["honest_boundary"] = {
        "claim": "the pinned F01 terrain asset bound to the shared M06 contact "
                 "path with material identity, settled-probe agreement inside "
                 "frozen tolerances, and attempt-local renders of the actual "
                 "contact state",
        "not_claimed": [
            "engine run, native load_mesh upload, or HTTP playthrough",
            "boundary-post or trunk contact (F03/next-card scope; inventoried)",
            "world-build 4 km terrain lane integration (context only, hashes in "
            "PREREGISTRATION section 1)",
            "training, runtime or playable-build acceptance",
            "any visual acceptance beyond the declared cameras and this receipt"],
    }
    (EVIDENCE / "checks.json").write_bytes(json.dumps(
        results, indent=1, sort_keys=True).encode("utf-8"))
    print(json.dumps({"evidence": str(EVIDENCE), "all_ok": results["all_ok"],
                      "bites_all_bite": results["all_bites_bite"]}))
    return results


if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv or argv[0] == "build":
        build()
    elif argv[0] == "all":
        build()
        import make_capture_manifest
        make_capture_manifest.main()
        import make_report
        make_report.main()
    else:
        raise SystemExit("run_terrain_contact: unknown verb " + repr(argv))
