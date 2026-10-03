# construct_controls.py - INSTRUMENT-V2 chain stop 2, job 1 of 2.
# Constructs the C1-C5 control scenes of the frozen declaration (section 4.1)
# and freezes them into outputs/control_input_table.json (declared --keep).
# The battery job (run_instrument_v2.py) pins this table by sha256 and refuses
# on drift; the constructed truths are frozen BEFORE any instrument run.
#
# Construction independence (declared honestly, declaration 4.1): C1-C3
# truths are rigid transforms, analytically known. C4/C5 attempt the
# kinematic fold first (a joint-angle scan for exact mesh-mesh overlap of an
# ADJACENT certified pair with ACTIVE - outside-the-joint-region - features);
# if no fold yields an active gross overlap within the certified ranges, the
# telescoping rigid construction of the same adjacent pair is used and
# labeled RIGID_PAIR_TRANSLATION. C4/C5 therefore validate the instrument's
# CLASSIFICATION LOGIC (screening, adjudication plumbing, class assignment,
# ledger scope), while primitive correctness rests on C1-C3, the closed-form
# cylinder cases, and independent Sergeant review.
# Stdlib only; deterministic; CPU only via the canonical runner.

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instrument_v2 as iv  # noqa: E402

OUT_NAME = "control_input_table.json"
FOLD_SCAN_N = 61
BISECT_ITERS = 60
C4_GROSS_MIN_DEPTH = 1.0e-3   # 10*tau: gross beyond the faceting column
C5_TELESCOPE_EXTRA = 3.0e-3   # gross telescoping depth for C4 fallback


def find_prereg():
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "PREREGISTRATION.md")
    if not os.path.isfile(p):
        p = os.path.join(os.getcwd(), "tools/monkey_campaign/contributions/"
                                      "INSTRUMENT-V2-20261002/PREREGISTRATION.md")
    if not os.path.isfile(p):
        iv.refuse("input_pin_missing", "committed prereg bytes not found")
    return p


def build_model():
    mut, bodies, joints_by_name, anchor_name, worst = iv.parse_hand_model(
        iv.A05_PATH, iv.A05_XML_PATH)
    stl_local = {}
    sphere_locals = {}
    for name in sorted(bodies):
        if name == anchor_name:
            continue
        stl_pins = [g["stl_sha256"] for g in
                    next(bb for bb in mut["bodies"]
                         if bb["name"] == name)["geometry"] if "stl_sha256" in g]
        path = None
        for k in iv.STL_NAMES:
            fp = iv.VENDOR_MESHES + k + ".stl"
            if iv.sha256_file(fp) == stl_pins[0]:
                path = fp
                break
        if path is None:
            iv.refuse("input_pin_missing", "stl for " + name)
        verts, tris = iv.parse_stl(path)
        stl_local[name] = (verts, tris)
        c, r = iv.bounding_sphere_scaled(verts)
        sphere_locals[name] = (c, r)
    bounds = mut["envelope_check"]["hand_vtp_bounds_m"]
    pts, tris, hist = iv.parse_vtp(iv.VTP_PATH)
    lo = [min(v[k] for v in pts) for k in range(3)]
    hi = [max(v[k] for v in pts) for k in range(3)]
    worst_v = max(max(abs(lo[k] - float(bounds[0][k])),
                      abs(hi[k] - float(bounds[1][k]))) for k in range(3))
    if worst_v > 1e-9:
        iv.refuse("input_pin_mismatch", "scaled VTP AABB worst %r" % worst_v)
    ac, ar = iv.anchor_bounds_sphere(bounds)
    sphere_locals[anchor_name] = (ac, ar)
    vtp_local = (pts, tris)
    return (mut, bodies, joints_by_name, anchor_name, stl_local,
            sphere_locals, vtp_local, bounds)


def hand_frames_at(bodies, stl_local, sphere_locals, vtp_local, anchor_name,
                   q_map):
    zero_wrist = (0.0, 0.0)
    positions, rotations, joint_records = iv.fk_frames(
        bodies, anchor_name, q_map, wrist=zero_wrist)
    frames = iv.build_hand_frames(bodies, stl_local, positions, rotations,
                                  sphere_locals, anchor_name, vtp_local)
    return frames, positions, rotations, joint_records


def zero_q(joints_by_name):
    return {jn: 0.0 for jn in joints_by_name}


# ---------------------------------------------------------------------------
# C1
# ---------------------------------------------------------------------------

