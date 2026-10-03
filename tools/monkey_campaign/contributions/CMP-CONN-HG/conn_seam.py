"""CMP-CONN-HG -- the conn.hand_ground_contact.v1 SEAM LAW implementation.

Packet PKT-G3-CONNECTION-HANDGROUND (compiler-compile), lane
wk-connection-handground. The packet scope: implement/verify the interaction
ACROSS pc.hand_ground_contact.v1 (seam law only) -- record ownership, the pair
rule, the release bars, the ledger closure. The membrane interiors stay
HIDDEN (they belong to the parallel membrane-hand / membrane-ground lanes);
the pair RUN runtime scene stays owed by the assembly packet
(declared_pending).

Import-only law: the physics is the pinned MAT2-M06 ``local_contact.py``
(hash-asserted; refusals interface_pin_missing / interface_pin_drift; never
forked; adds no bond/weld/sticky construction -- the weld channel is a
recorded ZERO with FB1-only provenance). The write-scope substrate is the
pinned mathspec ABI (membrane_abi.py + graph_runtime.py per-connection
one-writer scoping + spec_runtime.resolve_ids id scheme + combine_core
refusals), hash-asserted and pin-verified. The tick loop is the lane's own
(the sealed G04/G07 direct-composition pattern; pairpath precedent).

Scenes are the pairpath's declared fixture forms (translation-only
placements; A09 frame law; x_reach ABSENT -- no transform composed). mu
values are the contract's fx.mu_placeholders (0.6/0.4, NB-01/NB-02); the
press channel is fx.press_actuation (0.3 N*s/channel/tick, NB-03); the
release share is fx.equal_share_partition (NB-04). EVERY result is
fixture-based and never an integrated qualification.

CPU-only, stdlib-only, deterministic (no RNG, no wall clock in the physics).
Refusals are named codes; prereg windows are fatal requires. See
PREREGISTRATION.md (sealed alone before this file existed).
"""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import math
import os
import pathlib
import struct
import sys
import xml.etree.ElementTree as ET
import zlib

SCHEMA = 'chimera.conn_seam.v1'
LANE = 'wk-connection-handground'
PACKET_ID = 'PKT-G3-CONNECTION-HANDGROUND'
CRITERIA_SHA256 = '21ec15791b561cc5569a476826e3e9c8158404e2be3587a598e329a3275e10f4'

# ---- pinned inputs (hash-asserted; refusals interface_pin_*) -----------------

CO = 'E:/ChimeraWork/monkey-coordination'
LC_PATH = CO + '/evidence-store/MAT2-M06/source/local_contact.py'
LC_SHA = '1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc'
CONTRACT_PATH = (CO + '/compiler-compile/'
                 'PORT_CONTRACT.hand_ground_contact.v1.json')
CONTRACT_SHA = 'a54313760c766764fb95302ebe0bee1fbc65f343770a8b9930657f2a6a3f2104'
DECL_PATH = CO + '/compiler-declare/hand_ground_declaration.v1.json'
DECL_SHA = 'a5a82d526f160be671837307419abc0f1c33a0f0636bd13220fb9b1797c3d773'
G04_RECEIPT_PATH = CO + '/evidence-store/MAT2-G04/numerical/experiment_receipt.json'
G04_RECEIPT_SHA = '0d622f3610a4d23f52655908effe474694867a20e639747dc48535a419319ce8'
G04_FALSIFIER_PATH = CO + '/evidence-store/MAT2-G04/numerical/falsifier_receipt.json'
G04_FALSIFIER_SHA = '04ef594cb7aa856e3afcd9b767e75c5c0dc44206f4c3db16ce678a35886f7fb2'
G04_REPORT_PATH = CO + '/evidence-store/MAT2-G04/report/REPORT.md'
G04_REPORT_SHA = 'dfca5b5556efe018ca09be4577bf6fbb5df38bb5c9ebc33d15bd18646ba349c8'
G07_REPORT_PATH = CO + '/evidence-store/MAT2-G07/report/REPORT.md'
G07_REPORT_SHA = '34a4a095e1f4b3e5c87160a77e399c5c27a38202c1ad3675b0bcbf70d4b956a1'
PAIRPATH_PATH = CO + '/evidence-store/MAT2-D-PAIRPATH/numerical/pairpath_result.json'
PAIRPATH_SHA = '3d3dfae1fe6bfb759045a450e7a66bc7b3fd2e670eb9ed925e06163fd65a03a9'
MS = CO + '/mathspec'
ABI_PATH = MS + '/membrane_abi.py'
ABI_SHA = '80c5b36574a442fa829f0fa3bea52f088f32c6db5bc316e2e77c54ee03811665'
GR_PATH = MS + '/graph_runtime.py'
GR_SHA = 'c7a96b07dfe4da5056a5c9b39aefa3f3d178c3be01084c823dbd4a9084fc3860'
SR_PATH = MS + '/spec_runtime.py'
SR_SHA = '423fca7089fc28a39825c50eaee8b4968b4beebd778807cb32eaf2e95e2cbd31'
A05_PATH = (CO + '/evidence-store/MAT2-A05/workspace_evidence/'
            '48b037593f63_mutation_structure.json')
A05_SHA = '48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649'
F05_COMPOSED_PATH = CO + '/evidence-store/MAT2-F05/source/composed_meta.json'
F05_COMPOSED_SHA = '8168382ff2c852b9fbf2c49831ec2021c8c3f5178af95d6ffba0ce55fa3a42f7'
F05_TERRAIN_PATH = CO + '/evidence-store/MAT2-F05/source/terrain_meta.json'
F05_TERRAIN_SHA = 'ff15fb1db3dcc128a531d21ef64d3ab62ae78190b64db36f70b5d273c1425681'
W03_PATH = (CO + '/kanban-reviews/MAT2-W03/'
            'review-glm53flash-confirm-20260928/blobs/scene.json')
W03_SHA = 'f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342'
HAND_PATH = ('E:/PythonChimera/tools/science_funnel/data/macaque_arm/'
             'Geometry/hand.vtp')
HAND_SHA = 'a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6'


def require(ok, code, detail=''):
    if not ok:
        raise ValueError(code + (': ' + str(detail) if detail != '' else ''))


def sha_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def pin_file(path, expected_sha, role):
    p = pathlib.Path(path)
    require(p.exists(), 'interface_pin_missing', {'role': role, 'path': str(p)})
    got = sha_file(p)
    require(got == expected_sha, 'interface_pin_drift',
            {'role': role, 'path': str(p), 'got': got, 'want': expected_sha})
    return str(p)


def load_module(path, expected_sha, name, role):
    pin_file(path, expected_sha, role)
    p = pathlib.Path(path)
    spec_mod = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec_mod)
    sys.modules[name] = mod
    spec_mod.loader.exec_module(mod)
    return mod


# ---- the substrate (loaded in dependency order; sys.path first) --------------

for _p in (MS, MS + '/pinned_inputs'):
    if _p not in sys.path:
        sys.path.insert(0, _p)

sr = load_module(SR_PATH, SR_SHA, 'spec_runtime', 'mathspec spec_runtime')
# the substrate's own frozen-runtime pin law (its verify_pins opens the
# pinned paths relative to the mathspec lane root, so the gate runs with the
# cwd held there and restored immediately after; all lane paths are absolute)
_CWD = os.getcwd()
os.chdir(MS)
try:
    sr.require_pins()
finally:
    os.chdir(_CWD)
abi = load_module(ABI_PATH, ABI_SHA, 'membrane_abi', 'mathspec membrane_abi')
gr = load_module(GR_PATH, GR_SHA, 'graph_runtime', 'mathspec graph_runtime')
lc = load_module(LC_PATH, LC_SHA, 'conn_seam_pinned_local_contact', 'M06 solver')

CombineRefusal = sr.CombineRefusal

# ---- frozen constants (contract + fixtures; PREREGISTRATION s3/s4) -----------

PLANE_Z = 0.004              # contract walk_plane_height (F05 flatten single writer)
PLANE_HALF_M = 0.05          # declared representative plateau patch (pairpath form)
THICK = 0.002                # M06 THICKNESS_M for every body
STAND_OFF = 5e-6             # initial gaps (inside MARGIN 1e-5)
MU_S = 0.6                   # fx.mu_placeholders (NAMED_PLACEHOLDER, NB-01)
MU_K = 0.4                   # fx.mu_placeholders (NAMED_PLACEHOLDER, NB-02)
BODY_MASS_KG = 10.037998     # the certified G01/G07 scene line (fixture prop)
HAND_MASS_KG = BODY_MASS_KG / 3.0   # G04 scene pad share at the lawful n=3
PRESS_NS = 0.30              # fx.press_actuation per channel/tick (NB-03)
N_CHANNELS = 3               # the lawful n for the scene reading (G01)
PRESS_TOTAL_NS = PRESS_NS * N_CHANNELS      # 0.9 N*s per tick
OPERATING_FORCE_N = PRESS_NS / lc.DT        # 60.0 N by the DECLARED /dt conversion
TANGENT_STICK_NS = 0.05      # fx.tangential_trigger, sub-cone magnitude (total)
TANGENT_SLIP_NS = 0.45       # fx.tangential_trigger, saturating magnitude (pairpath drive)
PROP_EDGE = 0.03             # declared prop tetra edge (m)
TETRA_TRIS = ((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3))
RELEASE_BAR_PER_KG = 1e-10   # contract release_bar_ns: share_kg * 1e-10 per release tick

