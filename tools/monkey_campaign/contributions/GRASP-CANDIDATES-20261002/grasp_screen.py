# grasp_screen.py - the grasp-candidates chain-stop-1 CHEAP GEOMETRIC SCREEN.
# Lane wk-grasp-candidates, E:/ChimeraWork/monkey-coordination/grasp-candidates/.
#
# FROZEN DESIGN: CANDIDATE_FORMULATION.md,
# sha256 0c24657de95068eb7499c3b9f140b8467f58e5ba6bcc94d02c69207341dbd1b1,
# verified at run; drift = refusal (the formulation is the screen law and is
# frozen BEFORE this run; no constant below is tuned after results).
#
# REUSED INSTRUMENT (merged verdict #323, VALID): instrument_v2.py shipped
# BYTE-IDENTICAL in this directory (sha256
# 9514c5b15a27948c65563070f16dffee4a5a28347c281a5d7e255fe93e516ddd, verified
# equal to the FINAL sealed implementation, seal
# ee7c1a24bfb343519e3b03b7a62644d1, manifest
# beb077ed7ba78aa27abc163ce2e27cd8d3d4de4d442f584cbb05bb0df0c1c477,
# job dac7d830d1cf4daf83df2db4fec5f38a PASSED). It is imported, not edited;
# every exact primitive, frozen constant and the input gate come from it.
#
# TAXONOMY (formulation section 1): T1 joint origins (certified A05 q=0 body
# origins, FK at q) vs T2 mesh surfaces (19 pinned STLs + hand.vtp envelope
# at their placement transforms) vs T3 contact points (Level-2-established
# surface meetings within tau / pi_c only). The GP1-CC3 v1 failure class:
# placements built on T1 (origins ON the cylinder, h_len ~ 2.06e-6 m at q_c)
# forced T2 through the solid and asserted T3 where T1 sat. Family v2.0
# builds the offset on T2 (mesh-tangency solve) and decides T3 only by
# adjudication. The v1 chord gate is ABOLISHED: chord is recorded, gated by
# nothing.
#
# Screens (formulation section 3): light validity gate C1/C2/C3 (frozen
# control table, byte-identical in-package copy) -> S0 vertex-envelope offset
# solve + sound per-bone rejection -> S3 reach/lawfulness -> S1 exact Level-2
# (capped per posture and by a declared cumulative wall-clock budget) ->
# survivors. Anchor envelope: recorded, never merged. Serial, deterministic.

import hashlib
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import instrument_v2 as iv  # the merged, sealed instrument (unmodified)

FORMULATION_SHA256 = (
    "0c24657de95068eb7499c3b9f140b8467f58e5ba6bcc94d02c69207341dbd1b1")
FORMULATION_PATH = ("E:/ChimeraWork/monkey-coordination/grasp-candidates/"
                    "CANDIDATE_FORMULATION.md")
CONTROL_TABLE_NAME = "control_input_table.json"
CONTROL_TABLE_SHA256 = (
    "d8aacc23b27e2caaf60304c0e9a4fe711ac51245c0ca3bf6d021d8f7b5164bf2")
INSTRUMENT_SHA256 = (
    "9514c5b15a27948c65563070f16dffee4a5a28347c281a5d7e255fe93e516ddd")

# frozen screen constants (formulation section 3; NOTHING here overrides the
# instrument's own frozen TAU / PI_C / R / HH)
N_THETA = 720                    # the sealed GP1-CC3 axis resolution, reused
N_MIRROR = 2
S_BRACKET_LO = 0.0               # declared offset bracket [m]
S_BRACKET_HI = 0.15
CAP_S1_PER_POSTURE = 96          # declared S1 cap per posture
S1_TIME_BUDGET_S = 2.5 * 3600.0  # declared cumulative S1 wall-clock budget
DET_SLICE_AXES = 8               # declared determinism slice: first 8 axes
                                 # per posture re-solved and byte-compared
AXIS_FAMILY_CHECK_AXES = 8       # declared axis-identity check against the
                                 # sealed iv.placement_family construction

ANCHOR = "macaque_hand_anchor"