def construct_c1(bodies, stl_local, sphere_locals, vtp_local, anchor_name):
    q0 = zero_q_full(joints_by_name_ref[0])
    frames, _, _, _ = hand_frames_at(bodies, stl_local, sphere_locals,
                                     vtp_local, anchor_name, q0)
    ac = frames[anchor_name].sphere_center
    target = (iv.TRUNK_R + iv.ANCHOR_R + 0.01, 0.0, 0.0)
    delta = iv.sub(target, ac)
    moved = {n: iv.translate_frame(f, delta) for n, f in frames.items()}
    # trunk: axis z through the origin
    o, u = (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)
    per_body = {}
    zero_flags = True
    all_clear = True
    for name in sorted(moved):
        res = iv.adjudicate_body_vs_cylinder(moved[name], o, u, iv.TAU)
        per_body[name] = dict(level1_flag=res["level1"]["flag"],
                              cls=res["class"], d=res["d"])
        if res["level1"]["flag"]:
            zero_flags = False
        if res["class"] != "CLEAR":
            all_clear = False
    if not zero_flags or not all_clear:
        iv.refuse("control_c1_construction_failed",
                  "zero_flags=%s all_clear=%s" % (zero_flags, all_clear))
    return dict(translation=list(delta), per_body=per_body,
                truth="separated: zero hand-trunk GENUINE_PENETRATION, zero "
                      "TOUCHING, zero Level-1 flags vs the trunk")


# ---------------------------------------------------------------------------
# C2/C3 (distal_thumb tangency + 5 mm gross intrusion)
# ---------------------------------------------------------------------------

def construct_c2c3(bodies, stl_local, sphere_locals, vtp_local, anchor_name,
                   c1):
    q0 = zero_q_full(joints_by_name_ref[0])
    frames, _, _, _ = hand_frames_at(bodies, stl_local, sphere_locals,
                                     vtp_local, anchor_name, q0)
    delta1 = tuple(c1["translation"])
    moved = {n: iv.translate_frame(f, delta1) for n, f in frames.items()}
    target_body = "distal_thumb"
    o, u = (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)
    base = moved[target_body]
    d0 = iv.body_cyl_exact_distance(base, o, u)
    if d0 <= iv.TAU:
        iv.refuse("control_c2_construction_failed", "d0 not clear: %r" % d0)
    c = base.sphere_center
    radial = iv.unit((c[0], c[1], 0.0))
    # bisect the tangency translation magnitude: predicate = surfaces touch or
    # intersect (exact distance 0)
    def touching_at(t):
        f = iv.translate_frame(base, scale_neg(radial, t))
        return iv.body_cyl_exact_distance(f, o, u) == 0.0
    lo, hi = 0.0, d0
    if touching_at(hi) is False:
        # grow until contact (should contact at ~d0)
        while not touching_at(hi) and hi < d0 * 4.0:
            hi += d0 / 8.0
    for _ in range(BISECT_ITERS):
        mid = (lo + hi) / 2.0
        if touching_at(mid):
            hi = mid
        else:
            lo = mid
    t_star = hi
    frame_c2 = iv.translate_frame(base, scale_neg(radial, t_star))
    d_touch = iv.body_cyl_exact_distance(frame_c2, o, u)
    frame_c3 = iv.translate_frame(frame_c2, scale_neg(radial, 5.0e-3))
    res3 = iv.adjudicate_body_vs_cylinder(frame_c3, o, u, iv.TAU)
    if res3["class"] != "GENUINE_PENETRATION" or \
            res3["depth"] is None or res3["depth"] < 4.0e-3:
        iv.refuse("control_c3_construction_failed",
                  "class=%s depth=%r" % (res3["class"], res3.get("depth")))
    return dict(target_body=target_body, d0=d0, radial=list(radial),
                t_touch=t_star, d_at_touch=d_touch,
                gross_translation=list(scale_neg(radial, 5.0e-3)),
                c3_measured_depth=res3["depth"],
                truth_c2="TOUCHING for distal_thumb (exact distance 0 within "
                         "tau); neither GENUINE_PENETRATION nor "
                         "PROXY_FALSE_POSITIVE",
                truth_c3="GENUINE_PENETRATION for distal_thumb, depth ~5 mm "
                         "(50*tau, constructed rigid intrusion)")


def scale_neg(v, t):
    return (v[0] * -t, v[1] * -t, v[2] * -t)


# ---------------------------------------------------------------------------
# C4/C5: articulated self-collision controls (fold scan first, telescoping
# rigid fallback second)
# ---------------------------------------------------------------------------

