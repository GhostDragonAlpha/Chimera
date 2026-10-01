"""MAT2-G05 contact/support observation interface (PREREGISTRATION.md,
frozen).

done_when: "Controller receives only declared measurable contact/pose
signals with explicit timing". Observation: "No hidden simulator
information represented as sensed information".

Three established interfaces, each imported at run time, hash-asserted
against its frozen pin, and never forked:

- THE SOLVER: MAT2-M06 ``chimera.local_contact.v1`` (via G04's pinned
  loader). Every impulse in this card comes from ``lc.solve_tick``.
- THE GRIP PHYSICS + FIXTURE: MAT2-G04's sealed ``grip_contact.py`` (the
  exact revision merged in PR #298). G05 consumes its fixture builders,
  press channel, closed forms, named-absent list and window set. G05 adds
  NO physics and NO fixture constant of its own.
- THE FROZEN OBSERVATION CONTRACT (W04, TC-2): ``observation_interface_v2``
  (policy-interface/2.0.0, dim 80, OBS_SCHEMA_VERSION 2). G05 does NOT
  extend or re-declare the 80-field walking interface (its owner is W04);
  G05 declares the TASK-OWNED grasp-side table below, which composes with
  the frozen contract's DECLARED LAWS (fixed dim, fixed order, float32
  dtype, declared source per field, availability recipe, privileged_
  forbidden, zero un-declared history) and pins the contract bytes.

The deliverable:

- OBS_FIELDS: the declared 32-slot float32 vector (fixed order, every slot
  with unit, frame, source trace key, and an explicit alias row where one
  recorded quantity feeds more than one slot -- the C21 aliasing law).
- The TIMING BLOCK: tick, phase, dt, seconds -- explicit on every sample.
- ObservationSeam: the ONLY channel the controller receives. It refuses
  undeclared fields, unbound/drifted timing, occupied absent slots,
  privileged sources, non-finite values and dimension mismatch with named
  codes. Nothing is silently repaired.
- observe_scenario: a G05-owned tick loop performing EXACTLY the sealed
  G04 per-tick operations in the same order, additionally measuring the
  pad centroid poses from the pinned body state, cross-validated
  bit-identical against ``gc.run_scenario`` (refusal ``observer_drift``).

CPU-only, stdlib-only, deterministic (no RNG, no wall clock).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parent

SCHEMA = 'chimera.g05_obs.v1'

# ---- the established interfaces (imported, hash-asserted, never forked) ----
G04_MODULE_REL = '../MAT2-G04/grip_contact.py'
G04_MODULE_SHA256 = ('0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b'
                     '4173d69245')
CONTRACT_HOST = ('E:/ChimeraWork/pass3-integ/repo/tools/science_funnel/'
                 'validation/policy_interface_freeze_20260920/'
                 'observation_interface_v2.json')
CONTRACT_SHA256 = ('e8c2d698dee0337414c48e8d2f6569c45f6f61828dabdeff6a4f1188'
                   'b1c0671c')


def load_g04_module(rel=G04_MODULE_REL, expected_sha=G04_MODULE_SHA256):
    """Import the pinned G04 module after asserting its bytes.
    Refusals: interface_pin_missing / interface_pin_drift."""
    path = (HERE / rel).resolve()
    if not path.exists():
        raise ValueError('interface_pin_missing:' + str(path))
    raw = path.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != expected_sha:
        raise ValueError('interface_pin_drift:' + got)
    spec = importlib.util.spec_from_file_location('g05_pinned_grip_contact',
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_contract(host=CONTRACT_HOST, expected_sha=CONTRACT_SHA256):
    """Load the pinned W04 TC-2 observation contract after asserting its
    bytes and its frozen law fields. Refusals: contract_pin_missing /
    contract_pin_drift / contract_law_drift."""
    path = pathlib.Path(host)
    if not path.exists():
        raise ValueError('contract_pin_missing:' + host)
    raw = path.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != expected_sha:
        raise ValueError('contract_pin_drift:' + got)
    doc = json.loads(raw.decode('utf-8'))
    law = {
        'kind': doc.get('kind'),
        'interface_freeze_version': doc.get('interface_freeze_version'),
        'obs_schema_version': doc.get('obs_schema_version'),
        'dim': doc.get('dim'),
        'legacy_dim': doc.get('legacy_dim'),
        'dtype': doc.get('dtype'),
        'privileged_forbidden': doc.get('privileged_forbidden'),
        'history_ticks': doc.get('history_ticks'),
        'availability_recipe': doc.get('availability_recipe'),
        'fields': len(doc.get('fields', [])),
    }
    expected = {'kind': 'policy_observation_interface',
                'interface_freeze_version': 'policy-interface/2.0.0',
                'obs_schema_version': 2, 'dim': 80, 'legacy_dim': 64,
                'dtype': 'float32', 'privileged_forbidden': True,
                'history_ticks': 0, 'fields': 80}
    for key, want in expected.items():
        if key == 'availability_recipe':
            if not law[key]:
                raise ValueError('contract_law_drift:' + key)
            continue
        if law[key] != want:
            raise ValueError('contract_law_drift:' + key)
    return doc, law


# ---- the declared timing block (explicit on every sample) ----
TIMING_KEYS = ('t_tick', 't_phase', 't_dt_s', 't_seconds')
PHASES = ('hold', 'release')


# ---- the declared vector table (32 slots, fixed order, float32) ----
# Declared aliasing law: when one recorded quantity feeds more than one
# slot, EVERY slot in the group carries a non-empty alias row; the audit
# refuses undeclared shared sources (C21 aliasing test).
_CH_SPECS = tuple(
    (k, suffix, meaning, unit, source, alias)
    for k in range(3)
    for (suffix, meaning, unit, source, alias) in (
        ('contact_flag',
         '1.0 iff pad %d recorded at least one contact record this tick',
         '1', 'pads[%d].mode', 'recorded mode: the contact/no-contact '
         'projection (group primary; stick/slip flags alias it)'),
        ('stick_flag', '1.0 iff pad %d recorded mode stick this tick',
         '1', 'pads[%d].mode', 'projection of pads[%d].mode (disjoint with '
         'slip_flag)'),
        ('slip_flag', '1.0 iff pad %d recorded mode slip this tick',
         '1', 'pads[%d].mode', 'projection of pads[%d].mode (disjoint with '
         'stick_flag)'),
        ('jn_Ns', 'pad %d recorded normal impulse sum this tick',
         'N*s', 'pads[%d].jn_sum_Ns', 'recorded impulse sum (group primary; '
         'contact_force_N aliases it via the declared /dt conversion)'),
        ('jt_Ns', 'pad %d recorded tangential impulse sum this tick',
         'N*s', 'pads[%d].jt_sum_Ns', ''),
        ('contact_force_N', 'pad %d declared normal force jn/dt this tick',
         'N', 'pads[%d].jn_sum_Ns', 'alias_of pads[%d].jn_sum_Ns via the '
         'declared conversion /dt'),
        ('disp_down_cum_m', 'pad %d cumulative downward displacement',
         'm', 'pads[%d].disp_down_m_cum', ''),
        ('centroid_z_m', 'pad %d measured centroid z (pinned body state; '
         'cross-checked against z0_k - disp_down_cum)', 'm',
         'body[%d].vertices (measured)', ''),
    ))


def _build_fields():
    fields = []
    for k, suffix, meaning, unit, source, alias in _CH_SPECS:
        fields.append({
            'index': len(fields), 'name': 'ch%d_%s' % (k, suffix),
            'group': 'contact_support_channel', 'meaning': meaning % (k,),
            'unit': unit, 'frame': 'm06_experiment_z_up',
            'source': source % (k,), 'alias': (alias % (k,) if '%d' in alias
                                               else alias),
            'dtype': 'float32', 'privileged': False,
            'availability': 'unavailable for k >= n_channels; declared '
                            'fill 0.0'})
    aggregates = (
        ('agg_support_count', 'count of AVAILABLE channels in recorded '
         'stick mode this tick', '1', 'pads[k].mode (count)', '', False),
        ('agg_supported_flag', '1.0 iff every available channel is stick '
         'AND phase hold (the declared support law; a slip channel is '
         'honestly NOT supported)', '1', 'pads[k].mode + t_phase', '', False),
        ('agg_release_flag', '1.0 iff phase release (the press channel is '
         'off; support removed)', '1', 't_phase', 'alias_of t_phase '
         '(declared projection)', False),
        ('agg_trunk_anchor_z_Ns', 'recorded trunk anchor reaction z '
         '(the VISIBLE recorded root anchor)', 'N*s',
         'ledger.trunk_anchor[2]', '', False),
        ('agg_ledger_residual_max_Ns', 'full-tick identity residual this '
         'tick (the integrity signal)', 'N*s',
         'ledger.residual_full_max', '', False),
        ('agg_reciprocity_max_Ns', 'max |reciprocity residual| this tick '
         '(the recorded action-reaction integrity signal)', 'N*s',
         'ledger.reciprocity_residual (max abs)', '', False),
        ('obs_mask_mean', 'mean availability over the 32 vector slots '
         'this tick', '1', 'availability_mask', 'recorded availability '
         'mask (group primary; obs_frac_avail is the group-level '
         'projection)', False),
        ('obs_frac_avail', 'fraction of slot GROUPS with any available '
         'source this tick (W04 sensor-health law composition)', '1',
         'availability_mask', 'same recorded mask as obs_mask_mean; '
         'declared group-level projection', False),
    )
    for name, meaning, unit, source, alias, priv in aggregates:
        fields.append({'index': len(fields), 'name': name,
                       'group': 'contact_support_aggregate',
                       'meaning': meaning, 'unit': unit,
                       'frame': 'm06_experiment_z_up', 'source': source,
                       'alias': alias, 'dtype': 'float32',
                       'privileged': priv, 'availability':
                       'always available'})
    return tuple(fields)


OBS_FIELDS = _build_fields()
OBS_DIM = len(OBS_FIELDS)                       # 32
OBS_NAMES = tuple(f['name'] for f in OBS_FIELDS)
OBS_NAME_SET = frozenset(f['name'] for f in OBS_FIELDS)
DECLARED_SAMPLE_KEYS = frozenset(TIMING_KEYS) | OBS_NAME_SET

# Declared channel geometry: 8 slots per channel, channels in fixture order.
SLOTS_PER_CHANNEL = 8


def aliasing_audit():
    """The C21 aliasing test: two slots sharing a source key must each
    declare the alias. Refusal: aliasing_undeclared."""
    by_source = {}
    for f in OBS_FIELDS:
        by_source.setdefault(f['source'], []).append(f['name'])
    undeclared = []
    declared_groups = {}
    for source, names in sorted(by_source.items()):
        if len(names) > 1:
            missing = [n for n in names
                       for f in (OBS_FIELDS[OBS_NAMES.index(n)],)
                       if not f['alias']]
            if missing:
                undeclared.append({'source': source, 'names': names,
                                   'missing_alias_rows': missing})
            else:
                declared_groups[source] = names
    if undeclared:
        raise ValueError('aliasing_undeclared:' + json.dumps(undeclared))
    return {'declared_shared_sources': declared_groups,
            'shared_source_count': len(declared_groups),
            'total_fields': OBS_DIM}


# Named absent law: the x_* namespace is RESERVED (the ten inherited from
# the pinned G04 module are never deliverable); no synthetic constant
# occupies an absent slot.
ABSENT_PREFIX = 'x_'

# Privileged-forbidden law (W04 composition): solver-internal quantities
# with NO slot, never deliverable.
PRIVILEGED_NON_GRATA = (
    'contact_penetration_pre_solve', 'baumgarte_bias', 'solver_bias',
    'pre_press_velocity', 'solver_penetration_m', 'penetration_m',
)


def to_f32(v):
    """The declared float32 delivery conversion."""
    return struct.unpack('f', struct.pack('f', v))[0]


# ---- the seam: the ONLY channel the controller receives ----

class ObservationSeam:
    """Delivery gates with named refusal codes; a census of accepted
    samples and refusals. One seam instance per scenario run (the
    monotonicity law is per scenario tick axis)."""

    def __init__(self, scenario_id, dt_s):
        self.scenario_id = scenario_id
        self.dt_s = dt_s
        self.accepted = 0
        self.refusals = []
        self.last_tick = 0

    def _refuse(self, code, detail=''):
        self.refusals.append({'code': code, 'detail': str(detail)[:400]})
        raise ValueError(code + (': ' + str(detail) if detail != '' else ''))

    def deliver(self, sample):
        keys = set(sample)
        # check order = the preregistered discriminator order: the x_*
        # namespace and the privileged registry are named BEFORE the
        # generic undeclared-field gate so FB3/FB5 land on their codes.
        absent = sorted(k for k in keys if k.startswith(ABSENT_PREFIX))
        if absent:
            self._refuse('named_absent_occupied', absent)
        privileged = sorted(k for k in keys if k in PRIVILEGED_NON_GRATA)
        if privileged:
            self._refuse('privileged_source', privileged)
        extra = sorted(keys - DECLARED_SAMPLE_KEYS)
        if extra:
            self._refuse('undeclared_field', extra)
        missing = sorted(DECLARED_SAMPLE_KEYS - keys)
        if missing:
            self._refuse('undeclared_field', 'missing:' + str(missing))
        tick = sample['t_tick']
        if isinstance(tick, bool) or not isinstance(tick, int) or tick < 1:
            self._refuse('timing_unbound', {'t_tick': tick})
        if sample['t_phase'] not in PHASES:
            self._refuse('timing_unbound', {'t_phase': sample['t_phase']})
        dt = sample['t_dt_s']
        if not (isinstance(dt, float) and math.isfinite(dt) and dt > 0.0):
            self._refuse('timing_unbound', {'t_dt_s': dt})
        if dt != self.dt_s:
            self._refuse('timing_drift', {'t_dt_s': dt,
                                          'declared': self.dt_s})
        if abs(sample['t_seconds'] - tick * self.dt_s) > 1e-12:
            self._refuse('timing_drift', {'t_seconds': sample['t_seconds']})
        if tick <= self.last_tick:
            self._refuse('timing_drift',
                         'non_monotone:%d<=%d' % (tick, self.last_tick))
        for name in OBS_NAMES:
            v = sample[name]
            if not isinstance(v, float) or not math.isfinite(v):
                self._refuse('nonfinite_value', {name: v})
        if len([k for k in keys if k in OBS_NAME_SET]) != OBS_DIM:
            self._refuse('dim_mismatch', len(keys))
        self.last_tick = tick
        self.accepted += 1
        return True

    def census(self):
        return {'scenario_id': self.scenario_id, 'accepted': self.accepted,
                'refusals': list(self.refusals)}


# ---- the observer (G05-owned loop; pinned G04 operations, same order) ----

def _centroid(vertices):
    s = [0.0, 0.0, 0.0]
    for v in vertices:
        s[0] += v[0]
        s[1] += v[1]
        s[2] += v[2]
    n = len(vertices)
    return (s[0] / n, s[1] / n, s[2] / n)


def observe_scenario(gc, lc, geom, reading_kg, n_channels, mu_s=None,
                     mu_k=None, press_ns=None, hold_ticks=None,
                     release_ticks=None, scenario_id=None):
    """Re-run the frozen fixture through a G05-owned tick loop performing
    EXACTLY the sealed G04 per-tick operations in the same order (press
    impulse, solve, ledger identity, reaction re-verification, same row
    fields), additionally measuring the pad centroid pose from the pinned
    body state each tick. Returns (header, rows, centroids, samples,
    census); ``centroids[tick_index][k]`` is the measured pad centroid
    AFTER that tick's solve.

    Cross-validation is the caller's duty (refusal observer_drift):
    rows/header must be BIT-IDENTICAL to gc.run_scenario's output.
    """
    kwargs = {}
    if mu_s is not None:
        kwargs['mu_s'] = mu_s
    if mu_k is not None:
        kwargs['mu_k'] = mu_k
    if press_ns is not None:
        kwargs['press_ns'] = press_ns
    if hold_ticks is not None:
        kwargs['hold_ticks'] = hold_ticks
    if release_ticks is not None:
        kwargs['release_ticks'] = release_ticks
    share = reading_kg / n_channels
    facets = gc.channel_facets(geom, n_channels)
    trunk = lc.Body(body_id='trunk_01.lateral',
                    surface_id='trunk_01.lateral',
                    matter_id=gc.TRUNK_MATTER, mass_kg=1.0,
                    mu_s=gc.TRUNK_MU_S, mu_k=gc.TRUNK_MU_K,
                    thickness_m=gc.SOLID_THICKNESS_M,
                    vertices=list(geom['vertices_m06']),
                    triangles=[geom['triangles'][i]
                               for i in geom['lateral_indices']],
                    pinned=True)
    pads = []
    pad_norm = []
    for k, (ti, cen, n) in enumerate(facets):
        ey, ez = gc.orthobasis(n)
        origin = gc.vadd(cen, gc.vscale(n, gc.PAD_OFFSET_M))
        verts = gc.place_tetra(origin, n, ey, ez)
        pads.append(lc.Body(
            body_id='grip.pad_%d' % k, surface_id='grip.pad_%d' % k,
            matter_id='grip_fixture_placeholder_mu',
            mass_kg=share, mu_s=(kwargs.get('mu_s', gc.PAD_MU_S)),
            mu_k=(kwargs.get('mu_k', gc.PAD_MU_K)),
            thickness_m=gc.SOLID_THICKNESS_M, vertices=list(verts),
            triangles=list(gc.TETRA_TRIS), pinned=False))
        pad_norm.append(n)
    bodies = [trunk] + pads
    press_ns_ = kwargs.get('press_ns', gc.PRESS_JN_NS)
    hold = kwargs.get('hold_ticks', gc.HOLD_TICKS)
    release = kwargs.get('release_ticks', gc.RELEASE_TICKS)
    rows = []
    centroids = []

    def pad_centroid_z(pad):
        return _centroid(pad.vertices)[2]

    z_prev = [pad_centroid_z(p) for p in pads]
    total_ticks = hold + release
    for tick in range(1, total_ticks + 1):
        pressing = tick <= hold
        v_before_press = {b.id: b.velocity for b in bodies}
        press = {b.id: [0.0, 0.0, 0.0] for b in bodies}
        if pressing:
            for k, pad in enumerate(pads):
                vec = gc.vscale(pad_norm[k], -press_ns_)   # inward
                pad.velocity = gc.vadd(pad.velocity,
                                       gc.vscale(vec, 1.0 / pad.mass_kg))
                press[pad.id] = list(vec)
        records, ledger = lc.solve_tick(bodies)
        v_after = {b.id: b.velocity for b in bodies}
        for b in bodies:
            dv = gc.vsub(v_after[b.id], v_before_press[b.id])
            lhs = tuple(dv) if b.pinned else gc.vscale(dv, b.mass_kg)
            rhs = gc.vadd(tuple(press[b.id]),
                          tuple(ledger['gravity'].get(b.id, (0.0, 0.0, 0.0))))
            rhs = gc.vadd(rhs, tuple(ledger['contact'][b.id]))
            rhs = gc.vadd(rhs, tuple(ledger['anchor'][b.id]))
            resid = gc.vsub(lhs, rhs)
            gc.require(gc.vlen(resid) <= gc.WIN_LEDGER,
                       'ledger_imbalance:full_tick',
                       {'body': b.id, 'tick': tick, 'resid': list(resid)})
        trunk_contact = tuple(ledger['contact'][trunk.id])
        trunk_anchor = tuple(ledger['anchor'][trunk.id])
        gc.require(gc.vlen(gc.vadd(trunk_contact, trunk_anchor))
                   <= gc.WIN_LEDGER, 'reaction_concealed',
                   {'tick': tick, 'anchor': list(trunk_anchor),
                    'contact': list(trunk_contact)})
        tick_centroids = [_centroid(p.vertices) for p in pads]
        centroids.append(tick_centroids)
        # the full-tick residuals again, in G04's row shape (the observer's
        # ledger block must be BIT-IDENTICAL to the pinned runner's)
        resid_rows = []
        for b in bodies:
            dv = gc.vsub(v_after[b.id], v_before_press[b.id])
            lhs = tuple(dv) if b.pinned else gc.vscale(dv, b.mass_kg)
            rhs = gc.vadd(tuple(press[b.id]),
                          tuple(ledger['gravity'].get(b.id, (0.0, 0.0, 0.0))))
            rhs = gc.vadd(rhs, tuple(ledger['contact'][b.id]))
            rhs = gc.vadd(rhs, tuple(ledger['anchor'][b.id]))
            resid_rows.append(gc.vlen(gc.vsub(lhs, rhs)))
        row = {'tick': tick, 'phase': 'hold' if pressing else 'release',
               'pads': [], 'ledger': {
                   'reciprocity_residual':
                       list(ledger['reciprocity_residual']),
                   'trunk_anchor': list(trunk_anchor),
                   'trunk_contact': list(trunk_contact),
                   'residual_full_max': max(resid_rows)}}
        row['weld_recorded_ns'] = {b.id: 0.0 for b in bodies}
        for k, pad in enumerate(pads):
            recs = [r for r in records
                    if r['body_a'] == pad.id or r['body_b'] == pad.id]
            jn_sum = 0.0
            jt_sum = 0.0
            vt_post = 0.0
            modes = set()
            surfaces = set()
            for r in recs:
                jn_sum += r['jn_Ns']
                jt_sum += r['jt_Ns']
                vt_post = max(vt_post, r['vt_post'])
                modes.add(r['mode'])
                surfaces.update((r['surface_a'], r['surface_b']))
            mode = ('no_contact' if not modes else
                    ('stick' if 'stick' in modes else 'slip'))
            z_now = pad_centroid_z(pad)
            disp = z_prev[k] - z_now
            row['pads'].append({
                'pad': pad.id, 'jn_sum_Ns': jn_sum, 'jt_sum_Ns': jt_sum,
                'mode': mode, 'vt_post_mps': vt_post, 'disp_tick_m': disp,
                'surfaces': sorted(surfaces)})
            z_prev[k] = z_now
        rows.append(row)
    cum = [0.0] * n_channels
    for row in rows:
        for k, pd in enumerate(row['pads']):
            cum[k] += pd['disp_tick_m']
            pd['disp_down_m_cum'] = cum[k]
    header = {
        'scenario_id': scenario_id, 'reading_kg': reading_kg,
        'n_channels': n_channels, 'pad_share_kg': share,
        'mu_s': kwargs.get('mu_s', gc.PAD_MU_S),
        'mu_k': kwargs.get('mu_k', gc.PAD_MU_K),
        'press_ns': press_ns_, 'hold_ticks': hold,
        'release_ticks': release, 'pad_offset_m': gc.PAD_OFFSET_M,
        'trunk_surface': 'trunk_01.lateral', 'pair_rule': 'elementwise_min',
        'pair_mu_s': min(kwargs.get('mu_s', gc.PAD_MU_S), gc.TRUNK_MU_S),
        'pair_mu_k': min(kwargs.get('mu_k', gc.PAD_MU_K), gc.TRUNK_MU_K),
        'pinned_bodies': ['trunk_01.lateral'],
        'injections': {'sticky_release_weld': False, 'hidden_anchor': None},
        'channels': [{'tri': ti, 'centroid_m06': list(cen),
                      'normal_m06': list(nrm)}
                     for (ti, cen, nrm) in facets],
    }
    return header, rows, centroids


def initial_centroid_z(gc, geom, n_channels):
    """The declared initial pad centroid z (the frozen placement formula:
    origin = facet centroid + normal * PAD_OFFSET; local tetra centroid at
    (0.025, 0.025, 0.025))."""
    facets = gc.channel_facets(geom, n_channels)
    out = []
    for k, (ti, cen, n) in enumerate(facets):
        ey, ez = gc.orthobasis(n)
        origin = gc.vadd(cen, gc.vscale(n, gc.PAD_OFFSET_M))
        verts = gc.place_tetra(origin, n, ey, ez)
        out.append(_centroid(verts)[2])
    return out


def project_sample(gc, lc, row, centroid_zs, n_channels, dt_s):
    """Project one recorded row + measured poses into the declared sample
    (every vector value through the float32 delivery conversion)."""
    tick = row['tick']
    phase = row['phase']
    sample = {'t_tick': tick, 't_phase': phase, 't_dt_s': dt_s,
              't_seconds': tick * dt_s}
    n = n_channels
    stick_count = 0
    for k in range(3):
        if k < n:
            pd = row['pads'][k]
            mode = pd['mode']
            jn = pd['jn_sum_Ns']
            jt = pd['jt_sum_Ns']
            contact = 0.0 if mode == 'no_contact' else 1.0
            stick = 1.0 if mode == 'stick' else 0.0
            slip = 1.0 if mode == 'slip' else 0.0
            force = jn / dt_s
            disp = pd['disp_down_m_cum']
            cz = centroid_zs[k]
        else:
            contact = stick = slip = jn = jt = force = disp = cz = 0.0
        sample['ch%d_contact_flag' % k] = to_f32(contact)
        sample['ch%d_stick_flag' % k] = to_f32(stick)
        sample['ch%d_slip_flag' % k] = to_f32(slip)
        sample['ch%d_jn_Ns' % k] = to_f32(jn)
        sample['ch%d_jt_Ns' % k] = to_f32(jt)
        sample['ch%d_contact_force_N' % k] = to_f32(force)
        sample['ch%d_disp_down_cum_m' % k] = to_f32(disp)
        sample['ch%d_centroid_z_m' % k] = to_f32(cz)
        if k < n and stick == 1.0:
            stick_count += 1
    supported = 1.0 if (n > 0 and stick_count == n and phase == 'hold') \
        else 0.0
    release_flag = 1.0 if phase == 'release' else 0.0
    avail_slots = SLOTS_PER_CHANNEL * n + 8
    mask_mean = avail_slots / OBS_DIM
    frac_avail = ((1 if n > 0 else 0) + 2) / 5.0
    sample['agg_support_count'] = to_f32(float(stick_count))
    sample['agg_supported_flag'] = to_f32(supported)
    sample['agg_release_flag'] = to_f32(release_flag)
    sample['agg_trunk_anchor_z_Ns'] = to_f32(row['ledger']['trunk_anchor'][2])
    sample['agg_ledger_residual_max_Ns'] = to_f32(
        row['ledger']['residual_full_max'])
    sample['agg_reciprocity_max_Ns'] = to_f32(
        max(abs(v) for v in row['ledger']['reciprocity_residual']))
    sample['obs_mask_mean'] = to_f32(mask_mean)
    sample['obs_frac_avail'] = to_f32(frac_avail)
    return sample


def observe_and_deliver(gc, lc, geom, reading_kg, n_channels, scenario_id,
                        **kwargs):
    """One observed scenario: the G05 loop, the pinned-runner cross-check,
    then one delivered sample per tick through a fresh seam.
    Returns (header, rows, samples, census)."""
    header, rows, centroids = observe_scenario(
        gc, lc, geom, reading_kg, n_channels, scenario_id=scenario_id,
        **kwargs)
    header_ref, rows_ref = gc.run_scenario(
        lc, geom, reading_kg, n_channels, scenario_id=scenario_id, **kwargs)
    if header != header_ref:
        raise ValueError('observer_drift:header:' + str(scenario_id))
    for r_obs, r_ref in zip(rows, rows_ref):
        if r_obs['tick'] != r_ref['tick'] or r_obs['phase'] != r_ref['phase']:
            raise ValueError('observer_drift:row:%d' % r_obs['tick'])
        if r_obs['ledger'] != r_ref['ledger']:
            raise ValueError('observer_drift:ledger:%d' % r_obs['tick'])
        for p_obs, p_ref in zip(r_obs['pads'], r_ref['pads']):
            for key in ('jn_sum_Ns', 'jt_sum_Ns', 'mode', 'disp_tick_m',
                        'surfaces', 'vt_post_mps', 'pad'):
                if p_obs[key] != p_ref[key]:
                    raise ValueError('observer_drift:pads:%s:%d'
                                     % (key, r_obs['tick']))
    seam = ObservationSeam(scenario_id, lc.DT)
    z0 = initial_centroid_z(gc, geom, n_channels)
    for i, row in enumerate(rows):
        sample = project_sample(gc, lc, row, [c[2] for c in centroids[i]],
                                n_channels, lc.DT)
        seam.deliver(sample)
    return header, rows, seam, z0, centroids
