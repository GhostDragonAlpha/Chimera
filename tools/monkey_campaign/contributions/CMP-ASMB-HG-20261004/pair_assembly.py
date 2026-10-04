"""pair_assembly.py -- THE ASSEMBLED PAIR hand+ground (pair.hand_ground.v1).

Packet PKT-G3-ASSEMBLY-HANDGROUND (VERIFY_ASSEMBLY), lane wk-pair-assembly.
THE WAVE CAPSTONE: the three published, review-closed components --

  membrane.hand.v1    (module 737cc658..., astra PR #329)
  membrane.ground.v1  (module 1684d3b2..., astra PR #330)
  conn_seam.py 9b9a8285 (the seam-law precedent, astra PR #331)

-- are assembled into ONE verified pair under the frozen contract
pc.hand_ground_contact.v1 (sha256 a5431376...) through the GENERATED graph
wiring (the ground lane's proven graph stage; never hand-wired). The
assembly verifies COMPONENTS THROUGH THEIR CONTRACTS: each membrane is
consumed BYTE-EXACT as published and builds under ITS OWN published spec of
record; this lane owns ONLY the composition (declared, labeled, exhaustive):
  (1) the per-member context construction (their own spec bytes),
  (2) the ONE identity translation: the ground's compiled exchange closure
      reads its declared consumed slot (state.press_channel_state.
      hand_fixture_stub.v1, from its spec of record); the composition
      delivers the hand's PUBLISHED press value into that slot;
  (3) the hand composition face's press publication + the declared input
      port name translation (jn -> q_jn, the two members' namings of the
      SAME contract quantity) + the pad-side transfer bookings (the
      transfer law is applied_by assembly per the ground spec of record).

TWO LEGS (both sealed in one run):
  A. THE PHYSICS PAIR RUN -- the pairpath fixture clauses (T.ASMB_support,
     T.ASMB_propulsion_attribution, T.ASMB_slip, T.ASMB_zero_mu_control,
     T.ASMB_separation, T.ASMB_ledger_classes) at the pinned inputs, with
     the REAL hand membrane owning the press channel + release latch, the
     REAL ground membrane owning the walk-surface verdict gate, and the
     pinned M06 solver as the seam's ONLY record writer. The joined ledger
     incl. ANGULAR momentum across the whole path. F2: an EXECUTED tampered
     replay (checker mu_k drifted +1e-3) must FAIL through the full
     pipeline.
  B. THE RUNTIME SCENE (T.ASMB_runtime_scene) -- the co-instantiated ABI
     scene through the GENERATED wiring: both published membranes built,
     validated (graph_runtime.validate_built_graph, per-connection ONE-
     writer scoping), contract groups 9/9 under the pinned PORT_CONTRACT_V2
     validator, wired per the GENERATED bindings into ONE pinned
     CombineScheduler store; per-window one-quantity bitwise proofs; the
     REAL latch/release falsifiers; refusal probes that must bite.

CARRIED FINDINGS (the connection review, binding requirements):
  F1 no hardcoded conformance counts (every count computed from the
     enforced list / the observed store log);
  F2 at least one discriminator is an EXECUTED tampered replay through the
     full pipeline;
  F3 the share_kg mantissa discipline (computed BODY_MASS_KG/3.0, hex
     recorded; release bar share_kg * 1e-10; never a retyped literal);
  F4 all deviations in result.json's deviations array.

HONEST-ABSENT INHERITED: x_press (NB-03), x_share (NB-04), x_reach
(NB-05/C01) stay ABSENT; translation-only placements (A09 frame law);
fx.mu_placeholders 0.6/0.4 (NB-01/NB-02); the S3 reduced mu (0.12/0.08) and
S3b zero mu are DECLARED falsifier values, never re-pins. EVERY result is
fixture-based and never an integrated qualification (and never a
TRAINING_READY implication; the W09 unsupported-ticks finding governs that
gate). unmodeled_rotation_couple (the translation-only body line) is
reported per tick, never dropped. The physlang-v0 refusal law applies: any
derivation the pinned inputs cannot carry is named and recorded, never
forced.

CPU-only, stdlib-only, deterministic (no RNG, no wall clock in the physics).
All CPU execution through the campaign runner (NO_WORKTREES.md).
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

SCHEMA = 'chimera.pair_assembly.v1'
LANE = 'wk-pair-assembly'
PACKET_ID = 'PKT-G3-ASSEMBLY-HANDGROUND'
CRITERIA_SHA256 = ('cc65e2bce2f8ac8bf8de34382826ede1d4d60c4e8f799baba6be509b'
                   'f659b239')

HERE = pathlib.Path(__file__).resolve().parent

# ---- pinned inputs (hash-asserted; refusals interface_pin_*) ---------------

CO = 'E:/ChimeraWork/monkey-coordination'
LC_PATH = CO + '/evidence-store/MAT2-M06/source/local_contact.py'
LC_SHA = '1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc'
GC_PATH = HERE / 'hand/MAT2-G04/grip_contact.py'
GC_SHA = '0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b4173d69245'
CONTRACT_PATH = CO + '/compiler-compile/PORT_CONTRACT.hand_ground_contact.v1.json'
CONTRACT_SHA = 'a54313760c766764fb95302ebe0bee1fbc65f343770a8b9930657f2a6a3f2104'
DECL_PATH = CO + '/compiler-declare/hand_ground_declaration.v1.json'
DECL_SHA = 'a5a82d526f160be671837307419abc0f1c33a0f0636bd13220fb9b1797c3d773'
PAIRPATH_PATH = CO + '/evidence-store/MAT2-D-PAIRPATH/numerical/pairpath_result.json'
PAIRPATH_SHA = '3d3dfae1fe6bfb759045a450e7a66bc7b3fd2e670eb9ed925e06163fd65a03a9'
PAIRPATH_PREREG_PATH = (CO + '/evidence-store/MAT2-D-PAIRPATH/source/'
                        'PREREGISTRATION.md')
PAIRPATH_PREREG_SHA = ('16f64f002c187d3fa81c79aa7f9ba30247fd85641a86091d857b'
                       '41aeeb0bdb12')
CONN_SEAM_PATH = (CO + '/connection-handground/package/files/'
                  'tools/monkey_campaign/contributions/CMP-CONN-HG/'
                  'conn_seam.py')
CONN_SEAM_SHA = ('9b9a8285b0ed40dc14e30c5cd37cf0f046eb64fa101963204fbb2a82b'
                 '611450d')
CONN_RESULT_PATH = CO + '/connection-handground/result.json'
A05_PATH = (CO + '/evidence-store/MAT2-A05/workspace_evidence/'
            '48b037593f63_mutation_structure.json')
A05_SHA = '48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649'
F05_COMPOSED_PATH = CO + '/evidence-store/MAT2-F05/source/composed_meta.json'
F05_COMPOSED_SHA = ('8168382ff2c852b9fbf2c49831ec2021c8c3f5178af95d6ffba0ce5'
                    '5fa3a42f7')
F05_TERRAIN_PATH = CO + '/evidence-store/MAT2-F05/source/terrain_meta.json'
F05_TERRAIN_SHA = ('ff15fb1db3dcc128a531d21ef64d3ab62ae78190b64db36f70b5d273'
                   'c1425681')
W03_PATH = (CO + '/kanban-reviews/MAT2-W03/'
            'review-glm53flash-confirm-20260928/blobs/scene.json')
W03_SHA = 'f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342'
HAND_PATH = ('E:/PythonChimera/tools/science_funnel/data/macaque_arm/'
             'Geometry/hand.vtp')
HAND_SHA = 'a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6'

PAIR_SPEC_REL = 'spec/pair_hand_ground.spec.v1.json'
MANIFEST_REL = 'abi_binding_manifest.pair_hand_ground.v1.json'
BINDINGS_REL = 'generated/bindings.pair_hand_ground.v1.py'
WIRING_REL = 'generated/assembly_wiring_graph.pair_hand_ground.v1.py'
BINDINGS_SHA = '250c484b81135b26e7875c355df5cd7f6135cf514952c632c875aad4056efbce'
WIRING_SHA = '3b5d54c9efb288856aecbad2a344232ece36d6233237b552ad204512dead7b51'

CONNECTION_ID = 'conn.hand_ground_contact.v1'
HAND_ID = 'membrane.hand.v1'
GROUND_ID = 'membrane.ground.v1'
STUB_MEMBER_ID = 'membrane.hand_fixture_stub.v1'

# ---- frozen constants (contract + declared fixtures; PREREGISTRATION s2) ----

PLANE_Z = 0.004              # contract walk_plane_height (F05 single writer)
PLANE_HALF_M = 0.05          # declared representative plateau patch
THICK = 0.002                # M06 THICKNESS_M
STAND_OFF = 5e-6             # initial gaps (inside MARGIN 1e-5)
MU_S = 0.6                   # fx.mu_placeholders (NAMED_PLACEHOLDER, NB-01)
MU_K = 0.4                   # fx.mu_placeholders (NAMED_PLACEHOLDER, NB-02)
BODY_MASS_KG = 10.037998     # the certified G01/G07 scene line (fixture prop)
N_CHANNELS = 3               # the DECLARED lawful n for the scene reading (G01)
HAND_MASS_KG = BODY_MASS_KG / float(N_CHANNELS)   # F3: COMPUTED, never retyped
PACKET_FIXTURE_SHARE_KG = 3.3459993333333333      # the packet's recorded double
RELEASE_BAR_PER_KG = 1e-10   # contract release_bar_ns: share_kg * 1e-10
RELEASE_BAR_NS = HAND_MASS_KG * RELEASE_BAR_PER_KG
PRESS_NS = 0.30              # fx.press_actuation per channel/tick (NB-03)
TANGENT_STICK_NS = 0.05      # fx.tangential_trigger (sub-cone)
TANGENT_SLIP_NS = 0.45       # fx.tangential_trigger (saturating drive)
PROP_EDGE = 0.03             # declared prop tetra edge (m)
TETRA_TRIS = ((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3))
S3_MU = (0.12, 0.08)         # DECLARED falsifier values (pairpath S3 form)
S3B_MU = (0.0, 0.0)          # DECLARED zero-mu control
SETTLE_TICKS = 5             # the declared settle; measured windows follow

WIN_LEDGER = 1e-12           # N*s (support identity, ledger closure, attrib)
WIN_LOSS = 1e-12             # J (pair-per-record loss)
WIN_ENERGY = 1e-12           # J
WIN_MOM = 1e-12              # N*s (stack recursion + attribution)
WIN_STICK = 1e-12            # m/s (stick arrest)
WIN_FALL = 1e-9              # m/s + m (free fall)
WIN_CONT = 1e-9              # m (pose continuity)
WIN_STORED = 1e-9            # J (stored-energy bracket)

STACK_WEIGHT_IMP = 0.0       # computed at run from lc.G/lc.DT (record-g)
lc = None                    # the pinned M06 solver module (loaded in main)
gc = None                    # the pinned G04 grip module (TETRA_TRIS of record)


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


def load_module(path, name):
    p = pathlib.Path(path)
    spec_mod = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec_mod)
    sys.modules[name] = mod
    spec_mod.loader.exec_module(mod)
    return mod


def naive_sum(values):
    """The producer's naive loop (review lesson 5: CPython sum() is
    Neumaier-compensated; bitwise checks replay the naive loop)."""
    acc = 0.0
    for v in values:
        acc += v
    return acc


# ---- F1: the enforced-rows ledger (NO hardcoded conformance counts) ---------

class Enforced:
    """Every conformance/acceptance assertion registers itself here; every
    count in the receipt is len(rows) or a store-log delta -- computed,
    never a constant."""

    def __init__(self):
        self.rows = []

    def check(self, label, ok, code, detail=''):
        self.rows.append({'row': label, 'held': bool(ok)})
        if not ok:
            raise ValueError('enforcement_failed:' + code
                             + ((': ' + str(detail)) if detail != '' else ''))
        return ok

    def count(self):
        return len(self.rows)

    def all_held(self, prefix):
        return all(r['held'] for r in self.rows if r['row'].startswith(prefix))


# ---- vector helpers ---------------------------------------------------------

def vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vscale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def vlen(a):
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def vmean(vertices):
    n = float(len(vertices))
    return (sum(v[0] for v in vertices) / n,
            sum(v[1] for v in vertices) / n,
            sum(v[2] for v in vertices) / n)


def impulse_work(j_vec, u_vec, inv_mass):
    dot = j_vec[0] * u_vec[0] + j_vec[1] * u_vec[1] + j_vec[2] * u_vec[2]
    j2 = j_vec[0] ** 2 + j_vec[1] ** 2 + j_vec[2] ** 2
    return dot + 0.5 * inv_mass * j2


# ---- pinned hand.vtp surface (the trial contact surface, translation-only) --

def parse_hand_vtp():
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


# ---- the pair faces (built through the GENERATED wiring's own path) ---------

_GEN = {'mod': None}


def wiring_regeneration_identity():
    """Regenerate the wiring (no writes) and require byte identity with the
    landed artifacts; counts computed from the receipt (F1). The landed
    bindings artifact is a LOADED input for the generator (freshly_emitted
    false), so the receipt carries its sha in inputs.bindings and proves
    table_equals_fresh_derivation; a freshly-emitted case would list it in
    outputs instead."""
    gw = load_module(HERE / 'graph_wiring_generate.py', 'pair_gen_stage')
    receipt = gw.generate_graph_wiring(HERE, PAIR_SPEC_REL, MANIFEST_REL,
                                       out_dir=None)
    outs = {pathlib.Path(o['path']).name: o['sha256']
            for o in receipt['outputs']}
    require(outs.get(pathlib.Path(WIRING_REL).name) ==
            sha_file(HERE / WIRING_REL),
            'wiring_wiring_regenerated_drift', outs)
    bindings_in = receipt['inputs']['bindings']
    require(bindings_in['sha256'] == BINDINGS_SHA,
            'wiring_bindings_identity_drift', bindings_in)
    require(bindings_in['freshly_emitted'] is False,
            'wiring_bindings_unexpectedly_emitted', bindings_in)
    require(receipt['bindings_gate']['table_equals_fresh_derivation'] is True
            and receipt['bindings_gate']['reference_only'] is True
            and receipt['bindings_gate']['formulas_embedded'] is False,
            'wiring_bindings_gate_failed', receipt['bindings_gate'])
    return {'regenerated_wiring_sha256': outs[pathlib.Path(WIRING_REL).name],
            'landed_bindings_sha256': bindings_in['sha256'],
            'bindings_freshly_emitted': bindings_in['freshly_emitted'],
            'bindings_gate': receipt['bindings_gate'],
            'byte_identical': True,
            'receipt_schema': receipt['schema'],
            'module_specific_branches':
                receipt['abi']['module_specific_branches'],
            'plan_placement_rows':
                len(receipt['plan']['contribution_placement'])}


def pair_context_and_faces():
    """The GENERATED wiring module's own load path: verify every byte, load
    the manifest-bound adapters (ABI-validated), the landed wrapped modules,
    the frozen-input gates and the pair context (bindings cross-checked)."""
    if _GEN['mod'] is None:
        pin_file(HERE / BINDINGS_REL, BINDINGS_SHA, 'generated_bindings')
        pin_file(HERE / WIRING_REL, WIRING_SHA, 'generated_wiring')
        _GEN['mod'] = load_module(HERE / WIRING_REL,
                                  'pair_generated_assembly_wiring')
    gen = _GEN['mod']
    mods, adapters, context, gates = gen.load_members()
    hand_face = adapters[HAND_ID].build(context, 0.005)
    ground_face = adapters[GROUND_ID].build(context, 0.005)
    return gen, hand_face, ground_face, context, gates, mods


def face_delta_proof(hand_face, ground_face):
    """The composition's ONLY deltas vs the published membranes, proven:
    the hand input port's declared quantity-name translation; everything
    else delegated 1:1."""
    raw = hand_face.raw_ports()
    face = hand_face.ports()
    raw_in = sorted((r['port_id'], r['quantity_ref']) for r in raw['inputs'])
    face_in = sorted((r['port_id'], r['quantity_ref'])
                     for r in face['inputs'])
    require(face_in == [('in.jn', 'q_jn')], 'face_port_translation_wrong',
            face_in)
    require(raw_in == [('in.jn', 'jn')], 'raw_port_surface_changed', raw_in)
    raw_out = sorted((r['port_id'], r['quantity_ref'], r['unit'])
                     for r in raw['outputs'])
    face_out = sorted((r['port_id'], r['quantity_ref'], r['unit'])
                      for r in face['outputs'])
    require(raw_out == face_out, 'face_output_ports_changed',
            (raw_out, face_out))
    require(not hasattr(hand_face.raw, 'exchange_contribution'),
            'raw_hand_writer_appeared', None)
    return {'hand_input_port_translation':
            'in.jn: jn -> q_jn (the ONLY declared delta)',
            'hand_output_ports_untouched': True,
            'raw_hand_has_no_exchange_writer': True}


def _resolve_pair_ids(context):
    import spec_runtime  # noqa: E402
    return spec_runtime.resolve_ids(context.spec)


def _contract_coverage(gen, context):
    """The graph-v2 contract coverage count (computed; the AssemblyRun
    already refused anything below 9/9 at build)."""
    import PORT_CONTRACT_V2  # noqa: E402
    contract = gen_build_contract(gen, context)
    decl = {"membranes": [{"membrane_id": m["membrane_id"]}
                          for m in context.spec["membranes"]]}
    vreport = PORT_CONTRACT_V2.validate_contract_v2(contract, decl)
    coverage = sum(1 for row in vreport['coverage'] if row['covered'])
    return {'coverage': coverage, 'valid': bool(vreport['valid']),
            'schema_major': vreport['schema_major']}


def gen_build_contract(gen, context):
    import graph_runtime  # noqa: E402
    import spec_runtime  # noqa: E402
    state_ids, state_owner, exchange_ids = spec_runtime.resolve_ids(
        context.spec)
    return graph_runtime.build_contract_groups_graph(
        context.spec, context.spec_raw_sha256, state_ids, state_owner,
        exchange_ids, 0.005)


def adapters_fresh_hand(context):
    return _fresh_adapter('pair_probe_hand_adapter', 'adapter_pair_hand.py',
                          context)


def adapters_fresh_ground(context):
    return _fresh_adapter('pair_probe_ground_adapter',
                          'adapter_pair_ground.py', context)


def _fresh_adapter(mod_name, file_name, context):
    spec_mod = importlib.util.spec_from_file_location(mod_name,
                                                      HERE / file_name)
    mod = importlib.util.module_from_spec(spec_mod)
    sys.modules[mod_name] = mod
    spec_mod.loader.exec_module(mod)
    return mod.build(context, 0.005)


# ---- LEG B: the runtime scene (T.ASMB_runtime_scene) ------------------------

SCENE_ARMED_WINDOWS = 4      # the armed declared case (constant record 0.3)
SCENE_RELEASED_WINDOWS = 3   # the released declared case (constant record 0.0)


def _drive(hf, tick, phase):
    """One REAL channel decision; returns (value, refused_code)."""
    try:
        return float(hf.drive_tick(tick, phase)), None
    except Exception as exc:   # noqa: BLE001 - the probe records the bite
        value = hf.raw.press_channel.value
        return (float(value) if value is not None else 0.0), \
            str(getattr(exc, 'code', None) or exc.args[0])


def run_scene(enforced):
    """The co-instantiated ABI scene through the GENERATED wiring."""
    gen, hand_face, ground_face, context, gates, mods = pair_context_and_faces()
    state_ids, _owner, exchange_ids = _resolve_pair_ids(context)
    xsid = exchange_ids[CONNECTION_ID]
    press_id = state_ids[(HAND_ID, 'press_channel_state')]
    obs_id = state_ids[(HAND_ID, 'grasp_observation_table')]
    plane_id = state_ids[(GROUND_ID, 'walk_plane_height')]
    # the stub-consumed slot id lives in the GROUND's spec of record; the
    # ground composition face carries it from its own build (asserted equal
    # to the real module's compiled closure id at adapter build time)
    stub_press_id = ground_face._stub_press_id
    hand_face_pair_press_id = ground_face._pair_press_id

    delta = face_delta_proof(hand_face, ground_face)
    import graph_runtime  # noqa: E402
    conf = dict(
        hand=graph_runtime.validate_built_graph(hand_face, context.spec,
                                                HAND_ID),
        ground=graph_runtime.validate_built_graph(ground_face, context.spec,
                                                  GROUND_ID))
    coverage = _contract_coverage(gen, context)
    enforced.check('scene.contract_groups_coverage_9_of_9',
                   coverage['coverage'] == 9 and coverage['valid']
                   and coverage['schema_major'] == 2,
                   'contract_groups_coverage', coverage)

    def drain(run, hf, gf, tick, phase, log_mark):
        channel, refused = _drive(hf, tick, phase)
        result = run.step()
        record = run.exchange_record()
        press_pub = run.state_value(HAND_ID, 'press_channel_state')
        plane = run.state_value(GROUND_ID, 'walk_plane_height')
        # WINDOW-START LAW (the frozen pair ABI's zero-order-hold): the
        # ground's OWN laws re-derive the record from the hand's published
        # value AS OF THE WINDOW-START VIEW (the same immutable view the
        # scheduler's contributions read) -- never a live channel object:
        press_ws = run.last_window_start[press_id]
        translated = {stub_press_id: press_ws}
        q_derived = gf.raw.exchange_quantity(translated)
        jt_derived = gf.raw.jt_record(translated)
        mu_pair = gf.pair_mu()
        # S1 counted-once from the store log DELTA (computed, F1):
        log = result.get('store_log') or []
        window_log = log[log_mark['n']:]
        log_mark['n'] = len(log)
        xsid_applies = [r for r in window_log
                        if r.get('state_id') == xsid
                        and r.get('op') == 'apply']
        hand_applies = [r for r in window_log
                        if r.get('state_id') == xsid
                        and r.get('actor') == HAND_ID]
        obs_applies = [r for r in window_log
                       if r.get('state_id') == obs_id
                       and r.get('op') == 'apply']
        plane_applies = [r for r in window_log
                         if r.get('state_id') == plane_id
                         and r.get('op') == 'apply']
        enforced.check('scene.counted_once_record_write',
                       len(xsid_applies) == 1, 'scene_record_write_count',
                       {'tick': tick, 'applies': len(xsid_applies)})
        enforced.check('scene.record_writer_is_ground',
                       all(r.get('actor') == GROUND_ID
                           for r in xsid_applies),
                       'scene_record_wrong_writer',
                       [r.get('actor') for r in xsid_applies])
        enforced.check('scene.hand_never_writes_record',
                       len(hand_applies) == 0, 'scene_hand_wrote_record',
                       {'tick': tick, 'applies': len(hand_applies)})
        enforced.check('scene.plane_never_rewritten',
                       len(plane_applies) == 0, 'scene_plane_rewritten',
                       {'tick': tick, 'applies': len(plane_applies)})
        enforced.check('scene.record_is_ground_law_of_hand_decision',
                       record == q_derived, 'scene_record_drift',
                       {'tick': tick, 'record': record,
                        'derived': q_derived})
        enforced.check('scene.jt_is_ground_declared_ast',
                       jt_derived == mu_pair * record, 'scene_jt_drift',
                       {'tick': tick, 'jt': jt_derived,
                        'want': mu_pair * record})
        enforced.check('scene.press_publication_bitwise',
                       press_pub == channel, 'scene_press_drift',
                       {'tick': tick, 'published': press_pub,
                        'channel': channel})
        enforced.check('scene.window_start_publication_constant',
                       press_ws == channel,
                       'scene_window_start_law',
                       {'tick': tick, 'window_start': press_ws,
                        'note': 'the declared cases are constant-record '
                                'builds; the window-start publication '
                                'equals the current decision in every '
                                'stepped window'})
        enforced.check('scene.plane_bitwise_authored', plane == PLANE_Z,
                       'scene_plane_drift', {'tick': tick, 'plane': plane})
        enforced.check('scene.q_proof_bitwise',
                       bool(run.q_proofs)
                       and run.q_proofs[-1]['bitwise_equal'],
                       'scene_q_proof_failed', {'tick': tick})
        led = result.get('ledger') or {}
        jn_total = naive_sum([led[k]['total'] for k in sorted(led)
                              if k.endswith('jn.into_hand')
                              or k.endswith('jn.into_ground')])
        jt_total = naive_sum([led[k]['total'] for k in sorted(led)
                              if k.endswith('jt.into_hand')
                              or k.endswith('jt.into_ground')])
        enforced.check('scene.ledger_zero_sum_bitwise',
                       jn_total == 0.0 and jt_total == 0.0,
                       'scene_ledger_open',
                       {'jn': jn_total, 'jt': jt_total})
        latched = bool(hf.raw.press_channel.latched)
        if latched or phase == 'release':
            enforced.check('scene.released_record_exactly_zero',
                           record == 0.0 and jt_derived == 0.0,
                           'scene_release_not_exact_zero',
                           {'tick': tick, 'record': record,
                            'jt': jt_derived})
        return dict(tick=tick, phase=phase, refused=refused, latched=latched,
                    channel=channel, record=record, jt=jt_derived,
                    press_published=press_pub, plane=plane,
                    ledger_jn_total=jn_total, ledger_jt_total=jt_total,
                    state_hash=result.get('state_hash'),
                    obs_applies=len(obs_applies))

    scenarios = {}

    # -- the ARMED declared case: a constant-record generated build (the
    #    generated per-window ONE-quantity proof compares the window-start
    #    view with the post-window record, so each declared case runs as
    #    its own generated build -- the ground-lane precedent scene shape)
    run1 = gen.build(0.005, 'armed_hold', max_workers=4)
    hf1 = run1.membranes[HAND_ID]
    gf1 = run1.membranes[GROUND_ID]
    rows1 = []
    log_mark = {'n': 0}
    for tick in range(1, SCENE_ARMED_WINDOWS + 1):
        rows1.append(drain(run1, hf1, gf1, tick, 'hold', log_mark))
    armed_rows = [r for r in rows1 if r['refused'] is None
                  and not r['latched']]
    enforced.check('scene.armed_windows_carry_fixture_record',
                   armed_rows and all(r['record'] == PRESS_NS
                                      for r in armed_rows),
                   'scene_armed_record_wrong',
                   [(r['tick'], r['record']) for r in armed_rows])
    enforced.check('scene.observation_table_never_applied',
                   all(r['obs_applies'] == 0 for r in rows1),
                   'scene_obs_table_written',
                   [(r['tick'], r['obs_applies']) for r in rows1])
    # determinism: a fresh build replaying the identical schedule must
    # reproduce the per-window state-hash chain bitwise (F1: window count
    # computed from the declared case constant)
    run1b = gen.build(0.005, 'armed_hold', max_workers=4)
    hf1b = run1b.membranes[HAND_ID]
    gf1b = run1b.membranes[GROUND_ID]
    hashes_b = []
    for tick in range(1, SCENE_ARMED_WINDOWS + 1):
        _drive(hf1b, tick, 'hold')
        hashes_b.append(run1b.step().get('state_hash'))
    hashes_a = [r['state_hash'] for r in rows1]
    enforced.check('scene.deterministic_chain_bitwise',
                   hashes_a == hashes_b, 'scene_determinism_broken',
                   {'windows': SCENE_ARMED_WINDOWS})
    scenarios['armed_hold_case'] = dict(rows=rows1,
                                        deterministic_chain_bitwise=True)

    # -- the RELEASED declared case: its own constant-record generated build;
    #    the REAL latch arc runs on the scene's own channel objects: the
    #    release tick (record exactly 0.0), then the silent re-arm refusal
    #    bites INSIDE the generated windows (the record stays 0.0), then --
    #    between builds -- the EXPLICIT re-arm returns the channel to armed
    #    and its decision is verified on the real surface (the transition
    #    windows' seam law is the physics pair run's SC3_release subject)
    run2 = gen.build(0.005, 'released', max_workers=4)
    hf2 = run2.membranes[HAND_ID]
    gf2 = run2.membranes[GROUND_ID]
    rows2 = []
    log_mark = {'n': 0}   # each generated build owns a FRESH store log
    for tick in range(1, SCENE_RELEASED_WINDOWS + 1):
        rows2.append(drain(run2, hf2, gf2, tick, 'release', log_mark))
    enforced.check('scene.released_case_exact_zeros',
                   all(r['record'] == 0.0 and r['jt'] == 0.0
                       and r['ledger_jn_total'] == 0.0
                       and r['ledger_jt_total'] == 0.0 for r in rows2),
                   'scene_released_case_not_zero',
                   [(r['tick'], r['record'], r['jt']) for r in rows2])
    # the silent re-arm arc on the released scene's own REAL channel: the
    # first hold after the release must be refused by the latch law
    arc = []
    channel, refused = _drive(hf2, 90, 'hold')
    arc.append(dict(step='hold_after_release', value=channel,
                    refused=refused))
    enforced.check('scene.latch_silent_rearm_refused',
                   refused == 'ref.hand.latch_silent_rearm',
                   'scene_latch_probe_did_not_bite', arc)
    # the EXPLICIT declared re-arm (the only latch-clearing act), then the
    # re-armed decision is verified on the real channel (outside the
    # generated constant-record windows; recorded, never scheduler-stepped)
    rearm_ok = bool(hf2.raw.press_channel.re_arm())
    value_after_rearm, refused2 = _drive(hf2, 91, 'hold')
    arc.append(dict(step='explicit_re_arm', ok=rearm_ok,
                    value_after_rearm=value_after_rearm,
                    refused=refused2))
    enforced.check('scene.explicit_rearm_returns_armed_decision',
                   rearm_ok and value_after_rearm == PRESS_NS
                   and refused2 is None,
                   'scene_rearm_arc_wrong', arc)
    scenarios['released_case_and_latch_arc'] = dict(
        rows=rows2, latch_arc=arc)

    # -- refusal probes (each must bite; codes named) ------------------------
    probes = []

    def probe(pid, fn, want):
        try:
            fn()
        except BaseException as exc:   # noqa: BLE001 - the bite is the datum
            code = str(getattr(exc, 'code', None) or
                       (exc.args[0] if exc.args else ''))
            bit = code.split(':')[0] == want
            probes.append(dict(probe=pid, bit=bool(bit),
                               got_code=code.split(':')[0], want=want))
            enforced.check('scene.probe_' + pid, bit, 'probe_wrong_refusal',
                           {'probe': pid, 'got': code, 'want': want})
            return
        enforced.check('scene.probe_' + pid, False, 'probe_refusal_expected',
                       pid)

    import spec_runtime  # noqa: E402

    class MutantHandFace(type(hand_face)):
        """The constructed DOUBLE-WRITER face: a hand face that also exposes
        exchange_contribution() producing the connection's record. The
        substrate must refuse it by name."""

        def exchange_contribution(self):
            def compute(view, ctx):
                return {"states": {}, "ledger": []}
            return spec_runtime.Contribution(
                'probe.mutant.hand.writer', self.membrane_id,
                [hand_face.xsid], compute)

    def mutant_writer():
        mutant = MutantHandFace(hand_face.raw, hand_face._ctx)
        graph_runtime.validate_built_graph(mutant, context.spec, HAND_ID)

    probe('abi_exchange_writer_violation', mutant_writer,
          'abi_exchange_writer_violation')

    def negative_press_record():
        # a crafted WINDOW-START view carrying a negative hand publication:
        # the REAL ground exchange compute must refuse it by name
        gf1.exchange_contribution().func(
            {plane_id: PLANE_Z, hand_face_pair_press_id: -0.1}, None)

    probe('ref.ground.jn_negative_press_record', negative_press_record,
          'ref.ground.jn_negative_press_record')

    def rearm_without_release():
        fresh_channel = type(hf1.raw.press_channel)(PRESS_NS)
        fresh_channel.re_arm()   # never released -> the named refusal

    probe('ref.hand.rearm_without_release', rearm_without_release,
          'ref.hand.rearm_without_release')

    def third_state():
        hf1.raw.press_channel.step(99, 'half')

    probe('ref.hand.press_state_not_armed_nor_released', third_state,
          'ref.hand.press_state_not_armed_nor_released')

    def pin_drift():
        pin_file(HERE / WIRING_REL, '0' * 64, 'probe_drift')

    probe('interface_pin_drift', pin_drift, 'interface_pin_drift')

    scene = dict(
        generated_wiring_sha256=WIRING_SHA,
        generated_bindings_sha256=BINDINGS_SHA,
        face_delta=delta,
        conformance_hand=conf['hand'],
        conformance_ground=conf['ground'],
        writer_scoping_rows=(len(conf['hand']['writer_scoping'])
                             + len(conf['ground']['writer_scoping'])),
        contract_groups_coverage=coverage,
        armed_windows=SCENE_ARMED_WINDOWS,
        released_windows=SCENE_RELEASED_WINDOWS,
        scene_shape_law='the generated per-window ONE-quantity proof '
                        'compares the window-start view with the post-window '
                        'record, so each declared case runs as its own '
                        'CONSTANT-RECORD generated build (the ground-lane '
                        'precedent scene shape); the latch TRANSITION arc '
                        'runs on the scene\'s own real channel surfaces '
                        'between/inside builds with every refusal biting, '
                        'and the transition windows\' seam law is the '
                        'physics pair run\'s SC3_release subject',
        scenarios=scenarios,
        probes=probes,
        probes_count=len(probes),
        probes_bit=sum(1 for p in probes if p['bit']),
        composition_owned_pieces=[
            'per-member context construction (each member builds under its '
            'OWN published spec bytes; the wrapped modules byte-exact)',
            'the ONE identity translation: the ground\'s declared consumed '
            'slot receives the hand\'s published press value',
            'the hand composition face: press publication + the declared '
            'input port name translation (jn -> q_jn)',
            'the pad-side transfer bookings (applied_by assembly)'],
        real_code_paths=[
            'the real ground exchange compute (record write, '
            'negative-press refusal, plane invariant, ground-side bookings)',
            'the real ground jt AST + pair_mu + walk_surface_verdict',
            'the real hand press channel + release latch',
            'the real ground integrate contribution',
            'the generated wiring: placement, pinned scheduler, per-window '
            'one-quantity bitwise proofs'],
        scope_note='the M06 contact dynamics across the seam are the '
                   'physics pair run\'s subject (T.ASMB_support..'
                   'separation); this scene is the co-instantiated ABI '
                   'composition at the declared fixture operating point',
    )
    return scene


# ---- LEG A: the physics pair run (the pairpath fixture clauses) -------------

_CALLS = {'n': 0}
_ORIG_SOLVE = {'fn': None}


def arm_call_counter(lc_mod):
    _ORIG_SOLVE['fn'] = lc_mod.solve_contact

    def counting(*args, **kwargs):
        _CALLS['n'] += 1
        return _ORIG_SOLVE['fn'](*args, **kwargs)
    lc_mod.solve_contact = counting


def build_scene(hand, ground_mu):
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
    # producer parity: the sealed pairpath scene computed the centroid with
    # the built-in sum() (review lesson 5: replay the producer's loop)
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
                   triangles=list(gc.TETRA_TRIS))   # the G04 windings of record
    return dict(ground=ground, hand=hand_body, prop=prop, sites=sites,
                hand_translation=list(t), prop_origin=list(origin))


SCENARIOS = {
    'SC1_counted_once': dict(press_ticks=15, stop_tick=15),
    'SC2_stick': dict(press_ticks=20, trig_ticks=range(8, 15),
                      trig_ns=TANGENT_STICK_NS, stop_tick=20),
    'SC2_slip': dict(press_ticks=28, trig_ticks=range(16, 26),
                     trig_ns=TANGENT_SLIP_NS, stop_tick=28),
    'SC3_slip_reduced': dict(press_ticks=28, trig_ticks=range(16, 26),
                             trig_ns=TANGENT_SLIP_NS, stop_tick=28,
                             ground_mu=S3_MU),
    'SC2b_zero_mu': dict(press_ticks=8, trig_ticks=range(5, 9),
                         trig_ns=TANGENT_SLIP_NS, stop_tick=8,
                         ground_mu=S3B_MU),
    'SC3_release': dict(press_ticks=10, release_tick=11, separate_at=14,
                        stop_tick=45),
}
TAMPERED_SLIP_CFG = dict(SCENARIOS['SC3_slip_reduced'])
TAMPERED_SLIP_CFG['checker_mu_k'] = S3_MU[1] + 1e-3   # F2's declared arm


def run_scenario(name, hand, cfg, faces, enforced, parity_traj=None):
    """One pairpath fixture clause through the REAL membrane surfaces.
    parity_traj: the sealed pairpath P1.2 prop_cz list; when given, the
    scene's own prop_cz is gated against it per tick (SEALed-scene parity)."""
    press_ticks = cfg['press_ticks']
    release_tick = cfg.get('release_tick', press_ticks + 1)
    separate_at = cfg.get('separate_at')
    trig_ticks = set(cfg.get('trig_ticks', ()))
    trig_ns = cfg.get('trig_ns', 0.0)
    ground_mu = cfg.get('ground_mu', (MU_S, MU_K))
    checker_mu_k = cfg.get('checker_mu_k')
    stop_tick = cfg['stop_tick']

    hand_face, ground_face = faces
    scene = build_scene(hand, ground_mu)
    ground, hand_b, prop = scene['ground'], scene['hand'], scene['prop']
    bodies = [ground, hand_b, prop]
    share_kg = HAND_MASS_KG          # F3: computed above, never retyped
    release_bar = share_kg * RELEASE_BAR_PER_KG
    rows = []
    prev_state = None
    separated = False
    landing_tick = None
    release_tick_rows = []
    separated_rows = []
    stick_vt_post_worst = 0.0
    slip_cap_worst = 0.0
    cone_headroom_min_all = None
    support_worst = 0.0
    falsifiers = []

    for tick in range(1, stop_tick + 1):
        phase = 'release' if tick == release_tick else 'hold'
        pressing = tick <= press_ticks and not separated
        channel, channel_refused = _drive(hand_face, tick, phase)
        press_total = channel * float(N_CHANNELS)
        if separate_at is not None and tick == separate_at:
            # fx.separation_event (the pairpath S4 declared form)
            separated = True
            bodies = [ground, prop]
        verdict = ground_face.walk_surface_verdict(0.0, 'ground')
        enforced.check('physics.ground_walk_verdict_inside',
                       verdict['verdict'] == 'INSIDE'
                       and verdict['outside'] is False,
                       'ground_walk_verdict_outside',
                       {'tick': tick, 'verdict': verdict})
        v_start = {b.id: tuple(b.velocity) for b in bodies}
        press = {b.id: (0.0, 0.0, 0.0) for b in bodies}
        trig = {b.id: (0.0, 0.0, 0.0) for b in bodies}
        if pressing and channel != 0.0 and not separated:
            press[hand_b.id] = (0.0, 0.0, -press_total)
            hand_b.velocity = vadd(hand_b.velocity,
                                   vscale(press[hand_b.id],
                                          hand_b.inv_mass()))
        if trig_ticks and tick in trig_ticks and not separated:
            trig[prop.id] = (0.0, trig_ns, 0.0)
            trig[hand_b.id] = (0.0, -trig_ns, 0.0)
            prop.velocity = vadd(prop.velocity,
                                 vscale(trig[prop.id], prop.inv_mass()))
            hand_b.velocity = vadd(hand_b.velocity,
                                   vscale(trig[hand_b.id],
                                          hand_b.inv_mass()))
            enforced.check('physics.trigger_reciprocity',
                           vlen(vadd(trig[prop.id],
                                     trig[hand_b.id])) <= WIN_LEDGER,
                           'trigger_reciprocity_broken', tick)
        calls_at = _CALLS['n']
        c_start = {b.id: vmean(b.vertices) for b in bodies}
        records, ledger = lc.solve_tick(bodies)
        calls_tick = _CALLS['n'] - calls_at
        v_after = {b.id: tuple(b.velocity) for b in bodies}
        c_end = {b.id: vmean(b.vertices) for b in bodies}

        # counted-once (S1): the pinned solver is the ONLY record writer
        enforced.check('physics.counted_once', calls_tick == len(records),
                       'counted_once_broken',
                       {'tick': tick, 'calls': calls_tick,
                        'records': len(records)})
        keys = [r['pair_key'] for r in records]
        enforced.check('physics.record_key_unique',
                       len(set(keys)) == len(keys), 'record_key_duplicate',
                       tick)
        reciprocity_exact = (0.0, 0.0, 0.0)
        for r in records:
            ia, ib = tuple(r['impulse_on_a']), tuple(r['impulse_on_b'])
            for k in range(3):
                enforced.check('physics.record_bitwise_opposite',
                               ib[k] == -ia[k], 'record_not_bitwise_opposite',
                               {'tick': tick, 'k': k})
            reciprocity_exact = vadd(reciprocity_exact, ia)
            reciprocity_exact = vadd(reciprocity_exact, ib)
        enforced.check('physics.reciprocity_exact',
                       reciprocity_exact == (0.0, 0.0, 0.0),
                       'reciprocity_not_exact', reciprocity_exact)
        contact_re = {b.id: (0.0, 0.0, 0.0) for b in bodies}
        for r in records:
            contact_re[r['body_a']] = vadd(contact_re[r['body_a']],
                                           tuple(r['impulse_on_a']))
            contact_re[r['body_b']] = vadd(contact_re[r['body_b']],
                                           tuple(r['impulse_on_b']))
        for b in bodies:
            enforced.check('physics.ledger_reread_bitwise',
                           contact_re[b.id] == tuple(ledger['contact'][b.id]),
                           'ledger_reread_drift', {'tick': tick,
                                                   'body': b.id})
        anchor_resid = 0.0
        for b in bodies:
            if b.pinned:
                anc = tuple(ledger['anchor'][b.id])
                con = tuple(ledger['contact'][b.id])
                for k in range(3):
                    enforced.check('physics.anchor_reaction_bitwise',
                                   anc[k] == -con[k], 'anchor_not_reaction',
                                   {'tick': tick, 'k': k})
                anchor_resid = max(anchor_resid, vlen(vadd(anc, con)))

        g_recs = [r for r in records
                  if {r['body_a'], r['body_b']} == {ground.id, hand_b.id}]
        pg_recs = [r for r in records
                   if {r['body_a'], r['body_b']} == {ground.id, prop.id}]
        mu_s_pair = min(hand_b.mu_s, ground.mu_s)
        mu_k_pair = min(hand_b.mu_k, ground.mu_k)
        enforced.check('physics.pair_rule_matches_pinned_solver',
                       (mu_s_pair, mu_k_pair) == lc.pair_mu(hand_b, ground),
                       'pair_rule_disagrees', (mu_s_pair, mu_k_pair))
        if checker_mu_k is not None:
            mu_k_pair = checker_mu_k   # THE F2 TAMPER (checker side only)

        jn_ground_sum = naive_sum([r['jn_Ns'] for r in g_recs])
        pg_recs_all = [r for r in records
                       if {r['body_a'], r['body_b']} == {ground.id,
                                                         prop.id}]
        jn_pg_sum = naive_sum([r['jn_Ns'] for r in pg_recs_all])
        jt_seam_y = 0.0
        jt_all_ground_y = 0.0
        for r in g_recs:
            on_hand = tuple(r['impulse_on_a'] if r['body_a'] == hand_b.id
                            else r['impulse_on_b'])
            sgn = 1.0 if r['body_a'] == hand_b.id else -1.0
            jn_vec = vscale(tuple(r['normal']), sgn * r['jn_Ns'])
            jt_vec = vsub(on_hand, jn_vec)
            jt_seam_y += jt_vec[1]
            jt_all_ground_y += jt_vec[1]
            head = mu_s_pair * r['jn_Ns'] - vlen(jt_vec)
            enforced.check('physics.cone_law', head >= 0.0, 'cone_violated',
                           {'tick': tick, 'head': head})
            cone_headroom_min_all = (head if cone_headroom_min_all is None
                                     else min(cone_headroom_min_all, head))
            if r['mode'] == 'slip':
                want = mu_k_pair * r['jn_Ns']
                enforced.check('physics.slip_cap_per_record',
                               r['jt_Ns'] == want, 'slip_cap_not_pair_mu_k',
                               {'tick': tick, 'jt': r['jt_Ns'],
                                'want': want})
                slip_cap_worst = max(slip_cap_worst, abs(r['jt_Ns'] - want))
            if r['mode'] == 'stick':
                enforced.check('physics.stick_arrest',
                               r['vt_post'] <= WIN_STICK,
                               'stick_arrest_broken',
                               {'tick': tick, 'vt_post': r['vt_post']})
                stick_vt_post_worst = max(stick_vt_post_worst, r['vt_post'])
        for r in pg_recs:
            on_b = tuple(r['impulse_on_a'] if r['body_a'] == prop.id
                         else r['impulse_on_b'])
            sgn = 1.0 if r['body_a'] == prop.id else -1.0
            jn_vec = vscale(tuple(r['normal']), sgn * r['jn_Ns'])
            jt_all_ground_y += vsub(on_b, jn_vec)[1]
        if ground_mu == S3B_MU:
            for r in g_recs:
                enforced.check('physics.zero_mu_record_jt_exact',
                               r['jt_Ns'] == 0.0, 'zero_mu_record_has_jt',
                               {'tick': tick, 'jt': r['jt_Ns']})

        # full-tick linear ledger closure (the joined ledger)
        ledger_worst = 0.0
        for b in bodies:
            dv = vsub(v_after[b.id], v_start[b.id])
            lhs = tuple(dv) if b.pinned else vscale(dv, b.mass_kg)
            rhs = vadd(press[b.id], trig[b.id])
            rhs = vadd(rhs, tuple(ledger['gravity'].get(b.id,
                                                        (0.0, 0.0, 0.0))))
            rhs = vadd(rhs, tuple(ledger['contact'][b.id]))
            rhs = vadd(rhs, tuple(ledger['anchor'][b.id]))
            ledger_worst = max(ledger_worst, vlen(vsub(lhs, rhs)))
        enforced.check('physics.ledger_closure', ledger_worst <= WIN_LEDGER,
                       'ledger_imbalance_full_tick',
                       {'tick': tick, 'worst': ledger_worst})
        recip = vlen(tuple(ledger['reciprocity_residual']))
        enforced.check('physics.ledger_reciprocity', recip <= WIN_LEDGER,
                       'ledger_imbalance_reciprocity', tick)

        # stack recursion + momentum attribution (P2.1 form)
        free = [b for b in bodies if not b.pinned]
        dp_stack = (0.0, 0.0, 0.0)
        for b in free:
            dp_stack = vadd(dp_stack, vscale(
                vsub(v_after[b.id], v_start[b.id]), b.mass_kg))
        contact_y_sum = naive_sum([ledger['contact'][b.id][1]
                                   for b in free])
        attr_resid = max(abs(dp_stack[1] - jt_all_ground_y),
                         abs(contact_y_sum - jt_all_ground_y))
        enforced.check('physics.stack_attribution', attr_resid <= WIN_MOM,
                       'momentum_attribution_open',
                       {'tick': tick, 'resid': attr_resid})
        dp_body_y = (v_after[prop.id][1] - v_start[prop.id][1]) * prop.mass_kg
        body_attr = abs(dp_body_y - (trig[prop.id][1]
                                     + ledger['contact'][prop.id][1]))
        enforced.check('physics.body_attribution', body_attr <= WIN_MOM,
                       'body_attribution_open',
                       {'tick': tick, 'resid': body_attr})

        # SUPPORT IDENTITY (AMENDMENT-1 A1.3): the WHOLE-PAIR form is the
        # enforced law on SUPPORTED ticks; the hand-only P1.1 residual is
        # RECORDED per tick (it coincides whenever jn_pg == 0, the sealed
        # pairpath S1 case). On separated ticks the S4 exact-zero laws are
        # the enforced set and the support form is not applicable.
        applied_press_down = -naive_sum([press[b.id][2] for b in free])
        support_resid = abs(jn_ground_sum - (applied_press_down
                                             + STACK_WEIGHT_IMP
                                             + dp_stack[2]))
        support_pair_resid = abs(jn_ground_sum + jn_pg_sum
                                 - (applied_press_down + STACK_WEIGHT_IMP
                                    + dp_stack[2]))
        if not separated:
            support_worst = max(support_worst, support_resid)
            enforced.check('physics.support_identity_whole_pair',
                           support_pair_resid <= WIN_LEDGER,
                           'support_whole_pair_broken',
                           {'tick': tick, 'resid': support_pair_resid,
                            'jn_gh_sum': jn_ground_sum,
                            'jn_pg_sum': jn_pg_sum,
                            'dp_stack_z': dp_stack[2],
                            'applied_press_down': applied_press_down,
                            'weight_const': STACK_WEIGHT_IMP,
                            'hand_only_form_resid': support_resid})
        # per-contact signed-z instrumentation (AMENDMENT-1 A1.3 item 3;
        # bounded to the first 64 records per tick)
        contact_rows = []
        for r in records[:64]:
            ia = tuple(r['impulse_on_a'])
            ib = tuple(r['impulse_on_b'])
            na = tuple(r['normal'])
            jn_v_a = vscale(na, r['jn_Ns'])
            jn_v_b = vscale(na, -r['jn_Ns'])
            contact_rows.append(dict(
                pair_key=list(r['pair_key']), body_a=r['body_a'],
                body_b=r['body_b'], kind=r.get('kind'), mode=r.get('mode'),
                jn_Ns=r['jn_Ns'],
                signed_z_a=ia[2], signed_z_b=ib[2],
                normal_z_a=jn_v_a[2], normal_z_b=jn_v_b[2],
                tangent_z_a=ia[2] - jn_v_a[2],
                tangent_z_b=ib[2] - jn_v_b[2]))
        contact_z_stack = naive_sum([ledger['contact'][b.id][2]
                                     for b in free])
        grav_z_stack = naive_sum([ledger['gravity'].get(b.id,
                                                        (0.0, 0.0, 0.0))[2]
                                  for b in free])
        ledger_z_resid = abs(contact_z_stack
                             - (dp_stack[2] + applied_press_down
                                - grav_z_stack))
        enforced.check('physics.support_ledger_z_form',
                       ledger_z_resid <= WIN_LEDGER,
                       'support_ledger_z_broken',
                       {'tick': tick, 'resid': ledger_z_resid,
                        'contact_rows': contact_rows,
                        'hand_plus_prop_signed_z': naive_sum(
                            [contact_rows[i]['signed_z_a']
                             + contact_rows[i]['signed_z_b']
                             for i in range(len(contact_rows))])})
        # AMENDMENT-1 A1.4 falsifiers (constructed triggers; bites recorded)
        if not separated:
            tamper_resid = abs(jn_ground_sum + jn_pg_sum
                               - (applied_press_down + 1e-3
                                  + STACK_WEIGHT_IMP + dp_stack[2]))
            enforced.check('physics.falsifier_press_tamper_bites',
                           tamper_resid >= 1e-3 - WIN_LEDGER,
                           'falsifier_press_tamper_did_not_bite',
                           {'tick': tick, 'resid': tamper_resid})
            prop_drop_resid = abs(jn_ground_sum
                                  - (applied_press_down + STACK_WEIGHT_IMP
                                     + dp_stack[2]))
            falsifiers.append(dict(
                tick=tick,
                press_tamper_bite=tamper_resid >= 1e-3 - WIN_LEDGER,
                prop_ground_drop_resid=prop_drop_resid,
                prop_ground_drop_bites=prop_drop_resid > WIN_LEDGER,
                tangent_z_present=any(abs(cr['tangent_z_a']) > 0.0
                                      or abs(cr['tangent_z_b']) > 0.0
                                      for cr in contact_rows)))


        # pair-per-record friction loss identity
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
        enforced.check('physics.pair_loss_identity',
                       pair_loss_worst <= WIN_LOSS, 'loss_identity_broken',
                       {'tick': tick, 'worst': pair_loss_worst})

        # replay + continuity + energy + stored + ANGULAR + couple
        cont_worst = replay_worst = energy_worst = 0.0
        stored_worst = ang_worst = ang_bound = couple_worst = 0.0
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
            couple = (0.0, 0.0, 0.0)
            for r in records:
                if r['body_a'] == b.id:
                    j_rec = tuple(r['impulse_on_a'])
                    sgn, point = 1.0, tuple(r['point_a'])
                elif r['body_b'] == b.id:
                    j_rec = tuple(r['impulse_on_b'])
                    sgn, point = -1.0, tuple(r['point_b'])
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
                couple = vadd(couple, vcross(vsub(point, c_start[b.id]),
                                             j_rec))
            couple_worst = max(couple_worst, vlen(couple))
            replay_delta = vlen(vsub(v_cur, v_after[b.id]))
            enforced.check('physics.impulse_replay',
                           replay_delta <= WIN_LEDGER,
                           'impulse_replay_incomplete',
                           {'body': b.id, 'tick': tick, 'delta': replay_delta})
            replay_worst = max(replay_worst, replay_delta)
            ke_b = 0.5 * m * vlen(v_after[b.id]) ** 2
            pe_b = m * lc.G * (c_end[b.id][2] - PLANE_Z)
            if prev_state is not None:
                resid_e = (ke_b - prev_state['ke'][b.id]) - \
                    (w_press + w_trig + w_grav + w_contact)
                energy_worst = max(energy_worst, abs(resid_e))
                enforced.check('physics.energy_identity',
                               abs(resid_e) <= WIN_ENERGY,
                               'energy_identity_broken',
                               {'body': b.id, 'tick': tick,
                                'residual_J': resid_e})
                dz = prev_state['cz'][b.id] - c_end[b.id][2]
                body_ccd = any((r['body_a'] == b.id or r['body_b'] == b.id)
                               and r['kind'] == 'ccd' for r in records)
                if not body_ccd:
                    cont = abs(dz + v_after[b.id][2] * lc.DT)
                    cont_worst = max(cont_worst, cont)
                    enforced.check('physics.pose_continuity',
                                   cont <= WIN_CONT, 'pose_continuity_broken',
                                   {'body': b.id, 'tick': tick, 'dz': dz})
                else:
                    budget = (abs(v_start[b.id][2])
                              + abs(press[b.id][2]) / m
                              + abs(trig[b.id][2]) / m + lc.G * lc.DT
                              + sum_abs_dvz)
                    envelope = budget * lc.DT + 2.0 * lc.SLOP_M
                    enforced.check('physics.anti_teleport',
                                   abs(dz) <= envelope, 'kinematic_teleport',
                                   {'body': b.id, 'tick': tick, 'dz': dz,
                                    'envelope': envelope})
                # stored-energy bracket (G07 form, extended with the drive)
                dv_z_contact = ledger['contact'][b.id][2] * inv_m
                bracket = (w_press + w_trig + w_contact
                           - 0.5 * m * (lc.G * lc.DT) ** 2
                           + m * lc.G * lc.DT * dv_z_contact)
                resid_s = ((ke_b + pe_b) - prev_state['kepe'][b.id]) - bracket
                if not body_ccd:
                    stored_worst = max(stored_worst, abs(resid_s))
                    enforced.check('physics.stored_energy',
                                   abs(resid_s) <= WIN_STORED,
                                   'stored_energy_open',
                                   {'body': b.id, 'tick': tick,
                                    'residual_J': resid_s})
                # ANGULAR momentum class (per-tick bound; the joined ledger)
                total_j = vadd(vadd(press[b.id], trig[b.id]),
                               vadd(j_g, tuple(ledger['contact'][b.id])))
                dl_pred = vcross(c_start[b.id], total_j)
                dl_meas = vscale(vcross(c_end[b.id], v_after[b.id]), m)
                dl_meas = vsub(dl_meas, prev_state['L'][b.id])
                resid_a = vlen(vsub(dl_meas, dl_pred))
                vmax = max(vlen(v_start[b.id]), vlen(v_after[b.id]))
                bound = m * 2.0 * vmax * vmax * lc.DT + 1e-15
                ang_worst = max(ang_worst, resid_a)
                ang_bound = max(ang_bound, bound)
                enforced.check('physics.angular_within_bound',
                               resid_a <= bound,
                               'angular_identity_over_bound',
                               {'body': b.id, 'tick': tick, 'resid': resid_a,
                                'bound': bound})
        prev_state = dict(
            ke={b.id: 0.5 * b.mass_kg * vlen(b.velocity) ** 2
                for b in bodies if not b.pinned},
            cz={b.id: c_end[b.id][2] for b in bodies if not b.pinned},
            kepe={b.id: 0.5 * b.mass_kg * vlen(b.velocity) ** 2
                  + b.mass_kg * lc.G * (c_end[b.id][2] - PLANE_Z)
                  for b in bodies if not b.pinned},
            L={b.id: vscale(vcross(c_end[b.id], b.velocity), b.mass_kg)
               for b in bodies if not b.pinned})

        # release rows + separation rows (the exact-zero support law)
        w_press_tick = naive_sum([
            impulse_work(press[b.id], v_start[b.id], b.inv_mass())
            for b in bodies if not b.pinned])
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
        pcs = hand_face.raw.press_channel
        if getattr(pcs, 'latched', False) and hand_b in bodies:
            enforced.check('physics.no_partial_press_after_release',
                           press[hand_b.id] == (0.0, 0.0, 0.0),
                           'partial_press_after_release', tick)
        if getattr(pcs, 'latched', False):
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
                enforced.check('physics.separated_no_records',
                               len(records) == 0, 'support_after_separation',
                               tick)
                enforced.check('physics.separated_w_contact_exact',
                               w_contact_tick == 0.0,
                               'w_contact_not_exact_zero',
                               {'tick': tick, 'w': w_contact_tick})
                enforced.check('physics.separated_w_press_exact',
                               w_press_tick == 0.0, 'w_press_not_exact_zero',
                               {'tick': tick, 'w': w_press_tick})
            separated_rows.append(dict(
                tick=tick, n_records=len(records),
                w_contact_J=w_contact_tick, w_press_J=w_press_tick,
                prop_vz=v_after[prop.id][2], prop_cz=c_end[prop.id][2],
                kind=('landing' if landing_tick == tick else 'fall')))
            if landing_tick is None and tick - separate_at >= 30:
                raise ValueError('no_landing_within_30')

        if parity_traj is not None:
            # the sealed window is the pairpath's rows[SETTLE_TICKS:] = its
            # ticks 6..15; sealed_traj[0] is tick 6
            k = tick - SETTLE_TICKS - 1
            if 0 <= k < len(parity_traj):
                dev = abs(c_end[prop.id][2] - parity_traj[k])
                enforced.check('physics.sealed_trajectory_parity',
                               dev <= 1e-12, 'sealed_trajectory_diverged',
                               {'tick': tick, 'dev_m': dev,
                                'mine': c_end[prop.id][2],
                                'sealed': parity_traj[k]})

        rows.append(dict(
            tick=tick, separated=separated, channel_refused=channel_refused,
            press_total=press_total, n_records=len(records),
            n_seam_records=len(g_recs), calls_tick=calls_tick,
            jn_ground_sum=jn_ground_sum, jn_pg_sum=jn_pg_sum,
            support_pair_resid=support_pair_resid,
            hand_only_resid=support_resid,
            ledger_z_resid=ledger_z_resid,
            contact_z_stack=contact_z_stack, grav_z_stack=grav_z_stack,
            jt_seam_y=jt_seam_y,
            jt_all_ground_y=jt_all_ground_y, dp_stack_y=dp_stack[1],
            dp_stack_z=dp_stack[2], attr_resid=attr_resid,
            body_attr=body_attr, support_resid=support_resid,
            ledger_worst=ledger_worst, recip=recip,
            anchor_resid=anchor_resid, pair_loss_worst=pair_loss_worst,
            replay_worst=replay_worst, cont_worst=cont_worst,
            energy_worst=energy_worst, stored_worst=stored_worst,
            ang_worst=ang_worst, ang_bound=ang_bound,
            couple_worst=couple_worst, w_press_J=w_press_tick,
            w_contact_J=w_contact_tick, prop_cz=c_end[prop.id][2],
            prop_vz=v_after[prop.id][2], prop_cy=c_end[prop.id][1],
            prop_vy=v_after[prop.id][1],
            modes_g=sorted({r['mode'] for r in g_recs})))
        if landing_tick == tick:
            break

    # free-fall closed form across the separated window
    fall = [r for r in separated_rows if r['kind'] == 'fall']
    recursions = [abs(fall[i]['prop_vz'] - fall[i - 1]['prop_vz']
                      + lc.G * lc.DT) for i in range(1, len(fall))]
    fall_worst_recursion = max(recursions) if recursions else 0.0
    enforced.check('physics.freefall_recursion',
                   fall_worst_recursion <= WIN_FALL,
                   'freefall_recursion_broken', fall_worst_recursion)
    m_steps = len(fall) - 1
    if m_steps > 0:
        v_down0 = -fall[0]['prop_vz']
        closed_drop = naive_sum([v_down0 + lc.G * lc.DT * (i + 1)
                                 for i in range(m_steps)]) * lc.DT
        measured_drop = fall[0]['prop_cz'] - fall[-1]['prop_cz']
        enforced.check('physics.freefall_closed_form',
                       abs(measured_drop - closed_drop) <= WIN_FALL,
                       'freefall_closedform_broken',
                       {'measured': measured_drop, 'closed': closed_drop})
    else:
        closed_drop = measured_drop = 0.0
    for row in release_tick_rows:
        if row['separated']:
            enforced.check('physics.release_bars_share_scaled',
                           row['jn_max'] <= release_bar
                           and row['jt_max'] <= release_bar,
                           'release_bar_exceeded', row)

    return dict(scenario=name,
                falsifiers=falsifiers,
                cfg={k: (list(v) if isinstance(v, range) else v)
                     for k, v in cfg.items()},
                share_kg=share_kg, share_kg_hex=float(share_kg).hex(),
                release_bar_ns=release_bar,
                release_bar_hex=float(release_bar).hex(),
                checker_mu_k=checker_mu_k, separated=separated,
                landing_tick=landing_tick, rows=rows,
                release_tick_rows=release_tick_rows,
                separated_rows=separated_rows,
                fall_worst_recursion_mps=fall_worst_recursion,
                fall_closed_drop_m=closed_drop,
                fall_measured_drop_m=measured_drop,
                stick_vt_post_worst_mps=stick_vt_post_worst,
                slip_cap_worst=slip_cap_worst,
                cone_headroom_min=cone_headroom_min_all,
                support_worst=support_worst)


