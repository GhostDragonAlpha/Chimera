"""MAT2-M11: reuse the same material rules in a loaded monkey limb.

One SHAPE-PARAMETRIC material law implementation (the sealed M03/M04/M05 law
stack, imported UNMODIFIED — composition only, no upstream edits), exercised
on three declared shapes supplied purely as geometry data:

  icosphere  M03 icosphere L2 (R = 0.05 m)   (the M03/M10 lineage shape)
  cube       M03 cube_grid                    (topologically distinct)
  limb       capped tube bladder erected between real endpoints of the
             pinned macaque arm (B03/B02 geometry), carrying the REAL B03
             bone masses at REAL A06 attachment sites

There is NO shape-specific motion code: shapes differ only in builder data
(SHAPES registry below); the dynamics path (schedule, substep order,
projection, contact, tie solve, ledger) is one code path (LimbWorld.run).
Gate X1a audits this by AST.

Load path (tissue -> bone -> foot -> ground): an extending bladder column
(belt chord family, M10's measured prolate-extension direction — same law
code, layout is authored data) stands on the ground through the FOOT; the
shoulder guide is a declared LATERAL guide (x,y pinned, z free) so no
vertical load can bypass the column; the declared load hangs from the top
pole; bones ride the column through M05-form ties bound at real A06 sites;
the foot is a declared contact element resting on the M05-law penalty plane.

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
# carried from M03/M04/M05); PREREGISTRATION section 3 is the freeze.
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
# Point-mass mode damping, derived from declared constants (Amendment A1):
# critical damping for a mass-spring mode is c_crit = 2*sqrt(k*m);
#   foot-contact mode k=K_CONTACT, m=M_FOOT: c_crit = 63.2 1/s -> C_FOOT
#   declared 3.16x critical (overdamped, settles within P0);
#   bone-tie mode k=K_TIE_BONE, m=humerus 0.0225 kg: c_crit = 23.2 1/s ->
#   C_BONE declared 1.3x critical.
C_FOOT = 200.0
C_BONE = 30.0
SYNTH_TISSUE_MASS_KG = 0.020     # synthetic shapes: equal per vertex (M10)
LIMB_TISSUE_MASS_KG = 2.0e-3     # limb: declared tissue mass (NOT a bone mass)
M_LOAD_SYNTH_KG = 2.0            # synthetic-column compression load (declared;
                                 # Amendment A1: > thrust p_hold*pi*R^2 =
                                 # 7.85 N at 1000 Pa, margin 2.5x, so the
                                 # column stays in stance compression)
M_LOAD_LIMB_KG = 0.25            # limb stance surrogate (declared; > thrust
                                 # 0.45 N at 1000 Pa, margin 5.4x; a
                                 # forelimb-share body-weight surrogate, NOT a
                                 # measured claim)
M_FOOT_SYNTH_KG = 0.010          # synthetic-shape foot point mass (declared)
M_FOOT_LIMB_KG = 0.010           # limb foot INERTIAL mass (declared; Amendment
                                 # A1: B03 counted hand mass stays 0.0 bitwise;
                                 # the contact element needs a declared
                                 # inertial mass, labeled engineering)
GRAV = 9.80665
K_TIE = 600.0                    # N/m (M05-form tie, M10 heritage)
L_TIE_SYNTH = 0.10               # m load-tie rest (synthetic shapes)
L_TIE_LIMB = 0.05                # m load-tie rest (limb; prereg section 3)
K_TIE_BONE = 600.0               # N/m bone ties (same M05 form)
GUIDE_EXTRA_LATERAL_N_PER_M = 0.0   # (reserved; guide is a hard x,y pin)
R_FOOT = 5.0e-3                  # m foot contact radius (declared)
K_CONTACT = ix05.K_CONTACT_PA_PER_M   # 1.0e5, M05 pinned law (never invented)
SOURCE_ID = 'm11_source'
P_EXT_PA = 0.0
MAX_DELTA_P_PA = 5000.0
MAX_FLOW_M3_PER_S = 1.0e-3
SOURCE_PROVENANCE = ('MAT2-M11 preregistered pneumatic source '
                     '(engineering actuator demonstration; M03 limits)')
DP_WORK_PA = 1000.0
# Amendment A1 load/thrust balance: DP_WORK_PA lowered 4000 -> 1000 Pa so
# the pressure thrust (icosphere: p*pi*R^2 = 7.85 N; limb tube:
# p*pi*R_T^2 = 0.45 N) stays BELOW the declared compression loads
# (2.0 kg -> 19.6 N, margin 2.5x; 0.25 kg -> 2.45 N, margin 5.4x): the
# column stays in stance compression instead of lifting off (probed:
# 49 N point tie at 4000 Pa inverted the shell through the single pole
# vertex; reactions now distribute over declared rings).
M_LOAD_SYNTH_KG = 2.0            # synthetic-column compression load (declared)
# schedule (prereg section 4)
PRESETTLE_END = 200
RAMP_UP_END = 400
HOLD_END = 1100
POWER_OFF_END = 1300
TOTAL_TICKS = 1500
SETTLE_WINDOW = 200
RELEASE_TICK = 450               # connection-removal control (declared)
SNAP_TICKS = (0, 300, 450, 700, 1000, 1100, 1200, 1350, 1499)
BASELINE_WINDOW = (100, 200)
LOADED_WINDOW = (1000, 1100)
OFF_WINDOW = (1400, 1500)
# frozen windows (prereg section 5; derived from declared constants)
X_FLOOR_M = 1.0e-7               # integrator positional identity floor
REL = 0.05
BITE_M = 1.0e-3                  # connection-removal departure bite
TRACTION_RATIO_REL = 1.0e-9
AUDIT_WINDOW_M = 1.0e-9
AUDIT_BITE_M = 1.0e-3
GUIDE_FZ_FLOOR_N = K_CONTACT * X_FLOOR_M   # 1.0e-2 N
PHASE_NAMES = ('P0_presettle', 'A_rampup', 'B_hold', 'C_poweroff',
               'D_settled_off')


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
    """Preregistered schedule (PASCALS): 0 (0-199), ramp 0->4000 (200-399),
    hold 4000 (400-1099), ramp to 0 POWER OFF (1100-1299), 0 (1300-1499)."""
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
    vertices to <=1e-12 or the binding refuses (transform_mismatch) — it is
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
        mid = 'bone_' + bone
        require(mid in matter, 'real_mass_missing:' + mid)
        region = [r for r in b03['regions'] if r['id'] == bone][0]
        key = region['rest_geometry']['mesh_blob_region_key']
        src = blob['regions'][key]
        r_mat, t_vec, err = _rigid_from_body_to_world(
            np.array(src['vertices_m'], dtype=np.float64),
            np.array(src['world_vertices_m'], dtype=np.float64))
        bones[bone] = {
            'mass_kg': matter[mid]['mass_kg'],
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
        'counted_source': 'MAT2-B03 matter entry shell_hand (zero, bitwise)',
        'region_frame': hand_region['rest_geometry']['frame'],
        'frame_id': 'unresolved_body:hand (B04 admission ledger)',
        'mesh_region_key': key,
        'vertices_m': np.array(src['vertices_m'], dtype=np.float64),
        'world_vertices_m': np.array(src['world_vertices_m'],
                                     dtype=np.float64),
        'transform_residual_m': err,
        'status': 'explicitly_unresolved_terminal',
    }
    frames = {k: v['frame_id'] for k, v in b04['fitted_frames'].items()}
    sites = a06['path_records']
    palm = [e for e in a06['grasp_endpoints']
            if e['endpoint_id'] == 'grasp.palm_anchor']
    ports = b05['ports']
    ledger = b05['input_status_ledger']
    return {'b03': b03, 'b04': b04, 'a06': a06, 'b05': b05, 'bones': bones,
            'frames': frames, 'sites': sites, 'palm': palm,
            'ports': ports, 'ledger': ledger,
            'blob_frame_note': blob['frame_note']}


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

    Pure geometry data for the `limb` shape; the DYNAMICS never branches on
    which builder produced the mesh. Outward-consistent winding: ring
    quads + two apex caps (ring order verified by Membrane.require_closed
    at build; a winding defect refuses at construction)."""
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
        # sphere-cap profile: rings sweep z from -R..+R in tube-local frame
        zc = -radius + (2.0 * radius) * (ri + 0.5) / rings
        center_local = zc
        rr = math.sqrt(max(1e-16, radius * radius - zc * zc))
        ring_start.append(len(verts))
        base = p0 + a_hat * (span + 2.0 * center_local) / 2.0
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
        tris.append((0, ring_start[0] + ki, ring_start[0] + k2))
    base = ring_start[-1]                        # north cap
    for ki in range(radials):
        k2 = (ki + 1) % radials
        tris.append((north, base + k2, base + ki))
    return v, np.array(tris, dtype=np.int64)


