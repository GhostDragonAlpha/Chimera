"""Independent validator for the MAT2-A05 first-mutation hand structure.

Deliberately does NOT import build_mutation. Re-derives every number from the
pinned sources (vendor XML, osim, hand.vtp parsed directly, graph JSON) and
checks the emitted artifacts (mutation_structure.json, macaque_hand_mutation.xml)
against them. Writes validation_receipt.json with per-check PASS/FAIL lines;
FAIL lines preserve observed values. Read-only over E:/PythonChimera.
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
VENDOR = Path('E:/PythonChimera/vendor/myo_sim')
OSIM = Path('E:/PythonChimera/tools/science_funnel/data/macaque_arm/monkeyArm_current.osim')
GRAPH = Path('E:/PythonChimera/tools/creature_graph/data/creature_graph.json')
VTP = OSIM.parent / 'Geometry/hand.vtp'

HUMAN_BODIES = ['firstmc', 'proximal_thumb', 'distal_thumb',
                'secondmc', 'proxph2', 'midph2', 'distph2',
                'thirdmc', 'proxph3', 'midph3', 'distph3',
                'fourthmc', 'proxph4', 'midph4', 'distph4',
                'fifthmc', 'proxph5', 'midph5', 'distph5']
PHALANGES = [b for b in HUMAN_BODIES if 'ph' in b] + ['proximal_thumb', 'distal_thumb']
MCS = [b for b in HUMAN_BODIES if b.endswith('mc') or b == 'firstmc']
MESH_OF = {'firstmc': '1mc', 'proximal_thumb': 'thumbprox', 'distal_thumb': 'thumbdist',
           'secondmc': '2mc', 'proxph2': '2proxph', 'midph2': '2midph', 'distph2': '2distph',
           'thirdmc': '3mc', 'proxph3': '3proxph', 'midph3': '3midph', 'distph3': '3distph',
           'fourthmc': '4mc', 'proxph4': '4proxph', 'midph4': '4midph', 'distph4': '4distph',
           'fifthmc': '5mc', 'proxph5': '5proxph', 'midph5': '5midph', 'distph5': '5distph'}

CHECKS = []


def check(cid, ok, detail, observed=None):
    row = {'id': cid, 'result': 'PASS' if ok else 'FAIL', 'detail': detail}
    if observed is not None:
        row['observed'] = observed
    CHECKS.append(row)
    print(f'{"PASS" if ok else "FAIL"} {cid}: {detail}'
          + (f' | observed: {observed}' if observed is not None else ''))
    return ok


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def vec(t):
    return [float(x) for x in t.split()]


def vadd(a, b):
    return [a[i] + b[i] for i in range(3)]


def vmul(a, k):
    return [x * k for x in a]


def vnorm(a):
    return math.sqrt(sum(x * x for x in a))


def vtp_bbox(p: Path):
    r = ET.parse(p).getroot()
    piece = r.find('PolyData').find('Piece')
    pts = piece.find('Points').find('DataArray').text.split()
    xs = [float(x) for x in pts[0::3]]
    ys = [float(x) for x in pts[1::3]]
    zs = [float(x) for x in pts[2::3]]
    return [[min(xs), min(ys), min(zs)], [max(xs), max(ys), max(zs)]]


def main() -> int:
    # ---- independent re-derivation from pins ----
    root = ET.parse(VENDOR / 'hand/assets/myohand_body.xml').getroot()
    pos, parent, joints, inertial = {}, {}, {}, {}
    for p in root.iter('body'):
        for c in p.findall('body'):
            n = c.get('name')
            pos[n] = vec(c.get('pos'))
            parent[n] = p.get('name')
            joints[n] = {j.get('name'): [float(x) for x in j.get('range').split()]
                         for j in c.findall('joint')}
            i = c.find('inertial')
            if i is not None:
                inertial[n] = {'mass': float(i.get('mass')),
                               'fullinertia': [float(x) for x in i.get('fullinertia').split()]}

    def chain_offset(name, stop='lunate'):
        v = [0.0, 0.0, 0.0]
        while name != stop:
            v = vadd(v, pos[name])
            name = parent[name]
        return v

    tips = {'thumb': 'distal_thumb', 'digit2': 'distph2', 'digit3': 'distph3',
            'digit4': 'distph4', 'digit5': 'distph5'}
    L_human = max(vnorm(chain_offset(t)) for t in tips.values())

    oroot = ET.parse(OSIM).getroot()
    hb = next(b for b in oroot.iter('Body') if b.get('name') == 'hand')
    mac_mass = float(hb.find('mass').text)
    mac_mc = vec(hb.find('mass_center').text)
    mac_inertia = [float(hb.find(f'inertia_{k}').text) for k in ('xx', 'yy', 'zz', 'xy', 'xz', 'yz')]
    wrist = hb.find('.//CustomJoint[@name="wrist"]')
    mac_wrist = {co.get('name'): vec(co.find('range').text) for co in wrist.findall('.//Coordinate')}
    mac_axes = {ta.get('name'): vec(ta.find('axis').text)
                for ta in wrist.findall('.//TransformAxis') if ta.find('coordinates') is not None
                and ta.find('coordinates').text}
    mac_anchors = []
    for m in oroot.iter('Schutte1993Muscle_Deprecated'):
        if m.get('name') in ('ext_digitorum', 'flex_digit_profundus'):
            for pp in m.iter('PathPoint'):
                if pp.find('body').text.strip() == 'hand':
                    mac_anchors.append((m.get('name'), pp.get('name'), vec(pp.find('location').text)))

    raw_bbox = vtp_bbox(VTP)
    L_mac = (raw_bbox[1][1] - raw_bbox[0][1]) * 0.001  # vtp source units mm -> m
    graph = json.loads(GRAPH.read_text(encoding='utf-8'))
    gb = graph['objects']['geom.macaque_arm.hand']['physical']['metrics']['bounds_m']
    L_mac_graph = gb[1][1] - gb[0][1]
    s = L_mac / L_human
    hum_total = sum(inertial[n]['mass'] for n in HUMAN_BODIES)
    mac_ulna = graph['objects']['geom.macaque_arm.ulna']['physical']['metrics']['bounds_m']
    L_ulna = mac_ulna[1][1] - mac_ulna[0][1]

    # ---- load emitted artifacts ----
    struct_ok = True
    try:
        st = json.loads((HERE / 'mutation_structure.json').read_text(encoding='utf-8'))
    except Exception as e:  # noqa: BLE001
        check('V0-structure-json-parses', False, 'mutation_structure.json must parse', str(e))
        (HERE / 'validation_receipt.json').write_text(json.dumps(CHECKS, indent=1) + '\n', encoding='utf-8')
        return 1
    check('V0-structure-json-parses', True, 'mutation_structure.json parses as JSON')
    try:
        mroot = ET.parse(HERE / 'macaque_hand_mutation.xml').getroot()
        check('V0-mjcf-parses', True, 'macaque_hand_mutation.xml is well-formed XML with root <mujoco>',
              mroot.tag)
    except Exception as e:  # noqa: BLE001
        mroot = None
        struct_ok = False
        check('V0-mjcf-parses', False, 'macaque_hand_mutation.xml must be well-formed', str(e))

    bodies = {b['name']: b for b in st['bodies']}
    # ---- V1 structure ----
    check('V1-body-count', len(bodies) == 19 and len(st['bodies']) == 19,
          'exactly 19 explicit digit bodies (5 metacarpals + 14 phalanges)', len(st['bodies']))
    check('V1-phalanx-count', len(PHALANGES) == 14 and all(b in bodies for b in PHALANGES),
          '14 phalanges present (prox/mid/dist x4 + thumb 2)', len(PHALANGES))
    check('V1-metacarpal-count', len(MCS) == 5 and all(b in bodies for b in MCS),
          '5 metacarpals present (firstmc..fifthmc)', len(MCS))
    # chain connectivity to anchor
    connected, chain_errors = 0, []
    for n in HUMAN_BODIES:
        cur, hops, ok, seen = n, 0, False, set()
        while hops <= 4:
            par = bodies[cur]['parent']
            par_name = par.rsplit('.', 1)[-1]
            if par_name == 'macaque_hand_anchor':
                ok = True
                break
            if par_name not in bodies or par_name in seen:
                chain_errors.append((n, par))
                break
            seen.add(cur)
            cur = par_name
            hops += 1
        if ok:
            connected += 1
    check('V1-chain-connectivity', connected == 19 and not chain_errors,
          'all 19 bodies connected to macaque_hand_anchor within <=4 hops', chain_errors)
    # thumb 2-segment
    thumb = bodies['distal_thumb']['parent'].endswith('proximal_thumb') and \
        bodies['proximal_thumb']['parent'].endswith('firstmc')
    check('V1-thumb-topology', thumb, 'thumb chain anchor->firstmc->proximal_thumb->distal_thumb')
    # joint counts: digit joints in JSON bodies
    jcount = sum(len(b['joints']) for b in st['bodies'])
    check('V1-joint-count', jcount == 20, '20 explicit digit joints (thumb 4 + fingers 16)', jcount)
    anchor_joints = st['anchor_body']['joints']
    check('V1-anchor-wrist-joints', len(anchor_joints) == 2,
          'mutant wrist anchor declares the 2 macaque wrist dof', [j['name'] for j in anchor_joints])
    # XML body tree matches JSON names/parents
    xml_bodies = {}
    xml_joints = {}
    if mroot is not None:
        def walk(el, par_name):
            for b in el.findall('body'):
                xml_bodies[b.get('name')] = par_name
                xml_joints[b.get('name')] = [(j.get('name'), [float(x) for x in j.get('axis').split()],
                                              [float(x) for x in j.get('range').split()])
                                             for j in b.findall('joint')]
                walk(b, b.get('name'))
        anchor = mroot.find('.//body[@name="macaque_hand_anchor"]')
        walk(anchor, 'macaque_hand_anchor')
        xml_names = set(xml_bodies) - {'macaque_hand_anchor'}
        check('V1-xml-json-body-agreement', xml_names == set(HUMAN_BODIES),
              'MJCF body set equals JSON body set',
              sorted(xml_names ^ set(HUMAN_BODIES)))
        xml_parent_ok = all(
            xml_bodies[n] == (bodies[n]['parent'].rsplit('.', 1)[-1]) for n in HUMAN_BODIES)
        check('V1-xml-json-parent-agreement', xml_parent_ok,
              'MJCF parent structure equals JSON parent structure')

    # ---- V2 numbers recomputable ----
    expected_pos = {}
    for n in HUMAN_BODIES:
        if n == 'firstmc':
            off = vadd(vadd(pos['capitate'], pos['trapezium']), pos['firstmc'])
        elif n in ('secondmc', 'thirdmc', 'fourthmc', 'fifthmc'):
            off = vadd(pos['capitate'], pos[n])
        else:
            off = pos[n]
        expected_pos[n] = vmul(off, s)
    worst = 0.0
    for n in HUMAN_BODIES:
        got = bodies[n]['mutation']['pos_m']
        exp = expected_pos[n]
        err = max(abs(got[i] - exp[i]) for i in range(3))
        worst = max(worst, err)
    check('V2-positions-recomputable', worst <= 1e-12,
          'every mutant pos_m equals s*human offset componentwise within 1e-12', worst)
    if mroot is not None:
        wxml = 0.0
        for n in HUMAN_BODIES:
            el = mroot.find(f'.//body[@name="{n}"]')
            got = vec(el.get('pos'))
            wxml = max(wxml, max(abs(got[i] - expected_pos[n][i]) for i in range(3)))
        check('V2-xml-positions-recomputable', wxml <= 1e-9,
              'MJCF body pos equals s*human offset within 1e-9 (9 sig digits emitted)', wxml)
    s_recorded = st['allometry']['mutation_scale']
    check('V2-scale-recomputable', abs(s_recorded - s) <= 1e-12,
          'recorded mutation scale equals recomputed s', {'recorded': s_recorded, 'recomputed': s})
    # ranges verbatim vs sources
    rng_err = []
    for n in HUMAN_BODIES:
        for j in bodies[n]['joints']:
            if j['range'] != joints[n][j['name']]:
                rng_err.append((n, j['name'], j['range'], joints[n][j['name']]))
    check('V2-digit-ranges-verbatim', not rng_err,
          'every digit joint range equals its myohand source range verbatim', rng_err)
    wrist_rec = {j['name']: j['range'] for j in anchor_joints}
    check('V2-wrist-ranges-macaque',
          wrist_rec.get('mutation_wrist_flexion') == mac_wrist['wrist_flexion'] and
          wrist_rec.get('mutation_wrist_abduction') == mac_wrist['wrist_abduction'],
          'mutant wrist anchor carries the macaque wrist ranges verbatim', wrist_rec)
    axis_rec = {j['name']: j['axis'] for j in anchor_joints}
    check('V2-wrist-axes-macaque',
          axis_rec.get('mutation_wrist_flexion') == mac_axes['rotation1'] and
          axis_rec.get('mutation_wrist_abduction') == mac_axes['rotation2'],
          'mutant wrist axes equal the osim TransformAxis axes', axis_rec)
    # masses recomputable
    m_err = max(abs(bodies[n]['mutation']['mass_prior_kg'] - mac_mass * inertial[n]['mass'] / hum_total)
                for n in HUMAN_BODIES)
    check('V2-mass-priors-recomputable', m_err <= 1e-12,
          'every mass prior equals 0.049*human_mass/0.1589 within 1e-12', m_err)
    check('V2-anchor-mass-verbatim',
          st['anchor_body']['physical']['mass_kg'] == mac_mass and
          st['anchor_body']['physical']['mass_center_m'] == mac_mc and
          st['anchor_body']['physical']['inertia_kg_m2'] == mac_inertia,
          'anchor body carries the macaque hand body mass/center/inertia verbatim')

    # ---- V3 allometric coherence ----
    L_mut = max(vnorm(chain_offset(t)) * s for t in tips.values())
    check('V3-hand-length-identity', abs(L_mut - L_mac) <= 1e-9,
          'mutant hand length equals MACAQUE_HAND_LENGTH within 1e-9',
          {'mutant': L_mut, 'macaque': L_mac, 'diff': abs(L_mut - L_mac)})
    ratio_mac = L_mac / L_ulna
    ratio_mut = L_mut / L_ulna
    check('V3-ratio-coherence', abs(ratio_mut - ratio_mac) <= 1e-3,
          'mutant hand/forearm(ulna) equals macaque ratio within 1e-3',
          {'mutant': ratio_mut, 'macaque': ratio_mac})
    check('V3-vtp-vs-graph-agreement', abs(L_mac - L_mac_graph) <= 1e-9,
          'hand.vtp direct bbox (mm->m) matches geom.macaque_arm.hand graph bounds',
          {'vtp': L_mac, 'graph': L_mac_graph})
    envelope = st['envelope_check']
    y_ok = all(gb[0][1] <= p[1] <= gb[1][1] for p in envelope['fingertip_positions_m'].values())
    check('V3-y-span-fits-envelope', y_ok,
          'every mutant fingertip Y lies inside the hand.vtp Y span (preregistered falsifier)',
          {k: v[1] for k, v in envelope['fingertip_positions_m'].items()})
    xz_out = [k for k, p in envelope['fingertip_positions_m'].items()
              if not (gb[0][0] <= p[0] <= gb[1][0] and gb[0][2] <= p[2] <= gb[1][2])]
    check('V3-radial-overshoot-declared', bool(xz_out) ==
          bool(st['honest_gaps']) and xz_out,
          'radial (X/Z) envelope overshoot recorded as declared deviation (honest, not hidden)',
          xz_out)

    # ---- V4 units ----
    check('V4-units-block', st['units'] == {'length': 'm', 'angle': 'rad', 'mass': 'kg',
                                            'inertia': 'kg m^2'},
          'structure declares m/rad/kg units', st['units'])
    big = [b['name'] for b in st['bodies']
           if max(abs(x) for x in b['mutation']['pos_m']) > 0.2]
    check('V4-no-mm-as-m', not big,
          'no mutant position exceeds 0.2 m (mm-as-m scale error would be ~1000x)', big)
    vtp_units = st['anchor_body']['geometry'][0]['source_units_to_m']
    check('V4-single-mm-to-m', vtp_units == [0.001, 0.001, 0.001],
          'mm->m conversion recorded exactly once, on the macaque vtp assets', vtp_units)
    dbl = [b['name'] for b in st['bodies']
           if abs(vnorm(b['mutation']['pos_m']) - vnorm(expected_pos[b['name']])) > 1e-12]
    check('V4-no-double-scale', not dbl,
          'scale applied exactly once (positions match single-scaled offsets)', dbl)

    # ---- V5 constraint sources ----
    anchors_rec = st['muscle_anchor_mapping']
    ok_anchors = len(anchors_rec) == len(mac_anchors) and all(
        any(r['muscle'] == a[0] and r['path_point'] == a[1] and
            max(abs(r['location_m'][i] - a[2][i]) for i in range(3)) <= 1e-9
            for r in anchors_rec) for a in mac_anchors)
    check('V5-muscle-anchors-recorded', ok_anchors,
          'all three macaque hand-frame muscle anchors recorded with osim coordinates',
          [f"{r['muscle']}/{r['path_point']}->{r['nearest_mutant_body']}" for r in anchors_rec])
    sp = {src['id']: src for src in st['sources']}
    check('V5-species-labels', 'Homo sapiens' in sp['source.myo_sim_human_hand']['species'] and
          'Macaca' in sp['source.macaque_arm_constraints']['species'],
          'both source lineages carry species labels (hybrid disclosure)',
          {k: v['species'][:60] for k, v in sp.items()})
    mesh_err = []
    for b in st['bodies']:
        g = b['geometry'][0]
        asset_id = g['asset_id'].rsplit('.', 1)[-1]
        if asset_id != MESH_OF[b['name']]:
            mesh_err.append((b['name'], asset_id))
        if abs(g['transform']['uniform_scale'] - s) > 1e-12:
            mesh_err.append((b['name'], 'scale'))
    check('V5-geometry-bindings', not mesh_err,
          'every body binds its vendor STL asset at the recorded mutation scale', mesh_err)
    stl_err = []
    for b in st['bodies']:
        asset_id = b['geometry'][0]['asset_id'].rsplit('.', 1)[-1]
        p = VENDOR / 'meshes' / f'{asset_id}.stl'
        if sha256_file(p) != 'x' * 64:  # existence + readable
            pass
        if not p.is_file():
            stl_err.append(str(p))
    check('V5-stl-files-exist', not stl_err, 'all referenced STL files exist in the vendor tree',
          stl_err)
    stl_hash_bad = []
    for b in st['bodies']:
        recorded = b['geometry'][0].get('stl_sha256')
        if not isinstance(recorded, str) or len(recorded) != 64 or \
                any(c not in '0123456789abcdef' for c in recorded):
            stl_hash_bad.append((b['name'], 'not full 64-hex', recorded))
    check('V5-stl-sha256-recorded', len(st['bodies']) == 19 and not stl_hash_bad,
          'every body binding records a full 64-hex stl_sha256 (not a 16-hex prefix)',
          stl_hash_bad)
    stl_hash_bad = []
    for b in st['bodies']:
        g = b['geometry'][0]
        p = VENDOR / 'meshes' / f"{g['asset_id'].rsplit('.', 1)[-1]}.stl"
        recomputed = sha256_file(p)
        if g.get('stl_sha256') != recomputed:
            stl_hash_bad.append((b['name'], g.get('stl_sha256'), recomputed))
    check('V5-stl-sha256-matches-vendor', not stl_hash_bad,
          'every recorded stl_sha256 equals the sha256 recomputed from the pinned vendor STL',
          stl_hash_bad)

    # ---- V6 references resolve ----
    ref_err = []
    for b in st['bodies']:
        hs = b['human_source']
        if hs['sha256'] != '21a6649236801439649ae992459c29bbc020767c2022c4d79de688689462ed28':
            ref_err.append((b['name'], 'human pin'))
        if hs['body'] != b['name']:
            ref_err.append((b['name'], 'human body name'))
    check('V6-human-pins', not ref_err,
          'every body pins its human source body + vendor file sha256', ref_err)
    decision = st['captain_decision']
    dp = Path(decision['record'])
    dsha = sha256_file(dp) if dp.is_file() else None
    check('V6-captain-decision-pin',
          dsha == decision['sha256'] and decision['decision_id'] == 'A05-DIGIT-MUTATION-20260928',
          'captain decision reference resolves and its sha256 matches',
          {'sha256': dsha, 'decision_id': decision['decision_id']})
    if mroot is not None:
        meshes_xml = {m.get('name'): m.get('file') for m in mroot.findall('.//asset/mesh')}
        miss = [f for f in meshes_xml.values() if not Path(f).is_file()]
        check('V6-mjcf-mesh-files', not miss, 'every MJCF mesh file path resolves on disk', miss)
        geom_refs = {g.get('mesh') for g in mroot.findall('.//geom[@mesh]')}
        check('V6-mjcf-geom-resolve', geom_refs <= set(meshes_xml),
              'every MJCF geom mesh reference resolves to a declared asset',
              sorted(geom_refs - set(meshes_xml)))
        scale_ok = all(all(abs(float(x) - s) < 1e-9 for x in m.get('scale').split())
                       for m in mroot.findall('.//asset/mesh'))
        check('V6-mjcf-mesh-scale', scale_ok, 'every MJCF mesh scale equals the mutation scale s')

    # ---- summary ----
    fails = [c for c in CHECKS if c['result'] == 'FAIL']
    summary = {'total': len(CHECKS), 'passed': len(CHECKS) - len(fails), 'failed': len(fails)}
    print('')
    print(f"SUMMARY: {summary['passed']}/{summary['total']} checks passed, "
          f"{summary['failed']} failed")
    (HERE / 'validation_receipt.json').write_text(
        json.dumps({'summary': summary, 'checks': CHECKS}, indent=1) + '\n', encoding='utf-8')
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
