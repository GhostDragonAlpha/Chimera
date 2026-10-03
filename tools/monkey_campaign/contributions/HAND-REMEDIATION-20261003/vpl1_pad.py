# vpl1_pad.py - HAND-REMEDIATION-20261003 R1 stage 1: the VPL-1 declared-
# synthetic volar pad layer, amended by the measured macaque pad-stiffness
# source (AMENDMENT-1). Pins: prereg commit 4def67e4 (bytes 9213bf7d...),
# amendment commit 0c06e093 (bytes 018f0bc1...). The SEALED instrument
# (instrument_v2.py, 9514c5b1...) and the SEALED v2.0 screen
# (grasp_screen.py, 6b924e87...) are imported UNMODIFIED; this module adds
# the pad layer only. Stdlib only; deterministic; serial.
#
# FROZEN LAW (anti-tuning law extended to synthetic parameters; every value
# below is pinned by the prereg + amendment and is never adjusted after any
# result is seen):
#   VPL-1-GEOM (prereg G-1..G-6, unchanged by the amendment):
#     covered bodies = distal_thumb, distph2, distph3, distph4, distph5
#     t = 2.0e-3 m; u_max = 2.0e-3 m; admission window d in (pi_c, t+u_max]
#     patch rule = {v : n_v . a_B > 0}; post-hoc reclassification at the
#     UNCHANGED rigid solution; bone-level classes byte-identical.
#   VPL-1-FORCE (amendment-1): p = k*(u/t); k = K_eff*t/A_thumb;
#     K_eff = 120.0 N/m (0.120 mN/um, Kumar/Liu/Schloerb/Srinivasan 2015,
#     PMC4403516, independently verified); A_thumb = 5.160493e-05 m^2
#     (declared half-area from the vendor STLs at scale s).
#     THE PAD IS A CONTACT-GEOMETRY LAYER, NEVER A SUPPORT ELEMENT: at the
#     window edge it transmits K_eff*t = 0.24 N - 2.5 orders below the
#     declared 60 N/channel fixture press (TC-8 stays 0/8).

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import instrument_v2 as iv  # noqa: E402  (sealed, unmodified)
import grasp_screen as gs   # noqa: E402  (sealed, unmodified)

# ---------------------------------------------------------------------------
# pinned identities (refused on drift)
# ---------------------------------------------------------------------------
PREREG_R1_SHA = ("9213bf7d91ed9a6e6b2c5bbddc05d5ee36db63c600dfce42b559"
                 "632f6f565da9")
AMENDMENT_1_SHA = ("018f0bc120c0fa44cdcc1f611ab883764eb91e2d668975573f7922"
                   "18b93f94ac")
RECEIPT_V20_SHA = ("065328e4942a0bb8794138a96966aa8a3267fcd15ce084b9fb0490"
                   "dff76b19ec")
CONTROL_SEALED_SHA = gs.CONTROL_TABLE_SHA256      # d8aacc23...
INSTRUMENT_SHA = gs.INSTRUMENT_SHA256             # 9514c5b1...
SCREEN_SHA = ("6b924e87151f5e2235b9d9c023be85d0f7602d42020b37df4ba7bf58c0e"
              "9e0ea")
MESH_TABLE_SHA = ("6e5f3bac345a278eaa994203d48df71fa3a4d5d3f6d9be3e9c59f3b"
                  "08491cfb2")
MUTSTRUCT_SHA = ("48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d"
                 "54f45649")
CONTROL_VPL1_NAME = "control_input_table_vpl1.json"
CONTROL_VPL1_SHA = (
    "9cd8a56d89bdbe403a0c8513f04a32b2a43de85eea3d38c34f39931be9317783")

# ---------------------------------------------------------------------------
# frozen VPL-1 parameters (prereg + amendment-1; NEVER tuned post-run)
# ---------------------------------------------------------------------------
COVERED_BODIES = ("distal_thumb", "distph2", "distph3", "distph4",
                  "distph5")
T = 2.0e-3                     # layer thickness [m]      (prereg G-2)
U_MAX = 2.0e-3                 # max admitted indent [m] (prereg G-3)
WINDOW_LO = iv.PI_C            # 1.0e-3 m                (prereg G-4)
WINDOW_HI = T + U_MAX          # 4.0e-3 m                (prereg G-4)
K_EFF = 120.0                  # N/m                     (amendment-1 F-2)
A_THUMB = 5.160493e-05         # m^2 declared half-area  (amendment-1 1.1)
K = K_EFF * T / A_THUMB        # 4650.718448799368 Pa    (amendment-1 1.2)

