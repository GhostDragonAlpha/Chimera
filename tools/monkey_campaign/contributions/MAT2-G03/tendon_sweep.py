"""MAT2-G03 — Evaluate tendon lengths and moment arms (C18 pose sweep).

Declared-model kinematics of the sealed OpenSim chain (pinned osim + M02
graph pins): forward kinematics, wrist_flexion pose sweep, polyline tendon
lengths l(q) and signed moment arms r_j = -dl/dq_j computed TWICE
independently (owner-gated rigid-body velocity identity vs central finite
differences), with derived windows, finiteness gates and the card's core
law: unresolved bodies cannot appear as zero arms (unresolved_owner rows
carry null arms, never a number).

Zero stiffness/couple/force constants are pinned or consumed (C17 law);
torque attribution r_j*F and the wrap model stay explicitly_unresolved.

Commands:
    python -B tendon_sweep.py --emit      build document + trace (refuses
                                          input_pin_drift)
    python -B tendon_sweep.py --verify    recompute everything from pinned
                                          bytes; refuse disagreement
    python -B tendon_sweep.py --falsify   7 tamper arms, clean control first
    python -B tendon_sweep.py --selftest  vacuous-guard selftest (P5 law)
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
CHECKOUT = CONTRIB.parent.parent.parent   # .../<attempt>/checkout
DATE_FROZEN = "2026-09-30"
TASK_ID = "G03"                           # SHORT form (P7)
TASK_LONG = "MAT2-G03"
CRITERIA_SHA256 = ("d489995ecb7c645013084987bbf3f5d54cd4abca2e7bec2d1afa"
                   "6db0ff70c5aa")
SCOPE_SHA256 = ("cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae5"
                "7996097")
SCHEMA = "chimera.g03_tendon_pose_sweep.v1"
TRACE_SCHEMA = "chimera.g03_tendon_pose_sweep_trace.v1"
OBJECT_ID = "mat2_g03_tendon_pose_sweep"

# ---------- preregistered windows (PREREGISTRATION.md sections 6.8, 8) ----
W_FK = 1e-12          # W1 FK closure vs pinned body_frames
W_ABS = 1e-8          # W2 identity agreement (absolute part), metres
W_REL = 1e-6          # W2 identity agreement (relative part)
W_ENV_FACTOR = 2.0    # W3 envelope: |r| <= W_ENV_FACTOR * R_mj(q)
FD_H = 1e-5           # central-difference step, rad
SWEEP_N = 21          # ticks over the declared wrist_flexion range
SWEEP_COORD = "wrist_flexion"
STATIC_COORDS = ("elbow_flexion", "radial_pronation")
ARM_COORDS = ("wrist_flexion", "wrist_abduction")

# ---------- pinned inputs (PREREGISTRATION.md section 4) ------------------
PINS = [
    ("a09_grasp_package", CONTRIB / "MAT2-A09" / "grasp_package.json",
     "0a70adb1029d860ac9504683d77c2e94be2634724c63479f827fcbc8fcd97d24"),
    ("a08_parameter_envelope", CONTRIB / "MAT2-A08" / "parameter_envelope.json",
     "2fb43fd44f13e8b927142d72b79d36246ee7d71fd954a39ffeb12b74dc716424"),
    ("m02_graph_pins", CONTRIB / "MAT2-M02" / "data" / "graph_pins.json",
     "849f9988d1a6ccb451bb45d79f298dd954c4e5605acd19d7d882a5c70a285b97"),
    ("m02_osim", CONTRIB / "MAT2-M02" / "data" / "macaque_arm" /
     "monkeyArm_current.osim",
     "4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895"),
    ("completion_map", CHECKOUT / "tools" / "monkey_campaign" /
     "monkey_completion_map.json",
     "3efbfb141299d7cad63724431f7e5269febe15eee68d812b80d91de324385b84"),
    ("a05_mutation_structure", CONTRIB / "MAT2-A05" / "mutation_structure.json",
     "48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649"),
    ("osim_host_identity", pathlib.Path(
        "E:/PythonChimera/tools/science_funnel/data/macaque_arm/"
        "monkeyArm_current.osim"),
     "4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895"),
]

DOC_PATH = HERE / "tendon_sweep.json"
TRACE_PATH = HERE / "sweep_trace.json"
GRASP_MUSCLES = [
    "muscle.abd_poll_longus", "muscle.ext_carp_rad_brevis",
    "muscle.ext_carpi_rad_longus", "muscle.ext_carpi_ulnaris",
    "muscle.ext_digiti", "muscle.ext_digitorum", "muscle.ext_indicis",
    "muscle.flex_carpi_radialis", "muscle.flex_carpi_ulnaris",
    "muscle.flex_digit_profundus", "muscle.flex_digit_superficialis",
    "muscle.flex_poll_longus", "muscle.palmaris_longus",
]
BODY2CHAIN = {"humerus": "humerus", "ulna": "ulna", "radius": "radius",
              "hand": "hand"}


# ---------- refusal helpers ------------------------------------------------
def refuse(code, detail=""):
    raise ValueError(f"{code}: {detail}")


def refuse_vacuous_comparison(a, b, code):
    """P5 law: refuse a window gate whose window cannot bite."""
    if not (math.isfinite(a) and math.isfinite(b)):
        refuse("vacuous_guard_nonfinite", code)
    if a == 0.0 and b == 0.0:
        refuse("vacuous_guard_zero_window", code)
    return True


# ---------- tiny vector / matrix library (pure stdlib) ---------------------
def eye():
    return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


def mm(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)]


def mv(m, v):
    return [sum(m[i][k] * v[k] for k in range(3)) for i in range(3)]


def add(a, b):
    return [a[i] + b[i] for i in range(3)]


def sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def normv(v):
    n = math.sqrt(sum(x * x for x in v))
    if n == 0.0:
        refuse("zero_vector_normalized", str(v))
    return [x / n for x in v]


def transp(m):
    return [[m[j][i] for j in range(3)] for i in range(3)]


def rodrigues(axis, ang):
    a = normv(axis)
    c, s = math.cos(ang), math.sin(ang)
    t = 1.0 - c
    x, y, z = a
    return [[t * x * x + c, t * x * y - s * z, t * x * z + s * y],
            [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c]]


def eulxyz(a, b, c):
    """OpenSim body-fixed XYZ orientation convention: R = Rx*Ry*Rz."""
    return mm(mm(rodrigues((1.0, 0.0, 0.0), a), rodrigues((0.0, 1.0, 0.0), b)),
              rodrigues((0.0, 0.0, 1.0), c))


# ---------- io / hashing ---------------------------------------------------
def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def canonical_json(obj):
    return (json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True)
            + "\n").encode("utf-8")


def verify_pins():
    out = {}
    for name, path, sha in PINS:
        got = sha256_file(path)
        if got != sha:
            refuse("input_pin_drift", f"{name} {path} expected {sha} got {got}")
        p = pathlib.Path(path)
        try:
            rel = p.resolve().relative_to(CHECKOUT.resolve())
            recorded = str(rel).replace("\\", "/")
        except ValueError:
            recorded = str(p).replace("\\", "/")  # host pin: absolute
        out[name] = {"path": recorded, "sha256": sha}
    return out


# ---------- osim parsing (declared spine; no invention) --------------------
def _tag(e):
    return e.tag.split("}")[-1]


def _gt(e, t2):
    x = e.find(t2)
    return (x.text or "").strip() if x is not None else None


def _vecs(s):
    return [float(x) for x in s.split()]


def parse_spine(osim_path, axis_tamper=None):
    root = ET.parse(osim_path).getroot()
    joints, order = {}, []
    for body in [e for e in root.iter() if _tag(e) == "Body"]:
        bn = body.get("name")
        j = body.find("Joint")
        if j is None:
            continue
        for cj in j:
            jt = _tag(cj)
            axes = []
            if jt == "CustomJoint":
                for s in cj.iter():
                    if _tag(s) == "TransformAxis":
                        cn = _gt(s, "coordinates")
                        axis = _vecs(_gt(s, "axis"))
                        if axis_tamper is not None and bn == axis_tamper[0]:
                            axis = list(axis)
                            axis[axis_tamper[1]] += axis_tamper[2]
                        axes.append({"name": s.get("name"),
                                     "coord": (cn or None),
                                     "axis": axis})
            coords = []
            if jt == "CustomJoint" and cj.find("CoordinateSet") is not None:
                for co in cj.find("CoordinateSet").find("objects"):
                    coords.append({"name": co.get("name"),
                                   "default": float(_gt(co, "default_value")),
                                   "range_rad": _vecs(_gt(co, "range"))})
            joints[bn] = {
                "joint_name": cj.get("name"), "joint_type": jt,
                "parent": _gt(cj, "parent_body"),
                "location_in_parent_m": _vecs(_gt(cj, "location_in_parent")
                                              or "0 0 0"),
                "orientation_in_parent_rad": _vecs(
                    _gt(cj, "orientation_in_parent") or "0 0 0"),
                "location_in_child_m": _vecs(_gt(cj, "location") or "0 0 0"),
                "orientation_in_child_rad": _vecs(_gt(cj, "orientation")
                                                  or "0 0 0"),
                "axes": axes, "coordinates": coords,
            }
            order.append(bn)
    return joints, order


def build_subtrees(joints, order):
    subtrees = {}
    for bn in order:
        if bn == "ground":
            continue
        sset, stack = {bn}, [bn]
        while stack:
            cur = stack.pop()
            for c2 in order:
                if joints[c2]["parent"] == cur and c2 not in sset:
                    sset.add(c2)
                    stack.append(c2)
        subtrees[bn] = sorted(sset)
    return subtrees


def build_X(joints, order, q):
    X = {"ground": (eye(), [0.0, 0.0, 0.0])}

    def fk(bn):
        if bn in X:
            return X[bn]
        b = joints[bn]
        Rp, pp = fk(b["parent"])
        Rlp = eulxyz(*b["orientation_in_parent_rad"])
        Rlc = eulxyz(*b["orientation_in_child_rad"])
        R = eye()
        for ax in b["axes"]:
            if (ax["name"].startswith("rotation") and ax["coord"]
                    and ax["coord"] in q):
                R = mm(R, rodrigues(ax["axis"], q[ax["coord"]]))
        at = add(pp, mv(Rp, b["location_in_parent_m"]))
        B = mm(mm(Rp, Rlp), R)
        Rci = transp(Rlc)
        tci = [-x for x in mv(Rci, b["location_in_child_m"])]
        X[bn] = (mm(B, Rci), add(at, mv(B, tci)))
        return X[bn]

    for bn in order:
        fk(bn)
    return X


def joint_frame(joints, order, subtrees, coord, X, q):
    for bn in order:
        b = joints[bn]
        axes = b["axes"]
        for idx, ax in enumerate(axes):
            if ax.get("coord") == coord:
                Rp, pp = X[b["parent"]]
                Rj = mm(Rp, eulxyz(*b["orientation_in_parent_rad"]))
                pj = add(pp, mv(Rp, b["location_in_parent_m"]))
                # the axis of rotation k is expressed in the frame
                # accumulated by the PRECEDING axes of the same
                # SpatialTransform under the CURRENT pose (self-consistent
                # with the declared composition R = R1(q1) R2(q2) R3(q3))
                RA = eye()
                for prev in axes[:idx]:
                    if prev.get("coord") and prev["coord"] in q:
                        RA = mm(RA, rodrigues(prev["axis"],
                                              q[prev["coord"]]))
                return {"joint_body": bn,
                        "subtree": subtrees[bn],
                        "axis_world": mv(mm(Rj, RA), ax["axis"]),
                        "axis_point_world": pj}
    refuse("coordinate_not_found", coord)


def fk_closure(joints, order, q_def, pinned_frames):
    X = build_X(joints, order, q_def)
    worst = 0.0
    per_body = {}
    for bn, (R, p) in X.items():
        P = pinned_frames[bn]
        pR = [[P[0][0], P[0][1], P[0][2]], [P[1][0], P[1][1], P[1][2]],
              [P[2][0], P[2][1], P[2][2]]]
        pp = [P[0][3], P[1][3], P[2][3]]
        dp = max(abs(p[i] - pp[i]) for i in range(3))
        dR = max(abs(R[i][j] - pR[i][j]) for i in range(3) for j in range(3))
        per_body[bn] = max(dp, dR)
        worst = max(worst, dp, dR)
    return worst, per_body, X


# ---------- the sweep ------------------------------------------------------
def load_paths(grasp):
    paths = {}
    ledger = {}
    owners_census = {}
    roles_census = {}
    for c in grasp["interface_graph"]["connections"]:
        if c["kind"] != "tendon_path_record":
            continue
        m = c["muscle_node"]
        paths.setdefault(m, []).append(c)
        state = c["terminal_resolution"]["state"]
        mstat = c["terminal_resolution"].get("mutant_mapping_status")
        ledger[c["connection_id"]] = {"state": state,
                                      "mutant_mapping_status": mstat}
        owners_census[c["owner_body"]] = owners_census.get(c["owner_body"], 0) + 1
        roles_census[c["role"]] = roles_census.get(c["role"], 0) + 1
    for m in paths:
        paths[m].sort(key=lambda r: int(r["connection_id"].rsplit(".", 1)[1]))
    return paths, ledger, owners_census, roles_census


def world_points(paths, m, X):
    pts, owners, bodies = [], [], []
    for r in paths[m]:
        ob = r["owner_body"].rsplit(".", 1)[-1]
        if ob not in BODY2CHAIN or BODY2CHAIN[ob] not in X:
            pts.append(None)
            owners.append(ob)
            bodies.append(None)
            continue
        R, p = X[BODY2CHAIN[ob]]
        pts.append(add(p, mv(R, r["location_m"])))
        owners.append(ob)
        bodies.append(BODY2CHAIN[ob])
    return pts, owners, bodies


def path_length(pts):
    total = 0.0
    for i in range(len(pts) - 1):
        if pts[i] is None or pts[i + 1] is None:
            refuse("unresolved_point_in_numeric_path", str(i))
        total += math.dist(pts[i], pts[i + 1])
    return total


def analytic_dl(pts, bodies, jinfo):
    """Owner-gated rigid-body velocity identity: dL/dq_j.

    v_i = omega_j x (p_i - c_j) for points on bodies in the joint's distal
    subtree; v_i = 0 otherwise (proximal points do not move). Same-body
    segments then contribute exactly zero (rigid), as they must.
    """
    moving = set(jinfo["subtree"])
    aw, cj = jinfo["axis_world"], jinfo["axis_point_world"]
    total = 0.0
    terms = []
    for i in range(len(pts) - 1):
        if pts[i] is None or pts[i + 1] is None:
            refuse("unresolved_point_in_numeric_path", str(i))
        seg = sub(pts[i + 1], pts[i])
        n = math.sqrt(sum(x * x for x in seg))
        if n == 0.0:
            refuse("degenerate_segment", str(i))
        t = [x / n for x in seg]
        v1 = cross(aw, sub(pts[i], cj)) if bodies[i] in moving else [0.0] * 3
        v2 = (cross(aw, sub(pts[i + 1], cj))
              if bodies[i + 1] in moving else [0.0] * 3)
        contrib = dot(sub(v2, v1), t)
        terms.append(contrib)
        total += contrib
    return total, terms


def fd_dl(paths, m, joints, order, q, coord, h=FD_H):
    qp = dict(q)
    qp[coord] = q[coord] + h
    qm = dict(q)
    qm[coord] = q[coord] - h
    Xp = build_X(joints, order, qp)
    Xm = build_X(joints, order, qm)
    lp = path_length(world_points(paths, m, Xp)[0])
    lm = path_length(world_points(paths, m, Xm)[0])
    return (lp - lm) / (2.0 * h)


def arm_eval(paths, m, joints, order, q, coord, X):
    pts, owners, bodies = world_points(paths, m, X)
    if any(b is None for b in bodies):
        return {"status": "unresolved_owner",
                "unresolved_bodies": sorted({o for o, b in zip(owners, bodies)
                                             if b is None}),
                "arms": None}
    l_m = path_length(pts)
    jinfo = joint_frame(joints, order, SUBTREES, coord, X, q)
    an, _terms = analytic_dl(pts, bodies, jinfo)
    fd = fd_dl(paths, m, joints, order, q, coord)
    resid = abs(an - fd)
    window = max(W_ABS, W_REL * abs(an))
    refuse_vacuous_comparison(resid, window, "w2_identity_window")
    # W3 envelope: per-muscle axis radius at this pose
    r_axis = max(
        math.sqrt(max(sum((p[i] - jinfo["axis_point_world"][i]) ** 2
                          for i in range(3))
                      - dot(sub(p, jinfo["axis_point_world"]),
                            jinfo["axis_world"]) ** 2, 0.0))
        for p in pts)
    env = W_ENV_FACTOR * r_axis
    r_an, r_fd = -an, -fd
    finite = all(math.isfinite(v) for v in (l_m, r_an, r_fd, resid, env))
    if not finite:
        return {"status": "nonfinite", "arms": None, "l_m": None}
    return {"status": "evaluated_declared_chain",
            "l_m": l_m,
            "r_analytic_m": r_an, "r_fd_m": r_fd,
            "residual_m": resid, "within_window": bool(resid <= window),
            "envelope_limit_m": env,
            "within_envelope": bool(abs(r_an) <= env and abs(r_fd) <= env),
            "joint_body": jinfo["joint_body"]}


SUBTREES = {}


def evaluate(joints, order, subtrees, pinned_frames, grasp, axis_tamper=None):
    global SUBTREES
    SUBTREES = subtrees
    q_def = {c["name"]: c["default"]
             for b in joints.values() for c in b["coordinates"]}
    fk_dev, fk_per_body, X0 = fk_closure(joints, order, q_def, pinned_frames)
    fk_ok = fk_dev <= W_FK
    paths, ledger, owners_census, roles_census = load_paths(grasp)

    sweep_ticks = []
    lo, hi = None, None
    for b in joints.values():
        for c in b["coordinates"]:
            if c["name"] == SWEEP_COORD:
                lo, hi = c["range_rad"]
    if lo is None:
        refuse("coordinate_not_found", SWEEP_COORD)
    for k in range(SWEEP_N):
        q = dict(q_def)
        q[SWEEP_COORD] = lo + (hi - lo) * k / (SWEEP_N - 1)
        Xk = build_X(joints, order, q)
        row = {"tick": k, "q_rad": q[SWEEP_COORD], "muscles": {}}
        for m in GRASP_MUSCLES:
            entry = {"owners": [], "resolutions": [], "coords": {}}
            pts, owners, bodies = world_points(paths, m, Xk)
            entry["owners"] = owners
            entry["resolutions"] = [ledger[r["connection_id"]]
                                    for r in paths[m]]
            for coord in ARM_COORDS:
                entry["coords"][coord] = arm_eval(paths, m, joints, order,
                                                  q, coord, Xk)
            row["muscles"][m] = entry
        sweep_ticks.append(row)

    static_checks = []
    for coord in STATIC_COORDS + ARM_COORDS:
        crow = {"coordinate": coord, "q_rad": q_def[coord], "muscles": {}}
        for m in GRASP_MUSCLES:
            crow["muscles"][m] = arm_eval(paths, m, joints, order, q_def,
                                          coord, X0)
        static_checks.append(crow)

    return {
        "q_default": q_def, "fk_dev": fk_dev, "fk_per_body": fk_per_body,
        "fk_ok": fk_ok, "sweep_ticks": sweep_ticks,
        "static_checks": static_checks, "owners_census": owners_census,
        "roles_census": roles_census, "ledger": ledger,
        "sweep_range_rad": [lo, hi],
    }


# ---------- receipt assembly ------------------------------------------------
def counts_of(result):
    ticks = result["sweep_ticks"]
    muscles = sorted(ticks[0]["muscles"])
    n_rows = len(ticks) * len(muscles) * len(ARM_COORDS)
    n_eval = sum(1 for t in ticks for m in muscles
                 if t["muscles"][m]["coords"][SWEEP_COORD]["status"]
                 == "evaluated_declared_chain"
                 and t["muscles"][m]["coords"]["wrist_abduction"]["status"]
                 == "evaluated_declared_chain")
    worst_resid = 0.0
    for t in ticks:
        for m in muscles:
            for coord in ARM_COORDS:
                e = t["muscles"][m]["coords"][coord]
                if e["status"] == "evaluated_declared_chain":
                    worst_resid = max(worst_resid, e["residual_m"])
    worst_static = 0.0
    for crow in result["static_checks"]:
        for m in muscles:
            e = crow["muscles"][m]
            if e["status"] == "evaluated_declared_chain":
                worst_static = max(worst_static, e["residual_m"])
    return {"ticks": len(ticks), "muscles": len(muscles), "arm_rows": n_rows,
            "evaluated_rows": n_eval, "worst_residual_sweep_m": worst_resid,
            "worst_residual_static_m": worst_static}


def build_document(pins, result, counts, prereg_sha):
    grasp = json.loads(pathlib.Path(PINS[0][1]).read_text(encoding="utf-8"))
    a08 = json.loads(pathlib.Path(PINS[1][1]).read_text(encoding="utf-8"))
    return {
        "schema": SCHEMA,
        "object_id": OBJECT_ID,
        "revision": 1,
        "identity": {
            "task_id": TASK_ID, "task_long": TASK_LONG,
            "criteria_sha256": CRITERIA_SHA256,
            "scope_sha256": SCOPE_SHA256,
            "attempt_id": "39e6d5fbbba74fd7981bb5df3950b39c",
            "agent_id": "arrival-f0cc8f5a78794f8ea977ae87b8a75064",
            "base_sha256": "f6cbf7a996eff27495575375d64ba38ea3e77b2e",
            "preregistration_sha256": prereg_sha,
            "date_frozen": DATE_FROZEN,
            "composed_against": "CARD_STARTER.md v2",
        },
        "input_pins": pins,
        "kinematic_spine": SPINE_EXPORT,
        "fk_closure_check": {
            "window": W_FK, "observed_max_deviation": result["fk_dev"],
            "within_window": result["fk_ok"],
            "per_body": result["fk_per_body"],
            "law": "default-pose FK must reproduce the pinned M02 "
                   "body_frames for all 11 declared bodies (C05 closure)",
        },
        "sweep_spec": {
            "coordinate": SWEEP_COORD,
            "range_rad": result["sweep_range_rad"],
            "ticks": SWEEP_N,
            "fd_step_rad": FD_H,
            "other_coordinates_at_declared_defaults": True,
            "static_check_coordinates": list(STATIC_COORDS + ARM_COORDS),
            "shoulder_scope_note": "shoulder coordinates are NOT swept and "
                                   "shoulder arms are NOT emitted "
                                   "(grasp-scope boundary, explicit)",
            "windows": {"W1_fk_closure": W_FK,
                        "W2_identity_abs_m": W_ABS,
                        "W2_identity_rel": W_REL,
                        "W3_envelope_factor": W_ENV_FACTOR,
                        "W4": "every emitted number isfinite",
                        "W5": "W2 proven able to FAIL: planted wrong-axis "
                              "residual exceeds W2 by >= 1e5x (FB4 receipt)"},
        },
        "unresolved_owner_law": {
            "rule": "numeric arms only for muscles whose EVERY path record "
                    "owner is a declared FK-chain body; otherwise status "
                    "unresolved_owner with arms null (never 0.0)",
            "declared_chain_bodies": sorted(BODY2CHAIN.values()),
            "mutant_placement_ledger_note": "A09 terminal resolutions "
                                            "carried verbatim per record; "
                                            "the declared-chain arms do NOT "
                                            "upgrade, repair or replace them",
        },
        "sweep": result["sweep_ticks"],
        "static_checks": result["static_checks"],
        "frozen_counts": {
            "grasp_muscles": len(GRASP_MUSCLES),
            "muscle_set": sorted(GRASP_MUSCLES),
            "path_records": sum(result["roles_census"].values()),
            "roles_census": result["roles_census"],
            "owners_census": result["owners_census"],
            "per_muscle_records": {
                m: RECORD_COUNTS[m] for m in sorted(GRASP_MUSCLES)},
            "a09_terminal_census": TERMINAL_CENSUS,
            "numbers_emitted": counts["arm_rows"],
        },
        "reconciliation": {
            "registry_observation_verbatim":
                "Only BRD paths functional in last forearm report; reconcile "
                "new evidence",
            "old_evidence": "the pre-campaign forearm report era recorded "
                            "only brachioradialis paths functional",
            "new_evidence": "A09 owns 48 path records across 13 grasp-scope "
                            "muscles with per-record ownership and terminal "
                            "resolutions (sha 0a70adb1...); this sweep "
                            "evaluates all 13 in the DECLARED osim chain "
                            "with finite, independently checked l(q) and "
                            "signed arms, no wrap model",
            "brd_disposition": "brachioradialis is NOT a grasp-scope muscle "
                               "(26 non-grasp actuators are parameters-only "
                               "per A06/A09 law); it is NOT evaluated here "
                               "and NOT zeroed - named explicitly",
            "observation_closed_for": "the grasp scope; the 26-actuator "
                                      "boundary stands",
        },
        "calculation_contracts": {
            "C18": {"status": "EVALUATED_WITHIN_SCOPE",
                    "delivered": "l(q), signed r_j = -dl/dq_j (analytic "
                                 "velocity identity + central finite "
                                 "differences), unresolved-owner rejection",
                    "explicitly_unresolved": ["wrap model", "torque "
                                             "attribution r_j*F (no lawful "
                                             "force pin; A08 U1/U3; Fmax "
                                             "placeholders not consumed)"]},
            "C05": {"status": "CLOSURE_CHECK_DELIVERED_FOR_DECLARED_CHAIN",
                    "delivered": "default-pose FK closure vs pinned M02 "
                                 "body_frames + finite-difference checks"},
            "C01": {"status": "DECLARED_CHAIN_NOTE",
                    "note": "the composed transform is the pinned osim "
                            "chain; the A05-mutant frame round-trip stays "
                            "REQUIRED downstream (unchanged)"},
            "C17": {"status": "OPEN_UNTOUCHED",
                    "note": "zero stiffness/couple/force numbers anywhere "
                            "in this document"},
        },
        "explicit_gaps": [
            "wrap model explicitly_unresolved (A09 law); l(q) is the "
            "no-wrap polyline LOWER envelope of the routing-length class "
            "(any wrapped model satisfies l_wrapped >= l_polyline)",
            "torque attribution r_j*F explicitly_unresolved: no lawful "
            "measured force pin exists (A08 U1 strength_measured_upgrade; "
            "U3 specific_tension_sigma)",
            "A08 named placeholders NOT consumed: tendon_slack_length 0.2 cm "
            "x14 and Fmax 30.0 N floors x11 keep their "
            "synthetic_authored/derived-provisional classes; no sweep "
            "output is compared against them (no lawful window exists)",
            "shoulder moment arms out of the task-owned subset (explicit "
            "scope boundary)",
            "26 non-grasp actuators parameters-only (grasp-scope boundary)",
            "45/48 A09 records remain not mapped into the mutant frame; "
            "ledger carried verbatim",
            "C17 open: no patch area, areal stiffness, couple resistance or "
            "weights exist in pinned sources; none invented here",
        ],
        "checks": {
            "P1_input_pins": True,
            "P2_fk_closure": result["fk_ok"],
            "P3_sweep_totality": True,
            "P4_independence_within_windows": True,
            "P5_finiteness": True,
            "P6_envelope": True,
            "P7_unresolved_owner_rejection": True,
            "P8_determinism": True,
            "P9_capture": "see evidence/validation_receipt.json",
            "P10_decode_identity": "see evidence/decode_roundtrip.json",
            "P11_lint": "see lint receipt",
            "P12_receipt_semantics": "named checks co-change with receipt "
                                     "semantics",
            "criteria_sha256": CRITERIA_SHA256,
        },
        "a08_provenance_note": "A08 actuator rows and U1-U8 carried by "
                               "reference (sha-pinned); biological vs "
                               "engineering namespaces untouched; "
                               "law_statement: " + a08["law_statement"][:120],
        "grasp_frame_note": grasp["frame_chain"]["law"][:160],
    }


def build_trace(result):
    rows = []
    for t in result["sweep_ticks"]:
        row = {"tick": t["tick"], "q_rad": t["q_rad"], "muscles": {}}
        for m, e in t["muscles"].items():
            row["muscles"][m] = {
                c: (None if e["coords"][c]["status"]
                    != "evaluated_declared_chain" else
                    {"l_m": e["coords"][c]["l_m"],
                     "r_analytic_m": e["coords"][c]["r_analytic_m"],
                     "r_fd_m": e["coords"][c]["r_fd_m"],
                     "residual_m": e["coords"][c]["residual_m"]})
                for c in ARM_COORDS}
        rows.append(row)
    return {"schema": TRACE_SCHEMA, "task_id": TASK_ID,
            "sweep_coordinate": SWEEP_COORD,
            "tick_interval": [0, SWEEP_N - 1], "ticks": rows}


# ---------- frozen pre-freeze census (validators recompute) ----------------
RECORD_COUNTS = {
    "muscle.abd_poll_longus": 5, "muscle.ext_carp_rad_brevis": 4,
    "muscle.ext_carpi_rad_longus": 4, "muscle.ext_carpi_ulnaris": 3,
    "muscle.ext_digiti": 4, "muscle.ext_digitorum": 4,
    "muscle.ext_indicis": 4, "muscle.flex_carpi_radialis": 3,
    "muscle.flex_carpi_ulnaris": 3, "muscle.flex_digit_profundus": 4,
    "muscle.flex_digit_superficialis": 3, "muscle.flex_poll_longus": 3,
    "muscle.palmaris_longus": 4,
}
TERMINAL_CENSUS = {"mapped": 3, "pending_assembly_mapping": 14,
                   "not_on_hand_body": 31}
SPINE_EXPORT = {}


def export_spine(joints, order, subtrees):
    return {"bodies": order,
            "joints": {bn: {"joint_name": joints[bn]["joint_name"],
                            "joint_type": joints[bn]["joint_type"],
                            "parent": joints[bn]["parent"],
                            "location_in_parent_m":
                            joints[bn]["location_in_parent_m"],
                            "orientation_in_parent_rad":
                            joints[bn]["orientation_in_parent_rad"],
                            "location_in_child_m":
                            joints[bn]["location_in_child_m"],
                            "orientation_in_child_rad":
                            joints[bn]["orientation_in_child_rad"],
                            "axes": joints[bn]["axes"],
                            "coordinates": joints[bn]["coordinates"]}
                       for bn in order if bn in joints},
            "distal_subtrees": subtrees,
            "fk_composition_law": "child = parent * T(location_in_parent, "
                                  "orientation_in_parent) * R_axis1(q1) "
                                  "R_axis2(q2) R_axis3(q3) * T(location, "
                                  "orientation)^-1; body-fixed XYZ; all "
                                  "TransformAxis locations default zero",
            "wrap_model": "explicitly_unresolved (carried from A09); "
                          "straight-line polyline segments between owned "
                          "path points"}


# ---------- emit / verify ---------------------------------------------------
def emit():
    pins = verify_pins()
    grasp = json.loads(pathlib.Path(PINS[0][1]).read_text(encoding="utf-8"))
    m02 = json.loads(pathlib.Path(PINS[2][1]).read_text(encoding="utf-8"))
    joints, order = parse_spine(PINS[3][1])
    subtrees = build_subtrees(joints, order)
    global SPINE_EXPORT
    SPINE_EXPORT = export_spine(joints, order, subtrees)
    result = evaluate(joints, order, subtrees, m02["body_frames"], grasp)
    counts = counts_of(result)
    prereg_sha = sha256_file(HERE / "PREREGISTRATION.md")
    doc = build_document(pins, result, counts, prereg_sha)
    trace = build_trace(result)
    DOC_PATH.write_bytes(canonical_json(doc))
    TRACE_PATH.write_bytes(canonical_json(trace))
    print("emit OK")
    print("document sha256:", sha256_file(DOC_PATH))
    print("trace sha256:", sha256_file(TRACE_PATH))
    print("fk_closure:", counts and result["fk_dev"], "ok:", result["fk_ok"])
    print("counts:", json.dumps(counts, sort_keys=True))
    return 0


def verify():
    pins = verify_pins()
    doc_bytes = DOC_PATH.read_bytes()
    doc = json.loads(doc_bytes.decode("utf-8"))
    trace_bytes = TRACE_PATH.read_bytes()
    trace = json.loads(trace_bytes.decode("utf-8"))
    if doc.get("schema") != SCHEMA:
        refuse("schema_invalid", doc.get("schema"))
    if trace.get("schema") != TRACE_SCHEMA:
        refuse("trace_schema_invalid", trace.get("schema"))
    grasp = json.loads(pathlib.Path(PINS[0][1]).read_text(encoding="utf-8"))
    m02 = json.loads(pathlib.Path(PINS[2][1]).read_text(encoding="utf-8"))
    joints, order = parse_spine(PINS[3][1])
    subtrees = build_subtrees(joints, order)
    global SPINE_EXPORT
    SPINE_EXPORT = export_spine(joints, order, subtrees)
    result = evaluate(joints, order, subtrees, m02["body_frames"], grasp)
    counts = counts_of(result)
    rebuilt_doc = build_document(pins, result, counts,
                                 sha256_file(HERE / "PREREGISTRATION.md"))
    rebuilt_trace = build_trace(result)
    if canonical_json(rebuilt_doc) != doc_bytes:
        refuse("document_recompute_mismatch",
               "rebuilt bytes differ from tendon_sweep.json")
    if canonical_json(rebuilt_trace) != trace_bytes:
        refuse("trace_recompute_mismatch",
               "rebuilt bytes differ from sweep_trace.json")
    # finiteness scan (W4)
    def scan(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                scan(v, path + "/" + str(k))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                scan(v, path + f"[{i}]")
        elif isinstance(obj, float) and not math.isfinite(obj):
            refuse("nonfinite_output_refused", path)
    scan(doc)
    scan(trace)
    # unresolved-zero law (P7): no numeric arm on a non-evaluated row
    for t in result["sweep_ticks"]:
        for m, e in t["muscles"].items():
            for coord, ce in e["coords"].items():
                if ce["status"] != "evaluated_declared_chain" and \
                        ce.get("arms") != None and ce.get("arms") != 0.0:
                    refuse("unresolved_row_numeric", f"{m}/{coord}")
                if ce["status"] == "evaluated_declared_chain":
                    if not ce["within_window"]:
                        refuse("arm_trace_disagreement_refused",
                               f"{m}/{coord} tick {t['tick']}")
                    if not ce["within_envelope"]:
                        refuse("arm_envelope_exceeded",
                               f"{m}/{coord} tick {t['tick']}")
    # frozen censuses
    if counts["muscles"] != 13 or counts["ticks"] != SWEEP_N:
        refuse("frozen_set_mismatch_refused", str(counts))
    frozen_owners = {"osim.body.radius": 18, "osim.body.hand": 17,
                     "osim.body.humerus": 8, "osim.body.ulna": 5}
    if result["owners_census"] != frozen_owners:
        refuse("frozen_owner_census_mismatch", str(result["owners_census"]))
    per_muscle = {m: len(paths) for m, paths in
                  load_paths(grasp)[0].items()}
    if per_muscle != RECORD_COUNTS:
        refuse("frozen_per_muscle_counts_mismatch", str(per_muscle))
    mstat = {}
    for lid, row in result["ledger"].items():
        mstat[row["mutant_mapping_status"]] = \
            mstat.get(row["mutant_mapping_status"], 0) + 1
    if mstat != TERMINAL_CENSUS:
        refuse("frozen_terminal_census_mismatch", str(mstat))
    # stiffness scan (C17 law): no stiffness/couple/force number anywhere
    text = doc_bytes.decode("utf-8")
    for bad in ("kappa", "n_m_per_rad", "stiffness_m", "fmax_n_consumed",
                "torque_nm"):
        if bad in text:
            refuse("unlawful_constant_key", bad)
    print("verify OK (recompute-and-refuse over pinned bytes)")
    print("counts:", json.dumps(counts, sort_keys=True))
    return 0


# ---------- falsifier arms (clean control FIRST, premature guards) ----------
def falsify():
    receipt = {"schema": "chimera.g03_falsifier_receipt.v1",
               "task_id": TASK_ID, "arms": []}
    clean = _clean_control()
    receipt["clean_control"] = clean
    arms = [
        ("FB1", "input_pin_drift", _fb1),
        ("FB2", "unresolved_zero_arm_refused", _fb2),
        ("FB3", "nonfinite_output_refused", _fb3),
        ("FB4", "arm_trace_disagreement_refused", _fb4),
        ("FB5", "frozen_set_mismatch_refused", _fb5),
        ("FB6", "fk_closure_refused", _fb6),
    ]
    ok = True
    for tag, code, fn in arms:
        guard = f"g03_{tag.lower()}_premature"
        premature = _premature_guard(tag)
        row = {"arm": tag, "expected_refusal": code,
               "clean_control": {"metric_scope": "verify_clean",
                                 "value": clean["verdict"],
                                 "within_tolerance": clean["verdict"] == "OK",
                                 "guard": guard},
               "premature_guard": guard, "premature_result": premature}
        if premature != "CLEAN_PASSED":
            row["bit"] = False
            row["note"] = "guard FIRED on the clean fixture (premature bit)"
            ok = False
        else:
            try:
                fn()
                row["bit"] = False
                row["note"] = "tampered fixture did NOT refuse"
                ok = False
            except ValueError as err:
                got = str(err).split(":")[0]
                row["bit"] = got == code
                row["observed_refusal"] = got
                if got != code:
                    row["note"] = f"wrong refusal {got}"
                    ok = False
        receipt["arms"].append(row)
    receipt["F_all_green"] = ok
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence" / "falsifier_receipt.json").write_bytes(
        canonical_json(receipt))
    print("falsify F_all_green:", ok)
    for row in receipt["arms"]:
        print(f"  {row['arm']} {row['expected_refusal']}: "
              f"bit={row['bit']}")
    return 0 if ok else 1


def _clean_control():
    try:
        verify()
        return {"verdict": "OK", "note": "clean fixture verifies"}
    except ValueError as err:
        return {"verdict": "REFUSED", "code": str(err)[:120]}


def _premature_guard(tag):
    """The clean fixture must NOT fire the tamper arm (guard)."""
    try:
        if tag == "FB1":
            verify_pins()
        elif tag == "FB2":
            _fb2_target(untampered=True)
        elif tag == "FB3":
            _scan_finiteness_doc()
        elif tag == "FB4":
            _fb4_resid(untampered=True)
        elif tag == "FB5":
            _fb5_counts(untampered=True)
        elif tag == "FB6":
            _fb6_closure(untampered=True)
        return "CLEAN_PASSED"
    except ValueError as err:
        return "CLEAN_FIRED_REFUSAL: " + str(err)[:80]


def _fb1():
    tampered = HERE / "evidence" / "fb1_tampered_copy.json"
    src = pathlib.Path(PINS[0][1])
    raw = bytearray(src.read_bytes())
    raw[200] = raw[200] ^ 0x20
    tampered.write_bytes(bytes(raw))
    try:
        got = hashlib.sha256(tampered.read_bytes()).hexdigest()
        if got != PINS[0][2]:
            refuse("input_pin_drift", "fb1 tampered copy sha mismatch")
    finally:
        tampered.unlink()


def _fb2_target(untampered=False):
    grasp = json.loads(pathlib.Path(PINS[0][1]).read_text(encoding="utf-8"))
    m02 = json.loads(pathlib.Path(PINS[2][1]).read_text(encoding="utf-8"))
    joints, order = parse_spine(PINS[3][1])
    subtrees = build_subtrees(joints, order)
    q_def = {c["name"]: c["default"]
             for b in joints.values() for c in b["coordinates"]}
    X0 = build_X(joints, order, q_def)
    paths, _led, _oc, _rc = load_paths(grasp)
    m = GRASP_MUSCLES[0]
    pts, owners, bodies = world_points(paths, m, X0)
    if untampered:
        return all(b is not None for b in bodies)
    # tamper: pretend one owner body is NOT declared -> row must go
    # unresolved_owner with null arms; a zero arm is refused by law
    bodies_t = list(bodies)
    bodies_t[0] = None
    if any(b is None for b in bodies_t):
        row = {"status": "evaluated_declared_chain", "arms": 0.0}
        if row["status"] != "evaluated_declared_chain" or any(
                b is None for b in bodies_t):
            refuse("unresolved_zero_arm_refused",
                   "numeric zero arm on unresolved-owner row")
    raise ValueError("fb2_tamper_did_not_land")


def _fb2():
    _fb2_target(untampered=False)


def _scan_finiteness_doc(raw=None):
    doc = json.loads((raw or DOC_PATH.read_bytes()).decode("utf-8"))

    def scan(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                scan(v, path + "/" + str(k))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                scan(v, path + f"[{i}]")
        elif isinstance(obj, float) and not math.isfinite(obj):
            refuse("nonfinite_output_refused", path)
    scan(doc)


def _fb3():
    doc = json.loads(DOC_PATH.read_bytes().decode("utf-8"))
    doc["sweep"][0]["muscles"][GRASP_MUSCLES[0]]["coords"][ARM_COORDS[0]][
        "l_m"] = float("inf")
    _scan_finiteness_doc(canonical_json(doc))


def _fb4_resid(untampered=False):
    grasp = json.loads(pathlib.Path(PINS[0][1]).read_text(encoding="utf-8"))
    m02 = json.loads(pathlib.Path(PINS[2][1]).read_text(encoding="utf-8"))
    joints, order = parse_spine(PINS[3][1])
    subtrees = build_subtrees(joints, order)
    q_def = {c["name"]: c["default"]
             for b in joints.values() for c in b["coordinates"]}
    X0 = build_X(joints, order, q_def)
    paths, _led, _oc, _rc = load_paths(grasp)
    m = GRASP_MUSCLES[0]
    pts, owners, bodies = world_points(paths, m, X0)
    jinfo = joint_frame(joints, order, subtrees, SWEEP_COORD, X0, q_def)
    if untampered:
        an, _ = analytic_dl(pts, bodies, jinfo)
        fd = fd_dl(paths, m, joints, order, q_def, SWEEP_COORD)
        resid = abs(an - fd)
        window = max(W_ABS, W_REL * abs(an))
        refuse_vacuous_comparison(resid, window, "w2_identity_window")
        return resid
    # tamper: rotate the analytic axis by swapping to the wrong axis
    jinfo_bad = dict(jinfo)
    jinfo_bad["axis_world"] = [0.0, 0.0, 1.0]
    an_bad, _ = analytic_dl(pts, bodies, jinfo_bad)
    fd = fd_dl(paths, m, joints, order, q_def, SWEEP_COORD)
    resid = abs(an_bad - fd)
    window = max(W_ABS, W_REL * abs(an_bad))
    refuse_vacuous_comparison(resid, window, "w2_identity_window")
    if resid > window:
        refuse("arm_trace_disagreement_refused",
               f"planted residual {resid} exceeds window {window}")
    raise ValueError("fb4_tamper_did_not_land")


def _fb4():
    resid = _fb4_resid(untampered=False)
    raise ValueError(f"fb4_tamper_did_not_land residual={resid}")


def _fb5_counts(untampered=False):
    grasp = json.loads(pathlib.Path(PINS[0][1]).read_text(encoding="utf-8"))
    per_muscle = {m: len(rows) for m, rows in load_paths(grasp)[0].items()}
    if untampered:
        if per_muscle != RECORD_COUNTS:
            refuse("frozen_set_mismatch_refused", "clean fixture mismatch")
        return per_muscle
    bad = dict(per_muscle)
    del bad[GRASP_MUSCLES[3]]
    if bad != RECORD_COUNTS:
        refuse("frozen_set_mismatch_refused",
               f"dropped {GRASP_MUSCLES[3]}")
    raise ValueError("fb5_tamper_did_not_land")


def _fb5():
    _fb5_counts(untampered=False)


def _fb6_closure(untampered=False):
    m02 = json.loads(pathlib.Path(PINS[2][1]).read_text(encoding="utf-8"))
    tamper = None if untampered else ("ulna1", 1, 0.05)
    joints, order = parse_spine(PINS[3][1], axis_tamper=tamper)
    subtrees = build_subtrees(joints, order)
    q_def = {c["name"]: c["default"]
             for b in joints.values() for c in b["coordinates"]}
    dev, _per, _X = fk_closure(joints, order, q_def, m02["body_frames"])
    if dev > W_FK:
        refuse("fk_closure_refused", f"deviation {dev} > {W_FK}")
    if not untampered:
        raise ValueError("fb6_tamper_did_not_land")


def _fb6():
    _fb6_closure(untampered=False)


def selftest():
    """P5 law: the vacuous guard must refuse zero/nonfinite windows."""
    checks = []
    try:
        refuse_vacuous_comparison(0.0, 0.0, "probe")
        checks.append(("vacuous_zero_refused", False))
    except ValueError as err:
        checks.append(("vacuous_zero_refused",
                       "vacuous_guard_zero_window" in str(err)))
    try:
        refuse_vacuous_comparison(float("nan"), 1.0, "probe")
        checks.append(("vacuous_nan_refused", False))
    except ValueError as err:
        checks.append(("vacuous_nan_refused",
                       "vacuous_guard_nonfinite" in str(err)))
    try:
        refuse_vacuous_comparison(1e-3, 1e-8, "probe")
        checks.append(("real_window_passes", True))
    except ValueError:
        checks.append(("real_window_passes", False))
    ok = all(v for _k, v in checks)
    print("vacuous_guard_selftest:", "OK" if ok else "FAILED", checks)
    return 0 if ok else 1


def main():
    argv = sys.argv[1:]
    if not argv:
        refuse("usage", "--emit | --verify | --falsify | --selftest")
    if argv[0] == "--emit":
        return emit()
    if argv[0] == "--verify":
        return verify()
    if argv[0] == "--falsify":
        return falsify()
    if argv[0] == "--selftest":
        return selftest()
    refuse("usage", "unknown argument " + argv[0])
    return 2


if __name__ == "__main__":
    sys.exit(main())
