# instrument_v2.py - the CORRECTED two-level collision/penetration instrument.
# Implementation lane wk-instrument-v2, 2026-10-02, resumed after power failure.
#
# FROZEN LAW SOURCE: the committed prereg bytes at git commit
# b564bdd268a78ee2f7067c331bc8abe012ee2f75
# (origin/review/INSTRUMENT-V2-20261002), file
# tools/monkey_campaign/contributions/INSTRUMENT-V2-20261002/PREREGISTRATION.md,
# sha256 897ca164ac5a63437c465783af2dd8f9c743d6c587d5423f4d3cec1b7190bdaf,
# and the lane declaration INSTRUMENT_V2_DECLARATION.md, sha256
# 71e31cdd4122e20bfefdf343df28b0e01fc2a51e70cba11296924ca97ce991ea.
#
# Law implemented EXACTLY:
#   LEVEL 1  screening: the unchanged GP1-CC2 bounding spheres (19 pinned STLs
#            scaled 0.5384048132470733, center = scaled-AABB midpoint, radius =
#            max vertex distance; anchor = hand_vtp_bounds_m AABB sphere
#            r = 0.0450782444410896). Non-adjacent spheres-not-overlapping =>
#            CLEARED at screening (recorded). An overlap is a PROXY FLAG,
#            never a verdict.
#   LEVEL 2  mesh adjudication: exact surface-level triangle-level tests
#            against the represented geometry (the 19 pinned STLs; the pinned
#            hand.vtp envelope for the anchor body; the EXACT analytic trunk
#            cylinder R = 0.037 m, H = 1.158 m). Pair classes:
#            GENUINE_PENETRATION | TOUCHING (the declared contact class)
#            | PROXY_FALSE_POSITIVE | UNRESOLVED_GEOMETRY (never forced).
#   LEDGER:  nothing disabled. ONLY the 19 certified parent-child edges are
#            JOINT-REGION exempt inside r_joint = 5.0e-3 m about the certified
#            child-body frame origin at q (the FK position of the child body);
#            outside it, detection between the same two bodies REMAINS ACTIVE.
#   TOLERANCES frozen a priori, never enlarged: tau = 1.0e-4 m (all pairs),
#            pi_c = 1.0e-3 m (the two declared contact segments vs the trunk),
#            r_joint = 5.0e-3 m. Robustness columns recorded, never decisive:
#            tau {0.5e-4, 2.0e-4}; pi_c {0.5e-3, 2.0e-3}; r_joint
#            {2.5e-3, 1.0e-2}.
#
# Exactness discipline (declared honestly, no sampling in any verdict):
#  - Cylinder tests are closed-form exact: the region SDF is exact per region;
#    segment/solid and triangle/solid intersection are exact (vertex-in /
#    boundary-crossing / plane-section conic cases, complete for a convex
#    solid); the depth is a certified bisection on the exact shrunk-solid
#    predicate; the disjoint minimum is the complete feature set (3 vertices +
#    3 edges + the plane-support branch), exact when triangle and solid are
#    disjoint.
#  - Mesh-mesh tests are exact triangle-triangle predicates with AABB/grid
#    prefilter; containment parity re-casts through a fixed direction list on
#    degeneracy.
#  - CLASSIFICATION never depends on a sampled or approximate value: CLEAR is
#    certified by the complete disjoint minimum or by Lipschitz bounds;
#    GENUINE/TOUCHING are certified by exact intersection predicates.
# FK/model discipline: the sealed GP1 parser/FK reused verbatim in substance
# (A05 mutation_structure.json authority, A05 XML exact cross-check, hinge at
# body origin, first-joint-outermost composition).
# Interpreter: stdlib only; deterministic (fixed iteration order everywhere).

import hashlib
import itertools
import json
import math
import re
import struct
import xml.etree.ElementTree as ET

PREREG_SHA256 = "897ca164ac5a63437c465783af2dd8f9c743d6c587d5423f4d3cec1b7190bdaf"
PREREG_COMMIT = "b564bdd268a78ee2f7067c331bc8abe012ee2f75"
DECLARATION_SHA256 = "71e31cdd4122e20bfefdf343df28b0e01fc2a51e70cba11296924ca97ce991ea"
DECLARATION_PATH = ("E:/ChimeraWork/monkey-coordination/instrument-v2/"
                    "INSTRUMENT_V2_DECLARATION.md")

COORD_BASE = "E:/ChimeraWork/monkey-coordination/"
REPO = "E:/PythonChimera/"
VENDOR_MESHES = REPO + "vendor/myo_sim/meshes/"
VTP_PATH = REPO + "tools/science_funnel/data/macaque_arm/Geometry/hand.vtp"
A05_PATH = (COORD_BASE +
            "evidence-store/MAT2-A05/workspace_evidence/"
            "48b037593f63_mutation_structure.json")
A05_XML_PATH = (COORD_BASE +
                "evidence-store/MAT2-A05/workspace_evidence/"
                "9c91124600ab_macaque_hand_mutation.xml")

# frozen instrument constants (declaration sections 2/3; NEVER tuned)
SCALE = 0.5384048132470733
ANCHOR_R = 0.0450782444410896
TRUNK_R = 0.037
TRUNK_H = 1.158
TAU = 1.0e-4
PI_C = 1.0e-3
R_JOINT = 5.0e-3
TAU_VARIANTS = (0.5e-4, 2.0e-4)
PI_C_VARIANTS = (0.5e-3, 2.0e-3)
R_JOINT_VARIANTS = (2.5e-3, 1.0e-2)
N_THETA = 720
N_MIRROR = 2
DEPTH_SEARCH_MAX = 0.02      # 20 mm certified depth bracket (< R - tau)
DEPTH_SEARCH_ITERS = 60
TERNARY_ITERS = 120

# the declared contact tips of the PRIMARY placement family (GP1-CC3 PRIMARY
# pair: thumb x digit3)
CONTACT_BODIES = ("distal_thumb", "distph3")

# sealed GP1 witness configuration q_c(PRIMARY) (GP1 FINAL job adcbe82b...,
# receipt twin sha e68e6089...; embedded verbatim; refuse on drift)
Q_C_PRIMARY = {
    "cmc_abduction": 0.18493827160493828,
    "cmc_flexion": 0.34199074074074076,
    "ip_flexion": 0.0,
    "mcp2_abduction": 0.0,
    "mcp2_flexion": 0.0,
    "mcp3_abduction": -0.22085923868312754,
    "mcp3_flexion": 0.1442324074074074,
    "mcp4_abduction": 0.0,
    "mcp4_flexion": 0.0,
    "mcp5_abduction": 0.0,
    "mcp5_flexion": 0.0,
    "md2_flexion": 0.0,
    "md3_flexion": 0.0,
    "md4_flexion": 0.0,
    "md5_flexion": 0.0,
    "mp_flexion": 0.5647745578703703,
    "mutation_wrist_abduction": 0.0,
    "mutation_wrist_flexion": 0.0,
    "pm2_flexion": 0.0,
    "pm3_flexion": 0.17150324074074075,
    "pm4_flexion": 0.0,
    "pm5_flexion": 0.0,
}
Q_C_PRIMARY_CHORD = 0.0739999998849158
Q_C_PRIMARY_TIPS = {
    "thumb": (0.04135221500423684, -0.027599029322521736, -0.02221154381793844),
    "digit3": (-0.0032325688315962228, -0.0820381513722398, 0.0006921463593120188),
}
# sealed GP1 fallback solves (declared 6-joint subboxes; all other joints 0)
Q_C_FALLBACKS = {
    "F1": {"cmc_abduction": 0.6794238683127571, "cmc_flexion": 0.5625823045267491,
           "mcp4_abduction": -0.16732780735596708,
           "mcp4_flexion": 0.35654089506172837,
           "mp_flexion": 0.4445811550925926, "pm4_flexion": 0.8948873456790123},
    "F2": {"cmc_abduction": 0.27925925925925926, "cmc_flexion": 0.6931481481481481,
           "mcp5_abduction": 0.18261288271604936,
           "mcp5_flexion": 0.025452777777777776,
           "mp_flexion": 0.5848067916666666, "pm5_flexion": 0.1708972222222222},
    "F3": {"cmc_abduction": 0.2491358024691358, "cmc_flexion": 0.6840123456790124,
           "mcp2_abduction": 0.05649417721193416,
           "mcp2_flexion": 0.021412654320987653,
           "mp_flexion": 0.6868757924382715, "pm2_flexion": 0.11574953703703703},
}

# frozen Level-1 witness expectation at q_c(PRIMARY): the 34 non-adjacent
# sphere-overlap rows recorded by the sealed GP1 receipt (its DERIVED-PROXY
# instrument; quoted-fact provenance, never a rewrite target). Level 1 uses
# the SAME declared construction, so this table is the witness cross-check.
GP1_CC2_WITNESS_OVERLAPS = [
    ("macaque_hand_anchor", "distph2", -0.003759518),
    ("macaque_hand_anchor", "distph3", -0.003749603),
    ("macaque_hand_anchor", "distph4", -0.006695383),
    ("macaque_hand_anchor", "distph5", -0.011418243),
    ("macaque_hand_anchor", "midph2", -0.016526010),
    ("macaque_hand_anchor", "midph3", -0.018260401),
    ("macaque_hand_anchor", "midph4", -0.019012546),
    ("macaque_hand_anchor", "midph5", -0.021182498),
    ("macaque_hand_anchor", "proximal_thumb", -0.012677681),
    ("macaque_hand_anchor", "proxph2", -0.037345245),
    ("macaque_hand_anchor", "proxph3", -0.040251221),
    ("macaque_hand_anchor", "proxph4", -0.038619181),
    ("macaque_hand_anchor", "proxph5", -0.036153294),
    ("distph3", "distph4", -0.001171330),
    ("distph4", "midph3", -0.002936146),
    ("fifthmc", "fourthmc", -0.024378437),
    ("fifthmc", "secondmc", -0.013161599),
    ("fifthmc", "thirdmc", -0.019202487),
    ("firstmc", "secondmc", -0.010261480),
    ("firstmc", "thirdmc", -0.005305021),
    ("fourthmc", "proxph5", -0.003250742),
    ("fourthmc", "secondmc", -0.020387164),
    ("fourthmc", "thirdmc", -0.026897967),
    ("midph3", "midph4", -0.008016194),
    ("midph4", "proxph3", -0.001484542),
    ("midph5", "proxph4", -0.002102792),
    ("proxph2", "proxph3", -0.009285910),
    ("proxph2", "proxph4", -0.001522382),
    ("proxph3", "proxph4", -0.015358799),
    ("proxph3", "proxph5", -0.005023993),
    ("proxph4", "proxph5", -0.010311493),
    ("proxph4", "thirdmc", -0.000025980),
    ("proxph5", "thirdmc", -0.000376573),
    ("secondmc", "thirdmc", -0.028401370),
]
GP1_WITNESS_NONADJACENT_TESTED = 171
GP1_WITNESS_NONADJACENT_OVERLAPS = 34
LEVEL1_MATCH_TOL = 5.0e-9  # the GP1 table was recorded at 9 decimals

