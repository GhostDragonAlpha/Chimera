"""MAT2-G06 supported limb-transfer sequence (PREREGISTRATION.md, frozen).

done_when: "At least one reachable transfer retains admissible support
throughout its tested envelope".

Declared model (prereg section 2): the sealed G04 pad-as-carried-share
abstraction extended with the DECLARED load handover (holders carry
m/(n-1) during the flight window; the sealed G01 row (reading, n-1) IS the
transfer-admissibility condition) and the DECLARED climb channel (a
recorded fixture input at a declared schedule, never an actuator
qualification; x_press stays ABSENT). Every impulse in this card comes
from the pinned M06 ``lc.solve_tick``; the fixture is the sealed G04
trunk/pad/press fixture; the observation table is the pinned G05 32-slot
table with the task-owned G06 phase universe.

Established interfaces, imported at run time, hash-asserted, never forked:
- THE SOLVER: MAT2-M06 ``chimera.local_contact.v1`` (via G04's loader).
- THE GRIP PHYSICS + FIXTURE: MAT2-G04 ``grip_contact.py`` (PR #298).
- THE OBSERVATION TABLE: MAT2-G05 ``contact_support_obs.py`` (PR #300);
  G06 does NOT modify it and does NOT re-declare the W04 TC-2 interface.
- THE SEALED BOUNDARY: the MAT2-G01 pinned feasibility receipt (host pin;
  its 12-row case table is the transfer-admissibility authority).

CPU-only, stdlib-only, deterministic (no RNG, no wall clock). Refusals are
named codes; nothing is silently repaired.
"""
from __future__ import annotations

import hashlib
import importlib.util
import math
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parent

SCHEMA = 'chimera.g06_transfer.v1'

# ---- the established interfaces (imported, hash-asserted, never forked) ----
G05_MODULE_REL = '../MAT2-G05/contact_support_obs.py'
G05_MODULE_SHA256 = ('3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693f725e'
                     '4f31c46bd3')
G04_MODULE_REL = '../MAT2-G04/grip_contact.py'
G04_MODULE_SHA256 = ('0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b'
                     '4173d69245')


def load_g05_module(rel=G05_MODULE_REL, expected_sha=G05_MODULE_SHA256):
    """Import the pinned G05 observation module after asserting its bytes.
    Refusals: interface_pin_missing / interface_pin_drift."""
    path = (HERE / rel).resolve()
    if not path.exists():
        raise ValueError('interface_pin_missing:' + str(path))
    raw = path.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != expected_sha:
        raise ValueError('interface_pin_drift:' + got)
    spec = importlib.util.spec_from_file_location('g06_pinned_contact_support'
                                                 '_obs', path)
    mod = importable_spec(spec)
    return mod


def importable_spec(spec):
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_g04_module(rel=G04_MODULE_REL, expected_sha=G04_MODULE_SHA256):
    """Import the pinned G04 fixture module after asserting its bytes."""
    path = (HERE / rel).resolve()
    if not path.exists():
        raise ValueError('interface_pin_missing:' + str(path))
    raw = path.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != expected_sha:
        raise ValueError('interface_pin_drift:' + got)
    spec = importlib.util.spec_from_file_location('g06_pinned_grip_contact',
                                                  path)
    return importable_spec(spec)


