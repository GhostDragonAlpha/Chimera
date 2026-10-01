"""MAT2-G04 physical grip contact fixture (PREREGISTRATION.md, frozen).

Attachment, friction, reaction loads and release operate through the
physical solver without invisible anchors. The solver is MAT2-M06's
``chimera.local_contact.v1`` (``local_contact.py``) -- the SAME local
contact and material interface implementation ground locomotion (MAT2-F04)
vendored byte-identical and hash-asserted. This card imports it, asserts
its sha256 against the frozen pin, and never forks it.

Grip mechanics, all inside the solver:
- ATTACHMENT: a DECLARED external press-impulse channel (per tick, per pad,
  ``P = 0.30 N*s`` inward along the facet normal -- the sealed F03 S1
  operating point ``jn/dt = 60 N``). Recorded every tick; the full-tick
  ledger identity ``m*dv == press + weld + gravity + contact + anchor``
  (measured directly from body velocities) is asserted every tick. No bond
  or sticky constraint exists in production; when the press stops nothing
  holds.
- FRICTION: M06's Coulomb stick/slip law with the ``elementwise_min`` pair
  rule. mu_s = 0.6 / mu_k = 0.4 are the NAMED placeholders (FRICTION_SOURCES
  verdict: no lawful measured pin exists for macaque volar skin on bark at
  the operating load; REPIN ORDER 2 holds; acquisition stays this card's
  recorded debt).
- REACTION LOADS: the trunk is the only pinned body (declared rooted), so
  its per-tick anchor reaction is a RECORDED, re-verified ledger entry
  (visible anchor), and the pad-side support travels through the contact
  impulses only.
- RELEASE: press channel set to 0 -> jn -> 0 -> jt -> 0 -> free fall.

``sticky_release_weld`` / ``hidden_anchor`` are FALSIFIER-ONLY injection
hooks (FB1/FB3): production callers never set them; every injection is
recorded in the scenario header.

CPU-only, stdlib-only, deterministic (no RNG, no wall clock). Refusals are
named codes; nothing is silently repaired.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent

SCHEMA = 'chimera.g04_grip.v1'

# ---- the established interface: imported, hash-asserted, never forked ----
INTERFACE_REL = '../MAT2-M06/local_contact.py'
INTERFACE_SHA256 = '1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc'


def load_interface(interface_rel=INTERFACE_REL, expected_sha=INTERFACE_SHA256):
    """Import the pinned M06 local_contact module after asserting its bytes.
    Refusals: interface_pin_missing / interface_pin_drift."""
    path = (HERE / interface_rel).resolve()
    if not path.exists():
        raise ValueError('interface_pin_missing:' + str(path))
    raw = path.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != expected_sha:
        raise ValueError('interface_pin_drift:' + got)
    spec = importlib.util.spec_from_file_location('g04_pinned_local_contact',
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---- frozen fixture constants (PREREGISTRATION sections 2-4) ----
TRUNK_MESH_REL = '../MAT2-F03/assets/trunk_01_mesh.json'
TRUNK_MESH_SHA256 = ('3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820'
                     'cef6ee7')
BASE_XYZ = (11.976783, 0.0, 2.471766)     # trunk base centre, f01 frame
TRUNK_MATTER = 'wood_trunk_01'            # F03 material layer
TRUNK_MU_S = 0.6                          # F03 declared placeholder layer
TRUNK_MU_K = 0.6
PAD_MU_S = 0.6                            # NAMED placeholder (G04 debt)
PAD_MU_K = 0.4                            # NAMED placeholder (M06 block)
SOLID_THICKNESS_M = 0.0                   # F03 heritage; no shell invented
PAD_OFFSET_M = 0.9e-5                     # inside MARGIN 1e-5; bias stays 0
PRESS_JN_NS = 0.30                        # the sealed F03 S1 press impulse
HOLD_TICKS = 20
RELEASE_TICKS = 10
TETRA_LOCAL = ((0.0, 0.0, 0.0), (0.1, 0.0, 0.0), (0.0, 0.1, 0.0),
               (0.0, 0.0, 0.1))
TETRA_TRIS = ((0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3))  # outward, right
S1_FACET_TRIANGLE = 0                     # the sealed F03 S1 lateral facet
S1_FACET_CENTROID_M06 = [0.036763, -0.002406, 0.386]
S1_FACET_NORMAL_M06 = [0.9951835289511874, -0.09802930023345664, 0.0]
# the two DISTINCT body readings (sealed register; never averaged)
READINGS_KG = (('band_lo', 5.4), ('band_mid', 6.15), ('band_hi', 6.9),
               ('scene', 10.037998))
CHANNELS = (1, 2, 3)
# closed-form window set (PREREGISTRATION section 5)
WIN_JN = 1e-9           # N*s, jn_pad == P
WIN_VT = 1e-12          # m/s, stick arrest (F03 S1 bar)
WIN_RECURSION_V = 1e-9  # m/s, slip/free-fall velocity recursion
WIN_DISP = 1e-9         # m, displacement recursion after tick 1
WIN_LEDGER = 1e-12      # N*s, full-tick ledger identity
WIN_RELEASE = 1e-12     # N*s, post-release jn/jt zero bar (exact-contact
#                        branch); see WIN_RELEASE_SCALE below for the
#                        sliding-tick noise bar (prereg amendment a2)
WIN_RELEASE_SCALE = 1e-10   # N*s per kg of pad share: the release-tick
#                        (jn, jt) bar is share_kg * WIN_RELEASE_SCALE --
#                        the closest-feature normal carries O(1e-12)
#                        absolute float noise, so a sliding pad's
#                        separating velocity projects onto it as
#                        ~ share * |v| * 6e-12 (measured development
#                        shakedown worst 1.17e-11 per kg; amendment a2)
ZERO_MU_CONTROL = {'reading': 'band_mid', 'n': 3, 'mu_s': 0.0, 'mu_k': 0.0}
# named absent variables (verbatim provenance inherited from sealed G01)
NAMED_ABSENT = (
    ('x_press', 'measured grip-force actuator bound behind the normal press',
     'measured maximum isometric force (or measured PCSA plus measured '
     'specific tension) for the selected animal; the sealed carrier Fmax '
     'values are 22 derived-provisional / 6 provenance-unknown / 11 '
     'hand-set defaults (20260921 memo verdict), not source-backed'),
    ('x_share', 'per-port load share (contact force partition)',
     'Per-port load share is UNPINNED (no partition source).'),
    ('x_aperture', 'achievable grasp aperture (joint limits, C05 inputs)',
     'Joint axes, attachment frames, limits, chain topology'),
    ('x_reach', 'hand-to-trunk placement transform T_hand_trunk',
     'every packaged position carries its source frame declaration; NO '
     'transform is composed between frames and NO new fit is recorded '
     '(C01: the round-trip/handedness/landmark verification is registered '
     'as still REQUIRED downstream)'),
    ('x_com', 'grasp-posture centre-of-mass offset from the grip axis',
     'the 9 unresolved bodies hand_l, hand_r, talus_l, talus_r, thorax, '
     'toes_l, toes_r, ulna, ulna_l carry ZERO transported mass'),
    ('x_inertia', 'adopted-assembly body inertia in a grasp posture',
     'NOT runtime-qualified: TC-8 measured inputs absent (0/8 ports, '
     'honest refusal stands); drive table not re-declared (TC-3 '
     're-declare pending from the assembly\'s own sealed sources)'),
    ('x_trajectory', 'transfer trajectory',
     'NOT runtime-qualified: TC-8 measured inputs absent (0/8 ports, '
     'honest refusal stands); drive table not re-declared (TC-3 '
     're-declare pending from the assembly\'s own sealed sources)'),
    ('x_sequence', 'support sequence for vertical transfer',
     'Support sequence, body inertia, forces, transfer trajectory, work'),
    ('x_losses', 'transfer losses (dynamic balance)',
     'Duty factor and contact channels MISSING from the sealed walk trace'),
    ('x_trunk_strength', 'measured trunk/root structural strength bound',
     'none (rigid and rooted; optional per card context); validated by '
     'unmodified M04 validate_passive_law (profile rigid)'),
)
def require(ok, code, detail=''):
    if not ok:
        raise ValueError(code + (': ' + str(detail) if detail != '' else ''))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


# ---- vector helpers (3-tuples; F03 heritage forms) ----

def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vscale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def vdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def vlen(a):
    return math.sqrt(vdot(a, a))


def vnorm(a):
    n = vlen(a)
    require(n > 0.0, 'degenerate_normal')
    return (a[0] / n, a[1] / n, a[2] / n)


def to_m06_frame(p, base=BASE_XYZ):
    """The pinned asset's own frame_transform_to_m06 map (no other transform
    is composed anywhere in this card)."""
    return (p[0] - base[0], -(p[2] - base[2]), p[1] - base[1])


# ---- pinned trunk geometry (asset in-repo; hash-asserted) ----

def load_trunk_geometry(mesh_rel=TRUNK_MESH_REL,
                        expected_sha=TRUNK_MESH_SHA256):
    """Read the pinned F03 trunk asset, assert its bytes, partition by the
    F03 per-triangle rule, return vertices in the M06 frame plus lateral
    triangle indices."""
    path = (HERE / mesh_rel).resolve()
    if not path.exists():
        raise ValueError('input_pin_missing:' + str(path))
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError('input_pin_drift:' + str(path))
    doc = json.loads(raw.decode('utf-8'))
    require(doc.get('object_id') == 'trunk_01', 'input_pin_drift:object_id')
    vs6 = [to_m06_frame(p) for p in doc['vertices_f01_world_y_up']]
    lateral = [i for i, t in enumerate(doc['triangles'])
               if 128 not in t and 129 not in t]
    require(len(lateral) == 64, 'trunk_partition:lateral', len(lateral))
    return {'vertices_m06': vs6, 'triangles': doc['triangles'],
            'lateral_indices': lateral, 'raw': doc}


def lateral_facet(vs6, triangles, tri_index):
    """(centroid, outward unit normal) of one lateral facet. Outward = the
    normal whose in-plane direction points away from the trunk axis."""
    t = triangles[tri_index]
    a, b, c = vs6[t[0]], vs6[t[1]], vs6[t[2]]
    cen = vscale(vadd(vadd(a, b), c), 1.0 / 3.0)
    n = vnorm(vcross(vsub(b, a), vsub(c, a)))
    radial = (cen[0], cen[1], 0.0)
    if vdot(n, radial) < 0.0:
        n = vscale(n, -1.0)
    return cen, n


def channel_facets(geom, n_channels):
    """PREREGISTERED selection: channel 0 is the sealed F03 S1 facet
    (lateral triangle 0); channel k>0 is the same-height-band facet whose
    centroid azimuth is nearest to azimuth(channel_0) + 360*k/n degrees
    (ties to the lowest triangle index). Refusal: channel_band_mismatch."""
    vs6, tris = geom['vertices_m06'], geom['triangles']
    lat = geom['lateral_indices']
    cen0, n0 = lateral_facet(vs6, tris, S1_FACET_TRIANGLE)
    require(abs(cen0[0] - S1_FACET_CENTROID_M06[0]) < 1e-9
            and abs(cen0[1] - S1_FACET_CENTROID_M06[1]) < 1e-9
            and abs(cen0[2] - S1_FACET_CENTROID_M06[2]) < 1e-9,
            'channel_band_mismatch:s1_facet', cen0)
    require(abs(n0[0] - S1_FACET_NORMAL_M06[0]) < 1e-9
            and abs(n0[1] - S1_FACET_NORMAL_M06[1]) < 1e-9
            and abs(n0[2] - S1_FACET_NORMAL_M06[2]) < 1e-9,
            'channel_band_mismatch:s1_normal', n0)
    az0 = math.degrees(math.atan2(cen0[1], cen0[0])) % 360.0
    band = []
    for ti in lat:
        cen, _ = lateral_facet(vs6, tris, ti)
        if abs(cen[2] - cen0[2]) > 1e-6:
            continue
        band.append((ti, cen))
    require(len(band) == 32, 'channel_band_mismatch:count', len(band))
    out = [(S1_FACET_TRIANGLE, cen0, n0)]
    for k in range(1, n_channels):
        want = (az0 + 360.0 * k / n_channels) % 360.0
        best = None
        for ti, cen in band:
            az = math.degrees(math.atan2(cen[1], cen[0])) % 360.0
            d = min(abs(az - want), 360.0 - abs(az - want))
            if best is None or (d, ti) < best[0]:
                best = ((d, ti), cen)
        (d, ti), cen = best
        _, nrm = lateral_facet(vs6, tris, ti)
        out.append((ti, cen, nrm))
    return out


def orthobasis(n):
    """F03 _orthobasis heritage."""
    a = (0.0, 0.0, 1.0) if abs(n[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = vnorm(vcross(a, n))
    v = vcross(n, u)
    return u, v


def place_tetra(origin, ex, ey, ez):
    """F03 _place_tetra heritage: local vertex k -> origin + ex*x + ey*y +
    ez*z (the contact face is the local x=0 face, tri (0,3,2))."""
    return tuple(tuple(origin[i] + ex[i] * p[0] + ey[i] * p[1] + ez[i] * p[2]
                       for i in range(3)) for p in TETRA_LOCAL)


def tangent_dir(n):
    """Gravity direction projected off the facet normal (the slide axis,
    pointing DOWN the wall)."""
    g = (0.0, 0.0, -1.0)
    t = vsub(g, vscale(n, vdot(g, n)))
    return vnorm(t)


# ---- scenario runner (the press channel + full-tick ledger) ----

def run_scenario(lc, geom, reading_kg, n_channels, mu_s=PAD_MU_S,
                 mu_k=PAD_MU_K, press_ns=PRESS_JN_NS,
                 hold_ticks=HOLD_TICKS, release_ticks=RELEASE_TICKS,
                 scenario_id=None, sticky_release_weld=False,
                 hidden_anchor=None):
    """One grip scenario through unmodified lc.solve_tick.

    Returns (header, rows); one row per tick with per-pad scalars.
    """
    share = reading_kg / n_channels
    facets = channel_facets(geom, n_channels)
    trunk = lc.Body(body_id='trunk_01.lateral', surface_id='trunk_01.lateral',
                    matter_id=TRUNK_MATTER, mass_kg=1.0, mu_s=TRUNK_MU_S,
                    mu_k=TRUNK_MU_K, thickness_m=SOLID_THICKNESS_M,
                    vertices=list(geom['vertices_m06']),
                    triangles=[geom['triangles'][i]
                               for i in geom['lateral_indices']],
                    pinned=True)
    pads = []
    pad_norm = []
    for k, (ti, cen, n) in enumerate(facets):
        ey, ez = orthobasis(n)
        origin = vadd(cen, vscale(n, PAD_OFFSET_M))
        verts = place_tetra(origin, n, ey, ez)   # ex = n: face x=0 faces trunk
        pads.append(lc.Body(
            body_id='grip.pad_%d' % k, surface_id='grip.pad_%d' % k,
            matter_id='grip_fixture_placeholder_mu',
            mass_kg=share, mu_s=mu_s, mu_k=mu_k,
            thickness_m=SOLID_THICKNESS_M, vertices=list(verts),
            triangles=list(TETRA_TRIS), pinned=False))
        pad_norm.append(n)
    bodies = [trunk] + pads
    up_dir = vscale(tangent_dir(pad_norm[0]), -1.0)   # UP the wall

    def pad_centroid_z(pad):
        s = 0.0
        for v in pad.vertices:
            s += v[2]
        return s / len(pad.vertices)

    rows = []
    z_prev = [pad_centroid_z(p) for p in pads]
    last_jt = [0.0] * n_channels
    total_ticks = hold_ticks + release_ticks
    for tick in range(1, total_ticks + 1):
        pressing = tick <= hold_ticks
        v_before_press = {b.id: b.velocity for b in bodies}
        press = {b.id: [0.0, 0.0, 0.0] for b in bodies}
        weld = {b.id: [0.0, 0.0, 0.0] for b in bodies}
        if pressing:
            for k, pad in enumerate(pads):
                vec = vscale(pad_norm[k], -press_ns)     # inward
                pad.velocity = vadd(pad.velocity,
                                    vscale(vec, 1.0 / pad.mass_kg))
                press[pad.id] = list(vec)
        if sticky_release_weld and not pressing:
            # FB1 injection: the weld a hidden sticky constraint would
            # create. RECORDED (so the ledger stays balanced); the RELEASE
            # law (jn=jt=0, free fall) is what bites on the tampered trace.
            for k, pad in enumerate(pads):
                if last_jt[k] <= 0.0:
                    continue
                vec = vscale(up_dir, last_jt[k])
                pad.velocity = vadd(pad.velocity,
                                    vscale(vec, 1.0 / pad.mass_kg))
                weld[pad.id] = list(vec)
        if hidden_anchor is not None and pressing:
            # FB3 injection: an INVISIBLE anchor -- applied to the body but
            # deliberately absent from every recorded channel.
            pad = pads[0]
            pad.velocity = vadd(pad.velocity,
                                vscale(hidden_anchor, 1.0 / pad.mass_kg))
        records, ledger = lc.solve_tick(bodies)
        v_after = {b.id: b.velocity for b in bodies}
        # Full-tick identity measured DIRECTLY from velocities:
        #   m*(v_after - v_before_press) ==
        #     press + weld + gravity + contact + anchor      (per body)
        residual_full = {}
        for b in bodies:
            dv = vsub(v_after[b.id], v_before_press[b.id])
            lhs = tuple(dv) if b.pinned else vscale(dv, b.mass_kg)
            rhs = vadd(tuple(press[b.id]), tuple(weld[b.id]))
            rhs = vadd(rhs, tuple(ledger['gravity'].get(b.id,
                                                        (0.0, 0.0, 0.0))))
            rhs = vadd(rhs, tuple(ledger['contact'][b.id]))
            rhs = vadd(rhs, tuple(ledger['anchor'][b.id]))
            resid = vsub(lhs, rhs)
            residual_full[b.id] = list(resid)
            require(vlen(resid) <= WIN_LEDGER, 'ledger_imbalance:full_tick',
                    {'body': b.id, 'tick': tick, 'resid': list(resid)})
        # Trunk anchor reaction re-verified externally (PREREG section 5):
        # the recorded anchor equals minus the summed contact impulse.
        trunk_contact = tuple(ledger['contact'][trunk.id])
        trunk_anchor = tuple(ledger['anchor'][trunk.id])
        require(vlen(vadd(trunk_contact, trunk_anchor)) <= WIN_LEDGER,
                'reaction_concealed',
                {'tick': tick, 'anchor': list(trunk_anchor),
                 'contact': list(trunk_contact)})
        row = {'tick': tick, 'phase': 'hold' if pressing else 'release',
               'pads': [], 'weld_recorded_ns': {
                   pid: vlen(tuple(v)) for pid, v in weld.items()},
               'ledger': {
                   'reciprocity_residual':
                       list(ledger['reciprocity_residual']),
                   'trunk_anchor': list(trunk_anchor),
                   'trunk_contact': list(trunk_contact),
                   'residual_full_max':
                       max(vlen(tuple(v)) for v in residual_full.values())}}
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
            z_now = pad_centroid_z(pad)
            disp = z_prev[k] - z_now       # downward positive (gravity -z)
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
        'mu_s': mu_s, 'mu_k': mu_k, 'press_ns': press_ns,
        'hold_ticks': hold_ticks, 'release_ticks': release_ticks,
        'pad_offset_m': PAD_OFFSET_M, 'trunk_surface': 'trunk_01.lateral',
        'pair_rule': 'elementwise_min',
        'pair_mu_s': min(mu_s, TRUNK_MU_S), 'pair_mu_k': min(mu_k, TRUNK_MU_K),
        'pinned_bodies': ['trunk_01.lateral'],
        'injections': {'sticky_release_weld': bool(sticky_release_weld),
                       'hidden_anchor':
                           list(hidden_anchor) if hidden_anchor is not None
                           else None},
        'channels': [{'tri': ti, 'centroid_m06': list(cen),
                      'normal_m06': list(nrm)}
                     for (ti, cen, nrm) in facets],
    }
    return header, rows


# ---- closed forms (PREREG section 5) ----

def closed_form_slip(lc, m_pad, mu_k, press_ns, ticks):
    """v(k) = v(k-1) + g*DT - mu_k*P/m_pad (exact tangential recursion)."""
    g, dt = lc.G, lc.DT
    vs = []
    v = 0.0
    for _ in range(ticks):
        v = v + g * dt - mu_k * press_ns / m_pad
        vs.append(v)
    return vs


def closed_form_freefall(lc, v0, ticks):
    """v(k) = v(k-1) + g*DT from initial tangential speed v0."""
    g, dt = lc.G, lc.DT
    vs = []
    v = v0
    for _ in range(ticks):
        v = v + g * dt
        vs.append(v)
    return vs


def stick_expected(lc, m_pad, mu_s, press_ns):
    """Per-channel stick iff (m/n)*g*DT <= mu_s*P (PREREG section 5)."""
    return m_pad * lc.G * lc.DT <= mu_s * press_ns


def boundary_prediction(lc):
    """The 12-row closed-form table: 'reading|n=k' -> 'STICK'/'SLIP'."""
    table = {}
    for name, kg in READINGS_KG:
        for n in CHANNELS:
            table[scenario_label(name, n)] = (
                'STICK' if stick_expected(lc, kg / n, PAD_MU_S, PRESS_JN_NS)
                else 'SLIP')
    return table


def g01_boundary_rows(receipt_path):
    """Parse the pinned G01 feasibility receipt case table into
    {(reading, n): friction_feasible} (host pin; sha verified by the
    run_experiments pin gate before this is called)."""
    doc = json.loads(pathlib.Path(receipt_path).read_text(encoding='utf-8'))
    out = {}
    for row in doc['derivation']['case_table']:
        out[(row['reading'], row['n_channels'])] = bool(
            row['friction_feasible'])
    return out


def scenario_label(reading, n):
    return '%s|n=%d' % (reading, n)


BATTERY = tuple(scenario_label(name, n)
                for name, _ in READINGS_KG for n in CHANNELS)