# the 19 certified parent-child edges (declaration section 2; exact pairs)
CERTIFIED_EDGES = [
    ("macaque_hand_anchor", "firstmc"),
    ("macaque_hand_anchor", "secondmc"),
    ("macaque_hand_anchor", "thirdmc"),
    ("macaque_hand_anchor", "fourthmc"),
    ("macaque_hand_anchor", "fifthmc"),
    ("firstmc", "proximal_thumb"),
    ("proximal_thumb", "distal_thumb"),
    ("secondmc", "proxph2"), ("proxph2", "midph2"), ("midph2", "distph2"),
    ("thirdmc", "proxph3"), ("proxph3", "midph3"), ("midph3", "distph3"),
    ("fourthmc", "proxph4"), ("proxph4", "midph4"), ("midph4", "distph4"),
    ("fifthmc", "proxph5"), ("proxph5", "midph5"), ("midph5", "distph5"),
]

# inherited input pins (GP1 prereg section 7 lineage, embedded verbatim)
GP1_PINS_ABS = {
    COORD_BASE + "x-aperture/GRASP_MECHANISMS.md":
        "ac5e258360e45f46e26117147ab944167aafea55b65df549fb4cecbcbf3c1c5d",
    COORD_BASE + "x-aperture/EVIDENCE.md":
        "68b5e429a0c5e0a81718c1fb77fc86856ed901ee7843f02f136303996ee5ad91",
    COORD_BASE + "evidence-store/MAT2-A09/numerical/grasp_package.json":
        "0a70adb1029d860ac9504683d77c2e94be2634724c63479f827fcbc8fcd97d24",
    A05_PATH:
        "48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649",
    A05_XML_PATH:
        "9c91124600abc67a4a33d78ce79ab1a0604a48b5a9a2e6377d15de05717e5adf",
    COORD_BASE + "evidence-store/MAT2-G01/report/REPORT.md":
        "e6d6c432680e503d5a70a1903ed59b52d5044cb8d3c7934da3b0db8acf3293a9",
    COORD_BASE + "g04-friction/FRICTION_SOURCES.md":
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
    REPO + "tools/monkey_campaign/MONKEY_COMPLETION_MAP.md":
        "0e3984578b0cae38ab435daaa77cc10559cceeadbaf9885c3f31b979a362ecae",
    VTP_PATH:
        "a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6",
}
GRASP_MECH_PRE_AMENDMENT_SHA = (
    "855c1a9ffc5629a9cdc6877688a3656f7679a1a5e3ca22eeca0c82ec281992e1")

STL_NAMES = ["1mc", "thumbprox", "thumbdist", "2mc", "2proxph", "2midph",
             "2distph", "3mc", "3proxph", "3midph", "3distph", "4mc",
             "4proxph", "4midph", "4distph", "5mc", "5proxph", "5midph",
             "5distph"]


# ---------------------------------------------------------------------------
# gate refusal
# ---------------------------------------------------------------------------

class GateRefusal(SystemExit):
    def __init__(self, code, detail):
        SystemExit.__init__(self, 3)
        self.code = code
        self.detail = detail


def refuse(code, detail):
    raise GateRefusal(code, code + ": " + detail)


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# ---------------------------------------------------------------------------
# vector helpers (the sealed GP1 discipline, reused verbatim in substance)
# ---------------------------------------------------------------------------

def axis_rotation(ax, ang):
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
        refuse("degenerate_vector_refused", str(a))
    return (a[0] / n, a[1] / n, a[2] / n)


def dist(a, b):
    return norm(sub(a, b))


def parse_axis(ax):
    if isinstance(ax, str):
        return tuple(float(x) for x in ax.split())
    return tuple(float(x) for x in ax)


# ---------------------------------------------------------------------------
# certified model parse (A05 authority; A05 XML exact cross-check; GP1 module)
# ---------------------------------------------------------------------------

def parse_hand_model(mut_path, xml_path):
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
    bodies[anchor_name] = dict(pos=(0.0, 0.0, 0.0), joints=wrist_js,
                               parent=None, stl=None)

    for b in mut["bodies"]:
        name = b["name"]
        pos = tuple(float(x) for x in b["mutation"]["pos_m"])
        js = []
        for j in b.get("joints", []):
            js.append((j["name"], parse_axis(j["axis"]),
                       (float(j["range"][0]), float(j["range"][1]))))
        stl_pins = [g["stl_sha256"] for g in b.get("geometry", [])
                    if "stl_sha256" in g]
        if len(stl_pins) != 1:
            refuse("input_pin_missing", "body without exactly one stl pin: " + name)
        bodies[name] = dict(pos=pos, joints=js,
                            parent=b["parent"].rsplit(".", 1)[-1],
                            stl=stl_pins[0])

    for n in bodies:
        for jn, axis, rng in bodies[n]["joints"]:
            if jn in joints_by_name:
                refuse("input_pin_missing", "duplicate joint name " + jn)
            joints_by_name[jn] = dict(body=n, axis=axis, range=rng)
    if len(joints_by_name) != 22:
        refuse("input_pin_missing",
               "expected 22 declared joints, parsed %d" % len(joints_by_name))
    if len(bodies) != 20:
        refuse("input_pin_missing",
               "expected anchor + 19 bodies, parsed %d" % len(bodies))

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
                    refuse("input_pin_missing", "duplicate joint in XML: " + jname)
                xml_joints[jname] = dict(body=name, axis=axis, range=(lo, hi))
            xml_bodies[name] = dict(pos=pos, joints=js, parent=parent_name)
            walk(body, name)

    walk(xml_root.find("worldbody"), None)
    if set(xml_bodies) != set(bodies):
        refuse("input_pin_mismatch", "body set mismatch XML vs mutation_structure")
    if set(xml_joints) != set(joints_by_name):
        refuse("input_pin_mismatch", "joint set mismatch XML vs mutation_structure")
    worst_pos = 0.0
    for n in bodies:
        if xml_bodies[n]["parent"] != bodies[n]["parent"]:
            refuse("input_pin_mismatch", "parent mismatch: " + n)
        worst_pos = max(worst_pos, max(abs(a - bb) for a, bb in
                                       zip(xml_bodies[n]["pos"], bodies[n]["pos"])))
        if len(xml_bodies[n]["joints"]) != len(bodies[n]["joints"]):
            refuse("input_pin_mismatch", "joint count mismatch: " + n)
        for (jn1, ax1, r1), (jn2, ax2, r2) in zip(xml_bodies[n]["joints"],
                                                  bodies[n]["joints"]):
            if jn1 != jn2 or ax1 != ax2 or r1 != r2:
                refuse("input_pin_mismatch", "joint mismatch: " + jn1)
    if worst_pos >= 1e-8:
        refuse("input_pin_mismatch", "XML-vs-JSON position truncation")
    return mut, bodies, joints_by_name, anchor_name, worst_pos


def chain_to(bodies, anchor_name, target):
    chain = []
    n = target
    while n is not None and n != anchor_name:
        chain.append(n)
        n = bodies[n]["parent"]
    if n != anchor_name:
        refuse("input_pin_missing", "chain does not reach anchor: " + str(target))
    return list(reversed(chain))


def fk_frames(bodies, anchor_name, q_map, wrist=(0.0, 0.0)):
    """Frames at q_map: hinge at body origin; first-joint-outermost
    composition; a joint declared in a body does NOT move that body's own
    origin (the sealed GP1 discipline)."""
    R = IDENT
    for jn, axis, _ in bodies[anchor_name]["joints"]:
        q = wrist[0] if jn == "mutation_wrist_flexion" else wrist[1]
        R = mat_mat(R, axis_rotation(axis, q))
    P = bodies[anchor_name]["pos"]
    positions = {anchor_name: P}
    rotations = {anchor_name: R}
    joint_records = []
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
        refuse("input_pin_missing", "fk_frames did not reach every body")
    return positions, rotations, joint_records


def fk_origin(bodies, anchor_name, q_map, target, wrist=(0.0, 0.0)):
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
# mesh parsing (binary STL; VTP polydata) with AABB grid
# ---------------------------------------------------------------------------

