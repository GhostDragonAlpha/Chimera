# gp1_physics.py - the GP1 candidate-posture feasibility instrument mechanics.
# Implementation lane wk-gp1-impl, 2026-10-02, for card MAT2-GP1-POSTURE-FEASIBILITY.
#
# FROZEN LAW SOURCE: the committed prereg bytes at git commit a18fe92e0ea7ed95edf4c4
# c383203c1af749b04d (origin/review/GP1-POSTURE-20261002), file
# tools/monkey_campaign/contributions/GP1-POSTURE-20261002/PREREGISTRATION.md,
# sha256 bb7bf71829067d8f61142679948145a394f0413e0d0ddfbade7c0141bec13c2e.
# This module implements EXACTLY the declared instruments of prereg section 4:
#   CC0 input gate helpers (hash pins, constant re-parse, prefix identity)
#   CC1 candidate contact-configuration solve (the sealed aperture derivation's
#       deterministic class: grid + zoom + coordinate polish; stdlib only)
#   CC2 self-collision via derived bounding-sphere proxies (19 pinned STLs +
#       the certified anchor AABB; collision geometry ABSENT -> DERIVED-PROXY)
#   CC3 trunk penetration via the deterministic 720x2 placement sweep
#   CC5 statics: tau = J(q)^T f on the certified chain + load-support law
# FK discipline: the sealed aperture derivation's parser/FK (runner job
# 2b32a723030646f6920191702fa8e21a), which reproduced the recorded endpoints to
# 1.3877787807814457e-17 m: A05 mutation_structure.json authority, A05 XML exact
# cross-check, hinge at body origin, first-joint-outermost composition.
#
# Labels: every emitted number is a CONDITIONAL-CALCULATION of the declared
# assumption set A1-A8 of the prereg - never a measured monkey value.
# Interpreter: C:/Python314/python.exe -B (task interpreter). stdlib only.

import hashlib
import itertools
import json
import math
import re
import struct
import xml.etree.ElementTree as ET

PREREG_SHA256 = "bb7bf71829067d8f61142679948145a394f0413e0d0ddfbade7c0141bec13c2e"
PREREG_COMMIT = "a18fe92e0ea7ed95edf4c4c383203c1af749b04d"

COORD_BASE = "E:/ChimeraWork/monkey-coordination/"
REPO = "E:/PythonChimera/"
BENCH = "E:/ChimeraWork/research-data/20260929/benchmark-grasp/"
K01_RESULTS = "E:/ChimeraWork/task-runner/results/97f2145b45cb4f99a8073a772f4092bf/"