# palmar sign rule (declared a priori from the CERTIFIED ranges, never from
# results): the pad faces the side the tuft curls toward under the range's
# DOMINANT flexion direction; sign = -1 iff the dominant magnitude of the
# certified distal-joint range is at negative theta. ip_flexion
# [-1.309, +0.436] -> dominant negative -> -1; md{k}_flexion [0, +1.5708]
# -> dominant positive -> +1. Verified two ways: the in-run FK check
# (palmar_axis_fk_identity) and control C6's constructed contact.
SIGN_TABLE = {"distal_thumb": -1.0, "distph2": 1.0, "distph3": 1.0,
              "distph4": 1.0, "distph5": 1.0}

C10_DEPTHS = (200e-6, 400e-6, 600e-6, 800e-6)   # measured protocol depths
C10_FORCES = tuple(K_EFF * u for u in C10_DEPTHS)


def sha_of(path):
    with open(path, "rb") as fh:
        import hashlib
        return hashlib.sha256(fh.read()).hexdigest()


# ---------------------------------------------------------------------------
# deterministic vertex normals (accumulate area-weighted triangle normals in
# ascending triangle index order; normalize; degenerate -> zero vector which
# the strict mask test excludes). NOTE: iv.parse_stl emits per-triangle
# corner vertices without deduplication, so each accumulated normal is the
# facet normal of exactly one triangle - the mask is a per-facet test and
# every corner of a masked triangle shares its mask value.
# ---------------------------------------------------------------------------
def compute_vertex_normals(verts, tris):
    acc = [[0.0, 0.0, 0.0] for _ in verts]
    for tri in tris:
        ia, ib, ic = tri[0], tri[1], tri[2]
        pa, pb, pc = verts[ia], verts[ib], verts[ic]
        ux, uy, uz = pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2]
        wx, wy, wz = pc[0] - pa[0], pc[1] - pa[1], pc[2] - pa[2]
        nx = uy * wz - uz * wy
        ny = uz * wx - ux * wz
        nz = ux * wy - uy * wx
        for idx in (ia, ib, ic):
            acc[idx][0] += nx
            acc[idx][1] += ny
            acc[idx][2] += nz
    out = []
    for v in acc:
        n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
        out.append((v[0] / n, v[1] / n, v[2] / n) if n > 0.0
                   else (0.0, 0.0, 0.0))
    return out


def vertex_areas(verts, tris):
    """per-corner area (1/3 of the incident triangle's area, accumulated in
    ascending triangle index order) - for the recorded mask-area column."""
    area = [0.0] * len(verts)
    for tri in tris:
        ia, ib, ic = tri[0], tri[1], tri[2]
        pa, pb, pc = verts[ia], verts[ib], verts[ic]
        ux, uy, uz = pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2]
        wx, wy, wz = pc[0] - pa[0], pc[1] - pa[1], pc[2] - pa[2]
        nx = uy * wz - uz * wy
        ny = uz * wx - ux * wz
        nz = ux * wy - uy * wx
        a = 0.5 * math.sqrt(nx * nx + ny * ny + nz * nz)
        third = a / 3.0
        area[ia] += third
        area[ib] += third
        area[ic] += third
    return area


def build_pad_data(model, prep):
    """Pad data per covered body at the evaluated posture: world facet
    normals, palmar axis a_B (declared sign rule; world frame at q), strict
    mask {n_v . a_B > 0}, recorded mask area."""
    bodies = model[0]
    pad = {}
    for name in COVERED_BODIES:
        verts_local, tris_local = model[3][name]
        normals_local = compute_vertex_normals(verts_local, tris_local)
        varea = vertex_areas(verts_local, tris_local)
        rot = prep.rotations[name]
        origin = prep.positions[name]
        far = max(prep.world[name], key=lambda v: iv.dist(v, origin))
        e_ext = iv.unit(iv.sub(far, origin))
        jn, axis_local, rng = bodies[name]["joints"][0]
        u_flex_world = iv.mat_vec(rot, axis_local)
        a_b = iv.scale(iv.unit(iv.cross(u_flex_world, e_ext)),
                       SIGN_TABLE[name])
        normals_world = [iv.mat_vec(rot, n) for n in normals_local]
        mask = [iv.dot(nw, a_b) > 0.0 for nw in normals_world]
        mask_area = 0.0
        total_area = 0.0
        for i, va in enumerate(varea):
            total_area += va
            if mask[i]:
                mask_area += va
        pad[name] = dict(joint=jn, axis_world=list(u_flex_world),
                         extent_world=list(e_ext), a_b=list(a_b),
                         normals_world=normals_world, mask=mask,
                         mask_area_m2=mask_area, total_area_m2=total_area)
    return pad