# ---- frozen schedule (PREREGISTRATION section 4; 229 ticks) ----
APPROACH_TICKS = 3          # ticks 1..3, flyer press = A_PRESS
ATTACH_TICKS = 4            # ticks 4..7, press at the operating point
LOAD_TICKS = 3              # ticks 8..10, climb-to-friction handover
HOLD_TICKS = 20             # ticks 11..30
BRAKE_TICKS = 10            # declared brake, ends at v = 0 exactly
HOVER_TICKS = 2             # post-brake hover before re-attach
ATTACH2_TICKS = 4
LOAD2_TICKS = 3
HOLD2_TICKS = 20
RELEASE_TICKS = 10
TARGET_TRI = 1              # same-column upper facet (centroid z 0.772)
FLYER = 0                   # the relocating channel (sealed S1 facet)
V_CLIMB_MPS = 0.5           # declared climb speed
A_PRESS_NS = 0.0016         # declared approach press
STANDOFF_M = 2.0e-5         # flyer start, outside the 1e-5 contact margin
CAPTURE_WINDOW_M = 5e-3     # declared stop window at the target band
D_MAX_REACH_M = 0.5         # DECLARED fixture reach envelope (C16; x_reach
#                            stays ABSENT -- fixture kinematics, not anatomy)
ENVELOPE_FIRST_TICK = 4     # the done_when tested envelope [4, hold2_end]
Z_TOUCH = 1e-12             # stick arrest window (m/s)
WIN_JN = 1e-9               # N*s, jn == P at the operating point
WIN_JT = 1e-9               # N*s, handover jt == share*g*DT
WIN_LEDGER = 1e-12          # N*s, full-tick ledger identity
WIN_FLIGHT = 1e-12          # m, per-tick flight closed form (non-event)
WIN_RECURSION = 1e-9        # m/s, slip/free-fall velocity recursion
WIN_DISP = 1e-9             # m, displacement recursion after tick 1
WIN_RELEASE_SCALE = 1e-10   # N*s per kg of pad share, release-tick bar
STANDARD_G = 9.80665        # the record-g arithmetic used for the X2
#                            no-flip composition only (the solver G is 9.81)

# the preregistered 8-case transfer battery (section 5) + zero-mu control
TRANSFER_READINGS = (('band_lo', 5.4), ('band_mid', 6.15), ('band_hi', 6.9),
                     ('scene', 10.037998))
TRANSFER_CHANNELS = (2, 3)
ZERO_MU_CONTROL = {'reading': 'band_mid', 'n': 3, 'mu_s': 0.0, 'mu_k': 0.0}

# the G06 phase universe (section 8): the G05 universe was hold/release
PHASES = ('approach', 'attach', 'load', 'hold', 'transfer', 'attach2',
          'load2', 'hold2', 'release')
TIMING_KEYS = ('t_tick', 't_phase', 't_dt_s', 't_seconds')


def require(ok, code, detail=''):
    if not ok:
        raise ValueError(code + (': ' + str(detail) if detail != '' else ''))


def canonical(value):
    import json
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def to_f32(v):
    return struct.unpack('f', struct.pack('f', v))[0]


# ---- vector helpers (3-tuples; G04 heritage forms) ----

def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vscale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def vlen(a):
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def centroid(vertices):
    s = [0.0, 0.0, 0.0]
    for v in vertices:
        s[0] += v[0]
        s[1] += v[1]
        s[2] += v[2]
    n = len(vertices)
    return (s[0] / n, s[1] / n, s[2] / n)


# ---- fixture geometry probes (P7) ----

def target_facet_probe(gc, geom):
    """The X6 run-time coplanarity probe (refusal target_facet_drift): the
    target facet's outward normal equals the source facet's and the source
    centroid lies on the target facet's plane."""
    vs6, tris = geom['vertices_m06'], geom['triangles']
    cen_s, n_s = gc.lateral_facet(vs6, tris, gc.S1_FACET_TRIANGLE)
    cen_t, n_t = gc.lateral_facet(vs6, tris, TARGET_TRI)
    require(vlen(vsub(n_t, n_s)) <= 1e-12, 'target_facet_drift:normal',
            {'source': list(n_s), 'target': list(n_t)})
    offset = abs(_dot(vsub(cen_s, cen_t), n_t))
    require(offset <= 1e-12, 'target_facet_drift:coplanarity', offset)
    return {'source_centroid_m06': list(cen_s), 'target_centroid_m06':
            list(cen_t), 'normal_m06': list(n_t), 'plane_offset_m': offset,
            'travel_m': cen_t[2] - cen_s[2]}


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


# ---- frozen schedule ----

def cruise_ticks(travel_m):
    """The preregistered closed form:
    cruise = floor(travel/(V*DT)) - 1 - (BRAKE-1)//2."""
    v_step = V_CLIMB_MPS * 0.005
    return int(math.floor(travel_m / v_step)) - 1 - (BRAKE_TICKS - 1) // 2