# ---------------------------------------------------------------------------
# section-7 input pins (drift = refusal input_pin_mismatch / input_pin_missing)
# ---------------------------------------------------------------------------
PINS_ABS = {
    COORD_BASE + "x-aperture/GRASP_MECHANISMS.md":
        "ac5e258360e45f46e26117147ab944167aafea55b65df549fb4cecbcbf3c1c5d",
    COORD_BASE + "x-aperture/aperture_report.txt":
        "d60a6aec8927ec1b35eeb510b8a71a65c649bea0706852a5f71bdb03d8e36ef5",
    COORD_BASE + "x-aperture/aperture_result.json":
        "bbfc2bbb2e23da906f6392da04481d8da304808758a5316732e1c1426f59e663",
    COORD_BASE + "x-aperture/EVIDENCE.md":
        "68b5e429a0c5e0a81718c1fb77fc86856ed901ee7843f02f136303996ee5ad91",
    COORD_BASE + "evidence-store/MAT2-A09/numerical/grasp_package.json":
        "0a70adb1029d860ac9504683d77c2e94be2634724c63479f827fcbc8fcd97d24",
    COORD_BASE + "evidence-store/MAT2-A05/workspace_evidence/48b037593f63_mutation_structure.json":
        "48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649",
    COORD_BASE + "evidence-store/MAT2-A05/workspace_evidence/9c91124600ab_macaque_hand_mutation.xml":
        "9c91124600abc67a4a33d78ce79ab1a0604a48b5a9a2e6377d15de05717e5adf",
    COORD_BASE + "evidence-store/MAT2-G01/report/REPORT.md":
        "e6d6c432680e503d5a70a1903ed59b52d5044cb8d3c7934da3b0db8acf3293a9",
    COORD_BASE + "climb-derivation/DERIVATION.md":
        "da34420558f6632b0544ca94bc3e25ece515027628c7bd8cc54b9fdd30b7ebd9",
    COORD_BASE + "climb-derivation/derivation_output.txt":
        "534ac1f3dfe98bbfb14636704132ca192ca92f47e23cf1f065f9bd5032e2d73f",
    COORD_BASE + "climb-derivation/grasp-geometry/grasp_geometry.py":
        "e5614b3120dc9d663c204acf6a5db21f11e5c27c7616911f07eb385eee2cfc97",
    COORD_BASE + "climb-derivation/grasp-geometry/derivation_output.txt":
        "955956538d8b2e5236e77e14752352dd51c45065a1c5be8222efaa777965a4db",
    COORD_BASE + "climb-derivation/grasp-geometry/SGT_GEOMETRY_REVIEW.md":
        "30a2d6aeb6ed1059c1e416a7aa39ab3285cd3fa12013e8141dab20288a3ebc3b",
    COORD_BASE + "g04-friction/FRICTION_SOURCES.md":
        "336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b",
    COORD_BASE + "evidence-store/MAT2-F05/source/FRICTION_SOURCES.md":
        "336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b",
    COORD_BASE + "evidence-store/MAT2-D-MASSREG/numerical/mass_register.json":
        "61fb79b1bf2df8c5e1a5b1bff2ab1c4f41700de25bc7f1a114cbc78fe693cc7a",
    COORD_BASE + "b07-prereqs/RUNTIME_CONTRACT.md":
        "f33c188bcb561b1946b104340cf36cba366709526c095874684529a599df338c",
    COORD_BASE + "evidence-store/MAT2-W04/numerical/w04_certificate.json":
        "07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598",
    COORD_BASE + "evidence-store/MAT2-B07/unclassified/adoption_record.json":
        "f6952e8afc778f79a0ede05b61d73dd7c3fabd68789703552cd6136e25ef0199",
    COORD_BASE + "assembly-identity/ASSEMBLY_IDENTITY.md":
        "2ab248bda4db799685a5be9f446bb3e731a47b40b9db1108072cce18bafad035",
    COORD_BASE + "capture-gate-template/README.md":
        "331939f3156ca6158956e53c557cc324a3eeb0aa6a381b5170ec5ea83175ddb6",
    COORD_BASE + "capture-gate-template/TEMPLATE_MANIFEST.json":
        "1c4d1dcad9af98c73e1aa4ebb46bff6359b9992e390b38c37fae578e779a59a7",
    BENCH + "GRASP_BENCHMARK.md":
        "d936cebe38b1416dfc417db727ea81396eb8eb9217efed3f05b344db17f71610",
    REPO + "tools/monkey_campaign/MONKEY_COMPLETION_MAP.md":
        "0e3984578b0cae38ab435daaa77cc10559cceeadbaf9885c3f31b979a362ecae",
    REPO + "tools/science_funnel/data/macaque_arm/Geometry/hand.vtp":
        "a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6",
    K01_RESULTS + "receipt.json":
        "f0af6968cf9f063062a20536bb4de3460382c92e66dc1654f5b7b4396c7efbc1",
    K01_RESULTS + "artifacts/outputs/k01_experiment_receipt.json":
        "ee1b26fc8e3eda1f2a95f75806cb1caed44805aa8787698e92f09bad69304dd5",
    K01_RESULTS + "artifacts/outputs/k01_trace.json":
        "2f342339863e41f9ce8a8b1d11e34740827442dfaa1b88c3942d85260739dc45",
}
GRASP_MECH_PRE_AMENDMENT_SHA = "855c1a9ffc5629a9cdc6877688a3656f7679a1a5e3ca22eeca0c82ec281992e1"

# The five RETRACTED defective static quotes (climb-derivation/DERIVATION.md
# section 7 tabulation). MUST NOT appear in any GP1 artifact (prereg section 6).
RETRACTED_QUOTES = [
    "0.73549875",
    "1.005181625",
    "1.12776475",
    "1.3672101817597224",
    "0.9114734545064815",
]

# ---------------------------------------------------------------------------
# vector / matrix helpers (3x3 rotations as row tuples; clarity over speed)
# ---------------------------------------------------------------------------