def parse_stl(path):
    """Binary STL -> (scaled vertex list, tri index triples)."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:5] == b"solid" and b"facet" in data[:512]:
        refuse("ascii_stl_unexpected_declared_binary_bytes", path)
    ntri = struct.unpack_from("<I", data, 80)[0]
    if len(data) < 84 + 50 * ntri:
        refuse("stl_truncated", path)
    verts = []
    tris = []
    off = 84
    for _ in range(ntri):
        vals = struct.unpack_from("<12f", data, off)
        off += 50
        idx = len(verts)
        verts.append(scale((vals[3], vals[4], vals[5]), SCALE))
        verts.append(scale((vals[6], vals[7], vals[8]), SCALE))
        verts.append(scale((vals[9], vals[10], vals[11]), SCALE))
        tris.append((idx, idx + 1, idx + 2))
    return verts, tris


def parse_vtp(path):
    """Pinned hand.vtp (ascii DataArrays, MILLIMETRE source units) ->
    (points in metres via the certified 1e-3 conversion, tri triples,
    poly-size histogram). The certified anchor AABB identity is
    hand_vtp_bounds_m == (raw VTP AABB) / 1000, verified at the gate
    (delta 0.0 at run; refusal otherwise). Polys triangulated by a fixed fan
    from each poly's first vertex (identity for all-triangle polys; the
    poly-size histogram is recorded)."""
    root = ET.parse(path).getroot()
    piece = root.find("PolyData").find("Piece")
    npts = int(piece.get("NumberOfPoints"))
    npolys = int(piece.get("NumberOfPolys"))
    pts_da = None
    for da in piece.find("Points"):
        pts_da = da
    coords = [float(x) for x in (pts_da.text or "").split()]
    if len(coords) != 3 * npts:
        refuse("input_pin_mismatch", "vtp point count %d vs %d coords"
               % (npts, len(coords)))
    points = [scale((coords[3 * i], coords[3 * i + 1], coords[3 * i + 2]),
                    1.0e-3) for i in range(npts)]
    poly_das = list(piece.find("Polys"))
    if len(poly_das) != 2:
        refuse("input_pin_mismatch", "vtp polys expect connectivity+offsets")
    conn = [int(x) for x in (poly_das[0].text or "").split()]
    offs = [int(x) for x in (poly_das[1].text or "").split()]
    if len(offs) != npolys:
        refuse("input_pin_mismatch", "vtp offsets %d vs %d polys"
               % (len(offs), npolys))
    tris = []
    hist = {}
    start = 0
    for oi in range(npolys):
        end = offs[oi]
        size = end - start
        hist[size] = hist.get(size, 0) + 1
        if size < 3:
            refuse("input_pin_mismatch", "degenerate vtp poly size %d" % size)
        for k in range(1, size - 1):
            tris.append((conn[start], conn[start + k], conn[start + k + 1]))
        start = end
    return points, tris, hist


def subdivide_tris(verts, tris, levels):
    """Exact planar midpoint subdivision (1 triangle -> 4 per level). The
    represented surface is UNCHANGED: every sub-triangle is a planar subset
    of its parent, so all Level-2 quantities (intersections, distances,
    margins) are mathematically identical; only the per-triangle bounds
    tighten, which sharpens the certified Lipschitz prefilter for coarse
    meshes (the pinned hand.vtp envelope). Deterministic (fixed midpoint
    cache keyed by the sorted vertex-index pair)."""
    for _ in range(levels):
        new_verts = list(verts)
        new_tris = []
        cache = {}
        for (i, j, k) in tris:
            def mid(a, b):
                key = (a, b) if a < b else (b, a)
                if key not in cache:
                    cache[key] = len(new_verts)
                    new_verts.append(scale(add(verts[key[0]], verts[key[1]]),
                                           0.5))
                return cache[key]
            ab = mid(i, j)
            bc = mid(j, k)
            ca = mid(k, i)
            new_tris.extend([(i, ab, ca), (ab, j, bc), (ca, bc, k),
                             (ab, bc, ca)])
        verts = new_verts
        tris = new_tris
    return verts, tris


class Mesh(object):
    """Triangle soup with per-triangle precomputeds and an AABB grid."""

    def __init__(self, name, verts, tris):
        self.name = name
        self.verts = verts
        self.tris = tris
        self.tri_verts = []
        self.tri_aabb = []
        self.tri_diam = []
        self.max_diam = 0.0
        for (i, j, k) in tris:
            a, b, c = verts[i], verts[j], verts[k]
            self.tri_verts.append((a, b, c))
            lo = (min(a[0], b[0], c[0]), min(a[1], b[1], c[1]),
                  min(a[2], b[2], c[2]))
            hi = (max(a[0], b[0], c[0]), max(a[1], b[1], c[1]),
                  max(a[2], b[2], c[2]))
            self.tri_aabb.append((lo, hi))
            d = max(dist(a, b), dist(b, c), dist(c, a))
            self.tri_diam.append(d)
            if d > self.max_diam:
                self.max_diam = d
        lo = [min(v[axis] for v in verts) for axis in range(3)]
        hi = [max(v[axis] for v in verts) for axis in range(3)]
        self.aabb = (tuple(lo), tuple(hi))
        self.span = max(hi[axis] - lo[axis] for axis in range(3))
        self.cell = max(self.max_diam, 1e-9)
        self.grid = {}
        wide = []
        for ti in range(len(tris)):
            (tlo, thi) = self.tri_aabb[ti]
            clo = tuple(int(math.floor(tlo[axis] / self.cell)) for axis in range(3))
            chi = tuple(int(math.floor(thi[axis] / self.cell)) for axis in range(3))
            ncells = ((chi[0] - clo[0] + 1) * (chi[1] - clo[1] + 1)
                      * (chi[2] - clo[2] + 1))
            if ncells > 512:
                wide.append(ti)
                continue
            for cx in range(clo[0], chi[0] + 1):
                for cy in range(clo[1], chi[1] + 1):
                    for cz in range(clo[2], chi[2] + 1):
                        self.grid.setdefault((cx, cy, cz), []).append(ti)
        self.wide = wide

    def query_aabb(self, lo, hi):
        clo = tuple(int(math.floor(lo[axis] / self.cell)) for axis in range(3))
        chi = tuple(int(math.floor(hi[axis] / self.cell)) for axis in range(3))
        seen = set(self.wide)
        out = []
        for cx in range(clo[0], chi[0] + 1):
            for cy in range(clo[1], chi[1] + 1):
                for cz in range(clo[2], chi[2] + 1):
                    bucket = self.grid.get((cx, cy, cz))
                    if bucket:
                        for ti in bucket:
                            if ti not in seen:
                                seen.add(ti)
                                out.append(ti)
        return out

    def query_sphere(self, center, radius):
        lo = tuple(center[axis] - radius for axis in range(3))
        hi = tuple(center[axis] + radius for axis in range(3))
        return self.query_aabb(lo, hi)


# ---------------------------------------------------------------------------
# analytic cylinder primitives (EXACT; local frame via the perp/axial map,
# which is a global isometry: image-dot = world-dot)
# ---------------------------------------------------------------------------

def cyl_to_local(p, o, u):
    d = sub(p, o)
    z = dot(d, u)
    perp = sub(d, scale(u, z))
    return (perp[0], perp[1], z)


def cyl_sdf(p, R, hh):
    """Exact signed distance to the closed cylinder surface (negative inside).
    Region form, exact per region."""
    rho = math.sqrt(p[0] * p[0] + p[1] * p[1])
    dr = rho - R
    dz = abs(p[2]) - hh
    if dr >= 0.0 and dz >= 0.0:
        return math.sqrt(dr * dr + dz * dz)
    if dr >= 0.0:
        return dr
    if dz >= 0.0:
        return dz
    return max(dr, dz)


def seg_solid_intersect(a, b, R, hh):
    """Exact: does segment ab meet the closed solid cylinder?"""
    if cyl_sdf(a, R, hh) < 0.0 or cyl_sdf(b, R, hh) < 0.0:
        return True
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dz = b[2] - a[2]
    A = dx * dx + dy * dy
    B = 2.0 * (a[0] * dx + a[1] * dy)
    C = a[0] * a[0] + a[1] * a[1] - R * R
    if A > 0.0:
        disc = B * B - 4.0 * A * C
        if disc >= 0.0:
            sq = math.sqrt(disc)
            for t in ((-B - sq) / (2.0 * A), (-B + sq) / (2.0 * A)):
                if 0.0 <= t <= 1.0:
                    if abs(a[2] + t * dz) <= hh:
                        return True
    if dz != 0.0:
        for zc in (hh, -hh):
            t = (zc - a[2]) / dz
            if 0.0 <= t <= 1.0:
                x = a[0] + t * dx
                y = a[1] + t * dy
                if x * x + y * y <= R * R:
                    return True
    return False


def _q_conic(a, e1, e2, R):
    """Lateral constraint on a plane: Q(s,t) <= 0 inside the cylinder's
    radial bound, for p = a + s e1 + t e2 in cylinder-LOCAL coords.
    Q(s,t) = [s t] G [s t]^T + g.[s t] + F with G = E^T E, E = [e1_xy e2_xy]."""
    A = e1[0] * e1[0] + e1[1] * e1[1]
    B2 = e1[0] * e2[0] + e1[1] * e2[1]
    C = e2[0] * e2[0] + e2[1] * e2[1]
    D = 2.0 * (a[0] * e1[0] + a[1] * e1[1])
    E = 2.0 * (a[0] * e2[0] + a[1] * e2[1])
    F = a[0] * a[0] + a[1] * a[1] - R * R
    return ((A, B2), (B2, C)), (D, E), F


def _q_eval(G, g, F, s, t):
    return (G[0][0] * s * s + 2.0 * G[0][1] * s * t + G[1][1] * t * t
            + g[0] * s + g[1] * t + F)


def _in_simplex(s, t):
    return (s >= 0.0) and (t >= 0.0) and (s + t <= 1.0)


def _ellipse_support_pts(G, g):
    """Center and the 4 axis-extreme points of the ellipse
    {x: (x-xc)^T G (x-xc) <= rho^2} for the conic x^T G x + g.x + F = 0
    with G positive definite."""
    det = G[0][0] * G[1][1] - G[0][1] * G[1][0]
    if det <= 0.0:
        return None, []
    Ginv = ((G[1][1] / det, -G[0][1] / det),
            (-G[1][0] / det, G[0][0] / det))
    xc = (-(Ginv[0][0] * g[0] + Ginv[0][1] * g[1]),
          -(Ginv[1][0] * g[0] + Ginv[1][1] * g[1]))
    pts = []
    for d in ((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)):
        Gd = (Ginv[0][0] * d[0] + Ginv[0][1] * d[1],
              Ginv[1][0] * d[0] + Ginv[1][1] * d[1])
        dd = math.sqrt(d[0] * Gd[0] + d[1] * Gd[1])
        if dd > 0.0:
            pts.append((xc[0] + Gd[0] / dd, xc[1] + Gd[1] / dd))
    return xc, pts


def tri_solid_intersect_local(a, b, c, R, hh):
    """Exact triangle vs closed solid cylinder in cylinder-LOCAL coords.
    Complete for the convex solid: (i) a vertex inside; (ii) an edge crossing
    the boundary surface; (iii) the plane section K = solid-intersect-plane
    meeting the triangle (via K-boundary representatives: cap-line crossings,
    ellipse/cap-line vertices, ellipse axis extremes)."""
    if cyl_sdf(a, R, hh) < 0.0 or cyl_sdf(b, R, hh) < 0.0 \
            or cyl_sdf(c, R, hh) < 0.0:
        return True
    for (p, q) in ((a, b), (b, c), (c, a)):
        if seg_solid_intersect(p, q, R, hh):
            return True
    e1 = sub(b, a)
    e2 = sub(c, a)
    G, g, F = _q_conic(a, e1, e2, R)
    verts2d = ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0))
    az = a[2]
    e1z = e1[2]
    e2z = e2[2]
    plane_flat = (e1z == 0.0 and e2z == 0.0)

    def z_at(st):
        return az + st[0] * e1z + st[1] * e2z

    # (iii-a) any triangle vertex in K
    for st in verts2d:
        if _q_eval(G, g, F, st[0], st[1]) <= 0.0 and abs(z_at(st)) <= hh:
            return True
    # (iii-b) any triangle edge crossing the ellipse curve (inside the strip)
    for (i, j) in ((0, 1), (1, 2), (2, 0)):
        p0 = verts2d[i]
        p1 = verts2d[j]
        d0 = (p1[0] - p0[0], p1[1] - p0[1])
        A = G[0][0] * d0[0] * d0[0] + 2.0 * G[0][1] * d0[0] * d0[1] \
            + G[1][1] * d0[1] * d0[1]
        B = 2.0 * (G[0][0] * p0[0] * d0[0]
                   + G[0][1] * (p0[0] * d0[1] + p0[1] * d0[0])
                   + G[1][1] * p0[1] * d0[1]) + g[0] * d0[0] + g[1] * d0[1]
        C = _q_eval(G, g, F, p0[0], p0[1])
        roots = []
        if A != 0.0:
            disc = B * B - 4.0 * A * C
            if disc >= 0.0:
                sq = math.sqrt(disc)
                roots = ((-B - sq) / (2.0 * A), (-B + sq) / (2.0 * A))
        elif B != 0.0:
            roots = (-C / B,)
        for u in roots:
            if 0.0 <= u <= 1.0:
                st = (p0[0] + u * d0[0], p0[1] + u * d0[1])
                if abs(z_at(st)) <= hh:
                    return True
    # (iii-c) any triangle edge crossing a cap line z = +-hh (inside ellipse)
    if not plane_flat:
        for zc in (hh, -hh):
            for (i, j) in ((0, 1), (1, 2), (2, 0)):
                p0 = verts2d[i]
                p1 = verts2d[j]
                dz = (p1[0] - p0[0]) * e1z + (p1[1] - p0[1]) * e2z
                z0 = z_at(p0)
                if dz != 0.0:
                    u = (zc - z0) / dz
                    if 0.0 <= u <= 1.0:
                        st = (p0[0] + u * (p1[0] - p0[0]),
                              p0[1] + u * (p1[1] - p0[1]))
                        if _q_eval(G, g, F, st[0], st[1]) <= 0.0:
                            return True
    # (iii-d) K vertices: cap line x ellipse intersections inside the simplex
    if not plane_flat:
        for zc in (hh, -hh):
            # line z(s,t) = zc; substitute t = alpha - beta*s (e2z != 0) with
            # alpha = (zc - az)/e2z, beta = e1z/e2z, and solve Q(s, t(s)) = 0
            if e2z != 0.0:
                alpha = (zc - az) / e2z
                beta = e1z / e2z
                As = G[0][0] - 2.0 * G[0][1] * beta + G[1][1] * beta * beta
                Bs = 2.0 * G[0][1] * alpha - 2.0 * G[1][1] * alpha * beta \
                    + g[0] - g[1] * beta
                Cs = _q_eval(G, g, F, 0.0, alpha)
                if As != 0.0:
                    disc = Bs * Bs - 4.0 * As * Cs
                    if disc >= 0.0:
                        sq = math.sqrt(disc)
                        for s in ((-Bs - sq) / (2.0 * As), (-Bs + sq) / (2.0 * As)):
                            t = alpha - beta * s
                            if _in_simplex(s, t):
                                return True
                elif Bs != 0.0:
                    s = -Cs / Bs
                    t = alpha - beta * s
                    if _in_simplex(s, t):
                        return True
            if e1z != 0.0:
                # s = alpha - beta*t with alpha = (zc - az)/e1z, beta = e2z/e1z
                alpha = (zc - az) / e1z
                beta = e2z / e1z
                At = G[1][1] - 2.0 * G[0][1] * beta + G[0][0] * beta * beta
                Bt = 2.0 * G[0][1] * alpha - 2.0 * G[0][0] * alpha * beta \
                    + g[1] - g[0] * beta
                Ct = _q_eval(G, g, F, alpha, 0.0)
                if At != 0.0:
                    disc = Bt * Bt - 4.0 * At * Ct
                    if disc >= 0.0:
                        sq = math.sqrt(disc)
                        for t in ((-Bt - sq) / (2.0 * At), (-Bt + sq) / (2.0 * At)):
                            s = alpha - beta * t
                            if _in_simplex(s, t):
                                return True
                elif Bt != 0.0:
                    t = -Ct / Bt
                    s = alpha - beta * t
                    if _in_simplex(s, t):
                        return True
    # (iii-e) ellipse axis extremes inside the simplex (and in the strip):
    # catches the ellipse-contained-in-triangle case with no edge crossings
    _, ext = _ellipse_support_pts(G, g)
    for st in ext:
        if _in_simplex(st[0], st[1]) and abs(z_at(st)) <= hh:
            return True
    return False


def tri_solid_intersect(a, b, c, R, hh):
    """Exact 3D triangle vs closed solid cylinder (world/local agnostic: the
    points must already be in the cylinder-local frame)."""
    return tri_solid_intersect_local(a, b, c, R, hh)


def tri_min_f_disjoint(a, b, c, R, hh):
    """Exact minimum of the cylinder SDF over the triangle when the triangle
    and the solid are DISJOINT. The SDF has unit gradient almost everywhere
    and is piecewise smooth, so a per-edge minimum is attained at an endpoint
    or at an exact region-boundary crossing (the lateral cylinder rho = R or
    the cap planes z = +-hh); the triangle minimum is the min over the 3
    vertices, the 3 edges' exact candidate sets, and the plane-support
    branch. Closed form, no iteration."""
    best = min(cyl_sdf(a, R, hh), cyl_sdf(b, R, hh), cyl_sdf(c, R, hh))

    def edge_min(p, q):
        dx = q[0] - p[0]
        dy = q[1] - p[1]
        dz = q[2] - p[2]
        cands = [0.0, 1.0]
        A = dx * dx + dy * dy
        B = 2.0 * (p[0] * dx + p[1] * dy)
        C = p[0] * p[0] + p[1] * p[1] - R * R
        if A > 0.0:
            disc = B * B - 4.0 * A * C
            if disc >= 0.0:
                sq = math.sqrt(disc)
                cands.extend([(-B - sq) / (2.0 * A), (-B + sq) / (2.0 * A)])
        if dz != 0.0:
            cands.extend([(hh - p[2]) / dz, (-hh - p[2]) / dz])
        else:
            cands.extend([0.0, 1.0])
        m = min(cyl_sdf(p, R, hh), cyl_sdf(q, R, hh))
        for t in cands:
            if 0.0 <= t <= 1.0:
                m = min(m, cyl_sdf((p[0] + t * dx, p[1] + t * dy,
                                    p[2] + t * dz), R, hh))
        return m

    for (p, q) in ((a, b), (b, c), (c, a)):
        best = min(best, edge_min(p, q))

    nvec = unit(cross(sub(b, a), sub(c, a)))
    perp2 = nvec[0] * nvec[0] + nvec[1] * nvec[1]
    h_min = -R * math.sqrt(perp2) - hh * abs(nvec[2])
    dist_plane = dot(nvec, a) - h_min
    if dist_plane > 0.0:
        if perp2 > 1e-18:
            sp = math.sqrt(perp2)
            qstar = (-R * nvec[0] / sp, -R * nvec[1] / sp,
                     -hh if nvec[2] >= 0.0 else hh)
        else:
            qstar = (0.0, 0.0, -hh if nvec[2] >= 0.0 else hh)
        wp = sub(sub(qstar, a), scale(nvec, dot(sub(qstar, a), nvec)))
        e1v = sub(b, a)
        e2v = sub(c, a)
        m11 = dot(e1v, e1v)
        m12 = dot(e1v, e2v)
        m22 = dot(e2v, e2v)
        r1 = dot(wp, e1v)
        r2 = dot(wp, e2v)
        det = m11 * m22 - m12 * m12
        if det != 0.0:
            su = (r1 * m22 - r2 * m12) / det
            sv = (r2 * m11 - r1 * m12) / det
            if _in_simplex(su, sv):
                best = min(best, dist_plane)
    return best


def tri_depth_local(a, b, c, R, hh, tau):
    """Certified penetration depth = -(min f) for a triangle already known to
    intersect the shrunk solid. Certified bisection on the exact predicate
    intersect(T, solid(R + x, hh + x)); lo = largest x known NOT intersecting,
    hi = smallest x known intersecting; starts hi = -tau (given)."""
    hi = -tau
    if not tri_solid_intersect_local(a, b, c, R + hi, hh + hi):
        refuse("depth_bracket_invalid", "triangle did not intersect shrunk solid")
    x = -2.0 * tau
    lo = -DEPTH_SEARCH_MAX
    while True:
        if x <= -DEPTH_SEARCH_MAX:
            lo = -DEPTH_SEARCH_MAX
            break
        if not tri_solid_intersect_local(a, b, c, R + x, hh + x):
            lo = x
            break
        hi = x
        x *= 2.0
    for _ in range(DEPTH_SEARCH_ITERS):
        mid = (lo + hi) / 2.0
        if tri_solid_intersect_local(a, b, c, R + mid, hh + mid):
            hi = mid
        else:
            lo = mid
    return -(hi + lo) / 2.0


# ---------------------------------------------------------------------------
# triangle-triangle primitives (exact; deterministic branch order)
# ---------------------------------------------------------------------------

def dist_point_tri(p, a, b, c):
    """Exact point-triangle distance (Ericson region decomposition)."""
    ab = sub(b, a)
    ac = sub(c, a)
    ap = sub(p, a)
    d1 = dot(ab, ap)
    d2 = dot(ac, ap)
    if d1 <= 0.0 and d2 <= 0.0:
        return dist(p, a)
    bp = sub(p, b)
    d3 = dot(ab, bp)
    d4 = dot(ac, bp)
    if d3 >= 0.0 and d4 <= d3:
        return dist(p, b)
    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v = d1 / (d1 - d3)
        return dist(p, add(a, scale(ab, v)))
    cp = sub(p, c)
    d5 = dot(ab, cp)
    d6 = dot(ac, cp)
    if d6 >= 0.0 and d5 <= d6:
        return dist(p, c)
    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w = d2 / (d2 - d6)
        return dist(p, add(a, scale(ac, w)))
    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        return dist(p, add(b, scale(sub(c, b), w)))
    denom = 1.0 / (va + vb + vc)
    v = vb * denom
    w = vc * denom
    return dist(p, add(a, add(scale(ab, v), scale(ac, w))))


def dist_seg_seg(p1, q1, p2, q2):
    """Exact segment-segment distance (clamped parametric, fixed order)."""
    d1 = sub(q1, p1)
    d2 = sub(q2, p2)
    r = sub(p1, p2)
    a = dot(d1, d1)
    e = dot(d2, d2)
    f = dot(d2, r)
    if a <= 0.0 and e <= 0.0:
        return dist(p1, p2)
    if a <= 0.0:
        s = 0.0
        t = min(1.0, max(0.0, f / e))
    else:
        c = dot(d1, r)
        if e <= 0.0:
            t = 0.0
            s = min(1.0, max(0.0, -c / a))
        else:
            b = dot(d1, d2)
            denom = a * e - b * b
            s = min(1.0, max(0.0, (b * f - c * e) / denom)) if denom != 0.0 else 0.0
            t = (b * s + f) / e
            if t < 0.0:
                t = 0.0
                s = min(1.0, max(0.0, -c / a))
            elif t > 1.0:
                t = 1.0
                s = min(1.0, max(0.0, (b - c) / a))
    return dist(add(p1, scale(d1, s)), add(p2, scale(d2, t)))


def dist_tri_tri(t1, t2):
    """Exact triangle-triangle distance for disjoint triangles: the complete
    candidate set (9 edge-edge + 6 vertex-face)."""
    best = float("inf")
    for (p, q) in ((t1[0], t1[1]), (t1[1], t1[2]), (t1[2], t1[0])):
        for (r, s) in ((t2[0], t2[1]), (t2[1], t2[2]), (t2[2], t2[0])):
            best = min(best, dist_seg_seg(p, q, r, s))
    for v in t1:
        best = min(best, dist_point_tri(v, t2[0], t2[1], t2[2]))
    for v in t2:
        best = min(best, dist_point_tri(v, t1[0], t1[1], t1[2]))
    return best


def _orient2d(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_seg2d(a, b, c):
    return (min(a[0], b[0]) <= c[0] <= max(a[0], b[0])) and \
           (min(a[1], b[1]) <= c[1] <= max(a[1], b[1]))


def _seg2d_intersect(p1, p2, p3, p4):
    d1 = _orient2d(p3, p4, p1)
    d2 = _orient2d(p3, p4, p2)
    d3 = _orient2d(p1, p2, p3)
    d4 = _orient2d(p1, p2, p4)
    if ((d1 > 0.0 and d2 < 0.0) or (d1 < 0.0 and d2 > 0.0)) and \
       ((d3 > 0.0 and d4 < 0.0) or (d3 < 0.0 and d4 > 0.0)):
        return True
    if d1 == 0.0 and _on_seg2d(p3, p4, p1):
        return True
    if d2 == 0.0 and _on_seg2d(p3, p4, p2):
        return True
    if d3 == 0.0 and _on_seg2d(p1, p2, p3):
        return True
    if d4 == 0.0 and _on_seg2d(p1, p2, p4):
        return True
    return False


def _pt_in_tri2d(p, tri):
    d1 = _orient2d(tri[0], tri[1], p)
    d2 = _orient2d(tri[1], tri[2], p)
    d3 = _orient2d(tri[2], tri[0], p)
    has_neg = (d1 < 0.0) or (d2 < 0.0) or (d3 < 0.0)
    has_pos = (d1 > 0.0) or (d2 > 0.0) or (d3 > 0.0)
    return not (has_neg and has_pos)


def _dominant_axis(n):
    nx, ny, nz = abs(n[0]), abs(n[1]), abs(n[2])
    if nx >= ny and nx >= nz:
        return (1, 2)
    if ny >= nz:
        return (0, 2)
    return (0, 1)


def _coplanar_intersect(t1, t2, n1):
    i0, i1 = _dominant_axis(n1)
    T1 = [(v[i0], v[i1]) for v in t1]
    T2 = [(v[i0], v[i1]) for v in t2]
    for (p, q) in ((T1[0], T1[1]), (T1[1], T1[2]), (T1[2], T1[0])):
        for (r, s) in ((T2[0], T2[1]), (T2[1], T2[2]), (T2[2], T2[0])):
            if _seg2d_intersect(p, q, r, s):
                return True
    if _pt_in_tri2d(T2[0], T1):
        return True
    if _pt_in_tri2d(T1[0], T2):
        return True
    return False


def _seg_touches_tri(seg_a, seg_b, tri):
    """Exact: does the closed segment meet the closed triangle (any contact)?"""
    if dist_point_tri(seg_a, tri[0], tri[1], tri[2]) == 0.0:
        return True
    if dist_point_tri(seg_b, tri[0], tri[1], tri[2]) == 0.0:
        return True
    for (p, q) in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
        if dist_seg_seg(seg_a, seg_b, p, q) == 0.0:
            return True
    return False


def _interval_pair(dv, v0, v1, v2):
    """Moller interval construction for one triangle against the other's
    plane; returns None when the triangle lies fully on one side."""
    zs = [i for i in range(3) if dv[i] == 0.0]
    vs = (v0, v1, v2)
    if len(zs) == 3:
        return "coplanar"
    if len(zs) == 2:
        i0, i1 = zs
        return ("edge_in_plane", vs[i0], vs[i1])
    if len(zs) == 1:
        z = zs[0]
        o = [i for i in range(3) if i != z]
        i0, i1 = o
        if (dv[i0] > 0.0) == (dv[i1] > 0.0):
            return (vs[z], vs[z])
        a = vs[i0]
        b = vs[i1]
        t = dv[i0] / (dv[i0] - dv[i1])
        return (vs[z], (a[0] + t * (b[0] - a[0]),
                        a[1] + t * (b[1] - a[1]),
                        a[2] + t * (b[2] - a[2])))
    # no vertex on the plane: the standard two-point construction
    pos = [i for i in range(3) if dv[i] > 0.0]
    if len(pos) == 1:
        p = pos[0]
        o = [i for i in range(3) if i != p]
        i0, i1 = o
    else:
        n = [i for i in range(3) if dv[i] < 0.0]
        p = n[0]
        o = [i for i in range(3) if i != p]
        i0, i1 = o
    a = vs[p]
    b = vs[i0]
    c = vs[i1]
    t0 = dv[p] / (dv[p] - dv[i0])
    t1 = dv[p] / (dv[p] - dv[i1])
    pt_a = (a[0] + t0 * (b[0] - a[0]), a[1] + t0 * (b[1] - a[1]),
            a[2] + t0 * (b[2] - a[2]))
    pt_b = (a[0] + t1 * (c[0] - a[0]), a[1] + t1 * (c[1] - a[1]),
            a[2] + t1 * (c[2] - a[2]))
    return (pt_a, pt_b)


def tri_tri_intersect(t1, t2):
    """Exact triangle-triangle intersection (Moller interval method with
    explicit on-plane handling; deterministic branch order). Touching counts
    as intersecting (inclusive semantics, documented)."""
    n1 = cross(sub(t1[1], t1[0]), sub(t1[2], t1[0]))
    d1 = -dot(n1, t1[0])
    du = tuple(dot(n1, v) + d1 for v in t2)
    n2 = cross(sub(t2[1], t2[0]), sub(t2[2], t2[0]))
    d2 = -dot(n2, t2[0])
    dv = tuple(dot(n2, v) + d2 for v in t1)
    if (du[0] > 0.0 and du[1] > 0.0 and du[2] > 0.0) or \
       (du[0] < 0.0 and du[1] < 0.0 and du[2] < 0.0):
        return False
    if (dv[0] > 0.0 and dv[1] > 0.0 and dv[2] > 0.0) or \
       (dv[0] < 0.0 and dv[1] < 0.0 and dv[2] < 0.0):
        return False
    r1 = _interval_pair(du, t2[0], t2[1], t2[2])
    r2 = _interval_pair(dv, t1[0], t1[1], t1[2])
    if r1 == "coplanar" and r2 == "coplanar":
        return _coplanar_intersect(t1, t2, n1)
    if r1 == "coplanar" or r2 == "coplanar":
        # one triangle lies in the other's plane: exact degenerate handling
        if r1 == "coplanar":
            flat, other = t2, t1
        else:
            flat, other = t1, t2
        for (p, q) in ((other[0], other[1]), (other[1], other[2]),
                       (other[2], other[0])):
            if _seg_touches_tri(p, q, flat):
                return True
        return False
    if isinstance(r1, tuple) and len(r1) == 3:
        # edge_in_plane of t2: that edge must meet t1
        return _seg_touches_tri(r1[1], r1[2], t1)
    if isinstance(r2, tuple) and len(r2) == 3:
        return _seg_touches_tri(r2[1], r2[2], t2)
    # both are proper intervals: project on the dominant axis of N1 x N2
    D = cross(n1, n2)
    ax = _dominant_axis(D)
    i0 = ax[0]
    a0, a1 = r1[0][i0], r1[1][i0]
    b0, b1 = r2[0][i0], r2[1][i0]
    if a0 > a1:
        a0, a1 = a1, a0
    if b0 > b1:
        b0, b1 = b1, b0
    return a0 <= b1 and b0 <= a1


RAY_DIRS = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
            (1.0, 1.0, 1.0), (-1.0, 1.0, 0.5), (0.5, -1.0, 1.0),
            (1.0, 0.5, -1.0), (-0.5, -0.5, -1.0),
            (0.6180339887498949, 0.38202201979262192, 1.0),
            (1.0, 0.6180339887498949, 0.38202201979262192),
            (0.38202201979262192, 1.0, 0.6180339887498949),
            (-1.0, -0.6180339887498949, -0.38202201979262192))


def _seg_tri_crossing(p, q, a, b, c):
    """Exact segment vs triangle crossing for parity counting.
    True (proper crossing), False (none), 'degenerate' (on-boundary hit)."""
    d = sub(q, p)
    e1 = sub(b, a)
    e2 = sub(c, a)
    h = cross(d, e2)
    det = dot(e1, h)
    if det == 0.0:
        # parallel: degenerate only if they actually meet
        if _seg_touches_tri(p, q, (a, b, c)):
            return "degenerate"
        return False
    inv = 1.0 / det
    s = sub(p, a)
    u = dot(s, h) * inv
    if u < 0.0 or u > 1.0:
        return False
    qvec = cross(s, e1)
    v = dot(d, qvec) * inv
    if v < 0.0 or u + v > 1.0:
        return False
    t = dot(e2, qvec) * inv
    if t < 0.0 or t > 1.0:
        return False
    if u == 0.0 or v == 0.0 or u + v == 1.0:
        # the ray grazes a triangle edge or vertex: parity ambiguous
        return "degenerate"
    if t == 0.0 or t == 1.0:
        # a segment endpoint lies in the triangle's plane: degenerate ONLY if
        # that endpoint is inside the triangle; a plane-hit outside the
        # triangle is simply no crossing
        if 0.0 <= u <= 1.0 and 0.0 <= v <= 1.0 and u + v <= 1.0:
            return "degenerate"
        return False
    return True


def point_in_mesh(p, mesh):
    """Containment by ray parity (closed vendor meshes). A bounded ray twice
    the mesh span is used; the far endpoint is outside the mesh. Degenerate
    crossings re-cast through a fixed deterministic direction list; if every
    direction is degenerate (points on the full symmetry-diagonal network of
    the mesh), the list is retried once from a deterministically
    micro-shifted origin (1e-9 m; this only differs from the true answer when
    p is itself within ~1e-9 of the surface, where the class is decided by
    the distance machinery, not parity)."""
    for origin in (p, add(p, (1.0e-9, 0.6180339887498949e-9,
                              0.38202201979262192e-9))):
        for direction in RAY_DIRS:
            far = add(origin, scale(direction, 2.0 * mesh.span + 1.0))
            count = 0
            degenerate = False
            for ti in mesh.query_aabb((min(origin[0], far[0]),
                                       min(origin[1], far[1]),
                                       min(origin[2], far[2])),
                                      (max(origin[0], far[0]),
                                       max(origin[1], far[1]),
                                       max(origin[2], far[2]))):
                (a, b, c) = mesh.tri_verts[ti]
                res = _seg_tri_crossing(origin, far, a, b, c)
                if res == "degenerate":
                    degenerate = True
                    break
                if res:
                    count += 1
            if degenerate:
                continue
            return (count % 2) == 1
    refuse("containment_ray_exhausted", mesh.name + " at " + str(p))


def point_depth_in_mesh(p, mesh):
    """Exact depth of a point inside (or near) a closed mesh: the exact
    distance to the surface (min point-triangle distance)."""
    best = float("inf")
    radius = mesh.span
    for ti in mesh.query_sphere(p, radius):
        (a, b, c) = mesh.tri_verts[ti]
        best = min(best, dist_point_tri(p, a, b, c))
    if best == float("inf"):
        for ti in range(len(mesh.tris)):
            (a, b, c) = mesh.tri_verts[ti]
            best = min(best, dist_point_tri(p, a, b, c))
    return best


# ---------------------------------------------------------------------------
# Level-1 spheres (the unchanged GP1-CC2 construction)
# ---------------------------------------------------------------------------

def bounding_sphere_scaled(verts):
    """Declared CC2 construction: center = scaled-AABB midpoint; radius =
    max vertex distance to that center (conservative)."""
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    center = ((min(xs) + max(xs)) / 2.0,
              (min(ys) + max(ys)) / 2.0,
              (min(zs) + max(zs)) / 2.0)
    r2 = 0.0
    for v in verts:
        d = sub(v, center)
        d2 = dot(d, d)
        if d2 > r2:
            r2 = d2
    return center, math.sqrt(r2)


def anchor_bounds_sphere(bounds):
    """Same construction on the certified anchor AABB (hand_vtp_bounds_m):
    center = AABB midpoint; radius = max distance to the 8 corners."""
    lo = tuple(float(x) for x in bounds[0])
    hi = tuple(float(x) for x in bounds[1])
    center = tuple((lo[k] + hi[k]) / 2.0 for k in range(3))
    r2 = 0.0
    for corner in itertools.product((lo[0], hi[0]), (lo[1], hi[1]),
                                    (lo[2], hi[2])):
        d = sub(corner, center)
        r2 = max(r2, dot(d, d))
    return center, math.sqrt(r2)


# ---------------------------------------------------------------------------
# scenes: world-space bodies at a configuration
# ---------------------------------------------------------------------------

class BodyFrame(object):
    """One rigid body's world-space mesh + Level-1 sphere at a configuration."""

    def __init__(self, name, local_verts, tris, pos, rot, sphere_center_local,
                 sphere_r, is_anchor=False, is_envelope=False):
        self.name = name
        self.pos = pos
        self.rot = rot
        self.is_anchor = is_anchor
        self.is_envelope = is_envelope
        wv = [add(pos, mat_vec(rot, v)) for v in local_verts]
        self.mesh = Mesh(name, wv, tris)
        self.pair_mesh = self.mesh
        self.sphere_center = add(pos, mat_vec(rot, sphere_center_local))
        self.sphere_r = sphere_r