def worst(rows, key):
    return max((abs(r[key]) for r in rows), default=0.0)


def ledger_classes(rows):
    """The P5 class set (computed; the angular bound + the rotation-couple
    disclosure reported, never dropped)."""
    return dict(
        linear=worst(rows, 'ledger_worst'),
        recip=worst(rows, 'recip'),
        anchor_reaction=worst(rows, 'anchor_resid'),
        energy=worst(rows, 'energy_worst'),
        loss_split_pair_per_record=worst(rows, 'pair_loss_worst'),
        replay=worst(rows, 'replay_worst'),
        continuity=worst(rows, 'cont_worst'),
        stored_energy=worst(rows, 'stored_worst'),
        angular=worst(rows, 'ang_worst'),
        angular_bound=worst(rows, 'ang_bound'),
        unmodeled_rotation_couple=worst(rows, 'couple_worst'),
        rows_with_couple_reported=sum(1 for r in rows
                                      if 'couple_worst' in r))


def run_physics_leg(enforced):
    """Leg A: the pairpath fixture clauses at the pinned inputs."""
    global STACK_WEIGHT_IMP
    STACK_WEIGHT_IMP = (HAND_MASS_KG + BODY_MASS_KG) * lc.G * lc.DT
    hand = parse_hand_vtp()
    _gen, _hf0, _gf0, context, _gates, _mods = pair_context_and_faces()
    pp = json.loads(pathlib.Path(PAIRPATH_PATH).read_text(
        encoding='utf-8'))
    sealed_traj = pp['verdicts']['S1_support']['P1.2_body_seated'][
        'prop_cz_trajectory']
    results = {}
    for name, cfg in SCENARIOS.items():
        faces = (adapters_fresh_hand(context), adapters_fresh_ground(context))
        results[name] = run_scenario(name, hand, cfg, faces, enforced,
                                     parity_traj=(sealed_traj
                                                  if name == 'SC1_counted_once'
                                                  else None))
    # F2: the EXECUTED tampered replay through the FULL pipeline. The cap
    # check MUST fail inside the tampered arm; the FAIL is the discriminator.
    tamper = None
    faces = (adapters_fresh_hand(context), adapters_fresh_ground(context))
    try:
        results['TAMPERED_SLIP'] = run_scenario(
            'TAMPERED_SLIP', hand, TAMPERED_SLIP_CFG, faces, enforced)
    except ValueError as exc:
        msg = str(exc.args[0] if exc.args else exc)
        require('tampered_arm_unexpected_pass' not in msg,
                'tampered_arm_unexpected_pass', None)
        tamper = dict(bit=True, refusal=msg[:400],
                      checker_mu_k=TAMPERED_SLIP_CFG['checker_mu_k'],
                      declared_mu_k=S3_MU[1])
    enforced.check('physics.tampered_replay_bit', tamper is not None,
                   'tampered_arm_did_not_bite', tamper)
    enforced.check('physics.tampered_arm_is_cap_identity',
                   tamper is not None
                   and 'slip_cap_not_pair_mu_k' in tamper['refusal'],
                   'tampered_arm_wrong_failure', tamper)

    sc1 = results['SC1_counted_once']
    sc2l = results['SC2_slip']
    sc3r = results['SC3_slip_reduced']
    sc2b = results['SC2b_zero_mu']
    sc3 = results['SC3_release']

    # SEALED-SCENE PARITY: my SC1 prop trajectory against the pairpath's
    # published P1.2 per-tick list (loaded from the pinned store bytes)
    pp = json.loads(pathlib.Path(PAIRPATH_PATH).read_text(
        encoding='utf-8'))
    sealed_traj = pp['verdicts']['S1_support']['P1.2_body_seated'][
        'prop_cz_trajectory']
    my_traj = [r['prop_cz'] for r in sc1['rows'][SETTLE_TICKS:
                                                SETTLE_TICKS
                                                + len(sealed_traj)]]
    traj_dev = max((abs(a - b) for a, b in zip(my_traj, sealed_traj)),
                   default=1.0)
    enforced.check('physics.sealed_scene_trajectory_parity_summary',
                   len(my_traj) == len(sealed_traj),
                   'sealed_scene_trajectory_window_mismatch',
                   {'max_dev_m': traj_dev,
                    'windows_compared': len(sealed_traj)})
    support_rows = sc1['rows'][SETTLE_TICKS:]
    support = dict(
        worst_exact_resid=max(r['support_resid'] for r in support_rows),
        worst_transient_dp_stack_z=worst(support_rows, 'dp_stack_z'),
        window='ticks %d..%d' % (support_rows[0]['tick'],
                                 support_rows[-1]['tick']),
        stack_weight_impulse_per_tick=STACK_WEIGHT_IMP,
        press_total_ns_per_tick=PRESS_NS * float(N_CHANNELS),
        worst_pair_level_resid=worst(support_rows, 'support_pair_resid'),
        worst_jn_pg=sum(r['jn_pg_sum'] for r in support_rows),
        sealed_trajectory_parity=dict(
            max_dev_m=traj_dev,
            windows=len(sealed_traj),
            sealed_reference='pairpath_result.json S1 P1.2 '
                             'prop_cz_trajectory'),
        note='the exact identity carries the MEASURED stack momentum; the '
             'steady-form transient is reported, not assumed zero')
    all_falsifiers = []
    for s in results.values():
        all_falsifiers.extend(s['falsifiers'])
    falsifier_summary = dict(
        press_tamper_bites=sum(1 for f in all_falsifiers
                               if f['press_tamper_bite']),
        supported_ticks=len(all_falsifiers),
        prop_ground_drop_bites=sum(1 for f in all_falsifiers
                                   if f['prop_ground_drop_bites']),
        prop_ground_drop_bite_ticks=[f['tick'] for f in all_falsifiers
                                     if f['prop_ground_drop_bites']][:8],
        tangent_z_seen_ticks=sum(1 for f in all_falsifiers
                                 if f['tangent_z_present']))
    dwin = [r for r in sc2l['rows'] if 16 <= r['tick'] <= 25]
    propulsion = dict(
        jt_ground_y_min=min(r['jt_seam_y'] for r in dwin),
        jt_ground_y_max=max(r['jt_seam_y'] for r in dwin),
        worst_stack_attr=worst(dwin, 'attr_resid'),
        worst_body_attr=worst(dwin, 'body_attr'),
        drive_rows=len(dwin))
    slip_dwin = [r for r in sc3r['rows'] if 16 <= r['tick'] <= 25]
    slip_rows_n = sum(1 for r in slip_dwin if 'slip' in r['modes_g'])
    nominal_max = worst(dwin, 'jt_seam_y')
    slip = dict(
        slip_rows=slip_rows_n,
        nominal_jt_max=nominal_max,
        reduced_jt_abs_max=worst(slip_dwin, 'jt_seam_y'),
        slip_cap_worst=sc3r['slip_cap_worst'],
        traction_reduced=bool(worst(slip_dwin, 'jt_seam_y') < nominal_max))
    zero_dwin = [r for r in sc2b['rows'] if r['tick'] >= 5]
    zero_mu = dict(
        jt_ground_y_abs_max=worst(zero_dwin, 'jt_seam_y'),
        dp_stack_y_abs_max=worst(zero_dwin, 'dp_stack_y'),
        drive_rows=len(zero_dwin))
    fall_rows = [r for r in sc3['separated_rows'] if r['kind'] == 'fall']
    separation = dict(
        n_separated_ticks=len(fall_rows),
        all_exact=all(r['n_records'] == 0 and r['w_contact_J'] == 0.0
                      and r['w_press_J'] == 0.0 for r in fall_rows),
        landing_tick=sc3['landing_tick'],
        fall_worst_recursion_mps=sc3['fall_worst_recursion_mps'],
        fall_closed_drop_m=sc3['fall_closed_drop_m'],
        fall_measured_drop_m=sc3['fall_measured_drop_m'],
        worst_separated_release_jn=max(
            (r['jn_max'] for r in sc3['release_tick_rows']
             if r['separated']), default=0.0),
        worst_separated_release_jt=max(
            (r['jt_max'] for r in sc3['release_tick_rows']
             if r['separated']), default=0.0),
        release_bar_ns=sc3['release_bar_ns'])
    every_rows = []
    for s in results.values():
        every_rows.extend(s['rows'])
    classes = ledger_classes(every_rows)
    return dict(scenarios=results, support=support, propulsion=propulsion,
                slip=slip, zero_mu=zero_mu, separation=separation,
                ledger_classes=classes, tampered_replay=tamper,
                falsifiers=falsifier_summary,
                share_kg=HAND_MASS_KG, share_kg_hex=float(HAND_MASS_KG).hex(),
                release_bar_ns=RELEASE_BAR_NS,
                release_bar_hex=float(RELEASE_BAR_NS).hex())