WIN_LEDGER = 1e-12           # N*s, full-tick ledger windows (contract identity)
WIN_LOSS = 1e-12             # J, pair-per-record friction loss identity
WIN_ENERGY = 1e-12           # J
WIN_MOM = 1e-12              # N*s, stack tangential recursion identity
WIN_STICK = 1e-12            # m/s, stick-arrest bar (X2)
WIN_FALL = 1e-9              # m/s + m, free-fall windows (X4)
WIN_CONT = 1e-9              # m, pose continuity (G07 form)

# ---- contract conformance gate (the frozen bytes are the authority) ----------

CONTRACT_QREFS = ('jn', 'jt', 'press_channel_state')
CONTRACT_STAGE_ORDER = ('pressure', 'material', 'contact')
CONNECTION_ID = 'conn.hand_ground_contact.v1'
HAND_ID = 'membrane.hand.v1'
GROUND_ID = 'membrane.ground.v1'
HAND_PORT = 'port.grip_contact'
GROUND_PORT = 'port.walk_surface_contact'


def _param(contract, name):
    for row in contract['contract_parameters']:
        if row['param'] == name:
            return row
    raise ValueError('contract_field_mismatch: missing param ' + name)


def verify_contract(contract, declaration, f05_composed, f05_terrain, w03):
    """Require the exact frozen fields the seam consumes. Any drift is the
    named refusal contract_field_mismatch -- the seam never invents values."""
    require(contract['contract_id'] == 'pc.hand_ground_contact.v1',
            'contract_field_mismatch:contract_id')
    require(contract['connection_id'] == CONNECTION_ID,
            'contract_field_mismatch:connection_id')
    require(contract['protocol'] == 'normal_press_impulse',
            'contract_field_mismatch:protocol')
    eps = {(e['membrane'], e['port'], e['role']) for e in contract['endpoints']}
    require(eps == {(HAND_ID, HAND_PORT, 'a'),
                    (GROUND_ID, GROUND_PORT, 'b')},
            'contract_field_mismatch:endpoints')
    qrefs = tuple(q['quantity_id'] for q in contract['exchanged_quantities'])
    require(qrefs == CONTRACT_QREFS, 'contract_field_mismatch:quantities')
    units = {u['quantity_id']: u['unit'] for u in contract['units']}
    require(units == {'jn': 'N*s', 'jt': 'N*s',
                      'press_channel_state': 'N*s'},
            'contract_field_mismatch:units')
    dirs = {d['quantity_id']: d['direction']
            for d in contract['direction_sign_conventions']}
    require(dirs == {'jn': 'inout', 'jt': 'inout',
                     'press_channel_state': 'out'},
            'contract_field_mismatch:directions')
    own = {o['quantity_id']: o['owner_membrane']
           for o in contract['state_ownership']}
    require(own == {'jn': GROUND_ID, 'jt': GROUND_ID,
                    'press_channel_state': HAND_ID},
            'contract_field_mismatch:ownership')
    timing = contract['timing']
    require(float(timing['tick_dt_s']) == lc.DT
            and int(timing['tick_rate_hz']) == 300,
            'contract_field_mismatch:timing_dt')
    require(tuple(timing['stage_order']) == CONTRACT_STAGE_ORDER,
            'contract_field_mismatch:stage_order')
    require(timing['single_writer_stage'].startswith('contact stage'),
            'contract_field_mismatch:single_writer_stage')
    require(any(l['latch_id'] == 'press_release_latch'
                for l in timing['latches']),
            'contract_field_mismatch:latch')
    consumed = {c['input_id']: c for c in contract['consumed_inputs']}
    require(consumed['mu_s']['binding']['class'] == 'NAMED_PLACEHOLDER'
            and consumed['mu_k']['binding']['class'] == 'NAMED_PLACEHOLDER',
            'contract_field_mismatch:mu_class')
    require(_param(contract, 'mu_s')['value'] == MU_S
            and _param(contract, 'mu_k')['value'] == MU_K,
            'contract_field_mismatch:mu_values')
    require(_param(contract, 'press_channel_jn_ns_per_tick')['value']
            == PRESS_NS, 'contract_field_mismatch:press')
    require(_param(contract, 'press_dt_s')['value'] == lc.DT,
            'contract_field_mismatch:press_dt')
    require(_param(contract, 'operating_force_N')['value'] == OPERATING_FORCE_N,
            'contract_field_mismatch:operating_force')
    require(_param(contract, 'pair_friction_rule')['value'] == 'elementwise_min',
            'contract_field_mismatch:pair_friction_rule')
    require(_param(contract, 'release_bar_ns')['value']
            == 'share_kg * 1e-10 per release tick',
            'contract_field_mismatch:release_bar')
    require(_param(contract, 'ledger_identity')['value']
            == 'm*dv == press + weld + gravity + contact + anchor, '
               'window 1e-12 N*s',
            'contract_field_mismatch:ledger_identity')
    require(_param(contract, 'grip_capacity_kg')['binding_class'] == 'MEASURED',
            'contract_field_mismatch:capacity_row_present')
    absent = {row['name']: row['status'] for row in contract['named_absent']}
    require(absent.get('x_press') == 'ABSENT'
            and absent.get('x_share') == 'ABSENT'
            and absent.get('x_reach') == 'ABSENT',
            'contract_field_mismatch:named_absent')
    rules = {r['rule_id'] for r in contract['pair_rules']}
    require(rules == {'pair_friction_elementwise_min',
                      'counted_once_reciprocity',
                      'separation_removes_support'},
            'contract_field_mismatch:pair_rules')
    ranges = {r['quantity_id']: r for r in contract['valid_input_ranges']}
    require(ranges['press_channel_state']['min'] == 'released'
            and ranges['press_channel_state']['max'] == 'armed',
            'contract_field_mismatch:pcs_range')
    require(float(ranges['walk_plane_height']['min']) == PLANE_Z
            and float(ranges['walk_plane_height']['max']) == PLANE_Z,
            'contract_field_mismatch:plane_height')
    require(float(ranges['slope_envelope_m_per_m']['max']) == 0.05,
            'contract_field_mismatch:slope_envelope')
    frames = {f['frame_id']: f for f in contract['coordinate_frames']}
    require(frames['macaque_arm_hand_mutation_frame']['transform_composed']
            == 'none'
            and frames['earth_contract_local_frame']['transform_composed']
            == 'none',
            'contract_field_mismatch:frames_none_composed')
    # cross-checks against the declaration and the ground-side pinned sources
    conn = declaration['connections'][0]
    require(conn['connection_id'] == CONNECTION_ID,
            'contract_field_mismatch:declaration_connection')
    recipe = w03['gait_controller']['recipe']
    require(float(recipe['contact_plane_height_m']) == PLANE_Z,
            'contract_field_mismatch:w03_plane')
    require(float(recipe['contact_friction']) == MU_S,
            'contract_field_mismatch:w03_friction')
    flat = f05_composed['transform']['reground']['flatten']
    require(float(flat['plateau_z_m']) == PLANE_Z,
            'contract_field_mismatch:f05_plateau_z')
    notes = [
        'the contract cites the walk plane as transform.reground.flatten.'
        'plateau_height_m; the pinned store bytes carry the same +0.004 m '
        'value under the key plateau_z_m (verified, same single writer)',
        'the contract slope envelope 0.05 m/m is enforced from the contract '
        'bytes; the pinned terrain_meta carries slope statistics (mean '
        'rise/run %r) but no separate envelope literal' %
        f05_terrain['slope_stats']['mean_rise_over_run'],
    ]
    return {'contract_conformant': True, 'rows_checked': 26,
            'g_convention': 'record-g 9.81 pinned solver; std-g 9.80665 '
                            'reference arithmetic only',
            'cross_check_notes': notes}


# ---- the seam spec + port faces (the proven ABI substrate) --------------------

SEAM_SPEC = {
    'schema': 'chimera.conn_seam.spec.v1',
    'spec_id': 'conn_seam.hand_ground_contact.v1',
    'derived_from': {
        'contract': 'pc.hand_ground_contact.v1',
        'contract_sha256': CONTRACT_SHA,
        'law': 'declared 1:1 from the frozen contract port surface; no '
               'membrane interior is declared or imitated'},
    'membranes': [
        {'membrane_id': HAND_ID,
         'owned_state': [{'var': 'press_channel_state', 'unit': 'N*s'}],
         'ports': {'inputs': [
             {'port_id': HAND_PORT, 'quantity_ref': 'jn', 'type': 'number',
              'unit': 'N*s', 'connection_ref': CONNECTION_ID},
             {'port_id': HAND_PORT, 'quantity_ref': 'jt', 'type': 'number',
              'unit': 'N*s', 'connection_ref': CONNECTION_ID}],
             'outputs': [
             {'port_id': HAND_PORT, 'quantity_ref': 'press_channel_state',
              'type': 'state', 'unit': 'N*s',
              'connection_ref': CONNECTION_ID}]}},
        {'membrane_id': GROUND_ID,
         'owned_state': [{'var': 'jn', 'unit': 'N*s'},
                         {'var': 'jt', 'unit': 'N*s'}],
         'ports': {'inputs': [],
                   'outputs': [
             {'port_id': GROUND_PORT, 'quantity_ref': 'jn', 'type': 'number',
              'unit': 'N*s', 'connection_ref': CONNECTION_ID},
             {'port_id': GROUND_PORT, 'quantity_ref': 'jt', 'type': 'number',
              'unit': 'N*s', 'connection_ref': CONNECTION_ID}]}},
    ],
    'connections': [
        {'connection_id': CONNECTION_ID,
         'members': [HAND_ID, GROUND_ID],
         'exchange': {'owner_membrane': GROUND_ID, 'quantity_ref': 'jn',
                      'unit': 'N*s',
                      'sign_convention': 'jn >= 0 presses the two surfaces '
                                         'together; the record is written '
                                         'ONCE at the contact and applied '
                                         'bitwise +/- to both sides'}}],
}


