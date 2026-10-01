"""MAT2-G07 unsupported release and fall measurement (PREREGISTRATION.md,
frozen).

done_when: "Loss/release of support removes its forces and yields
accounted motion and energy". Observation: "Preserve failures; no reset
or leftover constraint concealing loss of support".

Three established interfaces, each imported at run time, hash-asserted
against its frozen pin, and never forked:

- THE SOLVER: MAT2-M06 ``chimera.local_contact.v1`` (via G04's pinned
  loader). Every impulse in this card comes from ``lc.solve_tick``; the
  recorded per-contact ``w_f_ke_J`` is the declared losses line.
- THE GRIP PHYSICS + FIXTURE: MAT2-G04's sealed ``grip_contact.py`` (the
  exact revision merged in PR #298). G07 consumes the fixture builders,
  press channel, closed forms, injection hooks, named-absent list and
  window set. The one declared scenario-level input: the battery calls
  the unmodified machinery with ``release_ticks = 40`` (a declared
  ``run_scenario`` parameter; G04's default 10 stays sealed).
- THE OBSERVATION SEAM: MAT2-G05's sealed ``contact_support_obs.py``
  (the exact revision merged in PR #300). Every measurement is delivered
  ONLY through G05's ``ObservationSeam``/``project_sample``; the declared
  32-slot table is not extended.

The deliverable: ``observe_with_account`` -- a G07-owned tick loop
performing EXACTLY the sealed G04 per-tick operations in the same order
(cross-validated BIT-IDENTICAL against ``gc.run_scenario``, refusal
``observer_drift``), additionally recording per tick and body the
velocities, the recorded ledger impulse vectors, the pad contact records
in solver order and the measured pad centroid, and building the exact
discrete accounts:

- ENERGY (C13): per body per tick,
  ``KE(t) - KE(t-1) == W_press + W_gravity + W_contact + W_anchor``
  with each owner's exact discrete impulse work ``W = J.u + (w/2)|J|^2``
  replayed in solver order from the RECORDED impulses (refusal
  ``impulse_replay_incomplete`` if the replay misses a record); the
  friction split of the replay cross-checks the solver's recorded
  dissipation: ``W_friction == -sum(w_f_ke_J)``.
- STORED ENERGY (C13): with PE = m*g*(z - z_ref), the exact tick
  identity ``d(KE+PE) - [W_press + W_contact - (m/2)(g*DT)^2
  + m*g*DT*dv_z_contact] == residual_energy`` (the declared symplectic
  discretization account; given the KE identity it reduces to the same
  residual -- recorded transparently in the receipt). Precondition: the
  pose-continuity identity ``z(t-1) - z(t) == -v_z_after(t)*DT``, which
  is also the anti-teleport law (C13: no teleport or hidden reset).
- RELEASE (the done_when): on every release tick the recorded pad
  impulses sit inside the sealed G04 share-scaled noise bars,
  ``W_press == 0`` and the trunk anchor sits inside its bar.
- MOTION (C13/C20): the free-fall velocity recursion
  ``v_down(k) - v_down(k-1) == g*DT`` and the closed-form downward
  displacement from the release-start state, inside the sealed windows;
  every phase metric extracted by a keyed per-phase extractor that
  refuses unknown/empty phases (P6; C20 static/dynamic separation).

CPU-only, stdlib-only, deterministic (no RNG, no wall clock). Refusals
are named codes; nothing is silently repaired.
"""
from __future__ import annotations

import json
import math
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

SCHEMA = 'chimera.g07_release_fall.v1'

# ---- the established interfaces (imported, hash-asserted, never forked) --
G05_MODULE_REL = '../MAT2-G05/contact_support_obs.py'
G05_MODULE_SHA256 = ('3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693f725e'
                     '4f31c46bd3')