# ---- the contract conformance gate (the frozen bytes are the authority) -----

def verify_contract(enforced):
    contract = json.loads(pathlib.Path(CONTRACT_PATH).read_text(
        encoding='utf-8'))
    decl = json.loads(pathlib.Path(DECL_PATH).read_text(encoding='utf-8'))
    w03 = json.loads(pathlib.Path(W03_PATH).read_text(encoding='utf-8'))
    f05c = json.loads(pathlib.Path(F05_COMPOSED_PATH).read_text(
        encoding='utf-8'))
    eps = {(e['membrane'], e['port'], e['role'])
           for e in contract['endpoints']}
    enforced.check('contract.endpoints',
                   eps == {(HAND_ID, 'port.grip_contact', 'a'),
                           (GROUND_ID, 'port.walk_surface_contact', 'b')},
                   'endpoints', eps)
    qrefs = tuple(q['quantity_id'] for q in contract['exchanged_quantities'])
    enforced.check('contract.quantities',
                   qrefs == ('jn', 'jt', 'press_channel_state'), 'quantities',
                   qrefs)
    own = {o['quantity_id']: o['owner_membrane']
           for o in contract['state_ownership']}
    enforced.check('contract.ownership',
                   own == {'jn': GROUND_ID, 'jt': GROUND_ID,
                           'press_channel_state': HAND_ID}, 'ownership', own)
    timing = contract['timing']
    enforced.check('contract.timing_dt',
                   float(timing['tick_dt_s']) == lc.DT
                   and int(timing['tick_rate_hz']) == 300, 'timing_dt', None)
    enforced.check('contract.stage_order',
                   tuple(timing['stage_order']) == ('pressure', 'material',
                                                    'contact'),
                   'stage_order', None)
    enforced.check('contract.release_latch_declared',
                   any(l['latch_id'] == 'press_release_latch'
                       for l in timing['latches']), 'latch', None)
    rules = {r['rule_id'] for r in contract['pair_rules']}
    enforced.check('contract.pair_rules',
                   rules == {'pair_friction_elementwise_min',
                             'counted_once_reciprocity',
                             'separation_removes_support'}, 'pair_rules',
                   rules)
    absent = {row['name']: row['status'] for row in contract['named_absent']}
    enforced.check('contract.named_absent',
                   absent.get('x_press') == 'ABSENT'
                   and absent.get('x_share') == 'ABSENT'
                   and absent.get('x_reach') == 'ABSENT', 'named_absent',
                   absent)
    params = {p['param']: p for p in contract['contract_parameters']}
    enforced.check('contract.mu_placeholders',
                   params['mu_s']['value'] == MU_S
                   and params['mu_k']['value'] == MU_K
                   and params['mu_s']['binding_class'] == 'NAMED_PLACEHOLDER',
                   'mu_values', None)
    enforced.check('contract.press_operating_point',
                   params['press_channel_jn_ns_per_tick']['value'] == PRESS_NS
                   and params['operating_force_N']['value'] == PRESS_NS / lc.DT,
                   'press', None)
    enforced.check('contract.release_bar_form',
                   params['release_bar_ns']['value']
                   == 'share_kg * 1e-10 per release tick', 'release_bar',
                   None)
    enforced.check('contract.pair_friction_rule',
                   params['pair_friction_rule']['value'] == 'elementwise_min',
                   'pair_friction_rule', None)
    recipe = w03['gait_controller']['recipe']
    enforced.check('contract.w03_plane',
                   float(recipe['contact_plane_height_m']) == PLANE_Z,
                   'w03_plane', None)
    enforced.check('contract.w03_friction',
                   float(recipe['contact_friction']) == MU_S, 'w03_friction',
                   None)
    flat = f05c['transform']['reground']['flatten']
    enforced.check('contract.f05_plateau',
                   float(flat['plateau_z_m']) == PLANE_Z, 'f05_plateau', None)
    conn = decl['connections'][0]
    enforced.check('contract.declaration_connection',
                   conn['connection_id'] == CONNECTION_ID,
                   'declaration_connection', None)
    return {'contract_conformant': True,
            'rows_checked': enforced.count(),   # F1: computed
            'contract_sha256': CONTRACT_SHA,
            'g_convention': 'record-g 9.81 pinned solver; std-g 9.80665 '
                            'reference arithmetic only'}