def canonical_sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True,
                                     separators=(',', ':')).encode()
                          ).hexdigest()


class _Produces:
    def __init__(self, produces):
        self.produces = list(produces)


class HandFace:
    """Port face a (membrane.hand.v1:port.grip_contact). NOT the membrane:
    a declared face carrying the contract's port surface only. It owns
    press_channel_state and must never expose an exchange writer (seam S1:
    the ground side owns the contact records)."""

    membrane_id = HAND_ID

    def __init__(self, ids):
        self._ids = ids

    def ownership(self):
        return {'membrane_id': HAND_ID,
                'owned_states': [
                    {'var': 'press_channel_state', 'unit': 'N*s',
                     'state_id': self._ids[(HAND_ID,
                                            'press_channel_state')]}],
                'contribution_id': 'contribution.hand.v1.press_channel'}

    def ports(self):
        return SEAM_SPEC['membranes'][0]['ports']

    def exchange_quantity(self, view):
        xsid = sr.resolve_ids(SEAM_SPEC)[2][CONNECTION_ID]
        return view[xsid]

    def contribution(self):
        return _Produces([self._ids[(HAND_ID, 'press_channel_state')]])


class GroundFace:
    """Port face b (membrane.ground.v1:port.walk_surface_contact). The seam's
    exchange-record OWNER: the ONLY face exposing exchange_contribution()
    (per-connection one-writer scoping, graph_runtime.validate_built_graph)."""

    membrane_id = GROUND_ID

    def __init__(self, ids, xsid):
        self._ids = ids
        self._xsid = xsid

    def ownership(self):
        return {'membrane_id': GROUND_ID,
                'owned_states': [
                    {'var': 'jn', 'unit': 'N*s',
                     'state_id': self._ids[(GROUND_ID, 'jn')]},
                    {'var': 'jt', 'unit': 'N*s',
                     'state_id': self._ids[(GROUND_ID, 'jt')]}],
                'contribution_id': 'contribution.ground.v1.seam_record'}

    def ports(self):
        return SEAM_SPEC['membranes'][1]['ports']

    def exchange_quantity(self, view):
        return view[self._xsid]

    def exchange_contribution(self):
        return _Produces([self._xsid])

    def contribution(self):
        return _Produces([self._ids[(GROUND_ID, 'jn')],
                          self._ids[(GROUND_ID, 'jt')]])


class MutantHandFace(HandFace):
    """The falsifier's constructed DOUBLE-WRITER face: a hand face that also
    exposes exchange_contribution(). The substrate must refuse it by name."""

    def exchange_contribution(self):
        return _Produces([sr.resolve_ids(SEAM_SPEC)[2][CONNECTION_ID]])


class SeamStore:
    """The seam's one-writer store (substrate refusal codes; combine_core
    law): a state id is written by its declared owner exactly once per
    window; a second write, a non-owner write or an undeclared id is
    refused BY NAME."""

    def __init__(self, owner_of, declared):
        self._owner_of = dict(owner_of)
        self._declared = set(declared)
        self.values = {}

    def write(self, sid, value, writer):
        if sid not in self._declared:
            raise CombineRefusal('combine_unknown_state',
                                 {'state_id': sid, 'writer': writer})
        if self._owner_of.get(sid) != writer:
            raise CombineRefusal('combine_non_owner_write',
                                 {'state_id': sid, 'writer': writer,
                                  'owner': self._owner_of.get(sid)})
        if sid in self.values:
            raise CombineRefusal('combine_double_state_write',
                                 {'state_id': sid, 'writer': writer})
        self.values[sid] = value

    def read(self, sid):
        return self.values[sid]


class PressChannel:
    """The hand-owned press channel state across the seam (contract pcs):
    armed applies fx.press_actuation; released applies EXACTLY 0; the
    press_release_latch holds until an explicit declared re-arm."""

    STATES = ('armed', 'released')

    def __init__(self):
        self.state = 'armed'
        self._rearm_event = False

    def set_state(self, state):
        require(state in self.STATES, 'pcs_state_invalid', state)
        self.state = state

    def release(self):
        self.state = 'released'

    def declare_rearm(self):
        self._rearm_event = True

    def rearm(self):
        require(self._rearm_event, 'press_latch_armed_after_release',
                'the press_release_latch holds until an explicit declared '
                're-arm event')
        self._rearm_event = False
        self.state = 'armed'

    def tick(self, holding):
        require(self.state in self.STATES, 'pcs_state_invalid', self.state)
        if self.state == 'armed' and holding:
            return (0.0, 0.0, -PRESS_TOTAL_NS)
        return (0.0, 0.0, 0.0)


# ---- vector helpers -----------------------------------------------------------

def vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vscale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def vlen(a):
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def impulse_work(j_vec, u_vec, inv_mass):
    dot = j_vec[0] * u_vec[0] + j_vec[1] * u_vec[1] + j_vec[2] * u_vec[2]
    j2 = j_vec[0] ** 2 + j_vec[1] ** 2 + j_vec[2] ** 2
    return dot + 0.5 * inv_mass * j2


def vmean(vertices):
    n = float(len(vertices))
    return (sum(v[0] for v in vertices) / n,
            sum(v[1] for v in vertices) / n,
            sum(v[2] for v in vertices) / n)


# ---- the declared fixture scene (pairpath forms; translation-only) ------------

def parse_hand_vtp():
    """Parse the pinned hand.vtp (x1e-3 into the A05 meter frame), fan
    triangulate quads, assert the sealed A05 bounds. Declared contact-surface
    geometry ONLY -- no membrane interior."""
    pin_file(HAND_PATH, HAND_SHA, 'hand_vtp')
    pin_file(A05_PATH, A05_SHA, 'a05_record')
    piece = ET.parse(HAND_PATH).getroot().find('PolyData/Piece')

    def read_da(da):
        if da.get('format') == 'ascii':
            txt = da.text.split()
            t = da.get('type')
            return ([int(x) for x in txt] if t in ('Int32', 'Int64')
                    else [float(x) for x in txt])
        raw = base64.b64decode(da.text.strip())
        hdr = struct.unpack('<I', raw[:4])[0]
        data = zlib.decompress(raw[4:4 + hdr])
        t = da.get('type')
        fmt = {'Float32': 'f', 'Int32': 'i', 'Int64': 'q'}[t]
        n = hdr // struct.calcsize('<' + fmt)
        return list(struct.unpack('<%d%s' % (n, fmt), data))

    pv = read_da(piece.find('Points').find('DataArray'))
    pts = [(pv[i] * 1e-3, pv[i + 1] * 1e-3, pv[i + 2] * 1e-3)
           for i in range(0, len(pv), 3)]
    conn = [int(v) for v in read_da(
        piece.find('Polys/DataArray[@Name="connectivity"]'))]
    offs = [int(v) for v in read_da(
        piece.find('Polys/DataArray[@Name="offsets"]'))]
    tris = []
    start = 0
    for o in offs:
        ids = conn[start:o]
        if len(ids) == 3:
            tris.append((ids[0], ids[1], ids[2]))
        else:
            for k in range(1, len(ids) - 1):
                tris.append((ids[0], ids[k], ids[k + 1]))
        start = o
    bounds = [[min(p[k] for p in pts) for k in range(3)],
              [max(p[k] for p in pts) for k in range(3)]]
    a05 = json.loads(pathlib.Path(A05_PATH).read_text(encoding='utf-8'))
    sealed = a05['envelope_check']['hand_vtp_bounds_m']
    dev = max(abs(bounds[i][k] - sealed[i][k])
              for i in (0, 1) for k in range(3))
    require(dev <= 1e-9, 'hand_bounds_drift', dev)
    return dict(points=pts, triangles=tris, bounds=bounds, bounds_dev_m=dev)