def load_g05_module(rel=G05_MODULE_REL, expected_sha=G05_MODULE_SHA256):
    """Import the pinned G05 module after asserting its bytes.
    Refusals: interface_pin_missing / interface_pin_drift."""
    import hashlib
    import importlib.util
    path = (HERE / rel).resolve()
    if not path.exists():
        raise ValueError('interface_pin_missing:' + str(path))
    raw = path.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != expected_sha:
        raise ValueError('interface_pin_drift:' + got)
    spec = importlib.util.spec_from_file_location('g07_pinned_contact_obs',
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---- frozen scenario/window declarations (PREREG sections 2-3) -----------
HOLD_TICKS = 20
RELEASE_TICKS = 40          # the declared release_ticks (G04 default 10)
TOTAL_TICKS = HOLD_TICKS + RELEASE_TICKS   # 60
SCENARIO_COUNT = 13
DELIVERIES_EXPECTED = SCENARIO_COUNT * TOTAL_TICKS   # 780
RELEASE_TICK_START = HOLD_TICKS + 1         # 21

WIN_ENERGY = 1e-12          # J, per body per tick impulse-work identity
WIN_LOSS = 1e-12            # J, friction split vs recorded w_f_ke_J sum
WIN_DRIFT = 1e-9            # J, stored-energy account window (frozen)
WIN_REPLAY_V = 1e-12        # m/s, impulse replay closure
WIN_CONT = 1e-9             # m, pose continuity (anti-teleport)
WIN_RELEASE_SCALE = 1e-10   # N*s per kg (sealed G04 amendment a2 bar)
WIN_RECURSION_V = 1e-9      # m/s (sealed G04 window, reused verbatim)
WIN_DISP = 1e-9             # m   (sealed G04 window, reused verbatim)
PHASES = ('hold', 'release')


def require(ok, code, detail=''):
    if not ok:
        raise ValueError(code + (': ' + str(detail) if detail != '' else ''))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


# ---- the exact discrete impulse work (PREREG section 2a) ------------------

def impulse_work(j_vec, u_vec, inv_mass):
    """W = J.u + (inv_mass/2)|J|^2 -- the EXACT kinetic-energy change of
    applying impulse J to pre-impulse velocity u (sequential discrete
    application)."""
    dot = j_vec[0] * u_vec[0] + j_vec[1] * u_vec[1] + j_vec[2] * u_vec[2]
    j2 = j_vec[0] ** 2 + j_vec[1] ** 2 + j_vec[2] ** 2
    return dot + 0.5 * inv_mass * j2


def _vlen(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def _vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _vscale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


# ---- the G07 observer (sealed G04 ops; pinned-runner cross-check) ---------

def observe_with_account(cso, gc, lc, geom, reading_kg, n_channels,
                         scenario_id, mu_s=None, mu_k=None, press_ns=None,
                         hold_ticks=None, release_ticks=None,
                         sticky_release_weld=False, hidden_anchor=None,
                         teleport_at_tick=None, propulsion_ns=None,
                         require_ledger=True, enforce_account=True):
    """Run one scenario through the G07 loop (EXACTLY G04's per-tick
    operations, same order) and build the account.

    Injection hooks (every use RECORDED in the acct rows; falsifier-only;
    production callers never set them):
    - ``sticky_release_weld``: G04's recorded leftover-constraint hook,
      mirrored bit-identically (the tampered rows still cross-check
      against ``gc.run_scenario(sticky_release_weld=True)``); the weld is
      a RECORDED owner and its exact work is booked as ``work_weld_J``
      (exactly 0.0 on every clean run).
    - ``hidden_anchor``: G04's unrecorded hold-phase impulse hook; the
      caller must pass ``require_ledger=False`` (the production N*s
      ledger law stays armed on every clean run).
    - ``teleport_at_tick``: G07 hook (FB3): at that tick the falling
      pad 0 is reset to its pre-solve pose with its pre-solve velocity.
    - ``propulsion_ns``: G07 hook (FB4): an upward UNRECORDED impulse
      on pad 0 every release tick (caller passes
      ``require_ledger=False``).
    - ``enforce_account=False``: falsifier-only measurement mode (FB2-
      FB4): the account residuals are still computed and RECORDED per
      row, but not enforced, so the tampered trace can be measured
      (worst energy residual in joules, continuity break in meters)
      instead of dying at its first refusal. Never used on a clean run.

    Returns (header, rows, acct_rows, centroids).
    """
    kwargs = {}
    if mu_s is not None:
        kwargs['mu_s'] = mu_s
    if mu_k is not None:
        kwargs['mu_k'] = mu_k
    if press_ns is not None:
        kwargs['press_ns'] = press_ns
    hold = hold_ticks if hold_ticks is not None else gc.HOLD_TICKS
    release = release_ticks if release_ticks is not None else gc.RELEASE_TICKS
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
    up_dir = gc.vscale(gc.tangent_dir(pad_norm[0]), -1.0)   # UP the wall

    def centroid_z(vertices):
        s = 0.0
        for v in vertices:
            s += v[2]
        return s / len(vertices)

    def centroid(vertices):
        sx = sy = sz = 0.0
        for v in vertices:
            sx += v[0]
            sy += v[1]
            sz += v[2]
        n = float(len(vertices))
        return (sx / n, sy / n, sz / n)

    rows = []
    acct_rows = []
    centroids = []
    z_prev = [centroid_z(p.vertices) for p in pads]
    last_jt = [0.0] * n_channels
    total_ticks = hold + release
    for tick in range(1, total_ticks + 1):
        pressing = tick <= hold
        v_start = {b.id: tuple(b.velocity) for b in bodies}
        press = {b.id: [0.0, 0.0, 0.0] for b in bodies}
        weld = {b.id: [0.0, 0.0, 0.0] for b in bodies}
        if pressing:
            for k, pad in enumerate(pads):
                vec = gc.vscale(pad_norm[k], -press_ns_)     # inward
                pad.velocity = gc.vadd(pad.velocity,
                                       gc.vscale(vec, 1.0 / pad.mass_kg))
                press[pad.id] = list(vec)
        if sticky_release_weld and not pressing:
            # G04's FB1 hook, mirrored bit-identically (RECORDED owner).
            for k, pad in enumerate(pads):
                if last_jt[k] <= 0.0:
                    continue
                vec = gc.vscale(up_dir, last_jt[k])
                pad.velocity = gc.vadd(pad.velocity,
                                       gc.vscale(vec, 1.0 / pad.mass_kg))
                weld[pad.id] = list(vec)
        if hidden_anchor is not None and pressing:
            # G04's FB3 hook: applied to the body, absent from every
            # recorded channel (UNRECORDED owner).
            pad = pads[0]
            pad.velocity = gc.vadd(pad.velocity,
                                   gc.vscale(hidden_anchor,
                                             1.0 / pad.mass_kg))
        if propulsion_ns is not None and not pressing:
            # G07 FB4 hook: unrecorded upward impulse, release ticks only.
            pad = pads[0]
            pad.velocity = gc.vadd(pad.velocity,
                                   gc.vscale((0.0, 0.0, 1.0),
                                             propulsion_ns / pad.mass_kg))
        teleport_pose = None
        if teleport_at_tick is not None and tick == teleport_at_tick:
            # G07 FB3 hook: the reset target is the pre-solve state.
            teleport_pose = ([tuple(v) for v in pads[0].vertices],
                             tuple(pads[0].velocity))
        v_press = {b.id: tuple(b.velocity) for b in bodies}
        records, ledger = lc.solve_tick(bodies)
        v_after = {b.id: tuple(b.velocity) for b in bodies}
        if teleport_pose is not None:
            pads[0].vertices = [tuple(v) for v in teleport_pose[0]]
            pads[0].velocity = teleport_pose[1]
            v_after[pads[0].id] = tuple(pads[0].velocity)
        # Full-tick N*s ledger identity (G04's law; armed on clean runs).
        residual_full = {}
        for b in bodies:
            dv = gc.vsub(v_after[b.id], v_start[b.id])
            lhs = tuple(dv) if b.pinned else gc.vscale(dv, b.mass_kg)
            rhs = gc.vadd(tuple(press[b.id]), tuple(weld[b.id]))
            rhs = gc.vadd(rhs, tuple(ledger['gravity'].get(b.id,
                                                        (0.0, 0.0, 0.0))))
            rhs = gc.vadd(rhs, tuple(ledger['contact'][b.id]))
            rhs = gc.vadd(rhs, tuple(ledger['anchor'][b.id]))
            resid = gc.vsub(lhs, rhs)
            residual_full[b.id] = list(resid)
            if require_ledger:
                gc.require(gc.vlen(resid) <= gc.WIN_LEDGER,
                           'ledger_imbalance:full_tick',
                           {'body': b.id, 'tick': tick,
                            'resid': list(resid)})
        trunk_contact = tuple(ledger['contact'][trunk.id])
        trunk_anchor = tuple(ledger['anchor'][trunk.id])
        gc.require(gc.vlen(gc.vadd(trunk_contact, trunk_anchor))
                   <= gc.WIN_LEDGER, 'reaction_concealed',
                   {'tick': tick, 'anchor': list(trunk_anchor),
                    'contact': list(trunk_contact)})
        # ---- the G07 account (per pad, single exact replay) ----
        acct_pads = []
        centroid_tick = []
        ccd_tick = any(r['kind'] == 'ccd' for r in records)
        for k, pad in enumerate(pads):
            inv_m = pad.inv_mass()
            m = pad.mass_kg
            j_g = tuple(ledger['gravity'].get(pad.id, (0.0, 0.0, 0.0)))
            # recorded-owner works: press -> weld (the weld's pre-velocity
            # is v_start + press*inv_m; both are RECORDED channels)
            w_press = impulse_work(press[pad.id], v_start[pad.id], inv_m)
            w_weld = impulse_work(
                weld[pad.id],
                _vadd(v_start[pad.id],
                      _vscale(press[pad.id], inv_m)), inv_m)
            w_grav = impulse_work(j_g, v_press[pad.id], inv_m)
            w_contact = 0.0
            w_friction = 0.0
            w_loss_solver = 0.0
            v_cur = _vadd(v_press[pad.id], _vscale(j_g, inv_m))
            for r in records:
                if r['body_a'] == pad.id:
                    j_rec = tuple(r['impulse_on_a'])
                    jn_vec = _vscale(tuple(r['normal']), r['jn_Ns'])
                elif r['body_b'] == pad.id:
                    j_rec = tuple(r['impulse_on_b'])
                    jn_vec = _vscale(tuple(r['normal']), -r['jn_Ns'])
                else:
                    continue
                jt_vec = _vsub(j_rec, jn_vec)
                w_contact += impulse_work(jn_vec, v_cur, inv_m)
                v_cur = _vadd(v_cur, _vscale(jn_vec, inv_m))
                w_fric = impulse_work(jt_vec, v_cur, inv_m)
                w_contact += w_fric
                w_friction += w_fric
                w_loss_solver += r['w_f_ke_J']
                v_cur = _vadd(v_cur, _vscale(jt_vec, inv_m))
            w_anchor = impulse_work(tuple(ledger['anchor'][pad.id]),
                                    v_cur, inv_m)
            replay_delta = _vlen(_vsub(v_cur, v_after[pad.id]))
            if enforce_account:
                require(replay_delta <= WIN_REPLAY_V,
                        'impulse_replay_incomplete',
                        {'pad': pad.id, 'tick': tick,
                         'delta_mps': replay_delta})
            ke_start = 0.5 * m * _vlen(v_start[pad.id]) ** 2
            ke_after = 0.5 * m * _vlen(v_after[pad.id]) ** 2
            resid_e = (ke_after - ke_start) \
                - (w_press + w_weld + w_grav + w_contact + w_anchor)
            if enforce_account:
                require(abs(resid_e) <= WIN_ENERGY,
                        'energy_identity_broken',
                        {'pad': pad.id, 'tick': tick,
                         'residual_J': resid_e})
                require(abs(w_friction + w_loss_solver) <= WIN_LOSS,
                        'loss_identity_broken',
                        {'pad': pad.id, 'tick': tick,
                         'w_friction_J': w_friction,
                         'w_solver_J': w_loss_solver})
            z_now = centroid_z(pad.vertices)
            disp = z_prev[k] - z_now          # downward positive
            # Pose continuity (anti-teleport). On an UNOBSTRUCTED tick the
            # position advances with the post-solve velocity and the exact
            # identity is enforced. On a CCD-advance tick (a recorded
            # collision event) the sub-step advance happens at the
            # pre-impact velocity, so the exact form does not apply; the
            # KINEMATIC anti-teleport bound is enforced instead (the body
            # cannot advance farther than free fall from its pre-solve
            # velocity, nor move upward) and the exact-form residual is
            # still recorded as evidence.
            cont = abs(disp - (-v_after[pad.id][2] * lc.DT))
            if not ccd_tick:
                if enforce_account:
                    require(cont <= WIN_CONT, 'continuity_broken',
                            {'pad': pad.id, 'tick': tick,
                             'residual_m': cont})
            else:
                v_bound = (abs(v_press[pad.id][2]) + lc.G * lc.DT) * lc.DT \
                    + WIN_CONT
                if enforce_account:
                    require(-WIN_CONT <= disp <= v_bound,
                            'continuity_broken:teleport_bound',
                            {'pad': pad.id, 'tick': tick, 'disp_m': disp,
                             'bound_m': v_bound})
            # stored-energy account (exact given the KE identity and the
            # no-CCD continuity precondition; reduces to resid_e
            # algebraically). On a CCD-advance tick the exact form does
            # not apply; the residual is recorded as the collision's
            # stored-energy exchange, not enforced.
            contact_dv_z = (v_after[pad.id][2] - v_press[pad.id][2]
                            + lc.G * lc.DT)
            dkepe = (ke_after - ke_start) + m * lc.G * (z_now - z_prev[k])
            pred = (w_press + w_weld + w_contact
                    - 0.5 * m * (lc.G * lc.DT) ** 2
                    + m * lc.G * lc.DT * contact_dv_z)
            drift_resid = dkepe - pred
            if enforce_account and not ccd_tick:
                require(abs(drift_resid) <= WIN_DRIFT,
                        'drift_identity_broken',
                        {'pad': pad.id, 'tick': tick,
                         'residual_J': drift_resid})
            centroid_tick.append(centroid(pad.vertices))
            acct_pads.append({
                'pad': pad.id,
                'vz_start_mps': v_start[pad.id][2],
                'vz_press_mps': v_press[pad.id][2],
                'vz_after_mps': v_after[pad.id][2],
                'ke_start_J': ke_start, 'ke_after_J': ke_after,
                'work_press_J': w_press, 'work_weld_J': w_weld,
                'work_gravity_J': w_grav,
                'work_contact_J': w_contact, 'work_anchor_J': w_anchor,
                'work_friction_J': w_friction,
                'loss_solver_J': w_loss_solver,
                'residual_J': resid_e,
                'v_replay_delta_mps': replay_delta,
                'centroid_z_m': z_now,
                'disp_down_tick_m': disp,
                'continuity_residual_m': cont,
                'unobstructed': not ccd_tick,
                'contact_dv_z_mps': contact_dv_z,
                'dkepe_J': dkepe, 'drift_pred_J': pred,
                'drift_residual_J': drift_resid,
            })
            z_prev[k] = z_now
        # trunk account (pinned: velocity stays exactly zero, work zero)
        require(_vlen(v_after[trunk.id]) == 0.0, 'trunk_not_still',
                {'tick': tick, 'v': list(v_after[trunk.id])})
        acct_rows.append({
            'tick': tick, 'phase': 'hold' if pressing else 'release',
            'pads': acct_pads,
            'trunk': {'v_after_norm_mps': _vlen(v_after[trunk.id]),
                      'contact_Ns': list(trunk_contact),
                      'anchor_Ns': list(trunk_anchor), 'residual_J': 0.0},
            'ledger_residual_full_max_Ns': max(_vlen(v) for v
                                               in residual_full.values()),
            'ledger_armed': bool(require_ledger),
            'account_enforced': bool(enforce_account),
            'injections': {'sticky_release_weld': bool(sticky_release_weld),
                           'hidden_anchor':
                               (list(hidden_anchor) if hidden_anchor
                                is not None else None),
                           'teleport_at_tick': teleport_at_tick,
                           'propulsion_ns': propulsion_ns},
        })
        # ---- G04's row shape (the bit-identical cross-check payload) ----
        row = {'tick': tick, 'phase': 'hold' if pressing else 'release',
               'pads': [], 'weld_recorded_ns': {
                   b.id: _vlen(tuple(weld[b.id])) for b in bodies},
               'ledger': {
                   'reciprocity_residual':
                       list(ledger['reciprocity_residual']),
                   'trunk_anchor': list(trunk_anchor),
                   'trunk_contact': list(trunk_contact),
                   'residual_full_max': max(_vlen(tuple(v)) for v
                                            in residual_full.values())}}
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
            if pressing:
                last_jt[k] = jt_sum
            row['pads'].append({
                'pad': pad.id, 'jn_sum_Ns': jn_sum, 'jt_sum_Ns': jt_sum,
                'mode': mode, 'vt_post_mps': vt_post,
                'disp_tick_m': acct_pads[k]['disp_down_tick_m'],
                'surfaces': sorted(surfaces)})
        rows.append(row)
        centroids.append(centroid_tick)
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
        'press_ns': press_ns_, 'hold_ticks': hold, 'release_ticks': release,
        'pad_offset_m': gc.PAD_OFFSET_M,
        'trunk_surface': 'trunk_01.lateral', 'pair_rule': 'elementwise_min',
        'pair_mu_s': min(kwargs.get('mu_s', gc.PAD_MU_S), gc.TRUNK_MU_S),
        'pair_mu_k': min(kwargs.get('mu_k', gc.PAD_MU_K), gc.TRUNK_MU_K),
        'pinned_bodies': ['trunk_01.lateral'],
        'injections': {'sticky_release_weld': bool(sticky_release_weld),
                       'hidden_anchor':
                           list(hidden_anchor) if hidden_anchor is not None
                           else None},
        # the G07-only hook names are recorded per acct row, never in the
        # header (the header stays bit-identical to gc.run_scenario's).
        'channels': [{'tri': ti, 'centroid_m06': list(cen),
                      'normal_m06': list(nrm)}
                     for (ti, cen, nrm) in facets],
    }
    return header, rows, acct_rows, centroids


def cross_check_rows(header, rows, header_ref, rows_ref, scenario_id):
    """The G05 heritage law: the G07 loop's rows are BIT-IDENTICAL to
    gc.run_scenario's. Refusal: observer_drift."""
    if header != header_ref:
        raise ValueError('observer_drift:header:' + str(scenario_id))
    if len(rows) != len(rows_ref):
        raise ValueError('observer_drift:row_count:' + str(scenario_id))
    for r_obs, r_ref in zip(rows, rows_ref):
        if r_obs['tick'] != r_ref['tick'] or r_obs['phase'] != r_ref['phase']:
            raise ValueError('observer_drift:row:%d' % r_obs['tick'])
        if r_obs['ledger'] != r_ref['ledger']:
            raise ValueError('observer_drift:ledger:%d' % r_obs['tick'])
        if r_obs['weld_recorded_ns'] != r_ref['weld_recorded_ns']:
            raise ValueError('observer_drift:weld:%d' % r_obs['tick'])
        for p_obs, p_ref in zip(r_obs['pads'], r_ref['pads']):
            for key in ('pad', 'jn_sum_Ns', 'jt_sum_Ns', 'mode',
                        'disp_tick_m', 'surfaces', 'vt_post_mps',
                        'disp_down_m_cum'):
                if p_obs[key] != p_ref[key]:
                    raise ValueError('observer_drift:pads:%s:%d'
                                     % (key, r_obs['tick']))


# ---- keyed per-phase extraction (P6; C20 static/dynamic separation) -------

def phase_rows(acct_rows, phase):
    """Select one phase's rows; refuse unknown/empty phases and untagged
    rows. Metrics are ONLY extracted through this keyed selector."""
    require(phase in PHASES, 'phase_unknown', phase)
    sel = [r for r in acct_rows if r['phase'] == phase]
    require(sel, 'phase_unknown:empty', phase)
    require(all(r['phase'] == phase for r in sel), 'mixed_phase_scan', phase)
    return sel


def phase_metric(acct_rows, phase, key, pad=None):
    """Keyed per-phase metric: every selected row must carry the key."""
    sel = phase_rows(acct_rows, phase)
    if pad is None:
        require(all(key in r for r in sel), 'phase_metric_key_missing',
                {'phase': phase, 'key': key})
        return [r[key] for r in sel]
    require(all(pad < len(r['pads']) and key in r['pads'][pad]
                for r in sel), 'phase_metric_key_missing',
            {'phase': phase, 'key': key, 'pad': pad})
    return [r['pads'][pad][key] for r in sel]


# ---- the release account (PREREG section 2c; the done_when measurement) ---

def release_account(rows, acct_rows, n_channels, share_kg, dt_s,
                    hold_ticks=HOLD_TICKS):
    """Evaluate the release account over one clean scenario. Returns the
    per-scenario release summary; refuses any residual-support signature
    on the UNOBSTRUCTED release ticks. A recorded CCD collision event (a
    sliding pad's corner striking a facet ridge; the solver's own 'ccd'
    kind) is a real transient contact force, NOT residual support: it is
    carried in full by the exact energy account, and this summary records
    it as collision evidence (amendment a2)."""
    bar = share_kg * WIN_RELEASE_SCALE
    total_bar = share_kg * n_channels * WIN_RELEASE_SCALE
    worst_jn = 0.0
    worst_jt = 0.0
    worst_anchor = 0.0
    collisions = []
    rel_rows = phase_rows(rows, 'release')
    for row in rel_rows:
        ai = row['tick'] - 1
        unobstructed = all(p['unobstructed'] for p in acct_rows[ai]['pads'])
        if not unobstructed:
            collisions.append({
                'tick': row['tick'],
                'jn_max_Ns': max(abs(p['jn_sum_Ns'])
                                 for p in row['pads']),
                'jt_max_Ns': max(abs(p['jt_sum_Ns']) for p in row['pads']),
                'anchor_Ns': _vlen(tuple(row['ledger']['trunk_anchor'])),
            })
            continue
        for pd in row['pads']:
            worst_jn = max(worst_jn, abs(pd['jn_sum_Ns']))
            worst_jt = max(worst_jt, abs(pd['jt_sum_Ns']))
            require(abs(pd['jn_sum_Ns']) <= bar, 'release_bar_exceeded',
                    {'tick': row['tick'], 'jn': pd['jn_sum_Ns'], 'bar': bar})
            require(abs(pd['jt_sum_Ns']) <= bar, 'release_bar_exceeded',
                    {'tick': row['tick'], 'jt': pd['jt_sum_Ns'], 'bar': bar})
        anchor = tuple(row['ledger']['trunk_anchor'])
        worst_anchor = max(worst_anchor, _vlen(anchor))
        require(_vlen(anchor) <= total_bar, 'release_bar_exceeded',
                {'tick': row['tick'], 'anchor': list(anchor),
                 'bar': total_bar})
    w_press_release = sum(v for k in range(n_channels)
                          for v in phase_metric(acct_rows, 'release',
                                                'work_press_J', pad=k))
    require(w_press_release == 0.0, 'release_press_work_nonzero',
            w_press_release)
    # motion account: free-fall velocity recursion on every unobstructed
    # release tick; the gravity-only closed form on the UNOBSTRUCTED
    # PREFIX (up to the first collision event)
    worst_recursion = 0.0
    worst_disp = 0.0
    dt = dt_s
    first_collision = min((c['tick'] for c in collisions),
                          default=TOTAL_TICKS + 1)
    for k in range(n_channels):
        v_rel = None
        cum_start = None
        j = 0
        v0 = None
        for row in rows:
            ai = row['tick'] - 1
            vz = acct_rows[ai]['pads'][k]['vz_after_mps']
            cum = row['pads'][k]['disp_down_m_cum']
            if row['tick'] == hold_ticks:
                v0 = -vz
                cum_start = cum
                v_rel = -vz
                continue
            if row['phase'] != 'release':
                continue
            j += 1
            v_down = -vz
            if row['tick'] < first_collision:
                worst_recursion = max(worst_recursion,
                                      abs(v_down - v_rel - 9.81 * dt))
                want = v0 * j * dt + 0.5 * 9.81 * dt * dt * j * (j + 1)
                worst_disp = max(worst_disp, abs(cum - cum_start - want))
            v_rel = v_down
    require(worst_recursion <= WIN_RECURSION_V, 'motion_recursion_broken',
            worst_recursion)
    require(worst_disp <= WIN_DISP, 'motion_closed_form_broken', worst_disp)
    return {'jn_max_Ns': worst_jn, 'jt_max_Ns': worst_jt,
            'anchor_max_Ns': worst_anchor, 'bar_Ns': bar,
            'anchor_bar_Ns': total_bar,
            'press_work_release_J': w_press_release,
            'recursion_worst_mps': worst_recursion,
            'disp_closed_form_worst_m': worst_disp,
            'collision_events': collisions,
            'collision_count': len(collisions),
            'unobstructed_release_ticks':
                RELEASE_TICKS - len(collisions),
            'closed_form_prefix_ticks':
                max(first_collision - HOLD_TICKS - 1, 0)}