def schedule(geom, gc):
    """The frozen 229-tick schedule for the declared target facet."""
    probe = target_facet_probe(gc, geom)
    travel = probe['travel_m']
    require(travel > 0.0, 'target_facet_drift:travel', travel)
    cruise = cruise_ticks(travel)
    marks = {}
    t = 1
    marks['approach'] = (t, t + APPROACH_TICKS - 1); t += APPROACH_TICKS
    marks['attach'] = (t, t + ATTACH_TICKS - 1); t += ATTACH_TICKS
    marks['load'] = (t, t + LOAD_TICKS - 1); t += LOAD_TICKS
    marks['hold'] = (t, t + HOLD_TICKS - 1); t += HOLD_TICKS
    marks['handover'] = t
    marks['transfer'] = (t, t + 1 + cruise + BRAKE_TICKS + HOVER_TICKS - 1)
    t += 1 + cruise + BRAKE_TICKS + HOVER_TICKS
    marks['reattach'] = t
    marks['attach2'] = (t, t + ATTACH2_TICKS - 1); t += ATTACH2_TICKS
    marks['load2'] = (t, t + LOAD2_TICKS - 1); t += LOAD2_TICKS
    marks['hold2'] = (t, t + HOLD2_TICKS - 1); t += HOLD2_TICKS
    marks['release'] = (t, t + RELEASE_TICKS - 1)
    total = t + RELEASE_TICKS - 1
    marks['total_ticks'] = total
    marks['cruise'] = cruise
    marks['envelope'] = (ENVELOPE_FIRST_TICK, marks['hold2'][1])
    return marks, probe


def phase_of(marks, t):
    for name in ('approach', 'attach', 'load', 'hold'):
        a, b = marks[name]
        if a <= t <= b:
            return name
    if marks['transfer'][0] <= t <= marks['transfer'][1]:
        return 'transfer'
    for name in ('attach2', 'load2', 'hold2'):
        a, b = marks[name]
        if a <= t <= b:
            return name
    return 'release'


# ---- the scenario runner (press + climb channels, full-tick ledger) ----