def build_hand_frames(bodies, stl_meshes_local, positions, rotations,
                      sphere_locals, anchor_name, vtp_local):
    """World frames for all 20 bodies (19 STL bones + the anchor envelope).
    The envelope mesh is exact-planar-subdivided 2 levels (the represented
    surface is UNCHANGED - every sub-triangle is a planar subset of its
    parent; this only sharpens the certified Lipschitz prefilter for the
    coarse skin triangles and is declared in the receipt). The Level-1
    spheres are computed from the ORIGINAL pinned vertex set, never from the
    subdivision points."""
    frames = {}
    for name in sorted(bodies):
        if name == anchor_name:
            sv, st = subdivide_tris(vtp_local[0], vtp_local[1], 2)
            frames[name] = BodyFrame(
                name, sv, st, positions[name],
                rotations[name], sphere_locals[name][0], sphere_locals[name][1],
                is_anchor=True, is_envelope=True)
            wv_coarse = [add(positions[name],
                             mat_vec(rotations[name], v))
                         for v in vtp_local[0]]
            frames[name].pair_mesh = Mesh(name + "_pair", wv_coarse,
                                          vtp_local[1])
        else:
            verts, tris = stl_meshes_local[name]
            frames[name] = BodyFrame(
                name, verts, tris, positions[name], rotations[name],
                sphere_locals[name][0], sphere_locals[name][1])
    return frames