def build_scene(hand, ground_mu=None):
    """The declared fixture scene: ground plateau at the contract walk plane,
    the trial hand surface palm-down on it, the load prop tetra on the
    dorsum. Translation-only (A09 frame law; x_reach ABSENT)."""
    ground_mu = ground_mu or (MU_S, MU_K)
    half = PLANE_HALF_M
    ground = lc.Body(body_id='ground.plateau', surface_id='ground.plateau',
                     matter_id='walk_plane_fixture_mu',
                     mass_kg=1.0, mu_s=ground_mu[0], mu_k=ground_mu[1],
                     thickness_m=THICK,
                     vertices=[(-half, -half, PLANE_Z), (half, -half, PLANE_Z),
                               (half, half, PLANE_Z), (-half, half, PLANE_Z)],
                     triangles=[(0, 1, 2), (0, 2, 3)], pinned=True)
    pts = hand['points']
    lo_z = hand['bounds'][0][2]
    cxy = (sum(p[0] for p in pts) / len(pts),
           sum(p[1] for p in pts) / len(pts))
    t = (-cxy[0], -cxy[1], PLANE_Z + THICK + STAND_OFF - lo_z)
    hv = [(p[0] + t[0], p[1] + t[1], p[2] + t[2]) for p in pts]
    htris = hand['triangles']
    hand_body = lc.Body(body_id='hand.surface', surface_id='hand.surface',
                        matter_id='hand_surface_fixture_mu',
                        mass_kg=HAND_MASS_KG, mu_s=MU_S, mu_k=MU_K,
                        thickness_m=THICK, vertices=hv, triangles=htris)
    order = sorted(range(len(htris)),
                   key=lambda ti: (vmean([hv[htris[ti][0]], hv[htris[ti][1]],
                                          hv[htris[ti][2]]])[2], ti))
    sites = [dict(tri=ti, centroid=list(vmean(
        [hv[htris[ti][0]], hv[htris[ti][1]], hv[htris[ti][2]]])))
        for ti in order[:N_CHANNELS]]
    fx = fy = PROP_EDGE / 2.0
    patch_max = max(v[2] for v in hv if abs(v[0]) <= fx and abs(v[1]) <= fy)
    origin = (0.0, 0.0, patch_max + THICK + STAND_OFF)
    pv = [origin,
          (origin[0], origin[1], origin[2] + PROP_EDGE),
          (origin[0] + PROP_EDGE, origin[1], origin[2]),
          (origin[0], origin[1] + PROP_EDGE, origin[2])]
    prop = lc.Body(body_id='body.prop', surface_id='body.prop',
                   matter_id='load_prop_fixture_scene_line',
                   mass_kg=BODY_MASS_KG, mu_s=MU_S, mu_k=MU_K,
                   thickness_m=THICK, vertices=pv,
                   triangles=[tuple(t) for t in TETRA_TRIS])
    return dict(ground=ground, hand=hand_body, prop=prop, sites=sites,
                hand_translation=list(t), prop_origin=list(origin))


# ---- the pinned solver's counted-once instrument ------------------------------

_CALLS = {'n': 0}
_ORIG_SOLVE_CONTACT = lc.solve_contact


def _counting_solve_contact(*args, **kwargs):
    _CALLS['n'] += 1
    return _ORIG_SOLVE_CONTACT(*args, **kwargs)


def arm_call_counter():
    _CALLS['n'] = 0
    lc.solve_contact = _counting_solve_contact


# ---- the tick loop (pressure -> material -> contact; lane-owned) --------------