def run_case(lc, gc, geom, reading_kg, n, mu_s=None, mu_k=None,
             scenario_id=None, injections=None):
    """One transfer scenario through unmodified lc.solve_tick under the
    frozen schedule. Returns (header, rows). The DECLARED handover events
    (holders -> m/(n-1) at the handover tick, back to m/n at re-attach) are
    recorded schedule events; the climb channel is a recorded fixture input
    applied from MEASURED velocity each tick; the full-tick ledger identity
    m*(v_after - v_before) == press + climb + gravity + contact + anchor is
    asserted for every body, every tick."""
    inj = dict(injections or {})
    share = reading_kg / n
    facets = gc.channel_facets(geom, n)
    marks, probe = schedule(geom, gc)
    handover = marks['handover']
    reattach = marks['reattach']
    release_start = marks['release'][0]
    climb_stop = reattach - 1
    # the declared windows: accel at the handover tick, cruise through
    # brake_start-1, the BRAKE_TICKS brake ending at v = 0 exactly at
    # brake_end, then the declared hover through climb_stop
    brake_start = climb_stop - BRAKE_TICKS - HOVER_TICKS + 1
    brake_end = climb_stop - HOVER_TICKS
    total = marks['total_ticks']
    trunk = lc.Body(body_id='trunk_01.lateral',
                    surface_id='trunk_01.lateral', matter_id=gc.TRUNK_MATTER,
                    mass_kg=1.0, mu_s=gc.TRUNK_MU_S, mu_k=gc.TRUNK_MU_K,
                    thickness_m=gc.SOLID_THICKNESS_M,
                    vertices=list(geom['vertices_m06']),
                    triangles=[geom['triangles'][i]
                               for i in geom['lateral_indices']],
                    pinned=True)
    pads, pad_norm = [], []
    for k, (ti, cen, nn) in enumerate(facets):
        ey, ez = gc.orthobasis(nn)
        off = STANDOFF_M if k == FLYER else gc.PAD_OFFSET_M
        origin = gc.vadd(cen, gc.vscale(nn, off))
        pads.append(lc.Body(body_id='grip.pad_%d' % k,
                            surface_id='grip.pad_%d' % k,
                            matter_id='grip_fixture_placeholder_mu',
                            mass_kg=share,
                            mu_s=(gc.PAD_MU_S if mu_s is None else mu_s),
                            mu_k=(gc.PAD_MU_K if mu_k is None else mu_k),
                            thickness_m=gc.SOLID_THICKNESS_M,
                            vertices=list(gc.place_tetra(origin, nn, ey, ez)),
                            triangles=list(gc.TETRA_TRIS), pinned=False))
        pad_norm.append(nn)
    bodies = [trunk] + pads
    flyer = pads[FLYER]
    up = (0.0, 0.0, 1.0)
    z0 = centroid(flyer.vertices)[2] - 0.025   # face-plane height (the tetra
    # centroid rides +0.025 in the vertical ez of the declared placement)
    face_target_z = probe['target_centroid_m06'][2]
    events = []
    last_jt = [0.0] * n
    rows = []

    def climb_target(t):
        """The declared climb servo target (applied from MEASURED velocity):
        hover wherever self-carried, accel/cruise/brake/hover in the flight
        window, zero wherever the grip carries the limb."""
        if handover <= t <= climb_stop:
            if t == handover:
                return V_CLIMB_MPS
            if t < brake_start:
                return V_CLIMB_MPS
            if t <= brake_end:
                return V_CLIMB_MPS * (brake_end - t) / float(BRAKE_TICKS)
            return 0.0                       # the declared post-brake hover
        if t <= marks['attach'][1] or marks['attach2'][0] <= t \
                <= marks['attach2'][1]:
            return 0.0                       # approach/attach/attach2 hover
        return None                          # climb channel OFF

    for tick in range(1, total + 1):
        phase = phase_of(marks, tick)
        pressing = tick < release_start
        flyer_pressed = pressing and not (handover <= tick < reattach)
        holders = [p for i, p in enumerate(pads) if i != FLYER]
        if tick == handover:
            for p in holders:
                p.mass_kg = reading_kg / (n - 1)
            events.append({'tick': tick, 'event': 'handover',
                           'holder_mass_kg': reading_kg / (n - 1)})
        if tick == reattach:
            for p in holders:
                p.mass_kg = share
            events.append({'tick': tick, 'event': 'handover_back',
                           'holder_mass_kg': share})
        v_before = {b.id: b.velocity for b in bodies}
        press = {b.id: [0.0, 0.0, 0.0] for b in bodies}
        climb = {b.id: [0.0, 0.0, 0.0] for b in bodies}
        weld = {b.id: [0.0, 0.0, 0.0] for b in bodies}
        for k, pad in enumerate(pads):
            active = ((k == FLYER and flyer_pressed) or
                      (k != FLYER and pressing))
            if active:
                jn_ns = (A_PRESS_NS if (k == FLYER and
                                        tick <= marks['approach'][1]) else
                         gc.PRESS_JN_NS)
                vec = gc.vscale(pad_norm[k], -jn_ns)     # inward
                pad.velocity = gc.vadd(pad.velocity,
                                       gc.vscale(vec, 1.0 / pad.mass_kg))
                press[pad.id] = list(vec)
        v_target = climb_target(tick)
        if v_target is not None:
            fz = flyer.velocity[2]
            j_up = flyer.mass_kg * (v_target - fz + lc.G * lc.DT)
            vec = (0.0, 0.0, j_up)
            flyer.velocity = gc.vadd(flyer.velocity,
                                     gc.vscale(vec, 1.0 / flyer.mass_kg))
            climb[flyer.id] = list(vec)
        if inj.get('sticky_release') and not pressing:
            # FB4 injection: the impulse a hidden sticky constraint would
            # re-apply after press-off. RECORDED (ledger stays balanced);
            # the release law is what bites on the tampered trace.
            for k, pad in enumerate(pads):
                if last_jt[k] <= 0.0:
                    continue
                vec = (0.0, 0.0, last_jt[k])
                pad.velocity = gc.vadd(pad.velocity,
                                       gc.vscale(vec, 1.0 / pad.mass_kg))
                weld[pad.id] = list(vec)
        if inj.get('hidden_anchor') is not None and \
                marks['transfer'][0] <= tick <= marks['transfer'][1]:
            # FB3 injection: an INVISIBLE per-tick anchor on the flyer --
            # applied to the body but absent from every recorded channel.
            vec = inj['hidden_anchor']
            flyer.velocity = gc.vadd(flyer.velocity,
                                     gc.vscale(vec, 1.0 / flyer.mass_kg))
        if inj.get('teleport_at_tick') == tick:
            # FB1 injection: the teleportation class -- the flyer's vertices
            # jump to the target pose at the handover tick (RECORDED in the
            # header; the continuity law is what bites).
            jump = face_target_z - z0
            flyer.vertices = [gc.vadd(v, (0.0, 0.0, jump))
                              for v in flyer.vertices]
            events.append({'tick': tick, 'event': 'teleport_injection',
                           'dz_m': jump})
        records, ledger = lc.solve_tick(bodies)
        v_after = {b.id: b.velocity for b in bodies}
        resid_max = 0.0
        for b in bodies:
            dv = gc.vsub(v_after[b.id], v_before[b.id])
            lhs = tuple(dv) if b.pinned else gc.vscale(dv, b.mass_kg)
            rhs = gc.vadd(tuple(press[b.id]), tuple(climb[b.id]))
            rhs = gc.vadd(rhs, tuple(weld[b.id]))
            rhs = gc.vadd(rhs, tuple(ledger['gravity'].get(b.id,
                                                          (0.0, 0.0, 0.0))))
            rhs = gc.vadd(rhs, tuple(ledger['contact'][b.id]))
            rhs = gc.vadd(rhs, tuple(ledger['anchor'][b.id]))
            resid = gc.vlen(gc.vsub(lhs, rhs))
            require(resid <= WIN_LEDGER, 'ledger_imbalance:full_tick',
                    {'body': b.id, 'tick': tick, 'resid': resid})
            resid_max = max(resid_max, resid)
        trunk_contact = tuple(ledger['contact'][trunk.id])
        trunk_anchor = tuple(ledger['anchor'][trunk.id])
        require(gc.vlen(gc.vadd(trunk_contact, trunk_anchor)) <= WIN_LEDGER,
                'reaction_concealed',
                {'tick': tick, 'anchor': list(trunk_anchor),
                 'contact': list(trunk_contact)})
        # recorded flight telemetry for the X3 advance model: the flyer's
        # velocity after press+climb (before the solve), plus any event
        # (toc, impulse) pairs from CCD contacts inside the tick.
        flyer_events = []
        for r in records:
            if r['body_a'] == flyer.id or r['body_b'] == flyer.id:
                if r['kind'] == 'ccd' and r.get('toc', 0.0):
                    imp = (r['impulse_on_a'] if r['body_a'] == flyer.id
                           else r['impulse_on_b'])
                    flyer_events.append(
                        {'kind': 'ccd', 'toc': r['toc'],
                         'jn_Ns': r['jn_Ns'], 'jt_Ns': r['jt_Ns'],
                         'impulse_z_on_flyer': imp[2],
                         'tri': r['tri_b'] if r['body_a'] == flyer.id
                         else r['tri_a']})
                    events.append({'tick': tick, 'event': 'flight_contact',
                                   'jn_Ns': r['jn_Ns'],
                                   'toc': r['toc'],
                                   'tri': r['tri_b']
                                   if r['body_a'] == flyer.id
                                   else r['tri_a']})
        flyer_events.sort(key=lambda e: e['toc'])
        row = {'tick': tick, 'phase': phase,
               'flyer_climb_Ns': climb[flyer.id][2],
               'flyer_press_Ns': press[flyer.id][2],
               'flyer_v1z_mps': _flyer_v1z(v_before, press, climb, weld,
                                           flyer),
               'flyer_events': flyer_events,
               'pads': [], 'residual_full_max': resid_max,
               'ledger': {
                   'reciprocity_residual':
                       list(ledger['reciprocity_residual']),
                   'trunk_anchor': list(trunk_anchor),
                   'trunk_contact': list(trunk_contact)}}
        for k, pad in enumerate(pads):
            recs = [r for r in records
                    if r['body_a'] == pad.id or r['body_b'] == pad.id]
            jn_sum = 0.0
            jt_sum = 0.0
            vt_post = 0.0
            modes = set()
            tris = set()
            for r in recs:
                jn_sum += r['jn_Ns']
                jt_sum += r['jt_Ns']
                vt_post = max(vt_post, r['vt_post'])
                modes.add(r['mode'])
                tris.add(r['tri_b'] if r['body_a'] == pad.id
                         else r['tri_a'])
            mode = ('no_contact' if not modes else
                    ('stick' if 'stick' in modes else
                     ('still' if modes == {'still'} else 'slip')))
            if pressing:
                last_jt[k] = jt_sum
            row['pads'].append({
                'k': k, 'jn_sum_Ns': jn_sum, 'jt_sum_Ns': jt_sum,
                'mode': mode, 'vt_post_mps': vt_post,
                'vz_mps': pad.velocity[2],
                'centroid_z_m': centroid(pad.vertices)[2],
                'centroid_m06': list(centroid(pad.vertices)),
                'mass_kg': pad.mass_kg, 'tris': sorted(tris)})
        rows.append(row)
    header = {
        'scenario_id': scenario_id, 'reading_kg': reading_kg, 'n_channels': n,
        'pad_share_kg': share,
        'mu_s': (gc.PAD_MU_S if mu_s is None else mu_s),
        'mu_k': (gc.PAD_MU_K if mu_k is None else mu_k),
        'press_ns': gc.PRESS_JN_NS, 'approach_press_ns': A_PRESS_NS,
        'standoff_m': STANDOFF_M, 'v_climb_mps': V_CLIMB_MPS,
        'brake_ticks': BRAKE_TICKS, 'hover_ticks': HOVER_TICKS,
        'brake_start_tick': brake_start, 'brake_end_tick': brake_end,
        'climb_stop_tick': climb_stop,
        'marks': {k: v for k, v in marks.items()},
        'total_ticks': total, 'flyer_channel': FLYER, 'target_tri': TARGET_TRI,
        'target_probe': probe, 'flyer_face_z0_m': z0,
        'capture_window_m': CAPTURE_WINDOW_M,
        'envelope': marks['envelope'],
        'pinned_bodies': ['trunk_01.lateral'], 'pair_rule': 'elementwise_min',
        'channels': [{'tri': ti, 'centroid_m06': list(cen),
                      'normal_m06': list(nn)} for (ti, cen, nn) in facets],
        'injections': {
            'teleport_at_tick': inj.get('teleport_at_tick'),
            'hidden_anchor': (list(inj['hidden_anchor'])
                              if inj.get('hidden_anchor') is not None
                              else None),
            'sticky_release': bool(inj.get('sticky_release'))},
        'events': events,
        'handover_tick': handover, 'reattach_tick': reattach,
    }
    return header, rows