def level1_pair_rows(frames, bodies, anchor_name):
    """LEVEL 1: the sphere screen recorded for all 190 body pairs."""
    rows = []
    names = sorted(frames)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            na, nb = names[i], names[j]
            fa, fb = frames[na], frames[nb]
            d = dist(fa.sphere_center, fb.sphere_center)
            rsum = fa.sphere_r + fb.sphere_r
            adjacent = (bodies[na]["parent"] == nb) or \
                       (bodies[nb]["parent"] == na)
            rows.append(dict(a=na, b=nb, distance=d, radius_sum=rsum,
                             clearance=d - rsum, adjacent=bool(adjacent),
                             proxy_overlap=bool(d < rsum)))
    return rows


# ---------------------------------------------------------------------------
# mesh-mesh pair adjudication (bones) with the joint-region ledger
# ---------------------------------------------------------------------------

def _tri_tri_segment(t1, t2):
    """Exact intersection segment (or None) for two triangles, inclusive of
    touching contacts. Deterministic."""
    n1 = cross(sub(t1[1], t1[0]), sub(t1[2], t1[0]))
    d1 = -dot(n1, t1[0])
    du = tuple(dot(n1, v) + d1 for v in t2)
    n2 = cross(sub(t2[1], t2[0]), sub(t2[2], t2[0]))
    d2 = -dot(n2, t2[0])
    dv = tuple(dot(n2, v) + d2 for v in t1)
    if (du[0] > 0.0 and du[1] > 0.0 and du[2] > 0.0) or \
       (du[0] < 0.0 and du[1] < 0.0 and du[2] < 0.0):
        return None
    if (dv[0] > 0.0 and dv[1] > 0.0 and dv[2] > 0.0) or \
       (dv[0] < 0.0 and dv[1] < 0.0 and dv[2] < 0.0):
        return None
    r1 = _interval_pair(du, t2[0], t2[1], t2[2])
    r2 = _interval_pair(dv, t1[0], t1[1], t1[2])
    if r1 == "coplanar" and r2 == "coplanar":
        if _coplanar_intersect(t1, t2, n1):
            # proximity witness: the deterministic minimum candidate
            best = (None, None)
            bestd = float("inf")
            for v in t1:
                dd = dist_point_tri(v, t2[0], t2[1], t2[2])
                if dd < bestd:
                    bestd = dd
                    best = (v, v)
            for (p, q) in ((t1[0], t1[1]), (t1[1], t1[2]), (t1[2], t1[0])):
                for (r_, s_) in ((t2[0], t2[1]), (t2[1], t2[2]),
                                 (t2[2], t2[0])):
                    dd = dist_seg_seg(p, q, r_, s_)
                    if dd < bestd:
                        bestd = dd
                        best = (p, r_)
            return (best[0], best[1])
        return None
    if r1 == "coplanar" or r2 == "coplanar":
        if r1 == "coplanar":
            flat, other = t2, t1
        else:
            flat, other = t1, t2
        for (p, q) in ((other[0], other[1]), (other[1], other[2]),
                       (other[2], other[0])):
            if _seg_touches_tri(p, q, flat):
                return (p, p) if dist_point_tri(p, flat[0], flat[1],
                                                flat[2]) == 0.0 else (p, q)
        return None
    if isinstance(r1, tuple) and len(r1) == 3:
        if _seg_touches_tri(r1[1], r1[2], t1):
            return (r1[1], r1[2])
        return None
    if isinstance(r2, tuple) and len(r2) == 3:
        if _seg_touches_tri(r2[1], r2[2], t2):
            return (r2[1], r2[2])
        return None
    # both are proper intervals on the intersection line: project on the
    # dominant axis of N1 x N2 and test the overlap
    D = cross(n1, n2)
    ax = _dominant_axis(D)
    i0 = ax[0]
    a0, a1 = r1[0][i0], r1[1][i0]
    b0, b1 = r2[0][i0], r2[1][i0]
    if a0 > a1:
        a0, a1 = a1, a0
    if b0 > b1:
        b0, b1 = b1, b0
    L = max(a0, b0)
    U = min(a1, b1)
    if L > U:
        return None

    def point_at(x):
        if r1[1][i0] != r1[0][i0]:
            t = (x - r1[0][i0]) / (r1[1][i0] - r1[0][i0])
            return tuple(r1[0][k] + t * (r1[1][k] - r1[0][k]) for k in range(3))
        if r2[1][i0] != r2[0][i0]:
            t = (x - r2[0][i0]) / (r2[1][i0] - r2[0][i0])
            return tuple(r2[0][k] + t * (r2[1][k] - r2[0][k]) for k in range(3))
        # degenerate: both intervals are single points
        return tuple(r1[0])

    if L == U:
        p = point_at(L)
        return (p, p)
    return (point_at(L), point_at(U))