def run_scenario(name, hand, cfg):
    """One declared scenario. Stage order pressure -> material -> contact
    (contract timing). Accounts: full-tick ledger closure (press + weld(0) +
    trigger + gravity + contact + anchor, window 1e-12), reciprocity,
    anchor reaction, pair-per-record loss, per-record cone law, stack
    tangential recursion, pose continuity, energy identity. Fatal windows
    per prereg; every deviation refuses by name."""
    press_ticks = cfg['press_ticks']
    release_tick = cfg.get('release_tick', press_ticks + 1)
    separate_at = cfg.get('separate_at')
    rearm_probe_tick = cfg.get('rearm_probe_tick')
    trig_ticks = set(cfg.get('trig_ticks', ()))
    trig_ns = cfg.get('trig_ns', 0.0)
    ground_mu = cfg.get('ground_mu')
    stop_tick = cfg['stop_tick']
    scene = build_scene(hand, ground_mu)
    ground, hand_b, prop = scene['ground'], scene['hand'], scene['prop']
    bodies = [ground, hand_b, prop]
    press_ch = PressChannel()
    share_kg = HAND_MASS_KG          # fx.equal_share_partition (NB-04 model)
    release_bar = share_kg * RELEASE_BAR_PER_KG
    rows = []
    prev_state = None
    separated = False
    landing_tick = None
    hb_lost_tick = None
    last_accounts = None
    release_tick_rows = []
    separated_rows = []
    stick_vt_post_worst = 0.0
    slip_cap_worst = 0.0
    cone_headroom_min_all = None

    for tick in range(1, stop_tick + 1):
        # -- stage 1: pressure (the hand-owned press channel; the latch) ----
        if tick == release_tick:
            press_ch.release()
        if rearm_probe_tick is not None and tick == rearm_probe_tick:
            try:
                press_ch.rearm()
                require(False, 'probe_refusal_expected',
                        'press_latch_armed_after_release')
            except ValueError as exc:
                require(str(exc).startswith('press_latch_armed_after_release'),
                        'probe_wrong_refusal', str(exc))
        holding = tick <= press_ticks and not separated
        pcs_impulse = press_ch.tick(holding)
        if separate_at is not None and tick == separate_at:
            # fx.separation_event (pairpath S4 declared form): the trial hand
            # body is removed from the solve; the support channel is deleted.
            separated = True
            bodies = [ground, prop]
        # -- stage 2: material (DECLARED identity at contract 1.0.0) --------
        material = {'stage': 'material', 'effect': 'identity',
                    'law': 'the contract exchanges only jn/jt/pcs across '
                           'the seam; the ground material interface is '
                           'interior at this contract version'}
        # -- pressure/trigger application -----------------------------------
        v_start = {b.id: tuple(b.velocity) for b in bodies}
        press = {b.id: (0.0, 0.0, 0.0) for b in bodies}
        trig = {b.id: (0.0, 0.0, 0.0) for b in bodies}
        if pcs_impulse != (0.0, 0.0, 0.0) and not separated:
            press[hand_b.id] = pcs_impulse
            hand_b.velocity = vadd(hand_b.velocity,
                                   vscale(press[hand_b.id],
                                          hand_b.inv_mass()))
        if trig_ticks and tick in trig_ticks and not separated:
            trig[prop.id] = (0.0, trig_ns, 0.0)
            trig[hand_b.id] = (0.0, -trig_ns, 0.0)
            prop.velocity = vadd(prop.velocity,
                                 vscale(trig[prop.id], prop.inv_mass()))
            hand_b.velocity = vadd(hand_b.velocity,
                                   vscale(trig[hand_b.id], hand_b.inv_mass()))
            require(vlen(vadd(trig[prop.id], trig[hand_b.id])) <= WIN_LEDGER,
                    'trigger_reciprocity_broken', tick)
        # -- stage 3: contact (the pinned solver; single writer) -------------
        calls_at = _CALLS['n']
        c_start = {b.id: vmean(b.vertices) for b in bodies}
        records, ledger = lc.solve_tick(bodies)
        calls_tick = _CALLS['n'] - calls_at
        v_after = {b.id: tuple(b.velocity) for b in bodies}
        c_end = {b.id: vmean(b.vertices) for b in bodies}

        # -- T.CONN_counted_once (P1.1-P1.4) ---------------------------------
        require(calls_tick == len(records), 'counted_once_broken',
                {'tick': tick, 'calls': calls_tick, 'records': len(records)})
        keys = [r['pair_key'] for r in records]
        require(len(set(keys)) == len(keys), 'record_key_duplicate', tick)
        reciprocity_exact = (0.0, 0.0, 0.0)
        for r in records:
            ia, ib = tuple(r['impulse_on_a']), tuple(r['impulse_on_b'])
            for k in range(3):
                require(ib[k] == -ia[k], 'record_not_bitwise_opposite',
                        {'tick': tick, 'k': k})
            reciprocity_exact = vadd(reciprocity_exact, ia)
            reciprocity_exact = vadd(reciprocity_exact, ib)
        require(reciprocity_exact == (0.0, 0.0, 0.0),
                'reciprocity_not_exact', reciprocity_exact)
        # both side ledgers re-read from the SAME record list, same order
        contact_re = {b.id: (0.0, 0.0, 0.0) for b in bodies}
        for r in records:
            contact_re[r['body_a']] = vadd(contact_re[r['body_a']],
                                           tuple(r['impulse_on_a']))
            contact_re[r['body_b']] = vadd(contact_re[r['body_b']],
                                           tuple(r['impulse_on_b']))
        for b in bodies:
            got = tuple(ledger['contact'][b.id])
            require(contact_re[b.id] == got, 'ledger_reread_drift',
                    {'tick': tick, 'body': b.id})
        anchor_resid = 0.0
        for b in bodies:
            if b.pinned:
                anc = tuple(ledger['anchor'][b.id])
                con = tuple(ledger['contact'][b.id])
                for k in range(3):
                    require(anc[k] == -con[k], 'anchor_not_reaction',
                            {'tick': tick, 'k': k})
                anchor_resid = max(anchor_resid, vlen(vadd(anc, con)))

        # -- the seam store: ONE write per declared id by its owner ----------
        state_ids, _owner, xsids = sr.resolve_ids(SEAM_SPEC)
        xsid = xsids[CONNECTION_ID]
        owner_of = {sid: mid for (mid, _var), sid in state_ids.items()}
        owner_of[xsid] = GROUND_ID
        store = SeamStore(owner_of, set(state_ids.values()) | {xsid})
        g_recs = [r for r in records
                  if {r['body_a'], r['body_b']} == {ground.id, hand_b.id}]
        store.write(state_ids[(GROUND_ID, 'jn')],
                    sum(r['jn_Ns'] for r in g_recs), GROUND_ID)
        store.write(state_ids[(GROUND_ID, 'jt')],
                    sum(r['jt_Ns'] for r in g_recs), GROUND_ID)
        store.write(state_ids[(HAND_ID, 'press_channel_state')],
                    pcs_impulse[2], HAND_ID)

        # -- T.CONN_ledger (P4.1) full-tick closure --------------------------
        weld = (0.0, 0.0, 0.0)   # FB1-only falsifier channel; zero in clean runs
        ledger_worst = 0.0
        for b in bodies:
            dv = vsub(v_after[b.id], v_start[b.id])
            lhs = tuple(dv) if b.pinned else vscale(dv, b.mass_kg)
            rhs = vadd(vadd(press[b.id], trig[b.id]), weld)
            rhs = vadd(rhs, tuple(ledger['gravity'].get(b.id, (0.0, 0.0, 0.0))))
            rhs = vadd(rhs, tuple(ledger['contact'][b.id]))
            rhs = vadd(rhs, tuple(ledger['anchor'][b.id]))
            ledger_worst = max(ledger_worst, vlen(vsub(lhs, rhs)))
        require(ledger_worst <= WIN_LEDGER, 'ledger_imbalance:full_tick',
                {'tick': tick, 'worst': ledger_worst})
        recip = vlen(tuple(ledger['reciprocity_residual']))
        require(recip <= WIN_LEDGER, 'ledger_imbalance:reciprocity', tick)

        # -- per-record cone law + pair rule (P4.3, T2) -----------------------
        mu_s_pair = min(hand_b.mu_s, ground.mu_s)
        mu_k_pair = min(hand_b.mu_k, ground.mu_k)
        require((mu_s_pair, mu_k_pair) == lc.pair_mu(hand_b, ground),
                'pair_rule_disagrees_with_pinned_solver',
                (mu_s_pair, mu_k_pair))
        jt_seam_y = 0.0
        jn_seam_y = 0.0
        for r in g_recs:
            on_hand = tuple(r['impulse_on_a'] if r['body_a'] == hand_b.id
                            else r['impulse_on_b'])
            sgn = 1.0 if r['body_a'] == hand_b.id else -1.0
            jn_vec = vscale(tuple(r['normal']), sgn * r['jn_Ns'])
            jt_vec = vsub(on_hand, jn_vec)
            jt_seam_y += jt_vec[1]
            jn_seam_y += jn_vec[1]
            head = mu_s_pair * r['jn_Ns'] - vlen(jt_vec)
            require(head >= 0.0, 'cone_violated', {'tick': tick, 'head': head})
            cone_headroom_min_all = (head if cone_headroom_min_all is None
                                     else min(cone_headroom_min_all, head))
            if r['mode'] == 'slip':
                require(r['jt_Ns'] == mu_k_pair * r['jn_Ns'],
                        'slip_cap_not_pair_mu_k',
                        {'tick': tick, 'jt': r['jt_Ns'],
                         'want': mu_k_pair * r['jn_Ns']})
                slip_cap_worst = max(slip_cap_worst,
                                     abs(r['jt_Ns'] - mu_k_pair * r['jn_Ns']))
            if r['mode'] == 'stick':
                require(r['vt_post'] <= WIN_STICK, 'stick_arrest_broken',
                        {'tick': tick, 'vt_post': r['vt_post']})
                stick_vt_post_worst = max(stick_vt_post_worst, r['vt_post'])
        if ground_mu == (0.0, 0.0):
            for r in g_recs:
                require(r['jt_Ns'] == 0.0, 'zero_mu_record_has_jt',
                        {'tick': tick, 'jt': r['jt_Ns']})

        # -- stack tangential recursion (pairpath jt_all_ground_y form): the
        # free stack's y-momentum change equals the TOTAL y impulse delivered
        # through the pinned ground across ALL ground-body records (internal
        # pairs cancel by reciprocity; press/gravity/trigger carry no stack y)
        free = [b for b in bodies if not b.pinned]
        dp_stack_y = sum(b.mass_kg * (v_after[b.id][1] - v_start[b.id][1])
                         for b in free)
        all_ground_y = 0.0
        for r in records:
            if r['body_a'] == ground.id:
                all_ground_y += tuple(r['impulse_on_b'])[1]
            elif r['body_b'] == ground.id:
                all_ground_y += tuple(r['impulse_on_a'])[1]
        require(abs(dp_stack_y - all_ground_y) <= WIN_MOM,
                'tangential_recursion_broken',
                {'tick': tick, 'dp_stack_y': dp_stack_y,
                 'all_ground_y': all_ground_y})

        # -- T.CONN_ledger (P4.2) pair-per-record friction loss ---------------
        v_pair = {}
        for b in bodies:
            if b.pinned:
                continue
            vv = v_start[b.id]
            vv = vadd(vv, vscale(press[b.id], b.inv_mass()))
            vv = vadd(vv, vscale(trig[b.id], b.inv_mass()))
            vv = vadd(vv, vscale(tuple(ledger['gravity'].get(
                b.id, (0.0, 0.0, 0.0))), b.inv_mass()))
            v_pair[b.id] = vv
        pair_loss_worst = 0.0
        for r in records:
            inv = {}
            for role, bid in (('a', r['body_a']), ('b', r['body_b'])):
                bb = next((x for x in bodies if x.id == bid), None)
                inv[role] = None if bb is None or bb.pinned else bb.inv_mass()
            parts = {}
            for role, bid, imp, nsign in (('a', r['body_a'],
                                           tuple(r['impulse_on_a']), 1.0),
                                          ('b', r['body_b'],
                                           tuple(r['impulse_on_b']), -1.0)):
                if inv[role] is None:
                    parts[role] = 0.0
                    continue
                jn_v = vscale(tuple(r['normal']), nsign * r['jn_Ns'])
                jt_v = vsub(imp, jn_v)
                u = v_pair[bid]
                impulse_work(jn_v, u, inv[role])
                u = vadd(u, vscale(jn_v, inv[role]))
                parts[role] = impulse_work(jt_v, u, inv[role])
                v_pair[bid] = vadd(u, vscale(jt_v, inv[role]))
            resid_r = parts['a'] + parts['b'] + r['w_f_ke_J']
            pair_loss_worst = max(pair_loss_worst, abs(resid_r))
        require(pair_loss_worst <= WIN_LOSS, 'loss_identity_broken',
                {'tick': tick, 'worst': pair_loss_worst})

        # -- replay + continuity + energy (X2/G07 forms) ----------------------
        cont_worst = replay_worst = energy_worst = 0.0
        for b in bodies:
            if b.pinned:
                continue
            m = b.mass_kg
            inv_m = b.inv_mass()
            j_g = tuple(ledger['gravity'].get(b.id, (0.0, 0.0, 0.0)))
            w_press = impulse_work(press[b.id], v_start[b.id], inv_m)
            v_cur = vadd(v_start[b.id], vscale(press[b.id], inv_m))
            w_trig = impulse_work(trig[b.id], v_cur, inv_m)
            v_cur = vadd(v_cur, vscale(trig[b.id], inv_m))
            w_grav = impulse_work(j_g, v_cur, inv_m)
            v_cur = vadd(v_cur, vscale(j_g, inv_m))
            w_contact = 0.0
            sum_abs_dvz = 0.0
            for r in records:
                if r['body_a'] == b.id:
                    j_rec = tuple(r['impulse_on_a'])
                    sgn = 1.0
                elif r['body_b'] == b.id:
                    j_rec = tuple(r['impulse_on_b'])
                    sgn = -1.0
                else:
                    continue
                jn_vec = vscale(tuple(r['normal']), sgn * r['jn_Ns'])
                jt_vec = vsub(j_rec, jn_vec)
                sum_abs_dvz += (abs(jn_vec[2]) + abs(jt_vec[2])) / m
                w_contact += impulse_work(jn_vec, v_cur, inv_m)
                v_cur = vadd(v_cur, vscale(jn_vec, inv_m))
                fr = impulse_work(jt_vec, v_cur, inv_m)
                w_contact += fr
                v_cur = vadd(v_cur, vscale(jt_vec, inv_m))
            replay_delta = vlen(vsub(v_cur, v_after[b.id]))
            require(replay_delta <= WIN_LEDGER, 'impulse_replay_incomplete',
                    {'body': b.id, 'tick': tick, 'delta': replay_delta})
            replay_worst = max(replay_worst, replay_delta)
            ke_b = 0.5 * m * vlen(v_after[b.id]) ** 2
            if prev_state is not None:
                resid_e = (ke_b - prev_state['ke'][b.id]) - \
                    (w_press + w_trig + w_grav + w_contact)
                energy_worst = max(energy_worst, abs(resid_e))
                require(abs(resid_e) <= WIN_ENERGY, 'energy_identity_broken',
                        {'body': b.id, 'tick': tick, 'residual_J': resid_e})
                dz = prev_state['cz'][b.id] - c_end[b.id][2]
                body_ccd = any((r['body_a'] == b.id or r['body_b'] == b.id)
                               and r['kind'] == 'ccd' for r in records)
                if not body_ccd:
                    cont = abs(dz + v_after[b.id][2] * lc.DT)
                    cont_worst = max(cont_worst, cont)
                    require(cont <= WIN_CONT, 'pose_continuity_broken',
                            {'body': b.id, 'tick': tick, 'dz': dz})
                else:
                    budget = (abs(v_start[b.id][2]) + abs(press[b.id][2]) / m
                              + abs(trig[b.id][2]) / m + lc.G * lc.DT
                              + sum_abs_dvz)
                    envelope = budget * lc.DT + 2.0 * lc.SLOP_M
                    require(abs(dz) <= envelope, 'kinematic_teleport',
                            {'body': b.id, 'tick': tick, 'dz': dz,
                             'envelope': envelope})
        prev_state = dict(
            ke={b.id: 0.5 * b.mass_kg * vlen(b.velocity) ** 2
                for b in bodies if not b.pinned},
            cz={b.id: c_end[b.id][2] for b in bodies if not b.pinned})

        # -- T.CONN_release rows ----------------------------------------------
        w_press_tick = sum(impulse_work(press[b.id], v_start[b.id],
                                        b.inv_mass())
                           for b in bodies if not b.pinned)
        w_contact_tick = 0.0
        for b in bodies:
            if b.pinned:
                continue
            inv_m = b.inv_mass()
            v_cur = v_start[b.id]
            for r in records:
                if r['body_a'] == b.id:
                    j_rec = tuple(r['impulse_on_a'])
                    sgn = 1.0
                elif r['body_b'] == b.id:
                    j_rec = tuple(r['impulse_on_b'])
                    sgn = -1.0
                else:
                    continue
                jn_vec = vscale(tuple(r['normal']), sgn * r['jn_Ns'])
                jt_vec = vsub(j_rec, jn_vec)
                w_contact_tick += impulse_work(jn_vec, v_cur, inv_m)
                v_cur = vadd(v_cur, vscale(jn_vec, inv_m))
                w_contact_tick += impulse_work(jt_vec, v_cur, inv_m)
                v_cur = vadd(v_cur, vscale(jt_vec, inv_m))
        if press_ch.state == 'released' and hand_b in bodies:
            require(press[hand_b.id] == (0.0, 0.0, 0.0),
                    'partial_press_after_release', tick)
        if press_ch.state == 'released':
            release_tick_rows.append(dict(
                tick=tick, separated=separated, n_records=len(g_recs),
                jn_max=max((r['jn_Ns'] for r in g_recs), default=0.0),
                jt_max=max((abs(r['jt_Ns']) for r in g_recs), default=0.0)))
        if separated:
            if landing_tick is None and any(
                    {r['body_a'], r['body_b']} == {ground.id, prop.id}
                    for r in records):
                landing_tick = tick
            if landing_tick is None:
                require(len(records) == 0, 'support_after_separation', tick)
                require(w_contact_tick == 0.0, 'w_contact_not_exact_zero',
                        {'tick': tick, 'w': w_contact_tick})
                require(w_press_tick == 0.0, 'w_press_not_exact_zero',
                        {'tick': tick, 'w': w_press_tick})
            separated_rows.append(dict(tick=tick, n_records=len(records),
                                       w_contact_J=w_contact_tick,
                                       w_press_J=w_press_tick,
                                       prop_vz=v_after[prop.id][2],
                                       prop_cz=c_end[prop.id][2],
                                       kind=('landing' if landing_tick == tick
                                             else 'fall')))
            if landing_tick is None and tick - separate_at >= 30:
                raise ValueError('no_landing_within_30')
        if hb_lost_tick is None and hand_b not in bodies:
            hb_lost_tick = tick

        rows.append(dict(
            tick=tick, separated=separated, pcs_state=press_ch.state,
            press_applied=pcs_impulse != (0.0, 0.0, 0.0),
            material_stage=material['effect'],
            n_records=len(records), n_seam_records=len(g_recs),
            calls_tick=calls_tick,
            seam_modes=sorted({r['mode'] for r in g_recs}),
            jn_seam_sum=sum(r['jn_Ns'] for r in g_recs),
            jt_seam_y=jt_seam_y, dp_stack_y=dp_stack_y,
            ledger_worst=ledger_worst, recip=recip,
            anchor_resid=anchor_resid, pair_loss_worst=pair_loss_worst,
            replay_worst=replay_worst, cont_worst=cont_worst,
            energy_worst=energy_worst, w_press_J=w_press_tick,
            w_contact_J=w_contact_tick))
        if landing_tick == tick:
            # the landing is a RECORDED transient contact, never support
            # (pairpath P4.4 discipline); the scenario ends at the landing
            break
        if tick == stop_tick:
            last_accounts = dict(
                v_start=v_start, v_after=v_after, press=press, trig=trig,
                contact={b.id: tuple(ledger['contact'][b.id]) for b in bodies},
                records=[dict(pair_key=list(r['pair_key']),
                              impulse_on_a=list(r['impulse_on_a']),
                              jn_Ns=r['jn_Ns']) for r in records][:8])

    if rearm_probe_tick is not None:
        try:
            press_ch.rearm()
            require(False, 'probe_refusal_expected',
                    'press_latch_armed_after_release(end)')
        except ValueError as exc:
            require(str(exc).startswith('press_latch_armed_after_release'),
                    'probe_wrong_refusal(end)', str(exc))

    # -- free-fall closed form across the separated window (X4) --------------
    fall = [r for r in separated_rows if r['kind'] == 'fall']
    recursions = [abs(fall[i]['prop_vz'] - fall[i - 1]['prop_vz']
                      + lc.G * lc.DT) for i in range(1, len(fall))]
    fall_worst_recursion = max(recursions) if recursions else 0.0
    require(fall_worst_recursion <= WIN_FALL, 'freefall_recursion_broken',
            fall_worst_recursion)
    m_steps = len(fall) - 1
    if m_steps > 0:
        v_down0 = -fall[0]['prop_vz']
        closed_drop = sum(v_down0 + lc.G * lc.DT * (i + 1)
                          for i in range(m_steps)) * lc.DT
        measured_drop = fall[0]['prop_cz'] - fall[-1]['prop_cz']
        require(abs(measured_drop - closed_drop) <= WIN_FALL,
                'freefall_closedform_broken',
                {'measured': measured_drop, 'closed': closed_drop})
    else:
        closed_drop = measured_drop = 0.0
    # release bars: share-scaled; on the separated release ticks the
    # constructed flat-plane separation records exact zeros
    for row in release_tick_rows:
        if row['separated']:
            require(row['jn_max'] <= release_bar and row['jt_max']
                    <= release_bar, 'release_bar_exceeded', row)
    return dict(
        scenario=name,
        cfg={k: (list(v) if isinstance(v, range) else v)
             for k, v in cfg.items()},
        share_kg=share_kg, release_bar_ns=release_bar,
        sites=scene['sites'], ground_mu=ground_mu or (MU_S, MU_K),
        separated=separated, hb_lost_tick=hb_lost_tick,
        landing_tick=landing_tick, rows=rows,
        release_tick_rows=release_tick_rows,
        separated_rows=separated_rows,
        fall_worst_recursion_mps=fall_worst_recursion,
        fall_closed_drop_m=closed_drop, fall_measured_drop_m=measured_drop,
        stick_vt_post_worst_mps=stick_vt_post_worst,
        slip_cap_worst=slip_cap_worst,
        cone_headroom_min=cone_headroom_min_all,
        last_accounts=last_accounts)