def axis_rotation(ax, ang):
    """Rodrigues rotation about unit axis ax by ang."""
    x, y, z = ax
    c = math.cos(ang)
    s = math.sin(ang)
    t = 1.0 - c
    return (
        (t * x * x + c,     t * x * y - s * z, t * x * z + s * y),
        (t * x * y + s * z, t * y * y + c,     t * y * z - s * x),
        (t * x * z - s * y, t * y * z + s * x, t * z * z + c),
    )


def mat_vec(m, v):
    return (
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    )


def mat_mat(a, b):
    return tuple(
        tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )


IDENT = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norm(a):
    return math.sqrt(dot(a, a))


def unit(a):
    n = norm(a)
    if n == 0.0:
        raise ValueError("zero_vector_unit_refused")
    return (a[0] / n, a[1] / n, a[2] / n)


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# ---------------------------------------------------------------------------
# certified model parse (A05 authority, A05 XML exact cross-check; the sealed
# aperture solver's discipline, reused verbatim in substance)
# ---------------------------------------------------------------------------


def parse_axis(ax):
    if isinstance(ax, str):
        return tuple(float(x) for x in ax.split())
    return tuple(float(x) for x in ax)


def parse_hand_model(mut_path, xml_path):
    """Parse the certified 20-body/22-joint hand; cross-check the XML exactly."""
    with open(mut_path, "r", encoding="utf-8") as fh:
        mut = json.load(fh)
    xml_root = ET.parse(xml_path).getroot()
    anchor_name = "macaque_hand_anchor"
    bodies = {}
    joints_by_name = {}

    wrist_js = []
    for j in mut["anchor_body"]["joints"]:
        wrist_js.append((j["name"], parse_axis(j["axis"]),
                         (float(j["range"][0]), float(j["range"][1]))))
    anchor_phys = mut["anchor_body"]["physical"]
    bodies[anchor_name] = dict(
        pos=(0.0, 0.0, 0.0), joints=wrist_js, parent=None,
        mass_kg=float(anchor_phys["mass_kg"]),
        mass_center=tuple(float(x) for x in anchor_phys["mass_center_m"]),
        stl=None,
    )

    for b in mut["bodies"]:
        name = b["name"]
        pos = tuple(float(x) for x in b["mutation"]["pos_m"])
        js = []
        for j in b.get("joints", []):
            js.append((j["name"], parse_axis(j["axis"]),
                       (float(j["range"][0]), float(j["range"][1]))))
        stl_pins = [g["stl_sha256"] for g in b.get("geometry", []) if "stl_sha256" in g]
        if len(stl_pins) != 1:
            raise SystemExit("input_pin_missing: body without exactly one stl pin: " + name)
        phys = b["physical"]
        bodies[name] = dict(
            pos=pos, joints=js,
            parent=b["parent"].rsplit(".", 1)[-1],
            mass_kg=float(b["mutation"]["mass_prior_kg"]),
            mass_center=tuple(float(x) for x in phys["mass_center_m"]),
            stl=stl_pins[0],
        )

    for n in bodies:
        for jn, axis, rng in bodies[n]["joints"]:
            if jn in joints_by_name:
                raise SystemExit("duplicate joint name " + jn)
            joints_by_name[jn] = dict(body=n, axis=axis, range=rng)
    if len(joints_by_name) != 22:
        raise SystemExit("expected 22 declared joints, parsed %d" % len(joints_by_name))
    if len(bodies) != 20:
        raise SystemExit("expected anchor + 19 bodies, parsed %d" % len(bodies))

    # exact XML cross-check (names, axes, ranges, parentage; the executable record)
    xml_bodies = {}
    xml_joints = {}

    def walk(el, parent_name):
        for body in el.findall("body"):
            name = body.get("name")
            pos = tuple(float(x) for x in (body.get("pos") or "0 0 0").split())
            js = []
            for j in body.findall("joint"):
                jname = j.get("name")
                axis = tuple(float(x) for x in j.get("axis").split())
                lo, hi = (float(x) for x in j.get("range").split())
                js.append((jname, axis, (lo, hi)))
                if jname in xml_joints:
                    raise SystemExit("duplicate joint in XML: " + jname)
                xml_joints[jname] = dict(body=name, axis=axis, range=(lo, hi))
            xml_bodies[name] = dict(pos=pos, joints=js, parent=parent_name)
            walk(body, name)

    walk(xml_root.find("worldbody"), None)
    if set(xml_bodies) != set(bodies):
        raise SystemExit("body set mismatch XML vs mutation_structure")
    if set(xml_joints) != set(joints_by_name):
        raise SystemExit("joint set mismatch XML vs mutation_structure")
    worst_pos = 0.0
    for n in bodies:
        if xml_bodies[n]["parent"] != bodies[n]["parent"]:
            raise SystemExit("parent mismatch: " + n)
        worst_pos = max(worst_pos, max(abs(a - bb) for a, bb in
                                       zip(xml_bodies[n]["pos"], bodies[n]["pos"])))
        if len(xml_bodies[n]["joints"]) != len(bodies[n]["joints"]):
            raise SystemExit("joint count mismatch: " + n)
        for (jn1, ax1, r1), (jn2, ax2, r2) in zip(xml_bodies[n]["joints"], bodies[n]["joints"]):
            if jn1 != jn2 or ax1 != ax2 or r1 != r2:
                raise SystemExit("joint mismatch: " + jn1)
    if worst_pos >= 1e-8:
        raise SystemExit("XML-vs-JSON position truncation beyond declared scale")
    return mut, bodies, joints_by_name, anchor_name, worst_pos