def _aabb_gap(ab1, ab2):
    dx = max(ab1[0][0] - ab2[1][0], ab2[0][0] - ab1[1][0], 0.0)
    dy = max(ab1[0][1] - ab2[1][1], ab2[0][1] - ab1[1][1], 0.0)
    dz = max(ab1[0][2] - ab2[1][2], ab2[0][2] - ab1[1][2], 0.0)
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def _pair_candidates(fa, fb):
    """Exact prefiltered candidate triangle pairs (AABB overlap via grid).
    The smaller mesh drives; returns (i, j, swapped) with i indexing the
    driver mesh and swapped indicating that the driver is fb."""
    out = []
    ma, mb = fa.pair_mesh, fb.pair_mesh
    if _aabb_gap(ma.aabb, mb.aabb) > 0.0:
        return out
    if len(mb.tris) < len(ma.tris):
        bhi = ma.aabb
        driver, other = mb, ma
        swapped = True
    else:
        bhi = mb.aabb
        driver, other = ma, mb
        swapped = False
    region = driver.query_aabb(bhi[0], bhi[1])
    for ti in region:
        tlo, thi = driver.tri_aabb[ti]
        for tj in other.query_aabb(tlo, thi):
            out.append((ti, tj, swapped))
    return out


def mesh_pair_intersection_segments(fa, fb):
    """All exact tri-tri intersection segments (inclusive of touching).
    Returns a list of (p, q, ti, tj) with ti indexing fa.mesh and tj
    indexing fb.mesh."""
    segs = []
    for (ti, tj, swapped) in _pair_candidates(fa, fb):
        if swapped:
            t1 = fb.pair_mesh.tri_verts[ti]   # driver was fb
            t2 = fa.pair_mesh.tri_verts[tj]   # other was fa
        else:
            t1 = fa.pair_mesh.tri_verts[ti]
            t2 = fb.pair_mesh.tri_verts[tj]
        seg = _tri_tri_segment(t1, t2)
        if seg is not None:
            segs.append((seg[0], seg[1], ti, tj))
    return segs


def _seed_upper_bound(ma, mb):
    """A deterministic exact upper bound for the mesh-mesh minimum: the
    exact distance between the A-triangle whose AABB center is closest to
    B's AABB center and the B-triangle whose AABB center is closest to that
    A-triangle's center (a real pair, so the value is a valid upper bound,
    always finite)."""
    bc = ((mb.aabb[0][0] + mb.aabb[1][0]) / 2.0,
          (mb.aabb[0][1] + mb.aabb[1][1]) / 2.0,
          (mb.aabb[0][2] + mb.aabb[1][2]) / 2.0)
    best_ti = 0
    best_d = float("inf")
    for ti in range(len(ma.tris)):
        tlo, thi = ma.tri_aabb[ti]
        c = ((tlo[0] + thi[0]) / 2.0, (tlo[1] + thi[1]) / 2.0,
             (tlo[2] + thi[2]) / 2.0)
        d = dist(c, bc)
        if d < best_d:
            best_d = d
            best_ti = ti
    tlo, thi = ma.tri_aabb[best_ti]
    ac = ((tlo[0] + thi[0]) / 2.0, (tlo[1] + thi[1]) / 2.0,
          (tlo[2] + thi[2]) / 2.0)
    best_tj = 0
    best_dj = float("inf")
    for tj in range(len(mb.tris)):
        ulo, uhi = mb.tri_aabb[tj]
        c = ((ulo[0] + uhi[0]) / 2.0, (ulo[1] + uhi[1]) / 2.0,
             (ulo[2] + uhi[2]) / 2.0)
        d = dist(c, ac)
        if d < best_dj:
            best_dj = d
            best_tj = tj
    return dist_tri_tri(ma.tri_verts[best_ti], mb.tri_verts[best_tj])


def mesh_pair_exact_distance(fa, fb):
    """Exact minimum triangle-triangle distance for DISJOINT meshes
    (branch-and-bound over the AABB grid, seeded with a deterministic exact
    upper bound; the query radius at each triangle covers every triangle that
    could beat the incumbent, so the result is the exact mesh-to-mesh
    minimum)."""
    ma, mb = fa.pair_mesh, fb.pair_mesh
    gap = _aabb_gap(ma.aabb, mb.aabb)
    if gap > 0.0:
        best_seed = _seed_upper_bound(ma, mb)
    else:
        best_seed = float("inf")
    best = best_seed
    for ti in range(len(ma.tris)):
        tlo, thi = ma.tri_aabb[ti]
        if _aabb_gap((tlo, thi), mb.aabb) >= best:
            continue
        tv = ma.tri_verts[ti]
        rad = (best + ma.tri_diam[ti]) if best != float("inf") \
            else (mb.span * 2.0 + ma.tri_diam[ti])
        lo = (tlo[0] - rad, tlo[1] - rad, tlo[2] - rad)
        hi = (thi[0] + rad, thi[1] + rad, thi[2] + rad)
        for tj in mb.query_aabb(lo, hi):
            d = dist_tri_tri(tv, mb.tri_verts[tj])
            if d < best:
                best = d
    return best


def contained_vertices_depth(fa, fb):
    """Vertices of fa inside the closed mesh of fb, with exact depths. Only
    possible-inside vertices (inside fb's AABB) are parity-tested (complete:
    a vertex outside the AABB cannot be inside)."""
    out = []
    ma, mb = fa.pair_mesh, fb.pair_mesh
    (blo, bhi) = mb.aabb
    seen = set()
    for v in ma.verts:
        if not (blo[0] <= v[0] <= bhi[0] and blo[1] <= v[1] <= bhi[1]
                and blo[2] <= v[2] <= bhi[2]):
            continue
        if v in seen:
            continue
        seen.add(v)
        if point_in_mesh(v, mb):
            out.append((v, point_depth_in_mesh(v, mb)))
    return out


