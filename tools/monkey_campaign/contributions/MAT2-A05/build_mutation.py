"""Build the MAT2-A05 "first mutation" hand structure from pinned sources.

Read-only inputs (verified by sha256 before use):
  - E:/PythonChimera/vendor/myo_sim @ 33f3ded946f55adbdcf963c99999587aadaf975f
    hand/assets/myohand_body.xml (human per-digit base topology + numbers)
    meshes/{1mc..5mc, thumbprox, thumbdist, 2..5{proxph,midph,distph}}.stl
  - E:/PythonChimera/tools/science_funnel/data/macaque_arm/monkeyArm_current.osim
    (macaque hand mass, wrist ranges/axes, digit-named muscle hand-frame anchors)
  - E:/PythonChimera/tools/creature_graph/data/creature_graph.json
    (geom.macaque_arm.hand bounds_m + intake conventions)

Writes ONLY into this contribution directory:
  macaque_hand_mutation.xml  - MJCF structure record (bodies, joints, scaled mesh refs)
  mutation_structure.json    - graph-intake-style record (stable ids, pins, units, species labels)
  derivation_output.txt      - this run's printed arithmetic

Pure derivation; no GPU, no mesh authoring, no writes outside this directory.
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
VENDOR_REV = '33f3ded946f55adbdcf963c99999587aadaf975f'
OSIM = Path('E:/PythonChimera/tools/science_funnel/data/macaque_arm/monkeyArm_current.osim')
GRAPH = Path('E:/PythonChimera/tools/creature_graph/data/creature_graph.json')
MODEL = 'macaque_arm_hand_mutation'
REF = f'ref.{MODEL}'
GEOM = f'geom.{MODEL}'

BODY_XML_SHA = '21a6649236801439649ae992459c29bbc020767c2022c4d79de688689462ed28'
FINGER_XML_SHA = '6975e5c56d2adbd41c1b9ad8cdbece90b84611c80288337338adc7951a8b4b5f'
OSIM_SHA = '4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895'
GRAPH_SHA = None  # computed + recorded, graph file is large; pinned by content below
HAND_VTP_SHA = 'a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6'

HUMAN_BODIES = ['firstmc', 'proximal_thumb', 'distal_thumb',
                'secondmc', 'proxph2', 'midph2', 'distph2',
                'thirdmc', 'proxph3', 'midph3', 'distph3',
                'fourthmc', 'proxph4', 'midph4', 'distph4',
                'fifthmc', 'proxph5', 'midph5', 'distph5']
MESHES = ['1mc', 'thumbprox', 'thumbdist',
          '2mc', '2proxph', '2midph', '2distph',
          '3mc', '3proxph', '3midph', '3distph',
          '4mc', '4proxph', '4midph', '4distph',
          '5mc', '5proxph', '5midph', '5distph']
BODY_MESH = dict(zip(HUMAN_BODIES, MESHES))


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def vec(text):
    return [float(x) for x in text.split()]


def vsub(a, b):
    return [a[i] - b[i] for i in range(3)]


def vadd(a, b):
    return [a[i] + b[i] for i in range(3)]


def vmul(a, k):
    return [x * k for x in a]


def vnorm(a):
    return math.sqrt(sum(x * x for x in a))


def stl_metrics(p: Path) -> dict:
    data = p.read_bytes()
    n = struct.unpack_from('<I', data, 80)[0]
    verts = set()
    xs, ys, zs = [], [], []
    for i in range(n):
        off = 84 + i * 50 + 12
        for v in range(3):
            x, y, z = struct.unpack_from('<3f', data, off + v * 12)
            verts.add((x, y, z))
            xs.append(x); ys.append(y); zs.append(z)
    return {'triangles': n, 'vertices_unique': len(verts),
            'bounds_source_m': [[min(xs), min(ys), min(zs)], [max(xs), max(ys), max(zs)]]}


def main() -> int:
    out = []

    def say(line=''):
        out.append(line)
        print(line)

    # ---------- pin verification ----------
    say('== source pin verification ==')
    pins = {}
    for name, path, expect in [
        ('myohand_body.xml', VENDOR / 'hand/assets/myohand_body.xml', BODY_XML_SHA),
        ('finger_v0.xml', VENDOR / 'finger/finger_v0.xml', FINGER_XML_SHA),
        ('monkeyArm_current.osim', OSIM, OSIM_SHA),
        ('hand.vtp', OSIM.parent / 'Geometry/hand.vtp', HAND_VTP_SHA),
    ]:
        got = sha256_file(path)
        assert got == expect, f'sha256 mismatch {path}: {got}'
        pins[name] = {'path': str(path).replace('\\', '/'), 'sha256': got}
        say(f'OK {path} sha256={got}')
    graph_sha = sha256_file(GRAPH)
    pins['creature_graph.json'] = {'path': str(GRAPH).replace('\\', '/'), 'sha256': graph_sha}
    say(f'OK {GRAPH} sha256={graph_sha}')
    graph = json.loads(GRAPH.read_text(encoding='utf-8'))
    hand_geom_node = graph['objects']['geom.macaque_arm.hand']
    assert hand_geom_node['physical']['asset']['sha256'] == HAND_VTP_SHA

    # ---------- human base ----------
    say('')
    say('== human base: myohand_body.xml chain extraction ==')
    root = ET.parse(VENDOR / 'hand/assets/myohand_body.xml').getroot()
    pos, parent, joints, inertial, mesh_of = {}, {}, {}, {}, {}
    for p in root.iter('body'):
        for c in p.findall('body'):
            n = c.get('name')
            pos[n] = vec(c.get('pos'))
            parent[n] = p.get('name')
            joints[n] = [{'name': j.get('name'), 'axis': j.get('axis'),
                          'range': [float(x) for x in j.get('range').split()]}
                         for j in c.findall('joint')]
            if n in HUMAN_BODIES:
                assert c.get('euler') is None and c.get('quat') is None, n
            i = c.find('inertial')
            if i is not None:
                inertial[n] = {'mass': float(i.get('mass')),
                               'fullinertia': [float(x) for x in i.get('fullinertia').split()]}
            g = c.find('geom[@mesh]')
            if g is not None:
                mesh_of[n] = g.get('mesh')
    for n in HUMAN_BODIES:
        assert mesh_of.get(n) == BODY_MESH[n], (n, mesh_of.get(n))
    say('digit bodies carry no euler/quat: chain geometry is pure translation composition')

    def chain_offset(name, stop='lunate'):
        v = [0.0, 0.0, 0.0]
        while name != stop:
            v = vadd(v, pos[name])
            name = parent[name]
        return v

    chains = {'thumb': 'distal_thumb', 'digit2': 'distph2', 'digit3': 'distph3',
              'digit4': 'distph4', 'digit5': 'distph5'}
    say('human chain displacement from lunate origin (m):')
    hum_len = {}
    for k, tip in chains.items():
        v = chain_offset(tip)
        hum_len[k] = vnorm(v)
        say(f'  {k}: vector=[{v[0]:+.6f},{v[1]:+.6f},{v[2]:+.6f}] |v|={hum_len[k]:.6f}')
    L_human = max(hum_len.values())
    say(f'HUMAN_HAND_LENGTH = max chain displacement = {L_human:.6f} m (digit 3)')

    human_mass_total = sum(inertial[n]['mass'] for n in HUMAN_BODIES)
    say(f'human 19-digit-body mass sum = {human_mass_total:.4f} kg')

    # human forearm reference
    rb = stl_metrics(VENDOR / 'meshes/radius.stl')
    lunate_off = pos['lunate']  # radius-local wrist position
    L_forearm_human = abs(lunate_off[1]) + rb['bounds_source_m'][1][1]
    say(f'human radius.stl tris={rb["triangles"]} +Y extent={rb["bounds_source_m"][1][1]:.6f} m; '
        f'wrist(lunate y)={lunate_off[1]:.6f}; L_forearm_human={L_forearm_human:.6f} m')
    ratio_human = L_human / L_forearm_human
    say(f'human hand/forearm ratio = {L_human:.6f}/{L_forearm_human:.6f} = {ratio_human:.4f}')

    # ---------- macaque constraints ----------
    say('')
    say('== macaque constraints: monkeyArm_current.osim + graph geom node ==')
    oroot = ET.parse(OSIM).getroot()
    hand_body = next(b for b in oroot.iter('Body') if b.get('name') == 'hand')
    mac_mass = float(hand_body.find('mass').text)
    mac_mc = vec(hand_body.find('mass_center').text)
    inertias = [float(hand_body.find(f'inertia_{k}').text) for k in ('xx', 'yy', 'zz', 'xy', 'xz', 'yz')]
    say(f'macaque hand body: mass={mac_mass} kg mass_center={mac_mc} inertia={inertias}')
    wrist = hand_body.find('.//CustomJoint[@name="wrist"]')
    mac_wrist = {}
    for co in wrist.findall('.//Coordinate'):
        mac_wrist[co.get('name')] = vec(co.find('range').text)
    say(f'macaque wrist ranges (rad): {mac_wrist}')
    mac_axes = {}
    for ta in wrist.findall('.//TransformAxis'):
        mac_axes[ta.get('name')] = {'coordinates': ta.find('coordinates').text,
                                    'axis': vec(ta.find('axis').text)}
    say(f'macaque wrist transform axes: {mac_axes}')

    mac_muscle_anchors = []
    for m in oroot.iter('Schutte1993Muscle_Deprecated'):
        if m.get('name') not in ('ext_digitorum', 'flex_digit_profundus'):
            continue
        for pp in m.iter('PathPoint'):
            if pp.find('body').text.strip() != 'hand':
                continue
            mac_muscle_anchors.append({'muscle': m.get('name'), 'path_point': pp.get('name'),
                                       'location_m': vec(pp.find('location').text)})
    for a in mac_muscle_anchors:
        say(f'macaque muscle anchor on hand body: {a["muscle"]}/{a["path_point"]} '
            f'location_m=[{a["location_m"][0]:+.8f},{a["location_m"][1]:+.8f},{a["location_m"][2]:+.8f}]')

    gb = hand_geom_node['physical']['metrics']['bounds_m']
    L_mac = gb[1][1] - gb[0][1]
    say(f'MACAQUE_HAND_LENGTH = geom.macaque_arm.hand bounds_m Y extent = {L_mac:.8f} m')

    ulna = stl_metrics(OSIM.parent / 'Geometry/ulna.vtp') if False else None
    # ulna.vtp is VTP not STL; read its Y extent via the graph node
    ulna_node = graph['objects']['geom.macaque_arm.ulna']['physical']['metrics']['bounds_m']
    radius_node = graph['objects']['geom.macaque_arm.radius']['physical']['metrics']['bounds_m']
    L_ulna = ulna_node[1][1] - ulna_node[0][1]
    L_radius = radius_node[1][1] - radius_node[0][1]
    say(f'macaque forearm refs (m): ulna Y extent={L_ulna:.6f}, radius Y extent={L_radius:.6f}')
    ratio_mac = L_mac / L_ulna
    say(f'macaque hand/forearm(ulna) ratio = {L_mac:.8f}/{L_ulna:.6f} = {ratio_mac:.4f}')

    # ---------- mutation scale ----------
    say('')
    say('== mutation scale formula ==')
    s = L_mac / L_human
    say(f's = MACAQUE_HAND_LENGTH / HUMAN_HAND_LENGTH = {L_mac:.8f} / {L_human:.6f} = {s:.9f}')
    ratio_mut = (L_human * s) / L_ulna
    say(f'mutant hand/forearm(ulna) ratio = {L_human * s:.8f}/{L_ulna:.6f} = {ratio_mut:.4f} '
        f'(macaque {ratio_mac:.4f}; human base {ratio_human:.4f})')

    # ---------- mutant bodies ----------
    say('')
    say('== mutant bodies: anchor-relative positions (m) ==')
    anchor_pos = {}
    # thumb: firstmc sits under trapezium under capitate (carpals folded into palm anchor)
    anchor_pos['firstmc'] = vmul(vadd(vadd(pos['capitate'], pos['trapezium']), pos['firstmc']), s)
    for d in ('second', 'third', 'fourth', 'fifth'):
        anchor_pos[f'{d}mc'] = vmul(vadd(pos['capitate'], pos[f'{d}mc']), s)
    chain_parent = {n: parent[n] for n in HUMAN_BODIES}
    for n in HUMAN_BODIES:
        if n not in anchor_pos:
            anchor_pos[n] = vmul(pos[n], s)
    for n in HUMAN_BODIES:
        o = anchor_pos[n]
        say(f'  {n}: parent={chain_parent[n] if chain_parent[n] in HUMAN_BODIES else "macaque_hand_anchor"} '
            f'pos=[{o[0]:+.6f},{o[1]:+.6f},{o[2]:+.6f}] |pos|={vnorm(o):.6f}')

    mutant_chain_len = {k: vnorm(chain_offset(tip)) * s for k, tip in chains.items()}
    for k, v in mutant_chain_len.items():
        say(f'  mutant {k} chain length = {v:.6f} m')
    L_mut = max(mutant_chain_len.values())
    say(f'MUTANT_HAND_LENGTH = {L_mut:.8f} m (target {L_mac:.8f}, diff {abs(L_mut - L_mac):.2e})')

    tip_anchor = {k: chain_offset(tip) for k, tip in chains.items()}
    say('mutant fingertip anchor-frame positions (m):')
    for k in chains:
        t = vmul(tip_anchor[k], s)
        inside = (gb[0][0] <= t[0] <= gb[1][0], gb[0][1] <= t[1] <= gb[1][1], gb[0][2] <= t[2] <= gb[1][2])
        say(f'  {k}: [{t[0]:+.6f},{t[1]:+.6f},{t[2]:+.6f}] inside hand.vtp bbox XYZ={inside}')

    # muscle anchor -> nearest mutant body mapping (rest pose, anchor frame)
    world = {'macaque_hand_anchor': [0.0, 0.0, 0.0]}
    order = []
    def place(n):
        if n in world:
            return world[n]
        p = place(chain_parent[n] if chain_parent[n] in HUMAN_BODIES else 'macaque_hand_anchor')
        w = vadd(p, anchor_pos[n])
        world[n] = w
        order.append(n)
        return w
    for n in HUMAN_BODIES:
        place(n)
    say('muscle anchor mapping (rest pose, nearest mutant body):')
    muscle_map = []
    for a in mac_muscle_anchors:
        best, bd = None, None
        for n in ['macaque_hand_anchor'] + HUMAN_BODIES:
            d = vnorm(vsub(a['location_m'], world[n]))
            if bd is None or d < bd:
                best, bd = n, d
        a = dict(a, nearest_mutant_body=best, distance_m=bd)
        muscle_map.append(a)
        say(f'  {a["muscle"]}/{a["path_point"]} -> {best} (distance {bd:.6f} m)')

    # mass priors
    say('mutant per-body mass priors (formula: 0.049 * human_mass / %.4f):' % human_mass_total)
    mass_prior = {n: mac_mass * inertial[n]['mass'] / human_mass_total for n in HUMAN_BODIES}
    for n in HUMAN_BODIES:
        say(f'  {n}: human {inertial[n]["mass"]} -> {mass_prior[n]:.6f} kg')

    # mesh metrics at mutation scale
    say('mutant geometry assets (vendor STL @ uniform scale s):')
    geom_assets = {}
    for m in MESHES:
        p = VENDOR / 'meshes' / f'{m}.stl'
        met = stl_metrics(p)
        b = met['bounds_source_m']
        bounds_m = [[s * b[0][0], s * b[0][1], s * b[0][2]], [s * b[1][0], s * b[1][1], s * b[1][2]]]
        geom_assets[m] = {'path': str(p).replace('\\', '/'), 'sha256': sha256_file(p),
                          'triangles': met['triangles'], 'vertices_unique': met['vertices_unique'],
                          'bounds_source_m': b, 'bounds_m': bounds_m}
        say(f'  {m}.stl sha256={geom_assets[m]["sha256"][:16]}... tris={met["triangles"]} '
            f'verts={met["vertices_unique"]}')

    # ---------- emit mutation_structure.json ----------
    sp = {'id': 'source.myo_sim_human_hand',
          'kind': 'model_definition',
          'name': 'Human myo_sim hand framework (mutation base)',
          'status': 'derived_from',
          'species': 'Homo sapiens (MoBL-ARD myo_sim human hand, human-derived base structure)',
          'source_revision': VENDOR_REV,
          'pins': [pins['myohand_body.xml'], pins['finger_v0.xml']],
          'note': 'Vendor clone is unpinned upstream MyoHub/myo_sim; rev + file sha256 recorded at use time.'}
    mp = {'id': 'source.macaque_arm_constraints',
          'kind': 'model_definition',
          'name': 'Pinned macaque arm research model (mutation constraints)',
          'status': 'extracted',
          'species': 'Macaca mulatta (Limblab monkeyArm research model; original specimen/mesh ancestry unconfirmed per source receipt)',
          'source_revision': '4fb7dddeec06a0df9525c18f37234a824cb1b5b1',
          'pins': [pins['monkeyArm_current.osim'], pins['hand.vtp'], pins['creature_graph.json']]}
    bodies_json = []
    for n in HUMAN_BODIES:
        par = chain_parent[n] if chain_parent[n] in HUMAN_BODIES else 'macaque_hand_anchor'
        b = {'id': f'{REF}.body.{n}', 'kind': 'model_definition', 'name': n,
             'status': 'authored',
             'species': ('hybrid: human base structure (myo_sim @' + VENDOR_REV[:7] + ') scaled toward '
                         'macaque constraints (macaque_arm research model); species mixing DECLARED per '
                         'Captain decision A05-DIGIT-MUTATION-20260928'),
             'human_source': {'body': n, 'file': pins['myohand_body.xml']['path'],
                              'sha256': pins['myohand_body.xml']['sha256'],
                              'offset_m': pos[n], 'inertial': inertial.get(n)},
             'mutation': {'scale': s, 'pos_m': anchor_pos[n],
                          'mass_prior_kg': mass_prior[n],
                          'mass_prior_formula': f'{mac_mass} kg * {inertial[n]["mass"]} / {human_mass_total} kg',
                          'carpal_chain_folded_into_anchor': parent[n] not in HUMAN_BODIES},
             'physical': {'name': n, 'mass_kg': mass_prior[n],
                          'mass_center_m': [0.0, 0.0, 0.0],
                          'inertia_kg_m2': [x * (mass_prior[n] / inertial[n]['mass']) * (s ** 2)
                                            for x in inertial[n]['fullinertia']],
                          'mass_scope': 'declared training prior; proportional redistribution of the macaque hand mass over digit chains (not additive with the anchor mass)',
                          'frame': 'macaque_arm_hand_mutation_frame', 'units': 'm/rad/kg'},
             'parent': f'{REF}.body.{par}' if par in HUMAN_BODIES else f'{REF}.body.macaque_hand_anchor',
             'joints': joints[n],
             'geometry': [{'asset_id': f'{GEOM}.{BODY_MESH[n]}',
                           'stl_sha256': geom_assets[BODY_MESH[n]]['sha256'],
                           'transform': {'uniform_scale': s, 'source_units': 'm'},
                           'why_scaled_reference': 'no macaque phalanx mesh exists in-repo (PR #229/#230 search); vendor human STL reused at recorded mutation scale'}]}
        bodies_json.append(b)
    structure = {
        'schema': 'chimera.anatomical_assembly.v1',
        'id': f'model.{MODEL}',
        'title': 'MAT2-A05 first mutation: human myo_sim hand framework modified toward macaque anatomy',
        'captain_decision': {'decision_id': 'A05-DIGIT-MUTATION-20260928',
                             'record': 'E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-A05/CAPTAIN_DECISION_2_MUTATION.json',
                             'sha256': None,  # filled below
                             'authority': 'Captain (highest)'},
        'task': {'task_id': 'MAT2-A05', 'attempt_id': 'b4ad70883ac2480a928dcc828f33c65f',
                 'arrival_id': 'arrival-b22e42ce0ecf4204acb2f99d0aecff97',
                 'criteria_sha256': '34411771f7bd5dea2ec2cc4775d44b33df422e5454d283eae40676d1e3346544'},
        'units': {'length': 'm', 'angle': 'rad', 'mass': 'kg', 'inertia': 'kg m^2'},
        'species_disclosure': 'Hybrid derivation: human per-digit topology and base bone shapes; macaque scale, wrist ranges, hand mass, muscle anchors and frame. Declared adaptation per Captain decision 2, not a species-true scan claim.',
        'sources': [sp, mp],
        'frame': {'frame_id': 'macaque_arm_hand_mutation_frame',
                  'units': 'm',
                  'anchor': 'macaque hand body origin (wrist joint location 0 0 0 of the macaque wrist custom joint)',
                  'long_axis': '-Y, coincident with hand.vtp span'},
        'anchor_body': {'id': f'{REF}.body.macaque_hand_anchor', 'name': 'macaque_hand_anchor',
                        'status': 'extracted',
                        'physical': {'name': 'macaque hand body (verbatim osim values)',
                                     'mass_kg': mac_mass, 'mass_center_m': mac_mc,
                                     'inertia_kg_m2': inertias,
                                     'mass_scope': 'effective body segment, not isolated visible bone',
                                     'mass_note': 'anchor mass and digit mass priors are alternative allocation views of the same 0.049 kg macaque hand mass, not additive'},
                        'joints': [
                            {'name': 'mutation_wrist_flexion',
                             'coordinates': 'wrist_flexion', 'axis': mac_axes['rotation1']['axis'],
                             'range': mac_wrist['wrist_flexion'],
                             'source': 'monkeyArm_current.osim wrist TransformAxis rotation1'},
                            {'name': 'mutation_wrist_abduction',
                             'coordinates': 'wrist_abduction', 'axis': mac_axes['rotation2']['axis'],
                             'range': mac_wrist['wrist_abduction'],
                             'source': 'monkeyArm_current.osim wrist TransformAxis rotation2'}],
                        'geometry': [{'asset_id': 'geom.macaque_arm.hand (external, extracted graph node)',
                                      'path': 'Geometry/hand.vtp',
                                      'sha256': HAND_VTP_SHA,
                                      'source_units_to_m': [0.001, 0.001, 0.001],
                                      'note': 'macaque hand envelope; VTP is not MuJoCo-loadable so the MJCF anchor carries no mesh geom; the binding is recorded here'}]},
        'bodies': bodies_json,
        'muscle_anchor_mapping': muscle_map,
        'allometry': {'human_hand_length_m': L_human, 'macaque_hand_length_m': L_mac,
                      'mutation_scale': s, 'mutant_hand_length_m': L_mut,
                      'human_forearm_m': L_forearm_human, 'macaque_ulna_m': L_ulna,
                      'human_ratio': ratio_human, 'macaque_ratio': ratio_mac,
                      'mutant_ratio': ratio_mut,
                      'formula': 's = MACAQUE_HAND_LENGTH / HUMAN_HAND_LENGTH; mutant offset = s * human offset (componentwise)',
                      'tolerance': {'identity_1e-9': abs(L_mut - L_mac) <= 1e-9,
                                    'ratio_1e-3': abs(ratio_mut - ratio_mac) <= 1e-3}},
        'envelope_check': {'hand_vtp_bounds_m': gb,
                           'fingertip_positions_m': {k: vmul(tip_anchor[k], s) for k in chains},
                           'note': 'Y-span coherence is the preregistered falsifier; radial (X/Z) thumb overshoot is a declared deviation, recorded per axis'},
        'honest_gaps': [
            'no macaque per-phalanx proportions exist in-repo; a uniform allometric scale is applied instead',
            'no per-phalanx macaque mass data; masses are declared proportional training priors',
            'carpals are not duplicated as mutant bodies; the macaque hand body owns the carpus (mass/geometry)',
            'muscle/tendon paths are anchor points only; no muscle volume or skin geometry',
            'no dynamic simulation, no GPU work: pure derivation record'],
    }
    decision_path = Path('E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-A05/CAPTAIN_DECISION_2_MUTATION.json')
    decision_sha = sha256_file(decision_path)
    structure['captain_decision']['sha256'] = decision_sha
    say('')
    say(f'captain decision record sha256: {decision_sha}')

    # ---------- emit MJCF ----------
    def fmt(v):
        return ' '.join(f'{x:.9g}' if isinstance(x, float) else str(x) for x in v)

    lines = ['<mujoco model="macaque_arm_hand_mutation">',
             '  <!-- MAT2-A05 "first mutation": human myo_sim hand framework (vendor @',
             f'       {VENDOR_REV}) modified toward macaque anatomy. Derived record;',
             '       every number recomputable from mutation_structure.json. -->',
             f'  <!-- mutation scale s = {s:.9f} (macaque hand length / human hand length) -->',
             '  <compiler angle="radian" inertiafromgeom="false"/>',
             '  <asset>']
    for m in MESHES:
        lines.append(f'    <mesh name="mut_{m}" file="{geom_assets[m]["path"]}" scale="{s:.9f} {s:.9f} {s:.9f}"/>')
    lines += ['  </asset>', '  <worldbody>',
              '    <!-- macaque hand body anchor: osim hand body verbatim; wrist-anchored',
              '         via the macaque wrist joint (parent radius1) in the full model -->',
              f'    <body name="macaque_hand_anchor" pos="0 0 0">',
              f'      <joint name="mutation_wrist_flexion" axis="{fmt(mac_axes["rotation1"]["axis"])}" '
              f'range="{mac_wrist["wrist_flexion"][0]:.9g} {mac_wrist["wrist_flexion"][1]:.9g}" damping="0.25"/>',
              f'      <joint name="mutation_wrist_abduction" axis="{fmt(mac_axes["rotation2"]["axis"])}" '
              f'range="{mac_wrist["wrist_abduction"][0]:.9g} {mac_wrist["wrist_abduction"][1]:.9g}" damping="0.25"/>',
              f'      <inertial pos="{fmt(mac_mc)}" mass="{mac_mass}" fullinertia="{fmt(inertias)}"/>',
              '      <!-- macaque hand.vtp envelope (sha256 ' + HAND_VTP_SHA[:16] + '...) is bound in',
              '           mutation_structure.json; VTP is not MuJoCo-loadable, no fabricated mesh -->']
    tree = {}
    for n in HUMAN_BODIES:
        par = chain_parent[n] if chain_parent[n] in HUMAN_BODIES else 'macaque_hand_anchor'
        tree.setdefault(par, []).append(n)

    def emit(n, depth):
        o = anchor_pos[n]
        ind = '  ' * depth
        lines.append(f'{ind}<body name="{n}" pos="{fmt(o)}">')
        for j in joints[n]:
            lines.append(f'{ind}  <joint name="{j["name"]}" axis="{fmt(vec(j["axis"]))}" '
                         f'range="{j["range"][0]:.9g} {j["range"][1]:.9g}"/>')
        ine = inertial[n]
        k = (mass_prior[n] / ine['mass']) * (s ** 2)
        fi = [x * k for x in ine['fullinertia']]
        lines.append(f'{ind}  <inertial pos="0 0 0" mass="{mass_prior[n]:.9g}" fullinertia="{fmt(fi)}"/>')
        lines.append(f'{ind}  <geom name="mut_{BODY_MESH[n]}" mesh="mut_{BODY_MESH[n]}" type="mesh"/>')
        for c in tree.get(n, []):
            emit(c, depth + 1)
        lines.append(f'{ind}</body>')

    for d in ('firstmc', 'secondmc', 'thirdmc', 'fourthmc', 'fifthmc'):
        emit(d, 3)
    lines += ['    </body>', '  </worldbody>', '</mujoco>', '']
    (HERE / 'macaque_hand_mutation.xml').write_text('\n'.join(lines), encoding='utf-8')

    # XML well-formedness of the emitted record
    ET.parse(HERE / 'macaque_hand_mutation.xml')
    say('emitted macaque_hand_mutation.xml (well-formed XML verified)')

    (HERE / 'mutation_structure.json').write_text(
        json.dumps(structure, indent=1) + '\n', encoding='utf-8')
    struct_sha = sha256_file(HERE / 'mutation_structure.json')
    say(f'emitted mutation_structure.json sha256={struct_sha}')

    (HERE / 'derivation_output.txt').write_text('\n'.join(out) + '\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main())