def palmar_axis_fk_identity(model, pad_data, base_preps):
    """In-run verification of the declared sign rule against the CERTIFIED
    model, at the base (q_zero) pose: perturbing each covered body's distal
    joint by SIGN*0.1 rad (inside the certified range) must move the body's
    tuft (farthest vertex) toward a_B with positive dot. base_preps maps
    covered body -> (prep, q_map) for the q_zero posture. Any miss = ok
    False (driver refuses palmar_axis_fk_failed)."""
    bodies = model[0]
    rows = {}
    ok = True
    for name in COVERED_BODIES:
        prep0, q_map0 = base_preps[name]
        jn, _axis, rng = bodies[name]["joints"][0]
        theta_p = 0.1 * SIGN_TABLE[name]
        lo, hi = rng
        if not (lo - 1e-12 <= (q_map0.get(jn, 0.0) + theta_p)
                <= hi + 1e-12):
            theta_p = -theta_p
        q2 = dict(q_map0)
        q2[jn] = q_map0.get(jn, 0.0) + theta_p
        pos2, rot2, _ = iv.fk_frames(bodies, model[2], q2)
        origin2 = pos2[name]
        far2 = max(
            (iv.add(pos2[name], iv.mat_vec(rot2[name], v))
             for v in model[3][name][0]),
            key=lambda v: iv.dist(v, origin2))
        origin0 = prep0.positions[name]
        far0 = max(prep0.world[name], key=lambda v: iv.dist(v, origin0))
        disp = iv.sub(far2, far0)
        dot = iv.dot(disp, tuple(pad_data[name]["a_b"]))
        good = dot > 0.0
        rows[name] = dict(theta=theta_p, dot=dot, ok=bool(good))
        ok = ok and good
    return dict(ok=bool(ok), rows=rows)


# ---------------------------------------------------------------------------
# the pad scan: FULL pass over all vertices of one body at one placement;
# deepest depth among pad-covered vertices and among non-covered vertices
# separately (the anti-masking law: the deepest inside vertex must be a
# covered one, else the body is refused at the patch)
# ---------------------------------------------------------------------------
def pad_scan_verts(world, mask, normals_world, a_b, o, u):
    R, hh = iv.TRUNK_R, iv.TRUNK_H / 2.0
    d_cov = None
    wit = None
    wit_na = None
    d_ncov = None
    for i in range(len(world)):
        s = iv.cyl_sdf(iv.cyl_to_local(world[i], o, u), R, hh)
        if s >= 0.0:
            continue
        d = -s
        if mask[i]:
            if d_cov is None or d > d_cov:
                d_cov = d
                wit = i
                wit_na = iv.dot(normals_world[i], a_b)
        else:
            if d_ncov is None or d > d_ncov:
                d_ncov = d
    return dict(d_covered_max=d_cov, witness=wit, witness_na=wit_na,
                d_noncovered_max=d_ncov)


def pad_scan(prep, pad_data, name, o, u):
    pd = pad_data[name]
    return pad_scan_verts(prep.world[name], pd["mask"], pd["normals_world"],
                          pd["a_b"], o, u)


# ---------------------------------------------------------------------------
# the admission classification (pinned prereg G-4 + the amendment's honest
# band split; classes recorded per row, never merged into bone classes)
#   PAD_NO_CONTACT      d_cov <= pi_c            (no proven failure remains)
#   PAD_ABSORBED        pi_c < d_cov < t         (u = 0: the bone sits inside
#                        the pad's FREE thickness - the pad outer surface has
#                        not reached the trunk; no force)
#   PAD_CONTACT         t <= d_cov <= t+u_max    (u = d_cov - t in [0, u_max])
#   PAD_REFUSED_DEPTH   d_cov > t + u_max        (the window is exceeded)
#   PAD_REFUSED_PATCH   the deepest inside vertex is NON-covered (a dorsal or
#                        otherwise uncovered crossing is never absorbed)
# The row's sealed failure is SUBSTITUTED iff the class is PAD_ABSORBED or
# PAD_CONTACT (the pad-satisfied classes).
# ---------------------------------------------------------------------------
def classify_pad(scan):
    dc = scan["d_covered_max"]
    dn = scan["d_noncovered_max"]
    if dc is None or dc <= WINDOW_LO:
        return ("PAD_NO_CONTACT", None)
    if dn is not None and dn > dc:
        return ("PAD_REFUSED_PATCH", None)
    if dc > WINDOW_HI:
        return ("PAD_REFUSED_DEPTH", None)
    if dc < T:
        return ("PAD_ABSORBED", 0.0)
    return ("PAD_CONTACT", dc - T)