def _flyer_v1z(v_before, press, climb, weld, flyer):
    """The flyer's velocity after the recorded channels, before the solve
    (the X3 advance-model input; the solve then applies gravity + contact).
    The recorded channels carry IMPULSES (N*s); the velocity change is
    impulse / mass."""
    v0 = v_before[flyer.id]
    m = flyer.mass_kg
    return (v0[2] + (press[flyer.id][2] + climb[flyer.id][2]
                     + weld[flyer.id][2]) / m)


# ---- the declared support law (P6), tick by tick ----

def support_verdicts(header, rows):
    """The preregistered G06 support law per tick. approach: NOT supported
    (the relocating channel is establishing); attach/attach2: every holder
    stick AND the flyer pressed with jn == P; load/hold/load2/hold2: every
    channel stick; transfer: every HOLDING channel stick; release: NOT
    supported."""
    n = header['n_channels']
    marks = header['marks']
    out = []
    for row in rows:
        t = row['tick']
        ph = row['phase']
        flyer = row['pads'][FLYER]
        holding = [pd for k, pd in enumerate(row['pads']) if k != FLYER]
        if ph == 'approach':
            sup, reason = False, 'establishing'
        elif ph in ('attach', 'attach2'):
            ok_flyer = (flyer_pressed(header, t) and
                        abs(flyer['jn_sum_Ns'] - header['press_ns'])
                        <= WIN_JN)
            sup = (all(pd['mode'] == 'stick' for pd in holding)
                   and ok_flyer)
            reason = ('pressed_and_holding' if sup else
                      ('flyer_jn' if not ok_flyer else 'holder_mode'))
        elif ph in ('load', 'hold', 'load2', 'hold2'):
            sup = all(pd['mode'] == 'stick' for pd in row['pads'])
            reason = 'all_stick' if sup else 'mode'
        elif ph == 'transfer':
            sup = all(pd['mode'] == 'stick' for pd in holding)
            reason = 'holding_stick' if sup else 'holding_slip'
        else:
            sup, reason = False, 'release'
        out.append({'tick': t, 'phase': ph, 'supported': bool(sup),
                    'reason': reason,
                    'holding_stick_count':
                        sum(1 for pd in holding if pd['mode'] == 'stick'),
                    'all_stick_count':
                        sum(1 for pd in row['pads']
                            if pd['mode'] == 'stick')})
    return out