FOLD_CANDIDATES = [
    ("secondmc", "proxph2", "mcp2_flexion"),
    ("thirdmc", "proxph3", "mcp3_flexion"),
    ("firstmc", "proximal_thumb", "cmc_flexion"),
    ("proxph2", "midph2", "pm2_flexion"),
]


def pair_frames_at(model, q_map, names):
    """BodyFrames for ONLY the named bodies at q_map (scan-path optimization;
    the battery always builds the full hand)."""
    (_, bodies, joints_by_name, anchor_name, stl_local, sphere_locals,
     vtp_local, bounds) = model
    positions, rotations, joint_records = iv.fk_frames(bodies, anchor_name,
                                                       q_map)
    frames = {}
    for name in names:
        if name == anchor_name:
            frames[name] = iv.BodyFrame(
                name, vtp_local[0], vtp_local[1], positions[name],
                rotations[name], sphere_locals[name][0], sphere_locals[name][1],
                is_anchor=True, is_envelope=True)
        else:
            verts, tris = stl_local[name]
            frames[name] = iv.BodyFrame(
                name, verts, tris, positions[name], rotations[name],
                sphere_locals[name][0], sphere_locals[name][1])
    return frames


def pair_state(frames, na, nb, jc, r_joint, full_depth=False):
    """Compact active/overlap state of a pair at a configuration.
    Scan path: containment is computed only when crossing segments exist
    (the first contact of two disjoint comparable bones is a surface
    crossing; full containment is re-adjudicated completely by the battery).
    full_depth=True runs the complete contained-vertex scan."""
    segs = iv.mesh_pair_intersection_segments(frames[na], frames[nb])
    n_active = 0
    max_fd = 0.0
    for (p, q, ti, tj) in segs:
        fd = max(iv.dist(p, jc), iv.dist(q, jc))
        max_fd = max(max_fd, fd)
        if fd > r_joint:
            n_active += 1
    depth_a = []
    depth_b = []
    if segs or full_depth:
        depth_a = iv.contained_vertices_depth(frames[na], frames[nb])
        depth_b = iv.contained_vertices_depth(frames[nb], frames[na])
    active_depth = 0.0
    for (v, dep) in depth_a + depth_b:
        fd = iv.dist(v, jc)
        max_fd = max(max_fd, fd)
        if fd > r_joint:
            active_depth = max(active_depth, dep)
    if segs or depth_a or depth_b:
        if n_active == 0 and active_depth == 0.0:
            return dict(state="EXEMPT", max_fd=max_fd, active_depth=0.0)
        if active_depth > iv.TAU:
            return dict(state="GENUINE", max_fd=max_fd,
                        active_depth=active_depth)
        return dict(state="TOUCHING", max_fd=max_fd, active_depth=0.0)
    d = iv.mesh_pair_exact_distance(frames[na], frames[nb])
    return dict(state="CLEAR", d=d, max_fd=max_fd, active_depth=0.0)


def fold_scan(model, parent, child, joint):
    (_, bodies, joints_by_name, anchor_name, _, _, _, _) = model
    rng = joints_by_name[joint]["range"]
    best = None
    scan = []
    print("fold scan %s/%s via %s range %r" % (parent, child, joint, rng),
          flush=True)
    prev_active = None
    for i in range(FOLD_SCAN_N):
        qv = rng[0] + (rng[1] - rng[0]) * i / (FOLD_SCAN_N - 1)
        q0 = zero_q_full(joints_by_name)
        q0[joint] = qv
        frames = pair_frames_at(model, q0, [parent, child])
        child_origin = frames[child].pos
        st = pair_state(frames, parent, child, child_origin, iv.R_JOINT)
        st["q"] = qv
        scan.append(dict(q=qv, state=st["state"],
                         d=st.get("d"), active_depth=st.get("active_depth"),
                         max_fd=st.get("max_fd")))
        active_now = st["state"] in ("GENUINE", "TOUCHING")
        if st["state"] == "GENUINE" and \
                st["active_depth"] >= C4_GROSS_MIN_DEPTH:
            # bisect the active-contact boundary between the last inactive
            # scan point and this gross q for the C5 near-touch scene
            if prev_active is not None:
                lo, hi = prev_active, qv
                for _ in range(BISECT_ITERS):
                    mid = (lo + hi) / 2.0
                    qm = zero_q_full(joints_by_name)
                    qm[joint] = mid
                    fm = pair_frames_at(model, qm, [parent, child])
                    stm = pair_state(fm, parent, child, fm[child].pos,
                                     iv.R_JOINT)
                    if stm["state"] in ("GENUINE", "TOUCHING"):
                        hi = mid
                    else:
                        lo = mid
                q_touch = hi
            else:
                q_touch = None
            if q_touch is not None:
                return dict(mode="KINEMATIC_FOLD", joint=joint, q=qv,
                            q_touch=q_touch, state=st, scan=scan)
        if best is None and active_now:
            best = (st["state"], qv, st)
        if not active_now:
            prev_active = qv
    return dict(mode="KINEMATIC_FOLD_NONE", best=best, scan=scan)