def adjudicate_pair(frames, bodies, anchor_name, name_a, name_b, tau,
                    r_joint=R_JOINT, edge_set=None):
    """Full Level-2 adjudication of one body pair at a configuration.
    class in {GENUINE_PENETRATION, TOUCHING, PROXY_FALSE_POSITIVE,
    UNRESOLVED_GEOMETRY, JOINT_REGION_EXEMPT}; signed margin d; depth; and
    the ledger features (crossing segments, contained points, joint-region
    split)."""
    fa, fb = frames[name_a], frames[name_b]
    adjacent = (bodies[name_a]["parent"] == name_b) or \
               (bodies[name_b]["parent"] == name_a)
    anchor_involved = fa.is_anchor or fb.is_anchor
    row = dict(a=name_a, b=name_b, adjacent=bool(adjacent))
    jc = None
    if adjacent:
        child = name_a if bodies[name_a]["parent"] == name_b else name_b
        jc = frames[child].pos  # certified child-body frame origin at q
        row["joint_center"] = list(jc)

    if anchor_involved and not adjacent:
        # The anchor's ONLY available Level-2 surface is the pinned hand.vtp
        # envelope (1920 points whole-hand, an order coarser than the bone
        # STLs). An exact surface crossing IS decisive at the represented
        # surfaces; otherwise the pair cannot decide the anatomical question
        # and is UNRESOLVED_GEOMETRY (the predicted P3 class; never forced).
        segs = mesh_pair_intersection_segments(fa, fb)
        if segs:
            row["class"] = "GENUINE_PENETRATION"
            row["d"] = 0.0
            row["depth"] = None
            row["note"] = ("envelope_surface_crossing; skin-scale envelope; "
                           "crossing segments recorded")
            row["n_crossing_segments"] = len(segs)
            row["crossing_segments"] = [[list(p), list(q)]
                                        for (p, q, _, _) in segs[:8]]
        else:
            d = mesh_pair_exact_distance(fa, fb)
            row["class"] = "UNRESOLVED_GEOMETRY"
            row["d"] = d
            row["depth"] = None
            row["note"] = ("envelope separation measured; the envelope cannot "
                           "adjudicate bone-vs-palm-skeleton")
        return row

    segs = mesh_pair_intersection_segments(fa, fb)
    depth_a = [] if fa.is_envelope else contained_vertices_depth(fa, fb)
    depth_b = [] if fb.is_envelope else contained_vertices_depth(fb, fa)
    feat_dists = []
    in_region_depth = 0.0
    active_depth = 0.0
    n_active_segments = 0
    n_active_points = 0
    for (p, q, ti, tj) in segs:
        fd = max(dist(p, jc), dist(q, jc)) if jc is not None else None
        if fd is not None:
            feat_dists.append(fd)
        if fd is None or fd > r_joint:
            n_active_segments += 1
    for (v, dep) in depth_a + depth_b:
        fd = dist(v, jc) if jc is not None else None
        if fd is not None:
            feat_dists.append(fd)
        if fd is None or fd > r_joint:
            n_active_points += 1
            active_depth = max(active_depth, dep)
        else:
            in_region_depth = max(in_region_depth, dep)
    row["features"] = dict(
        n_crossing_segments=len(segs),
        n_segments_active=n_active_segments,
        n_contained_points_active=n_active_points,
        max_feature_dist_to_joint_center=(max(feat_dists) if feat_dists
                                          else None),
        in_region_depth=in_region_depth,
        active_depth=active_depth,
        feature_dists=sorted(feat_dists)[:16],
    )
    row["depth_contained_max"] = max([d for (_, d) in depth_a + depth_b],
                                     default=0.0)

    if segs or depth_a or depth_b:
        if adjacent and jc is not None and n_active_segments == 0 \
                and n_active_points == 0:
            row["class"] = "JOINT_REGION_EXEMPT"
            row["d"] = -in_region_depth
            row["depth"] = in_region_depth
            row["note"] = ("all intersection features inside the declared "
                           "joint region; exempt (articulation), recorded")
            return row
        if active_depth > tau:
            row["class"] = "GENUINE_PENETRATION"
            row["d"] = -active_depth
            row["depth"] = active_depth
            return row
        row["class"] = "TOUCHING"
        row["d"] = 0.0
        row["depth"] = 0.0
        row["note"] = "surface crossing within the declared contact tolerance"
        return row

    d = mesh_pair_exact_distance(fa, fb)
    row["d"] = d
    row["depth"] = None
    if d > tau:
        row["class"] = "PROXY_FALSE_POSITIVE"
    else:
        row["class"] = "TOUCHING"
    return row


# ---------------------------------------------------------------------------
# LEVEL 2: body surface vs the EXACT analytic trunk cylinder
# ---------------------------------------------------------------------------

def _cyl_aabb(o, u, R, hh):
    ext = []
    for k in range(3):
        perp = math.sqrt(max(0.0, 1.0 - u[k] * u[k]))
        ext.append(R * perp + hh * abs(u[k]))
    lo = tuple(o[k] - ext[k] for k in range(3))
    hi = tuple(o[k] + ext[k] for k in range(3))
    return lo, hi


def adjudicate_body_vs_cylinder(frame, o, u, tau):
    """Exact Level-2 adjudication of one body's surface vs the analytic
    cylinder (axis point o, unit axis u; R = TRUNK_R, hh = TRUNK_H/2).
    class in {CLEAR, TOUCHING, GENUINE_PENETRATION} at the declared tau;
    d = the signed surface margin (exact for resolved classes); depth for
    GENUINE. Candidate triangles are processed deepest-vertex-first so the
    GENUINE class is proven by the first shrunken-solid intersection and the
    certified depth bisections run only on triangles that can still raise
    the maximum depth (the per-triangle depth lower bound is -fmin_v and the
    upper bound is -fmin_v + tri_diam by the unit-gradient property)."""
    R, hh = TRUNK_R, TRUNK_H / 2.0
    c_local = cyl_to_local(frame.sphere_center, o, u)
    f_center = cyl_sdf(c_local, R, hh)
    flagged = f_center <= frame.sphere_r
    out = dict(level1=dict(flag=bool(flagged),
                           dist_center_solid=max(f_center, 0.0),
                           sphere_r=frame.sphere_r))
    if not flagged:
        out["class"] = "CLEAR"
        out["d"] = None
        out["depth"] = None
        return out
    mesh = frame.mesh
    cell_r = mesh.cell * math.sqrt(3.0) / 2.0
    skip_bound = tau + mesh.max_diam
    glo, ghi = _cyl_aabb(o, u, R + skip_bound + cell_r,
                         hh + skip_bound + cell_r)
    mlo, mhi = mesh.aabb
    clo = tuple(int(math.floor(max(glo[k], mlo[k]) / mesh.cell))
                for k in range(3))
    chi = tuple(int(math.floor(min(ghi[k], mhi[k]) / mesh.cell))
                for k in range(3))
    chi = tuple(min(chi[k], clo[k] + 512) for k in range(3))
    candidates = []
    for cx in range(clo[0], chi[0] + 1):
        for cy in range(clo[1], chi[1] + 1):
            for cz in range(clo[2], chi[2] + 1):
                bucket = mesh.grid.get((cx, cy, cz))
                if not bucket:
                    continue
                center = ((cx + 0.5) * mesh.cell, (cy + 0.5) * mesh.cell,
                          (cz + 0.5) * mesh.cell)
                if cyl_sdf(cyl_to_local(center, o, u), R, hh) - cell_r                         > skip_bound:
                    continue
                for ti in bucket:
                    (va, vb, vc) = mesh.tri_verts[ti]
                    la = cyl_to_local(va, o, u)
                    lb = cyl_to_local(vb, o, u)
                    lc = cyl_to_local(vc, o, u)
                    fmin_v = min(cyl_sdf(la, R, hh), cyl_sdf(lb, R, hh),
                                 cyl_sdf(lc, R, hh))
                    if fmin_v > skip_bound:
                        continue
                    candidates.append((fmin_v, mesh.tri_diam[ti],
                                       la, lb, lc))
    candidates.sort(key=lambda t: t[0])
    body_class = "CLEAR"
    body_d = None
    body_depth = 0.0
    n_exact = 0
    n_depth = 0
    for (fmin_v, diam, la, lb, lc) in candidates:
        if body_class == "GENUINE_PENETRATION":
            # only the recorded maximum depth can still improve; the sorted
            # order bounds every remaining triangle's depth
            if -fmin_v + diam <= body_depth:
                break
        n_exact += 1
        if tri_solid_intersect_local(la, lb, lc, R - tau, hh - tau):
            depth = tri_depth_local(la, lb, lc, R, hh, tau)
            n_depth += 1
            if depth > body_depth:
                body_depth = depth
            body_class = "GENUINE_PENETRATION"
            continue
        if fmin_v < 0.0:
            # grazes within tolerance (inside the unshrunk solid, never
            # deeper than tau)
            if body_d is None or fmin_v < body_d:
                body_d = fmin_v
            if body_class == "CLEAR":
                body_class = "TOUCHING"
            continue
        dtri = tri_min_f_disjoint(la, lb, lc, R, hh)
        if body_d is None or dtri < body_d:
            body_d = dtri
        if dtri <= tau and body_class == "CLEAR":
            body_class = "TOUCHING"
    out["class"] = body_class
    out["d"] = body_d
    out["depth"] = body_depth if body_class == "GENUINE_PENETRATION" else None
    out["n_exact_triangles"] = n_exact
    out["n_depth_bisections"] = n_depth
    return out


def translate_frame(frame, delta_world):
    """A rigidly translated copy of a frame (control construction)."""
    nf = BodyFrame.__new__(BodyFrame)
    nf.name = frame.name
    nf.pos = add(frame.pos, delta_world)
    nf.rot = frame.rot
    nf.is_anchor = frame.is_anchor
    nf.is_envelope = frame.is_envelope
    wv = [add(v, delta_world) for v in frame.mesh.verts]
    nf.mesh = Mesh(frame.name, wv, frame.mesh.tris)
    nf.pair_mesh = nf.mesh
    nf.sphere_center = add(frame.sphere_center, delta_world)
    nf.sphere_r = frame.sphere_r
    return nf


def body_cyl_exact_distance(frame, o, u):
    """Exact min distance of the body's surface to the cylinder solid
    (control construction; the body must be disjoint)."""
    R, hh = TRUNK_R, TRUNK_H / 2.0
    best = float("inf")
    mesh = frame.mesh
    for ti in range(len(mesh.tris)):
        (va, vb, vc) = mesh.tri_verts[ti]
        la = cyl_to_local(va, o, u)
        lb = cyl_to_local(vb, o, u)
        lc = cyl_to_local(vc, o, u)
        fmin_v = min(cyl_sdf(la, R, hh), cyl_sdf(lb, R, hh),
                     cyl_sdf(lc, R, hh))
        if fmin_v - mesh.tri_diam[ti] >= best:
            continue
        if tri_solid_intersect_local(la, lb, lc, R, hh):
            return 0.0
        dtri = tri_min_f_disjoint(la, lb, lc, R, hh)
        if dtri < best:
            best = dtri
    return best