def flyer_pressed(header, t):
    handover = header['handover_tick']
    reattach = header['reattach_tick']
    release_start = header['marks']['release'][0]
    return t < release_start and not (handover <= t < reattach)


# ---- closed forms (prereg section 5) ----

def boundary_closed_form(lc, gc, reading_kg, n):
    """(m/(n-1))*g*DT <= mu_s*P -- the sealed G01 stick condition at the
    holding configuration (the declared transfer-admissibility row)."""
    require(n >= 2, 'single_channel_outside_declared_boundary', n)
    m_holder = reading_kg / (n - 1)
    need = m_holder * lc.G * lc.DT
    cap = gc.PAD_MU_S * gc.PRESS_JN_NS
    return {'holder_share_kg': m_holder, 'required_Ns': need,
            'capacity_Ns': cap, 'closes': bool(need <= cap)}


def slip_velocity_recursion(lc, m_holder, mu_k, press_ns, ticks, v0=0.0):
    """v(k) = v(k-1) + g*DT - mu_k*P/m_holder (downward speed; the honest
    non-closing recursion)."""
    vs = []
    v = v0
    for _ in range(ticks):
        v = v + lc.G * lc.DT - mu_k * press_ns / m_holder
        vs.append(v)
    return vs


def freefall_recursion(lc, v0, ticks):
    """v(k) = v(k-1) + g*DT from the measured entry speed."""
    vs = []
    v = v0
    for _ in range(ticks):
        v = v + lc.G * lc.DT
        vs.append(v)
    return vs