def telescoping_construction(model, parent, child):
    """C4 construction: telescope the child bone into its certified parent
    until the overlap features OUTSIDE the declared joint region carry a
    gross constructed depth. The active features cross the r_joint sphere at
    a depth already far beyond tau at this geometry (measured), so no
    active-TOUCHING band exists on this path; C5 is constructed separately
    (near_touch_construction, non-adjacent pair, no exemption)."""
    (_, bodies, joints_by_name, anchor_name, _, _, _, _) = model
    q0 = zero_q_full(joints_by_name)
    frames = pair_frames_at(model, q0, [parent, child])
    fc = frames[child]
    fp = frames[parent]
    direction = iv.unit(iv.sub(fp.sphere_center, fc.sphere_center))
    jc = fc.pos

    def state_at(t):
        f = iv.translate_frame(fc, iv.scale(direction, t))
        fr2 = dict(frames)
        fr2[child] = f
        return pair_state(fr2, parent, child, jc, iv.R_JOINT)

    # scan outward for the first GROSS active overlap
    t_gross = None
    st_gross = None
    t = 0.0
    while t < 2.0e-2:
        st = state_at(t)
        if st["state"] == "GENUINE" and \
                st["active_depth"] >= C4_GROSS_MIN_DEPTH:
            t_gross = t
            st_gross = st
            break
        t += 5.0e-4
    if t_gross is None:
        return None
    return dict(mode="RIGID_PAIR_TRANSLATION", parent=parent, child=child,
                direction=list(direction), t_gross=t_gross,
                st_gross=st_gross)


C5_CANDIDATES = [
    ("proxph2", "proxph3"),
    ("midph3", "midph4"),
    ("proxph3", "proxph4"),
    ("midph2", "midph3"),
]


def near_touch_construction(model, na, nb):
    """C5 construction: a NON-ADJACENT pair at q = 0 with mesh-mesh distance
    within [0, tau] by constructed rigid translation of nb toward na
    (bisection on the exact distance; the achieved distance is frozen)."""
    (_, bodies, joints_by_name, anchor_name, _, _, _, _) = model
    q0 = zero_q_full(joints_by_name)
    frames = pair_frames_at(model, q0, [na, nb])
    fa, fb = frames[na], frames[nb]
    d0 = iv.mesh_pair_exact_distance(fa, fb)
    if d0 <= iv.TAU:
        return dict(kind="RIGID_TRANSLATION", pair=[na, nb],
                    translation=[0.0, 0.0, 0.0], d_start=d0, d_final=d0,
                    truth="mesh-mesh distance within [0, tau] at q = 0")
    direction = iv.unit(iv.sub(fa.sphere_center, fb.sphere_center))

    def dist_at(s):
        f = iv.translate_frame(fb, iv.scale(direction, s))
        fr2 = dict(frames)
        fr2[nb] = f
        return iv.mesh_pair_exact_distance(fr2[na], fr2[nb])

    target = iv.TAU / 2.0
    lo, hi = 0.0, d0
    if dist_at(hi) > target:
        return None
    for _ in range(BISECT_ITERS):
        mid = (lo + hi) / 2.0
        if dist_at(mid) <= target:
            hi = mid
        else:
            lo = mid
    s = hi
    d_final = dist_at(s)
    if d_final < 0.0 or d_final > iv.TAU:
        return None
    return dict(kind="RIGID_TRANSLATION", pair=[na, nb],
                translation=[direction[k] * s for k in range(3)],
                d_start=d0, d_final=d_final,
                truth="mesh-mesh distance within [0, tau] by constructed "
                      "rigid translation (bisection on the exact distance)")


joints_by_name_ref = [None]


def zero_q_full(joints_by_name):
    return {jn: 0.0 for jn in joints_by_name}