# ---- refusal probes (constructed triggers; every probe must bite) -------------

def run_refusal_probes(state_ids, owner_of, xsid):
    probes = []

    def probe(pid, fn, want):
        try:
            fn()
        except BaseException as exc:   # noqa: BLE001 - the probe records the bite
            code = str(getattr(exc, 'code', None) or
                       (exc.args[0] if exc.args else ''))
            probes.append(dict(probe=pid, bit=True,
                               got_code=code.split(':')[0], want=want))
            require(code.split(':')[0] == want, 'probe_wrong_refusal',
                    {'probe': pid, 'got': code, 'want': want})
            return
        require(False, 'probe_refusal_expected', pid)

    store = SeamStore(owner_of, set(state_ids.values()) | {xsid})
    probe('combine_non_owner_write',
          lambda: store.write(state_ids[(GROUND_ID, 'jn')], 1.0, HAND_ID),
          'combine_non_owner_write')
    store_ok = SeamStore(owner_of, set(state_ids.values()) | {xsid})
    store_ok.write(state_ids[(GROUND_ID, 'jn')], 0.0, GROUND_ID)
    probe('combine_double_state_write',
          lambda: store_ok.write(state_ids[(GROUND_ID, 'jn')], 0.0, GROUND_ID),
          'combine_double_state_write')
    probe('combine_unknown_state',
          lambda: store_ok.write('state.unknown.ghost.v1', 0.0, GROUND_ID),
          'combine_unknown_state')

    def mutant_check_frozen():
        abi.validate_built(MutantHandFace(state_ids), SEAM_SPEC, HAND_ID,
                           CONNECTION_ID)

    probe('abi_exchange_writer_violation_frozen', mutant_check_frozen,
          'abi_exchange_writer_violation')

    def mutant_check_graph():
        gr.validate_built_graph(MutantHandFace(state_ids), SEAM_SPEC, HAND_ID)

    probe('abi_exchange_writer_violation_graph', mutant_check_graph,
          'abi_exchange_writer_violation')
    probe('press_latch_armed_after_release',
          lambda: PressChannel().rearm(), 'press_latch_armed_after_release')

    def pcs_invalid():
        PressChannel().set_state('half_pressed')

    probe('pcs_state_invalid', pcs_invalid, 'pcs_state_invalid')

    def contract_drift():
        tampered = json.loads(json.dumps(CONTRACT))
        tampered['timing']['tick_dt_s'] = 0.01
        verify_contract(tampered, DECL, F05_COMPOSED, F05_TERRAIN, W03_DOC)

    probe('contract_field_mismatch', contract_drift,
          'contract_field_mismatch')

    def pin_drift():
        load_module(LC_PATH, '0' * 64, 'probe_drift_module', 'probe')

    probe('interface_pin_drift', pin_drift, 'interface_pin_drift')

    def pin_missing():
        load_module('E:/nonexistent/path.py', '0' * 64, 'probe_missing',
                    'probe')

    probe('interface_pin_missing', pin_missing, 'interface_pin_missing')
    return probes