def flight_advance_model(lc, header, rows):
    """The X3 per-tick expected face advance from the recorded channels:
    non-event ticks advance v_post_channels*z * DT exactly (gravity cancels
    inside the solve; contact impulses are zero there); event ticks advance
    through the recorded (toc, post-event impulse) segments."""
    expected = []
    for row in rows:
        v1z = row['flyer_v1z_mps']
        segs = []
        v = v1z - lc.G * lc.DT
        t_prev = 0.0
        for ev in row['flyer_events']:
            segs.append((t_prev, ev['toc'], v))
            v = v + ev['impulse_z_on_flyer'] / _flyer_mass(header)
            t_prev = ev['toc']
        segs.append((t_prev, lc.DT, v))
        dz = sum((b - a) * vz for (a, b, vz) in segs)
        expected.append({'tick': row['tick'], 'dz_expected_m': dz,
                         'segments': len(segs)})
    return expected


def _flyer_mass(header):
    return header['reading_kg'] / header['n_channels']


# ---- the G06 observation seam (section 8) ----

def build_seam_module(g05):
    """The G06 seam: the pinned G05 32-slot declared table (imported,
    bit-identical slot semantics) with the task-owned G06 phase universe.
    Same refusal family and discriminator order as the pinned seam."""
    g06_phases = tuple(PHASES)
    declared_keys = frozenset(TIMING_KEYS) | g05.OBS_NAME_SET

    class TransferSeam:
        def __init__(self, scenario_id, dt_s):
            self.scenario_id = scenario_id
            self.dt_s = dt_s
            self.accepted = 0
            self.refusals = []
            self.last_tick = 0

        def _refuse(self, code, detail=''):
            self.refusals.append({'code': code, 'detail': str(detail)[:400]})
            raise ValueError(code + (': ' + str(detail) if detail != ''
                                     else ''))

        def deliver(self, sample):
            keys = set(sample)
            absent = sorted(k for k in keys if k.startswith('x_'))
            if absent:
                self._refuse('named_absent_occupied', absent)
            privileged = sorted(k for k in keys
                                if k in g05.PRIVILEGED_NON_GRATA)
            if privileged:
                self._refuse('privileged_source', privileged)
            extra = sorted(keys - declared_keys)
            if extra:
                self._refuse('undeclared_field', extra)
            missing = sorted(declared_keys - keys)
            if missing:
                self._refuse('undeclared_field', 'missing:' + str(missing))
            tick = sample['t_tick']
            if isinstance(tick, bool) or not isinstance(tick, int) \
                    or tick < 1:
                self._refuse('timing_unbound', {'t_tick': tick})
            if sample['t_phase'] not in g06_phases:
                self._refuse('timing_unbound',
                             {'t_phase': sample['t_phase']})
            dt = sample['t_dt_s']
            if not (isinstance(dt, float) and math.isfinite(dt)
                    and dt > 0.0):
                self._refuse('timing_unbound', {'t_dt_s': dt})
            if dt != self.dt_s:
                self._refuse('timing_drift', {'t_dt_s': dt,
                                              'declared': self.dt_s})
            if abs(sample['t_seconds'] - tick * self.dt_s) > 1e-12:
                self._refuse('timing_drift',
                             {'t_seconds': sample['t_seconds']})
            if tick <= self.last_tick:
                self._refuse('timing_drift',
                             'non_monotone:%d<=%d' % (tick, self.last_tick))
            for name in g05.OBS_NAMES:
                v = sample[name]
                if not isinstance(v, float) or not math.isfinite(v):
                    self._refuse('nonfinite_value', {name: v})
            if len([k for k in keys if k in g05.OBS_NAME_SET]) \
                    != g05.OBS_DIM:
                self._refuse('dim_mismatch', len(keys))
            self.last_tick = tick
            self.accepted += 1
            return True

        def census(self):
            return {'scenario_id': self.scenario_id,
                    'accepted': self.accepted,
                    'refusals': list(self.refusals)}

    return TransferSeam