PAD_SATISFIED = ("PAD_ABSORBED", "PAD_CONTACT")


def pad_force_column(u, area):
    """VPL-1-FORCE: DECLARED-MODEL-FORCE (CONDITIONAL-CALCULATION under the
    declared mapping; never an actuator, solver input, or action channel)."""
    return K * (u / T) * area


# ---------------------------------------------------------------------------
# the extended battery: sealed C1-C3 (gs.light_gate on the sealed table)
# plus C6-C10 constructed here (frozen truths in control_input_table_vpl1)
# ---------------------------------------------------------------------------
def _translate_world(prep, name, delta):
    return [iv.add(v, delta) for v in prep.world[name]]


def _bisect_pad_depth(prep, pad_data, name, base_delta, radial, d_target,
                      iters=60):
    """Bisect the translation magnitude along -radial (toward the cylinder)
    from the base pose until the deepest covered bone-vertex depth equals
    d_target (the constructed truth is the bone geometry itself; the pad
    reading is then the model under test). Returns (delta, final_scan)."""
    lo, hi = 0.0, 0.2
    world0 = _translate_world(prep, name, base_delta)

    def depth_at(delta):
        moved = [iv.add(v, iv.scale(radial, -delta)) for v in world0]
        pd = pad_data[name]
        return pad_scan_verts(moved, pd["mask"], pd["normals_world"],
                              pd["a_b"], (0.0, 0.0, 0.0), (0.0, 0.0, 1.0))

    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        sc = depth_at(mid)
        d = sc["d_covered_max"]
        if d is None or d < d_target:
            lo = mid
        else:
            hi = mid
    delta = 0.5 * (lo + hi)
    return delta, depth_at(delta)