# ---------------------------------------------------------------------------
# the GP1-CC3 declared placement family (720 angles x 2 mirrors), the
# construction copied from the sealed GP1 code path
# ---------------------------------------------------------------------------

def placement_family(a, b, n_theta=N_THETA):
    v = sub(b, a)
    c = norm(v)
    if c == 0.0:
        refuse("degenerate_chord_refused", "placement family")
    if c > 2.0 * TRUNK_R:
        refuse("chord_exceeds_diameter_placement_family_undefined", repr(c))
    vh = scale(v, 1.0 / c)
    helper = (0.0, 0.0, 1.0) if abs(vh[2]) < 0.9 else (0.0, 1.0, 0.0)
    e1 = unit(cross(vh, helper))
    e2 = cross(vh, e1)
    m = scale(add(a, b), 0.5)
    h_len = math.sqrt(max(0.0, TRUNK_R * TRUNK_R - (c / 2.0) ** 2))
    placements = []
    for k in range(n_theta):
        theta = 2.0 * math.pi * k / n_theta
        u = add(scale(e1, math.cos(theta)), scale(e2, math.sin(theta)))
        w_base = unit(cross(vh, u))
        for mirror in (0, 1):
            w = w_base if mirror == 0 else scale(w_base, -1.0)
            o = add(m, scale(w, h_len))
            placements.append(dict(theta_index=k, theta=theta, mirror=mirror,
                                   u=u, o=o, w=w, h=h_len, chord=c))
    return placements


# ---------------------------------------------------------------------------
# input gate (prereg commit bytes, declaration, inherited pins, meshes,
# VTP envelope identity, constants)
# ---------------------------------------------------------------------------

def run_input_gate(prereg_path, control_table_path=None, control_table_sha=None):
    gate = dict(schema="chimera.instrument_v2.input_gate.v1", pins=[])
    h = sha256_file(prereg_path)
    if h != PREREG_SHA256:
        refuse("preregistration_sha_mismatch", h)
    gate["preregistration_sha256"] = h
    gate["prereg_commit"] = PREREG_COMMIT
    gate["prereg_branch"] = "origin/review/INSTRUMENT-V2-20261002"
    hd = sha256_file(DECLARATION_PATH)
    if hd != DECLARATION_SHA256:
        refuse("input_pin_mismatch", "declaration bytes " + hd)
    gate["declaration_sha256"] = hd
    if control_table_sha is not None:
        hc = sha256_file(control_table_path)
        if hc != control_table_sha:
            refuse("control_input_table_mismatch", hc)
        gate["control_input_table_sha256"] = hc
    # the x-aperture pair follows the declared dual-hash law (prereg section 1:
    # "a new declared action, never a silent normalization", GP1 review
    # section 5 law): the frozen prereg bytes are the append-only prefix
    # identity; prefix drift = refusal, pure appends are recorded as the
    # declared re-pin action with the current bytes sha256.
    DUAL_HASH_PATHS = {
        COORD_BASE + "x-aperture/GRASP_MECHANISMS.md":
            "ac5e258360e45f46e26117147ab944167aafea55b65df549fb4cecbcbf3c1c5d",
        COORD_BASE + "x-aperture/EVIDENCE.md":
            "68b5e429a0c5e0a81718c1fb77fc86856ed901ee7843f02f136303996ee5ad91",
    }
    gate["dual_hash"] = {}
    for path, expect in sorted(GP1_PINS_ABS.items()):
        if path in DUAL_HASH_PATHS:
            with open(path, "rb") as fh:
                cur = fh.read()
            cur_sha = hashlib.sha256(cur).hexdigest()
            prefix_len = None
            for ln in range(len(cur) + 1):
                if hashlib.sha256(cur[:ln]).hexdigest() == expect:
                    prefix_len = ln
                    break
            if prefix_len is None:
                refuse("input_pin_mismatch",
                       path + " prefix identity not found (non-append drift)")
            gate["dual_hash"][path] = dict(
                frozen_prereg_sha256=expect,
                current_sha256=cur_sha,
                prefix_identity_verified=True,
                prefix_len=prefix_len,
                appended_bytes=len(cur) - prefix_len,
                note="append-only errata bytes after the frozen prereg; the "
                     "declared re-pin action records the current sha256",
            )
            gate["pins"].append(dict(path=path, match=True, dual_hash=True))
            continue
        try:
            ok = sha256_file(path) == expect
        except OSError:
            refuse("input_pin_missing", path)
        gate["pins"].append(dict(path=path, match=ok))
        if not ok:
            refuse("input_pin_mismatch", path)
    with open(COORD_BASE + "x-aperture/GRASP_MECHANISMS.md", "rb") as fh:
        gm_cur = fh.read()
    prefix_len = None
    for ln in range(len(gm_cur) + 1):
        if hashlib.sha256(gm_cur[:ln]).hexdigest() == GRASP_MECH_PRE_AMENDMENT_SHA:
            prefix_len = ln
            break
    if prefix_len is None:
        refuse("input_pin_mismatch", "GRASP_MECHANISMS prefix identity not found")
    gate["grasp_mechanisms_prefix_len"] = prefix_len
    with open(A05_PATH) as fh:
        mut = json.load(fh)
    stl_pins = {}
    for b in mut["bodies"]:
        for g in b.get("geometry", []):
            if "stl_sha256" in g:
                stl_pins[b["name"]] = g["stl_sha256"]
    if len(stl_pins) != 19:
        refuse("input_pin_missing", "expected 19 stl pins")
    on_disk = {}
    for fname in STL_NAMES:
        on_disk[fname] = sha256_file(VENDOR_MESHES + fname + ".stl")
    stl_files = {}
    for name in sorted(stl_pins):
        hits = [f for f, hh2 in on_disk.items() if hh2 == stl_pins[name]]
        if len(hits) != 1:
            refuse("input_pin_mismatch",
                   "stl pin for %s matched %d files" % (name, len(hits)))
        stl_files[name] = VENDOR_MESHES + hits[0] + ".stl"
    gate["mesh_pins"] = dict(count=len(stl_files), all_match=True)
    with open(COORD_BASE + "evidence-store/MAT2-G01/report/REPORT.md",
              encoding="utf-8") as fh:
        g01 = fh.read()
    m = re.search(r"\| declared trunk radius \(from sealed analytic volume\)"
                  r" \| ([0-9.]+) m \|", g01)
    if m is None or float(m.group(1)) != TRUNK_R:
        refuse("threshold_pin_mismatch", "declared_trunk_radius_m")
    m = re.search(r"\| trunk height \| ([0-9.]+) m \|", g01)
    if m is None or float(m.group(1)) != TRUNK_H:
        refuse("threshold_pin_mismatch", "trunk_height_m")
    # VTP envelope identity: the VTP is in millimetre source units; the
    # certified conversion is 1e-3 and the envelope identity is
    # hand_vtp_bounds_m == (raw VTP AABB) / 1000, exact (refusal
    # input_pin_mismatch otherwise)
    bounds = mut["envelope_check"]["hand_vtp_bounds_m"]
    pts, tris, hist = parse_vtp(VTP_PATH)
    lo = [min(v[k] for v in pts) for k in range(3)]
    hi = [max(v[k] for v in pts) for k in range(3)]
    worst = 0.0
    for k in range(3):
        worst = max(worst, abs(lo[k] - float(bounds[0][k])),
                    abs(hi[k] - float(bounds[1][k])))
    if worst > 1e-9:
        refuse("input_pin_mismatch",
               "scaled VTP AABB vs hand_vtp_bounds_m worst %r" % worst)
    gate["vtp_envelope"] = dict(points=len(pts), polys=len(tris),
                                poly_size_histogram=hist,
                                scaled_aabb_worst_delta=worst)
    gate["ok"] = True
    return gate, mut, stl_files, bounds


# ---------------------------------------------------------------------------
# witness configuration identity (sealed GP1 values; refuse on drift)
# ---------------------------------------------------------------------------

def check_witness_identity(bodies, joints_by_name, anchor_name):
    tips_bodies = dict(thumb="distal_thumb", digit3="distph3")
    for jn, expected in sorted(Q_C_PRIMARY.items()):
        if jn not in joints_by_name:
            refuse("threshold_pin_mismatch", "witness joint missing " + jn)
        if Q_C_PRIMARY[jn] != expected:
            refuse("threshold_pin_mismatch", "witness joint value " + jn)
    a = fk_origin(bodies, anchor_name, Q_C_PRIMARY, tips_bodies["thumb"])
    b = fk_origin(bodies, anchor_name, Q_C_PRIMARY, tips_bodies["digit3"])
    for k in range(3):
        if abs(a[k] - Q_C_PRIMARY_TIPS["thumb"][k]) > 1e-12:
            refuse("threshold_pin_mismatch",
                   "thumb tip FK vs sealed receipt: %r vs %r"
                   % (a[k], Q_C_PRIMARY_TIPS["thumb"][k]))
        if abs(b[k] - Q_C_PRIMARY_TIPS["digit3"][k]) > 1e-12:
            refuse("threshold_pin_mismatch",
                   "digit3 tip FK vs sealed receipt: %r vs %r"
                   % (b[k], Q_C_PRIMARY_TIPS["digit3"][k]))
    chord = dist(a, b)
    if abs(chord - Q_C_PRIMARY_CHORD) > 1e-12:
        refuse("threshold_pin_mismatch",
               "witness chord %r vs sealed %r" % (chord, Q_C_PRIMARY_CHORD))
    return dict(a=list(a), b=list(b), chord=chord)


def build_level1_expectation_check(frames, bodies, anchor_name):
    """The frozen Level-1 witness cross-check: at q_c(PRIMARY) the sphere
    screen MUST reproduce the sealed GP1 CC2 table (same declared
    construction); drift beyond LEVEL1_MATCH_TOL = refusal."""
    rows = level1_pair_rows(frames, bodies, anchor_name)
    measured = {}
    for r in rows:
        if r["adjacent"]:
            continue
        key = tuple(sorted((r["a"], r["b"])))
        measured[key] = r
    problems = []
    n_overlap = 0
    for (na, nb, clearance) in GP1_CC2_WITNESS_OVERLAPS:
        key = tuple(sorted((na, nb)))
        r = measured.get(key)
        if r is None:
            problems.append("missing pair %s" % (key,))
            continue
        if abs(r["clearance"] - clearance) > LEVEL1_MATCH_TOL:
            problems.append("%s clearance %r vs sealed %r"
                            % (key, r["clearance"], clearance))
        if not r["proxy_overlap"]:
            problems.append("%s not flagged" % (key,))
    for key, r in measured.items():
        if r["proxy_overlap"]:
            n_overlap += 1
            if key not in [tuple(sorted((a, b)))
                           for (a, b, _) in GP1_CC2_WITNESS_OVERLAPS]:
                problems.append("unexpected flagged pair %s" % (key,))
    if n_overlap != GP1_WITNESS_NONADJACENT_OVERLAPS:
        problems.append("overlap count %d vs sealed %d"
                        % (n_overlap, GP1_WITNESS_NONADJACENT_OVERLAPS))
    if len(measured) != GP1_WITNESS_NONADJACENT_TESTED:
        problems.append("non-adjacent tested %d vs sealed %d"
                        % (len(measured), GP1_WITNESS_NONADJACENT_TESTED))
    if problems:
        refuse("level1_witness_mismatch", "; ".join(problems[:6]))
    return dict(nonadjacent_tested=len(measured),
                nonadjacent_overlaps=n_overlap, all_match=True)