# ---- sample projection (the declared four-way channel mapping) ----

def project_sample(g05, header, verdict_row, row, dt_s):
    """Project one recorded row + its support verdict into the declared
    sample. Channel flags use the G06 four-way recorded mode: contact =
    mode != no_contact, stick = (mode == stick), slip = (mode == slip); a
    still tick is honestly contact=1, stick=0, slip=0. agg_supported_flag
    is the P6 verdict (the G06 projection law for the new phases; identical
    to the pinned G05 law on hold/release)."""
    tick = row['tick']
    sample = {'t_tick': tick, 't_phase': row['phase'], 't_dt_s': dt_s,
              't_seconds': tick * dt_s}
    n = header['n_channels']
    sup_row = verdict_row
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
            cz = pd['centroid_z_m']
            disp = pd.get('disp_down_cum_m', 0.0)
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
    sample['agg_support_count'] = to_f32(float(sup_row['all_stick_count']))
    sample['agg_supported_flag'] = to_f32(1.0 if sup_row['supported']
                                          else 0.0)
    sample['agg_release_flag'] = to_f32(1.0 if row['phase'] == 'release'
                                        else 0.0)
    sample['agg_trunk_anchor_z_Ns'] = to_f32(row['ledger']['trunk_anchor'][2])
    sample['agg_ledger_residual_max_Ns'] = to_f32(row['residual_full_max'])
    sample['agg_reciprocity_max_Ns'] = to_f32(
        max(abs(v) for v in row['ledger']['reciprocity_residual']))
    avail = g05.SLOTS_PER_CHANNEL * n + 8
    sample['obs_mask_mean'] = to_f32(avail / g05.OBS_DIM)
    sample['obs_frac_avail'] = to_f32(((1 if n > 0 else 0) + 2) / 5.0)
    return sample


def cumulative_down_disp(rows):
    """Per-pad cumulative downward displacement (G04 row semantics:
    downward positive), measured from the recorded centroid heights."""
    n = len(rows[0]['pads'])
    out = [0.0] * n
    z_prev = None
    for row in rows:
        zs = [pd['centroid_z_m'] for pd in row['pads']]
        if z_prev is not None:
            for k in range(n):
                out[k] += z_prev[k] - zs[k]
                row['pads'][k]['disp_down_cum_m'] = out[k]
        z_prev = zs
    return out