def vpl1_battery(model, prep_zero, pad_data, vtable, sealed_light):
    """C6-C10. prep_zero = q_zero prep; the constructions use the sealed C1
    base translation then rigid translations along the sealed radial.
    sealed_light = the sealed C1-C3 result (gs.light_gate on the sealed
    table). Returns the C6-C10 result dict; any misclassification sets ok
    False with a named failure."""
    o, uax = (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)
    res = dict(schema="chimera.hand_remediation.vpl1_battery.v1",
               controls={}, ok=True, failures=[])
    c1_tr = tuple(vtable["c1_translation"])
    radial = tuple(vtable["c2_c3_radial"])

    # ---- C6 PAD-INDENT: deepest covered vertex depth D = 3.0e-3 m ->
    # expected PAD_CONTACT with u = D - t = 1.0e-3 m (amendment C6 law).
    c6 = vtable["c6"]
    delta6, scan6 = _bisect_pad_depth(prep_zero, pad_data, c6["body"],
                                      c1_tr, radial, c6["d_target"])
    cls6, u6 = classify_pad(scan6)
    exp_u = c6["d_target"] - T
    good6 = (cls6 == "PAD_CONTACT" and u6 is not None
             and abs(u6 - exp_u) <= iv.TAU
             and scan6["witness"] is not None)
    res["controls"]["C6"] = dict(
        expected="PAD_CONTACT u=%r" % exp_u, cls=cls6, u=u6,
        d_covered_max=scan6["d_covered_max"],
        witness=scan6["witness"], witness_na=scan6["witness_na"],
        delta=delta6, ok=bool(good6))
    if not good6:
        res["failures"].append("C6 classified %s u=%r" % (cls6, u6))
        res["ok"] = False

    # ---- C7 OVER-COMPRESSION: D = 5.0e-3 > window -> PAD_REFUSED_DEPTH.
    c7 = vtable["c7"]
    delta7, scan7 = _bisect_pad_depth(prep_zero, pad_data, c7["body"],
                                      c1_tr, radial, c7["d_target"])
    cls7, _u7 = classify_pad(scan7)
    good7 = cls7 == "PAD_REFUSED_DEPTH"
    res["controls"]["C7"] = dict(expected="PAD_REFUSED_DEPTH", cls=cls7,
                                 d_covered_max=scan7["d_covered_max"],
                                 ok=bool(good7))
    if not good7:
        res["failures"].append("C7 classified %s" % cls7)
        res["ok"] = False

    # ---- C8 ANTI-MASKING: the C6 tip pose AND midph2 intruded 2.0e-3 m
    # past its exact tangency (the sealed C2->C3 construction pattern:
    # measure the body's exact distance to the cylinder, then translate
    # inward by d0 + inward): expected PAD_CONTACT on the tip AND
    # GENUINE_PENETRATION on the non-covered body. THE F1 TRIGGER: any other
    # class = instrument_invalid_pad_masks_bone.
    c8 = vtable["c8"]
    frames_zero, _, _, _ = gs.frames_at(model, {jn: 0.0 for jn in model[1]})
    base_mid = frames_zero[c8["body"]]
    moved_base = iv.translate_frame(base_mid, c1_tr)
    sc_mid = iv.adjudicate_body_vs_cylinder(moved_base, o, uax, iv.TAU)
    if sc_mid["class"] != "CLEAR":
        res["failures"].append("C8 base %s not CLEAR: %s"
                               % (c8["body"], sc_mid["class"]))
        res["ok"] = False
    d0_mid = iv.body_cyl_exact_distance(moved_base, o, uax)
    sphere_c = moved_base.sphere_center
    rad_m = iv.sub(sphere_c, iv.scale(uax, iv.dot(sphere_c, uax)))
    rn = iv.norm(rad_m)
    rad_m = iv.scale(rad_m, 1.0 / rn) if rn > 0.0 else radial
    moved_mid = iv.translate_frame(
        moved_base, iv.scale(rad_m, -(d0_mid + c8["inward"])))
    r_mid = iv.adjudicate_body_vs_cylinder(moved_mid, o, uax, iv.TAU)
    good8 = (cls6 == "PAD_CONTACT" and r_mid["class"] == "GENUINE_PENETRATION"
             and r_mid["depth"] is not None
             and r_mid["depth"] <= c8["inward"] + 1.0e-3)
    res["controls"]["C8"] = dict(
        expected="PAD_CONTACT(tip) AND GENUINE_PENETRATION(%s ~2mm)"
        % c8["body"], tip_cls=cls6, body=c8["body"],
        body_cls=r_mid["class"], body_depth=r_mid["depth"], ok=bool(good8))
    if not good8:
        res["failures"].append(
            "C8 anti-masking: tip=%s body=%s depth=%r"
            % (cls6, r_mid["class"], r_mid["depth"]))
        res["ok"] = False

    # ---- C9 PAD-FREE: at the C1 separated scene, zero pad rows.
    c9_rows = 0
    for name in COVERED_BODIES:
        scan9 = pad_scan_verts(_translate_world(prep_zero, name, c1_tr),
                               pad_data[name]["mask"],
                               pad_data[name]["normals_world"],
                               pad_data[name]["a_b"], o, uax)
        cls9, _ = classify_pad(scan9)
        if cls9 in PAD_SATISFIED:
            c9_rows += 1
    good9 = c9_rows == 0
    res["controls"]["C9"] = dict(expected="zero pad rows", pad_rows=c9_rows,
                                 ok=bool(good9))
    if not good9:
        res["failures"].append("C9 pad rows %d" % c9_rows)
        res["ok"] = False

    # ---- C10 MEASURED-STIFFNESS IDENTITY (amendment-1 section 4): the
    # declared mapping reproduces F = K_eff * u exactly at the four measured
    # depths; plus the recorded mask-area validation column (declared
    # expectation within 2x of A_thumb; a FINDING if outside, never a re-tune).
    c10 = vtable["c10"]
    c10_rows = []
    good10 = True
    for u_x, f_exp in zip(C10_DEPTHS, C10_FORCES):
        f_got = pad_force_column(u_x, A_THUMB)
        rel = abs(f_got - f_exp) / f_exp
        good10 = good10 and rel <= 1e-12
        c10_rows.append(dict(u_m=u_x, expected_N=f_exp, got_N=f_got,
                             rel_err=rel))
    area_ratio = pad_data["distal_thumb"]["mask_area_m2"] / A_THUMB
    area_ok = 0.5 <= area_ratio <= 2.0
    res["controls"]["C10"] = dict(
        expected="F=K_eff*u at %r" % (list(C10_DEPTHS),), rows=c10_rows,
        ok=bool(good10), mask_area_m2=pad_data["distal_thumb"]["mask_area_m2"],
        mask_area_over_declared=area_ratio,
        mask_area_within_declared_2x=bool(area_ok))
    if not good10:
        res["failures"].append("C10 identity failed")
        res["ok"] = False
    if not area_ok:
        res["failures"].append(
            "C10 mask area ratio %.6f outside declared 2x (FINDING)"
            % area_ratio)
        res["ok"] = False
    res["sealed_light_gate_c1_c3_ok"] = sealed_light["ok"]
    if not sealed_light["ok"]:
        res["ok"] = False
        res["failures"].append("sealed C1-C3 light gate failed")
    return res