def parse_a09_tips(a09):
    """A09 grasp endpoints -> tip owner bodies + recorded q=0 positions."""
    tips = {}
    palm = None
    for ep in a09["interface_graph"]["grasp_endpoints"]:
        owner = ep["owner_body"].rsplit(".", 1)[-1]
        pos = tuple(float(x) for x in ep["position_m"])
        if ep["frame_decl"] != "macaque_arm_hand_mutation_frame":
            raise SystemExit("unexpected frame_decl: " + ep["endpoint_id"])
        if ep["terminal_resolution"]["state"] != "supported":
            raise SystemExit("endpoint not supported: " + ep["endpoint_id"])
        if ep["role"] == "grasp_contact_endpoint":
            tips[ep["endpoint_id"].rsplit(".", 1)[-1]] = dict(body=owner, recorded=pos)
        elif ep["role"] == "grasp_palm_reference":
            palm = dict(body=owner, recorded=pos)
    if len(tips) != 5 or palm is None:
        raise SystemExit("A09 endpoint parse mismatch")
    return tips, palm


# ---------------------------------------------------------------------------
# forward kinematics (hinge at body origin; first-joint-outermost composition;
# a joint declared in a body does NOT move that body's own origin)
# ---------------------------------------------------------------------------


def chain_to(bodies, anchor_name, target):
    chain = []
    n = target
    while n is not None and n != anchor_name:
        chain.append(n)
        n = bodies[n]["parent"]
    if n != anchor_name:
        raise SystemExit("chain does not reach anchor: " + str(target))
    return list(reversed(chain))


def wrist_joints(bodies, anchor_name):
    return [(jn, axis, rng) for (jn, axis, rng) in bodies[anchor_name]["joints"]]


def fk_frames(bodies, anchor_name, q_map, wrist=(0.0, 0.0)):
    """Full frames at q_map. Returns (positions, rotations, joint_records).

    positions[name], rotations[name]: body frame origin / orientation in the
    anchor frame. joint_records: list of (joint_name, body_name, origin, axis_w)
    with origin = the declaring body's frame origin and axis_w = the joint axis
    in world at q_map (the frame rotation BEFORE that joint's own rotation is
    applied). Declared axis-frame convention, cross-checked against the A05
    XML at parse time."""
    R = IDENT
    for jn, axis, _ in bodies[anchor_name]["joints"]:
        q = wrist[0] if jn == "mutation_wrist_flexion" else wrist[1]
        R = mat_mat(R, axis_rotation(axis, q))
    P = bodies[anchor_name]["pos"]
    positions = {anchor_name: P}
    rotations = {anchor_name: R}
    joint_records = []
    # anchor joints: origin (0,0,0); axis in the pre-joint frame
    Ra = IDENT
    for jn, axis, _ in bodies[anchor_name]["joints"]:
        q = wrist[0] if jn == "mutation_wrist_flexion" else wrist[1]
        joint_records.append((jn, anchor_name, P, mat_vec(Ra, axis)))
        Ra = mat_mat(Ra, axis_rotation(axis, q))
    order = [anchor_name]
    idx = 0
    while idx < len(order):
        cur = order[idx]
        idx += 1
        for n in sorted(bodies):
            if bodies[n]["parent"] == cur and n not in positions:
                Rp = rotations[cur]
                P = add(positions[cur], mat_vec(Rp, bodies[n]["pos"]))
                R = Rp
                for jn, axis, _ in bodies[n]["joints"]:
                    joint_records.append((jn, n, P, mat_vec(R, axis)))
                    R = mat_mat(R, axis_rotation(axis, q_map[jn]))
                positions[n] = P
                rotations[n] = R
                order.append(n)
    if len(positions) != len(bodies):
        raise SystemExit("fk_frames did not reach every body")
    return positions, rotations, joint_records