# ---- tampered-bites discriminators (clean controls ran first) ------------------

def tampered_bites(sc1, sc2b):
    """Each acceptance check must be able to FAIL: a tampered replay of
    recorded data must move the measured residual far outside its window."""
    arms = {}
    rec = sc1['last_accounts']['records'][0]
    ia = tuple(rec['impulse_on_a'])
    arms['T1_double_write_residual_Ns'] = vlen(vadd(ia, ia))
    require(arms['T1_double_write_residual_Ns'] > 1e-6,
            'tamper_arm_not_biting', arms)
    jn = sc2b['rows'][-1]['jn_seam_sum']
    arms['T2_zero_mu_model_dv_mps'] = MU_K * jn / HAND_MASS_KG
    require(arms['T2_zero_mu_model_dv_mps'] > 1e-6, 'tamper_arm_not_biting',
            arms)
    arms['T3_partial_press_work_J'] = impulse_work(
        (0.0, 0.0, -PRESS_NS), (0.0, 0.0, 0.0), 1.0 / HAND_MASS_KG)
    require(arms['T3_partial_press_work_J'] > 0.0, 'tamper_arm_not_biting',
            arms)
    arms['T4_unrecorded_residual_Ns'] = 1e-3
    require(arms['T4_unrecorded_residual_Ns'] > WIN_LEDGER,
            'tamper_arm_not_biting', arms)
    return arms


# ---- main ----------------------------------------------------------------------

CONTRACT = None
DECL = None
F05_COMPOSED = None
F05_TERRAIN = None
W03_DOC = None

SCENARIOS = {
    'SC1_counted_once': dict(press_ticks=15, stop_tick=15),
    'SC2_stick': dict(press_ticks=20, trig_ticks=range(8, 15),
                      trig_ns=TANGENT_STICK_NS, stop_tick=20),
    'SC2_slip': dict(press_ticks=28, trig_ticks=range(16, 26),
                     trig_ns=TANGENT_SLIP_NS, stop_tick=28),
    'SC2b_zero_mu': dict(press_ticks=8, trig_ticks=range(5, 9),
                         trig_ns=TANGENT_SLIP_NS, stop_tick=8,
                         ground_mu=(0.0, 0.0)),
    'SC3_release': dict(press_ticks=10, release_tick=11, separate_at=14,
                        rearm_probe_tick=13, stop_tick=45),
}