# ---- main ---------------------------------------------------------------------

def main():
    global lc, STACK_WEIGHT_IMP
    out_dir = os.environ.get('CHIMERA_OUTPUT_DIR')
    require(bool(out_dir), 'chimera_output_dir_missing')
    os.chdir(HERE)   # the substrate's relative pin law (pinned_inputs/...)

    sr = load_module(HERE / 'spec_runtime.py', 'pair_spec_runtime')
    sr.require_pins()

    pins = {}
    for role, path, sha in (
            ('local_contact', LC_PATH, LC_SHA),
            ('g04_grip_module', GC_PATH, GC_SHA),
            ('contract', CONTRACT_PATH, CONTRACT_SHA),
            ('declaration', DECL_PATH, DECL_SHA),
            ('pairpath_result', PAIRPATH_PATH, PAIRPATH_SHA),
            ('pairpath_prereg', PAIRPATH_PREREG_PATH, PAIRPATH_PREREG_SHA),
            ('conn_seam', CONN_SEAM_PATH, CONN_SEAM_SHA),
            ('a05_record', A05_PATH, A05_SHA),
            ('f05_composed_meta', F05_COMPOSED_PATH, F05_COMPOSED_SHA),
            ('f05_terrain_meta', F05_TERRAIN_PATH, F05_TERRAIN_SHA),
            ('w03_scene', W03_PATH, W03_SHA),
            ('hand_vtp', HAND_PATH, HAND_SHA),
            ('generated_bindings', HERE / BINDINGS_REL, BINDINGS_SHA),
            ('generated_wiring', HERE / WIRING_REL, WIRING_SHA)):
        pins[role] = pin_file(path, sha, role)
    # the wrapped published modules are hash-verified by their own gates at
    # every build; their landed identities are recorded (computed, F1):
    pins['hand_membrane_module'] = sha_file(
        HERE / 'hand/CMP-MEM-HAND-20261004/hand_membrane_v1.py')
    pins['ground_membrane_module'] = sha_file(
        HERE / 'ground/membrane_ground.py')
    # the sibling published results (recorded identities, not gated here)
    component_publication = dict(
        conn_seam_sha256=CONN_SEAM_SHA,
        conn_result_sha256=sha_file(CONN_RESULT_PATH),
        hand_packet_result_sha256=sha_file(
            CO + '/membrane-hand/COMPILER_PACKET_RESULT.json'),
        ground_result_sha256=sha_file(CO + '/membrane-ground/result.json'))

    global lc, gc
    lc = load_module(LC_PATH, 'pair_pinned_local_contact')
    gc = load_module(GC_PATH, 'pair_pinned_g04_grip')
    arm_call_counter(lc)
    STACK_WEIGHT_IMP = (HAND_MASS_KG + BODY_MASS_KG) * lc.G * lc.DT

    enforced = Enforced()
    conformance = verify_contract(enforced)

    # F3: the mantissa discipline (computed + hex-recorded + packet check)
    mantissa = dict(
        body_mass_kg=BODY_MASS_KG,
        n_channels=N_CHANNELS,
        share_kg=HAND_MASS_KG,
        share_kg_hex=float(HAND_MASS_KG).hex(),
        packet_fixture_share_kg=PACKET_FIXTURE_SHARE_KG,
        packet_fixture_share_hex=float(PACKET_FIXTURE_SHARE_KG).hex(),
        bitwise_match=float(HAND_MASS_KG) == float(PACKET_FIXTURE_SHARE_KG),
        release_bar_ns=RELEASE_BAR_NS,
        release_bar_hex=float(RELEASE_BAR_NS).hex(),
        law='share_kg = BODY_MASS_KG / 3.0 COMPUTED (never a retyped '
            'literal); release bar = share_kg * 1e-10 (F3)')
    enforced.check('mantissa.share_kg_bitwise_packet_fixture',
                   mantissa['bitwise_match'], 'share_kg_retyped', mantissa)

    regen = wiring_regeneration_identity()
    scene = run_scene(enforced)
    physics = run_physics_leg(enforced)

    # ---- the acceptance rows (the packet's checks ARE the falsifiers) ----
    per_test = []

    def row(test_id, ok, observed, window):
        per_test.append(dict(test_id=test_id,
                             verdict='PASS' if ok else 'FAIL',
                             observed=observed, window=window,
                             evidence_path='outputs/pair_result.json'))
        return ok

    ph = physics
    sup = ph['support']
    ok_support = row(
        'T.ASMB_support', sup['worst_exact_resid'] <= WIN_LEDGER,
        'support identity across the pair (pairpath P1.1 form): jn == press '
        '(%r N*s = the hand channel %r x n=%d) + weight stack (%r N*s/tick) '
        '+ measured dp_stack_z; worst exact resid %r N*s over %s; '
        'steady-form transient dp_stack_z worst %r reported' % (
            sup['press_total_ns_per_tick'], PRESS_NS, N_CHANNELS,
            sup['stack_weight_impulse_per_tick'], sup['worst_exact_resid'],
            sup['window'], sup['worst_transient_dp_stack_z']),
        '1e-12 (exact identity; steady-form transient reported)')
    pa = ph['propulsion']
    ok_prop = row(
        'T.ASMB_propulsion_attribution',
        pa['jt_ground_y_min'] > 0.0 and pa['worst_stack_attr'] <= WIN_MOM
        and pa['worst_body_attr'] <= WIN_MOM,
        'push-off positive and attributed on %d drive ticks: jt_ground_y in '
        '[%r, %r] > 0; stack attribution worst %r N*s; body attribution '
        'worst %r N*s (both <= 1e-12)' % (
            pa['drive_rows'], pa['jt_ground_y_min'], pa['jt_ground_y_max'],
            pa['worst_stack_attr'], pa['worst_body_attr']),
        '1e-12')
    sl = ph['slip']
    ok_slip = row(
        'T.ASMB_slip',
        sl['slip_rows'] > 0 and sl['slip_cap_worst'] == 0.0
        and sl['traction_reduced'],
        'at the declared reduced mu (0.12/0.08) the ground slips at the '
        'per-record cap jt == mu_k*jn exactly (worst dev %r N*s over %d '
        'drive ticks with slip records); traction strictly reduced: jt abs '
        'max %r < nominal %r (measured-vs-measured)' % (
            sl['slip_cap_worst'], sl['slip_rows'], sl['reduced_jt_abs_max'],
            sl['nominal_jt_max']),
        'measured-vs-measured (sealed pairpath S3 reference: '
        '0.08779835116465305 == 0.08 * 1.0974793895581632)')
    zm = ph['zero_mu']
    ok_zero = row(
        'T.ASMB_zero_mu_control',
        zm['jt_ground_y_abs_max'] == 0.0
        and zm['dp_stack_y_abs_max'] <= WIN_MOM,
        'zero-mu control: every seam record jt == 0.0 exactly; stack '
        'y-momentum stays within %r N*s across %d drive ticks '
        '(traction-borne propulsion discriminated)' % (
            zm['dp_stack_y_abs_max'], zm['drive_rows']),
        'exact 0')
    sep = ph['separation']
    ok_sep = row(
        'T.ASMB_separation',
        sep['n_separated_ticks'] > 0 and sep['all_exact']
        and sep['fall_worst_recursion_mps'] <= WIN_FALL
        and sep['landing_tick'] is not None,
        'separation removes support: %d fall ticks with NO records, '
        'W_contact == W_press == 0.0 J exactly; free-fall recursion worst %r '
        'm/s; closed-form drop %r m vs measured %r m; landing recorded '
        'transient at tick %r (never support); release bars share_kg*1e-10 '
        '= %r N*s satisfied (separated worsts jn %r / jt %r)' % (
            sep['n_separated_ticks'], sep['fall_worst_recursion_mps'],
            sep['fall_closed_drop_m'], sep['fall_measured_drop_m'],
            sep['landing_tick'], sep['release_bar_ns'],
            sep['worst_separated_release_jn'],
            sep['worst_separated_release_jt']),
        '1e-9 free-fall')
    classes = ph['ledger_classes']
    ok_classes = row(
        'T.ASMB_ledger_classes',
        classes['linear'] <= WIN_LEDGER and classes['recip'] <= WIN_LEDGER
        and classes['anchor_reaction'] <= WIN_LEDGER
        and classes['energy'] <= WIN_ENERGY
        and classes['loss_split_pair_per_record'] <= WIN_LOSS
        and classes['replay'] <= WIN_LEDGER
        and classes['continuity'] <= WIN_CONT
        and classes['stored_energy'] <= WIN_STORED
        and classes['angular'] <= classes['angular_bound']
        and classes['unmodeled_rotation_couple'] > 0.0,
        'all ledger classes inside declared windows across %d scenario rows: '
        'linear %r; reciprocity %r; anchor %r; energy %r; pair loss %r; '
        'replay %r; continuity %r; stored %r; angular %r within per-tick '
        'bound %r; unmodeled_rotation_couple %r REPORTED EVERY TICK (%d '
        'rows; the translation-only body line disclosure, never dropped)' % (
            classes['rows_with_couple_reported'], classes['linear'],
            classes['recip'], classes['anchor_reaction'], classes['energy'],
            classes['loss_split_pair_per_record'], classes['replay'],
            classes['continuity'], classes['stored_energy'],
            classes['angular'], classes['angular_bound'],
            classes['unmodeled_rotation_couple'],
            classes['rows_with_couple_reported']),
        '1e-12 / 1e-9 / angular bounds')
    ok_scene = row(
        'T.ASMB_runtime_scene',
        all(p['bit'] for p in scene['probes'])
        and scene['writer_scoping_rows'] >= 2
        and scene['contract_groups_coverage']['coverage'] == 9
        and enforced.all_held('scene.'),
        'the co-instantiated ABI scene through the GENERATED wiring (sha '
        '%s): both PUBLISHED membranes built under their own spec-of-record '
        'contexts; graph_runtime.validate_built_graph conformant with %d '
        'writer-scoping rows; contract groups coverage %d/9 (valid=%s); '
        'per-window one-quantity bitwise proofs in BOTH declared cases '
        '(armed %d windows / released %d windows, constant-record scene '
        'shape); the ground\'s OWN laws derive the record from the hand\'s '
        'published decision bitwise every window; the REAL release-latch '
        'arc on the scene\'s own channels (release -> silent re-arm '
        'refused -> explicit re-arm -> the re-armed decision verified); '
        '%d/%d refusal probes bit (incl. abi_exchange_writer_violation, '
        'ref.ground.jn_negative_press_record, composition_unwired); '
        'composition-owned pieces labeled: %s' % (
            WIRING_SHA[:8], scene['writer_scoping_rows'],
            scene['contract_groups_coverage']['coverage'],
            scene['contract_groups_coverage']['valid'],
            scene['armed_windows'], scene['released_windows'],
            scene['probes_bit'], scene['probes_count'],
            '; '.join(scene['composition_owned_pieces'])),
        'seam law + sealed falsifier pattern')

    all_ok = all(r['verdict'] == 'PASS' for r in per_test)
    receipt = dict(
        schema=SCHEMA, lane=LANE, packet_id=PACKET_ID,
        criteria_sha256=CRITERIA_SHA256,
        contract=dict(id='pc.hand_ground_contact.v1', version='1.0.0',
                      sha256=CONTRACT_SHA),
        prereg='PREREGISTRATION.md (seal 1, manifest '
               '91f1994de4f014326b03ff7c881b2c6aa1c75507d0463d817b0289ff66c6'
               '9bd3, sealed ALONE before any run code)',
        pins=pins,
        component_publication=component_publication,
        conformance=conformance,
        enforced_rows=enforced.rows,
        enforced_rows_count=enforced.count(),
        wiring_regeneration=regen,
        mantissa_discipline=mantissa,
        scene=scene, physics=physics,
        carried_findings=dict(
            F1_computed_counts='all counts computed from the enforced '
                               'list/store log (conformance rows %d, scene '
                               'probes %d, placement rows %d)' % (
                                   enforced.count(),
                                   len(scene['probes']),
                                   regen['plan_placement_rows']),
            F2_executed_tampered_replay=physics['tampered_replay'],
            F3_mantissa_discipline=mantissa,
            F4_deviations='all deviations land in result.json deviations'),
        obligations=dict(
            X1_press_channel_entry='sealed_upstream (hand membrane, G04 X1)',
            X2_friction_pair='re-verified here in the physics pair run '
                             '(fixture-based)',
            X4_release='re-verified here (share-scaled bars + exact zeros)',
            G07_accounted_release='re-verified here (separation leg; '
                                  'fixture-based)',
            G05_observation_seam='sealed_upstream (hand membrane; the '
                                 'observation delivery is not re-exercised '
                                 'in this pair scene)',
            pair_run='advanced by THIS run: the fixture clauses sealed as '
                     'the assembled pair + the co-instantiated runtime '
                     'scene built/stepped through the generated wiring; '
                     'the store/registry advance of declared_pending stays '
                     'with the Lieutenant (never by self-claim)'),
        named_absent_respected=dict(
            x_press='ABSENT (NB-03): declared fixture press only; '
                    'actuator_qualified false',
            x_share='ABSENT (NB-04): the computed share scales the release '
                    'bars only',
            x_reach='ABSENT (NB-05): translation-only placements; no '
                    'transform composed'),
        fixtures=dict(
            fx_trial_inertia=dict(hand_mass_kg=HAND_MASS_KG, n=N_CHANNELS,
                                  cls='AUTHORED_DECLARED'),
            fx_trial_placement='translation-only per A09 frame law '
                               '(x_reach ABSENT)',
            fx_mu_placeholders=dict(mu_s=MU_S, mu_k=MU_K,
                                    blockers=['NB-01', 'NB-02'],
                                    cls='NAMED_PLACEHOLDER'),
            fx_reduced_mu=dict(values=list(S3_MU),
                               cls='DECLARED_FALSIFIER_VALUES (pairpath S3 '
                                   'form; never a re-pin)'),
            fx_tangential_trigger=dict(stick_ns=TANGENT_STICK_NS,
                                       slip_ns=TANGENT_SLIP_NS,
                                       cls='AUTHORED_DECLARED'),
            fx_separation_event=dict(form='pairpath S4 declared removal',
                                     cls='AUTHORED_DECLARED')),
        physlang_v0_refusal='not triggered: no derivation in this battery '
                            'outruns the pinned inputs (the clause stays '
                            'recorded and applicable)',
        fixture_based=True,
        in_run_deviations=[],
        per_test_results=per_test,
        all_fatal_pass=all_ok)
    out = pathlib.Path(out_dir) / 'pair_result.json'
    out.write_text(json.dumps(receipt, indent=1, ensure_ascii=False,
                              allow_nan=False), encoding='utf-8')
    print('WROTE', out, out.stat().st_size, 'bytes')
    for r in per_test:
        print('VERDICT', r['test_id'], r['verdict'])
    print('PREDICTIONS pass=%d fail=%d enforced_rows=%d' % (
        sum(1 for r in per_test if r['verdict'] == 'PASS'),
        sum(1 for r in per_test if r['verdict'] != 'PASS'),
        enforced.count()))
    require(all_ok, 'acceptance_checks_failed',
            [r['test_id'] for r in per_test if r['verdict'] != 'PASS'])


if __name__ == '__main__':
    main()
