"""MAT2-M11: reuse the same material rules in a loaded monkey limb.

One SHAPE-PARAMETRIC material law implementation (the sealed M03/M04/M05 law
stack, imported UNMODIFIED -- composition only, no upstream edits), exercised
on three declared shapes supplied purely as geometry data:

  icosphere  M03 icosphere L2 (R = 0.05 m)   (the M03/M10 lineage shape)
  cube       M03 cube_grid                    (topologically distinct)
  limb       capped tube bladder erected between real endpoints of the
             pinned macaque arm (B04 fitted frame chain + A06 palm anchor),
             carrying the REAL B03 bone masses on the hanging chain

There is NO shape-specific motion code: shapes differ only in builder data
(SHAPES registry below); the dynamics path (schedule, substep order,
projection, chain solve, contact, ledger) is one code path (LimbWorld.run).
Gate X1a audits this by AST.

Amendment A1 architecture (the HANGING BONE-CHAIN RIG; the earlier stance-
push-column draft is the committed probe record -- its single-pole 49 N tie
punctured the shell at 4000 Pa and the 31.4 N thrust lifted the column;
probes recorded in Amendment A1):
  - the vessel hangs from the declared overhead CLAMP (the top ring fully
    pinned x,y,z; a declared VISIBLE support that never leaves the scene
    inventory),,
  - the BONE CHAIN hangs from the vessel's free (bottom) pole through
    M05-form TENSION ties: tissue -> humerus -> ulna -> radius -> foot(hand),
    declared rest gaps; real B03 masses ride their chain elements; every
    chain element carries a declared penalty ground contact (M05 pinned
    K_CONTACT law) so a released distal chain lands on its own contacts,
  - the belt (extension) chord layout drives the free pole DOWNWARD when
    pressurized (M10 measured +4.3e-3 m at 2000 Pa): the pole push descends
    the chain, the foot presses the ground, and every stage force is a
    measured tie tension T1..T4 beside the measured contact force,
  - the declared surrogate loads (prereg section 3 masses, re-issued by
    Amendment A1) remain as hanging surrogates on the clamped pole: their
    weight path is clamp-borne; the CHAIN WEIGHTS are the demonstrated load
    path (A1). The rig is erected so that at p = 0 the foot hangs at a small
    declared rest gap above the ground (contact bitwise 0) with the chain
    taut.

CPU-only; stdlib + numpy; float64; fixed 300 Hz tick; deterministic (no
stochastic inputs, no wall-clock in physics).
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
for _p in (str(HERE), str(CONTRIB / 'MAT2-M01'), str(CONTRIB / 'MAT2-M02'),
           str(CONTRIB / 'MAT2-M03'), str(CONTRIB / 'MAT2-M04'),
           str(CONTRIB / 'MAT2-M05'), str(CONTRIB / 'MAT2-B03'),
           str(CONTRIB / 'MAT2-B04'), str(CONTRIB / 'MAT2-A06'),
           str(CONTRIB / 'MAT2-B05')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import material_state as ms01  # noqa: E402  (M01 validator, UNMODIFIED)
import passive_response as pr04  # noqa: E402  (M04 anisotropy law, UNMODIFIED)
import pressure_membrane as pm  # noqa: E402  (M03 membrane laws, UNMODIFIED)
import interface_exchange as ix05  # noqa: E402  (M05 law constants, UNMODIFIED)


def require(condition, code):
    if not condition:
        raise ValueError(code)


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


# ---------------------------------------------------------------- pins ----
INPUT_PINS = {
    'MAT2-M01/material_state.py':
        'b6b009713daa4b315c6b5cb43c7ad4e756123b50edcdd802eeebd55c6afd6c40',
    'MAT2-M03/pressure_membrane.py':
        '3dd64f6465430380f1c0a53a95523c700cd51a6b1115e60f0df8afde2239c96e',
    'MAT2-M04/passive_response.py':
        '68a696e1728066a3dce93db7b6c98f8bb4826322a84bbad20eeadf38350e326b',
    'MAT2-M05/interface_exchange.py':
        '295e6c898ada14918f09b2b0633f5926c1623c9e09cd37258e516ab57450b9b9',
    'MAT2-B03/material_volume_input.json':
        '6e8033f26c823f410eb5beb8fdaaefd4c0c37db61327a86221e087bc832b9ddc',
    'MAT2-M02/monkey_arm_independent_meshes.json':
        '51d8231e0d1eacd7f0d4b558699f011e35ff765f5d0e07ef5889ded27216a834',
    'MAT2-B04/frame_forest.json':
        '156ef55722e1ecda3238f3733131eb707f209cb93531d0e133227b00ebba8203',
    'MAT2-A06/attachment_ownership.json':
        'f1f0430772258e8449fc354841becf2f1869783399e63f3f145565b8d0b1041c',
    'MAT2-B05/mechanical_port_requirements.json':
        'ef69ee740262cc5783e763517e4d27e0306f31d059b8273bb125486ad7647f3d',
}


def verify_input_pins():
    out = {}
    for rel, expected in INPUT_PINS.items():
        path = CONTRIB / rel
        require(path.exists(), 'input_pin_missing:' + rel)
        actual = sha256_file(path)
        require(actual == expected, 'input_pin_drift:' + rel)
        out[rel] = actual
    return out


# --------------------------------------------------- declared constants ----
# Pinned law constants carried from the sealed cards (M10 heritage, itself
# carried from M03/M04/M05); PREREGISTRATION sections 3 + Amendments A1/A2
# are the freeze.
SPHERE_R = 0.05
SPHERE_LEVEL = 2
CUBE_SIDE = 0.10
CUBE_N = 6
TUBE_RINGS = 12          # limb tube ring count (prereg section 3)
TUBE_RADIALS = 12        # limb tube radial count
TUBE_RADIUS = 0.012      # m (authored engineering detail, prereg section 3)
E_FIBER, E_TRANS = 1.0e8, 1.0e6                  # Pa
T_WALL = 3.0e-3                                  # m
A_CHORD = T_WALL * T_WALL                        # declared chord section (m^2)
BELT_DZ = (0.0, 0.42)      # belt chord |dz| band along the declared axis
CHORD_CAP_Z = 0.75         # chord endpoints within the axial band
XPBD_ITERS = 8
XPBD_RELAX = 0.15
N_SUB = 16
DT = 1.0 / 300.0
HS = DT / N_SUB
C_V = 2000.0
C_LOAD = 4.0
# Point-mass mode damping (declared constants, Amendment A1 derivation):
#   foot-contact mode k=K_CONTACT, m=M_FOOT: c_crit = 2*sqrt(k*m) = 63.2 1/s
#   -> C_FOOT declared 3.16x critical (overdamped, settles within P0);
#   bone-tie mode k=K_TIE_BONE, m=humerus 0.0225 kg: c_crit = 23.2 1/s
#   -> C_BONE declared 1.3x critical.
C_FOOT = 200.0
C_BONE = 30.0
SYNTH_TISSUE_MASS_KG = 0.020     # synthetic shapes: equal per vertex (M10)
LIMB_TISSUE_MASS_KG = 2.0e-3     # limb: declared tissue mass (NOT a bone mass)
M_LOAD_SYNTH_KG = 2.0            # synthetic hanging surrogate load (A1)
M_LOAD_LIMB_KG = 0.25            # limb hanging surrogate load (A1)
M_FOOT_SYNTH_KG = 0.010          # synthetic-shape foot point mass (declared)
M_FOOT_LIMB_KG = 0.010           # limb foot INERTIAL mass (declared; A1: the
                                 # B03 counted hand mass stays 0.0 bitwise)
GRAV = 9.80665
K_TIE = 600.0                    # N/m load surrogate tie (M05-form, M10)
K_TIE_BONE = 600.0               # N/m chain ties (same M05 form)
L_TIE_SYNTH = 0.05               # m surrogate tie rest (A2: derived ground
                                 # clearance -- the 2.0 kg surrogate on a
                                 # 600 N/m tie stretches 3.28e-2 m; the
                                 # erected icosphere clamped pole sits at
                                 # ~0.115 m so rest 0.10 would hang the mass
                                 # below the ground plane)
L_TIE_LIMB = 0.05                # m surrogate tie rest (prereg section 3)
REST_GAP_CHAIN = 0.01            # m chain tie rest gaps (A1 suggested 0.01)
R_FOOT = 5.0e-3                  # m foot contact radius (declared)
R_BONE = 5.0e-3                  # m per-bone contact radius (declared
                                 # engineering detail, A1 per-bone contacts)
K_CONTACT = ix05.K_CONTACT_PA_PER_M   # 1.0e5, M05 pinned law (never invented)
G_FOOT_TARGET_M = 2.0e-4         # declared p=0 settled foot rest gap target
                                 # (A2: the rig is erected at the declared
                                 # chain statics so the settled gap lands
                                 # within ~5e-5 m of this target; positive
                                 # gap => contact bitwise 0)
RECOVERY_GAP_M = 1.0e-3          # X4 power-off recovery window (A2: 2.5x the
                                 # declared gap target; covers the erection
                                 # estimation residual and the integrator
                                 # positional floor; declared before any run)
SOURCE_ID = 'm11_source'
P_EXT_PA = 0.0
MAX_DELTA_P_PA = 5000.0
MAX_FLOW_M3_PER_S = 1.0e-3
SOURCE_PROVENANCE = ('MAT2-M11 preregistered pneumatic source '
                     '(engineering actuator demonstration; M03 limits)')
DP_WORK_PA = 1000.0
# Amendment A1 schedule level (was 4000 in the probe): the belt descent at
# hold must exceed the declared foot rest gap (G_FOOT_TARGET_M) so the foot
# presses the ground (X4 discriminator); 1000 Pa is A1's frozen level.
# schedule (prereg section 4)
PRESETTLE_END = 200
RAMP_UP_END = 400
HOLD_END = 1100
POWER_OFF_END = 1300
TOTAL_TICKS = 1500
SETTLE_WINDOW = 200
RELEASE_TICK = 450               # connection-removal control (declared)
RELEASE_TIE_ID = 'T2'            # A1: the X5 control releases T2 only
SNAP_TICKS = (0, 300, 450, 700, 1000, 1100, 1200, 1350, 1499)
BASELINE_WINDOW = (100, 200)
LOADED_WINDOW = (1000, 1100)
OFF_WINDOW = (1400, 1500)
POST_RELEASE_WINDOW = (550, 650)     # X5 settled-after-release window
CONTACT_PICKUP_WINDOW = (650, 750)   # X5 distal-contact pickup window
# frozen windows (prereg section 5; derived from declared constants)
X_FLOOR_M = 1.0e-7               # integrator positional identity floor
REL = 0.05
BITE_M = 1.0e-3                  # connection-removal departure bite
TRACTION_RATIO_REL = 1.0e-9
AUDIT_WINDOW_M = 1.0e-9
AUDIT_BITE_M = 1.0e-3
X8_FLOOR_J = 2.0e-3            # A2 re-derivation: the settled-window
                                # cumulative no-source floor (max
                                # measured 1.396e-3 (cube); ~1.43x)
PHASE_NAMES = ('P0_presettle', 'A_rampup', 'B_hold', 'C_poweroff',
               'D_settled_off')
# A06 tie-site citations (A2): each chain tie cites ONE attachment-role A06
# record verbatim (A06 observation "do not reinterpret waypoints as
# attachment ports" honoured: only origin/insertion attachment roles).
TIE_SITE_IDS = {
    'T1': 'path.ext_carpi_rad_longus.0',   # humerus origin_attachment
    'T2': 'path.flex_carpi_ulnaris.0',     # ulna origin_attachment (elbow)
    'T3': 'path.flex_poll_longus.0',       # radius origin_attachment
    'T4': 'path.flex_carpi_radialis.2',    # hand insertion_attachment (palm)
}
BONE_MATTER_IDS = {'humerus': 'bone_humerus', 'ulna': 'bone_ulna',
                   'radius': 'bone_radius'}
# Per-shape erection offsets (A2): the hanging rig is lifted by the
# declared static chain hang PLUS this offset, which compensates the
# vessel's own axial compliance sag (not analytically computable for the
# XPBD network). Values are PROBE-DERIVED before the bank (probe: settle
# each rig at offset 0 over 600 ticks with the ground contacts DISABLED --
# the probe_free_hang probe-only tamper -- and measure the settled free-hang
# sag; offset := sag so the settled p=0 gap lands on the declared target;
# the sag is lift-invariant so the correction is exact, and with the
# corrected offset the p=0 trajectory never touches the ground, so the
# contact-free probe state IS the bank p=0 state bitwise). Recorded with
# the triggering probe values in Amendment A2.
ERECTION_OFFSET_M = {'icosphere': 0.0022280, 'cube': 0.0021341,
                     'limb': 0.0030312}


def phase_of(tick):
    t = int(tick)
    if t < PRESETTLE_END:
        return 'P0_presettle'
    if t < RAMP_UP_END:
        return 'A_rampup'
    if t < HOLD_END:
        return 'B_hold'
    if t < POWER_OFF_END:
        return 'C_poweroff'
    return 'D_settled_off'


def work_schedule(tick):
    """Preregistered schedule (PASCALS, A1 level): 0 (0-199), ramp
    0->DP_WORK_PA (200-399), hold (400-1099), ramp to 0 POWER OFF
    (1100-1299), 0 (1300-1499)."""
    t = int(tick)
    if t < PRESETTLE_END:
        return 0.0
    if t < RAMP_UP_END:
        frac = (t - PRESETTLE_END) / (RAMP_UP_END - PRESETTLE_END)
    elif t < HOLD_END:
        frac = 1.0
    elif t < POWER_OFF_END:
        frac = 1.0 - (t - HOLD_END) / (POWER_OFF_END - HOLD_END)
    else:
        frac = 0.0
    return DP_WORK_PA * frac


def off_schedule(tick):
    """Activation-off control: p = 0 throughout."""
    return 0.0


# ------------------------------------------------------------ real data ----
def _rigid_from_body_to_world(v_body, v_world):
    """Recover the blob's own admitted world_from_local rigid transform.

    Lawful frame plumbing (Amendment A1): the pinned mesh blob declares
    world_vertices_m as the admitted default-pose world frame of the SAME
    body vertices; the recovered transform must reproduce the pinned world
    vertices to <=1e-12 or the binding refuses (transform_mismatch) -- it is
    never a guessed alignment of foreign frames (B04 no_fusion honoured)."""
    cb = v_body.mean(axis=0)
    cw = v_world.mean(axis=0)
    h = (v_world - cw).T @ (v_body - cb)
    u, _s, vt = np.linalg.svd(h)
    d = np.linalg.det(u @ vt)
    r = u @ np.diag([1.0, 1.0, d]) @ vt
    t = cw - r @ cb
    err = float(np.max(np.abs((r @ v_body.T).T + t - v_world)))
    require(err <= 1e-12, 'transform_mismatch:%.3e' % err)
    return r, t, err


def load_real_data():
    """Read the sha-pinned real documents (masses, meshes, frames, sites).

    Returns a dict; every consumed record is carried verbatim with its
    source document id. No constant here is re-typed from memory."""
    b03 = json.loads((CONTRIB / 'MAT2-B03' / 'material_volume_input.json')
                     .read_bytes())
    blob = json.loads((CONTRIB / 'MAT2-M02' /
                       'monkey_arm_independent_meshes.json').read_bytes())
    b04 = json.loads((CONTRIB / 'MAT2-B04' / 'frame_forest.json').read_bytes())
    a06 = json.loads((CONTRIB / 'MAT2-A06' / 'attachment_ownership.json')
                     .read_bytes())
    b05 = json.loads((CONTRIB / 'MAT2-B05' /
                      'mechanical_port_requirements.json').read_bytes())
    matter = {m['id']: m for m in b03['matter']}
    bones = {}
    for bone in ('humerus', 'ulna', 'radius'):
        mid = BONE_MATTER_IDS[bone]
        require(mid in matter, 'real_mass_missing:' + mid)
        region = [r for r in b03['regions'] if r['id'] == bone][0]
        key = region['rest_geometry']['mesh_blob_region_key']
        src = blob['regions'][key]
        r_mat, t_vec, err = _rigid_from_body_to_world(
            np.array(src['vertices_m'], dtype=np.float64),
            np.array(src['world_vertices_m'], dtype=np.float64))
        bones[bone] = {
            'mass_kg': matter[mid]['mass_kg'],
            'matter_id': mid,
            'counted_source': 'MAT2-B03 matter entry ' + mid,
            'region_frame': region['rest_geometry']['frame'],
            'frame_id': 'fitted_' + bone,
            'mesh_region_key': key,
            'vertices_m': np.array(src['vertices_m'], dtype=np.float64),
            'world_vertices_m': np.array(src['world_vertices_m'],
                                         dtype=np.float64),
            'transform_residual_m': err,
        }
    hand_region = [r for r in b03['regions'] if r['id'] == 'hand'][0]
    key = hand_region['rest_geometry']['mesh_blob_region_key']
    src = blob['regions'][key]
    r_mat, t_vec, err = _rigid_from_body_to_world(
        np.array(src['vertices_m'], dtype=np.float64),
        np.array(src['world_vertices_m'], dtype=np.float64))
    bones['hand'] = {
        'mass_kg': 0.0,   # B03 shell law: open surface, zero counted mass
        'matter_id': None,
        'counted_source': 'MAT2-B03 matter entry shell_hand (zero, bitwise)',
        'region_frame': hand_region['rest_geometry']['frame'],
        'frame_id': 'unresolved_body:hand (B04 admission ledger)',
        'mesh_region_key': key,
        'vertices_m': np.array(src['vertices_m'], dtype=np.float64),
        'world_vertices_m': np.array(src['world_vertices_m'],
                                     dtype=np.float64),
        'transform_residual_m': err,
        'transform_t_m': [float(c) for c in t_vec],
        'status': 'explicitly_unresolved_terminal',
    }
    frames = {k: v['frame_id'] for k, v in b04['fitted_frames'].items()}
    sites = a06['path_records']
    site_by_id = {s['record_id']: s for s in sites}
    palm = [e for e in a06['grasp_endpoints']
            if e['endpoint_id'] == 'grasp.palm_anchor']
    require(len(palm) == 1, 'palm_anchor_missing')
    # the A06 palm anchor position (hand-anchor body frame origin) mapped
    # through the blob hand region's own admitted transform (<=1e-12 above)
    palm_world = np.array(bones['hand']['transform_t_m'], dtype=np.float64)
    ports = b05['ports']
    ledger = b05['input_status_ledger']
    return {'b03': b03, 'b04': b04, 'a06': a06, 'b05': b05, 'bones': bones,
            'frames': frames, 'sites': sites, 'site_by_id': site_by_id,
            'palm': palm, 'palm_world_m': palm_world,
            'ports': ports, 'ledger': ledger,
            'blob_frame_note': blob['frame_note']}


def assembly_mass_audit(chain_elements, real):
    """X2a / FB6: the assembly masses are compared BITWISE against a FRESH
    read of the pinned B03 document (never against the caller's dict). A
    synthetic stand-in mass is refused (real_input_ledger vocabulary)."""
    b03 = json.loads((CONTRIB / 'MAT2-B03' / 'material_volume_input.json')
                     .read_bytes())
    matter = {m['id']: m for m in b03['matter']}
    checked = {}
    for el in chain_elements:
        mid = el.get('matter_id')
        if mid is None:
            # the foot's inertial mass is declared engineering mass; its
            # B03 COUNTED mass must be bitwise zero
            require(float(el.get('b03_counted_mass_kg', 0.0)) == 0.0,
                    'b03_counted_mass_not_zero:' + el['name'])
            checked[el['name']] = 'declared_inertial_mass(b03_counted=0.0)'
            continue
        require(mid in matter, 'real_mass_missing:' + mid)
        pinned = matter[mid]['mass_kg']
        require(float(el['mass_kg']) == float(pinned),
                'synthetic_port_standin_refused:' + el['name'])
        checked[el['name']] = mid
    hand_counted = real['bones']['hand']['mass_kg']
    require(float(hand_counted) == 0.0,
            'synthetic_port_standin_refused:hand')
    return {'bitwise_matches_pinned_b03': True,
            'checked': checked,
            'hand_counted_mass_kg': float(hand_counted)}


# -------------------------------------------------------------- shapes ----
def _unique_edges(triangles):
    edge_index = {}
    order = []

    def key_of(a, b):
        return (a, b) if a < b else (b, a)

    for tri in np.asarray(triangles, dtype=np.int64).tolist():
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            key = key_of(a, b)
            if key not in edge_index:
                edge_index[key] = len(order)
                order.append(key)
    return np.array(order, dtype=np.int64), edge_index


def _capped_tube(p0, p1, radius, rings, radials):
    """A closed capped-tube bladder between two declared endpoints.

    Capsule profile (A2 builder correction; the probed draft profile
    clustered the rings in a mid-span band of width 2*radius, producing a
    two-cone spindle with ~140 N/m axial stiffness and a millimetre-scale
    pole sag): rings sweep the FULL axis; the radius follows a capsule --
    cylindrical body with spherical end caps. Pure geometry data for the
    `limb` shape; the DYNAMICS never branches on which builder produced
    the mesh. Outward-consistent winding: ring quads + two apex caps (ring
    order verified by Membrane.require_closed at build; a winding defect
    refuses at construction)."""
    p0 = np.asarray(p0, dtype=np.float64)
    p1 = np.asarray(p1, dtype=np.float64)
    axis = p1 - p0
    span = float(np.linalg.norm(axis))
    require(span > 2.0 * radius, 'tube_span_too_short')
    a_hat = axis / span
    ref = np.array([1.0, 0.0, 0.0])
    if abs(float(np.dot(ref, a_hat))) > 0.9:
        ref = np.array([0.0, 0.0, 1.0])
    u_hat = np.cross(a_hat, ref)
    u_hat /= np.linalg.norm(u_hat)
    w_hat = np.cross(a_hat, u_hat)
    verts = [tuple(p0)]                          # south cap apex (index 0)
    ring_start = []
    for ri in range(rings):
        s = (ri + 0.5) / rings * span            # axial position 0..span
        if s < radius:                           # south spherical cap
            rr = math.sqrt(max(1e-16, radius * radius -
                               (radius - s) * (radius - s)))
        elif s > span - radius:                  # north spherical cap
            rr = math.sqrt(max(1e-16, radius * radius -
                               (s - (span - radius)) *
                               (s - (span - radius))))
        else:                                    # cylindrical body
            rr = radius
        ring_start.append(len(verts))
        base = p0 + a_hat * s
        for ki in range(radials):
            ang = 2.0 * math.pi * ki / radials
            offset = rr * (math.cos(ang) * u_hat + math.sin(ang) * w_hat)
            verts.append(tuple(base + offset))
    north = len(verts)
    verts.append(tuple(p1))                      # north cap apex (last)
    v = np.array(verts, dtype=np.float64)
    tris = []
    for ri in range(rings - 1):
        a0, b0 = ring_start[ri], ring_start[ri + 1]
        for ki in range(radials):
            k2 = (ki + 1) % radials
            tris.append((a0 + ki, a0 + k2, b0 + k2))
            tris.append((a0 + ki, b0 + k2, b0 + ki))
    for ki in range(radials):                    # south cap (apex 0)
        k2 = (ki + 1) % radials
        # the strips carry ring edges forward on their lower ring
        # (a_ki->a_k2 in tri1); the cap must supply the BACKWARD direction
        tris.append((0, ring_start[0] + k2, ring_start[0] + ki))
    base = ring_start[-1]                        # north cap
    for ki in range(radials):
        k2 = (ki + 1) % radials
        # the strips carry ring edges backward on their upper ring
        # (b_k2->b_ki in tri2); the cap must supply the FORWARD direction
        tris.append((north, base + ki, base + k2))
    return v, np.array(tris, dtype=np.int64)


def _synth_chain():
    """Chain builder DATA for the synthetic shapes: a single foot element
    (the declared point mass) on tie T1. Same element schema as the limb."""
    return [{'name': 'foot', 'mass_kg': M_FOOT_SYNTH_KG,
             'matter_id': None, 'b03_counted_mass_kg': 0.0,
             'contact_radius_m': R_FOOT, 'tie_id': 'T1',
             'tie_site_record': None,
             'status': 'declared_point_mass'}]


def _limb_chain(real):
    """Chain builder DATA for the limb: humerus -> ulna -> radius -> foot,
    real B03 masses, one A06 attachment-role record cited per tie."""
    # the rig's terminal is the declared FOOT; its pinned body is the HAND
    # region (prereg section 1: "FOOT (distal terminal): the hand region")
    owner_of = {'humerus': 'humerus', 'ulna': 'ulna', 'radius': 'radius',
                'foot': 'hand'}
    def element(name, mass, matter_id, tie_id, status):
        rec = real['site_by_id'][TIE_SITE_IDS[tie_id]]
        require(rec['owner_body'] == owner_of[name],
                'tie_site_owner_mismatch:' + tie_id)
        require('attachment' in str(rec.get('role')),
                'tie_site_role_not_attachment:' + tie_id)
        return {'name': name, 'mass_kg': float(mass),
                'matter_id': matter_id, 'b03_counted_mass_kg': 0.0,
                'contact_radius_m': R_BONE if name != 'foot' else R_FOOT,
                'tie_id': tie_id,
                'tie_site_record': {'record_id': rec['record_id'],
                                    'declared_name': rec['declared_name'],
                                    'owner_body': rec['owner_body'],
                                    'role': rec['role'],
                                    'location_m':
                                    [float(c) for c in rec['location_m']]},
                'status': status}
    bones = real['bones']
    chain = [
        element('humerus', bones['humerus']['mass_kg'], 'bone_humerus',
                'T1', 'declared_point_mass(real_b03_mass)'),
        element('ulna', bones['ulna']['mass_kg'], 'bone_ulna',
                'T2', 'declared_point_mass(real_b03_mass)'),
        element('radius', bones['radius']['mass_kg'], 'bone_radius',
                'T3', 'declared_point_mass(real_b03_mass)'),
        element('foot', M_FOOT_LIMB_KG, None, 'T4',
                'explicitly_unresolved_terminal'),
    ]
    chain[3]['b03_counted_mass_kg'] = 0.0   # B03 shell law: zero, bitwise
    return chain


def build_shape(shape, real=None):
    """The SHAPES registry: builders return GEOMETRY DATA only.

    The dynamics (LimbWorld) never reads the shape value -- audit X1a."""
    if shape == 'icosphere':
        shell = pm.icosphere(SPHERE_LEVEL, SPHERE_R, 'm11_icosphere')
        return {'vertices': shell.vertices.copy(),
                'triangles': np.asarray(shell.triangles,
                                        dtype=np.int64).copy(),
                'tissue_mass': SYNTH_TISSUE_MASS_KG,
                'load_mass': M_LOAD_SYNTH_KG,
                'load_tie_rest': L_TIE_SYNTH,
                'chain': _synth_chain(),
                'erection_offset_m': ERECTION_OFFSET_M['icosphere'],
                'real_frame_audit': None}
    if shape == 'cube':
        shell = pm.cube_grid(CUBE_N, CUBE_SIDE, 'm11_cube')
        return {'vertices': shell.vertices.copy(),
                'triangles': np.asarray(shell.triangles,
                                        dtype=np.int64).copy(),
                'tissue_mass': SYNTH_TISSUE_MASS_KG,
                'load_mass': M_LOAD_SYNTH_KG,
                'load_tie_rest': L_TIE_SYNTH,
                'chain': _synth_chain(),
                'erection_offset_m': ERECTION_OFFSET_M['cube'],
                'real_frame_audit': None}
    if shape == 'limb':
        require(real is not None, 'limb_requires_real_data')
        bones = real['bones']
        hum = bones['humerus']['world_vertices_m']
        axis_hint = hum.mean(axis=0) - real['palm_world_m']
        a_hat = axis_hint / float(np.linalg.norm(axis_hint))
        top = hum[int(np.argmax(hum @ a_hat))]
        bottom = np.array(real['palm_world_m'], dtype=np.float64)
        v, t = _capped_tube(bottom, top, TUBE_RADIUS, TUBE_RINGS,
                            TUBE_RADIALS)
        return {'vertices': v, 'triangles': t,
                'tissue_mass': LIMB_TISSUE_MASS_KG,
                'load_mass': M_LOAD_LIMB_KG,
                'load_tie_rest': L_TIE_LIMB,
                'chain': _limb_chain(real),
                'erection_offset_m': ERECTION_OFFSET_M['limb'],
                'axis_top': top, 'axis_bottom': bottom,
                'real_frame_audit': {
                    'axis_top_m': [float(c) for c in top],
                    'axis_bottom_m': [float(c) for c in bottom],
                    'axis_top_source':
                        'MAT2-M02 blob fitted_humerus world vertices '
                        '(B04 fitted_humerus frame chain), max extent '
                        'along the declared axis',
                    'axis_bottom_source':
                        'MAT2-A06 grasp.palm_anchor via the blob hand '
                        'region admitted world_from_local transform '
                        '(asserted <=1e-12, transform_mismatch refuses)',
                    'transform_residuals_m':
                        {k: float(bones[k]['transform_residual_m'])
                         for k in bones}}}
    raise ValueError('shape_unknown:' + str(shape))


SHAPES = ('icosphere', 'cube', 'limb')


# --------------------------------------------------------------- ties -----
class TieElement:
    """M05 BondElement law form (tension-only) with declared rest length.

    M05's sealed module is the law authority, imported UNMODIFIED; its
    refusal vocabulary is reused verbatim (M10 heritage)."""

    REF_NOT_BOUND = 'bond_not_bound'
    REF_ALREADY = 'bond_already_bound'
    REF_RELEASE_UNBOUND = 'release_of_unbound_bond'

    def __init__(self, tie_id, k_tie, rest_length):
        require(k_tie > 0.0 and rest_length >= 0.0, 'tie_declaration_invalid')
        self.tie_id = tie_id
        self.k = float(k_tie)
        self.rest_length = float(rest_length)
        self.status = 'planned'
        self.bound_tick = None
        self.released_tick = None
        self.last_force = np.zeros(3)
        self.last_tension = 0.0
        self.last_extension = 0.0

    def bind(self, tick):
        require(self.status == 'planned', self.REF_ALREADY)
        self.status = 'qualified'
        self.bound_tick = int(tick)

    def release(self, tick):
        require(self.status == 'qualified', self.REF_RELEASE_UNBOUND)
        self.status = 'released'
        self.released_tick = int(tick)

    @property
    def active(self):
        return self.status == 'qualified'

    def force_on_body(self, anchor_point, x_body):
        if self.status == 'planned':
            raise ValueError(self.REF_NOT_BOUND)
        if not self.active:
            self.last_force = np.zeros(3)
            self.last_tension = 0.0
            self.last_extension = 0.0
            return np.zeros(3)
        d = anchor_point - x_body
        dist = float(np.linalg.norm(d))
        require(dist > 1e-12, 'tie_degenerate')
        ext = dist - self.rest_length
        self.last_extension = ext
        if ext <= 0.0:
            self.last_force = np.zeros(3)
            self.last_tension = 0.0
            return np.zeros(3)
        tension = self.k * ext
        axis = d / dist
        force = tension * axis
        self.last_force = force
        self.last_tension = tension
        return force


def refuse_auto_bond():
    """Explicit guard (M05 heritage): proximity never creates a bond."""
    raise ValueError('auto_bond_refused')


# --------------------------------------------------------------- world ----
class LimbWorld:
    """One declared run of the limb world (deterministic).

    ONE dynamics path for every shape. Declared substep order (digested per
    tick):
      1. damping (membrane c_v; load c_load; chain foot c_foot, bones
         c_bone; measured dissipation),
      2. pressure loads on CURRENT geometry (area-scaled, M03),
      3. gravity + tie forces: the load surrogate on its clamped-pole tie;
         the chain ties T1..Tn from the free pole through the elements;
         penalty ground contacts on every chain element; tie reactions on
         the declared rings (T1 reaction over the bottom ring, load
         reaction over the clamp ring) and on the proximal chain elements,
      4. semi-implicit step of the point masses and the membrane,
      5. batched under-relaxed XPBD edge+chord projection with the
         canonical post-projection velocity update (clamp ring excluded
         from the free weights),
      6. clamp pin: the declared overhead support re-pins the ring; the
         per-substep pin force m*drift/HS^2 is the MEASURED clamp reaction
         (M10 blocked-pin heritage),
      7. volume/work/ledger accumulation.
    """

    def __init__(self, shape, schedule_fn, ticks, mode='loaded', tamper=None,
                 real=None, snapshot_ticks=(), release_tie_id=None,
                 release_tick=None):
        require(shape in SHAPES, 'shape_unknown:' + str(shape))
        require(mode in ('loaded', 'off'), 'run_mode_invalid')
        self.shape = shape            # DATA tag only (never branched on)
        self.schedule_fn = schedule_fn
        self.ticks = int(ticks)
        self.mode = mode
        self.tamper = dict(tamper or {})
        self.pose_writer = bool(self.tamper.get('pose_writer', False))
        self.drop_load_reaction = bool(
            self.tamper.get('drop_load_reaction', False))
        self.drop_chain_reaction = bool(
            self.tamper.get('drop_chain_reaction', False))
        self.tie_boost = float(self.tamper.get('tie_boost', 1.0))
        self.constant_weighting = bool(
            self.tamper.get('constant_weighting', False))
        # PROBE-ONLY (never set by any bank or falsifier run): disables the
        # ground contacts so the free-hang sag can be measured for the
        # erection offset derivation (A2)
        self.probe_free_hang = bool(self.tamper.get('probe_free_hang',
                                                    False))
        self.release_tie_id = release_tie_id
        self.release_tick = release_tick
        spec = build_shape(shape, real)
        self.rest = spec['vertices'].copy()
        self.tris = spec['triangles']
        self.n_vertices = int(self.rest.shape[0])
        self.vertex_mass = spec['tissue_mass'] / self.n_vertices
        mem0 = pm.Membrane(self.rest, self.tris, 'm11_%s_rest' % shape)
        self.report = mem0.require_closed()
        self.volume_rest = float(self.report['signed_volume_m3'])
        # declared axis: principal direction of the rest geometry; for the
        # limb it is verified to run bottom(palm anchor) -> top(shoulder).
        # ERECTION ORIENTATION (A2): the pinned arm's world frame is NOT
        # z-up, so the rig is ROTATED to carry the declared axis along +z
        # before the hanging erection (a rigid placement of the declared
        # geometry; lengths, areas and the closure identity are invariant).
        ctr = self.rest.mean(axis=0)
        cov = np.cov((self.rest - ctr).T)
        eigval, vec = np.linalg.eigh(cov)
        self.axis = vec[:, int(np.argmax(eigval))]
        if 'axis_top' in spec:
            if float(np.dot(self.axis, spec['axis_top'] -
                            spec['axis_bottom'])) < 0.0:
                self.axis = -self.axis
        z_hat = np.array([0.0, 0.0, 1.0])
        c_dot = float(np.dot(self.axis, z_hat))
        if c_dot < 0.999999999:
            a = self.axis
            v_cross = np.cross(a, z_hat)
            s_norm = float(np.linalg.norm(v_cross))
            if s_norm < 1e-12:
                rot = np.diag([1.0, -1.0, -1.0])   # axis == -z: flip
            else:
                vx = np.array([[0.0, -v_cross[2], v_cross[1]],
                               [v_cross[2], 0.0, -v_cross[0]],
                               [-v_cross[1], v_cross[0], 0.0]])
                rot = np.eye(3) + vx + vx @ vx * ((1.0 - c_dot) / (s_norm * s_norm))
            self.rest = (rot @ self.rest.T).T
            self.axis = z_hat
            self.erection_rotation = {
                'rotated': True,
                'axis_dot_z_before': c_dot,
                'note': 'rigid placement rotation (declared axis -> +z); '
                        'no law input depends on absolute orientation'}
        else:
            self.erection_rotation = {'rotated': False,
                                      'axis_dot_z_before': c_dot}
        proj = self.rest @ self.axis
        self.top_idx = int(np.argmax(proj))
        self.bottom_idx = int(np.argmin(proj))
        # clamp ring: top pole + its 1-ring, fully pinned x,y,z (the
        # DECLARED visible overhead support; it never leaves the inventory)
        pairs, edge_index = _unique_edges(self.tris)
        self.edges = pairs
        nbrs = {}
        for a, b in pairs.tolist():
            nbrs.setdefault(a, set()).add(b)
            nbrs.setdefault(b, set()).add(a)
        clamp_set = {self.top_idx} | set(nbrs[self.top_idx])
        self.clamp_idx = np.array(sorted(clamp_set), dtype=np.int64)
        # declared load-introduction rings (Amendment A1: point tie forces
        # at a single pole vertex punctured the shell; reactions enter
        # through declared vertex patches, recorded in the state document)
        bottom_ring = {self.bottom_idx} | set(nbrs[self.bottom_idx])
        self.bottom_ring = np.array(sorted(bottom_ring), dtype=np.int64)
        # M04 iso-bladder edge law (E_TRANS, per edge, UNMODIFIED form)
        d = self.rest[pairs[:, 1]] - self.rest[pairs[:, 0]]
        self.l0 = np.linalg.norm(d, axis=1)
        require(np.all(self.l0 > 0.0), 'edge_rest_length_invalid')
        a_dual = np.zeros(len(pairs))
        for tri_idx, tri in enumerate(self.tris.tolist()):
            for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
                key = (a, b) if a < b else (b, a)
                a_dual[edge_index[key]] += mem0.areas[tri_idx]
        self.a_dual = a_dual
        self.k_edge = E_TRANS * T_WALL * a_dual / (self.l0 * self.l0)
        require(np.all(self.k_edge > 0.0), 'edge_stiffness_invalid')
        self.alpha = 1.0 / self.k_edge
        # belt chord family along the declared axis (M10 chord law form):
        # the measured M10 prolate-extension layout; the free pole descends
        # when pressurized
        zz = (proj - proj.min()) / max(1e-12, proj.max() - proj.min())
        chord_set = set()
        for v_i, ns in nbrs.items():
            if zz[v_i] > CHORD_CAP_Z:
                continue
            for t_v in ns:
                for w_v in nbrs[t_v]:
                    if w_v == v_i or w_v in ns:
                        continue
                    dv = self.rest[w_v] - self.rest[v_i]
                    lc = float(np.linalg.norm(dv))
                    require(lc > 0.0, 'chord_len_invalid')
                    dzz = abs(float(dv @ self.axis)) / lc
                    if BELT_DZ[0] <= dzz <= BELT_DZ[1]:
                        chord_set.add((min(v_i, w_v), max(v_i, w_v)))
        self.chords = (np.array(sorted(chord_set), dtype=np.int64)
                       if chord_set else np.zeros((0, 2), dtype=np.int64))
        self.n_chords = int(self.chords.shape[0])
        if self.n_chords:
            d_c = self.rest[self.chords[:, 1]] - self.rest[self.chords[:, 0]]
            self.chord_l0 = np.linalg.norm(d_c, axis=1)
            require(np.all(self.chord_l0 > 0.0), 'chord_rest_invalid')
            self.chord_k = E_FIBER * A_CHORD / np.maximum(self.chord_l0, 1e-12)
            self.chord_alpha = 1.0 / np.maximum(self.chord_k, 1e-12)
        else:
            self.chord_l0 = np.zeros(0)
            self.chord_k = np.zeros(0)
            self.chord_alpha = np.zeros(0)
        # ---- the chain (builder data; the dynamics loops over it) -------
        self.chain_spec = spec['chain']
        require(len(self.chain_spec) >= 1, 'chain_spec_empty')
        self.load_mass = spec['load_mass']
        # static erection (declared chain statics, Amendment A1 "declare
        # the rig geometry so at p=0 the foot hangs at a small declared
        # rest gap above the ground and the chain is taut"): tie i carries
        # the weights of the elements at/below it; ext_i = T_i / k;
        # the rig is lifted so the settled foot rests G_FOOT_TARGET_M above
        # the ground plane z=0 with every tie at its static extension.
        n_el = len(self.chain_spec)
        self.chain_mass = [float(e['mass_kg']) for e in self.chain_spec]
        self.chain_radius = [float(e['contact_radius_m'])
                             for e in self.chain_spec]
        w_below = [sum(self.chain_mass[i:] ) * GRAV
                   for i in range(n_el)]
        ext_static = [w / K_TIE_BONE for w in w_below]
        self.chain_static_tensions_n = w_below
        drop = [REST_GAP_CHAIN + e for e in ext_static]
        z_pole = (R_FOOT + G_FOOT_TARGET_M +
                  float(spec['erection_offset_m']) + sum(drop))
        z_elems = []
        z_acc = z_pole
        for dd in drop:
            z_acc -= dd
            z_elems.append(z_acc)
        lift = z_pole - float(self.rest[self.bottom_idx, 2])
        self.rest = self.rest + np.array([0.0, 0.0, lift])
        self.erection = {
            'static_tie_tensions_n': [float(w) for w in w_below],
            'static_tie_extensions_m': [float(e) for e in ext_static],
            'z_pole_target_m': float(z_pole),
            'z_elements_target_m': [float(z) for z in z_elems],
            'foot_gap_target_m': G_FOOT_TARGET_M,
            'lift_m': float(lift),
            'rest_gap_chain_m': REST_GAP_CHAIN,
            'note': 'declared static erection (A2); the presettle phase '
                    'absorbs the residual (vessel compliance not in the '
                    'static estimate; bounded by the declared gap target '
                    'margin)'}
        self.clamp_rest = np.column_stack(
            [self.rest[self.clamp_idx, :2],
             self.rest[self.clamp_idx, 2]]).copy()
        self.x = self.rest.copy()
        self.v = np.zeros_like(self.x)
        # chain element states (positions under the free pole; point masses,
        # placed at the declared static hang so the presettle residual is
        # only the vessel compliance)
        pole = self.rest[self.bottom_idx]
        self.chain_x = [pole - np.array([0.0, 0.0, drop[i]])
                        for i in range(n_el)]
        self.chain_x0 = [p.copy() for p in self.chain_x]
        self.chain_v = [np.zeros(3) for _ in range(n_el)]
        self.chain_x_before_tick = [p.copy() for p in self.chain_x]
        # surrogate load on its clamped-pole tie (declared hanging
        # surrogate; clamp-borne weight path; ring-introduced reaction);
        # placed at its declared static hang (rest + W/k below the pinned
        # pole) so it never swings: the surrogate is static ballast for the
        # whole run (A2)
        self.load_x = self.rest[self.top_idx] - np.array(
            [0.0, 0.0, spec['load_tie_rest'] +
             self.load_mass * GRAV / K_TIE])
        self.load_v = np.zeros(3)
        # ties (all M05-form; bound explicitly, never auto-bonded)
        self.load_tie = TieElement('load:clamped_pole', K_TIE,
                                   spec['load_tie_rest'])
        self.load_tie.bind(0)
        self.chain_ties = []
        for i, el in enumerate(self.chain_spec):
            tie = TieElement(el['tie_id'], K_TIE_BONE, REST_GAP_CHAIN)
            tie.bind(0)
            self.chain_ties.append(tie)
        self.chain_tie_ids = [t.tie_id for t in self.chain_ties]
        # X2a/FB6: assembly masses audited bitwise against a fresh read of
        # the pinned B03 document (a synthetic stand-in refuses here)
        self.spec_real_frame_audit = spec.get('real_frame_audit')
        self.mass_audit = assembly_mass_audit(self.chain_spec, real) \
            if real is not None else {
                'bitwise_matches_pinned_b03': None,
                'checked': {e['name']: 'no_real_data_for_this_shape'
                            for e in self.chain_spec},
                'hand_counted_mass_kg': None}
        self.site_bindings = [
            {'tie_id': el['tie_id'], 'name': el['name'],
             'site': el['tie_site_record'], 'status': el['status']}
            for el in self.chain_spec if el['tie_site_record'] is not None]
        self.source = pm.PressureSource(
            SOURCE_ID, P_EXT_PA, P_EXT_PA, MAX_DELTA_P_PA,
            MAX_FLOW_M3_PER_S, SOURCE_PROVENANCE)
        self.snapshot_ticks = sorted(int(t) for t in snapshot_ticks)
        self.snapshots = []
        self.record_forces = bool(self.tamper.get('record_forces', False))
        self.force_rows = []
        self.traction_ratio_worst = 0.0
        self.max_dp_seen = 0.0
        self.max_flow_seen = 0.0
        self.max_speed_seen = 0.0
        self.position_drift_m = 0.0
        self.clamp_force_acc = np.zeros(3)
        self.clamp_force_n = 0
        self.tie_law_dev_max = 0.0
        self.interface_dev_max = 0.0
        self.grav_turnover_j = 0.0
        self.prev_pz = 0.0
        self.spec_tissue_mass = float(spec['tissue_mass'])

    # -- helpers ----------------------------------------------------------
    def _membrane(self):
        return pm.Membrane(self.x, self.tris, 'm11_membrane_current')

    def _pole_point(self):
        return self.x[self.bottom_idx]

    def _clamp_point(self):
        return self.x[self.top_idx]

    def _chain_ke(self):
        return sum(0.5 * self.chain_mass[i] * float(self.chain_v[i] @
                                                    self.chain_v[i])
                   for i in range(len(self.chain_x)))

    def _energies(self):
        m = self
        d = self.x[m.edges[:, 1]] - self.x[m.edges[:, 0]]
        length = np.linalg.norm(d, axis=1)
        u_edge = float((0.5 * m.k_edge * (length - m.l0) ** 2).sum())
        if m.n_chords:
            d_c = self.x[m.chords[:, 1]] - self.x[m.chords[:, 0]]
            lc = np.linalg.norm(d_c, axis=1)
            ext = np.maximum(lc - m.chord_l0, 0.0)
            u_edge += float((0.5 * m.chord_k * ext * ext).sum())
        u_ties = 0.0
        if m.load_tie.last_extension > 0.0:
            u_ties += 0.5 * m.load_tie.k * m.load_tie.last_extension ** 2
        for tie in m.chain_ties:
            if tie.last_extension > 0.0:
                u_ties += 0.5 * tie.k * tie.last_extension ** 2
        e_grav = m.load_mass * GRAV * float(m.load_x[2]) + \
            m.vertex_mass * GRAV * float(self.x[:, 2].sum())
        for i in range(len(m.chain_x)):
            e_grav += m.chain_mass[i] * GRAV * float(m.chain_x[i][2])
        u_contact = 0.0
        for i in range(len(m.chain_x)):
            pen = max(0.0, m.chain_radius[i] - float(m.chain_x[i][2]))
            u_contact += 0.5 * K_CONTACT * pen * pen
        e_kin = float(0.5 * m.vertex_mass * (self.v * self.v).sum()) + \
            0.5 * m.load_mass * float(m.load_v @ m.load_v) + m._chain_ke()
        return e_kin, u_edge, u_ties, e_grav, u_contact

    def _state_digest(self, tick):
        payload = {
            'tick': int(tick),
            'x': [[float(c) for c in row] for row in self.x],
            'x_load': [float(c) for c in self.load_x],
            'x_chain': [[float(c) for c in p] for p in self.chain_x],
            'energies': [float(e) for e in self._energies()],
        }
        return digest(payload)

    def total_weight_n(self):
        """W_total: tissue + surrogate load + chain element weights."""
        return (self.spec_tissue_mass + self.load_mass +
                sum(self.chain_mass)) * GRAV

    # -- the ONE dynamics path --------------------------------------------
    def run(self):
        self.spec_tissue_mass = self.vertex_mass * self.n_vertices
        rows = []
        w_press_cum = 0.0
        q_cum = 0.0
        settle_start = self.ticks - SETTLE_WINDOW
        x_before_tick = self.x.copy()
        n_el = len(self.chain_x)
        for tick in range(self.ticks):
            dp = float(self.schedule_fn(tick))
            self.max_dp_seen = max(self.max_dp_seen, abs(dp))
            source = self.source.with_delta_p(dp)   # enforces M03 limits
            if (self.release_tie_id is not None
                    and self.release_tick is not None
                    and tick == self.release_tick):
                for tie in self.chain_ties:
                    if tie.tie_id == self.release_tie_id:
                        tie.release(tick)
            tick_w_vol = 0.0
            tick_q = 0.0
            e0 = self._energies()
            clamp_fz_tick = 0.0
            f_rows = []
            for sub in range(N_SUB):
                x_before = self.x.copy()
                mem = self._membrane()
                v_start = mem.signed_volume()
                # 1. damping (measured dissipation of this step)
                dmf = max(0.0, 1.0 - C_V * HS)
                ldf = max(0.0, 1.0 - C_LOAD * HS)
                q_damp = 0.5 * self.vertex_mass * \
                    float((self.v * self.v).sum()) * (1.0 - dmf * dmf) + \
                    0.5 * self.load_mass * \
                    float((self.load_v * self.load_v).sum()) * \
                    (1.0 - ldf * ldf)
                self.v = self.v * dmf
                self.load_v = self.load_v * ldf
                for i in range(n_el):
                    c_i = C_FOOT if i == n_el - 1 else C_BONE
                    f_i = max(0.0, 1.0 - c_i * HS)
                    q_damp += 0.5 * self.chain_mass[i] * \
                        float(self.chain_v[i] @ self.chain_v[i]) * \
                        (1.0 - f_i * f_i)
                    self.chain_v[i] = self.chain_v[i] * f_i
                tick_q += q_damp
                ke_damped = 0.5 * self.vertex_mass * \
                    float((self.v * self.v).sum()) + \
                    0.5 * self.load_mass * \
                    float((self.load_v * self.load_v).sum()) + \
                    self._chain_ke()
                # 2. pressure loads on CURRENT geometry (area-scaled, M03)
                weighting = ('constant' if self.constant_weighting
                             else 'area')
                loads, forces, _ = mem.vertex_loads(
                    source, area_weighting=weighting)
                if sub == 0 and abs(source.delta_p) > 0.0:
                    ratio = np.linalg.norm(forces, axis=1) / mem.areas
                    err = float(np.max(np.abs(
                        ratio - abs(source.delta_p))) / abs(source.delta_p))
                    self.traction_ratio_worst = max(
                        self.traction_ratio_worst, err)
                patch_force = np.zeros_like(self.x)
                # 3a. surrogate load: gravity + tie to the clamped pole
                f_grav_load = np.array([0.0, 0.0, -self.load_mass * GRAV])
                f_load_tie = self.load_tie.force_on_body(
                    self._clamp_point(), self.load_x)
                f_load_applied = f_load_tie * self.tie_boost
                load_reaction = -f_load_tie
                load_reaction_applied = np.zeros(3) if \
                    self.drop_load_reaction else load_reaction
                if self.record_forces:
                    f_rows.append([float(c) for c in f_load_tie] +
                                  [float(c) for c in load_reaction_applied])
                self.tie_law_dev_max = max(
                    self.tie_law_dev_max,
                    float(np.max(np.abs(f_load_applied - f_load_tie))))
                self.interface_dev_max = max(
                    self.interface_dev_max,
                    float(np.max(np.abs(load_reaction_applied -
                                        load_reaction))))
                dx_load = (self.load_v +
                           (f_grav_load + f_load_applied) /
                           self.load_mass * HS) * HS
                self.load_v = self.load_v + \
                    (f_grav_load + f_load_applied) / self.load_mass * HS
                self.load_x = self.load_x + dx_load
                if not self.drop_load_reaction:
                    patch_force[self.clamp_idx] += \
                        load_reaction_applied / len(self.clamp_idx)
                # 3b. the chain: ties + gravity + penalty ground contacts
                f_ties = []
                for k in range(n_el):
                    anchor = self._pole_point() if k == 0 \
                        else self.chain_x[k - 1]
                    f_ties.append(self.chain_ties[k].force_on_body(
                        anchor, self.chain_x[k]))
                chain_forces = []
                for k in range(n_el):
                    f_k = np.array(
                        [0.0, 0.0, -self.chain_mass[k] * GRAV]) + f_ties[k]
                    if k + 1 < n_el:
                        f_k = f_k - f_ties[k + 1]   # distal tie reaction
                    pen = 0.0 if self.probe_free_hang else max(
                        0.0, self.chain_radius[k] -
                        float(self.chain_x[k][2]))
                    f_k = f_k + np.array([0.0, 0.0, K_CONTACT * pen])
                    chain_forces.append(f_k)
                f_t1_law = f_ties[0].copy()
                f_t1_applied = f_ties[0] * self.tie_boost
                t1_reaction = -f_ties[0]
                t1_reaction_applied = np.zeros(3) if \
                    self.drop_chain_reaction else t1_reaction
                if self.record_forces:
                    f_rows[-1] = f_rows[-1] + \
                        [float(c) for c in chain_forces[-1]] + \
                        [float(c) for c in f_t1_law] + \
                        [float(c) for c in f_t1_applied] + \
                        [float(c) for c in t1_reaction_applied]
                self.tie_law_dev_max = max(
                    self.tie_law_dev_max,
                    float(np.max(np.abs(f_t1_applied - f_t1_law))))
                self.interface_dev_max = max(
                    self.interface_dev_max,
                    float(np.max(np.abs(t1_reaction_applied -
                                        t1_reaction))))
                for k in range(n_el):
                    self.chain_v[k] = self.chain_v[k] + \
                        chain_forces[k] / self.chain_mass[k] * HS
                    self.chain_x[k] = self.chain_x[k] + \
                        self.chain_v[k] * HS
                if not self.drop_chain_reaction:
                    patch_force[self.bottom_ring] += \
                        t1_reaction_applied / len(self.bottom_ring)
                if self.pose_writer:
                    # FB1 tamper: kinematic pose writer teleports the foot
                    # to the hung (loaded-interface) pose
                    self.chain_x[-1] = self._pole_point() - np.array(
                        [0.0, 0.0, REST_GAP_CHAIN])
                    self.chain_v[-1] = np.zeros(3)
                # 4. semi-implicit membrane step (the declared tissue
                # mass is weighted: gravity enters with the pressure and
                # patch forces so W_total balances through the clamp)
                f_grav_verts = self.vertex_mass * GRAV
                self.v = self.v + (loads + patch_force -
                                   f_grav_verts) / \
                    self.vertex_mass * HS
                self.x = self.x + self.v * HS
                # 5. batched XPBD edge+chord projection (under-relaxed),
                #    canonical post-projection velocity update; clamp ring
                #    excluded from the free weights
                w = np.ones(self.n_vertices) / self.vertex_mass
                w[self.clamp_idx] = 0.0
                e_i = np.concatenate([self.edges[:, 0], self.chords[:, 0]])
                e_j = np.concatenate([self.edges[:, 1], self.chords[:, 1]])
                L0_all = np.concatenate([self.l0, self.chord_l0])
                alpha_all = np.concatenate([self.alpha, self.chord_alpha])
                w_i, w_j = w[e_i], w[e_j]
                alpha_t = alpha_all / (HS * HS)
                v_count = self.n_vertices
                n_e = len(self.edges)
                for _ in range(XPBD_ITERS):
                    d = self.x[e_j] - self.x[e_i]
                    length = np.linalg.norm(d, axis=1)
                    length = np.maximum(length, 1e-12)
                    n = d / length[:, None]
                    c = length - L0_all
                    # tension-only chords (draft/M10-M11 form): a compressed
                    # chord carries no correction
                    if n_e < len(c):
                        c = np.where(np.arange(len(c)) < n_e, c,
                                     np.maximum(c, 0.0))
                    dlam = -c / (w_i + w_j + alpha_t)
                    gi = -(w_i * dlam)[:, None] * n
                    gj = (w_j * dlam)[:, None] * n
                    dx = np.zeros_like(self.x)
                    for comp in range(3):
                        dx[:, comp] = (
                            np.bincount(e_i,
                                        weights=XPBD_RELAX * gi[:, comp],
                                        minlength=v_count) +
                            np.bincount(e_j,
                                        weights=XPBD_RELAX * gj[:, comp],
                                        minlength=v_count))
                    self.x = self.x + dx
                self.v = (self.x - x_before) / HS
                # 6. clamp pin: the declared overhead support (the
                # draft form: the ring velocity is zeroed at the pin; a
                # drift/HS velocity carry-over goes into a substep limit
                # cycle when large direct forces -- the surrogate-load
                # reaction -- hang on the pinned ring; probed: 3 m/s
                # ring churn, 0.08 J/tick spurious dissipation). The KE
                # removed at the pin is bounded by the one-substep force
                # impulse (F^2 HS^2 / 2m ~ 1e-9 J per vertex here) and
                # stays inside the X8 cumulative bound. The GATED clamp
                # datum is the per-tick momentum balance (the only
                # externals are gravity, contacts and the clamp):
                # F_clamp_z = dP_z/dt + W_total - F_contacts_z.
                drift = self.clamp_rest - self.x[self.clamp_idx]
                f_pin = self.vertex_mass * drift / (HS * HS)
                self.clamp_force_acc += f_pin.sum(axis=0)
                self.clamp_force_n += 1
                clamp_fz_tick += float(f_pin[:, 2].sum())
                self.x[self.clamp_idx] = self.clamp_rest
                self.v[self.clamp_idx] = 0.0
                # A1.8 heritage: the substep's non-damping kinetic-energy
                # change is MEASURED, not modeled
                ke_post = 0.5 * self.vertex_mass * \
                    float((self.v * self.v).sum()) + \
                    0.5 * self.load_mass * \
                    float((self.load_v * self.load_v).sum()) + \
                    self._chain_ke()
                tick_q += ke_post - ke_damped
                # 7. volume/work accumulation
                mem_after = self._membrane()
                v_end = mem_after.signed_volume()
                tick_w_vol += source.delta_p * (v_end - v_start)
            # per-tick ledger
            e1 = self._energies()
            total0 = sum(e0)
            total1 = sum(e1)
            self.grav_turnover_j += abs(e1[3] - e0[3])
            r_tick = (total1 - total0) + tick_q - tick_w_vol
            turnover = abs(tick_w_vol) + abs(tick_q) + abs(total1 - total0)
            w_press_cum += tick_w_vol
            q_cum += tick_q
            v_free = self.v.copy()
            v_free[self.clamp_idx] = 0.0
            speed = max(float(np.max(np.linalg.norm(v_free, axis=1))),
                        float(np.linalg.norm(self.load_v)),
                        max(float(np.linalg.norm(cv))
                            for cv in self.chain_v))
            if tick >= settle_start:
                self.max_speed_seen = max(self.max_speed_seen, speed)
                drift_all = float(np.max(np.abs(self.x - x_before_tick)))
                for k in range(n_el):
                    drift_all = max(drift_all, float(
                        np.abs(self.chain_x[k] -
                               self.chain_x_before_tick[k]).max()))
                self.position_drift_m = max(self.position_drift_m,
                                            drift_all)
            pen_foot = max(0.0, self.chain_radius[-1] -
                           float(self.chain_x[-1][2]))
            pz = (float(self.v[:, 2].sum()) * self.vertex_mass +
                  float(self.load_v[2]) * self.load_mass +
                  sum(float(self.chain_v[k][2]) * self.chain_mass[k]
                      for k in range(n_el)))
            f_clamp_momentum = (pz - self.prev_pz) / DT + \
                self.total_weight_n() - K_CONTACT * pen_foot
            self.prev_pz = pz
            row = {
                'tick': tick,
                'phase': phase_of(tick),
                'delta_p_pa': dp,
                'volume_m3': float(v_end),
                'pole_gap_m': self.pole_gap(),
                'bottom_pole_z_m': float(self.x[self.bottom_idx, 2]),
                'load_z_m': float(self.load_x[2]),
                'load_tie_tension_n': float(self.load_tie.last_tension),
                'chain_z_m': [float(p[2]) for p in self.chain_x],
                'chain_tie_tensions_n': [float(t.last_tension)
                                         for t in self.chain_ties],
                'chain_tie_extensions_m': [float(t.last_extension)
                                           for t in self.chain_ties],
                'chain_contact_forces_n': [
                    K_CONTACT * max(0.0, self.chain_radius[k] -
                                    float(self.chain_x[k][2]))
                    for k in range(n_el)],
                'chain_contact_penetrations_m': [
                    max(0.0, self.chain_radius[k] -
                        float(self.chain_x[k][2]))
                    for k in range(n_el)],
                'contact_force_n': K_CONTACT * pen_foot,
                'contact_penetration_m': pen_foot,
                'foot_gap_m': float(self.chain_x[-1][2] -
                                    self.chain_radius[-1]),
                'clamp_fz_n': f_clamp_momentum,
                'clamp_pin_datum_n': clamp_fz_tick / N_SUB,
                'e_kin_j': e1[0], 'u_edge_j': e1[1], 'u_ties_j': e1[2],
                'e_grav_j': e1[3], 'u_contact_j': e1[4],
                'q_tick_j': tick_q,
                'w_press_vol_j': tick_w_vol,
                'r_tick_j': r_tick,
                'turnover_j': turnover,
                'w_press_cum_j': w_press_cum,
                'q_cum_j': q_cum,
                'residual_cum_j': r_tick if tick == 0 else
                rows[-1]['residual_cum_j'] + r_tick,
                'max_speed_m_per_s': speed,
                'state_digest': self._state_digest(tick),
            }
            x_before_tick = self.x.copy()
            self.chain_x_before_tick = [p.copy() for p in self.chain_x]
            rows.append(row)
            if self.record_forces:
                self.force_rows.append(f_rows)
            if (tick + 1) in self.snapshot_ticks:
                self.snapshots.append({
                    'tick': tick + 1, 'x': self.x.copy(),
                    'load': self.load_x.copy(),
                    'chain': [p.copy() for p in self.chain_x],
                    'delta_p_pa': float(dp),
                    'volume_m3': float(v_end),
                    'pole_gap_m': self.pole_gap(),
                    'foot_gap_m': float(self.chain_x[-1][2] -
                                        self.chain_radius[-1]),
                    'w_press_cum_j': float(w_press_cum),
                    'chain_tie_tensions_n': [float(t.last_tension)
                                             for t in self.chain_ties],
                    'load_tie_tension_n':
                        float(self.load_tie.last_tension),
                    'clamp_fz_n': clamp_fz_tick,
                    'state_digest': self._state_digest(tick)})
            if tick >= settle_start and len(rows) >= 2:
                flow = abs(rows[-1]['volume_m3'] -
                           rows[-2]['volume_m3']) / DT
                self.max_flow_seen = max(self.max_flow_seen, flow)
        self.rows = rows
        self.w_press_total = w_press_cum
        self.q_total = q_cum
        return self

    # -- metrics ------------------------------------------------------------
    def pole_gap(self):
        return float((self.x[self.top_idx] - self.x[self.bottom_idx]) @
                     self.axis)

    def window_mean(self, lo, hi, key):
        sel = [r for r in self.rows if lo <= r['tick'] < hi]
        require(sel, 'window_empty')
        return float(np.mean([r[key] for r in sel]))

    def window_min(self, lo, hi, key):
        sel = [r for r in self.rows if lo <= r['tick'] < hi]
        require(sel, 'window_empty')
        return float(np.min([r[key] for r in sel]))

    def clamp_force_mean(self):
        require(self.clamp_force_n > 0, 'clamp_force_unmeasured')
        return self.clamp_force_acc / self.clamp_force_n

    def settle_stats(self):
        return {
            'max_speed_m_per_s': self.max_speed_seen,
            'position_drift_m': self.position_drift_m,
            'clamp_force_n': [float(c) for c in self.clamp_force_mean()],
            'traction_ratio_worst': self.traction_ratio_worst,
            'max_delta_p_pa': self.max_dp_seen,
            'max_flow_m3_per_s': self.max_flow_seen,
            'tie_law_dev_max_n': self.tie_law_dev_max,
            'interface_dev_max_n': self.interface_dev_max,
            'grav_turnover_j': self.grav_turnover_j,
        }

    # -- audits -------------------------------------------------------------
    def audit_foot_trajectory(self):
        """FB1 clean control: re-integrate the FOOT along z from the
        RECORDED per-substep total forces with the declared integrator;
        returns the max deviation from the emitted trajectory z (m)."""
        require(self.record_forces, 'audit_requires_force_rows')
        v = 0.0
        pos = float(self.chain_x0[-1][2])
        worst = 0.0
        for tick in range(self.ticks):
            for sub in range(N_SUB):
                f = float(self.force_rows[tick][sub][8])   # fz of the foot
                ff = max(0.0, 1.0 - C_FOOT * HS)
                v = v * ff
                v = v + f / self.chain_mass[-1] * HS
                pos = pos + v * HS
            worst = max(worst, abs(pos - self.rows[tick]['chain_z_m'][-1]))
        return worst

    def audit_tie_interface(self):
        """FB3/FB5 state-determined audit: the applied chain tie force must
        equal the M05 law force at the same state and the applied reaction
        must equal its negative (equal/opposite). Uses the recorded
        per-substep force rows (T1 block); clean runs are bitwise-zero."""
        require(self.record_forces, 'audit_requires_force_rows')
        worst_law = 0.0
        worst_reaction = 0.0
        peak = 0.0
        for tick in range(self.ticks):
            for sub in range(N_SUB):
                row = self.force_rows[tick][sub]
                f_law = np.array(row[9:12])
                f_applied = np.array(row[12:15])
                r_applied = np.array(row[15:18])
                worst_law = max(worst_law, float(
                    np.linalg.norm(f_applied - f_law)))
                worst_reaction = max(worst_reaction, float(
                    np.linalg.norm(r_applied + f_law)))
                peak = max(peak, float(np.linalg.norm(f_law)))
        return {'max_force_law_dev_n': worst_law,
                'max_reaction_dev_n': worst_reaction,
                'peak_law_force_n': peak}

    def check_ledger_gates(self):
        """X8: the per-tick residuals are REPORTED (rows, never hidden);
        the binding no-source claim is the cumulative gate (prereg
        section 5, M03 T9 / M10 A1.8 heritage):
          |sum R| <= max(0.05*|W_press_total| + 0.05*grav_turnover, 5e-4 J)."""
        worst_rel = 0.0
        for row in self.rows:
            worst_rel = max(worst_rel, abs(row['r_tick_j']) /
                            max(row['turnover_j'], 1e-12))
        cum_r = sum(r['r_tick_j'] for r in self.rows)
        cum_bound = max(REL * abs(self.w_press_total) +
                        REL * self.grav_turnover_j, 5.0e-4)
        return {'ledger_worst_relative_r': worst_rel,
                'ledger_cumulative_residual_j': cum_r,
                'ledger_cumulative_bound_j': cum_bound,
                'ledger_cumulative_within':
                    bool(abs(cum_r) <= cum_bound),
                'w_press_total_j': self.w_press_total,
                'grav_turnover_j': self.grav_turnover_j,
                'ticks_checked': len(self.rows)}