# the declared posture set with GP1 contact pairs (formulation section 2).
# q maps: the sealed GP1 constants (iv.Q_C_PRIMARY / iv.Q_C_FALLBACKS) plus
# the zero control. Fallbacks inherit their non-declared joints at 0 exactly
# as the GP1 declared 6-joint subboxes.
def posture_maps(joints_by_name):
    zero = {jn: 0.0 for jn in joints_by_name}

    def with_zero(sub):
        q = dict(zero)
        q.update(sub)
        return q

    return [
        ("q_c_PRIMARY", with_zero(iv.Q_C_PRIMARY),
         ("distal_thumb", "distph3")),
        ("q_zero_CONTROL", zero, ("distal_thumb", "distph3")),
        ("F1", with_zero(iv.Q_C_FALLBACKS["F1"]),
         ("distal_thumb", "distph4")),
        ("F2", with_zero(iv.Q_C_FALLBACKS["F2"]),
         ("distal_thumb", "distph5")),
        ("F3", with_zero(iv.Q_C_FALLBACKS["F3"]),
         ("distal_thumb", "distph2")),
    ]


_report = []


def emit(line=""):
    _report.append(line)
    print(line, flush=True)


def sha_of(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def canonical(x):
    return json.dumps(x, indent=1, sort_keys=True)


# ---------------------------------------------------------------------------
# model construction (in-substance reuse of the sealed run_instrument_v2
# build_model/frames_at, source-noted; primitives all from instrument_v2)
# ---------------------------------------------------------------------------

def build_model():
    mut, bodies, joints_by_name, anchor_name, worst = iv.parse_hand_model(
        iv.A05_PATH, iv.A05_XML_PATH)
    stl_local = {}
    sphere_locals = {}
    for name in sorted(bodies):
        if name == anchor_name:
            continue
        geom = next(bb for bb in mut["bodies"]
                    if bb["name"] == name)["geometry"]
        pin = [g["stl_sha256"] for g in geom if "stl_sha256" in g][0]
        path = None
        for k in iv.STL_NAMES:
            fp = iv.VENDOR_MESHES + k + ".stl"
            if iv.sha256_file(fp) == pin:
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
    return (bodies, joints_by_name, anchor_name, stl_local, sphere_locals,
            (pts, tris), bounds)


def frames_at(model, q_map):
    (bodies, joints_by_name, anchor_name, stl_local, sphere_locals,
     vtp_local, bounds) = model
    positions, rotations, joint_records = iv.fk_frames(bodies, anchor_name,
                                                       q_map)
    frames = iv.build_hand_frames(bodies, stl_local, positions, rotations,
                                  sphere_locals, anchor_name, vtp_local)
    return frames, positions, rotations, joint_records


# ---------------------------------------------------------------------------
# the LIGHT validity gate (C1/C2/C3 from the frozen control table; the
# constructions copied in substance from the sealed run_control_battery,
# which certified C4/C5 in the merged battery - not exercised here)
# ---------------------------------------------------------------------------

def light_gate(model, table):
    (bodies, joints_by_name, anchor_name, stl_local, sphere_locals,
     vtp_local, bounds) = model
    o, u = (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)
    res = dict(schema="chimera.grasp_candidates.light_gate.v1",
               controls={}, ok=True, failures=[])
    zero = {jn: 0.0 for jn in joints_by_name}
    frames1, _, _, _ = frames_at(model, zero)
    moved1 = {n: iv.translate_frame(f, tuple(table["c1"]["translation"]))
              for n, f in frames1.items()}
    zero_flags = True
    all_clear = True
    for name in sorted(moved1):
        r = iv.adjudicate_body_vs_cylinder(moved1[name], o, u, iv.TAU)
        if r["level1"]["flag"]:
            zero_flags = False
        if r["class"] != "CLEAR":
            all_clear = False
    res["controls"]["C1"] = dict(expected="zero flags, all CLEAR",
                                 zero_flags=zero_flags, all_clear=all_clear)
    if not (zero_flags and all_clear):
        res["failures"].append("C1 misclassified")
        res["ok"] = False
    c23 = table["c2_c3"]
    base = moved1[c23["target_body"]]
    radial = tuple(c23["radial"])
    f_c2 = iv.translate_frame(
        base, tuple(-c23["t_touch"] * radial[k] for k in range(3)))
    r2 = iv.adjudicate_body_vs_cylinder(f_c2, o, u, iv.TAU)
    res["controls"]["C2"] = dict(expected="TOUCHING", cls=r2["class"],
                                 d=r2["d"])
    if r2["class"] != "TOUCHING":
        res["failures"].append("C2 classified %s" % r2["class"])
        res["ok"] = False
    f_c3 = iv.translate_frame(f_c2, tuple(c23["gross_translation"]))
    r3 = iv.adjudicate_body_vs_cylinder(f_c3, o, u, iv.TAU)
    res["controls"]["C3"] = dict(expected="GENUINE_PENETRATION ~5mm",
                                 cls=r3["class"], depth=r3["depth"])
    if r3["class"] != "GENUINE_PENETRATION" or r3["depth"] is None \
            or r3["depth"] < 4.0e-3:
        res["failures"].append("C3 classified %s depth %r"
                               % (r3["class"], r3["depth"]))
        res["ok"] = False
    res["control_input_table_sha256"] = CONTROL_TABLE_SHA256
    return res


# ---------------------------------------------------------------------------
# per-posture precomputation (world geometry at q; T1 origins, T2 surfaces)
# ---------------------------------------------------------------------------

class PosturePrep(object):
    pass


def prepare_posture(model, q_map, contact_pair):
    (bodies, joints_by_name, anchor_name, stl_local, sphere_locals,
     vtp_local, bounds) = model
    # S3-REACH (i): every q component within its certified A05 joint range
    # (refusal otherwise; recorded per posture)
    reach_rows = {}
    for jn, axis, rng in bodies[anchor_name]["joints"]:
        qv = 0.0  # the wrist joints at the GP1 sealed value (0)
        okj = (rng[0] - 1e-12) <= qv <= (rng[1] + 1e-12)
        reach_rows[jn] = dict(q=qv, range=list(rng), lawful=bool(okj))
        if not okj:
            iv.refuse("posture_outside_certified_ranges",
                      jn + " wrist q=0 vs range %r" % (rng,))
    for bname in sorted(bodies):
        for jn, axis, rng in bodies[bname]["joints"]:
            qv = q_map.get(jn)
            if qv is None:
                iv.refuse("input_pin_missing", "q component missing " + jn)
            okj = (rng[0] - 1e-12) <= qv <= (rng[1] + 1e-12)
            reach_rows[jn] = dict(q=qv, range=list(rng), lawful=bool(okj))
            if not okj:
                iv.refuse("posture_outside_certified_ranges",
                          jn + " q=%r vs range %r" % (qv, rng))
    positions, rotations, _ = iv.fk_frames(bodies, anchor_name, q_map)
    prep = PosturePrep()
    prep.contact_pair = contact_pair
    # T1: the certified tip JOINT ORIGINS at q (fk_origin; the v1 family's
    # construction points - used here ONLY as the anchor of the axis family
    # and for the recorded chord, NEVER as contact points)
    prep.a = iv.fk_origin(bodies, anchor_name, q_map, contact_pair[0])
    prep.b = iv.fk_origin(bodies, anchor_name, q_map, contact_pair[1])
    prep.m = iv.scale(iv.add(prep.a, prep.b), 0.5)
    prep.chord = iv.dist(prep.a, prep.b)
    prep.vh = iv.scale(iv.sub(prep.b, prep.a), 1.0 / prep.chord)
    prep.positions = positions
    prep.rotations = rotations
    prep.reach_rows = reach_rows
    # T2: world vertices per bone (scaled local verts at the FK transform)
    prep.world = {}
    prep.sphere_w = {}
    for name in sorted(bodies):
        c, r = sphere_locals[name]
        prep.sphere_w[name] = (iv.add(positions[name],
                                      iv.mat_vec(rotations[name], c)), r)
        if name == anchor_name:
            continue
        verts, _ = stl_local[name]
        prep.world[name] = [iv.add(positions[name],
                                   iv.mat_vec(rotations[name], v))
                            for v in verts]
    # per-posture p = v - m and |p|^2 about the chord midpoint anchor
    prep.p = {}
    prep.p2 = {}
    m = prep.m
    for name in prep.world:
        pw = []
        p2w = []
        for v in prep.world[name]:
            d = iv.sub(v, m)
            pw.append(d)
            p2w.append(iv.dot(d, d))
        prep.p[name] = pw
        prep.p2[name] = p2w
    prep.bones = sorted(n for n in bodies if n != anchor_name)
    prep.tips = list(contact_pair)
    prep.frames = frames_at(model, q_map)[0]
    return prep


# ---------------------------------------------------------------------------
# the sealed GP1-CC3 axis enumeration REUSED VERBATIM (minus the abolished
# chord gate); identity with iv.placement_family is CHECKED at run on the
# q_zero control (same u/w/theta/m construction) over the declared slice
# ---------------------------------------------------------------------------

def axis_basis(prep, k, mirror):
    vh = prep.vh
    helper = (0.0, 0.0, 1.0) if abs(vh[2]) < 0.9 else (0.0, 1.0, 0.0)
    e1 = iv.unit(iv.cross(vh, helper))
    e2 = iv.cross(vh, e1)
    theta = 2.0 * math.pi * k / N_THETA
    u = iv.add(iv.scale(e1, math.cos(theta)), iv.scale(e2, math.sin(theta)))
    w_base = iv.unit(iv.cross(vh, u))
    w = w_base if mirror == 0 else iv.scale(w_base, -1.0)
    return u, w, theta


def solve_s_star(prep, u, w):
    """Mesh-tangency offset (T2 law): s* = max over the two tip meshes'
    vertices of the larger root s_v+ = B + sqrt(R^2 - A + B^2), with
    p = v - m, A = |perp_u p|^2, B = p.w. For s > s* every tip vertex is
    outside the unshrunk solid; at s* at least one tip VERTEX (a surface
    point) lies exactly on the analytic surface. Returns
    (s_star or None, n_roots, winning body)."""
    R = iv.TRUNK_R
    best = None
    best_body = None
    n_roots = 0
    for tb in prep.tips:
        pw = prep.p[tb]
        p2w = prep.p2[tb]
        for i in range(len(pw)):
            p = pw[i]
            up = iv.dot(u, p)
            A = p2w[i] - up * up
            B = iv.dot(w, p)
            disc = R * R - A + B * B
            if disc > 0.0:
                n_roots += 1
                s = B + math.sqrt(disc)
                if best is None or s > best:
                    best = s
                    best_body = tb
    if best is None:
        return None, 0, None
    return best, n_roots, best_body


def scan_bone_vertices(prep, name, o, u):
    """Sound vertex scan of one Level-1-flagged bone at the candidate offset.
    Soundness: a mesh vertex is a surface point; a vertex inside the shrunk
    solid (R - tau, H/2 - tau) proves mesh penetration beyond tau (the
    instrument's own GENUINE criterion); a tip vertex deeper than pi_c in
    the unshrunk solid proves surface depth beyond the contact allowance.
    Early-exits on the first proven event; otherwise VERTEX_UNKNOWN (surface
    may dip between vertices - deferred to S1, never guessed)."""
    R, hh = iv.TRUNK_R, iv.TRUNK_H / 2.0
    tau, pi_c = iv.TAU, iv.PI_C
    is_tip = name in prep.contact_pair
    wv = prep.world[name]
    for i in range(len(wv)):
        la = iv.cyl_to_local(wv[i], o, u)
        if iv.cyl_sdf(la, R - tau, hh - tau) < 0.0:
            d0 = -iv.cyl_sdf(la, R, hh)
            if is_tip:
                if d0 > pi_c:
                    return dict(kind="TIP_DEEP", depth=d0)
            else:
                return dict(kind="PENETRATED", depth=d0)
    return dict(kind="VERTEX_UNKNOWN", worst_depth=None)


def classify_placement_bones(exact_state, contact_pair):
    """The merged declaration's pass predicate, unchanged: every NON-contact
    bone CLEAR; each declared contact segment TOUCHING (d >= -pi_c holds by
    the instrument's TOUCHING construction) or GENUINE with depth <= pi_c.
    Off-surface points are never counted: a tip CLEAR is NO contact."""
    contact = set(contact_pair)
    for name in sorted(exact_state):
        st = exact_state[name]
        cls = st["cls"]
        if name in contact:
            if cls == "GENUINE_PENETRATION":
                if st["depth"] is None or st["depth"] > iv.PI_C:
                    return ("REJECT", "S2_REJECT_DEEP:" + name)
            elif cls == "CLEAR":
                return ("REJECT", "S2_REJECT_NO_CONTACT:" + name)
        else:
            if cls == "GENUINE_PENETRATION":
                return ("REJECT", "S1_REJECT_NONCONTACT_PENETRATE:" + name)
            if cls == "TOUCHING":
                return ("REJECT", "S1_REJECT_NONCONTACT_TOUCH:" + name)
    return ("SURVIVOR", None)


def screen_posture(model, prep, pname, s1_clock):
    counters = dict(
        axes_total=N_THETA * N_MIRROR,
        s0_reject_no_approach=0,
        s3_reject_bracket=0,
        s0_reject_clearance=0,
        s0_reject_tip_deep=0,
        s0_survivors=0,
        s0_only_cap=0,
        s0_only_timing_cap=0,
        s1_reject_noncontact_penetrate=0,
        s1_reject_noncontact_touch=0,
        s2_reject_no_contact=0,
        s2_reject_deep=0,
        survivors=0,
        s1_cells_run=0,
    )
    clearance_by_bone = {}
    rejects = []
    survivors = []
    s1_done = 0
    determinism_slice = []
    for k in range(N_THETA):
        for mirror in range(N_MIRROR):
            u, w, theta = axis_basis(prep, k, mirror)
            s_star, n_roots, win_body = solve_s_star(prep, u, w)
            if len(determinism_slice) < DET_SLICE_AXES:
                # slice cells record the RESOLVED quantities regardless of
                # the screen outcome (survivors are not required)
                determinism_slice.append([k, mirror, list(u), s_star])
            if s_star is None:
                counters["s0_reject_no_approach"] += 1
                rejects.append([k, mirror, "S0_REJECT_NO_APPROACH"])
                continue
            if s_star < S_BRACKET_LO or s_star > S_BRACKET_HI:
                counters["s3_reject_bracket"] += 1
                rejects.append([k, mirror, "S3_REJECT_BRACKET",
                                repr(s_star)])
                continue
            o = iv.add(prep.m, iv.scale(w, s_star))
            # S0-CLEARANCE: the instrument's own Level-1 sphere bound per
            # bone; not flagged => SOUND_CLEAR (certified, no triangles);
            # flagged => sound vertex scan.
            proven_bad = None
            unknown_bones = []
            bone_state = {}
            for name in prep.bones:
                (sc, sr) = prep.sphere_w[name]
                f_center = iv.cyl_sdf(iv.cyl_to_local(sc, o, u),
                                      iv.TRUNK_R, iv.TRUNK_H / 2.0)
                if f_center > sr:
                    bone_state[name] = dict(cls="SOUND_CLEAR", d=None,
                                            depth=None)
                    continue
                sc_res = scan_bone_vertices(prep, name, o, u)
                if sc_res["kind"] == "PENETRATED":
                    proven_bad = (name, "S0_REJECT_CLEARANCE",
                                  sc_res["depth"])
                    clearance_by_bone[name] = \
                        clearance_by_bone.get(name, 0) + 1
                    break
                if sc_res["kind"] == "TIP_DEEP":
                    proven_bad = (name, "S0_REJECT_TIP_DEEP",
                                  sc_res["depth"])
                    clearance_by_bone[name] = \
                        clearance_by_bone.get(name, 0) + 1
                    break
                unknown_bones.append(name)
            if proven_bad is not None:
                if proven_bad[1] == "S0_REJECT_CLEARANCE":
                    counters["s0_reject_clearance"] += 1
                else:
                    counters["s0_reject_tip_deep"] += 1
                rejects.append([k, mirror, proven_bad[1], proven_bad[0],
                                repr(proven_bad[2])])
                continue
            counters["s0_survivors"] += 1
            if s1_done >= CAP_S1_PER_POSTURE:
                counters["s0_only_cap"] += 1
                continue
            if s1_clock[0] >= S1_TIME_BUDGET_S:
                counters["s0_only_timing_cap"] += 1
                continue
            # S1: exact Level-2 on flagged bones (VERTEX_UNKNOWN bones and
            # BOTH declared contact segments, always)
            t0 = time.time()
            exact_state = {}
            for name in prep.bones:
                if name in bone_state and \
                        bone_state[name]["cls"] == "SOUND_CLEAR":
                    exact_state[name] = dict(cls="CLEAR", d=None, depth=None,
                                             how="level1_sound_clear")
            for name in sorted(set(unknown_bones) | set(prep.tips)):
                r = iv.adjudicate_body_vs_cylinder(prep.frames[name], o, u,
                                                   iv.TAU)
                exact_state[name] = dict(cls=r["class"], d=r["d"],
                                         depth=r["depth"], how="level2_exact")
            verdict, reason = classify_placement_bones(exact_state,
                                                       prep.contact_pair)
            s1_clock[0] += time.time() - t0
            s1_done += 1
            if verdict == "REJECT":
                if reason.startswith("S1_REJECT_NONCONTACT_PENETRATE"):
                    counters["s1_reject_noncontact_penetrate"] += 1
                elif reason.startswith("S1_REJECT_NONCONTACT_TOUCH"):
                    counters["s1_reject_noncontact_touch"] += 1
                elif reason.startswith("S2_REJECT_NO_CONTACT"):
                    counters["s2_reject_no_contact"] += 1
                elif reason.startswith("S2_REJECT_DEEP"):
                    counters["s2_reject_deep"] += 1
                rejects.append([k, mirror, reason])
                continue
            # SURVIVOR: full record. The anchor envelope's exact class is
            # RECORDED, NEVER merged (merged R2 law). Pad columns and pi_c
            # robustness recorded (never decisive at this stop).
            ares = iv.adjudicate_body_vs_cylinder(prep.frames[ANCHOR], o, u,
                                                  iv.TAU)
            tip_rows = {}
            pad_cols = {}
            for tb in prep.tips:
                st = exact_state[tb]
                tip_rows[tb] = dict(cls=st["cls"], d=st["d"],
                                    depth=st["depth"])
                # pad-orientation column (RECORDED, not gating;
                # formulation section 3): cos between the tip's distal
                # extent direction (origin -> farthest mesh vertex, world)
                # and the inward cylinder radial at the tip origin.
                origin = prep.positions[tb]
                far = max(prep.world[tb], key=lambda v: iv.dist(v, origin))
                dird = iv.unit(iv.sub(far, origin))
                rad = iv.sub(origin, o)
                rad = iv.sub(rad, iv.scale(u, iv.dot(rad, u)))
                rn = iv.norm(rad)
                if rn == 0.0:
                    pad_cols[tb] = None
                else:
                    pad_cols[tb] = iv.dot(dird, iv.scale(rad, -1.0 / rn))
            pi_variants = {}
            for pi_v in iv.PI_C_VARIANTS:
                ok_v = True
                for tb in prep.tips:
                    st = exact_state[tb]
                    if st["cls"] == "CLEAR":
                        ok_v = False
                    elif st["cls"] == "GENUINE_PENETRATION":
                        if st["depth"] is None or st["depth"] > pi_v:
                            ok_v = False
                pi_variants[repr(pi_v)] = ok_v
            survivors.append(dict(
                theta_index=k, theta=theta, mirror=mirror,
                s_star=s_star, chord_t1=prep.chord, u=list(u), w=list(w),
                o=list(o), winning_tip_body=win_body,
                tips=tip_rows, pad_cos=pad_cols,
                pi_c_variants_pass=pi_variants,
                anchor_envelope=dict(cls=ares["class"], d=ares["d"],
                                     depth=ares["depth"],
                                     flag=ares["level1"]["flag"]),
                bodies=sorted((n, exact_state[n]["cls"], exact_state[n]["d"],
                               exact_state[n]["depth"])
                              for n in exact_state),
            ))
            counters["survivors"] += 1
    # coverage: every (theta, mirror) axis produced exactly one recorded
    # outcome; assert the arithmetic both ways
    counted = (counters["s0_reject_no_approach"]
               + counters["s3_reject_bracket"]
               + counters["s0_reject_clearance"]
               + counters["s0_reject_tip_deep"]
               + counters["survivors"] + counters["s0_only_cap"]
               + counters["s0_only_timing_cap"]
               + counters["s1_reject_noncontact_penetrate"]
               + counters["s1_reject_noncontact_touch"]
               + counters["s2_reject_no_contact"]
               + counters["s2_reject_deep"])
    coverage_ok = (counted == counters["axes_total"]) and \
        (len(rejects) + len(survivors) + counters["s0_only_cap"]
         + counters["s0_only_timing_cap"] == counters["axes_total"])
    return dict(counters=counters,
                clearance_by_bone=dict(sorted(clearance_by_bone.items())),
                survivors=survivors,
                rejects=rejects,
                coverage_ok=coverage_ok,
                determinism_slice=determinism_slice)


def axis_family_identity_check(model):
    """Declared check: my axis construction is IDENTICAL to the sealed
    iv.placement_family construction (u, w, theta, m) on the q_zero control
    over the declared slice. The offset o is INTENTIONALLY different
    (v1: origins-on-cylinder h_len; v2: solved mesh tangency) - recorded,
    never merged into this check."""
    (bodies, joints_by_name, anchor_name, stl_local, sphere_locals,
     vtp_local, bounds) = model
    zero = {jn: 0.0 for jn in joints_by_name}
    prep = prepare_posture(model, zero, ("distal_thumb", "distph3"))
    fam = iv.placement_family(prep.a, prep.b, n_theta=N_THETA)
    ok = True
    cells = 0
    for pl in fam:
        if pl["theta_index"] >= AXIS_FAMILY_CHECK_AXES:
            break
        u2, w2, theta2 = axis_basis(prep, pl["theta_index"], pl["mirror"])
        same = (canonical([u2, w2, theta2, prep.m])
                == canonical([pl["u"], pl["w"], pl["theta"],
                              iv.scale(iv.add(prep.a, prep.b), 0.5)]))
        ok = ok and same
        cells += 1
    return dict(cells=cells, ok=ok)


def pipeline():
    # ---- input identity (frozen design + reused instrument + its gate) ----
    fsha = sha_of(FORMULATION_PATH)
    if fsha != FORMULATION_SHA256:
        iv.refuse("formulation_sha_mismatch", fsha)
    isha = sha_of(os.path.join(HERE, "instrument_v2.py"))
    if isha != INSTRUMENT_SHA256:
        iv.refuse("instrument_copy_mismatch", isha)
    table_path = os.path.join(HERE, CONTROL_TABLE_NAME)
    tsha = sha_of(table_path)
    if tsha != CONTROL_TABLE_SHA256:
        iv.refuse("control_input_table_mismatch", tsha)
    prereg_path = os.path.join(HERE, "PREREGISTRATION.md")
    gate, _mut, _stl_files, _bounds = iv.run_input_gate(prereg_path)
    emit("=" * 78)
    emit("GATE. formulation %s MATCH; instrument copy %s MATCH (merged FINAL"
         " seal); control table MATCH; inherited input gate ok=%s pins=%d."
         % (fsha[:16], isha[:16], gate["ok"], len(gate["pins"])))
    model = build_model()
    with open(table_path, "r", encoding="utf-8") as fh:
        table = json.load(fh)
    lg = light_gate(model, table)
    emit("LIGHT GATE C1/C2/C3 (in-situ, frozen table): ok=%s %s"
         % (lg["ok"], json.dumps(lg["controls"], sort_keys=True)))
    if not lg["ok"]:
        iv.refuse("instrument_invalid_in_situ", json.dumps(lg["failures"]))
    wit = iv.check_witness_identity(model[0], model[1], model[2])
    emit("WITNESS. sealed q_c(PRIMARY) FK reproduces the GP1 receipt tips and"
         " chord %r (T1 origins; refuse on drift)." % wit["chord"])
    afc = axis_family_identity_check(model)
    emit("AXIS FAMILY IDENTITY vs sealed iv.placement_family (q_zero slice):"
         " cells=%d identical=%s" % (afc["cells"], afc["ok"]))
    if not afc["ok"]:
        iv.refuse("axis_family_identity_failed", "q_zero slice")
    receipt = dict(
        schema="chimera.grasp_candidates.screen.v1",
        task="GRASP-CANDIDATES-20261002 chain stop 1 (cheap geometric screen"
             " of candidate family v2.0; taxonomy T1/T2/T3; chord gate"
             " abolished; NO sweep at this stop)",
        lane="E:/ChimeraWork/monkey-coordination/grasp-candidates/",
        formulation_sha256=fsha,
        instrument_copy_sha256=isha,
        control_input_table_sha256=tsha,
        instrument_preregistration_sha256=iv.PREREG_SHA256,
        instrument_declaration_sha256=iv.DECLARATION_SHA256,
        frozen_constants=dict(tau=iv.TAU, pi_c=iv.PI_C, r_joint=iv.R_JOINT,
                              scale=iv.SCALE, trunk_r=iv.TRUNK_R,
                              trunk_h=iv.TRUNK_H, n_theta=N_THETA,
                              n_mirror=N_MIRROR,
                              s_bracket=[S_BRACKET_LO, S_BRACKET_HI],
                              cap_s1_per_posture=CAP_S1_PER_POSTURE,
                              s1_time_budget_s=S1_TIME_BUDGET_S),
        input_gate=gate,
        witness_identity=wit,
        axis_family_identity=afc,
        light_gate=lg,
        postures={},
    )
    s1_clock = [0.0]
    pmaps = posture_maps(model[1])
    for (pname, q_map, pair) in pmaps:
        prep = prepare_posture(model, q_map, pair)
        emit("-" * 78)
        emit("POSTURE %s pair=%s chord(T1 origins)=%r m (RECORDED, no gate)."
             % (pname, pair, prep.chord))
        res = screen_posture(model, prep, pname, s1_clock)
        res["chord_t1"] = prep.chord
        res["tip_t1_origins"] = dict(thumb=list(prep.a),
                                     digit=list(prep.b))
        res["reach_all_lawful"] = all(v["lawful"]
                                      for v in prep.reach_rows.values())
        receipt["postures"][pname] = res
        emit("  counters: %s" % json.dumps(res["counters"], sort_keys=True))
        emit("  clearance/tip-deep rejects by bone: %s"
             % json.dumps(res["clearance_by_bone"], sort_keys=True))
        emit("  coverage_ok=%s survivors=%d"
             % (res["coverage_ok"], res["counters"]["survivors"]))
        if not res["coverage_ok"]:
            iv.refuse("coverage_arithmetic_broken", pname)
    # determinism slice: re-solve the recorded slice cells; byte-compare
    det_ok = True
    det_cells = 0
    for (pname, q_map, pair) in pmaps:
        prep = prepare_posture(model, q_map, pair)
        for (k, mirror, u, s_star) in \
                receipt["postures"][pname]["determinism_slice"]:
            u2, w2, _ = axis_basis(prep, k, mirror)
            s2, _nr, _wb = solve_s_star(prep, u2, w2)
            same = (canonical([u2, s2]) == canonical([u, s_star]))
            det_ok = det_ok and same
            det_cells += 1
    receipt["determinism_slice"] = dict(cells=det_cells, ok=det_ok)
    emit("DETERMINISM SLICE: %d cells re-solved byte-identical = %s"
         % (det_cells, det_ok))
    survivors_total = sum(receipt["postures"][p]["counters"]["survivors"]
                          for (p, _, _) in pmaps)
    if survivors_total > 0:
        receipt["verdict"] = "SURVIVORS_PRESENT_PROCEED_TO_PREREG_SWEEP_BRANCH"
    else:
        receipt["verdict"] = "ZERO_SURVIVORS_CHEAP_REJECTION_NO_SWEEP"
    receipt["s1_cumulative_clock_s"] = s1_clock[0]
    emit("=" * 78)
    emit("VERDICT: %s (survivors=%d)" % (receipt["verdict"], survivors_total))
    return receipt


def main():
    outdir = os.environ.get("CHIMERA_OUTPUT_DIR", "outputs")
    os.makedirs(outdir, exist_ok=True)
    try:
        receipt = pipeline()
        text = "\n".join(_report) + "\n"
    except iv.GateRefusal as exc:
        with open(os.path.join(outdir, "grasp_screen_gate_receipt.json"),
                  "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(dict(
                schema="chimera.grasp_candidates.gate.v1",
                ok=False, refusal=exc.detail), indent=1) + "\n")
        print("REFUSAL: %s" % exc.detail, flush=True)
        raise SystemExit(3)
    with open(os.path.join(outdir, "grasp_screen_receipt.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(canonical(receipt) + "\n")
    with open(os.path.join(outdir, "grasp_screen_report.txt"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