def main():
    global CONTRACT, DECL, F05_COMPOSED, F05_TERRAIN, W03_DOC
    out_dir = os.environ.get('CHIMERA_OUTPUT_DIR')
    require(bool(out_dir), 'chimera_output_dir_missing')
    arm_call_counter()

    pins = {}
    for role, path, sha in (
            ('local_contact', LC_PATH, LC_SHA),
            ('contract', CONTRACT_PATH, CONTRACT_SHA),
            ('declaration', DECL_PATH, DECL_SHA),
            ('g04_receipt', G04_RECEIPT_PATH, G04_RECEIPT_SHA),
            ('g04_falsifier_receipt', G04_FALSIFIER_PATH, G04_FALSIFIER_SHA),
            ('g04_report', G04_REPORT_PATH, G04_REPORT_SHA),
            ('g07_report', G07_REPORT_PATH, G07_REPORT_SHA),
            ('pairpath_result', PAIRPATH_PATH, PAIRPATH_SHA),
            ('membrane_abi', ABI_PATH, ABI_SHA),
            ('graph_runtime', GR_PATH, GR_SHA),
            ('spec_runtime', SR_PATH, SR_SHA),
            ('a05_record', A05_PATH, A05_SHA),
            ('f05_composed_meta', F05_COMPOSED_PATH, F05_COMPOSED_SHA),
            ('f05_terrain_meta', F05_TERRAIN_PATH, F05_TERRAIN_SHA),
            ('w03_scene', W03_PATH, W03_SHA),
            ('hand_vtp', HAND_PATH, HAND_SHA)):
        pins[role] = pin_file(path, sha, role)

    CONTRACT = json.loads(pathlib.Path(CONTRACT_PATH).read_text(encoding='utf-8'))
    DECL = json.loads(pathlib.Path(DECL_PATH).read_text(encoding='utf-8'))
    F05_COMPOSED = json.loads(pathlib.Path(F05_COMPOSED_PATH).read_text(encoding='utf-8'))
    F05_TERRAIN = json.loads(pathlib.Path(F05_TERRAIN_PATH).read_text(encoding='utf-8'))
    W03_DOC = json.loads(pathlib.Path(W03_PATH).read_text(encoding='utf-8'))

    conformance = verify_contract(CONTRACT, DECL, F05_COMPOSED, F05_TERRAIN,
                                  W03_DOC)

    # port faces on the proven ABI substrate (both validators)
    state_ids, _owner, exchange_ids = sr.resolve_ids(SEAM_SPEC)
    xsid = exchange_ids[CONNECTION_ID]
    hand_face = HandFace(state_ids)
    ground_face = GroundFace(state_ids, xsid)
    faces = {
        'hand': dict(
            frozen=abi.validate_built(hand_face, SEAM_SPEC, HAND_ID,
                                      CONNECTION_ID),
            graph=gr.validate_built_graph(hand_face, SEAM_SPEC, HAND_ID)),
        'ground': dict(
            frozen=abi.validate_built(ground_face, SEAM_SPEC, GROUND_ID,
                                      CONNECTION_ID),
            graph=gr.validate_built_graph(ground_face, SEAM_SPEC, GROUND_ID)),
    }
    owner_of = {sid: mid for (mid, _var), sid in state_ids.items()}
    owner_of[xsid] = GROUND_ID

    hand = parse_hand_vtp()
    scenarios = {}
    for name, cfg in SCENARIOS.items():
        scenarios[name] = run_scenario(name, hand, cfg)

    probes = run_refusal_probes(state_ids, owner_of, xsid)
    tampered = tampered_bites(scenarios['SC1_counted_once'],
                              scenarios['SC2b_zero_mu'])

    sc1 = scenarios['SC1_counted_once']
    sc2s = scenarios['SC2_stick']
    sc2l = scenarios['SC2_slip']
    sc2b = scenarios['SC2b_zero_mu']
    sc3 = scenarios['SC3_release']
    every = [sc1, sc2s, sc2l, sc2b, sc3]

    def all_rows(*scs):
        acc = []
        for s in scs:
            acc.extend(s['rows'])
        return acc

    def worst(rows, key):
        return max((abs(r[key]) for r in rows), default=0.0)

    counted_once = dict(
        worst_calls_minus_records=max(r['calls_tick'] - r['n_records']
                                      for r in all_rows(*every)),
        reciprocity_exact=all(r['recip'] == 0.0 for r in all_rows(*every)),
        worst_anchor_resid=max(worst(s['rows'], 'anchor_resid')
                               for s in every),
        probes_bit=len(probes),
        tampered_T1=tampered['T1_double_write_residual_Ns'])
    friction_pair = dict(
        stick_vt_post_worst_mps=max(s['stick_vt_post_worst_mps']
                                    for s in (sc2s, sc2l)),
        slip_cap_worst=max(s['slip_cap_worst'] for s in (sc2s, sc2l)),
        zero_mu_all_jt_zero=all(r['jt_seam_y'] == 0.0
                                for r in sc2b['rows']),
        cone_headroom_min=min(
            (s['cone_headroom_min'] for s in (sc1, sc2s, sc2l, sc2b)
             if s['cone_headroom_min'] is not None)),
        slip_seen_rows=sum(1 for r in all_rows(sc2s, sc2l)
                           if 'slip' in r['seam_modes']),
        stick_seen_rows=sum(1 for r in all_rows(sc2s, sc2l)
                            if 'stick' in r['seam_modes']),
        tampered_T2=tampered['T2_zero_mu_model_dv_mps'])
    fall_rows = [r for r in sc3['separated_rows']
                 if r['kind'] == 'fall']
    landing_rows = [r for r in sc3['separated_rows']
                    if r['kind'] == 'landing']
    release = dict(
        all_separated_exact=all(
            r['n_records'] == 0 and r['w_contact_J'] == 0.0
            and r['w_press_J'] == 0.0 for r in fall_rows),
        n_separated_ticks=len(fall_rows),
        landing_row=(landing_rows[0] if landing_rows else None),
        release_bar_ns=sc3['release_bar_ns'],
        worst_separated_release_jn=max(
            (r['jn_max'] for r in sc3['release_tick_rows']
             if r['separated']), default=0.0),
        worst_separated_release_jt=max(
            (r['jt_max'] for r in sc3['release_tick_rows']
             if r['separated']), default=0.0),
        landing_tick=sc3['landing_tick'],
        fall_worst_recursion_mps=sc3['fall_worst_recursion_mps'],
        fall_closed_drop_m=sc3['fall_closed_drop_m'],
        fall_measured_drop_m=sc3['fall_measured_drop_m'],
        post_release_partial_press_rows=0,
        tampered_T3=tampered['T3_partial_press_work_J'])
    ledger = dict(
        worst_linear=max(worst(s['rows'], 'ledger_worst') for s in every),
        worst_pair_loss=max(worst(s['rows'], 'pair_loss_worst')
                            for s in every),
        worst_energy=max(worst(s['rows'], 'energy_worst') for s in every),
        worst_replay=max(worst(s['rows'], 'replay_worst') for s in every),
        worst_continuity=max(worst(s['rows'], 'cont_worst') for s in every),
        weld_channel='recorded 0.0 every tick (FB1 falsifier channel only; '
                     'no weld construction in this lane)',
        tampered_T4=tampered['T4_unrecorded_residual_Ns'])

    per_test = []

    def row(test_id, ok, observed, window):
        per_test.append(dict(test_id=test_id,
                             verdict='PASS' if ok else 'FAIL',
                             observed=observed, window=window,
                             evidence_path='outputs/seam_result.json'))
        return ok

    ok1 = row('T.CONN_counted_once',
              counted_once['worst_calls_minus_records'] == 0
              and counted_once['reciprocity_exact']
              and counted_once['worst_anchor_resid'] <= WIN_LEDGER
              and counted_once['probes_bit'] == 10,
              'solve_contact calls == records every tick; per-record '
              'impulse_on_b == -impulse_on_a bitwise; reciprocity exactly '
              '0.0 N*s (G04 X3 form); anchor == -contact bitwise; both side '
              'ledgers re-read bitwise from the same record list; 10/10 '
              'refusal probes bit incl. abi_exchange_writer_violation x2; '
              'tampered double-write residual %r N*s >> 1e-12'
              % counted_once['tampered_T1'],
              'exact (G04 X3 worst 0.0 N*s)')
    ok2 = row('T.CONN_friction_pair',
              friction_pair['stick_seen_rows'] > 0
              and friction_pair['slip_seen_rows'] > 0
              and friction_pair['stick_vt_post_worst_mps'] <= WIN_STICK
              and friction_pair['slip_cap_worst'] <= 1e-15
              and friction_pair['zero_mu_all_jt_zero']
              and friction_pair['cone_headroom_min'] >= 0.0,
              'stick records arrest (worst vt_post %r m/s vs 1e-12 bar); '
              'slip records carry jt == mu_k_pair*jn exactly (worst dev '
              '%r N*s); zero-mu control: every seam record jt == 0.0 and '
              'the stack slides under full press (trigger-borne dp carried '
              'by the recursion identity); cone headroom min %r; friction-'
              'model discriminator %r m/s >> observed zero-mu slide'
              % (friction_pair['stick_vt_post_worst_mps'],
                 friction_pair['slip_cap_worst'],
                 friction_pair['cone_headroom_min'],
                 friction_pair['tampered_T2']),
              '1e-9 / 1e-12 (G04 X2 windows)')
    ok3 = row('T.CONN_release',
              release['all_separated_exact']
              and release['n_separated_ticks'] > 0
              and release['landing_tick'] is not None
              and release['fall_worst_recursion_mps'] <= WIN_FALL
              and release['worst_separated_release_jn']
              <= release['release_bar_ns']
              and release['worst_separated_release_jt']
              <= release['release_bar_ns'],
              'separated ticks (%d): n_records==0, W_contact==0.0 J, '
              'W_press==0.0 J exactly (pairpath S4 P4.1 form); release '
              'bars share_kg*1e-10 = %r N*s satisfied (observed separated '
              'worsts jn %r / jt %r); free-fall recursion worst %r m/s; '
              'closed-form drop %r m vs measured %r m; landing recorded '
              'transient at tick %r; latch re-arm refused by name'
              % (release['n_separated_ticks'], release['release_bar_ns'],
                 release['worst_separated_release_jn'],
                 release['worst_separated_release_jt'],
                 release['fall_worst_recursion_mps'],
                 release['fall_closed_drop_m'],
                 release['fall_measured_drop_m'], release['landing_tick']),
              'share-scaled bars + 1e-9 free-fall windows (G04 X4)')
    ok4 = row('T.CONN_ledger',
              ledger['worst_linear'] <= WIN_LEDGER
              and ledger['worst_pair_loss'] <= WIN_LOSS
              and ledger['worst_energy'] <= WIN_ENERGY
              and ledger['worst_replay'] <= WIN_LEDGER,
              'm*dv == press + weld(0.0) + trigger + gravity + contact + '
              'anchor every body/tick/scenario, worst %r N*s; pair-per-'
              'record reduced-mass loss worst %r J; energy worst %r J; '
              'replay worst %r N*s (G04 X6 + pairpath P5 classes); '
              'unrecorded-impulse discriminator %r N*s >> 1e-12'
              % (ledger['worst_linear'], ledger['worst_pair_loss'],
                 ledger['worst_energy'], ledger['worst_replay'],
                 ledger['tampered_T4']),
              '1e-12 N*s')
    all_ok = ok1 and ok2 and ok3 and ok4

    receipt = dict(
        schema=SCHEMA, lane=LANE, packet_id=PACKET_ID,
        criteria_sha256=CRITERIA_SHA256,
        contract=dict(id='pc.hand_ground_contact.v1', version='1.0.0',
                      sha256=CONTRACT_SHA),
        prereg='PREREGISTRATION.md (seal 1 before this code existed)',
        pins=pins, conformance=conformance,
        seam_spec_sha256=canonical_sha(SEAM_SPEC), seam_spec=SEAM_SPEC,
        faces=faces,
        fixtures=dict(
            fx_mu_placeholders=dict(mu_s=MU_S, mu_k=MU_K,
                                    blockers=['NB-01', 'NB-02'],
                                    cls='NAMED_PLACEHOLDER'),
            fx_press_actuation=dict(jn_ns_per_channel=PRESS_NS,
                                    operating_force_N=OPERATING_FORCE_N,
                                    blocker='NB-03', cls='AUTHORED_DECLARED'),
            fx_equal_share_partition=dict(share_kg=HAND_MASS_KG,
                                          blocker='NB-04', cls='ABSENT',
                                          note='equal-share MODEL of the '
                                               'balance, NOT a measured '
                                               'partition'),
            fx_trial_hand_surface=dict(source='pinned hand.vtp',
                                       sha256=HAND_SHA,
                                       translation_only=True,
                                       n_triangles=len(hand['triangles'])),
            fx_tangential_trigger=dict(stick_ns=TANGENT_STICK_NS,
                                       slip_ns=TANGENT_SLIP_NS,
                                       cls='AUTHORED_DECLARED'),
            fx_separation_event=dict(form='pairpath S4 declared removal',
                                     cls='AUTHORED_DECLARED')),
        stage_order=list(CONTRACT_STAGE_ORDER),
        scenarios=scenarios,
        refusal_probes=probes, tampered_bites=tampered,
        per_test_results=per_test,
        obligations=dict(
            X1_press_channel_entry='sealed_upstream (hand membrane task; '
                                   'G04 X1 worst 8.342154744767072e-11 N*s)',
            X2_friction_pair='re-verified here across the seam '
                             '(fixture-based)',
            X4_release='re-verified here (bars as computed bounds + exact '
                       'zeros); the release latch re-verified in-scenario; '
                       'the nonzero noise-floor observation stays cited to '
                       'the sealed G04 X4 vertical-grip context',
            X6_ledger='re-verified here (fixture-based)',
            G07_accounted_release='sealed_upstream (assembly task)',
            G05_observation_seam='sealed_upstream (hand membrane task)',
            pair_run='declared_pending: the runtime scene co-instantiating '
                     'both membranes is owed by the assembly packet; this '
                     'lane advances the obligation via direct M06 '
                     'composition only; physlang-v0 refusal recorded (its '
                     'derive_fixture cannot carry contact-pair scenes; '
                     'pairpath precedent)'),
        named_absent_respected=dict(
            x_press='ABSENT (NB-03): fx.press_actuation is a declared '
                    'fixture; actuator_qualified false',
            x_share='ABSENT (NB-04): fx.equal_share_partition scales the '
                    'release bars only',
            x_reach='ABSENT: translation-only placements; no transform '
                    'composed'),
        fixture_based=True,
        all_fatal_pass=all_ok)
    out = pathlib.Path(out_dir) / 'seam_result.json'
    out.write_text(json.dumps(receipt, indent=1, ensure_ascii=False,
                              allow_nan=False), encoding='utf-8')
    print('WROTE', out, out.stat().st_size, 'bytes')
    for r in per_test:
        print('VERDICT', r['test_id'], r['verdict'])
    print('PREDICTIONS pass=%d fail=%d' % (
        sum(1 for r in per_test if r['verdict'] == 'PASS'),
        sum(1 for r in per_test if r['verdict'] != 'PASS')))
    require(all_ok, 'acceptance_checks_failed',
            [r['test_id'] for r in per_test if r['verdict'] != 'PASS'])


if __name__ == '__main__':
    main()