def main():
    outdir = os.environ.get("CHIMERA_OUTPUT_DIR", "outputs")
    os.makedirs(outdir, exist_ok=True)
    prereg = find_prereg()
    gate, mut, stl_files, bounds = iv.run_input_gate(prereg)
    model = build_model()
    (mut2, bodies, joints_by_name, anchor_name, stl_local, sphere_locals,
     vtp_local, bounds2) = model
    joints_by_name_ref[0] = joints_by_name

    print("== C1 ==")
    c1 = construct_c1(bodies, stl_local, sphere_locals, vtp_local, anchor_name)
    print("C1 constructed: zero flags, all CLEAR (truth frozen)")

    print("== C2/C3 ==")
    c2c3 = construct_c2c3(bodies, stl_local, sphere_locals, vtp_local,
                          anchor_name, c1)
    print("C2 tangency t=%r d=%r; C3 depth=%r"
          % (c2c3["t_touch"], c2c3["d_at_touch"], c2c3["c3_measured_depth"]))

    print("== C4/C5 ==")
    fold_result = None
    chosen = None
    for (parent, child, joint) in FOLD_CANDIDATES:
        res = fold_scan(model, parent, child, joint)
        if res["mode"] == "KINEMATIC_FOLD":
            chosen = dict(pair=[parent, child], **res)
            fold_result = dict(scanned=[parent, child, joint], found=True)
            break
        if fold_result is None:
            fold_result = dict(scanned=[parent, child, joint], found=False,
                               best=res.get("best"))
    if chosen is None:
        for (parent, child, _j) in FOLD_CANDIDATES:
            res = telescoping_construction(model, parent, child)
            if res is not None:
                chosen = dict(pair=[parent, child], **res)
                break
    if chosen is None:
        iv.refuse("control_c4c5_construction_failed",
                  "no fold or telescoping construction produced an active "
                  "gross overlap")
    print("C4/C5 construction mode:", chosen["mode"], "pair:", chosen["pair"])
    chosen["kind_c4"] = "gross_active_overlap"

    # C5: the near-touch construction (non-adjacent pair preferred: no
    # exemption applies and the declared truth is exactly mesh-mesh distance
    # within [0, tau])
    c5 = None
    if chosen["mode"] == "KINEMATIC_FOLD" and chosen.get("q_touch") is not None:
        c5 = dict(kind="FOLD_Q", pair=chosen["pair"], joint=chosen["joint"],
                  q=chosen["q_touch"],
                  truth="mesh-mesh distance within [0, tau] at the "
                        "constructed fold configuration")
    else:
        for (na, nb) in C5_CANDIDATES:
            c5 = near_touch_construction(model, na, nb)
            if c5 is not None:
                break
    if c5 is None:
        iv.refuse("control_c4c5_construction_failed",
                  "no near-touch construction landed within [0, tau]")
    print("C5 construction:", c5["kind"], c5["pair"],
          "d_final=%r" % c5.get("d_final"))

    table = dict(
        schema="chimera.instrument_v2.control_input_table.v1",
        frozen_before_instrument_runs=True,
        preregistration_sha256=iv.PREREG_SHA256,
        prereg_commit=iv.PREREG_COMMIT,
        declaration_sha256=iv.DECLARATION_SHA256,
        tau=iv.TAU, pi_c=iv.PI_C, r_joint=iv.R_JOINT,
        trunk=dict(R=iv.TRUNK_R, hh=iv.TRUNK_H / 2.0,
                   axis=(0.0, 0.0, 1.0), origin=(0.0, 0.0, 0.0)),
        construction_independence_note=(
            "C1-C3 truths are rigid transforms, analytically known. C4/C5 "
            "attempt the kinematic fold first; the fallback is the "
            "telescoping rigid translation of the same ADJACENT certified "
            "pair (labeled). The battery validates the classification logic "
            "(screening, adjudication plumbing, class assignment, ledger "
            "scope, sweep); primitive correctness rests on C1-C3, the "
            "closed-form cylinder cases, and independent Sergeant review."),
        c1=c1,
        c2_c3=c2c3,
        c4_c5=chosen,
        c5=c5,
        fold_probe=fold_result,
    )
    text = json.dumps(table, indent=1, sort_keys=True) + "\n"
    with open(os.path.join(outdir, OUT_NAME), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(text)
    print("control_input_table.json written; sha256:",
          iv.sha256_file(os.path.join(outdir, OUT_NAME)))
    raise SystemExit(0)


if __name__ == "__main__":
    try:
        main()
    except iv.GateRefusal as exc:
        outdir = os.environ.get("CHIMERA_OUTPUT_DIR", "outputs")
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "construct_gate_receipt.json"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(dict(
                schema="chimera.instrument_v2.gate.v1", ok=False,
                refusal=exc.detail), indent=1) + "\n")
        print("REFUSAL RECORDED: %s" % exc.detail)
        raise SystemExit(3)