def build_shape(shape, real=None):
    """The SHAPES registry: builders return GEOMETRY DATA only.

    The dynamics (LimbWorld) never reads the shape value — audit X1a."""
    if shape == 'icosphere':
        shell = pm.icosphere(SPHERE_LEVEL, SPHERE_R, 'm11_icosphere')
        return {'vertices': shell.vertices.copy(),
                'triangles': np.asarray(shell.triangles,
                                        dtype=np.int64).copy(),
                'tissue_mass': SYNTH_TISSUE_MASS_KG,
                'foot_mass': M_FOOT_SYNTH_KG, 'load_tie_rest': L_TIE_SYNTH,
                'load_mass': M_LOAD_SYNTH_KG,
                'bones': {}, 'sites': []}
    if shape == 'cube':
        shell = pm.cube_grid(CUBE_N, CUBE_SIDE, 'm11_cube')
        return {'vertices': shell.vertices.copy(),
                'triangles': np.asarray(shell.triangles,
                                        dtype=np.int64).copy(),
                'tissue_mass': SYNTH_TISSUE_MASS_KG,
                'foot_mass': M_FOOT_SYNTH_KG, 'load_tie_rest': L_TIE_SYNTH,
                'load_mass': M_LOAD_SYNTH_KG,
                'bones': {}, 'sites': []}
    if shape == 'limb':
        require(real is not None, 'limb_requires_real_data')
        bones = real['bones']
        top_sel = bones['humerus']['world_vertices_m']
        bot_sel = bones['hand']['world_vertices_m']
        axis_hint = top_sel.mean(axis=0) - bot_sel.mean(axis=0)
        a_hat = axis_hint / float(np.linalg.norm(axis_hint))
        top = top_sel[int(np.argmax(top_sel @ a_hat))]
        bottom = bot_sel[int(np.argmin(bot_sel @ a_hat))]
        v, t = _capped_tube(bottom, top, TUBE_RADIUS, TUBE_RINGS,
                            TUBE_RADIALS)
        return {'vertices': v, 'triangles': t,
                'tissue_mass': LIMB_TISSUE_MASS_KG,
                'foot_mass': M_FOOT_LIMB_KG, 'load_tie_rest': L_TIE_LIMB,
                'load_mass': M_LOAD_LIMB_KG,
                'bones': bones, 'sites': real['sites'],
                'axis_top': top, 'axis_bottom': bottom}
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
      1. damping (membrane c_v, point masses c_load; measured dissipation),
      2. pressure loads on CURRENT geometry (area-scaled, M03),
      3. gravity + tie forces (load tie, bone ties, foot tie) + ground
         penalty contact on the foot + tie reactions on anchor vertices,
      4. semi-implicit step,
      5. batched under-relaxed XPBD edge+chord projection with the canonical
         post-projection velocity update; guide ring pinned in x,y,
      6. volume/work/ledger accumulation.
    """

    def __init__(self, shape, schedule_fn, ticks, mode='loaded', tamper=None,
                 real=None, snapshot_ticks=(), release_bone_ties_at=None,
                 pin_guide_z=False):
        require(shape in SHAPES, 'shape_unknown:' + str(shape))
        self.shape = shape            # DATA tag only (never branched on)
        self.schedule_fn = schedule_fn
        self.ticks = int(ticks)
        self.mode = mode
        self.tamper = dict(tamper or {})
        self.pose_writer = bool(self.tamper.get('pose_writer', False))
        self.drop_reaction = bool(self.tamper.get('drop_tie_reaction', False))
        self.tie_boost = float(self.tamper.get('tie_boost', 1.0))
        self.constant_weighting = bool(
            self.tamper.get('constant_weighting', False))
        self.release_bone_ties_at = release_bone_ties_at
        self.pin_guide_z = bool(pin_guide_z)
        spec = build_shape(shape, real)
        self.rest = spec['vertices'].copy()
        self.tris = spec['triangles']
        self.n_vertices = int(self.rest.shape[0])
        self.vertex_mass = spec['tissue_mass'] / self.n_vertices
        mem0 = pm.Membrane(self.rest, self.tris, 'm11_%s_rest' % shape)
        self.report = mem0.require_closed()
        self.volume_rest = float(self.report['signed_volume_m3'])
        # declared axis: principal direction of the rest geometry; for the
        # limb it is verified to run bottom(palm-side) -> top(shoulder-side)
        ctr = self.rest.mean(axis=0)
        cov = np.cov((self.rest - ctr).T)
        eigval, vec = np.linalg.eigh(cov)
        self.axis = vec[:, int(np.argmax(eigval))]
        if 'axis_top' in spec:
            if float(np.dot(self.axis, spec['axis_top'] -
                            spec['axis_bottom'])) < 0.0:
                self.axis = -self.axis
        proj = self.rest @ self.axis
        self.top_idx = int(np.argmax(proj))
        self.bottom_idx = int(np.argmin(proj))
        # guide ring: top pole + its 1-ring, x,y pinned (z FREE by law;
        # pin_guide_z is the FB4 hidden-support tamper ONLY)
        pairs, edge_index = _unique_edges(self.tris)
        self.edges = pairs
        nbrs = {}
        for a, b in pairs.tolist():
            nbrs.setdefault(a, set()).add(b)
            nbrs.setdefault(b, set()).add(a)
        guide = {self.top_idx} | set(nbrs[self.top_idx])
        self.guide_idx = np.array(sorted(guide), dtype=np.int64)
        # declared load-introduction rings (Amendment A1: point tie forces
        # at a single pole vertex punctured the shell; loads enter through
        # declared vertex patches, recorded in the state document)
        bottom_ring = {self.bottom_idx} | set(nbrs[self.bottom_idx])
        self.bottom_ring = np.array(sorted(bottom_ring), dtype=np.int64)
        self.guide_xy = self.rest[self.guide_idx, :2].copy()
        self.guide_z = self.rest[self.guide_idx, 2].copy()
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
        # belt chord family along the declared axis (M10 chord law form)
        zz = (proj - proj.min()) / max(1e-12, proj.max() - proj.min())
        nbrs2 = dict(nbrs)
        chord_set = set()
        for v_i, ns in nbrs2.items():
            if zz[v_i] > CHORD_CAP_Z:
                continue
            for t_v in ns:
                for w_v in nbrs2[t_v]:
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
        # point masses
        self.foot_mass = spec['foot_mass']
        self.load_mass = spec['load_mass']
        # placement: bottom pole at 2*R_FOOT above the ground plane z=0;
        # the foot contact sphere (radius R_FOOT) hangs below the bottom
        # pole on a declared R_FOOT-rest link, initially just touching
        lift = 2.0 * R_FOOT - float(self.rest[self.bottom_idx, 2])
        self.rest = self.rest + np.array([0.0, 0.0, lift])
        self.guide_xy = self.rest[self.guide_idx, :2].copy()
        self.guide_z = self.rest[self.guide_idx, 2].copy()
        self.x = self.rest.copy()
        self.v = np.zeros_like(self.x)
        self.foot_x = self.rest[self.bottom_idx] - np.array(
            [0.0, 0.0, R_FOOT])
        self.foot_v = np.zeros(3)
        self.load_x = self.x[self.top_idx] + np.array(
            [0.0, 0.0, -spec['load_tie_rest'] - 2.0 * R_FOOT])
        self.load_v = np.zeros(3)
        # ties (all M05-form; bound explicitly, never auto-bonded)
        self.load_tie = TieElement('load:top_pole', K_TIE,
                                   spec['load_tie_rest'])
        self.load_tie.bind(0)
        self.foot_tie = TieElement('foot:bottom_pole', K_TIE, R_FOOT)
        self.foot_tie.bind(0)
        # foot link: a declared BILATERAL strut (distance spring, rest
        # R_FOOT). Stance columns PUSH; M05's tension-only law governs the
        # tendon ties (load, bones); the strut is this card's declared
        # compression composition (Amendment A1).
        self.foot_strut_k = K_TIE
        self.foot_strut_rest = R_FOOT
        self.last_strut_force = 0.0
        self.bone_ties = []
        self.bone_state = {}
        self.site_bindings = []
        for bone in ('humerus', 'ulna', 'radius'):
            info = spec['bones'].get(bone)
            if not info:
                continue
            site_recs = [s for s in (spec['sites'] or [])
                         if s.get('owner_body') == bone]
            require(site_recs, 'real_sites_missing:' + bone)
            src = info['world_vertices_m']
            bone_x = src.mean(axis=0) + np.array([0.0, 0.0, lift])
            anchors = []
            for rec in site_recs:
                vid = self._bind_site_vertex(info, rec, lift)
                anchors.append({'record_id': rec['record_id'],
                                'declared_name': rec['declared_name'],
                                'role': rec['role'], 'vertex': int(vid)})
                self.site_bindings.append({
                    'record_id': rec['record_id'],
                    'declared_name': rec['declared_name'],
                    'owner_body': rec['owner_body'],
                    'role': rec['role'],
                    'location_m': [float(c) for c in rec['location_m']],
                    'bound_vertex': int(vid)})
            self.bone_state[bone] = {
                'mass_kg': info['mass_kg'], 'x': bone_x, 'v': np.zeros(3),
                'anchors': anchors}
            for a in anchors:
                tie = TieElement('bone:%s:%s' % (bone, a['record_id']),
                                 K_TIE_BONE, 0.0)
                tie.bind(0)
                self.bone_ties.append((bone, tie, a['vertex']))
        self.source = pm.PressureSource(
            SOURCE_ID, P_EXT_PA, P_EXT_PA, MAX_DELTA_P_PA,
            MAX_FLOW_M3_PER_S, SOURCE_PROVENANCE)
        self.snapshot_ticks = sorted(int(t) for t in snapshot_ticks)
        self.snapshots = []
        self.tick_states = []
        self.traction_ratio_worst = 0.0
        self.max_dp_seen = 0.0
        self.max_flow_seen = 0.0
        self.max_speed_seen = 0.0
        self.position_drift_m = 0.0
        self.guide_fz_max = 0.0
        self.tie_law_dev_max = 0.0
        self.interface_dev_max = 0.0

    # -- helpers ----------------------------------------------------------
    def _bind_site_vertex(self, info, rec, lift):
        """Bind an A06 site to the nearest tissue rest vertex.

        Frame plumbing (Amendment A1): the site location is in the osim
        OWNER-BODY frame; it is mapped through the blob's own admitted
        world_from_local transform (recovered and asserted to <=1e-12 in
        load_real_data), then to the nearest rest vertex of the tissue
        assembly. The binding never edits the site record."""
        loc = np.asarray(rec['location_m'], dtype=np.float64)
        src_body = info['vertices_m']
        src_world = info['world_vertices_m']
        cb = src_body.mean(axis=0)
        cw = src_world.mean(axis=0)
        h = (src_world - cw).T @ (src_body - cb)
        u, _s, vt = np.linalg.svd(h)
        d = np.linalg.det(u @ vt)
        r = u @ np.diag([1.0, 1.0, d]) @ vt
        t = cw - r @ cb
        site_world = r @ loc + t + np.array([0.0, 0.0, lift])
        d2 = ((self.rest - site_world) ** 2).sum(axis=1)
        return int(np.argmin(d2))

    def _membrane(self):
        return pm.Membrane(self.x, self.tris, 'm11_membrane_current')

    def _anchor_point(self):
        return self.x[self.top_idx]

    def _foot_anchor_point(self):
        return self.x[self.bottom_idx]

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
        for tie in [self.load_tie, self.foot_tie]:
            if tie.last_extension > 0.0:
                u_ties += 0.5 * tie.k * tie.last_extension ** 2
        for _bone, tie, _vid in self.bone_ties:
            if tie.last_extension > 0.0:
                u_ties += 0.5 * tie.k * tie.last_extension ** 2
        e_grav = self.load_mass * GRAV * float(self.load_x[2]) + \
            self.foot_mass * GRAV * float(self.foot_x[2])
        for st in self.bone_state.values():
            e_grav += st['mass_kg'] * GRAV * float(st['x'][2])
        pen = max(0.0, R_FOOT - float(self.foot_x[2]))
        u_contact = 0.5 * K_CONTACT * pen * pen
        e_kin = float(0.5 * self.vertex_mass * (self.v * self.v).sum()) + \
            0.5 * self.load_mass * float(self.load_v @ self.load_v) + \
            0.5 * self.foot_mass * float(self.foot_v @ self.foot_v)
        for st in self.bone_state.values():
            e_kin += 0.5 * st['mass_kg'] * float(st['v'] @ st['v'])
        return e_kin, u_edge, u_ties, e_grav, u_contact

    def _state_digest(self, tick):
        payload = {
            'tick': int(tick),
            'x': [[float(c) for c in row] for row in self.x],
            'x_load': [float(c) for c in self.load_x],
            'x_foot': [float(c) for c in self.foot_x],
            'x_bones': {b: [float(c) for c in st['x']]
                        for b, st in self.bone_state.items()},
            'energies': [float(e) for e in self._energies()],
        }
        return digest(payload)

    # -- the ONE dynamics path --------------------------------------------
    def run(self):
        rows = []
        w_press_cum = 0.0
        q_cum = 0.0
        settle_start = self.ticks - SETTLE_WINDOW
        x_before_tick = self.x.copy()
        for tick in range(self.ticks):
            dp = float(self.schedule_fn(tick))
            self.max_dp_seen = max(self.max_dp_seen, abs(dp))
            source = self.source.with_delta_p(dp)   # enforces M03 limits
            if (self.release_bone_ties_at is not None
                    and tick == self.release_bone_ties_at):
                for _bone, tie, _vid in self.bone_ties:
                    tie.release(tick)
            tick_w_vol = 0.0
            tick_q = 0.0
            e0 = self._energies()
            guide_fz_tick = 0.0
            for sub in range(N_SUB):
                x_before = self.x.copy()
                mem = self._membrane()
                v_start = mem.signed_volume()
                # 1. damping (measured dissipation of this step)
                dmf = max(0.0, 1.0 - C_V * HS)
                ldf = max(0.0, 1.0 - C_LOAD * HS)
                fdf = max(0.0, 1.0 - C_FOOT * HS)
                bdf = max(0.0, 1.0 - C_BONE * HS)
                q_damp = 0.5 * self.vertex_mass * \
                    float((self.v * self.v).sum()) * (1.0 - dmf * dmf) + \
                    0.5 * self.load_mass * \
                    float((self.load_v * self.load_v).sum()) * \
                    (1.0 - ldf * ldf) + \
                    0.5 * self.foot_mass * \
                    float((self.foot_v * self.foot_v).sum()) * \
                    (1.0 - fdf * fdf) + \
                    sum(0.5 * st['mass_kg'] * float(st['v'] @ st['v']) *
                        (1.0 - bdf * bdf) for st in
                        self.bone_state.values())
                self.v = self.v * dmf
                self.load_v = self.load_v * ldf
                self.foot_v = self.foot_v * fdf
                for st in self.bone_state.values():
                    st['v'] = st['v'] * bdf
                tick_q += q_damp
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
                # 3a. load point mass: gravity + tie to the top pole
                f_grav_load = np.array([0.0, 0.0, -self.load_mass * GRAV])
                f_tie = self.load_tie.force_on_body(self._anchor_point(),
                                                    self.load_x)
                f_tie_applied = f_tie * self.tie_boost
                # tie-force-law audit datum: the M05-law tie force at this
                # state (bitwise zero deviation expected on clean runs)
                dev = float(np.max(np.abs(f_tie_applied - f_tie)))
                self.tie_law_dev_max = max(self.tie_law_dev_max, dev)
                f_load_total = f_grav_load + f_tie_applied
                reaction = -f_tie
                interface_applied = np.zeros(3) if self.drop_reaction \
                    else reaction
                self.interface_dev_max = max(
                    self.interface_dev_max,
                    float(np.max(np.abs(interface_applied - reaction))))
                dx_load = (self.load_v +
                           f_load_total / self.load_mass * HS) * HS
                self.load_v = self.load_v + \
                    f_load_total / self.load_mass * HS
                self.load_x = self.load_x + dx_load
                # 3b. foot point mass: gravity + bilateral strut to the
                # bottom pole + penalty ground contact
                f_grav_foot = np.array([0.0, 0.0, -self.foot_mass * GRAV])
                d_foot = self.foot_x - self._foot_anchor_point()
                dist_foot = float(np.linalg.norm(d_foot))
                require(dist_foot > 1e-12, 'strut_degenerate')
                ext_foot = dist_foot - self.foot_strut_rest
                f_strut = (-self.foot_strut_k * ext_foot /
                           dist_foot) * d_foot   # bilateral: push AND pull
                self.last_strut_force = float(-f_strut[2])
                strut_reaction = -f_strut      # on the bottom pole
                pen = max(0.0, R_FOOT - float(self.foot_x[2]))
                f_contact = np.array([0.0, 0.0, K_CONTACT * pen])
                f_foot_total = f_grav_foot + f_strut + f_contact
                self.foot_v = self.foot_v + \
                    f_foot_total / self.foot_mass * HS
                self.foot_x = self.foot_x + self.foot_v * HS
                # 3c. bones: gravity + ties to anchor vertices
                patch_force = np.zeros_like(self.x)
                for bone, tie, vid in self.bone_ties:
                    st = self.bone_state[bone]
                    fb = tie.force_on_body(self.x[vid], st['x'])
                    f_b = np.array([0.0, 0.0, -st['mass_kg'] * GRAV]) + fb
                    st['v'] = st['v'] + f_b / st['mass_kg'] * HS
                    st['x'] = st['x'] + st['v'] * HS
                    if not self.drop_reaction:
                        patch_force[vid] -= fb
                if self.pose_writer:
                    self.foot_x = self.x[self.bottom_idx] + np.array(
                        [0.0, 0.0, 0.02])
                    self.foot_v = np.zeros(3)
                # 4. semi-implicit membrane step (reactions enter through
                # the declared rings)
                if not self.drop_reaction:
                    patch_force[self.guide_idx] += \
                        reaction / len(self.guide_idx)
                patch_force[self.bottom_ring] += \
                    strut_reaction / len(self.bottom_ring)
                self.v = self.v + (loads + patch_force) / \
                    self.vertex_mass * HS
                self.x = self.x + self.v * HS
                # 5. batched XPBD edge+chord projection (under-relaxed),
                #    canonical post-projection velocity update
                w = np.ones(self.n_vertices) / self.vertex_mass
                w[self.guide_idx] = 0.0
                e_i = np.concatenate([self.edges[:, 0], self.chords[:, 0]])
                e_j = np.concatenate([self.edges[:, 1], self.chords[:, 1]])
                L0_all = np.concatenate([self.l0, self.chord_l0])
                alpha_all = np.concatenate([self.alpha, self.chord_alpha])
                # tension-only chords: build the bilateral set but zero the
                # correction of compressed chords after the measure
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
                    # guide: hard lateral pin (x,y), z FREE by law
                    self.x[self.guide_idx, 0] = self.guide_xy[:, 0]
                    self.x[self.guide_idx, 1] = self.guide_xy[:, 1]
                    if self.pin_guide_z:
                        self.x[self.guide_idx, 2] = self.guide_z
                self.v = (self.x - x_before) / HS
                self.v[self.guide_idx] = 0.0
                # 6. guide vertical pin-force audit datum
                if self.pin_guide_z:
                    hold = self.guide_z
                    drift = hold - self.x[self.guide_idx, 2]
                    f_pin = self.vertex_mass * drift / (HS * HS)
                    guide_fz_tick += float(np.sum(f_pin))
                # 7. volume/work accumulation
                mem_after = self._membrane()
                v_end = mem_after.signed_volume()
                tick_w_vol += source.delta_p * (v_end - v_start)
            # per-tick ledger
            e1 = self._energies()
            total0 = sum(e0)
            total1 = sum(e1)
            r_tick = (total1 - total0) + tick_q - tick_w_vol
            turnover = abs(tick_w_vol) + abs(tick_q) + abs(total1 - total0)
            w_press_cum += tick_w_vol
            q_cum += tick_q
            v_free = self.v.copy()
            v_free[self.guide_idx] = 0.0
            speed = max(float(np.max(np.linalg.norm(v_free, axis=1))),
                        float(np.linalg.norm(self.load_v)),
                        float(np.linalg.norm(self.foot_v)),
                        max(float(np.linalg.norm(st['v']))
                            for st in self.bone_state.values()) if
                        self.bone_state else 0.0)
            if tick >= settle_start:
                self.max_speed_seen = max(self.max_speed_seen, speed)
                drift = float(np.max(np.abs(self.x - x_before_tick)))
                self.position_drift_m = max(self.position_drift_m, drift)
            self.guide_fz_max = max(self.guide_fz_max, abs(guide_fz_tick))
            pen = max(0.0, R_FOOT - float(self.foot_x[2]))
            row = {
                'tick': tick,
                'phase': phase_of(tick),
                'delta_p_pa': dp,
                'volume_m3': float(v_end),
                'top_z_m': float(self.x[self.top_idx, 2]),
                'bottom_z_m': float(self.x[self.bottom_idx, 2]),
                'pole_gap_m': self.pole_gap(),
                'foot_z_m': float(self.foot_x[2]),
                'load_z_m': float(self.load_x[2]),
                'contact_force_n': K_CONTACT * pen,
                'contact_penetration_m': pen,
                'load_tie_tension_n': float(self.load_tie.last_tension),
                'strut_force_n': float(self.last_strut_force),
                'bone_tie_tensions_n': {
                    b: float(tie.last_tension)
                    for b, tie, _v in self.bone_ties},
                'bone_z_m': {b: float(st['x'][2])
                             for b, st in self.bone_state.items()},
                'guide_fz_n': guide_fz_tick,
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
            rows.append(row)
            if (tick + 1) in self.snapshot_ticks:
                self.snapshots.append({
                    'tick': tick + 1, 'x': self.x.copy(),
                    'foot': self.foot_x.copy(), 'load': self.load_x.copy(),
                    'bones': {b: st['x'].copy()
                              for b, st in self.bone_state.items()}})
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
        sel = [st for st in self.tick_states_or_rows()
               if lo <= st['tick'] < hi]
        require(sel, 'window_empty')
        return float(np.mean([st[key] for st in sel]))

    def tick_states_or_rows(self):
        return self.rows