def fk_origin(bodies, anchor_name, q_map, target, wrist=(0.0, 0.0)):
    """Origin of body `target` in the anchor frame under q_map (light path)."""
    R = IDENT
    for jn, axis, _ in bodies[anchor_name]["joints"]:
        q = wrist[0] if jn == "mutation_wrist_flexion" else wrist[1]
        R = mat_mat(R, axis_rotation(axis, q))
    P = bodies[anchor_name]["pos"]
    for name in chain_to(bodies, anchor_name, target):
        P = add(P, mat_vec(R, bodies[name]["pos"]))
        for jn, axis, _ in bodies[name]["joints"]:
            R = mat_mat(R, axis_rotation(axis, q_map[jn]))
    return P


# ---------------------------------------------------------------------------
# STL parse + bounding-sphere proxies (CC2 declared instrument)
# ---------------------------------------------------------------------------


def parse_stl_vertices(path):
    """Binary STL vertices (the certified vendor bytes carry admesh headers)."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:5] == b"solid" and b"facet" in data[:512]:
        raise SystemExit("ascii_stl_unexpected_declared_binary_bytes: " + path)
    ntri = struct.unpack_from("<I", data, 80)[0]
    need = 84 + 50 * ntri
    if len(data) < need:
        raise SystemExit("stl_truncated: " + path)
    verts = []
    off = 84
    for _ in range(ntri):
        vals = struct.unpack_from("<12f", data, off)
        verts.append((vals[3], vals[4], vals[5]))
        verts.append((vals[6], vals[7], vals[8]))
        verts.append((vals[9], vals[10], vals[11]))
        off += 50
    return verts, ntri


def bounding_sphere_scaled(verts, s):
    """Declared CC2 construction: scale vertices by s; center = scaled-AABB
    midpoint; radius = max vertex distance to that center (conservative)."""
    xs = [v[0] * s for v in verts]
    ys = [v[1] * s for v in verts]
    zs = [v[2] * s for v in verts]
    center = ((min(xs) + max(xs)) / 2.0,
              (min(ys) + max(ys)) / 2.0,
              (min(zs) + max(zs)) / 2.0)
    r2 = 0.0
    for i in range(0, len(verts)):
        d = (verts[i][0] * s - center[0], verts[i][1] * s - center[1], verts[i][2] * s - center[2])
        d2 = dot(d, d)
        if d2 > r2:
            r2 = d2
    return center, math.sqrt(r2)


def anchor_bounds_sphere(bounds):
    """Same construction on the certified anchor AABB (hand_vtp_bounds_m):
    center = AABB midpoint; radius = max distance from the center to the 8
    AABB corners (the AABB's vertex set)."""
    lo = tuple(float(x) for x in bounds[0])
    hi = tuple(float(x) for x in bounds[1])
    center = tuple((lo[k] + hi[k]) / 2.0 for k in range(3))
    r2 = 0.0
    for corner in itertools.product((lo[0], hi[0]), (lo[1], hi[1]), (lo[2], hi[2])):
        d = sub(corner, center)
        r2 = max(r2, dot(d, d))
    return center, math.sqrt(r2)


# ---------------------------------------------------------------------------
# CC1 solver: the sealed aperture derivation's deterministic class
# (grid + zoom + coordinate polish), adapted to a chord TARGET.
# ---------------------------------------------------------------------------

GRID_N = 7
ZOOMS = 4
POLISH_PASSES = 3
POLISH_ITERS = 80


def grid_points(lo, hi, n):
    return [lo + (hi - lo) * i / (n - 1) for i in range(n)]


def solve_target(jlist, ranges, eval_fn, target, window_hi=None):
    """Deterministic solve of eval_fn(vals) -> chord to the target.

    Window discipline (declared, no tuned values): a sample whose chord
    exceeds window_hi is rejected lexicographically (objective = 1.0 +
    (chord - window_hi)); the best ANY sample is tracked and recorded too.
    Returns dict with the accepted in-window solution and the best-any."""
    def obj(chord):
        if window_hi is not None and chord > window_hi:
            return 1.0 + (chord - window_hi)
        return abs(chord - target)

    def chord_at(vals):
        return eval_fn(vals)

    los = [r[0] for r in ranges]
    his = [r[1] for r in ranges]

    n_eval = 0

    def scan(los_c, his_c):
        nonlocal n_eval
        pts = [grid_points(los_c[k], his_c[k], GRID_N) for k in range(len(jlist))]
        best = None
        best_any = None
        for combo in itertools.product(*pts):
            chord = chord_at(combo)
            n_eval += 1
            o = obj(chord)
            if best is None or o < best[0]:
                best = (o, chord, list(combo))
            oa = abs(chord - target)
            if best_any is None or oa < best_any[0]:
                best_any = (oa, chord, list(combo))
        return best, best_any, pts

    best, best_any, pts = scan(los, his)
    vals = list(best[2])
    chord = best[1]
    h = [(his[k] - los[k]) / (GRID_N - 1) for k in range(len(jlist))]

    for _ in range(ZOOMS):
        h = [x / (GRID_N - 1) for x in h]
        los_z = [max(ranges[k][0], vals[k] - h[k] * (GRID_N - 1) / 2) for k in range(len(jlist))]
        his_z = [min(ranges[k][1], vals[k] + h[k] * (GRID_N - 1) / 2) for k in range(len(jlist))]
        b2, ba2, pts2 = scan(los_z, his_z)
        los, his = los_z, his_z
        if b2[0] < best[0]:
            best = b2
            vals = list(b2[2])
            chord = b2[1]
        if ba2[0] < best_any[0]:
            best_any = ba2

    def obj_at(v):
        return obj(chord_at(v))

    v = list(vals)
    for _ in range(POLISH_PASSES):
        for k in range(len(jlist)):
            lo_k = max(ranges[k][0], v[k] - h[k])
            hi_k = min(ranges[k][1], v[k] + h[k])
            for _ in range(POLISH_ITERS):
                m1 = lo_k + (hi_k - lo_k) / 3
                m2 = hi_k - (hi_k - lo_k) / 3
                v1 = list(v)
                v2 = list(v)
                v1[k] = m1
                v2[k] = m2
                if obj_at(v1) < obj_at(v2):
                    lo_k = m1
                else:
                    hi_k = m2
            v[k] = (lo_k + hi_k) / 2
    chord_polished = chord_at(v)
    if obj(chord_polished) < best[0]:
        best = (obj(chord_polished), chord_polished, list(v))
    if abs(chord_polished - target) < best_any[0]:
        best_any = (abs(chord_polished - target), chord_polished, list(v))

    return dict(
        q={jn: best[2][k] for k, jn in enumerate(jlist)},
        chord=best[1],
        residual=abs(best[1] - target),
        best_any_chord=best_any[1],
        best_any_residual=best_any[0],
        evals=n_eval,
        grid_n=GRID_N, zooms=ZOOMS,
        polish_passes=POLISH_PASSES, polish_iters=POLISH_ITERS,
    )


# ---------------------------------------------------------------------------
# CC3 placement sweep + cylinder tests
# ---------------------------------------------------------------------------


def placement_sweep(a, b, segments, R, H, n_theta=720):
    """The declared 720x2 deterministic sweep (prereg section 4 CC3).

    a, b: contact points (on the lateral surface, chord c <= 2R).
    segments: list of dicts(name, center, radius, is_contact).
    Per placement: u (axis direction), o (axis point = m + h*w), w, per-segment
    margins / classes / fails. Witness = first zero-FAIL placement in sweep
    order (theta asc, mirror 0 then 1)."""
    v = sub(b, a)
    c = norm(v)
    if c == 0.0:
        raise SystemExit("degenerate_chord_refused")
    if c > 2.0 * R:
        raise SystemExit("chord_exceeds_diameter_placement_family_undefined")
    vh = scale(v, 1.0 / c)
    helper = (0.0, 0.0, 1.0) if abs(vh[2]) < 0.9 else (0.0, 1.0, 0.0)
    e1 = unit(cross(vh, helper))
    e2 = cross(vh, e1)
    m = scale(add(a, b), 0.5)
    h_len = math.sqrt(max(0.0, R * R - (c / 2.0) ** 2))
    placements = []
    for k in range(n_theta):
        theta = 2.0 * math.pi * k / n_theta
        u = add(scale(e1, math.cos(theta)), scale(e2, math.sin(theta)))
        w_base = unit(cross(vh, u))
        for mirror in (0, 1):
            w = w_base if mirror == 0 else scale(w_base, -1.0)
            o = add(m, scale(w, h_len))
            per_seg = []
            n_fail = 0
            worst = None
            for seg in segments:
                d = sub(seg["center"], o)
                z = dot(d, u)
                rho_vec = sub(d, scale(u, z))
                rho = norm(rho_vec)
                axial_overlap = abs(z) < H + seg["radius"]
                if axial_overlap:
                    margin = rho - (R + seg["radius"])
                else:
                    margin = None
                if seg["is_contact"]:
                    center_inside = (rho < R) and (abs(z) < H)
                    depth = (R + seg["radius"] - rho) if (rho < R + seg["radius"] and axial_overlap) else 0.0
                    fail = center_inside
                    cls = "contact_segment_fail" if fail else "contact_class_intersection"
                    seg_margin = rho - R
                else:
                    depth = 0.0
                    fail = bool(axial_overlap and rho < R + seg["radius"])
                    cls = "noncontact_fail" if fail else "noncontact_clear"
                    seg_margin = margin
                if fail:
                    n_fail += 1
                if seg_margin is not None:
                    worst = seg_margin if worst is None else min(worst, seg_margin)
                per_seg.append(dict(
                    name=seg["name"], rho=rho, z=z, margin=seg_margin,
                    cls=cls, fail=fail, intersection_depth=depth,
                ))
            placements.append(dict(
                theta_index=k, theta=theta, mirror=mirror,
                u=u, o=o, w=w, h=h_len, chord=c,
                n_fail=n_fail, worst_margin=worst, segments=per_seg,
            ))
    witness = None
    for pl in placements:
        if pl["n_fail"] == 0:
            witness = pl
            break
    finite = [p for p in placements if p["worst_margin"] is not None]
    min_clear = max(finite, key=lambda p: p["worst_margin"]) if finite else None
    max_pen = min(finite, key=lambda p: p["worst_margin"]) if finite else None
    return dict(chord=c, m=m, h=h_len, placements=placements,
                witness=witness, min_clearance=min_clear, max_penetration=max_pen)


# ---------------------------------------------------------------------------
# CC5 statics
# ---------------------------------------------------------------------------


def joint_torques(joint_records, contacts, press):
    """tau_j = sum_i ((p_i - o_j) x F_i) . u_j with F_i = press * n_i
    (force ON the hand). Returns dict joint_name -> dict(tau, arms)."""
    out = {}
    for (jn, body, o, u) in joint_records:
        tau = 0.0
        arms = {}
        for (cname, p, n) in contacts:
            fvec = scale(n, press)
            mom = cross(sub(p, o), fvec)
            tau += dot(mom, u)
            arms[cname] = norm(cross(sub(p, o), u))
        out[jn] = dict(body=body, origin=list(o), axis=list(u), tau=tau, arms=arms)
    return out


def descendants_map(bodies):
    desc = {}

    def collect(n):
        kids = [k for k in sorted(bodies) if bodies[k]["parent"] == n]
        all_desc = list(kids)
        for k in kids:
            all_desc = all_desc + collect(k)
        desc[n] = all_desc
        return all_desc

    for n in bodies:
        if n not in desc:
            collect(n)
    return desc
